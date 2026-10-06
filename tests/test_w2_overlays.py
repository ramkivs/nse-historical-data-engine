"""W2-C: overlay fixture accounting and the W1-DIV-OVERLAY disposition (W2 prompt §6, §10 C).

The disposition must be *determined* from evidence, not tuned: the disagreement counts are
preserved, the cause is mechanical, and the fail-closed branch (a genuine defect → cause stays
unresolved) is exercised with synthetic inputs. 37 / 39 are never forced to zero.
"""

from __future__ import annotations

import hashlib
import os
import unittest

from tests import support
from nse_engine import contract
from nse_engine.evidence_inputs import OverlayFixtureRow
from nse_engine.overlay_evidence import (
    account_overlay_fixture,
    assemble_disposition,
    determine_overlay_disposition,
)


class OverlayFixtureAccountingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = support.load_overlay_fixture_rows()
        cls.accounting = account_overlay_fixture(cls.rows)
        cls.fixture_path = os.path.join(support.FIXTURE_DIR, support.W2_EVIDENCE["overlay_rows"])

    def test_fixture_accounting_matches_the_published_aggregate(self):
        aggregate = support.w2_evidence("aggregate")
        self.assertEqual(self.accounting.total_rows, 3692)
        self.assertEqual(
            dict(self.accounting.counts_by_format_series_match_type),
            aggregate["counts_by_format_series_matchtype"],
        )
        self.assertEqual(self.accounting.base_same_isin_rows, 3356)
        self.assertEqual(self.accounting.no_base_orphan_rows, 336)
        self.assertEqual(
            self.accounting.base_same_isin_rows + self.accounting.no_base_orphan_rows,
            self.accounting.total_rows,
        )
        self.assertIn("does not classify overlays", aggregate["no_assumption"])
        guidance = aggregate["reading_guidance"]
        self.assertIn("BASE_BY_SYMBOL_ONLY", " ".join(guidance))
        self.assertNotIn("BASE_BY_SYMBOL_ONLY", {key.split("|")[2] for key, _ in self.accounting.counts_by_format_series_match_type})

    def test_fixture_totals_match_the_dec2_overlay_evidence(self):
        dec2 = support._read_json(support.DEC2_Q8_PATH)
        self.assertEqual(self.accounting.total_rows, dec2["per_row_published_rows"])
        self.assertEqual(self.accounting.orphans_by_series, (("BL", 3), ("IT", 333)))
        self.assertEqual(dict(self.accounting.orphans_by_series), dec2["orphans"])
        self.assertEqual(dict(self.accounting.qty_rel_counts), dec2["qty_rel_vs_same_day_base_row_for_same_isin"])
        self.assertIn("NOT established", dec2["t0_status"])

    def test_fixture_file_identity_matches_the_recorded_input_hash(self):
        dec2 = support._read_json(support.DEC2_Q8_PATH)
        with open(self.fixture_path, "rb") as handle:
            digest = hashlib.sha256(handle.read()).hexdigest()
        self.assertEqual(digest, dec2["input_hash"][os.path.basename(self.fixture_path)])

    def test_match_types_are_the_governed_enum(self):
        for key, _count in self.accounting.counts_by_format_series_match_type:
            _format, _series, match_type = key.split("|")
            self.assertIn(match_type, contract.MATCH_TYPES)

    def test_orphans_are_accounted_per_series_and_never_silently_dropped(self):
        for series, count in self.accounting.orphans_by_series:
            self.assertIn(series, contract.OVERLAY_SERIES_OBSERVED)
            self.assertGreater(count, 0)

    def test_quantity_relation_buckets_total_the_base_same_rows(self):
        total = sum(count for _key, count in self.accounting.qty_rel_counts)
        self.assertEqual(total, self.accounting.base_same_isin_rows)
        for key, _count in self.accounting.qty_rel_counts:
            series, qty_rel = key.split("|")
            self.assertIn(series, contract.OVERLAY_SERIES_OBSERVED)
            self.assertIn(qty_rel, ("gt", "lt", "eq", "undetermined"))
        # DEC-2 records no equal-quantity case; the engine must not manufacture one
        self.assertNotIn("eq", {key.split("|")[1] for key, _ in self.accounting.qty_rel_counts})

    def test_accounting_is_order_independent(self):
        reversed_rows = tuple(reversed(self.rows))
        self.assertEqual(
            account_overlay_fixture(self.rows).to_dict(),
            account_overlay_fixture(reversed_rows).to_dict(),
        )

    def test_empty_fixture_accounts_to_zero_without_error(self):
        accounting = account_overlay_fixture(())
        self.assertEqual(accounting.total_rows, 0)
        self.assertEqual(accounting.counts_by_format_series_match_type, ())


class OverlayDispositionOnThePublishedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w2 = support.build_w2_samples()
        cls.disposition = assemble_disposition(
            cls.w2.builds,
            support.load_inventory_records(),
            support.load_file_metric_records(),
            support.load_overlay_fixture_rows(),
        )

    def test_cause_is_fixture_truncation_from_source_coverage(self):
        self.assertEqual(self.disposition.cause, contract.W1_DIV_OVERLAY_CAUSE_FIXTURE_TRUNCATION)
        self.assertEqual(self.disposition.divergence_id, contract.W1_DIV_OVERLAY_ID)
        self.assertEqual(self.disposition.cause, "fixture_truncation_source_coverage")
        self.assertNotEqual(self.disposition.cause, contract.W1_DIV_OVERLAY_CAUSE_UNRESOLVED)

    def test_determination_is_explicit_and_not_an_elimination(self):
        document = self.disposition.to_dict()
        self.assertTrue(document["preserved_not_eliminated"])
        self.assertEqual(document["determination"], dict(contract.W1_DIV_OVERLAY_DETERMINATION))
        self.assertEqual(document["defect_count"], 0)
        self.assertIn("PRESERVED", document["determination"]["non_elimination"])
        self.assertIn("I4", document["determination"]["scope_limit"])

    def test_the_disagreement_is_reproduced_and_preserved_exactly(self):
        # The published corpus-wide fixture records 37 legacy verdict differences plus 39
        # unmatched rows (W1-DIV-OVERLAY). On the eight published extract dates the engine
        # reproduces 74 differing verdicts; all of them assert a base row that the extract does
        # not contain; 0 defects. The count is preserved verbatim, never tuned to zero.
        self.assertEqual(self.disposition.matched_diff_verdict, 74)
        self.assertEqual(self.disposition.unreproducible_with_base_absent, 74)
        self.assertEqual(self.disposition.unreproducible_with_base_present, 0)
        self.assertEqual(self.disposition.matched_same_verdict, 14)
        self.assertEqual(self.disposition.fixture_rows_on_extract_dates, 395)
        self.assertEqual(self.disposition.fixture_rows_row_not_in_extract, 307)
        self.assertEqual(self.disposition.engine_observations_without_fixture_row, 0)
        self.assertEqual(self.disposition.engine_observation_missing_for_sampled_row, 0)

    def test_every_engine_observation_has_a_fixture_row_at_the_same_key(self):
        self.assertEqual(self.disposition.engine_observations, 88)
        self.assertEqual(self.disposition.engine_observations_without_fixture_row, 0)

    def test_extract_coverage_is_recorded_per_date_and_is_small(self):
        self.assertEqual(len(self.disposition.coverage), len(support.PUBLISHED_SAMPLES))
        ratios = [record.coverage_ratio for record in self.disposition.coverage]
        self.assertEqual(round(min(ratios), 6), 0.128251)
        self.assertEqual(round(max(ratios), 6), 0.180781)
        self.assertLess(self.disposition.to_dict()["coverage_max"], 1.0)
        for record in self.disposition.coverage:
            self.assertLess(record.extract_rows, record.full_file_rows)
            self.assertEqual(
                record.coverage_ratio, record.extract_rows / record.full_file_rows
            )

    def test_disposition_carries_no_invented_matching_rule(self):
        text = repr(self.disposition.to_dict()).lower()
        for forbidden in ("symbol_only", "fuzzy", "tolerance", "fallback", "name_match"):
            self.assertNotIn(forbidden, text)
        self.assertEqual(contract.MATCH_BASIS_ISIN_NORMALIZED, "isin_normalized_upper_trim")
        self.assertEqual(contract.MATCH_TYPES, ("BASE_SAME_ISIN", "NO_BASE_ORPHAN"))


