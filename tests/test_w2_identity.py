"""W2-B: identity correlation scopes and dated associations (D05 §3.2–§3.3; W2 prompt §10 B).

Cases: valid dated association, effective-date boundaries (including state recurrence and
same-day parallel states), unmatched/unkeyable rows, ambiguity that must not be collapsed,
provenance preservation, overlay-row exclusion (counted, never silent), and determinism.
"""

from __future__ import annotations

import unittest

from tests import support
from nse_engine import contract
from nse_engine.identity import build_associations


ISIN_A = "INE144J01027"
ISIN_B = "INE002S01010"
MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")


def token(iso: str) -> str:
    year, month, day = iso.split("-")
    return "%s-%s-%s" % (day, MONTHS[int(month) - 1], year)


def member_on(iso: str, specs):
    """Build one legacy member dated ``iso``; every spec is a legacy_row override set."""
    rows = []
    for spec in specs:
        overrides = dict(spec)
        overrides["TIMESTAMP"] = token(iso)
        rows.append(support.legacy_row(**overrides))
    return support.parse_synthetic(
        support.legacy_member(rows),
        expected_source_date=iso,
        member_name="cm%s.csv" % iso.replace("-", ""),
    )


def member_2024_07_05(rows):
    return support.parse_synthetic(
        support.legacy_member(rows),
        expected_source_date="2024-07-05",
        member_name="cm05JUL2024bhav.csv.zip",
    )


def member_2024_07_08(rows):
    return support.parse_synthetic(
        support.legacy_member(rows),
        expected_source_date="2024-07-08",
        member_name="cm08JUL2024bhav.csv.zip",
    )


