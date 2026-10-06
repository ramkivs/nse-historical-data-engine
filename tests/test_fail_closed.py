"""Fail-closed behaviour and the no-unauthorized-semantics boundary (D07 §6, §13-B/C, §14)."""

from __future__ import annotations

import ast
import os
import unittest

from tests import support
from nse_engine import blocked, contract
from nse_engine.errors import GovernanceBlockedError

ENGINE_DIR = os.path.join(support.SRC_DIR, "nse_engine")
PARSE_PATH_MODULES = ("parsing", "rows", "overlays", "pipeline", "serialize")


def read_module(module: str) -> str:
    with open(os.path.join(ENGINE_DIR, module + ".py"), encoding="utf-8") as handle:
        return handle.read()


def code_only(source: str) -> str:
    """Source with docstrings and comment lines removed (documentation is not behaviour)."""
    text = source
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            docstring = ast.get_docstring(node, clean=False)
            if docstring:
                text = text.replace(docstring, "")
    kept = []
    for line in text.splitlines():
        if line.strip().startswith("#"):
            continue
        kept.append(line.split("#", 1)[0] if "#" in line else line)
    return "\n".join(kept)


class BlockedStubTests(unittest.TestCase):
    def test_every_stub_raises_and_names_its_dependency(self):
        for record in blocked.BLOCKED_DEPENDENCIES:
            with self.subTest(operation=record.operation):
                with self.assertRaises(GovernanceBlockedError) as caught:
                    record.stub()
                self.assertEqual(caught.exception.dependency_id, record.dependency_id)
                self.assertEqual(caught.exception.operation, record.operation)
                self.assertIn(record.dependency_id, str(caught.exception))
                self.assertTrue(record.reference)

    def test_registry_covers_each_d07_section_13_b_c_decision(self):
        operations = set(blocked.BLOCKED_OPERATIONS)
        for required in (
            "eligibility_predicate",
            "etf_register_join",
            "master_snapshot_dated_association",
            "delisting_marker",
            "corporate_action_colocation",
            "t0_volume_inclusion_rule",
            "it_series_interpretation",
            "sf_series_interpretation",
            "be_rights_vs_t2t_split",
            "sgb_stk_semantics",
            "xcont_boundary_continuity_policy",
            "fininstrm_id_namespace_resolution",
            "calendar_gap_label",
            "sme_surveillance_stage_classification",
        ):
            self.assertIn(required, operations)

    def test_dependency_ids_are_the_governed_identifiers(self):
        governed = {dep_id for dep_id, _label in contract.GOVERNANCE_DEPENDENCIES}
        for record in blocked.BLOCKED_DEPENDENCIES:
            if record.dependency_id not in ("NOT-AUTHORIZED", "D05-DEFERRED-CAL-LEGACY", "D05-OPEN-F3"):
                self.assertIn(record.dependency_id, governed)

    def test_stub_names_are_unique(self):
        self.assertEqual(len(blocked.BLOCKED_OPERATIONS), len(set(blocked.BLOCKED_OPERATIONS)))

    def test_blocked_stubs_are_not_reachable_from_the_parse_path(self):
        names = [record.operation for record in blocked.BLOCKED_DEPENDENCIES]
        for module in PARSE_PATH_MODULES:
            source = read_module(module)
            for name in names:
                self.assertNotIn(name + "(", source, "%s references blocked stub %s" % (module, name))
            self.assertNotIn("import blocked", source)
            self.assertNotIn("from .blocked", source)

    def test_no_module_in_the_engine_raises_governance_errors_outside_the_stub_module(self):
        for module in PARSE_PATH_MODULES:
            self.assertNotIn("GovernanceBlockedError(", read_module(module))


