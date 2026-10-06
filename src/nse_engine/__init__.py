"""NSE Historical Data Engine — W1 / I1 parser + W2 / I2 derivations.

NON-PRODUCTION. Implemented under D07 (scoped engine implementation authorization) on the
D05/D06 adopted canonical-model contract. No persistence, no ingestion, no live NSE access,
no credentials, no corpus mutation.

What W1 provides
----------------
``nse_engine.parsing``    name-keyed/header-aware member parser for both governed families
                          (``legacy13``, ``udiff34``) with the D05 §7 tolerances and
                          fail-closed width/malformed-record handling.
``nse_engine.rows``       canonical ``SecurityRow`` construction (D05 §3.1), non-gating
                          validity flags (D05 §5), ISIN handling (D05 §5/§6.1) and
                          unresolved-semantics identifiers (D07 §13-G).
``nse_engine.overlays``   overlay observations (D05 §3.5.1) — observations only.
``nse_engine.blocked``    fail-closed stubs naming every D07 §13-B/C governance dependency.
``nse_engine.serialize``  LF/deterministic canonical serialization and evidence (D05 §9).
``nse_engine.pipeline``   the reference assembly of the above.

What W2 / I2 adds (D07 §13-A; non-production)
---------------------------------------------
``nse_engine.calendar``         calendar derivation from D01 file presence + sourced labels;
                               unresolved dates carried as explicit unresolved states (D05 §3.4).
``nse_engine.identity``         correlation scopes and ``DatedAssociation`` rows (D05 §3.2-3.3),
                               observed-range intervals, fail-closed on unkeyable rows.
``nse_engine.metrics``          D01 metric re-computation: row-level formulas and the corpus
                               metric algebra over the frozen per-file evidence (D05 §4).
``nse_engine.overlay_evidence`` published overlay fixture accounting and the decisive-cause
                               disposition of the W1-DIV-OVERLAY evidence divergence.

Still deliberately NOT provided (deferred/blocked as before): cross-era continuity policy,
eligibility/ETF/master joins (DEC-1), corporate-action/delisting semantics, persistence,
ingestion, query/API/UI/reporting surfaces. Every unresolved semantic fails closed.
"""

from __future__ import annotations

from . import (
    blocked,
    calendar,
    contract,
    errors,
    evidence_inputs,
    identity,
    metrics,
    overlay_evidence,
    overlays,
    parsing,
    pipeline,
    provenance,
    rows,
    serialize,
)
from .calendar import CalendarDay, CalendarResult, MemberDateFact, derive_calendar
from .contract import SPEC_VERSION, TOOL_NAME, TOOL_VERSION
from .evidence_inputs import (
    CalendarLabelRecord,
    CircularHolidayRecord,
    ExtractCoverageRecord,
    FileMetricRecord,
    InventoryFileRecord,
    OverlayFixtureRow,
)
from .identity import (
    AssociationBuild,
    DatedAssociation,
    SecurityIdentity,
    UnkeyedRowGroup,
    build_associations,
)
from .metrics import (
    RowMetrics,
    compute_row_metrics,
    fold_file_metrics,
    series_class_rollup,
    series_universe,
)
from .overlay_evidence import (
    OverlayFixtureAccounting,
    OverlayFixtureDisposition,
    account_overlay_fixture,
    determine_overlay_disposition,
)
from .pipeline import W2Build, build_w2, member_date_facts
from .overlays import OverlayObservation, link_overlay_observations
from .parsing import SourceDescriptor, parse_member_bytes
from .pipeline import DEFAULT_CONFIG, CanonicalBuild, EngineConfig, build_canonical
from .provenance import Provenance, dual_hash, lf_normalize, tool_fingerprint
from .rows import Flag, SecurityRow, build_rows, iso6166_check_digit, isin_validity, normalize_isin
from .serialize import build_evidence, canonical_json, evidence_json, rows_jsonl, text_sha256

__all__ = [
    "DEFAULT_CONFIG",
    "AssociationBuild",
    "CalendarDay",
    "CalendarLabelRecord",
    "CalendarResult",
    "CanonicalBuild",
    "CircularHolidayRecord",
    "DatedAssociation",
    "EngineConfig",
    "ExtractCoverageRecord",
    "FileMetricRecord",
    "Flag",
    "InventoryFileRecord",
    "MemberDateFact",
    "OverlayFixtureAccounting",
    "OverlayFixtureDisposition",
    "OverlayFixtureRow",
    "OverlayObservation",
    "Provenance",
    "RowMetrics",
    "SecurityIdentity",
    "SecurityRow",
    "SourceDescriptor",
    "SPEC_VERSION",
    "TOOL_NAME",
    "TOOL_VERSION",
    "UnkeyedRowGroup",
    "W2Build",
    "account_overlay_fixture",
    "blocked",
    "build_associations",
    "build_w2",
    "build_canonical",
    "build_evidence",
    "build_rows",
    "calendar",
    "canonical_json",
    "compute_row_metrics",
    "contract",
    "derive_calendar",
    "determine_overlay_disposition",
    "evidence_inputs",
    "fold_file_metrics",
    "identity",
    "member_date_facts",
    "metrics",
    "overlay_evidence",
    "series_class_rollup",
    "series_universe",
    "dual_hash",
    "errors",
    "evidence_json",
    "iso6166_check_digit",
    "isin_validity",
    "lf_normalize",
    "link_overlay_observations",
    "normalize_isin",
    "overlays",
    "parse_member_bytes",
    "parsing",
    "pipeline",
    "provenance",
    "rows",
    "rows_jsonl",
    "serialize",
    "text_sha256",
    "tool_fingerprint",
]

__version__ = TOOL_VERSION
