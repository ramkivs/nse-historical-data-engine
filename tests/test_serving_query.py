"""Serving slice — Q3 instrument query semantics, determinism, rebuild (D23 §18 #4/#7/#8).

All cases run against the synthetic fixture package (tests/serving_fixtures.py) —
never against, or represented as, the qualified M2 baseline.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest

from tests import serving_fixtures
from serving.baseline import open_baseline
from serving.index import (
    INDEX_FILENAME,
    INDEX_DIGEST_FILENAME,
    ServingIndexError,
    build_index,
    load_index,
    write_index,
)
from serving.query import QueryError, query_instrument
from serving.rebuild import rebuild_state


def make_variant_package(src_pkg: str, dst_pkg: str, spec) -> object:
    """Copy ``src_pkg`` to ``dst_pkg`` with one published price changed, re-pointing
    the partition manifest, package manifest and completion marker so the variant
    verifies as self-consistent with a different manifest identity. Test-only."""
    import hashlib
    import json as _json
    import shutil

    shutil.copytree(src_pkg, dst_pkg)
    target = os.path.join(dst_pkg, "partitions/legacy13/2016/rows/fix-leg-2016-01-05.csv.rows.jsonl")
    with open(target, "r", encoding="utf-8") as handle:
        text = handle.read()
    with open(target, "w", encoding="utf-8", newline="") as handle:
        handle.write(text.replace("1040.00", "1041.00"))

    def sha(path):
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()

    # re-point the partition manifest entry for the changed file
    part_manifest = os.path.join(dst_pkg, "manifests/legacy13_2016.sha256")
    lines = []
    with open(part_manifest, "r", encoding="utf-8") as handle:
        for line in handle.read().splitlines():
            digest, relative = line.split("  ", 1)
            if relative == "partitions/legacy13/2016/rows/fix-leg-2016-01-05.csv.rows.jsonl":
                digest = sha(os.path.join(dst_pkg, relative.replace("/", os.sep)))
            lines.append("%s  %s" % (digest, relative))
    with open(part_manifest, "w", encoding="utf-8", newline="") as handle:
        handle.write("".join(line + "\n" for line in lines))

    # regenerate the package manifest over every retained file
    manifest_path = os.path.join(dst_pkg, "PACKAGE_MANIFEST.sha256")
    marker_path = os.path.join(dst_pkg, "RUN_COMPLETE.json")
    entries = []
    for dirpath, dirnames, filenames in os.walk(dst_pkg):
        dirnames.sort()
        for name in sorted(filenames):
            relative = os.path.relpath(os.path.join(dirpath, name), dst_pkg).replace(os.sep, "/")
            if relative in ("PACKAGE_MANIFEST.sha256", "RUN_COMPLETE.json"):
                continue
            entries.append("%s  %s" % (sha(os.path.join(dirpath, name)), relative))
    manifest_text = "".join(line + "\n" for line in sorted(entries))
    with open(manifest_path, "w", encoding="utf-8", newline="") as handle:
        handle.write(manifest_text)
    manifest_digest = hashlib.sha256(manifest_text.encode("utf-8")).hexdigest()

    with open(marker_path, "r", encoding="utf-8") as handle:
        marker = _json.load(handle)
    marker["package_manifest_sha256"] = manifest_digest
    with open(marker_path, "w", encoding="utf-8", newline="") as handle:
        handle.write(_json.dumps(marker, sort_keys=True, separators=(",", ":")) + "\n")

    from dataclasses import replace

    return replace(spec, manifest_sha256=manifest_digest)


class QueryBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="d24-serving-query-")
        self.pkg = os.path.join(self.root, "pkg")
        self.state = os.path.join(self.root, "state")
        self.facts = serving_fixtures.build_fixture_package(self.pkg)
        self.spec = self.facts["spec"]
        self.handle = open_baseline(self.pkg, spec=self.spec)
        self.index = build_index(self.handle)
        write_index(self.state, self.index)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)


class Q3InstrumentQueryTests(QueryBase):
    def test_instrument_key_is_exact_as_published_per_family(self):
        # Q3 matches the as-published (listing_symbol, series) — never normalised,
        # and never conflated across families. In legacy13 listing_symbol is SYMBOL
        # ("RELIANCE"); in udiff34 it is FinInstrmId ("500325") while the ticker
        # sits in underlying_symbol (TckrSymb) (D05 §3.1 field map). An ISIN-based
        # cross-family correlation is NOT authorized by Q3 (ISIN is a non-identity
        # attribute — D16-10 Q3).
        legacy = query_instrument(self.handle, self.index, "RELIANCE", "EQ")
        self.assertEqual([r["business_date"] for r in legacy], ["2016-01-04", "2016-01-05", "2017-02-06"])
        self.assertEqual([r["format_family"] for r in legacy], ["legacy13"] * 3)
        udiff = query_instrument(self.handle, self.index, "500325", "EQ")
        self.assertEqual([r["business_date"] for r in udiff], ["2024-03-05"])
        self.assertEqual([r["format_family"] for r in udiff], ["udiff34"])
        # the same underlying company is visible as the udiff row's underlying_symbol
        self.assertEqual(udiff[0]["source_values"]["underlying_symbol"], "RELIANCE")

    def test_as_published_values_are_served_exactly(self):
        first = query_instrument(self.handle, self.index, "RELIANCE", "EQ")[0]
        values = first["source_values"]
        # exact published text — no float conversion, no rescaling (D05 §3.1/§10)
        self.assertEqual(values["price_open"], "1000.00")
        self.assertEqual(values["price_close"], "1040.00")
        self.assertEqual(values["traded_quantity"], "1200000")
        self.assertEqual(values["listing_symbol"], "RELIANCE")
        self.assertEqual(values["series"], "EQ")
        self.assertEqual(first["business_date"], "2016-01-04")
        # raw retained line is NOT part of the served view (D16-08; D24 record)
        self.assertNotIn("raw_line", first)

    def test_absent_field_is_none_and_blank_field_is_empty_string(self):
        legacy = query_instrument(self.handle, self.index, "RELIANCE", "EQ", year=2016)[0]
        udiff = query_instrument(self.handle, self.index, "500325", "EQ", year=2024)[0]
        # security_name: absent in legacy13 (None), present in udiff34 (published text)
        self.assertIsNone(legacy["source_values"]["security_name"])
        self.assertEqual(udiff["source_values"]["security_name"], "RELIANCE INDUSTRIES LTD")
        # remarks: blank in the udiff fixture row — stays blank, never defaulted (D05 §2 rule 3)
        self.assertEqual(udiff["source_values"]["remarks"], "")
        # blank ISIN is carried with its informational validity category (never gating)
        wipro = query_instrument(self.handle, self.index, "WIPRO", "EQ")
        self.assertEqual(len(wipro), 1)
        self.assertEqual(wipro[0]["source_values"]["security_isin"], "")
        self.assertEqual(wipro[0]["isin_validity"], "BLANK")

    def test_series_is_part_of_the_instrument_key(self):
        # a query for a series the instrument does not carry returns nothing,
        # even though the symbol exists
        self.assertEqual(query_instrument(self.handle, self.index, "RELIANCE", "BE"), ())
        rows = query_instrument(self.handle, self.index, "RELIANCE", "EQ")
        self.assertEqual(len(rows), 3)

    def test_unknown_instrument_returns_empty_tuple_not_error(self):
        self.assertEqual(query_instrument(self.handle, self.index, "NOPE", "EQ"), ())

    def test_year_filter_restricts_to_the_partition(self):
        rows_2016 = query_instrument(self.handle, self.index, "RELIANCE", "EQ", year=2016)
        self.assertEqual([r["business_date"] for r in rows_2016], ["2016-01-04", "2016-01-05"])
        rows_2017 = query_instrument(self.handle, self.index, "RELIANCE", "EQ", year=2017)
        self.assertEqual([r["business_date"] for r in rows_2017], ["2017-02-06"])
        rows_2024 = query_instrument(self.handle, self.index, "500325", "EQ", year=2024)
        self.assertEqual([r["business_date"] for r in rows_2024], ["2024-03-05"])

    def test_results_carry_row_provenance_and_serving_envelope(self):
        rows = query_instrument(self.handle, self.index, "RELIANCE", "EQ")
        first = rows[0]
        provenance = first["provenance"]
        self.assertEqual(provenance["source_archive"], "fix-leg-2016-01-04.csv")
        self.assertEqual(provenance["member_name"], "fix-leg-2016-01-04.csv")
        self.assertEqual(provenance["format_family"], "legacy13")
        self.assertEqual(provenance["spec_version"], "D05/1.0")
        self.assertEqual(provenance["tool_sha256"], self.facts["engine_tool_sha256"])
        self.assertEqual(provenance["run_id"], serving_fixtures.FIXTURE_RUN_ID)
        self.assertTrue(provenance["member_sha256_raw_bytes"])
        self.assertTrue(provenance["member_sha256_lf_text"])
        self.assertEqual(first["serving"]["query"], "Q3-instrument")
        self.assertEqual(first["serving"]["source_file"], "partitions/legacy13/2016/rows/fix-leg-2016-01-04.csv.rows.jsonl")

    def test_query_rejects_non_string_inputs(self):
        with self.assertRaises(QueryError):
            query_instrument(self.handle, self.index, 42, "EQ")


class IndexDeterminismTests(QueryBase):
    def test_two_independent_builds_are_byte_identical(self):
        first = build_index(self.handle)
        second = build_index(self.handle)
        from serving.index import canonical_json

        self.assertEqual(canonical_json(first), canonical_json(second))

    def test_rebuild_after_deletion_is_byte_identical(self):
        before = write_index(self.state, build_index(self.handle))
        os.remove(os.path.join(self.state, INDEX_FILENAME))
        os.remove(os.path.join(self.state, INDEX_DIGEST_FILENAME))
        report = rebuild_state(self.handle, self.state)
        # deleting class (4) is never a data event: the rebuild reproduces the
        # exact bytes that deletion removed (D16-07)
        self.assertIsNone(report["before_sha256"])
        self.assertEqual(report["after_sha256"], before)
        self.assertEqual(report["rows_scanned"], serving_fixtures.EXPECTED_TOTAL_ROWS)
        self.assertEqual(report["files_scanned"], 4)

    def test_rebuild_on_unchanged_baseline_reports_identical(self):
        report = rebuild_state(self.handle, self.state)
        self.assertTrue(report["identical"])

    def test_index_embeds_package_identity_and_counts(self):
        self.assertEqual(self.index["package"]["manifest_sha256"], self.spec.manifest_sha256)
        self.assertEqual(self.index["package"]["run_id"], serving_fixtures.FIXTURE_RUN_ID)
        self.assertEqual(self.index["counts"]["row_count"], serving_fixtures.EXPECTED_TOTAL_ROWS)
        self.assertEqual(len(self.index["partitions"]), serving_fixtures.EXPECTED_PARTITIONS)
        self.assertEqual(self.index["partitions"]["legacy13/2016"]["row_files"], 2)
        self.assertEqual(self.index["partitions"]["legacy13/2016"]["row_count"], 5)

    def test_no_clock_path_or_host_value_in_index(self):
        from serving.index import canonical_json

        text = canonical_json(self.index)
        import re

        self.assertIsNone(re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", text))  # no ISO timestamps
        self.assertNotIn(self.root, text)  # no absolute paths
        self.assertNotIn("/home/", text)


class StaleIndexTests(QueryBase):
    def test_index_from_a_different_package_is_refused(self):
        # Build a content-different but self-consistent variant package, then show
        # that the index built for the original is refused against it (the baseline
        # is the source of truth; the remedy is a rebuild — D16-07 conflict rule).
        other_pkg = os.path.join(self.root, "pkg2")
        other_spec = make_variant_package(self.pkg, other_pkg, self.spec)
        other_handle = open_baseline(other_pkg, spec=other_spec)
        load_index(self.state, self.handle)  # the original index is fine for the original
        with self.assertRaises(ServingIndexError) as ctx:
            load_index(self.state, other_handle)
        self.assertEqual(ctx.exception.check, "index-stale")
        # and the rebuilt index for the variant serves the variant
        report = rebuild_state(other_handle, self.state)
        self.assertFalse(report["identical"])
        document, _digest = load_index(self.state, other_handle)
        rows = query_instrument(other_handle, document, "RELIANCE", "EQ")
        self.assertEqual(len(rows), 3)

    def test_corrupt_index_sidecar_is_refused(self):
        path = os.path.join(self.state, INDEX_DIGEST_FILENAME)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write("0" * 64 + "  " + INDEX_FILENAME + "\n")
        with self.assertRaises(ServingIndexError) as ctx:
            load_index(self.state, self.handle)
        self.assertEqual(ctx.exception.check, "index-load")

    def test_rebuild_refuses_to_delete_unknown_state_files(self):
        with open(os.path.join(self.state, "not-ours.txt"), "w", encoding="utf-8") as handle:
            handle.write("x\n")
        with self.assertRaises(ServingIndexError) as ctx:
            rebuild_state(self.handle, self.state)
        self.assertEqual(ctx.exception.check, "rebuild-refuse")


if __name__ == "__main__":
    unittest.main()
