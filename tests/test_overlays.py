"""Overlay observations: structure, non-gating flags, and no aggregation (D05 §3.5, §5)."""

from __future__ import annotations

import unittest

from tests import support
from nse_engine import contract
from nse_engine.pipeline import EngineConfig


def overlay_member_rows(overlay_quantity="191700", base_quantity="191700", overlay_isin="INE144J01027",
                        base_isin="INE144J01027", extra_bases=0, overlay_series="BL", base_series="EQ"):
    rows = [support.legacy_row(SERIES=overlay_series, ISIN=overlay_isin, TOTTRDQTY=overlay_quantity)]
    if base_isin is not None:
        rows.append(support.legacy_row(SERIES=base_series, ISIN=base_isin, TOTTRDQTY=base_quantity))
    for index in range(extra_bases):
        rows.append(
            support.legacy_row(SERIES="BE", ISIN=base_isin, TOTTRDQTY=str(int(base_quantity) + index + 1))
        )
    return rows


class OverlayObservationTests(unittest.TestCase):
    def test_base_same_isin_observation(self):
        build = support.parse_synthetic(
            support.legacy_member(overlay_member_rows(overlay_quantity="200", base_quantity="100")),
            expected_source_date="2016-09-20",
        )
        self.assertEqual(len(build.observations), 1)
        observation = build.observations[0]
        self.assertEqual(observation.match_type, contract.MATCH_TYPE_BASE_SAME_ISIN)
        self.assertEqual(observation.qty_rel, "gt")
        self.assertEqual(observation.overlay_series, "BL")
        self.assertEqual(observation.business_date, "2016-09-20")
        self.assertEqual(observation.isin, "INE144J01027")
        self.assertEqual(observation.base_line_number, 3)
        self.assertEqual(observation.base_candidate_count, 1)
        self.assertEqual(observation.series_match_basis, contract.MATCH_BASIS_SERIES_VERBATIM)
        self.assertEqual(observation.isin_match_basis, contract.MATCH_BASIS_ISIN_NORMALIZED)
        self.assertEqual(observation.base_selection_rule, contract.BASE_SELECTION_RULE)

    def test_quantity_relations(self):
        for overlay_quantity, base_quantity, expected in (
            ("100", "200", "lt"),
            ("200", "200", "eq"),
            ("300", "200", "gt"),
        ):
            with self.subTest(overlay=overlay_quantity, base=base_quantity):
                build = support.parse_synthetic(
                    support.legacy_member(
                        overlay_member_rows(overlay_quantity=overlay_quantity, base_quantity=base_quantity)
                    ),
                    expected_source_date="2016-09-20",
                )
                self.assertEqual(build.observations[0].qty_rel, expected)

    def test_qty_gt_base_flag_is_non_gating_and_row_is_retained(self):
        build = support.parse_synthetic(
            support.legacy_member(overlay_member_rows(overlay_quantity="500000")),
            expected_source_date="2016-09-20",
        )
        overlay_row = build.rows[0]
        self.assertEqual(overlay_row.flag_names(), (contract.FLAG_OVERLAY_QTY_GT_BASE,))
        self.assertIn("no aggregation is applied", overlay_row.flags[0].detail)
        self.assertEqual(len(build.rows), 2)  # nothing merged or dropped

    def test_orphan_without_base_row_is_flagged(self):
        build = support.parse_synthetic(
            support.legacy_member(overlay_member_rows(base_isin=None)),
            expected_source_date="2016-09-20",
        )
        self.assertEqual(len(build.rows), 1)
        row = build.rows[0]
        self.assertEqual(row.flag_names(), (contract.FLAG_ORPHAN_NO_BASE_ROW,))
        observation = build.observations[0]
        self.assertEqual(observation.match_type, contract.MATCH_TYPE_NO_BASE_ORPHAN)
        self.assertIsNone(observation.base_line_number)
        self.assertIsNone(observation.qty_rel)
        self.assertEqual(observation.base_candidate_count, 0)

    def test_orphan_with_blank_isin_is_flagged_with_explicit_reason(self):
        build = support.parse_synthetic(
            support.legacy_member(
                [support.legacy_row(SERIES="IT", ISIN=""), support.legacy_row(ISIN="INE002A01018")]
            ),
            expected_source_date="2016-09-20",
        )
        observation = build.observations[0]
        self.assertEqual(observation.match_type, contract.MATCH_TYPE_NO_BASE_ORPHAN)
        self.assertIn("no non-blank ISIN", observation.qty_rel_undetermined_reason)
        self.assertEqual(build.rows[0].flag_names(), (contract.FLAG_ORPHAN_NO_BASE_ROW,))

    def test_undetermined_quantity_is_recorded_not_guessed(self):
        build = support.parse_synthetic(
            support.legacy_member(overlay_member_rows(overlay_quantity="")),
            expected_source_date="2016-09-20",
        )
        observation = build.observations[0]
        self.assertIsNone(observation.qty_rel)
        self.assertIn("blank", observation.qty_rel_undetermined_reason)
        self.assertEqual(build.rows[0].flag_names(), ())  # no flag invented for this case

    def test_base_row_after_the_overlay_row_in_member_order_is_still_matched(self):
        # The published evidence structure indexes the member before comparing, so member
        # order does not change the observation.
        rows = [
            support.legacy_row(SERIES="BL", ISIN="INE144J01027", TOTTRDQTY="100"),
            support.legacy_row(SERIES="EQ", ISIN="INE144J01027", TOTTRDQTY="500"),
        ]
        build = support.parse_synthetic(
            support.legacy_member(rows), expected_source_date="2016-09-20"
        )
        observation = build.observations[0]
        self.assertEqual(observation.match_type, contract.MATCH_TYPE_BASE_SAME_ISIN)
        self.assertEqual(observation.qty_rel, "lt")
        self.assertEqual(observation.base_line_number, 3)
        self.assertEqual(build.rows[0].flag_names(), ())

    def test_multiple_base_candidates_are_counted_and_selection_is_documented(self):
        build = support.parse_synthetic(
            support.legacy_member(overlay_member_rows(base_quantity="100", extra_bases=2)),
            expected_source_date="2016-09-20",
        )
        observation = build.observations[0]
        self.assertEqual(observation.base_candidate_count, 3)
        self.assertEqual(observation.base_line_number, 3)  # first non-overlay row for that ISIN
        self.assertEqual(observation.qty_rel, "gt")  # 191700 vs 100

    def test_overlay_rows_keep_their_own_canonical_rows(self):
        build = support.parse_synthetic(
            support.legacy_member(
                [
                    support.legacy_row(SERIES="BL"),
                    support.legacy_row(SERIES="EQ"),
                    support.legacy_row(SERIES="T0", ISIN="INE002A01018"),
                    support.legacy_row(SERIES="EQ", ISIN="INE002A01018"),
                ]
            ),
            expected_source_date="2016-09-20",
        )
        self.assertEqual(len(build.rows), 4)
        self.assertEqual([row.series for row in build.rows], ["BL", "EQ", "T0", "EQ"])
        self.assertEqual(len(build.observations), 2)
        self.assertEqual(build.observations[0].overlay_series, "BL")
        self.assertEqual(build.observations[1].overlay_series, "T0")

    def test_match_type_vocabulary_is_the_governed_pair_only(self):
        self.assertEqual(contract.MATCH_TYPES, ("BASE_SAME_ISIN", "NO_BASE_ORPHAN"))
        build = support.parse_synthetic(
            support.legacy_member(overlay_member_rows()), expected_source_date="2016-09-20"
        )
        seen = {observation.match_type for observation in build.observations}
        self.assertTrue(seen <= set(contract.MATCH_TYPES))

    def test_series_matching_is_verbatim_never_case_folded(self):
        build = support.parse_synthetic(
            support.legacy_member([support.legacy_row(SERIES="bl"), support.legacy_row(SERIES="EQ")]),
            expected_source_date="2016-09-20",
        )
        self.assertEqual(build.observations, ())

    def test_requests_series_states_that_a_lowercase_series_token_is_not_an_overlay(self):
        member = support.legacy_member(
            [support.legacy_row(SERIES="t0", ISIN="INE002A01018"), support.legacy_row(ISIN="INE002A01018")]
        )
        build = support.parse_synthetic(member, expected_source_date="2016-09-20")
        self.assertEqual(build.observations, ())
        self.assertEqual(build.rows[0].governance_dependencies, ())  # no invented series reading