class NoUnauthorizedSemanticsTests(unittest.TestCase):
    """The engine must not evaluate eligibility, aggregate, dedupe, or resolve OPEN items."""

    MIXED_MEMBER_ROWS = (
        support.legacy_row(SYMBOL="ALPHA", SERIES="EQ", ISIN="INE144J01027"),
        support.legacy_row(SYMBOL="BETA", SERIES="BE", ISIN="INE144J01027"),
        support.legacy_row(SYMBOL="GAMMA", SERIES="T0", ISIN="INE144J01027"),
        support.legacy_row(SYMBOL="DELTA", SERIES="IT", ISIN="INE144J01027"),
        support.legacy_row(SYMBOL="EPS", SERIES="SF", ISIN="INE144J01027"),
        support.legacy_row(SYMBOL="ZETA", SERIES="GB", ISIN="IN0020200104"),
        support.legacy_row(SYMBOL="ETA", SERIES="SM", ISIN="INE144J01027"),
        support.legacy_row(SYMBOL="THETA", SERIES="ST", ISIN="INE144J01027"),
    )

    def _build(self):
        return support.parse_synthetic(
            support.legacy_member(self.MIXED_MEMBER_ROWS), expected_source_date="2016-09-20"
        )

    def test_every_row_is_retained_regardless_of_series_or_isin(self):
        build = self._build()
        self.assertEqual(len(build.rows), len(self.MIXED_MEMBER_ROWS))
        self.assertEqual(len(build.quarantined), 0)

    def test_no_series_based_filtering_or_reclassification(self):
        build = self._build()
        self.assertEqual(
            [row.series for row in build.rows], ["EQ", "BE", "T0", "IT", "SF", "GB", "SM", "ST"]
        )

    def test_unresolved_series_carry_dependency_annotations_only(self):
        build = self._build()
        dependencies = {row.series: row.governance_dependencies for row in build.rows}
        self.assertEqual(dependencies["BE"], ("D07-OPEN-4",))
        self.assertEqual(dependencies["T0"], ("D07-OPEN-1",))
        self.assertEqual(dependencies["IT"], ("D07-OPEN-2",))
        self.assertEqual(dependencies["SF"], ("D07-OPEN-3",))
        self.assertEqual(dependencies["GB"], ())  # SGB-STK mapping deliberately not inferred
        self.assertEqual(dependencies["SM"], ())  # SME-stage classification deliberately absent
        self.assertEqual(dependencies["EQ"], ())

    def test_governance_ids_not_attached_are_documented_with_reasons(self):
        for dep_id in ("D07-OPEN-5", "D07-OPEN-6", "D07-OPEN-8", "D07-OPEN-9"):
            self.assertIn(dep_id, contract.GOVERNANCE_IDS_NOT_ATTACHED_BY_W1)
            self.assertTrue(contract.GOVERNANCE_IDS_NOT_ATTACHED_BY_W1[dep_id])

    def test_no_aggregation_fields_are_produced(self):
        build = self._build()
        for row in build.rows:
            data = row.to_dict()
            for key in data:
                self.assertNotIn(key.lower(), ("total_volume", "total_value", "aggregate", "sum",
                                               "distinct_isin_count", "eligible", "eligibility",
                                               "is_eligible", "delisted", "delisting"))

    def test_rows_are_not_deduplicated(self):
        rows = (support.legacy_row(), support.legacy_row())
        build = support.parse_synthetic(
            support.legacy_member(rows), expected_source_date="2016-09-20"
        )
        self.assertEqual(len(build.rows), 2)
        self.assertEqual([row.line_number for row in build.rows], [2, 3])

    def test_row_never_carries_a_gating_field(self):
        build = self._build()
        data = build.rows[0].to_dict()
        self.assertNotIn("eligible", data)
        self.assertNotIn("gating", data)
        self.assertEqual(contract.GATING_FLAG_NAMES, ())

    def test_quarantine_is_structural_only_and_never_semantic(self):
        for code, _description, flags in contract.QUARANTINE_REASONS:
            with self.subTest(code=code):
                self.assertNotIn("semantic", code)
                for flag in flags:
                    self.assertIn(flag, contract.FLAG_SEVERITY)

    def test_engine_code_contains_no_eligibility_or_aggregation_call(self):
        # contract.py is a transcription module whose string constants quote governance text
        # (dependency labels, caveats, the divergence record); it contains no logic. The code
        # path modules must contain none of these tokens at all.
        forbidden = ("eligibility", "is_eligible", "eq_etf", "etf_list", "groupby", "aggregate(")
        for module in PARSE_PATH_MODULES:
            source = code_only(read_module(module))
            for token in forbidden:
                self.assertNotIn(token, source, "%s code must not reference %r" % (module, token))

    def test_disallowed_semantic_terms_do_not_appear_as_code(self):
        for module in PARSE_PATH_MODULES:
            source = code_only(read_module(module))
            for token in ("rights_entitlement", "t2t_state", "surveillance_stage", "is_delisted",
                          "is_etf", "sgb", "xcont_", "eligibility_predicate", "production_ingestion"):
                self.assertNotIn(token, source, "%s code must not reference %r" % (module, token))


if __name__ == "__main__":
    unittest.main()
