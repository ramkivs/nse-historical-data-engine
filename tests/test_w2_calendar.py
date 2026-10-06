"""W2-A: calendar derivation (D05 §3.4; W2 prompt §10 A).

Governed cases come from the published evidence: ``FIX-CAL-01_arena_partial.json`` (file-date
structure, 147 missing weekdays), ``d02_missing_weekdays.txt`` (the exact list) and
``DEC2_CAL_LABELS.json`` (the sourced labels: 29 official holidays, 3 unexplained dates, one
circular holiday that nevertheless carries a file).
"""

from __future__ import annotations

import datetime as dt
import unittest

from tests import support
from nse_engine import contract
from nse_engine.calendar import (
    CalendarEvidenceError,
    MemberDateFact,
    arithmetic_closes,
    derive_calendar,
)
from nse_engine.evidence_inputs import CalendarLabelRecord, CircularHolidayRecord, InventoryFileRecord


def file_record(date, root="LEGACY", name=None):
    return InventoryFileRecord(
        file_name=name or ("cm%s.csv.zip" % date.replace("-", "")),
        date=date,
        root=root,
        sha256="0" * 64,
        row_count=10,
    )


def weekday_span(first, last):
    days = []
    cursor = dt.date(*[int(part) for part in first.split("-")])
    end = dt.date(*[int(part) for part in last.split("-")])
    while cursor <= end:
        if cursor.weekday() < 5:
            days.append(cursor.isoformat())
        cursor += dt.timedelta(days=1)
    return days


