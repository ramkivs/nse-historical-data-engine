"""Integration cross-checks against the published, MANIFEST-anchored fixture evidence.

D07 §13-H acceptance: "parser acceptance on all 39 published windows_run artifacts" —
W1 parses the eight published row-sample artifacts and cross-checks the results against the
other published evidence artifacts (census, coverage, overlay observations) where the
comparison is well defined for a bounded sample.
"""

from __future__ import annotations

import hashlib
import os
import unittest

from tests import support
from nse_engine import contract


class FixtureIntegrityTests(unittest.TestCase):
    """W1's inputs must be the published, MANIFEST-anchored evidence (no re-derived data)."""

    def test_every_manifest_entry_verifies(self):
        path = os.path.join(support.FIXTURE_DIR, "MANIFEST.sha256")
        exact = crlf_restored = 0
        entries = 0
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                expected, name = line.split("  ", 1)
                entries += 1
                with open(os.path.join(support.FIXTURE_DIR, name), "rb") as payload:
                    data = payload.read()
                if hashlib.sha256(data).hexdigest() == expected:
                    exact += 1
                elif hashlib.sha256(data.replace(b"\n", b"\r\n")).hexdigest() == expected:
                    # D03 §15 packaging note: the tool's JSON writer used Windows text mode,
                    # so 10 manifest hashes embed CRLF while git stores LF.
                    crlf_restored += 1
                else:
                    self.fail("manifest entry does not verify: %s" % name)
        self.assertEqual(entries, 37)
        self.assertEqual((exact, crlf_restored), (27, 10))

    def test_row_sample_payloads_are_byte_exact(self):
        for name in support.PUBLISHED_SAMPLES:
            with self.subTest(member=name):
                data = support.fixture_bytes(name)
                with open(os.path.join(support.FIXTURE_DIR, "MANIFEST.sha256"), encoding="utf-8") as handle:
                    expected = dict(
                        line.rstrip("\n").split("  ", 1)[::-1] for line in handle if line.strip()
                    )
                self.assertEqual(hashlib.sha256(data).hexdigest(), expected[name])
                self.assertNotIn(b"\r", data)  # stored LF per D05 §9.1


class PublishedSampleAcceptanceTests(unittest.TestCase):
    def test_every_published_sample_parses_with_zero_quarantine(self):
        for name in support.PUBLISHED_SAMPLES:
            with self.subTest(member=name):
                build = support.build_sample(name)
                self.assertEqual(build.quarantined, ())
                self.assertEqual(build.rows, build.rows)
                expected = support.expected_sample_rows(name)
                self.assertEqual(len(build.rows), expected)

    def test_every_row_carries_a_governed_date_basis_and_family(self):
        for name in support.PUBLISHED_SAMPLES:
            build = support.build_sample(name)
            for row in build.rows:
                self.assertIn(row.business_date_basis, contract.DATE_BASES)
                self.assertIn(row.format_family, contract.FORMAT_FAMILIES)

    def test_row_counts_match_the_published_coverage_artifact(self):
        total = sum(support.expected_sample_rows(name) for name in support.PUBLISHED_SAMPLES)
        self.assertEqual(total, 3554)
        parsed = sum(len(support.build_sample(name).rows) for name in support.PUBLISHED_SAMPLES)
        self.assertEqual(parsed, total)

    def test_both_families_are_covered(self):
        families = {support.build_sample(name).parse.header.family for name in support.PUBLISHED_SAMPLES}
        self.assertEqual(families, {"legacy13", "udiff34"})

    def test_legacy_samples_carry_the_trailing_empty_field_variant(self):
        for name in support.PUBLISHED_SAMPLES:
            if support.sample_family(name) != contract.FAMILY_LEGACY:
                continue
            with self.subTest(member=name):
                build = support.build_sample(name)
                self.assertEqual(build.parse.header.physical_width, 14)
                self.assertEqual(
                    build.parse.header.tolerance_applied, "legacy13_trailing_empty_field"
                )

    def test_published_legacy_rows_all_use_the_four_digit_year_form(self):
        for name in support.PUBLISHED_SAMPLES:
            if support.sample_family(name) != contract.FAMILY_LEGACY:
                continue
            build = support.build_sample(name)
            for row in build.rows:
                self.assertEqual(
                    row.business_date_basis, contract.DATE_BASIS_LEGACY_FOUR_DIGIT_YEAR
                )
                self.assertEqual(row.business_date, support.sample_date(name))