class DatedAssociationTests(unittest.TestCase):
    def test_single_state_across_two_dates_is_one_association(self):
        first = member_on("2024-07-05", [{"SYMBOL": "ALPHA", "SERIES": "EQ", "ISIN": ISIN_A}])
        second = member_on("2024-07-08", [{"SYMBOL": "ALPHA", "SERIES": "EQ", "ISIN": ISIN_A}])
        build = build_associations(first.rows + second.rows)
        self.assertEqual(build.totals()["identities"], 1)
        self.assertEqual(build.totals()["associations"], 1)
        association = build.identities[0].associations[0]
        self.assertEqual(association.observed_from, "2024-07-05")
        self.assertEqual(association.observed_to, "2024-07-08")
        self.assertEqual(association.interval_basis, contract.INTERVAL_BASIS_OBSERVED_RANGE)
        self.assertEqual(association.association_type, contract.ASSOCIATION_TYPE_CORPUS_OBSERVED)

    def test_state_change_starts_a_new_association(self):
        first = member_on("2024-07-05", [{"SYMBOL": "ALPHA", "SERIES": "EQ", "ISIN": ISIN_A}])
        second = member_on("2024-07-08", [{"SYMBOL": "ALPHA", "SERIES": "BE", "ISIN": ISIN_A}])
        result = build_associations(first.rows + second.rows)
        states = [
            (entry.series, entry.observed_from, entry.observed_to)
            for entry in result.identities[0].associations
        ]
        self.assertEqual(states, [("EQ", "2024-07-05", "2024-07-05"), ("BE", "2024-07-08", "2024-07-08")])

    def test_state_recurrence_yields_three_dated_rows(self):
        # D05 §3.3: "the same ISIN appearing as EQ then BE then EQ yields three dated rows".
        rows = []
        for iso, series in (("2024-07-05", "EQ"), ("2024-07-08", "BE"), ("2024-07-09", "EQ")):
            member = member_on(iso, [{"SYMBOL": "ALPHA", "SERIES": series, "ISIN": ISIN_A}])
            rows.extend(member.rows)
        build = build_associations(rows)
        states = [entry.series for entry in build.identities[0].associations]
        self.assertEqual(states, ["EQ", "BE", "EQ"])
        self.assertEqual(build.totals()["identities"], 1)

    def test_symbol_change_within_one_series_is_a_new_association(self):
        first = member_on("2024-07-05", [{"SYMBOL": "ALPHA", "SERIES": "EQ", "ISIN": ISIN_A}])
        second = member_on("2024-07-08", [{"SYMBOL": "ALPHA-NEW", "SERIES": "EQ", "ISIN": ISIN_A}])
        build = build_associations(first.rows + second.rows)
        self.assertEqual(
            [(entry.symbol, entry.series) for entry in build.identities[0].associations],
            [("ALPHA", "EQ"), ("ALPHA-NEW", "EQ")],
        )
        self.assertEqual(build.totals()["identities_with_multiple_symbols"], 1)

    def test_effective_date_boundaries_are_observed_ranges_not_validity_periods(self):
        first = member_on("2024-07-05", [{"SYMBOL": "ALPHA", "SERIES": "EQ", "ISIN": ISIN_A}])
        third = member_on("2024-07-09", [{"SYMBOL": "ALPHA", "SERIES": "EQ", "ISIN": ISIN_A}])
        build = build_associations(first.rows + third.rows)
        association = build.identities[0].associations[0]
        self.assertEqual((association.observed_from, association.observed_to), ("2024-07-05", "2024-07-09"))
        observations = dict(association.observations)
        self.assertEqual(observations["interval_rule"], contract.ASSOCIATION_INTERVAL_RULE)
        self.assertEqual(observations["other_states_within_observed_range"], "0")
        self.assertEqual(observations["observed_dates"], "2")

    def test_same_day_parallel_states_are_kept_and_flagged_never_collapsed(self):
        build = member_on(
            "2024-07-05",
            [
                {"SYMBOL": "ALPHA", "SERIES": "EQ", "ISIN": ISIN_A},
                {"SYMBOL": "ALPHA", "SERIES": "BE", "ISIN": ISIN_A},
            ],
        )
        result = build_associations(build.rows)
        associations = result.identities[0].associations
        self.assertEqual(len(associations), 2)
        self.assertEqual({entry.observed_from for entry in associations}, {"2024-07-05"})
        for association in associations:
            self.assertEqual(dict(association.observations)["same_day_parallel_states"], "true")
        self.assertEqual(result.totals()["identities_with_same_day_parallel_states"], 1)

    def test_two_rows_of_the_same_state_on_one_date_are_one_association(self):
        build = member_on(
            "2024-07-05",
            [
                {"SYMBOL": "ALPHA", "SERIES": "EQ", "ISIN": ISIN_A},
                {"SYMBOL": "ALPHA", "SERIES": "EQ", "ISIN": ISIN_A},
            ],
        )
        result = build_associations(build.rows)
        self.assertEqual(len(result.identities[0].associations), 1)
        self.assertEqual(dict(result.identities[0].associations[0].observations)["observation_rows"], "2")

    def test_two_securities_stay_two_scopes(self):
        build = member_2024_07_05(
            [
                support.legacy_row(SYMBOL="ALPHA", SERIES="EQ", ISIN=ISIN_A),
                support.legacy_row(SYMBOL="BETA", SERIES="EQ", ISIN=ISIN_B),
            ]
        )
        result = build_associations(build.rows)
        self.assertEqual([identity.security_id for identity in result.identities], [ISIN_B, ISIN_A])
        self.assertEqual(result.totals()["identities"], 2)

    def test_isin_normalization_keys_by_upper_trim_but_keeps_the_source_value(self):
        build = member_2024_07_05(
            [support.legacy_row(SYMBOL="ALPHA", SERIES="EQ", ISIN=" ine144j01027 ")]
        )
        result = build_associations(build.rows)
        self.assertEqual(result.identities[0].security_id, ISIN_A)
        self.assertEqual(result.identities[0].isin_list, (ISIN_A,))
        self.assertEqual(result.identities[0].identity_basis, contract.IDENTITY_KEY_BASIS)
        self.assertEqual(result.identities[0].non_promotion_note, contract.IDENTITY_NON_PROMOTION_NOTE)


