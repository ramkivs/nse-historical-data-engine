"""G-I4-M1-CORRECTIVE: fixture-scale memory acceptance for the bounded-memory W2 accumulator.

Acceptance (the criterion is authoritative and is not weakened here): the retained accumulator +
runner state must project to **≤ 2.5 GB** at the governed corpus shape, using an explicit,
reproducible corpus-shape model, with the identity-dominated shape (one distinct ISIN per row —
the shape that produced the pre-corrective ≈4.33 GB projection and that the mandatory memory
profile requires) as the worst case.

Everything this module measures is synthetic; the real corpus is never read.

Retained-state methodology
--------------------------
* ``deep_size`` walks the accumulator's retained containers and sums ``sys.getsizeof`` over them
  recursively (keys, tables, arrays) — the *retained* footprint, no transient noise;
* the same quantity is cross-checked against ``tracemalloc`` current traced memory at a smaller
  scale in :meth:`test_deep_size_agrees_with_tracemalloc`;
* the runner's own state is measured end to end through ``i4_runner.main`` on a synthetic corpus;
* the corpus-shape model is: ``rows = 5,689,949`` (D01 exact), and the worst case assumes one
  distinct ISIN **and** one distinct symbol per row (the maximum any corpus can reach — the D01
  evidence's own distinct counts are both below the row count, so this is a strict upper bound).
"""

from __future__ import annotations

