"""Fail-closed stubs naming every governance dependency that blocks implementation.

D07 §13-B/C list what is blocked by unresolved semantics (D07 §9) and by DEC-1;
D07 §14 requires W1 to carry "fail-closed stubs naming each §13-B/C dependency".
D07 §6 states the governing principle: implementation authority NEVER promotes a
non-assumption into a rule — where the engine would need a frozen/OPEN semantic it MUST
fail closed with an explicit governance dependency.

Each stub below raises :class:`~nse_engine.errors.GovernanceBlockedError`; none of them is
called from the W1 parse -> row-build path (a test enforces that by inspection of the
engine source). They exist so a later increment cannot silently "just decide" one of these.

Nothing in this module computes anything: no defaults, no fallbacks, no "temporary"
interpretations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, NoReturn, Tuple

from .errors import GovernanceBlockedError

CATEGORY_DEC1 = "DEC-1 (DEFERRED)"
CATEGORY_OPEN = "OPEN-SEMANTICS (D07 §9)"
CATEGORY_DEFERRED = "DEFERRED"
CATEGORY_OUT_OF_SCOPE = "OUT OF SCOPE"


@dataclass(frozen=True)
class BlockedDependency:
    dependency_id: str
    operation: str
    category: str
    reason: str
    reference: str
    stub: Callable[..., NoReturn]

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "dependency_id": self.dependency_id,
            "operation": self.operation,
            "reason": self.reason,
            "reference": self.reference,
        }


def _declare(
    dependency_id: str, operation: str, category: str, reason: str, reference: str
) -> Tuple[Callable[..., NoReturn], BlockedDependency]:
    def stub(*_args, **_kwargs) -> NoReturn:
        raise GovernanceBlockedError(
            dependency_id=dependency_id,
            operation=operation,
            reason=reason,
            reference=reference,
        )

    stub.__name__ = operation
    stub.__qualname__ = operation
    stub.__doc__ = (
        "Fail-closed stub for %r. Blocked by %s [%s] — %s Reference: %s. "
        "Always raises GovernanceBlockedError; never returns a value."
        % (operation, dependency_id, category, reason, reference)
    )
    record = BlockedDependency(
        dependency_id=dependency_id,
        operation=operation,
        category=category,
        reason=reason,
        reference=reference,
        stub=stub,
    )
    return stub, record


# ------------------------------------------------------------------ DEC-1 (D07 §13-C)
eligibility_predicate, _DEP_ELIGIBILITY = _declare(
    "DEC-1",
    "eligibility_predicate",
    CATEGORY_DEC1,
    "no eligibility predicate is part of the canonical model; the candidate rule requires the deferred "
    "DEC-1 master acquisition plus consistency and acceptance",
    "D05 §6.5; D06 Decision B; D07 §13-C",
)

etf_register_join, _DEP_ETF_JOIN = _declare(
    "DEC-1",
    "etf_register_join",
    CATEGORY_DEC1,
    "ETF exclusion requires the official ETF register (eq_etfseclist.csv) and a validated ISIN join",
    "D05 §3.3, §6.5; D04B; D07 §13-C",
)

master_snapshot_dated_association, _DEP_MASTER_SNAPSHOT = _declare(
    "DEC-1",
    "master_snapshot_dated_association",
    CATEGORY_DEC1,
    "master-snapshot dated associations require monthly Masters snapshots; the master is not assumed "
    "authoritative",
    "D05 §3.3; D05 §12 F17; D07 §13-C",
)

delisting_marker, _DEP_DELISTING = _declare(
    "DEC-1",
    "delisting_marker",
    CATEGORY_DEC1,
    "delisting markers require DEC-1 master evidence; one-sided ISIN residuals are not interpreted",
    "D05 §3.2; D05 §12 F9/F17; D07 §13-C",
)

corporate_action_colocation, _DEP_CORP_ACTION = _declare(
    "DEC-1",
    "corporate_action_colocation",
    CATEGORY_DEC1,
    "corporate-action co-location semantics are not modeled and require DEC-1 evidence",
    "D05 §12 F16; D07 §13-C",
)

# ------------------------------------------------------------------ OPEN-SEMANTICS (D07 §13-B)
t0_volume_inclusion_rule, _DEP_T0 = _declare(
    "D07-OPEN-1",
    "t0_volume_inclusion_rule",
    CATEGORY_OPEN,
    "T0 volume-inclusion semantics are unresolved; overlay observations are emitted and no aggregate rule exists",
    "D05 §3.5.3; D06 §8.1; D07 §13-B",
)

it_series_interpretation, _DEP_IT = _declare(
    "D07-OPEN-2",
    "it_series_interpretation",
    CATEGORY_OPEN,
    "the IT series definition was never obtained; IT semantics are FROZEN and uninterpreted",
    "D05 §3.5; D05 §12 F11; D07 §13-B",
)

sf_series_interpretation, _DEP_SF = _declare(
    "D07-OPEN-3",
    "sf_series_interpretation",
    CATEGORY_OPEN,
    "no official SF code definition was obtained; SF rows stay unclassified",
    "D05 §12 F12; D07 §13-B",
)

be_rights_vs_t2t_split, _DEP_BE_SPLIT = _declare(
    "D07-OPEN-4",
    "be_rights_vs_t2t_split",
    CATEGORY_OPEN,
    "BE rights-entitlement vs T2T row-level split is unresolved; the RE-prefix heuristic is evidence-only",
    "D05 §12 F13; D07 §13-B",
)

sgb_stk_semantics, _DEP_SGB = _declare(
    "D07-OPEN-5",
    "sgb_stk_semantics",
    CATEGORY_OPEN,
    "the SGB-STK documentation contradiction is unresolved; no security-class reading is authorized",
    "D05 §12 F14; D07 §13-B",
)

xcont_boundary_continuity_policy, _DEP_XCONT = _declare(
    "D07-OPEN-6",
    "xcont_boundary_continuity_policy",
    CATEGORY_OPEN,
    "XCONT boundary continuity is a policy decision on top of the 83/122 UNINTERPRETED residuals; only "
    "match storage is authorized, and that is not W1 scope",
    "D05 §3.2; D05 §12 F9; D07 §13-B",
)

fininstrm_id_namespace_resolution, _DEP_FININSTRMID = _declare(
    "D07-OPEN-7",
    "fininstrm_id_namespace_resolution",
    CATEGORY_OPEN,
    "FinInstrmId namespace semantics are FROZEN; the column is opaque, is never an identity and is never joined",
    "D05 §6.2; D05 §12 F2; D07 §13-B",
)

calendar_gap_label, _DEP_CAL_GAP = _declare(
    "D07-OPEN-8",
    "calendar_gap_label",
    CATEGORY_OPEN,
    "three calendar dates (2024-11-20, 2025-10-20, 2026-01-15) are unexplained by obtained circulars",
    "D05 §3.4; evidence/d04/DEC2_CAL_LABELS.json; D07 §13-B",
)

sme_surveillance_stage_classification, _DEP_SME = _declare(
    "D07-OPEN-9",
    "sme_surveillance_stage_classification",
    CATEGORY_OPEN,
    "SME surveillance-stage detail for the corpus era is unresolved; SM/ST/SO rows are not classified",
    "D04B §1; D05 §3.3; D07 §13-B",
)

legacy_era_holiday_label, _DEP_LEGACY_HOLIDAY = _declare(
    "D05-DEFERRED-CAL-LEGACY",
    "legacy_era_holiday_label",
    CATEGORY_DEFERRED,
    "legacy-era (2016-2023) holiday labels were never retrieved and MUST NOT be invented",
    "D05 §3.4; D05 §12 F8",
)

undocumented_transition_continuity, _DEP_TRANSITION = _declare(
    "D05-OPEN-F3",
    "undocumented_transition_continuity",
    CATEGORY_OPEN,
    "series transitions that match no documented exchange action remain OPEN-SEMANTICS; no continuity "
    "policy is inferred",
    "D05 §3.3; D05 §12 F3",
)

# ------------------------------------------------------------------ W1 boundary (D07 §13-D)
production_ingestion, _DEP_PRODUCTION = _declare(
    "NOT-AUTHORIZED",
    "production_ingestion",
    CATEGORY_OUT_OF_SCOPE,
    "production ingestion, live NSE access, credentials and provider integration are explicitly outside "
    "the authorized scope",
    "D07 §13-D; W1 prompt §6",
)

authoritative_storage_decision, _DEP_STORAGE = _declare(
    "NOT-AUTHORIZED",
    "authoritative_storage_decision",
    CATEGORY_OUT_OF_SCOPE,
    "Parquet-vs-database authoritative-storage and durable output/persistence contracts are not decided; "
    "W1 performs no persistence",
    "D05 §2 L2; D07 §13-D; W1 prompt §6",
)

BLOCKED_DEPENDENCIES: Tuple[BlockedDependency, ...] = (
    _DEP_ELIGIBILITY,
    _DEP_ETF_JOIN,
    _DEP_MASTER_SNAPSHOT,
    _DEP_DELISTING,
    _DEP_CORP_ACTION,
    _DEP_T0,
    _DEP_IT,
    _DEP_SF,
    _DEP_BE_SPLIT,
    _DEP_SGB,
    _DEP_XCONT,
    _DEP_FININSTRMID,
    _DEP_CAL_GAP,
    _DEP_SME,
    _DEP_LEGACY_HOLIDAY,
    _DEP_TRANSITION,
    _DEP_PRODUCTION,
    _DEP_STORAGE,
)

BLOCKED_OPERATIONS = tuple(record.operation for record in BLOCKED_DEPENDENCIES)