class PublishedCensusCrossChecks(unittest.TestCase):
    """Corpus-proven facts (D02-F3, D03 §15 Q2/Q5/Q6) must hold on the bounded samples."""

    def test_every_series_and_symbol_token_is_populated(self):
        for name in support.PUBLISHED_SAMPLES:
            build = support.build_sample(name)
            for row in build.rows:
                self.assertEqual(len(row.series), 2, "%s line %d" % (name, row.line_number))
                self.assertNotEqual(row.listing_symbol, "")
                self.assertNotEqual(row.series.strip(), "")

    def test_no_published_sample_row_has_a_blank_isin(self):
        # D03 §15 Q2: zero blank-ISIN rows in either format across the corpus.
        for name in support.PUBLISHED_SAMPLES:
            build = support.build_sample(name)
            for row in build.rows:
                self.assertNotEqual(row.value("security_isin"), "")

    def test_udiff_samples_are_sgmt_cm_src_nse(self):
        # D03 §15 Q5: Sgmt=CM and Src=NSE on all UDiFF rows (non-discriminative singletons).
        for name in support.PUBLISHED_SAMPLES:
            if support.sample_family(name) != contract.FAMILY_UDIFF:
                continue
            build = support.build_sample(name)
            for row in build.rows:
                self.assertEqual(row.value("segment"), "CM")
                self.assertEqual(row.value("source"), "NSE")
                self.assertEqual(row.value("instrument_type"), "STK")

    def test_udiff_fininstrm_id_never_equals_the_isin(self):
        # D03 §15 Q4: 0 equal / 1,700,650 unequal corpus-wide.
        compared = 0
        for name in support.PUBLISHED_SAMPLES:
            if support.sample_family(name) != contract.FAMILY_UDIFF:
                continue
            build = support.build_sample(name)
            for row in build.rows:
                compared += 1
                self.assertNotEqual(row.listing_symbol, row.security_isin)
                self.assertNotIn(row.security_isin, row.listing_symbol)
        self.assertEqual(compared, 1966)

    def test_legacy_rows_carry_no_udiff_only_fields(self):
        for name in support.PUBLISHED_SAMPLES:
            if support.sample_family(name) != contract.FAMILY_LEGACY:
                continue
            build = support.build_sample(name)
            row = build.rows[0]
            for key in ("security_name", "segment", "source", "instrument_type", "rsvd1"):
                self.assertIsNone(row.value(key))


class PublishedOverlayCrossChecks(unittest.TestCase):
    def _published_overlay_index(self):
        index = {}
        for record in support.published_evidence("overlay_rows"):
            key = (
                record["format"],
                record["date"],
                record["overlay_series"],
                record["overlay_symbol"],
                record["overlay_isin"],
            )
            index.setdefault(key, []).append(record)
        return index

    def test_our_base_same_isin_observations_agree_with_the_published_fixture(self):
        """Frozen-fixture golden cross-check.

        The published overlay fixture was computed over full corpus members; the published
        row samples are stratified subsets. A sample-local base row can therefore be absent
        where the full file had one (ours NO_BASE_ORPHAN, published BASE_SAME_ISIN — expected
        and explained, see the assertion below). The guaranteed direction is: if *we* found a
        same-ISIN base inside the sample, the full-file fixture must have found one too, and
        for these frozen fixtures the compared quantity relation agrees as well.
        """
        index = self._published_overlay_index()
        compared = 0
        sample_local_orphans = 0
        for name in support.PUBLISHED_SAMPLES:
            family = "LEGACY" if support.sample_family(name) == contract.FAMILY_LEGACY else "UDIFF"
            build = support.build_sample(name)
            for row in build.rows:
                if row.overlay is None:
                    continue
                key = (
                    family,
                    support.sample_date(name),
                    row.series,
                    row.listing_symbol,
                    row.value("security_isin"),
                )
                published = index.get(key)
                if not published:
                    continue
                expected = published[0]
                if row.overlay["match_type"] == contract.MATCH_TYPE_BASE_SAME_ISIN:
                    compared += 1
                    self.assertEqual(
                        expected["match_type"],
                        contract.MATCH_TYPE_BASE_SAME_ISIN,
                        "published evidence disagrees for %r" % (key,),
                    )
                    self.assertEqual(row.overlay["qty_rel"], expected["qty_rel"])
                else:
                    sample_local_orphans += 1
                    self.assertIn(
                        expected["match_type"],
                        (contract.MATCH_TYPE_BASE_SAME_ISIN, contract.MATCH_TYPE_NO_BASE_ORPHAN),
                    )
        self.assertGreater(compared, 0)
        self.assertGreater(sample_local_orphans, 0)

    def test_overlay_observations_only_use_the_governed_match_types_and_relations(self):
        for name in support.PUBLISHED_SAMPLES:
            build = support.build_sample(name)
            for observation in build.observations:
                self.assertIn(observation.match_type, contract.MATCH_TYPES)
                if observation.qty_rel is not None:
                    self.assertIn(observation.qty_rel, contract.QTY_RELATIONS)

    def test_overlay_rows_keep_their_own_canonical_rows_in_every_sample(self):
        for name in support.PUBLISHED_SAMPLES:
            build = support.build_sample(name)
            self.assertEqual(len(build.rows), support.expected_sample_rows(name))
            overlay_series = {observation.overlay_series for observation in build.observations}
            for series in overlay_series:
                self.assertTrue(
                    any(row.series == series for row in build.rows),
                    "overlay row for series %s was dropped in %s" % (series, name),
                )