class IdentityFailClosedTests(unittest.TestCase):
    def test_blank_isin_rows_are_unkeyed_and_never_assigned_an_identity(self):
        build = member_2024_07_05(
            [
                support.legacy_row(SYMBOL="ALPHA", SERIES="EQ", ISIN=""),
                support.legacy_row(SYMBOL="BETA", SERIES="BE", ISIN="   "),
            ]
        )
        result = build_associations(build.rows)
        self.assertEqual(result.identities, ())
        self.assertEqual(len(result.unkeyed), 1)
        group = result.unkeyed[0]
        self.assertEqual(group.reason, contract.UNKEYED_REASON_BLANK_ISIN)
        self.assertEqual(len(group.line_numbers), 2)
        self.assertEqual(result.totals()["unkeyed_rows"], 2)

    def test_invalid_isin_flags_never_gate_or_dekey(self):
        # D05 §5 hard rule: ISIN validity is informational; a flagged row is still keyed.
        build = member_2024_07_05(
            [
                support.legacy_row(SYMBOL="ALPHA", SERIES="EQ", ISIN="INE144J01028"),  # bad check digit
                support.legacy_row(SYMBOL="BETA", SERIES="EQ", ISIN="IN0144J01027"),  # wrong length
            ]
        )
        flagged = [row for row in build.rows if row.flag_names()]
        self.assertTrue(flagged, "the fixture rows must carry validity flags")
        result = build_associations(build.rows)
        self.assertEqual(result.totals()["identities"], 2)
        self.assertEqual(result.unkeyed, ())

    def test_validity_stays_informational_and_never_asserts_invalidity(self):
        valid = member_on("2024-07-05", [{"SYMBOL": "ALPHA", "SERIES": "EQ", "ISIN": ISIN_A}])
        result = build_associations(valid.rows)
        self.assertIs(result.identities[0].is_valid_isin_format, True)
        self.assertEqual(dict(result.identities[0].observations)["isin_validity_values"], "VALID")

        flagged = member_on("2024-07-05", [{"SYMBOL": "ALPHA", "SERIES": "EQ", "ISIN": "INE144J01028"}])
        flagged_result = build_associations(flagged.rows)
        self.assertEqual(flagged_result.totals()["identities"], 1)
        self.assertIsNone(flagged_result.identities[0].is_valid_isin_format)
        self.assertEqual(
            dict(flagged_result.identities[0].observations)["isin_validity_values"],
            "INVALID_CHECKDIGIT",
        )

    def test_overlay_rows_are_excluded_from_the_chain_but_counted(self):
        build = member_2024_07_05(
            [
                support.legacy_row(SYMBOL="ALPHA", SERIES="EQ", ISIN=ISIN_A),
                support.legacy_row(SYMBOL="ALPHA", SERIES="BL", ISIN=ISIN_A),
                support.legacy_row(SYMBOL="BETA", SERIES="T0", ISIN=ISIN_B),
            ]
        )
        result = build_associations(build.rows)
        self.assertEqual(result.totals()["identities"], 1)
        self.assertEqual(result.totals()["associations"], 1)
        self.assertEqual(dict(result.overlay_rows_excluded), {"BL": 1, "T0": 1})
        self.assertEqual(result.totals()["overlay_rows_excluded"], 2)
        self.assertEqual(result.method, contract.ASSOCIATION_CHAIN_METHOD)
        # the overlay rows keep their own canonical rows (D05 §3.5.5): nothing was dropped
        self.assertEqual(len(build.rows), 3)

    def test_unresolved_series_are_carried_verbatim_and_never_interpreted(self):
        build = member_2024_07_05(
            [
                support.legacy_row(SYMBOL="ALPHA", SERIES="SF", ISIN=ISIN_A),
                support.legacy_row(SYMBOL="BETA", SERIES="BE", ISIN=ISIN_B),
            ]
        )
        result = build_associations(build.rows)
        tokens = {entry.series for identity in result.identities for entry in identity.associations}
        self.assertEqual(tokens, {"SF", "BE"})
        for identity in result.identities:
            for association in identity.associations:
                self.assertNotIn("market", association.to_dict().__str__().lower())
        # the unresolved dependency identifiers stay on the canonical rows (W1 behaviour),
        # and the association adds no interpretation of its own
        row_dependencies = {row.series: row.governance_dependencies for row in build.rows}
        self.assertEqual(row_dependencies["SF"], ("D07-OPEN-3",))
        self.assertEqual(row_dependencies["BE"], ("D07-OPEN-4",))

    def test_overlay_series_tokens_are_excluded_from_the_transition_chain(self):
        # IT is an overlay token in the governed observed set, so it is tracked as an overlay
        # row and excluded from the transition chain (the FIX-SYMBOL-HIST-01 method).
        build = member_2024_07_05(
            [
                support.legacy_row(SYMBOL="ALPHA", SERIES="IT", ISIN=ISIN_A),
                support.legacy_row(SYMBOL="ALPHA", SERIES="EQ", ISIN=ISIN_A),
            ]
        )
        result = build_associations(build.rows)
        self.assertEqual([entry.series for entry in result.identities[0].associations], ["EQ"])
        self.assertEqual(dict(result.overlay_rows_excluded), {"IT": 1})