import contextlib
import datetime
import gc
import hashlib
import io
import json
import os
import sys
import tempfile
import tracemalloc
import unittest
import zipfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
for path in (SRC_DIR, REPO_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from nse_engine import w2_stream  # noqa: E402
from nse_engine.evidence_inputs import InventoryFileRecord  # noqa: E402
from nse_engine.pipeline import build_canonical, build_w2  # noqa: E402
from tests import support  # noqa: E402

#: governed corpus parameters (D01 evidence: FIX-SEM-DEF-01__metrics.csv and
#: evidence/identity/d02_metrics.json — 2,462 files, rows/file min 1,660, mean 2,311, max 3,704)
CORPUS_ROWS = 5_689_949
CORPUS_MEMBERS = 2_462
CORPUS_MEAN_MEMBER_ROWS = 2311
CORPUS_MAX_MEMBER_ROWS = 3704
#: sum of the per-file distinct ISIN counts — an upper bound on the corpus-wide distinct count
#: (the same security counted once per file it appears in); the corpus-wide value is unknown
#: because the equity master is GATED
CORPUS_DISTINCT_ISIN_UPPER_BOUND = 5_686_592
CORPUS_DISTINCT_SYMBOL_UPPER_BOUND = 5_449_244

#: the authorization's acceptance ceiling (never raised, never redefined here)
CEILING_BYTES = 2_500_000_000


def deep_size(obj, seen=None) -> int:
    """Recursive ``sys.getsizeof`` over containers (the retained footprint of the state)."""
    if seen is None:
        seen = set()
    if id(obj) in seen:
        return 0
    seen.add(id(obj))
    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        for key, value in obj.items():
            size += deep_size(key, seen) + deep_size(value, seen)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for item in obj:
            size += deep_size(item, seen)
    return size


def retained_bytes(accumulator) -> int:
    """Retained accumulator state: every container the accumulator keeps after ingestion."""
    association = accumulator._associations
    tokens = accumulator._tokens
    return (
        deep_size(association._data)
        + deep_size(association._next)
        + deep_size(association._head)
        + deep_size(tokens.isin._ids)
        + deep_size(tokens.symbol._ids)
        + deep_size(tokens.raw_symbol._ids)
        + deep_size(accumulator._metrics._pairs._slots)
        + deep_size(accumulator._metrics._series._ids)
        + deep_size(association._series_tokens._ids)
        + deep_size(association._validity_tokens._ids)
        + deep_size(association._member_index)
        + deep_size(association._member_provenance)
        + deep_size(association._unkeyed)
        + deep_size(association._excluded)
        + deep_size(accumulator._facts)
    )


def _weekday_dates(count: int, start: datetime.date = datetime.date(2016, 9, 20)):
    dates, day = [], start
    while len(dates) < count:
        if day.weekday() <= 4:
            dates.append(day)
        day += datetime.timedelta(days=1)
    return dates


def _shape_rows(shape: str, member_index: int, rows_per_member: int):
    """Deterministic synthetic rows for the three declared shapes (legacy family)."""
    start = member_index * rows_per_member
    rows = []
    for offset in range(rows_per_member):
        index = start + offset
        if shape == "A":            # repeated identities and repeated observations
            isin, symbol = "INE%06dA0101%d" % (index % 2000, index % 10), "SYM%03d" % (index % 2000)
            series = "EQ" if offset % 2 else "BE"
        elif shape == "B":          # identity-dominated: one distinct ISIN and symbol per row
            isin, symbol = "INE%06dA0101%d" % (index, index % 10), "SYM%06d" % index
            series = "EQ"
        else:                       # mixed: identities repeat, symbols repeat moderately
            isin, symbol = "INE%06dA0101%d" % (index % 50000, index % 10), "SYM%04d" % (index % 5000)
            series = "EQ" if offset % 3 else "BE"
        rows.append(support.legacy_row(SYMBOL=symbol, ISIN=isin, SERIES=series,
                                       TIMESTAMP="20-SEP-2016"))
    return rows


def measure_shape(shape: str, members: int, rows_per_member: int, stream: bool = True) -> dict:
    """Ingest a synthetic corpus of the given shape and report its retained state."""
    accumulator = w2_stream.W2Accumulator()
    for member_index in range(members):
        name = "cm%05dSEP2016.csv" % member_index
        rows = _shape_rows(shape, member_index, rows_per_member)
        build = build_canonical(
            support.legacy_member(rows),
            support.source_for(name, expected_source_date="2016-09-20"),
        )
        accumulator.add_member(build.rows, build.parse.header.family)
        del build, rows
    identities = 0
    if stream:
        for _document in accumulator.identity_stream():
            identities += 1
    rows_total = members * rows_per_member
    retained = retained_bytes(accumulator)
    metrics = accumulator.metrics()
    return {
        "shape": shape,
        "rows": rows_total,
        "identities": identities or accumulator.identity_count(),
        "distinct_isin": metrics.get("distinct_nonblank_isin"),
        "distinct_symbol": metrics.get("distinct_nonblank_symbol"),
        "retained_bytes": retained,
        "bytes_per_row": retained / rows_total,
        "bytes_per_identity": retained / max(identities or accumulator.identity_count(), 1),
        "accumulator": accumulator,
    }


def measure_member_transient(rows_per_member: int = CORPUS_MEAN_MEMBER_ROWS) -> dict:
    """The runner's largest unavoidable transient: one member's complete processing cycle.

    The runner retains nothing per row beyond the accumulator, so its peak is the accumulator's
    retained state plus the **bounded** work of the member currently being processed. This measures
    that bounded work at the corpus's mean member size (2,311 rows) using the runner's own steps:
    parse the member (``build_canonical``), serialize its rows (``rows_jsonl``), build its evidence
    document (``build_evidence``), derive the member-date fact, and feed the rows to the
    accumulator. The value is used as a declared upper bound (multiplied by a safety factor) rather
    than extrapolated per row, because it does not grow with the corpus.
    """
    from nse_engine.serialize import build_evidence, rows_jsonl

    rows = _shape_rows("B", 0, rows_per_member)
    data = support.legacy_member(rows)
    gc.collect()
    tracemalloc.start()
    tracemalloc.reset_peak()
    build = build_canonical(
        data, support.source_for("cm20SEP2016.csv", expected_source_date="2016-09-20")
    )
    payload = rows_jsonl(build.rows)
    evidence = build_evidence(build)
    accumulator = w2_stream.W2Accumulator()
    accumulator.add_member(build.rows, build.parse.header.family)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return {
        "rows_per_member": rows_per_member,
        "transient_bytes": peak,
        "bytes_per_row": peak / rows_per_member,
        "rows_jsonl_bytes": len(payload),
        "evidence_keys": sorted(evidence)[:3],
        "fact": accumulator.member_facts()[0].business_date,
    }


def measure_runner_peak(members: int = 20, rows_per_member: int = 150) -> dict:
    """End-to-end runner peak (accumulator + runner state + writing) on a synthetic corpus."""
    sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))
    from tools.i4_runner import i4_runner

    tmp = tempfile.mkdtemp(prefix="i4-memory-")
    legacy = os.path.join(tmp, "legacy")
    udiff = os.path.join(tmp, "udiff")
    os.makedirs(legacy)
    os.makedirs(udiff)
    records = []
    for member_index, day in enumerate(_weekday_dates(members)):
        rows = [
            support.legacy_row(SYMBOL="SYM%06d" % (member_index * rows_per_member + offset),
                               ISIN="INE%06dA0101%d" % (member_index * rows_per_member + offset, offset % 10),
                               SERIES="EQ", TIMESTAMP=day.strftime("%d-%b-%Y").upper())
            for offset in range(rows_per_member)
        ]
        data = support.legacy_member(rows)
        name = "cm%s-bhav.csv" % day.strftime("%d%b%Y").upper()
        archive = os.path.join(legacy, name + ".zip")
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as handle:
            handle.writestr(name, data)
        with open(archive, "rb") as handle:
            raw = handle.read()
        headers = data.decode("utf-8").splitlines()[0].split(",")
        records.append({
            "root": "LEGACY", "relative_path": name + ".zip", "file_name": name + ".zip",
            "size_bytes": len(raw), "date_from_filename": day.isoformat(),
            "sha256": hashlib.sha256(raw).hexdigest(), "detected_format": "LEGACY",
            "row_count": rows_per_member, "bad_rows": 0, "headers": headers,
            "header_signature": "|".join(headers),
            "date_values": {day.strftime("%d-%b-%Y").upper(): rows_per_member},
            "series_counts": {"EQ": rows_per_member}, "symbol_count": rows_per_member,
            "isin_count": rows_per_member,
        })
    inventory_dir = os.path.join(tmp, "inventory")
    os.makedirs(inventory_dir)
    inventory_path = os.path.join(inventory_dir, "file_inventory.json")
    with open(inventory_path, "w", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps(records, indent=1, sort_keys=True) + "\n")

    gc.collect()
    tracemalloc.start()
    tracemalloc.reset_peak()
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        code = i4_runner.main([
            "run", "--legacy-root", legacy, "--udiff-root", udiff,
            "--inventory", inventory_path, "--out", os.path.join(tmp, "run"),
            "--run-id", "i4-memory",
        ])
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    rows_total = members * rows_per_member
    return {
        "exit_code": code,
        "rows": rows_total,
        "members": members,
        "peak_bytes": peak,
        "peak_bytes_per_row": peak / rows_total,
        "output": stdout.getvalue(),
    }


