"""W2-D: D01 metric re-computation (D05 §4; W2 prompt §7, §10 D).

Level A — row metrics over canonical rows (exact, governed definitions).
Level B — corpus metric algebra folded from the frozen per-file D01 metric evidence, plus the
D02 series facts recomputed from the D01 inventory.

Governed expected values: ``FIX-SEM-DEF-01__metrics.csv`` (2,462 files),
``FIX-SEM-DEF-01__d01_definition_verdict.json``, ``FIX-SEM-DEF-01__formula_definitions.json``,
``FIX-LEG-CENSUS-01__per_year.csv``, ``evidence/identity/d02_series_universe.csv``,
``evidence/identity/d02_series_class_rollup.csv`` and ``evidence/identity/d02_metrics.json``.
Nothing here re-derives a semantic: the series classification is carried evidence input.
"""

from __future__ import annotations

import unittest

from tests import support
from nse_engine import contract, metrics
from nse_engine.evidence_inputs import FileMetricRecord


#: Extract-scope expected values, verified against the published samples (W1 parse → W2 metrics).
EXPECTED_EXTRACT_METRICS = {
    "FIX-UD-ROW-SAMPLE-01__sample_legacy_2016-09-20.csv": (217, 0, 217, 217, 0),
    "FIX-UD-ROW-SAMPLE-01__sample_legacy_2022-10-03.csv": (414, 0, 414, 403, 11),
    "FIX-UD-ROW-SAMPLE-01__sample_legacy_2024-03-28.csv": (491, 0, 491, 491, 0),
    "FIX-UD-ROW-SAMPLE-01__sample_udiff_2024-07-08.csv": (492, 0, 492, 492, 0),
    "FIX-UD-ROW-SAMPLE-01__sample_udiff_2025-07-14.csv": (486, 0, 486, 485, 1),
    "FIX-UD-ROW-SAMPLE-01__sample_udiff_2025-10-30.csv": (493, 0, 493, 492, 1),
    "FIX-UD-ROW-SAMPLE-01__sample_udiff_2026-08-25.csv": (495, 0, 495, 495, 0),
}


def synthetic_metrics(rows):
    build = support.parse_synthetic(
        support.legacy_member(rows),
        expected_source_date="2024-07-05",
        member_name="synthetic.csv",
    )
    return metrics.compute_row_metrics(build.rows), build


class RowMetricGovernedDefinitionTests(unittest.TestCase):
    def test_definitions_are_the_governed_fixture_text(self):
        formulas = support.w2_evidence("formulas")
        published = formulas["formulas"]
        governed = dict(contract.D01_METRIC_DEFINITIONS)
        for name, text in published.items():
            self.assertIn(name, governed)
            self.assertEqual(governed[name], text)
        self.assertIn("blank_symbol_rows", governed)
        self.assertEqual(
            tuple(name for name, _definition in contract.D01_METRIC_DEFINITIONS),
            contract.D01_METRIC_NAMES,
        )

    def test_metric_name_set_matches_the_oracle_columns(self):
        oracle_columns = set(support.w2_evidence("metrics_oracle")[0].keys())
        self.assertTrue(set(contract.D01_METRIC_NAMES) <= oracle_columns)
        self.assertEqual(len(contract.D01_METRIC_NAMES), 9)

    def test_row_metrics_carry_their_governed_metadata(self):
        document = metrics.compute_row_metrics(()).to_dict()
        self.assertEqual(document["definitions"], dict(contract.D01_METRIC_DEFINITIONS))
        self.assertEqual(document["normalization"], contract.D01_NORMALIZATION)
        self.assertEqual(document["distinct_rule"], contract.D01_DISTINCT_RULE)


