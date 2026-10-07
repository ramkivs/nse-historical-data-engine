"""G-I4-M1 equivalence: bounded-memory streaming W2 vs the batch composition.

The authorization requires byte-level equivalence between the existing ``build_w2()`` result and
the bounded-memory streaming composition, over all applicable fixture corpora, including member
order permutation. This module proves it *inside the repository* (the cross-version proof against
the pre-revision engine is recorded in the G-I4-M1 report, produced outside the repository):

* ``build_w2()`` is now expressed over :class:`nse_engine.w2_stream.W2Accumulator`, so comparing
  it with a directly-driven accumulator is a composition check, not a semantic claim;
* the byte-level checks here are over the *serialized* artifacts the runner writes
  (``calendar.jsonl``, ``associations.jsonl``, ``identity_summary.json``, ``metrics.json``,
  ``unresolved.jsonl``) plus totals, exclusions, unkeyed groups, method, metric definitions,
  metric values, member facts, identity ordering and provenance ordering.

Every corpus used here is synthetic or a published row-sample fixture; the real corpus is never
touched. No test reads a clock, an environment value or a random source.
"""

from __future__ import annotations

import json
import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
for path in (SRC_DIR, REPO_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from nse_engine import contract, w2_stream  # noqa: E402
from nse_engine.evidence_inputs import InventoryFileRecord  # noqa: E402
from nse_engine.identity import AssociationStreamError, build_associations  # noqa: E402
from nse_engine.metrics import compute_row_metrics  # noqa: E402
from nse_engine.pipeline import build_canonical, build_w2, member_date_facts  # noqa: E402
from tests import support  # noqa: E402


def cjson(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def calendar_jsonl(result) -> str:
    return "".join(cjson(day.to_dict()) + "\n" for day in result.days)


def associations_jsonl(documents) -> str:
    return "".join(cjson(document.to_dict()) + "\n" for document in documents)


class StreamFixtureCase(unittest.TestCase):
    """Shared helpers: synthetic members and streaming/batch surfaces."""

    def synthetic_members(self):
        """Four members spanning both format families, with inverted file-date order.

        The corpus property this reproduces: ``discover_archives`` orders members by
        ``(root, relative_path)``, which is not date order, while identity runs and observed
        ranges must still be derived in ``(business_date, line_number)`` order.
        """
        specs = [
            ("legacy", "cm01JAN2025bhav.csv", "01-JAN-2025", "2025-01-01", [
                support.legacy_row(SYMBOL="AAA", ISIN="INE001A01011", SERIES="EQ",
                                   TIMESTAMP="01-JAN-2025"),
                support.legacy_row(SYMBOL="BBB", ISIN="INE002A01012", SERIES="EQ",
                                   TIMESTAMP="01-JAN-2025"),
                support.legacy_row(SYMBOL="CCC", ISIN="", SERIES="EQ", TIMESTAMP="01-JAN-2025"),
                support.legacy_row(SYMBOL="AAA", ISIN="INE001A01011", SERIES="BL",
                                   TIMESTAMP="01-JAN-2025"),
            ]),
            ("legacy", "cm31DEC2024bhav.csv", "31-DEC-2024", "2024-12-31", [
                support.legacy_row(SYMBOL="AAA", ISIN="INE001A01011", SERIES="EQ",
                                   TIMESTAMP="31-DEC-2024"),
                support.legacy_row(SYMBOL="AAA", ISIN="INE001A01011", SERIES="BE",
                                   TIMESTAMP="31-DEC-2024"),
                support.legacy_row(SYMBOL="ZZZ", ISIN="INE003A01013", SERIES="EQ",
                                   TIMESTAMP="31-DEC-2024"),
            ]),
            ("udiff", "BhavCopy_NSE_CM_0_0_0_20240709_F.csv", "2024-07-09", "2024-07-09", [
                support.udiff_row(TckrSymb="DDD", ISIN="INE004A01014", SctySrs="EQ",
                                  TradDt="2024-07-09", BizDt="2024-07-09"),
                support.udiff_row(TckrSymb="EEE", ISIN="", SctySrs="EQ",
                                  TradDt="2024-07-09", BizDt="2024-07-09"),
            ]),
            ("udiff", "BhavCopy_NSE_CM_0_0_0_20240702_F.csv", "2024-07-02", "2024-07-02", [
                support.udiff_row(TckrSymb="DDD", ISIN="INE004A01014", SctySrs="BE",
                                  TradDt="2024-07-02", BizDt="2024-07-02"),
                support.udiff_row(TckrSymb="FFF", ISIN="INE005A01015", SctySrs="EQ",
                                  TradDt="2024-07-02", BizDt="2024-07-02"),
            ]),
        ]
        builds, inventory = [], []
        for family, name, date_text, date_iso, rows in specs:
            data = support.legacy_member(rows) if family == "legacy" else support.udiff_member(rows)
            builds.append(build_canonical(
                data, support.source_for(name, expected_source_date=date_iso, run_id="i4-equiv")
            ))
            inventory.append(InventoryFileRecord(
                file_name=name, date=date_iso, root=family.upper(),
                sha256="0" * 64, row_count=len(rows),
            ))
        return tuple(builds), tuple(inventory)

    def stream(self, builds, inventory, labels=(), circular_holidays=()):
        """Drive the bounded-memory accumulator over the builds in the given order."""
        accumulator = w2_stream.W2Accumulator()
        for build in builds:
            accumulator.add_member(build.rows, build.parse.header.family)
        stream = accumulator.identity_stream()
        documents = tuple(stream)
        totals = stream.totals()
        return {
            "calendar": accumulator.calendar(
                inventory, labels=labels, circular_holidays=circular_holidays
            ),
            "metrics": accumulator.metrics(),
            "summary": accumulator.association_summary(),
            "documents": documents,
            "totals": totals,
            "member_facts": accumulator.member_facts(),
            "identity_count": accumulator.identity_count(),
            "row_count": accumulator.row_count(),
        }

    def assert_equivalent(self, w2, streamed):
        """Every comparable W2 surface must be byte-identical after serialization."""
        self.assertEqual(
            calendar_jsonl(w2.calendar), calendar_jsonl(streamed["calendar"]),
            "calendar days (and day order) must be byte-identical",
        )
        self.assertEqual(
            associations_jsonl(w2.associations.identities),
            associations_jsonl(streamed["documents"]),
            "identity documents (and identity order) must be byte-identical",
        )
        self.assertEqual(w2.associations.totals(), streamed["totals"])
        self.assertEqual(w2.associations.method, streamed["summary"].method)
        self.assertEqual(tuple(w2.associations.overlay_rows_excluded),
                         streamed["summary"].overlay_rows_excluded)
        self.assertEqual(tuple(w2.associations.unkeyed), streamed["summary"].unkeyed)
        self.assertEqual(w2.metrics.to_dict(), streamed["metrics"].to_dict())
        self.assertEqual(w2.calendar.totals(), streamed["calendar"].totals())
        self.assertEqual(dict(w2.calendar.label_status_counts()),
                         dict(streamed["calendar"].label_status_counts()))
        self.assertEqual(tuple(w2.calendar.unresolved_dates()),
                         tuple(streamed["calendar"].unresolved_dates()))
        self.assertEqual(len(w2.rows), streamed["row_count"])
        self.assertEqual(len(w2.associations.identities), streamed["identity_count"])
        # D01 metric definitions/values carried unchanged
        self.assertEqual(
            dict(w2.metrics.to_dict()["definitions"]), dict(contract.D01_METRIC_DEFINITIONS)
        )


class StreamingEquivalenceTests(StreamFixtureCase):
    def test_synthetic_corpus_streaming_equals_batch(self):
        builds, inventory = self.synthetic_members()
        w2 = build_w2(builds, inventory)
        self.assert_equivalent(w2, self.stream(builds, inventory))

    def test_published_fixture_corpora_streaming_equals_batch(self):
        w2 = support.build_w2_samples()
        labels, holidays, _registry, _document = support.load_calendar_labels()
        self.assert_equivalent(
            w2,
            self.stream(w2.builds, support.load_inventory_records(), labels, holidays),
        )

    def test_member_order_permutation_is_identity(self):
        builds, inventory = self.synthetic_members()
        forward = self.stream(builds, inventory)
        reversed_ = self.stream(tuple(reversed(builds)), inventory)
        self.assertEqual(
            calendar_jsonl(forward["calendar"]), calendar_jsonl(reversed_["calendar"])
        )
        self.assertEqual(
            associations_jsonl(forward["documents"]), associations_jsonl(reversed_["documents"])
        )
        self.assertEqual(forward["totals"], reversed_["totals"])
        self.assertEqual(
            forward["metrics"].to_dict(), reversed_["metrics"].to_dict()
        )
        # member facts are the same facts; only their input order differs (the calendar itself
        # is derived over a date-keyed mapping, which is why the calendar bytes above are stable)
        as_tuples = lambda facts: sorted(
            (fact.business_date, fact.format_family, fact.trad_dt_eq_biz_dt) for fact in facts
        )
        self.assertEqual(as_tuples(forward["member_facts"]), as_tuples(reversed_["member_facts"]))

    def test_member_facts_come_from_the_single_engine_rule(self):
        builds, inventory = self.synthetic_members()
        accumulator = w2_stream.W2Accumulator()
        for build in builds:
            accumulator.add_member(build.rows, build.parse.header.family)
        self.assertEqual(member_date_facts(builds), accumulator.member_facts())

    def test_metric_fold_is_the_single_engine_rule(self):
        builds, inventory = self.synthetic_members()
        rows = tuple(row for build in builds for row in build.rows)
        accumulator = w2_stream.W2Accumulator()
        for build in builds:
            accumulator.add_member(build.rows, build.parse.header.family)
        self.assertEqual(compute_row_metrics(rows).to_dict(), accumulator.metrics().to_dict())

    def test_association_accumulator_matches_the_batch_association_result(self):
        builds, inventory = self.synthetic_members()
        rows = tuple(row for build in builds for row in build.rows)
        batch = build_associations(rows)
        accumulator = w2_stream.W2Accumulator()
        accumulator.add_rows(rows)
        self.assertEqual(
            associations_jsonl(batch.identities),
            associations_jsonl(accumulator.identity_documents()),
        )
        summary = accumulator.association_summary()
        self.assertEqual(batch.method, summary.method)
        self.assertEqual(tuple(batch.unkeyed), summary.unkeyed)
        self.assertEqual(tuple(batch.overlay_rows_excluded), summary.overlay_rows_excluded)

    def test_identity_stream_totals_require_full_consumption(self):
        builds, inventory = self.synthetic_members()
        accumulator = w2_stream.W2Accumulator()
        for build in builds:
            accumulator.add_member(build.rows, build.parse.header.family)
        stream = accumulator.identity_stream()
        with self.assertRaises(AssociationStreamError):
            stream.totals()
        consumed = tuple(stream)
        self.assertEqual(len(consumed), stream.totals()["identities"])
        self.assertEqual(
            accumulator.association_build().totals(), stream.totals()
        )

    def test_serialization_is_deterministic_across_independent_compositions(self):
        builds, inventory = self.synthetic_members()
        first = self.stream(builds, inventory)
        second = self.stream(builds, inventory)
        self.assertEqual(calendar_jsonl(first["calendar"]), calendar_jsonl(second["calendar"]))
        self.assertEqual(
            associations_jsonl(first["documents"]), associations_jsonl(second["documents"])
        )
        self.assertEqual(cjson(first["totals"]), cjson(second["totals"]))

    def test_streamed_state_is_packed_and_bounded_per_row(self):
        """The accumulator holds packed integers per row, never row objects."""
        builds, inventory = self.synthetic_members()
        accumulator = w2_stream.W2Accumulator()
        for build in builds:
            accumulator.add_member(build.rows, build.parse.header.family)
        assoc = accumulator._associations
        self.assertIsInstance(assoc._data, __import__("array").array)
        self.assertEqual(assoc._FIELDS_PER_ROW, 7)
        self.assertEqual(len(assoc._data), assoc._FIELDS_PER_ROW * assoc.keyed_row_count())
        self.assertEqual(len(assoc._next), assoc.keyed_row_count())
        self.assertEqual(len(assoc._head), accumulator.identity_count())
        # one interned copy per distinct value, shared with the D01 fold
        self.assertEqual(len(accumulator._tokens.isin), accumulator.metrics().get("distinct_nonblank_isin"))
        # every reconstructed document is transient: the stream yields one identity at a time
        stream = accumulator.identity_stream()
        first = next(iter(stream))
        self.assertTrue(first.to_dict())


if __name__ == "__main__":
    unittest.main()