class OverlayFailClosedTests(unittest.TestCase):
    """A genuine defect must leave the cause unresolved (fail closed, never tuned)."""

    @classmethod
    def setUpClass(cls):
        cls.w2 = support.build_w2_samples()
        cls.fixture_rows = support.load_overlay_fixture_rows()
        cls._inputs_cache = None

    def _inputs(self):
        if self._inputs_cache is None:
            rows_by_date = {}
            observations = []
            for sample in support.PUBLISHED_SAMPLES:
                build = support.build_sample(sample)
                rows_by_date[build.rows[0].business_date] = list(build.rows)
                observations.extend(build.observations)
            type(self)._inputs_cache = (observations, rows_by_date)
        return self._inputs_cache

    def test_fixture_rows_outside_the_extract_assert_nothing(self):
        observations, rows_by_date = self._inputs()
        extract_dates = set(rows_by_date)
        outside = tuple(row for row in self.fixture_rows if row.date not in extract_dates)
        self.assertGreater(len(outside), 0)
        disposition = determine_overlay_disposition(observations, rows_by_date, outside, ())
        self.assertEqual(disposition.fixture_rows_row_not_in_extract, 0)
        self.assertEqual(disposition.fixture_rows_on_extract_dates, 0)
        # the engine's own observations still have no fixture row in this restricted input:
        # that defect is reported, and the cause therefore stays UNRESOLVED (fail closed).
        self.assertEqual(disposition.engine_observations_without_fixture_row, len(observations))
        self.assertEqual(disposition.cause, contract.W1_DIV_OVERLAY_CAUSE_UNRESOLVED)

    def test_base_present_but_still_unmatched_is_a_defect_and_stays_unresolved(self):
        observations, rows_by_date = self._inputs()
        target = None
        for observation in observations:
            if observation.match_type != contract.MATCH_TYPE_BASE_SAME_ISIN:
                continue
            bases = [
                row
                for row in rows_by_date[observation.business_date]
                if (row.security_isin or "").strip().upper() == observation.isin
                and row.series not in contract.OVERLAY_SERIES_OBSERVED
            ]
            if bases:
                target = observation
                break
        self.assertIsNotNone(target, "the sample extracts must contain a base-same observation")
        contradicted = OverlayFixtureRow(
            format_family="LEGACY",
            date=target.business_date,
            overlay_series=target.overlay_series,
            overlay_symbol="X",
            overlay_isin=target.isin,
            match_type=contract.MATCH_TYPE_NO_BASE_ORPHAN,
            base_symbol="",
            base_series="",
            base_isin="",
            qty_rel="",
        )
        disposition = determine_overlay_disposition(
            observations, rows_by_date, tuple(self.fixture_rows) + (contradicted,), ()
        )
        self.assertEqual(disposition.unreproducible_with_base_present, 1)
        self.assertEqual(disposition.defect_count, 1)
        self.assertEqual(disposition.cause, contract.W1_DIV_OVERLAY_CAUSE_UNRESOLVED)

    def test_engine_observation_missing_from_the_fixture_is_a_defect(self):
        observations, rows_by_date = self._inputs()
        disposition = determine_overlay_disposition(observations, rows_by_date, (), ())
        self.assertEqual(disposition.engine_observations_without_fixture_row, len(observations))
        self.assertEqual(disposition.cause, contract.W1_DIV_OVERLAY_CAUSE_UNRESOLVED)

    def test_row_in_extract_without_engine_observation_is_a_defect(self):
        observations, rows_by_date = self._inputs()
        first_observation = observations[0]
        rows = rows_by_date[first_observation.business_date]
        base_row = next(
            row
            for row in rows
            if row.series not in contract.OVERLAY_SERIES_OBSERVED
            and (row.security_isin or "").strip()
        )
        isin = (base_row.security_isin or "").strip().upper()
        fixture_row = OverlayFixtureRow(
            format_family="LEGACY",
            date=first_observation.business_date,
            overlay_series="IL",
            overlay_symbol="Y",
            overlay_isin=isin,
            match_type=contract.MATCH_TYPE_BASE_SAME_ISIN,
            base_symbol="Y",
            base_series="EQ",
            base_isin=isin,
            qty_rel="lt",
        )
        partial = tuple(
            observation
            for observation in observations
            if not (
                observation.business_date == first_observation.business_date
                and observation.overlay_series == "IL"
                and observation.isin == isin
            )
        )
        disposition = determine_overlay_disposition(partial, rows_by_date, (fixture_row,), ())
        self.assertEqual(disposition.engine_observation_missing_for_sampled_row, 1)
        self.assertEqual(disposition.cause, contract.W1_DIV_OVERLAY_CAUSE_UNRESOLVED)

    def test_disposition_is_deterministic(self):
        observations, rows_by_date = self._inputs()
        first = determine_overlay_disposition(observations, rows_by_date, self.fixture_rows, ())
        second = determine_overlay_disposition(observations, rows_by_date, self.fixture_rows, ())
        self.assertEqual(first.to_dict(), second.to_dict())


if __name__ == "__main__":
    unittest.main()
