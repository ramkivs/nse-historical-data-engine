"""Legacy timestamp tolerance and fail-closed date handling (D05 §3.1, §7.2; D05 §5 flags)."""

from __future__ import annotations

import unittest

from tests import support
from nse_engine import contract
from nse_engine.parsing import parse_legacy_timestamp


class LegacyTimestampUnitTests(unittest.TestCase):
    def test_four_digit_year_is_the_row_date(self):
        result = parse_legacy_timestamp("20-SEP-2016", None)
        self.assertTrue(result.ok)
        self.assertEqual(result.iso_date, "2016-09-20")
        self.assertEqual(result.basis, contract.DATE_BASIS_LEGACY_FOUR_DIGIT_YEAR)

    def test_two_digit_year_uses_the_governed_source_date(self):
        result = parse_legacy_timestamp("13-Jul-20", "2020-07-13")
        self.assertTrue(result.ok)
        self.assertEqual(result.iso_date, "2020-07-13")
        self.assertEqual(result.basis, contract.DATE_BASIS_LEGACY_TWO_DIGIT_YEAR_CROSSCHECKED)

    def test_two_digit_year_without_source_date_fails_closed(self):
        result = parse_legacy_timestamp("13-Jul-20", None)
        self.assertFalse(result.ok)
        self.assertEqual(result.failure_code, "legacy_two_digit_year_unresolvable")
        self.assertIsNone(result.iso_date)

    def test_two_digit_year_disagreeing_with_source_date_fails_closed(self):
        result = parse_legacy_timestamp("14-Jul-20", "2020-07-13")
        self.assertFalse(result.ok)
        self.assertEqual(result.failure_code, "legacy_two_digit_year_unresolvable")

    def test_blank_timestamp_fails_closed(self):
        result = parse_legacy_timestamp("", "2020-07-13")
        self.assertFalse(result.ok)
        self.assertEqual(result.failure_code, "legacy_timestamp_blank")

    def test_time_of_day_form_is_not_silently_interpreted(self):
        # D05 §7.2 states time-of-day is retained in raw; no time-of-day syntax is
        # documented as authorized tolerance, so W1 fails closed instead of inventing one.
        result = parse_legacy_timestamp("20-SEP-2016 15:30:00", "2016-09-20")
        self.assertFalse(result.ok)
        self.assertEqual(result.failure_code, "legacy_timestamp_unparseable")

    def test_impossible_calendar_date_fails_closed(self):
        result = parse_legacy_timestamp("31-FEB-2016", None)
        self.assertFalse(result.ok)
        self.assertEqual(result.failure_code, "legacy_timestamp_unparseable")

    def test_unknown_month_token_fails_closed(self):
        result = parse_legacy_timestamp("20-XXX-2016", None)
        self.assertFalse(result.ok)
        self.assertEqual(result.failure_code, "legacy_timestamp_unparseable")