class RowMetricExpectedValueTests(unittest.TestCase):
    def test_published_extract_metrics_match_the_expected_values(self):
        for name, expected in EXPECTED_EXTRACT_METRICS.items():
            with self.subTest(member=name):
                row_metrics = metrics.compute_row_metrics(support.build_sample(name).rows)
                rows, blank_isin, nonblank_isin, distinct_isin, duplicate_isin = expected
                self.assertEqual(row_metrics.get("rows"), rows)
                self.assertEqual(row_metrics.get("blank_isin_rows"), blank_isin)
                self.assertEqual(row_metrics.get("nonblank_isin_rows"), nonblank_isin)
                self.assertEqual(row_metrics.get("distinct_nonblank_isin"), distinct_isin)
                self.assertEqual(row_metrics.get("isins_extra_duplicate_rows"), duplicate_isin)
                self.assertEqual(
                    row_metrics.get("nonblank_isin_rows") - row_metrics.get("distinct_nonblank_isin"),
                    row_metrics.get("isins_extra_duplicate_rows"),
                )

    def test_extract_row_totals_match_the_published_selection_fixture(self):
        selection = support.published_evidence("coverage")
        total = 0
        per_date = {}
        for name in support.PUBLISHED_SAMPLES:
            build = support.build_sample(name)
            date = build.rows[0].business_date
            per_date[date] = len(build.rows)
            total += len(build.rows)
        self.assertEqual(total, selection["emitted_total_rows"])
        published = {
            key.split("|")[1]: value["sampled_rows"] for key, value in selection["per_date"].items()
        }
        self.assertEqual(per_date, published)

    def test_missing_values_are_counted_not_imputed(self):
        row_metrics, build = synthetic_metrics(
            [
                support.legacy_row(TIMESTAMP="05-JUL-2024", SYMBOL="ALPHA", SERIES="EQ", ISIN=""),
                support.legacy_row(TIMESTAMP="05-JUL-2024", SYMBOL="ALPHA", SERIES="EQ", ISIN="   "),
                support.legacy_row(
                    TIMESTAMP="05-JUL-2024", SYMBOL="ALPHA", SERIES="EQ", ISIN="INE144J01027"
                ),
            ]
        )
        self.assertEqual(len(build.rows), 3)
        self.assertEqual(row_metrics.get("blank_isin_rows"), 2)
        self.assertEqual(row_metrics.get("nonblank_isin_rows"), 1)
        self.assertEqual(row_metrics.get("distinct_nonblank_isin"), 1)
        # two blank-ISIN rows with the same (symbol, series) still count as a duplicate pair
        self.assertEqual(row_metrics.get("symbol_series_duplicate_rows"), 2)
        self.assertEqual(row_metrics.get("isins_extra_duplicate_rows"), 0)

    def test_blank_symbol_is_never_a_distinct_value(self):
        row_metrics, _build = synthetic_metrics(
            [
                support.legacy_row(TIMESTAMP="05-JUL-2024", SYMBOL="", SERIES="EQ", ISIN="INE144J01027"),
                support.legacy_row(
                    TIMESTAMP="05-JUL-2024", SYMBOL="ALPHA", SERIES="EQ", ISIN="INE002S01010"
                ),
            ]
        )
        self.assertEqual(row_metrics.get("blank_symbol_rows"), 1)
        self.assertEqual(row_metrics.get("distinct_nonblank_symbol"), 1)

    def test_normalization_is_strip_and_uppercase_for_isin_and_symbol(self):
        row_metrics, _build = synthetic_metrics(
            [
                support.legacy_row(
                    TIMESTAMP="05-JUL-2024", SYMBOL="alpha", SERIES="EQ", ISIN=" ine144j01027 "
                ),
                support.legacy_row(
                    TIMESTAMP="05-JUL-2024", SYMBOL="ALPHA", SERIES="EQ", ISIN="INE144J01027"
                ),
            ]
        )
        self.assertEqual(row_metrics.get("blank_isin_rows"), 0)
        self.assertEqual(row_metrics.get("distinct_nonblank_isin"), 1)
        self.assertEqual(row_metrics.get("distinct_nonblank_symbol"), 1)
        self.assertEqual(row_metrics.get("isins_extra_duplicate_rows"), 1)

    def test_invalid_isin_values_are_counted_verbatim_never_filtered(self):
        # D05 §5: ISIN validity is informational. No validation rule may be applied here, and
        # nothing may be coerced or dropped.
        row_metrics, build = synthetic_metrics(
            [
                support.legacy_row(
                    TIMESTAMP="05-JUL-2024", SYMBOL="ALPHA", SERIES="EQ", ISIN="INE144J01028"
                ),
                support.legacy_row(
                    TIMESTAMP="05-JUL-2024", SYMBOL="BETA", SERIES="EQ", ISIN="NOT-AN-ISIN"
                ),
            ]
        )
        self.assertEqual(row_metrics.get("distinct_nonblank_isin"), 2)
        self.assertTrue(build.rows[0].flag_names(), "the bad check-digit value must stay flagged")

    def test_series_is_compared_verbatim_never_case_folded(self):
        row_metrics, _build = synthetic_metrics(
            [
                support.legacy_row(TIMESTAMP="05-JUL-2024", SYMBOL="ALPHA", SERIES="eq", ISIN="INE144J01027"),
                support.legacy_row(TIMESTAMP="05-JUL-2024", SYMBOL="ALPHA", SERIES="EQ", ISIN="INE002S01010"),
            ]
        )
        self.assertEqual(row_metrics.get("distinct_symbol_series_pairs"), 2)
        self.assertEqual(row_metrics.get("symbol_series_duplicate_rows"), 0)

    def test_unknown_metric_name_fails_closed(self):
        row_metrics = metrics.compute_row_metrics(())
        with self.assertRaises(KeyError):
            row_metrics.get("not_a_metric")

    def test_row_metrics_are_order_independent(self):
        build = support.build_sample(support.PUBLISHED_SAMPLES[1])
        forward = metrics.compute_row_metrics(build.rows)
        backward = metrics.compute_row_metrics(tuple(reversed(build.rows)))
        self.assertEqual(forward.to_dict(), backward.to_dict())


class CorpusMetricAlgebraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = support.load_file_metric_records()
        cls.fold = metrics.fold_file_metrics(cls.records)
        cls.d02 = support._read_json(support.D02_METRICS_PATH)

    def test_corpus_totals_match_the_d02_evidence(self):
        totals = self.fold["totals"]
        self.assertEqual(totals["files"], 2462)
        self.assertEqual(totals["rows"], 5689949)
        self.assertEqual(totals["blank_isin_rows"], 0)
        self.assertEqual(totals["nonblank_isin_rows"], 5689949)
        self.assertEqual(totals["isins_extra_duplicate_rows"], 3357)
        self.assertEqual(totals["symbol_series_duplicate_rows"], 0)
        self.assertEqual(totals["files"], self.d02["total_files"])
        self.assertEqual(totals["rows"], self.d02["total_rows"])

    def test_per_format_totals_match_the_d02_evidence(self):
        per_format = self.fold["per_format"]
        self.assertEqual(sorted(per_format), ["LEGACY", "UDIFF"])
        self.assertEqual(per_format["LEGACY"]["files"], 1919)
        self.assertEqual(per_format["LEGACY"]["rows"], 3989299)
        self.assertEqual(per_format["UDIFF"]["files"], 543)
        self.assertEqual(per_format["UDIFF"]["rows"], 1700650)
        self.assertEqual(per_format["LEGACY"]["files"], self.d02["legacy_files"])
        self.assertEqual(per_format["LEGACY"]["rows"], self.d02["legacy_rows"])
        self.assertEqual(per_format["UDIFF"]["files"], self.d02["udiff_files"])
        self.assertEqual(per_format["UDIFF"]["rows"], self.d02["udiff_rows"])
        self.assertEqual(sum(entry["files"] for entry in per_format.values()), 2462)

    def test_definition_verdict_is_re_derived_from_the_numeric_columns(self):
        verdict = self.fold["definition_verdict"]
        published = support.w2_evidence("sem_def")
        self.assertEqual(verdict["discriminating_files"], 1078)
        self.assertEqual(verdict["match_distinct_nonblank"], 1078)
        self.assertEqual(verdict["match_nonblank_rows"], 0)
        self.assertEqual(verdict["verdict"], contract.D01_VERDICT_ISIN_EQ_DISTINCT_NONBLANK)
        for key in ("discriminating_files", "match_distinct_nonblank", "match_nonblank_rows", "verdict"):
            self.assertEqual(verdict[key], published[key], key)
        self.assertEqual(published["note"].startswith("Verdict derived only from files"), True)
        self.assertEqual(self.d02["files_isin_deficit"], verdict["discriminating_files"])
        self.assertEqual(self.d02["files_isin_excess"], verdict["match_nonblank_rows"])

    def test_fixture_booleans_are_cross_checked_not_trusted(self):
        self.assertEqual(self.fold["booleans_re_derived_consistently"], 2462)
        self.assertEqual(self.fold["symbol_definition_verdict"]["discriminating_files"], 1078)
        self.assertEqual(
            self.fold["symbol_definition_verdict"]["match_distinct_nonblank"],
            self.fold["symbol_definition_verdict"]["discriminating_files"],
        )

    def test_verdict_fails_closed_when_no_file_discriminates(self):
        empty = metrics.fold_file_metrics(())
        self.assertEqual(empty["definition_verdict"]["verdict"], contract.D01_VERDICT_UNDETERMINED)
        self.assertEqual(empty["totals"]["files"], 0)

    def test_verdict_reports_the_other_reading_when_the_evidence_selects_it(self):
        record = FileMetricRecord(
            format_family="LEGACY",
            file_name="synthetic.csv",
            rows=10,
            blank_symbol_rows=0,
            blank_isin_rows=0,
            nonblank_isin_rows=10,
            distinct_nonblank_isin=9,
            isins_extra_duplicate_rows=1,
            distinct_nonblank_symbol=10,
            distinct_symbol_series_pairs=10,
            symbol_series_duplicate_rows=0,
            d01_isin_count=10,
            d01_symbol_count=10,
            discriminating_file=True,
            d01_isin_eq_distinct_nonblank=False,
            d01_isin_eq_nonblank_rows=True,
            d01_sym_eq_distinct_nonblank=True,
            d01_sym_eq_rows=True,
            requested_date=None,
        )
        fold = metrics.fold_file_metrics((record,))
        self.assertEqual(
            fold["definition_verdict"]["verdict"], contract.D01_VERDICT_ISIN_EQ_NONBLANK_ROWS
        )

    def test_verdict_reports_mixed_evidence_never_rounds(self):
        base = dict(
            format_family="LEGACY",
            rows=10,
            blank_symbol_rows=0,
            blank_isin_rows=0,
            nonblank_isin_rows=10,
            distinct_nonblank_isin=9,
            isins_extra_duplicate_rows=1,
            distinct_nonblank_symbol=10,
            distinct_symbol_series_pairs=10,
            symbol_series_duplicate_rows=0,
            d01_symbol_count=10,
            discriminating_file=True,
            d01_sym_eq_distinct_nonblank=True,
            d01_sym_eq_rows=True,
            requested_date=None,
        )
        consistent = FileMetricRecord(
            file_name="a.csv",
            d01_isin_count=9,
            d01_isin_eq_distinct_nonblank=True,
            d01_isin_eq_nonblank_rows=False,
            **base
        )
        contradictory = FileMetricRecord(
            file_name="b.csv",
            d01_isin_count=10,
            d01_isin_eq_distinct_nonblank=False,
            d01_isin_eq_nonblank_rows=True,
            **base
        )
        fold = metrics.fold_file_metrics((consistent, contradictory))
        self.assertEqual(fold["definition_verdict"]["verdict"], contract.D01_VERDICT_MIXED)

    def test_fold_is_order_independent_and_deterministic(self):
        again = metrics.fold_file_metrics(self.records)
        self.assertEqual(self.fold, again)
        reversed_fold = metrics.fold_file_metrics(tuple(reversed(self.records)))
        self.assertEqual(self.fold["totals"], reversed_fold["totals"])
        self.assertEqual(self.fold["definition_verdict"], reversed_fold["definition_verdict"])
        self.assertEqual(self.fold["per_format"], reversed_fold["per_format"])