class IdentityProvenanceAndDeterminismTests(unittest.TestCase):
    def test_every_association_resolves_to_its_contributing_members(self):
        first = member_on("2024-07-05", [{"SYMBOL": "ALPHA", "SERIES": "EQ", "ISIN": ISIN_A}])
        second = member_on("2024-07-08", [{"SYMBOL": "ALPHA", "SERIES": "EQ", "ISIN": ISIN_A}])
        build = build_associations(first.rows + second.rows)
        association = build.identities[0].associations[0]
        self.assertEqual(len(association.provenance), 2)
        self.assertEqual(
            {entry.member_name for entry in association.provenance},
            {"cm20240705.csv", "cm20240708.csv"},
        )
        for entry in association.provenance:
            self.assertEqual(len(entry.member_sha256_raw_bytes), 64)
        self.assertEqual(
            [row.member_name for row in association.contributing_rows],
            ["cm20240705.csv", "cm20240708.csv"],
        )

    def test_association_build_is_order_independent(self):
        first = member_2024_07_05(
            [
                support.legacy_row(SYMBOL="ALPHA", SERIES="EQ", ISIN=ISIN_A),
                support.legacy_row(SYMBOL="BETA", SERIES="EQ", ISIN=ISIN_B),
                support.legacy_row(SYMBOL="GAMMA", SERIES="BE", ISIN=ISIN_A),
            ]
        )
        forward = build_associations(first.rows)
        backward = build_associations(tuple(reversed(first.rows)))
        self.assertEqual(
            [identity.to_dict() for identity in forward.identities],
            [identity.to_dict() for identity in backward.identities],
        )

    def test_association_build_is_repeatable_on_the_published_samples(self):
        w2 = support.build_w2_samples()
        again = support.build_w2_samples()
        self.assertEqual(w2.associations.totals(), again.associations.totals())

    def test_sample_scale_identity_counts_are_not_corpus_claims(self):
        # The published corpus facts (7,633 tracked ISINs / 845 multi-symbol / 2,431 multi-series)
        # need the full corpus; the stratified extracts can only demonstrate the mechanism.
        w2 = support.build_w2_samples()
        summary = support.w2_evidence("symbol_hist")
        totals = w2.associations.totals()
        self.assertLess(totals["identities"], summary["distinct_tracked_isins"])
        self.assertLess(totals["identities_with_multiple_symbols"], summary["isins_with_multiple_symbols"])
        self.assertEqual(
            summary["distinct_tracked_isins"], 7633
        )
        self.assertEqual(summary["isins_with_multiple_symbols"], 845)
        self.assertIn("I4", contract.D01_RECOMPUTATION_BOUNDARY)


if __name__ == "__main__":
    unittest.main()
