"""NSE Historical Data Engine — W1 / I1: reference parser + canonical row builder.

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

What W1 deliberately does NOT provide (see the W1 implementation report)
-----------------------------------------------------------------------
calendar derivation, D01 metric re-computation, ``SecurityIdentity``/``DatedAssociation``
construction, cross-era continuity, eligibility/ETF/DEC-1 joins, persistence, ingestion,
analytics surfaces. Every unresolved semantic fails closed.
"""

from __future__ import annotations

from . import blocked, contract, errors, overlays, parsing, pipeline, provenance, rows, serialize
from .contract import SPEC_VERSION, TOOL_NAME, TOOL_VERSION
from .overlays import OverlayObservation, link_overlay_observations
from .parsing import SourceDescriptor, parse_member_bytes
from .pipeline import DEFAULT_CONFIG, CanonicalBuild, EngineConfig, build_canonical
from .provenance import Provenance, dual_hash, lf_normalize, tool_fingerprint
from .rows import Flag, SecurityRow, build_rows, iso6166_check_digit, isin_validity, normalize_isin
from .serialize import build_evidence, canonical_json, evidence_json, rows_jsonl, text_sha256

__all__ = [
    "DEFAULT_CONFIG",
    "CanonicalBuild",
    "EngineConfig",
    "Flag",
    "OverlayObservation",
    "Provenance",
    "SecurityRow",
    "SourceDescriptor",
    "SPEC_VERSION",
    "TOOL_NAME",
    "TOOL_VERSION",
    "blocked",
    "build_canonical",
    "build_evidence",
    "build_rows",
    "canonical_json",
    "contract",
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