class LegacyCensusCrossCheckTests(unittest.TestCase):
    """The legacy census is NOT an oracle (W1-DIV-1): only its D01-shared columns are compared."""

    @classmethod
    def setUpClass(cls):
        cls.inventory = support.load_inventory_records()
        cls.records = support.load_file_metric_records()
        cls.date_by_file = {record.file_name: record.date for record in cls.inventory}

    def test_census_year_rows_are_reproduced_from_the_legacy_per_file_evidence(self):
        # the oracle's ``format`` column uses the evidence vocabulary LEGACY / UDIFF
        legacy_records = tuple(
            record for record in self.records if record.format_family == "LEGACY"
        )
        fold = metrics.fold_metrics_by_year(legacy_records, self.date_by_file)
        published = {row["year"]: row for row in support.load_legacy_census_per_year()}
        self.assertEqual([str(entry["year"]) for entry in fold], sorted(published))
        for entry in fold:
            reference = published[str(entry["year"])]
            for column in ("files", "rows", "blank_isin_rows", "symbol_series_duplicate_rows"):
                self.assertEqual(str(entry[column]), reference[column], (entry["year"], column))

    def test_year_fold_covers_the_whole_corpus_by_calendar_year(self):
        all_years = metrics.fold_metrics_by_year(self.records, self.date_by_file)
        self.assertEqual(sum(entry["files"] for entry in all_years), 2462)
        self.assertEqual(sum(entry["rows"] for entry in all_years), 5689949)
        self.assertEqual(sum(entry["nonblank_isin_rows"] for entry in all_years), 5689949)

    def test_year_fold_fails_closed_without_a_date_for_a_file(self):
        with self.assertRaises(KeyError):
            metrics.fold_metrics_by_year(self.records, {})


class SeriesUniverseRecomputationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = support.load_inventory_records()
        cls.classes = support.load_series_classes()
        cls.entries = metrics.series_universe(cls.inventory, cls.classes)
        cls.published = {row["series"]: row for row in support.load_series_universe_rows()}
        cls.d02 = support._read_json(support.D02_METRICS_PATH)

    def test_every_published_series_is_recomputed_exactly(self):
        self.assertEqual(len(self.entries), len(self.published))
        self.assertEqual(len(self.entries), self.d02["distinct_series_codes"])
        for entry in self.entries:
            with self.subTest(series=entry.series):
                reference = self.published[entry.series]
                for column, value in entry.to_dict().items():
                    expected = reference[column] or None
                    self.assertEqual(str(value) if value is not None else None, expected, column)

    def test_format_presence_vocabulary_matches_the_published_evidence(self):
        counts = {"BOTH": 0, "LEGACY_ONLY": 0, "UDIFF_ONLY": 0}
        for entry in self.entries:
            self.assertIn(entry.format_presence, contract.SERIES_FORMAT_PRESENCE_VALUES)
            counts[entry.format_presence] += 1
        self.assertEqual(counts["BOTH"], self.d02["series_shared_across_formats"])
        self.assertEqual(counts["LEGACY_ONLY"], len(self.d02["series_legacy_only"]))
        self.assertEqual(counts["UDIFF_ONLY"], len(self.d02["series_udiff_only"]))
        self.assertEqual(counts["LEGACY_ONLY"] + counts["UDIFF_ONLY"] + counts["BOTH"], 172)

    def test_series_class_is_carried_evidence_never_re_derived(self):
        for entry in self.entries:
            self.assertEqual(entry.provisional_class, self.classes[entry.series][0])
            self.assertEqual(entry.classification_basis, self.classes[entry.series][1])
        overrides = {code: ("MADE_UP", "made-up basis") for code in self.published}
        overridden = metrics.series_universe(self.inventory, overrides)
        self.assertEqual({entry.provisional_class for entry in overridden}, {"MADE_UP"})
        self.assertEqual({entry.total_obs for entry in overridden}, {entry.total_obs for entry in self.entries})

    def test_class_rollup_reproduces_the_published_rollup(self):
        rollup = metrics.series_class_rollup(self.entries)
        published = {row["provisional_class"]: row for row in support.load_series_class_rollup()}
        self.assertEqual({entry["provisional_class"] for entry in rollup}, set(published))
        self.assertEqual(len(rollup), len(published))
        for entry in rollup:
            reference = published[entry["provisional_class"]]
            self.assertEqual(str(entry["n_codes"]), reference["n_codes"])
            self.assertEqual(str(entry["total_obs"]), reference["total_obs"])
            self.assertEqual(str(entry["pct_of_all_rows"]), reference["pct_of_all_rows"])
        self.assertEqual(sum(entry["n_codes"] for entry in rollup), 172)
        self.assertEqual(sum(entry["total_obs"] for entry in rollup), 5689949)

    def test_inventory_series_counts_sum_to_the_row_count_for_every_file(self):
        for record in self.inventory:
            self.assertEqual(
                sum(count for _series, count in record.series_counts), record.row_count,
                record.file_name,
            )
        self.assertEqual(len(self.inventory), self.d02["files_series_sum_equals_row_count"])

    def test_unclassified_series_stay_unclassified(self):
        rollup = {entry["provisional_class"]: entry for entry in metrics.series_class_rollup(self.entries)}
        self.assertIn("UNCLASSIFIED", rollup)
        self.assertEqual(rollup["UNCLASSIFIED"]["n_codes"], 5)
        self.assertEqual(rollup["UNCLASSIFIED"]["total_obs"], 22)

    def test_series_universe_is_order_independent(self):
        reversed_entries = metrics.series_universe(tuple(reversed(self.inventory)), self.classes)
        self.assertEqual(
            [entry.to_dict() for entry in self.entries],
            [entry.to_dict() for entry in reversed_entries],
        )


if __name__ == "__main__":
    unittest.main()