class OverlayConfigTests(unittest.TestCase):
    def test_config_drives_which_rows_receive_observations(self):
        member = support.legacy_member(
            [support.legacy_row(SERIES="BL"), support.legacy_row(SERIES="EQ")]
        )
        configured = support.parse_synthetic(
            member, expected_source_date="2016-09-20", config=EngineConfig(overlay_series=("BL",))
        )
        self.assertEqual(len(configured.observations), 1)

        disabled = support.parse_synthetic(
            member,
            expected_source_date="2016-09-20",
            config=EngineConfig(emit_overlay_observations=False),
        )
        self.assertEqual(disabled.observations, ())
        self.assertEqual(len(disabled.rows), 2)
        self.assertEqual(disabled.rows[0].overlay, None)

    def test_default_config_transcribes_the_observed_set(self):
        self.assertEqual(
            EngineConfig().overlay_series, ("BL", "BO", "T0", "IT", "IL")
        )
        self.assertEqual(EngineConfig().overlay_series, contract.OVERLAY_SERIES_OBSERVED)
        self.assertIn("NOT an eligibility", contract.OVERLAY_SERIES_CAVEAT)
        self.assertIn("no merge/drop/dedupe", contract.OVERLAY_SERIES_CAVEAT)

    def test_config_fingerprint_is_stable_and_config_sensitive(self):
        self.assertEqual(EngineConfig().fingerprint(), EngineConfig().fingerprint())
        self.assertNotEqual(
            EngineConfig().fingerprint(), EngineConfig(overlay_series=("BL",)).fingerprint()
        )

    def test_observation_carries_the_non_assumption_caveat(self):
        build = support.parse_synthetic(
            support.legacy_member(overlay_member_rows()), expected_source_date="2016-09-20"
        )
        self.assertEqual(build.observations[0].caveat, contract.OVERLAY_SERIES_CAVEAT)
        self.assertIn("caveat", build.rows[0].overlay)


if __name__ == "__main__":
    unittest.main()