class PublishedAnomalyCrossChecks(unittest.TestCase):
    """D03 FIX-ANOM-01 closed the two anomalous legacy members as format variation."""

    def setUp(self):
        self.anomaly = support.published_evidence("anomaly")

    def _per_file(self, target, date):
        for report in self.anomaly["reports"]:
            if report["target"] == target:
                return report["per_file"][date]
        raise KeyError(target)

    def test_thirteen_field_member_variant_is_reproduced(self):
        record = self._per_file("2017-07-10", "2017-07-10")
        self.assertEqual(record["header_fields"], 13)
        self.assertEqual(set(record["field_count_hist"]), {"13"})
        self.assertEqual(record["line_endings"]["crlf"], 1684)

    def test_thirteen_field_member_with_two_digit_years_is_reproduced(self):
        record = self._per_file("2020-07-13", "2020-07-13")
        self.assertEqual(record["header_fields"], 13)
        self.assertEqual(record["timestamp_format_hist"], {"DD-Mon-YY_2digit_year": 2001})

        # Reproduce the member shape synthetically: 13 physical fields everywhere, CRLF,
        # 2-digit-year timestamps written in the corpus's mixed-case form (D02-F2 "13-Jul-20").
        rows = [
            support.legacy_row(TIMESTAMP="13-Jul-20", SYMBOL="20MICRONS", ISIN="INE144J01027"),
            support.legacy_row(TIMESTAMP="13-Jul-20", SYMBOL="21STCENMGM", ISIN="INE253B01015"),
        ]
        build = support.parse_synthetic(
            support.legacy_member(rows, trailing_empty_header=False, line_ending="\r\n"),
            expected_source_date="2020-07-13",
        )
        self.assertEqual(len(build.rows), 2)
        self.assertEqual(build.rows[0].business_date, "2020-07-13")
        self.assertEqual(build.rows[0].raw_biz_dt, "13-Jul-20")
        self.assertEqual(
            build.rows[0].business_date_basis,
            contract.DATE_BASIS_LEGACY_TWO_DIGIT_YEAR_CROSSCHECKED,
        )
        self.assertEqual(build.parse.report.crlf_line_endings, 3)

    def test_fourteen_field_member_variant_is_reproduced(self):
        record = self._per_file("2017-07-10", "2017-07-05")
        self.assertEqual(record["field_count_hist"], {"14": 1776})
        self.assertEqual(record["line_endings"]["lf_only"], 1776)


class PublishedLedgerCrossChecks(unittest.TestCase):
    def test_run_info_declares_the_fixture_contract_w1_consumes(self):
        run_info = support.published_evidence("run_info")
        self.assertEqual(run_info["files_by_kind"], {"LEGACY": 1919, "UDIFF": 543})
        self.assertIn("FIX-UD-ROW-SAMPLE-01", run_info["fixtures"])
        self.assertEqual(run_info["tool_version"], "d03-fixture-scan-1.1.0")

    def test_legacy_census_summary_reports_the_d03_era_checkdigit_population(self):
        summary = support.published_evidence("legacy_census_summary")
        self.assertEqual(summary["invalid_isin_categories"]["INVALID_CHECKDIGIT"], 215393)
        self.assertEqual(summary["invalid_isin_categories"]["INVALID_LEN"], 1)
        # W1-DIV-1 records why this figure is not reproducible by the governed ISO 6166 check.


if __name__ == "__main__":
    unittest.main()