class GovernedCalendarTests(unittest.TestCase):
    """The calendar over the real D01 inventory reproduces the published structure."""

    @classmethod
    def setUpClass(cls):
        cls.w2 = support.build_w2_samples()
        cls.calendar = cls.w2.calendar
        cls.fix_cal = support._read_json(support.CAL_PARTIAL_PATH)

    def test_file_presence_structure_matches_the_published_calendar_evidence(self):
        self.assertEqual(self.calendar.files, self.fix_cal["archive_dates"]["count"])
        self.assertEqual(self.calendar.first_date, self.fix_cal["archive_dates"]["first"])
        self.assertEqual(self.calendar.last_date, self.fix_cal["archive_dates"]["last"])
        self.assertEqual(self.calendar.span_weekdays, self.fix_cal["arithmetic"]["span_inclusive_weekdays"])
        self.assertEqual(len(self.calendar.missing_days), self.fix_cal["arithmetic"]["observed_missing"])
        self.assertEqual(self.calendar.formats[0], ("LEGACY", 1919))
        self.assertEqual(self.calendar.formats[1], ("UDIFF", 543))
        self.assertTrue(arithmetic_closes(self.calendar))

    def test_weekday_histogram_matches_the_published_evidence_exactly(self):
        published = self.fix_cal["archive_dates"]["day_of_week_histogram"]
        self.assertEqual(
            {name: count for name, count in self.calendar.weekday_histogram().items()},
            {name: published[name] for name in self.calendar.weekday_histogram()},
        )

    def test_no_weekend_day_is_a_calendar_day_and_no_weekend_file_exists(self):
        self.assertEqual(
            [day.trade_date for day in self.calendar.days if day.weekday not in
             ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")],
            [],
        )
        self.assertEqual(self.fix_cal["archive_dates"]["saturday_or_sunday_files"], 0)

    def test_missing_weekday_list_matches_the_derived_list_exactly(self):
        self.assertEqual(
            [day.trade_date for day in self.calendar.missing_days],
            list(self.fix_cal["missing_weekday_files"]["dates"]),
        )
        self.assertEqual(
            [day.trade_date for day in self.calendar.missing_days],
            list(support.load_missing_weekdays()),
        )

    def test_provenance_inputs_record_the_consumed_evidence(self):
        inputs = dict(self.calendar.provenance_inputs)
        self.assertEqual(inputs["inventory_records"], "2462")
        self.assertEqual(inputs["calendar_labels"], "32")
        self.assertEqual(inputs["circular_holidays"], "1")
        self.assertEqual(inputs["member_facts"], str(len(support.PUBLISHED_SAMPLES)))
        self.assertEqual(self.calendar.label_scope_start, "2024-07-05")

    def test_span_is_exactly_the_weekdays_between_first_and_last(self):
        self.assertEqual(
            [day.trade_date for day in self.calendar.days],
            weekday_span(self.calendar.first_date, self.calendar.last_date),
        )


class GovernedCalendarLabelTests(unittest.TestCase):
    """Labels are sourced, bounded and never invented."""

    @classmethod
    def setUpClass(cls):
        cls.w2 = support.build_w2_samples()
        cls.calendar = cls.w2.calendar
        cls.document = support._read_json(support.DEC2_CAL_PATH)

    def test_unresolved_dates_are_exactly_the_three_governed_dates(self):
        self.assertEqual(self.calendar.unresolved_dates(), contract.CALENDAR_UNRESOLVED_DATES)
        self.assertEqual(tuple(self.document["unexplained"]), contract.CALENDAR_UNRESOLVED_DATES)

    def test_unresolved_dates_carry_no_label_and_no_cause(self):
        for day in self.calendar.days:
            if day.trade_date in contract.CALENDAR_UNRESOLVED_DATES:
                self.assertIsNone(day.official_holiday_label)
                self.assertEqual(day.label_status, contract.CALENDAR_LABEL_UNEXPLAINED)
                self.assertEqual(day.label_registry_id, None)
                self.assertTrue(
                    any("unresolved" in note for note in day.notes),
                    "the unresolved state must be visible in the note set",
                )

    def test_official_holiday_labels_come_only_from_the_sourced_circulars(self):
        labelled = {
            day.trade_date
            for day in self.calendar.days
            if day.label_status == contract.CALENDAR_LABEL_OFFICIAL_HOLIDAY
        }
        published = {
            entry["missing_date"]
            for entry in self.document["per_missing_day"]
            if entry["label"] == "OFFICIAL-HOLIDAY"
        }
        special = {entry["holiday_per_circular"] for entry in self.document["files_present_on_circular_holiday"]}
        self.assertEqual(labelled, published | special)
        self.assertEqual(self.document["explained"], 29)

    def test_legacy_era_gaps_are_not_retrieved_and_never_labelled(self):
        legacy_gaps = [
            day
            for day in self.calendar.missing_days
            if day.label_status == contract.CALENDAR_LABEL_NOT_RETRIEVED
        ]
        self.assertEqual(len(legacy_gaps), 147 - 32)
        for day in legacy_gaps:
            self.assertIsNone(day.official_holiday_label)
            self.assertLessEqual(day.trade_date, self.calendar.label_scope_start)

    def test_circular_holiday_with_a_file_present_keeps_the_file_and_records_the_divergence(self):
        day = next(day for day in self.calendar.days if day.trade_date == "2025-10-21")
        self.assertTrue(day.file_present)
        self.assertFalse(day.missing_weekday)
        self.assertEqual(day.label_status, contract.CALENDAR_LABEL_OFFICIAL_HOLIDAY)
        self.assertTrue(any("divergence" in note.lower() for note in day.notes))

    def test_file_absent_day_outside_the_annual_list_is_not_relabelled(self):
        # 2025-10-20 is file-absent though NOT in the annual list: it stays unexplained.
        day = next(day for day in self.calendar.days if day.trade_date == "2025-10-20")
        self.assertTrue(day.missing_weekday)
        self.assertEqual(day.label_status, contract.CALENDAR_LABEL_UNEXPLAINED)

    def test_label_status_vocabulary_is_governed(self):
        for day in self.calendar.days:
            self.assertIn(day.label_status, contract.CALENDAR_LABEL_STATUSES)
        counts = self.calendar.label_status_counts()
        self.assertEqual(sum(counts.values()), self.calendar.span_weekdays)

    def test_presence_is_derived_from_files_never_from_circulars(self):
        # A date listed as a circular holiday but WITH a file stays present (both directions of
        # divergence observed); the reverse case (file absent, not in the annual list) stays absent.
        for day in self.calendar.days:
            has_presence_note = any("trading-session signal" in note for note in day.notes)
            self.assertEqual(has_presence_note, day.file_present, day.trade_date)


class CalendarToleranceAndFailClosedTests(unittest.TestCase):
    """Synthetic cases for the derivation mechanics and every fail-closed rule."""

    def test_minimal_calendar_spans_weekdays_only(self):
        inventory = [file_record("2024-07-05"), file_record("2024-07-08")]
        result = derive_calendar(inventory)
        self.assertEqual(
            [day.trade_date for day in result.days],
            ["2024-07-05", "2024-07-08"],
        )
        self.assertEqual(result.missing_days, ())

    def test_missing_weekdays_outside_the_labelled_scope_are_not_retrieved(self):
        inventory = [file_record("2024-07-05"), file_record("2024-07-08")]
        result = derive_calendar(inventory)
        gaps = [day for day in result.days if day.missing_weekday]
        self.assertEqual([day.trade_date for day in gaps], [])  # 06/07 are weekend days

    def test_missing_weekday_inside_the_labelled_scope_requires_a_label(self):
        inventory = [file_record("2024-07-05"), file_record("2024-07-09", root="UDIFF")]
        with self.assertRaises(CalendarEvidenceError) as caught:
            derive_calendar(inventory)
        self.assertIn("no governed label", str(caught.exception))

    def test_supplying_the_label_satisfies_the_rule(self):
        inventory = [file_record("2024-07-05"), file_record("2024-07-09", root="UDIFF")]
        result = derive_calendar(
            inventory,
            [CalendarLabelRecord(missing_date="2024-07-08", label="OFFICIAL-HOLIDAY", circular="Test")],
        )
        day = next(day for day in result.days if day.trade_date == "2024-07-08")
        self.assertEqual(day.label_status, contract.CALENDAR_LABEL_OFFICIAL_HOLIDAY)
        self.assertEqual(day.official_holiday_label, "Test")

    def test_label_for_a_date_with_a_file_is_a_contradiction(self):
        inventory = [file_record("2024-07-05")]
        with self.assertRaises(CalendarEvidenceError) as caught:
            derive_calendar(
                inventory,
                [CalendarLabelRecord(missing_date="2024-07-05", label="OFFICIAL-HOLIDAY")],
            )
        self.assertIn("HAS a file", str(caught.exception))

    def test_label_outside_the_corpus_span_is_rejected(self):
        inventory = [file_record("2024-07-05")]
        with self.assertRaises(CalendarEvidenceError):
            derive_calendar(
                inventory,
                [CalendarLabelRecord(missing_date="2023-01-02", label="OFFICIAL-HOLIDAY")],
            )

    def test_label_on_a_weekend_is_rejected(self):
        inventory = [file_record("2024-07-05")]
        with self.assertRaises(CalendarEvidenceError):
            derive_calendar(
                inventory,
                [CalendarLabelRecord(missing_date="2024-07-06", label="OFFICIAL-HOLIDAY")],
            )

    def test_weekend_file_is_rejected(self):
        with self.assertRaises(CalendarEvidenceError) as caught:
            derive_calendar([file_record("2024-07-06")])
        self.assertIn("weekend file date", str(caught.exception))

    def test_member_fact_for_a_date_without_a_file_is_rejected(self):
        inventory = [file_record("2024-07-05"), file_record("2024-07-09", root="UDIFF")]
        with self.assertRaises(CalendarEvidenceError) as caught:
            derive_calendar(
                inventory,
                [CalendarLabelRecord(missing_date="2024-07-08", label="OFFICIAL-HOLIDAY")],
                member_facts=[MemberDateFact(business_date="2024-07-08", format_family="udiff34")],
            )
        self.assertIn("no inventory file", str(caught.exception))

    def test_member_fact_outside_the_corpus_span_is_rejected(self):
        inventory = [file_record("2024-07-05")]
        with self.assertRaises(CalendarEvidenceError):
            derive_calendar(
                inventory,
                member_facts=[MemberDateFact(business_date="2024-09-02", format_family="udiff34")],
            )

    def test_unknown_governed_label_value_is_rejected(self):
        inventory = [file_record("2024-07-05"), file_record("2024-07-09")]
        with self.assertRaises(CalendarEvidenceError):
            derive_calendar(
                inventory,
                [CalendarLabelRecord(missing_date="2024-07-08", label="FESTIVAL-GUESS")],
            )

    def test_no_inventory_raises(self):
        with self.assertRaises(CalendarEvidenceError):
            derive_calendar([])

    def test_trad_dt_eq_biz_dt_is_carried_only_where_a_member_supplied_it(self):
        inventory = [file_record("2024-07-05"), file_record("2024-07-08")]
        result = derive_calendar(
            inventory,
            member_facts=[
                MemberDateFact(
                    business_date="2024-07-08", format_family="udiff34", trad_dt_eq_biz_dt=True
                )
            ],
        )
        days = {day.trade_date: day for day in result.days}
        self.assertIsNone(days["2024-07-05"].trad_dt_eq_biz_dt)
        self.assertTrue(days["2024-07-08"].trad_dt_eq_biz_dt)

    def test_conflicting_member_facts_for_one_date_are_rejected(self):
        inventory = [file_record("2024-07-08")]
        with self.assertRaises(CalendarEvidenceError):
            derive_calendar(
                inventory,
                member_facts=[
                    MemberDateFact("2024-07-08", "udiff34", True),
                    MemberDateFact("2024-07-08", "udiff34", False),
                ],
            )


class CalendarDeterminismTests(unittest.TestCase):
    def test_derivation_is_order_independent(self):
        inventory = [
            file_record("2024-07-05"),
            file_record("2024-07-09", root="UDIFF"),
            file_record("2024-07-10", root="UDIFF"),
        ]
        labels = [CalendarLabelRecord(missing_date="2024-07-08", label="OFFICIAL-HOLIDAY", circular="X")]
        first = derive_calendar(inventory, labels)
        second = derive_calendar(list(reversed(inventory)), labels)
        self.assertEqual([day.to_dict() for day in first.days], [day.to_dict() for day in second.days])

    def test_derivation_is_repeatable(self):
        inventory = tuple(support.load_inventory_records())
        labels, holidays, _registry, _doc = support.load_calendar_labels()
        first = derive_calendar(inventory, labels, holidays)
        second = derive_calendar(inventory, labels, holidays)
        self.assertEqual([day.to_dict() for day in first.days], [day.to_dict() for day in second.days])
        self.assertEqual(first.totals(), second.totals())

    def test_repeated_full_calendar_totals_are_stable(self):
        first = support.build_w2_samples().calendar.totals()
        second = support.build_w2_samples().calendar.totals()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