class LegacyTimestampMemberTests(unittest.TestCase):
    def test_four_digit_year_row_carries_date_and_raw_text(self):
        build = support.parse_synthetic(
            support.legacy_member([support.legacy_row()]), expected_source_date="2016-09-20"
        )
        row = build.rows[0]
        self.assertEqual(row.business_date, "2016-09-20")
        self.assertEqual(row.raw_biz_dt, "20-SEP-2016")
        self.assertEqual(row.business_date_basis, contract.DATE_BASIS_LEGACY_FOUR_DIGIT_YEAR)

    def test_two_digit_year_row_matches_the_2020_07_13_corpus_shape(self):
        build = support.parse_synthetic(
            support.legacy_member([support.legacy_row(TIMESTAMP="13-Jul-20")], line_ending="\r\n"),
            expected_source_date="2020-07-13",
        )
        row = build.rows[0]
        self.assertEqual(row.business_date, "2020-07-13")
        self.assertEqual(row.raw_biz_dt, "13-Jul-20")
        self.assertEqual(
            row.business_date_basis, contract.DATE_BASIS_LEGACY_TWO_DIGIT_YEAR_CROSSCHECKED
        )
        self.assertEqual(row.flag_names(), ())

    def test_row_with_unparseable_timestamp_is_quarantined_with_raw_text(self):
        build = support.parse_synthetic(
            support.legacy_member(
                [support.legacy_row(TIMESTAMP="20-SEP-2016 15:30"), support.legacy_row(ISIN="INE002A01018")]
            ),
            expected_source_date="2016-09-20",
        )
        self.assertEqual(len(build.rows), 1)
        self.assertEqual(len(build.quarantined), 1)
        record = build.quarantined[0]
        self.assertEqual(record.reason_code, "legacy_timestamp_unparseable")
        self.assertTrue(record.raw_line.startswith("20MICRONS,EQ,37.4"))

    def test_two_digit_year_without_source_date_is_quarantined(self):
        build = support.parse_synthetic(
            support.legacy_member([support.legacy_row(TIMESTAMP="13-Jul-20")])
        )
        self.assertEqual(len(build.rows), 0)
        self.assertEqual(
            build.quarantined[0].reason_code, "legacy_two_digit_year_unresolvable"
        )

    def test_date_source_conflict_is_flagged_and_both_dates_kept(self):
        build = support.parse_synthetic(
            support.legacy_member([support.legacy_row(TIMESTAMP="21-SEP-2016")]),
            expected_source_date="2016-09-20",
        )
        row = build.rows[0]
        self.assertEqual(row.business_date, "2016-09-21")
        self.assertEqual(row.value("raw_biz_dt"), "21-SEP-2016")
        self.assertEqual(row.flag_names(), (contract.FLAG_DATE_SOURCE_CONFLICT,))
        self.assertEqual(row.observations, (("date_source_conflict_evaluated", "true"),))

    def test_missing_source_date_leaves_conflict_check_unevaluated(self):
        build = support.parse_synthetic(support.legacy_member([support.legacy_row()]))
        row = build.rows[0]
        self.assertEqual(row.flag_names(), ())
        self.assertEqual(
            dict(row.observations)["date_source_conflict_evaluated"], "false"
        )


class UdiffDateTests(unittest.TestCase):
    def test_traddt_is_the_canonical_date(self):
        build = support.parse_synthetic(
            support.udiff_member([support.udiff_row()]), expected_source_date="2024-07-08"
        )
        row = build.rows[0]
        self.assertEqual(row.business_date, "2024-07-08")
        self.assertEqual(row.business_date_basis, contract.DATE_BASIS_UDIFF_TRADDT)
        self.assertEqual(dict(row.observations)["bizdt_traddt_comparison"], "verbatim_text_equality")
        self.assertEqual(row.flag_names(), ())

    def test_bizdt_ne_traddt_is_flagged_never_reconciled(self):
        build = support.parse_synthetic(
            support.udiff_member([support.udiff_row(BizDt="2024-07-09")]),
            expected_source_date="2024-07-08",
        )
        row = build.rows[0]
        self.assertEqual(row.business_date, "2024-07-08")
        self.assertEqual(row.value("raw_biz_dt"), "2024-07-09")
        self.assertIn(contract.FLAG_BIZDT_NE_TRADDT, row.flag_names())

    def test_blank_bizdt_is_not_flagged_as_a_difference(self):
        build = support.parse_synthetic(
            support.udiff_member([support.udiff_row(BizDt="")]), expected_source_date="2024-07-08"
        )
        row = build.rows[0]
        self.assertEqual(row.flag_names(), ())
        self.assertEqual(
            dict(row.observations)["bizdt_traddt_comparison"], "undetermined_blank_bizdt"
        )

    def test_non_iso_traddt_is_quarantined(self):
        for bad in ("2024-7-8", "", "08-07-2024", "2024-02-30"):
            with self.subTest(trad_dt=bad):
                build = support.parse_synthetic(
                    support.udiff_member([support.udiff_row(TradDt=bad)]),
                    expected_source_date="2024-07-08",
                )
                self.assertEqual(len(build.rows), 0)
                self.assertEqual(build.quarantined[0].reason_code, "udiff_traddt_unparseable")


if __name__ == "__main__":
    unittest.main()
