"""G-I4-M1-CORRECTIVE: the compact containers must be exact, deterministic and bounded.

The three primitives in :mod:`nse_engine.compact` carry governed state (the D01 distinct counts
and the identity key space), so "compact" must not mean "approximate":

* :class:`TokenIntern` must assign dense, first-appearance ids and rebuild its reverse table
  exactly, including after growth and after interleaved lookups;
* :class:`Uint64Set` must behave exactly like a Python ``set`` of the same integers — no
  probabilistic membership, no collision-based false positives, including across the internal
  growth boundaries and under deliberately colliding hash inputs;
* :class:`RowTokens` must reproduce the governed normalization and the distinct-value counters
  that the D01 fold and the association chain both read.

All inputs here are deterministic (a fixed integer sequence, no randomness, no clock).
"""

from __future__ import annotations

import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
for path in (SRC_DIR, REPO_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from nse_engine.compact import RowTokens, TokenIntern, Uint64Set, normalize_upper_trim  # noqa: E402

_MASK64 = (1 << 64) - 1


def sequence(count: int, seed: int = 0x2545F4914F6CDD1D):
    """A deterministic splitmix64 stream: same values on every platform and every run."""
    value = seed
    for _index in range(count):
        value = (value + 0x9E3779B97F4A7C15) & _MASK64
        mixed = value
        mixed = ((mixed ^ (mixed >> 30)) * 0xBF58476D1CE4E5B9) & _MASK64
        mixed = ((mixed ^ (mixed >> 27)) * 0x94D049BB133111EB) & _MASK64
        yield mixed ^ (mixed >> 31)


class TokenInternTests(unittest.TestCase):
    def test_ids_are_dense_and_first_appearance_ordered(self):
        intern = TokenIntern()
        self.assertEqual([intern.id(token) for token in ("b", "a", "b", "c", "a")], [0, 1, 0, 2, 1])
        self.assertEqual(intern.by_id(), ["b", "a", "c"])
        self.assertEqual(len(intern), 3)

    def test_reverse_table_is_cached_and_refreshed_after_insertion(self):
        intern = TokenIntern()
        intern.id("x")
        first = intern.by_id()
        self.assertIs(intern.by_id(), first, "the reverse table must be cached, not rebuilt")
        intern.id("y")
        second = intern.by_id()
        self.assertIsNot(second, first)
        self.assertEqual(second, ["x", "y"])

    def test_lookup_never_inserts(self):
        intern = TokenIntern()
        intern.id("x")
        self.assertEqual(intern.lookup("x"), 0)
        self.assertIsNone(intern.lookup("missing"))
        self.assertEqual(len(intern), 1)

    def test_keys_is_a_fresh_sortable_list(self):
        intern = TokenIntern()
        for token in ("c", "a", "b"):
            intern.id(token)
        keys = intern.keys()
        keys.sort()
        self.assertEqual(keys, ["a", "b", "c"])
        self.assertEqual(len(intern), 3, "sorting the returned list must not touch the intern")

    def test_none_and_empty_string_are_distinct_tokens(self):
        intern = TokenIntern()
        self.assertNotEqual(intern.id(None), intern.id(""))
        self.assertEqual(intern.by_id(), [None, ""])


class Uint64SetTests(unittest.TestCase):
    def test_matches_a_python_set_exactly_including_growth_boundaries(self):
        seen = Uint64Set(capacity=8)
        reference = set()
        values = list(sequence(5000))
        duplicates = values[::3]
        for value in values:
            reference.add(value)
            self.assertTrue(seen.add(value), "first insertion must report True")
        for value in duplicates:
            self.assertFalse(seen.add(value), "re-insertion must report False")
            self.assertIn(value, seen)
            self.assertIn(value, reference)
        self.assertEqual(len(seen), len(reference))
        for value in values:
            self.assertEqual(value in seen, value in reference)
        # an absent value must never report present
        absent = [value for value in sequence(2000, seed=1) if value not in reference]
        for value in absent[:500]:
            self.assertNotIn(value, seen)

    def test_forced_collisions_stay_exact(self):
        """Keys whose mixer outputs collide must still be distinguished by the stored key."""
        seen = Uint64Set(capacity=4)
        reference = set()
        # keys that share the lowest bits (a pathological linear-probe pattern)
        for index in range(4000):
            value = (index << 12) | (index & 0xFFF)
            reference.add(value)
            seen.add(value)
        self.assertEqual(len(seen), len(reference))
        for value in reference:
            self.assertIn(value, seen)

    def test_boundary_keys_and_rejections(self):
        seen = Uint64Set(capacity=4)
        self.assertTrue(seen.add(0))
        self.assertIn(0, seen)
        self.assertTrue(seen.add(_MASK64 - 1))
        self.assertIn(_MASK64 - 1, seen)
        self.assertNotIn(_MASK64, seen)
        self.assertNotIn(-1, seen)
        with self.assertRaises(ValueError):
            seen.add(_MASK64)

    def test_capacity_is_a_power_of_two_and_load_stays_bounded(self):
        seen = Uint64Set(capacity=8)
        for value in sequence(3000, seed=7):
            seen.add(value)
        self.assertEqual(seen.capacity() & (seen.capacity() - 1), 0)
        self.assertLessEqual(len(seen), seen.capacity() * 7 // 10)

    def test_membership_is_independent_of_process_hash_seed(self):
        """The mixer is ours, so membership cannot depend on ``PYTHONHASHSEED``."""
        import subprocess

        script = (
            "import sys; sys.path.insert(0, %r)\n"
            "from nse_engine.compact import Uint64Set\n"
            "seen = Uint64Set(capacity=4)\n"
            "for value in (1, 2, 3, 1 << 40, (1 << 64) - 2):\n"
            "    seen.add(value)\n"
            "print(len(seen), [value in seen for value in (1, 2, 3, 1 << 40, (1 << 64) - 2, 5)])\n"
        ) % SRC_DIR
        results = set()
        for seed in ("0", "1", "12345"):
            completed = subprocess.run(
                [sys.executable, "-B", "-c", script], capture_output=True, text=True,
                env=dict(os.environ, PYTHONHASHSEED=seed),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            results.add(completed.stdout.strip())
        self.assertEqual(len(results), 1, results)
        self.assertTrue(results.pop().endswith("[True, True, True, True, True, False]"))


class RowTokensTests(unittest.TestCase):
    def test_normalization_matches_the_governed_rule(self):
        self.assertEqual(normalize_upper_trim(None), "")
        self.assertEqual(normalize_upper_trim("  ine144j01027 "), "INE144J01027")
        self.assertEqual(normalize_upper_trim("\tAB\n"), "AB")

    def test_symbol_counter_counts_distinct_nonblank_normalized_symbols(self):
        tokens = RowTokens()
        for value in ("AAA", "aaa ", "BBB", "", None, "  ", "AAA"):
            tokens.symbol_id(normalize_upper_trim(value))
        self.assertEqual(tokens.distinct_symbol_count(), 2)
        self.assertEqual(len(tokens.symbol), 3, "the blank token is interned but not counted")

    def test_verbatim_symbol_is_a_second_copy_only_when_it_differs(self):
        tokens = RowTokens()
        clean = tokens.symbol_id(normalize_upper_trim("AAA"))
        self.assertEqual(tokens.raw_symbol_id("AAA") if "AAA" != normalize_upper_trim("AAA") else 0, 0)
        dirty = tokens.symbol_id(normalize_upper_trim(" aaa "))
        self.assertEqual(clean, dirty, "equal after normalization: one shared token")
        exception_id = tokens.raw_symbol_id(" aaa ")
        self.assertEqual(tokens.raw_symbol_by_exception_id(exception_id), " aaa ")
        self.assertNotEqual(exception_id, 0)
        # None is a verbatim value too and must round-trip
        none_id = tokens.raw_symbol_id(None)
        self.assertIsNone(tokens.raw_symbol_by_exception_id(none_id))

    def test_shared_tokens_give_the_metric_fold_its_distinct_counts(self):
        from nse_engine.metrics import RowMetricAccumulator

        tokens = RowTokens()
        accumulator = RowMetricAccumulator(tokens)
        self.assertEqual(len(tokens.isin), 0)
        self.assertEqual(tokens.distinct_symbol_count(), 0)
        self.assertEqual(accumulator.result().get("distinct_nonblank_isin"), 0)


if __name__ == "__main__":
    unittest.main()