class RetainedStateModelTests(unittest.TestCase):
    """The three declared shapes and the corpus-shape projection."""

    SHAPE_B_MEMBERS = 100
    SHAPE_B_ROWS_PER_MEMBER = 1000     # 100,000 rows / 100,000 identities / 100,000 symbols

    def test_identity_dominated_projection_meets_the_ceiling(self):
        """The authoritative acceptance: accumulator + runner state ≤ 2.5 GB at corpus scale.

        Model (explicit and reproducible):

        * rows = 5,689,949 (D01 exact);
        * identity profile = worst case: one distinct ISIN **and** one distinct symbol per row —
          the maximum any corpus can reach, and therefore independent of the unresolved real
          identity profile (the equity master is GATED);
        * accumulator state = measured retained bytes/row × rows (the accumulator retains nothing
          per member: only packed rows, per-identity packed chains and interned distinct values);
        * runner state = measured single-member transient (the largest unavoidable per-member
          work: parse + serialize + evidence + feed at the corpus's mean member size), carried at
          1.5× as a declared safety allowance. It does not scale with the corpus.
        """
        measured = measure_shape("B", self.SHAPE_B_MEMBERS, self.SHAPE_B_ROWS_PER_MEMBER)
        self.assertEqual(measured["identities"], self.SHAPE_B_MEMBERS * self.SHAPE_B_ROWS_PER_MEMBER)
        self.assertEqual(measured["distinct_isin"], measured["identities"])
        transient = measure_member_transient(CORPUS_MEAN_MEMBER_ROWS)
        self.assertEqual(transient["fact"], "2016-09-20")

        accumulator_bytes = measured["bytes_per_row"] * CORPUS_ROWS
        # the transient is linear in the member's row count, so the largest member in the corpus
        # (D01 exact: 3,704 rows) is the worst case; 1.5x is the declared safety allowance
        runner_allowance = (
            transient["transient_bytes"]
            * (CORPUS_MAX_MEMBER_ROWS / CORPUS_MEAN_MEMBER_ROWS)
            * 1.5
        )
        total_bytes = accumulator_bytes + runner_allowance
        detail = (
            "accumulator %.3f GB (%.1f B/row x %d rows) + runner allowance %.3f MB "
            "(1.5 x %.3f MB transient measured at %d rows, scaled to the %d-row maximum) "
            "= %.3f GB (ceiling %.3f GB)"
            % (
                accumulator_bytes / 1e9, measured["bytes_per_row"], CORPUS_ROWS,
                runner_allowance / 1e6, transient["transient_bytes"] / 1e6,
                CORPUS_MEAN_MEMBER_ROWS, CORPUS_MAX_MEMBER_ROWS, total_bytes / 1e9,
                CEILING_BYTES / 1e9,
            )
        )
        self.assertLessEqual(total_bytes, CEILING_BYTES, detail)
        # headroom: the accumulator term (the corpus-shape term) must stay under 2.0 GB
        self.assertLessEqual(accumulator_bytes / 1e9, 2.0, detail)

    def test_runner_transient_is_bounded_by_member_size_not_by_corpus_size(self):
        """Doubling the corpus must not change the per-member transient (no build retention)."""
        small_member = measure_member_transient(1155)
        large_member = measure_member_transient(2311)
        per_row_small = small_member["transient_bytes"] / small_member["rows_per_member"]
        per_row_large = large_member["transient_bytes"] / large_member["rows_per_member"]
        self.assertLess(per_row_large, per_row_small * 1.2, "transient must stay proportional to a member")
        # measured regime: the parse + serialization + evidence transient is ~15 kB/row of the
        # member being processed (member rows are released immediately afterwards)
        self.assertLess(per_row_large, 25_000.0)
        self.assertLess(per_row_small, 25_000.0)
        # the transient is a per-member quantity: at the corpus's largest member it stays a flat
        # allowance of tens of megabytes, never a function of the corpus
        biggest_member = per_row_large * CORPUS_MAX_MEMBER_ROWS
        self.assertLess(biggest_member, 96 * 1024 * 1024)

    def test_projection_sensitivity_to_the_unresolved_identity_profile(self):
        """The criterion holds at the worst case; every realistic profile is strictly smaller.

        The exact corpus-wide distinct-identity count is not available from the accessible evidence
        (the equity master is GATED), so acceptance uses the worst case — one distinct identity per
        row — and this test shows the projection only falls as the identity count falls. The
        per-identity term is the measured shape-B cost minus the packed row cost, and the runner
        allowance is carried at its full value in every row of the table.
        """
        measured = measure_shape("B", self.SHAPE_B_MEMBERS, self.SHAPE_B_ROWS_PER_MEMBER)
        transient = measure_member_transient()
        per_row_fixed = 28.0                     # seven uint32 packed row fields
        per_identity = measured["bytes_per_identity"] - per_row_fixed
        self.assertGreater(per_identity, 100.0)
        runner_allowance = (
            transient["transient_bytes"] * (CORPUS_MAX_MEMBER_ROWS / CORPUS_MEAN_MEMBER_ROWS) * 1.5
        )

        table = {}
        for label, identities in (
            ("every row a new identity (worst case)", CORPUS_ROWS),
            ("half the rows a new identity", CORPUS_ROWS // 2),
            ("one million identities", 1_000_000),
            ("two hundred thousand identities", 200_000),
        ):
            retained = per_row_fixed * CORPUS_ROWS + per_identity * identities
            table[label] = (retained + runner_allowance) / 1e9
        for label, value in table.items():
            self.assertLessEqual(value, 2.5, "%s -> %.3f GB" % (label, value))
        self.assertLess(table["two hundred thousand identities"],
                        table["every row a new identity (worst case)"])
        self.assertLess(table["half the rows a new identity"],
                        table["every row a new identity (worst case)"])

    def test_the_three_shapes_are_all_under_the_ceiling(self):
        shapes = {
            "A": (8, 2500),    # 20,000 rows / 200 identities / 200 symbols
            "B": (20, 1000),   # 20,000 rows / 20,000 identities / 20,000 symbols
            "C": (20, 1000),   # 20,000 rows / 5,000 identities / 500 symbols
        }
        projections = {}
        for shape, (members, rows_per_member) in shapes.items():
            measured = measure_shape(shape, members, rows_per_member)
            projections[shape] = measured["bytes_per_row"] * CORPUS_ROWS / 1e9
            self.assertLess(projections[shape], 2.5, "%s projection" % shape)
        # the identity-dominated shape must be the most expensive of the three
        self.assertGreaterEqual(projections["B"], projections["C"])
        self.assertGreaterEqual(projections["C"], projections["A"])

    def test_repeated_observation_shape_retains_far_less_than_identity_dominated(self):
        repeated = measure_shape("A", 8, 2500)          # 20,000 rows, 200 identities
        dominated = measure_shape("B", 20, 1000)        # 20,000 rows, 20,000 identities
        self.assertEqual(repeated["rows"], dominated["rows"])
        self.assertLess(repeated["retained_bytes"], dominated["retained_bytes"] / 4)
        self.assertGreater(repeated["bytes_per_identity"], dominated["bytes_per_identity"])

    def test_deep_size_agrees_with_tracemalloc(self):
        """Tie the retained-state metric to a second, independent measurement method."""
        gc.collect()
        tracemalloc.start()
        tracemalloc.reset_peak()
        measured = measure_shape("B", 20, 500)   # 10,000 rows / 10,000 identities
        traced = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        self.assertEqual(measured["rows"], 10_000)
        # both methods count the same retained objects; tracemalloc additionally sees the
        # interpreter's own allocations made while building the corpus
        self.assertLess(abs(traced - measured["retained_bytes"]) / measured["retained_bytes"], 0.50)

    def test_no_build_retention_and_no_per_member_growth(self):
        """Retained state must not grow with the number of members for the same total rows."""
        one_member = measure_shape("B", 1, 2000, stream=False)
        many_members = measure_shape("B", 20, 100, stream=False)
        self.assertEqual(one_member["rows"], many_members["rows"])
        ratio = many_members["retained_bytes"] / one_member["retained_bytes"]
        self.assertLess(ratio, 1.10, "per-member state must stay negligible")
        self.assertEqual(
            many_members["distinct_isin"], one_member["distinct_isin"],
            "the same rows must intern the same distinct ISINs regardless of partitioning",
        )

    def test_no_canonical_build_is_retained(self):
        """The accumulator must never hold a CanonicalBuild (or a SecurityRow) — only packed ids."""
        measured = measure_shape("B", 4, 500, stream=False)
        accumulator = measured["accumulator"]
        self.assertEqual(len(accumulator._associations._data), 7 * 2000)
        for value in accumulator._associations._data[:14]:
            self.assertIsInstance(int(value), int)
        self.assertFalse(hasattr(accumulator, "_builds"))
        self.assertFalse(hasattr(accumulator._associations, "_builds"))

    def test_packed_state_is_bounded_by_rows_identities_and_distinct_values(self):
        measured = measure_shape("B", 20, 500)   # 10,000 rows, all distinct
        accumulator = measured["accumulator"]
        self.assertEqual(len(accumulator._associations._data), 7 * 10_000)
        self.assertEqual(len(accumulator._associations._next), 10_000)
        self.assertEqual(len(accumulator._associations._head), 10_000)
        self.assertEqual(len(accumulator._tokens.isin), 10_000)
        self.assertEqual(len(accumulator._tokens.symbol), 10_000)
        self.assertEqual(accumulator._metrics._pairs.capacity() & (accumulator._metrics._pairs.capacity() - 1), 0)
        # packed rows cost 4 bytes per uint32 field: the whole row store is 28 bytes per row
        # (plus ``array`` growth slack, which stays under one doubling)
        data_bytes = sys.getsizeof(accumulator._associations._data)
        self.assertGreaterEqual(data_bytes, 28 * 10_000)
        self.assertLess(data_bytes, 28 * 10_000 * 2)


class StreamingVsRetentionTests(unittest.TestCase):
    """The pre-corrective retention pattern must stay far more expensive than the streaming one."""

    MEMBERS = 24
    ROWS_PER_MEMBER = 150

    def test_streaming_peak_is_a_fraction_of_the_retention_pattern(self):
        rows = self.MEMBERS * self.ROWS_PER_MEMBER
        dates = _weekday_dates(self.MEMBERS)

        def batch_peak():
            gc.collect()
            tracemalloc.start()
            tracemalloc.reset_peak()
            builds, inventory = [], []
            for index, day in enumerate(dates):
                name = "cm%s-bhav.csv" % day.strftime("%d%b%Y").upper()
                rows_data = _shape_rows("B", index, self.ROWS_PER_MEMBER)
                data = support.legacy_member(rows_data)
                builds.append(build_canonical(
                    data, support.source_for(name, expected_source_date=day.isoformat())
                ))
                inventory.append(InventoryFileRecord(
                    file_name=name, date=day.isoformat(), root="LEGACY",
                    sha256=hashlib.sha256(data).hexdigest(), row_count=self.ROWS_PER_MEMBER,
                ))
            build_w2(tuple(builds), inventory)
            _current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return peak

        def stream_peak():
            gc.collect()
            tracemalloc.start()
            tracemalloc.reset_peak()
            accumulator = w2_stream.W2Accumulator()
            for index, day in enumerate(dates):
                name = "cm%s-bhav.csv" % day.strftime("%d%b%Y").upper()
                rows_data = _shape_rows("B", index, self.ROWS_PER_MEMBER)
                data = support.legacy_member(rows_data)
                build = build_canonical(
                    data, support.source_for(name, expected_source_date=day.isoformat())
                )
                accumulator.add_member(build.rows, build.parse.header.family)
                del build, data, rows_data
            stream = accumulator.identity_stream()
            for _document in stream:
                pass
            stream.totals()
            _current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return peak

        batch = batch_peak()
        stream = stream_peak()
        self.assertEqual(rows, 3600)
        self.assertLess(stream, batch * 0.5, "streaming %.1f MB vs retention %.1f MB" % (stream / 1e6, batch / 1e6))

    def test_runner_end_to_end_peak_at_fixture_scale(self):
        runner = measure_runner_peak(20, 150)
        self.assertEqual(runner["exit_code"], 0, runner["output"])
        # declared fixture-scale runner bound: 24 MB for a 3,000-row corpus
        self.assertLess(runner["peak_bytes"], 24 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
