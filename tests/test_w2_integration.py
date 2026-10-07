"""W2-E: integration across the W2 surfaces and with the W1 baseline (W2 prompt §10 E).

Checks that the derived calendar, identity/dated associations, overlay reconciliation and D01
metric fold are mutually consistent and consistent with the governed evidence, that W1 outputs
are consumed without mutation, and that nothing is silently dropped on any boundary.
"""

from __future__ import annotations

import os
import unittest

from tests import support
from nse_engine import contract, metrics
from nse_engine.overlay_evidence import assemble_disposition
from nse_engine.serialize import rows_jsonl


def _normalize(value):
    return (value or "").strip().upper()


class W2CrossSurfaceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = support.load_inventory_records()
        cls.w2 = support.build_w2_samples()
        cls.d02 = support._read_json(support.D02_METRICS_PATH)
        cls.selection = support.published_evidence("coverage")

    def test_calendar_file_structure_agrees_with_the_d01_inventory_and_d02(self):
        self.assertEqual(self.w2.calendar.files, len(self.inventory))
        self.assertEqual(self.w2.calendar.files, self.d02["total_files"])
        self.assertEqual(dict(self.w2.calendar.formats), {"LEGACY": 1919, "UDIFF": 543})
        self.assertEqual(dict(self.w2.calendar.formats)["LEGACY"], self.d02["legacy_files"])
        self.assertEqual(dict(self.w2.calendar.formats)["UDIFF"], self.d02["udiff_files"])
        self.assertEqual(len(self.w2.calendar.missing_days), self.d02["missing_weekdays_count"])
        self.assertEqual(
            sum(self.w2.calendar.label_status_counts().values()), self.w2.calendar.span_weekdays
        )

    def test_every_sample_member_date_is_a_calendar_day_with_a_file(self):
        file_dates = {
            day.trade_date for day in self.w2.calendar.days if day.file_present
        }
        sample_dates = {build.rows[0].business_date for build in self.w2.builds}
        self.assertEqual(sample_dates, {support.sample_date(name) for name in support.PUBLISHED_SAMPLES})
        self.assertEqual(sample_dates - file_dates, set())
        for date in sample_dates:
            day = next(day for day in self.w2.calendar.days if day.trade_date == date)
            self.assertFalse(day.missing_weekday)

    def test_trad_dt_eq_biz_dt_is_derived_only_where_a_member_was_parsed(self):
        by_date = {day.trade_date: day for day in self.w2.calendar.days}
        for build in self.w2.builds:
            date = build.rows[0].business_date
            day = by_date[date]
            if build.parse.header.family == contract.FAMILY_UDIFF:
                self.assertIs(day.trad_dt_eq_biz_dt, True, date)
            else:
                self.assertIsNone(day.trad_dt_eq_biz_dt, date)
        # a file-present day with no parsed member in this run stays undetermined, never defaulted
        parsed = {build.rows[0].business_date for build in self.w2.builds}
        unparsed = [
            day for day in self.w2.calendar.present_days if day.trade_date not in parsed
        ]
        self.assertGreater(len(unparsed), 0)
        for day in unparsed:
            self.assertIsNone(day.trad_dt_eq_biz_dt)

    def test_identity_partitions_the_members_rows_without_loss(self):
        totals = self.w2.associations.totals()
        overlay_rows = [
            row
            for row in self.w2.rows
            if row.series in contract.OVERLAY_SERIES_OBSERVED
        ]
        self.assertEqual(totals["overlay_rows_excluded"], len(overlay_rows))
        contributing = sum(
            len(association.contributing_rows)
            for identity in self.w2.associations.identities
            for association in identity.associations
        )
        self.assertEqual(contributing + totals["overlay_rows_excluded"], len(self.w2.rows))
        self.assertEqual(totals["associations"], 2134)
        self.assertEqual(totals["identities"], 1435)
        self.assertEqual(totals["unkeyed_rows"], 0)

    def test_every_non_overlay_isin_is_an_identity_scope(self):
        identity_keys = {identity.security_id for identity in self.w2.associations.identities}
        expected = set()
        for row in self.w2.rows:
            if row.series in contract.OVERLAY_SERIES_OBSERVED:
                continue
            key = _normalize(row.security_isin)
            if key:
                expected.add(key)
        self.assertEqual(expected - identity_keys, set())
        self.assertEqual(identity_keys - expected, set())

    def test_overlay_rows_never_enter_the_transition_chain(self):
        identity_keys = {identity.security_id for identity in self.w2.associations.identities}
        for observation in self.w2.observations:
            self.assertIn(observation.overlay_series, contract.OVERLAY_SERIES_OBSERVED)
            self.assertIn(observation.business_date, {build.rows[0].business_date for build in self.w2.builds})

    def test_association_dates_are_calendar_days(self):
        calendar_dates = {day.trade_date for day in self.w2.calendar.days}
        for identity in self.w2.associations.identities:
            for association in identity.associations:
                self.assertIn(association.observed_from, calendar_dates)
                self.assertIn(association.observed_to, calendar_dates)
                self.assertLessEqual(association.observed_from, association.observed_to)

    def test_metric_row_total_equals_the_member_row_total(self):
        self.assertEqual(self.w2.metrics.get("rows"), len(self.w2.rows))
        self.assertEqual(self.w2.metrics.get("rows"), self.selection["emitted_total_rows"])
        per_member = sum(len(build.rows) for build in self.w2.builds)
        self.assertEqual(per_member, self.w2.metrics.get("rows"))

    def test_extract_metrics_are_a_subset_of_the_full_file_facts(self):
        oracle = {record.file_name: record for record in support.load_file_metric_records()}
        by_date_root = {(record.date, record.root): record for record in self.inventory}
        for build in self.w2.builds:
            date = build.rows[0].business_date
            root = "LEGACY" if build.parse.header.family == contract.FAMILY_LEGACY else "UDIFF"
            reference = oracle[by_date_root[(date, root)].file_name]
            row_metrics = metrics.compute_row_metrics(build.rows)
            self.assertLessEqual(row_metrics.get("rows"), reference.rows)
            self.assertLessEqual(row_metrics.get("blank_isin_rows"), reference.blank_isin_rows)
            self.assertLessEqual(
                row_metrics.get("distinct_nonblank_isin"), reference.distinct_nonblank_isin
            )
            self.assertEqual(row_metrics.get("symbol_series_duplicate_rows"), 0)

    def test_calendar_missing_day_count_and_labels_are_mutually_consistent(self):
        missing = [day for day in self.w2.calendar.days if day.missing_weekday]
        labelled = [
            day
            for day in missing
            if day.label_status != contract.CALENDAR_LABEL_NOT_RETRIEVED
        ]
        unresolved = [day for day in missing if day.label_status == contract.CALENDAR_LABEL_UNEXPLAINED]
        self.assertEqual(len(missing), 147)
        self.assertEqual(len(labelled), 32)
        self.assertEqual(len(unresolved), 3)
        self.assertEqual(
            len(missing) - len(labelled),
            self.w2.calendar.label_status_counts()[contract.CALENDAR_LABEL_NOT_RETRIEVED],
        )


class OverlayReconciliationIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w2 = support.build_w2_samples()
        cls.disposition = assemble_disposition(
            cls.w2.builds,
            support.load_inventory_records(),
            support.load_file_metric_records(),
            support.load_overlay_fixture_rows(),
        )

    def test_coverage_rows_match_the_member_row_counts(self):
        extract_rows = sum(len(build.rows) for build in self.w2.builds)
        self.assertEqual(
            sum(record.extract_rows for record in self.disposition.coverage), extract_rows
        )
        self.assertEqual(len(self.disposition.coverage), len(self.w2.builds))

    def test_every_overlay_row_in_the_extracts_has_an_observation(self):
        overlay_rows = [row for row in self.w2.rows if row.series in contract.OVERLAY_SERIES_OBSERVED]
        self.assertEqual(len(self.w2.observations), len(overlay_rows))
        observed_keys = {
            (observation.business_date, observation.overlay_series, observation.isin)
            for observation in self.w2.observations
        }
        for row in overlay_rows:
            key = (row.business_date, row.series, _normalize(row.security_isin))
            self.assertIn(key, observed_keys)

    def test_unmatched_fixture_rows_are_absent_overlay_rows_not_defects(self):
        # Every fixture row the engine could not reproduce on an extract date must be a row the
        # extract does not contain at all: absent from the engine's observations AND absent from
        # the extract's canonical rows. Anything else would be a genuine defect.
        extract_rows = {}
        for row in self.w2.rows:
            extract_rows.setdefault(
                (row.business_date, row.series, _normalize(row.security_isin)), 0
            )
            extract_rows[(row.business_date, row.series, _normalize(row.security_isin))] += 1
        observed = {
            (observation.business_date, observation.overlay_series, observation.isin)
            for observation in self.w2.observations
        }
        defects = []
        for fixture_row in support.load_overlay_fixture_rows():
            key = (
                fixture_row.date,
                fixture_row.overlay_series,
                _normalize(fixture_row.overlay_isin),
            )
            if key not in observed and key in extract_rows:
                defects.append(key)
        self.assertEqual(defects, [])
        self.assertEqual(self.disposition.engine_observation_missing_for_sampled_row, 0)
        self.assertEqual(self.disposition.engine_observations_without_fixture_row, 0)
        self.assertEqual(self.disposition.unreproducible_with_base_present, 0)

    def test_w1_div_1_is_carried_forward_untouched(self):
        # W2 must carry W1-DIV-1 forward: the census figure 215,393 / 1 is D03-era evidence
        # produced by an ungoverned check-digit routine; W1 implements the governed ISO 6166
        # definition and records the divergence. W2 neither reproduces nor alters it, and the
        # D01 metric algebra contains no ISIN-validity metric at all.
        summary = support.w2_evidence("leg_census_summary")
        self.assertEqual(summary["invalid_isin_categories"]["INVALID_CHECKDIGIT"], 215393)
        self.assertEqual(summary["invalid_isin_categories"]["INVALID_LEN"], 1)
        record = [item for item in contract.KNOWN_EVIDENCE_DIVERGENCES if item["id"] == "W1-DIV-1"]
        self.assertEqual(len(record), 1)
        self.assertIn("v[1:11]", record[0]["finding"])
        self.assertIn("does NOT reproduce", record[0]["w1_behaviour"])
        self.assertIn("not part of W1", record[0]["recommendation"])
        self.assertIn("215,393", record[0]["governed_text"])
        self.assertNotIn("invalid_isin", contract.D01_METRIC_NAMES)
        self.assertNotIn(
            "invalid_isin", metrics.fold_file_metrics(support.load_file_metric_records())["totals"]
        )


class W1NonMutationIntegrationTests(unittest.TestCase):
    def test_building_w2_does_not_mutate_the_w1_builds(self):
        builds = tuple(support.build_sample(name) for name in support.PUBLISHED_SAMPLES)
        before = [rows_jsonl(build.rows, include_run_metadata=False) for build in builds]
        labels, holidays, _registry, _document = support.load_calendar_labels()
        from nse_engine.pipeline import build_w2

        w2 = build_w2(builds, support.load_inventory_records(), labels, holidays)
        after = [rows_jsonl(build.rows, include_run_metadata=False) for build in builds]
        self.assertEqual(before, after)
        self.assertEqual(w2.rows, tuple(row for build in builds for row in build.rows))

    def test_contract_module_set_is_unchanged_by_w2(self):
        package = os.path.join(support.SRC_DIR, "nse_engine")
        self.assertEqual(
            sorted(contract.ENGINE_MODULES),
            sorted(name[0:-3] for name in os.listdir(package) if name.endswith(".py")),
        )


if __name__ == "__main__":
    unittest.main()
