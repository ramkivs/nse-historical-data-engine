"""Governed contract constants for the NSE Historical Data Engine — W1 (I1).

This module is a *transcription* of governed decisions. It contains no independent
semantic decisions of its own. Every constant below carries an explicit reference to
its authority:

* ``docs/specs/D05_CANONICAL_MODEL_SPEC.md``          (D05 — canonical model specification)
* ``docs/investigations/D06_CANONICAL_MODEL_ADOPTION_DECISION.md`` (D06 — adoption decision)
* ``docs/investigations/D07_GATE_DEFINITION_AND_IMPLEMENTATION_AUTHORIZATION.md`` (D07 — authority)

Statements tagged [NON-ASSUMPTION] / [OPEN-SEMANTICS] / [DEFERRED] in D05 are *not*
promoted to rules here. Where a governed semantic is unresolved, this module either
(a) records the identifier of the unresolved item so records can carry it, or (b)
provides nothing at all (fail-closed), never a default.

Explicitly out of W1 scope (see ``docs`` W1 report): calendar derivation, D01 metric
re-computation, ``SecurityIdentity``/``DatedAssociation`` construction, cross-era
continuity, persistence, production ingestion.
"""

from __future__ import annotations

# ------------------------------------------------------------------ contract identity
SPEC_VERSION = "D05/1.0"  # D05 §8 provenance field: spec_version
TOOL_NAME = "nse-engine"
TOOL_VERSION = "w1-1.0.0"

#: Complete set of engine modules covered by :func:`nse_engine.provenance.tool_fingerprint`.
#: A test asserts this equals the actual module set so the fingerprint cannot drift.
ENGINE_MODULES = (
    "__init__",
    "blocked",
    "contract",
    "errors",
    "overlays",
    "parsing",
    "pipeline",
    "provenance",
    "rows",
    "serialize",
)

# ------------------------------------------------------------------ format families
# D05 §3 "Logical field mapping (literal headers) [ADOPTED — corpus-proven schemas]".
FAMILY_LEGACY = "legacy13"
FAMILY_UDIFF = "udiff34"
FORMAT_FAMILIES = (FAMILY_LEGACY, FAMILY_UDIFF)

LEGACY_HEADER_FIELDS = (
    "SYMBOL",
    "SERIES",
    "OPEN",
    "HIGH",
    "LOW",
    "CLOSE",
    "LAST",
    "PREVCLOSE",
    "TOTTRDQTY",
    "TOTTRDVAL",
    "TIMESTAMP",
    "TOTALTRADES",
    "ISIN",
)

UDIFF_HEADER_FIELDS = (
    "TradDt",
    "BizDt",
    "Sgmt",
    "Src",
    "FinInstrmTp",
    "FinInstrmId",
    "ISIN",
    "TckrSymb",
    "SctySrs",
    "XpryDt",
    "FininstrmActlXpryDt",
    "StrkPric",
    "OptnTp",
    "FinInstrmNm",
    "OpnPric",
    "HghPric",
    "LwPric",
    "ClsPric",
    "LastPric",
    "PrvsClsgPric",
    "UndrlygPric",
    "SttlmPric",
    "OpnIntrst",
    "ChngInOpnIntrst",
    "TtlTradgVol",
    "TtlTrfVal",
    "TtlNbOfTxsExctd",
    "SsnId",
    "NewBrdLotQty",
    "Rmks",
    "Rsvd1",
    "Rsvd2",
    "Rsvd3",
    "Rsvd4",
)

LEGACY_LOGICAL_WIDTH = 13
#: D05 §7.1 / D03 §15 ANOM: the legacy family occurs in two *physical* serializations
#: that are the same logical schema — 13 physical fields, and 14 physical fields whose
#: 14th field is empty (the "trailing empty field" variant). The variant is a property
#: of the member as a whole: D03 §15/§17 evidence shows 1,917 files with 14 physical
#: fields on *every* line and 2 files (2017-07-10, 2020-07-13) with 13 physical fields
#: on every line.
LEGACY_TOLERATED_PHYSICAL_WIDTH = 14
UDIFF_WIDTH = 34  # D05 §3 / §13-A: width strictly 34; "fail-closed width ≠ 34"

# ------------------------------------------------------------------ canonical field map
#: D05 §3.1 canonical field -> (legacy source column, udiff source column).
#: ``None`` means *absent in that family* — which is NOT the same as blank-as-published.
#: The header field tables above and this map are asserted to be mutually exact by tests.
CANONICAL_FIELD_MAP = (
    ("security_isin", "ISIN", "ISIN"),
    ("listing_symbol", "SYMBOL", "FinInstrmId"),
    ("series", "SERIES", "SctySrs"),
    ("security_name", None, "FinInstrmNm"),
    ("business_date", "TIMESTAMP", "TradDt"),  # derived: legacy date part, udiff as published
    ("raw_biz_dt", "TIMESTAMP", "BizDt"),
    ("price_open", "OPEN", "OpnPric"),
    ("price_high", "HIGH", "HghPric"),
    ("price_low", "LOW", "LwPric"),
    ("price_close", "CLOSE", "ClsPric"),
    ("price_last", "LAST", "LastPric"),
    ("price_prev_close", "PREVCLOSE", "PrvsClsgPric"),
    ("traded_quantity", "TOTTRDQTY", "TtlTradgVol"),
    ("traded_value", "TOTTRDVAL", "TtlTrfVal"),
    ("trades_count", "TOTALTRADES", "TtlNbOfTxsExctd"),
    ("lot_size", None, "NewBrdLotQty"),
    ("remarks", None, "Rmks"),
    ("segment", None, "Sgmt"),
    ("source", None, "Src"),
    ("instrument_type", None, "FinInstrmTp"),
    ("underlying_symbol", None, "TckrSymb"),
    ("expiry", None, "XpryDt"),
    ("actual_expiry", None, "FininstrmActlXpryDt"),
    ("strike", None, "StrkPric"),
    ("option_type", None, "OptnTp"),
    ("underlying_price", None, "UndrlygPric"),
    ("settlement_price", None, "SttlmPric"),
    ("open_interest", None, "OpnIntrst"),
    ("open_interest_change", None, "ChngInOpnIntrst"),
    ("session_id", None, "SsnId"),
    ("rsvd1", None, "Rsvd1"),
    ("rsvd2", None, "Rsvd2"),
    ("rsvd3", None, "Rsvd3"),
    ("rsvd4", None, "Rsvd4"),
)

CANONICAL_FIELDS = tuple(entry[0] for entry in CANONICAL_FIELD_MAP)

#: Canonical fields that are *derived* rather than stored verbatim from one column:
#: ``business_date`` is the legacy ``TIMESTAMP`` date part (D05 §7.2 tolerance) or the
#: UDiFF ``TradDt`` value (D05 §3.1). Its source columns are nevertheless recorded in
#: :data:`CANONICAL_FIELD_MAP` so the mapping table stays a complete transcription.
DERIVED_FIELDS = ("business_date",)

#: D05 §3.1 typed canonical fields: published text is retained verbatim AND a typed
#: accessor is offered. Types are "decimal as-published" and "integer as-published";
#: no rescaling, no rounding, no defaulting (D05 §3.1, §10.1).
DECIMAL_FIELDS = (
    "price_open",
    "price_high",
    "price_low",
    "price_close",
    "price_last",
    "price_prev_close",
    "traded_value",
)
INTEGER_FIELDS = ("traded_quantity", "trades_count")

#: D05 §3.1: fields the canonical model states are stored *verbatim* (blank stays blank).
VERBATIM_FIELDS = tuple(
    field
    for field in CANONICAL_FIELDS
    if field not in DECIMAL_FIELDS + INTEGER_FIELDS + DERIVED_FIELDS
)

# ------------------------------------------------------------------ dates
DATE_BASIS_LEGACY_FOUR_DIGIT_YEAR = "legacy_row_date_four_digit_year"
DATE_BASIS_LEGACY_TWO_DIGIT_YEAR_CROSSCHECKED = (
    "legacy_row_date_two_digit_year_cross_checked_against_source_date"
)
DATE_BASIS_UDIFF_TRADDT = "udiff_traddt"
DATE_BASES = (
    DATE_BASIS_LEGACY_FOUR_DIGIT_YEAR,
    DATE_BASIS_LEGACY_TWO_DIGIT_YEAR_CROSSCHECKED,
    DATE_BASIS_UDIFF_TRADDT,
)

#: ISO date form used for the canonical ``business_date``.
ISO_DATE_LENGTH = 10
ISO_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"

# ------------------------------------------------------------------ validity flags
# D05 §5 "Validity flags [ADOPTED — non-gating]". Severity strings are verbatim from
# the spec table. The hard rule of D05 §5 (flags never gate/filter/reject/de-rank a row
# for identity, eligibility or aggregation) is enforced by tests.
FLAG_ISIN_INVALID_CHECKDIGIT = "isin_invalid_checkdigit"
FLAG_ISIN_INVALID_LENGTH = "isin_invalid_length"
FLAG_ROW_FIELDCOUNT_MISMATCH = "row_fieldcount_mismatch"
FLAG_DATE_SOURCE_CONFLICT = "date_source_conflict"
FLAG_BIZDT_NE_TRADDT = "bizdt_ne_traddt"
FLAG_ORPHAN_NO_BASE_ROW = "orphan_no_base_row"
FLAG_OVERLAY_QTY_GT_BASE = "overlay_qty_gt_base"

VALIDITY_FLAGS = (
    (FLAG_ISIN_INVALID_CHECKDIGIT, "informational", "D05 §5; D03 Q2"),
    (FLAG_ISIN_INVALID_LENGTH, "informational", "D05 §5"),
    (FLAG_ROW_FIELDCOUNT_MISMATCH, "quarantine row-level, keep raw", "D05 §5; D05 §7.3"),
    (FLAG_DATE_SOURCE_CONFLICT, "informational, keep both", "D05 §5; D05 §7.2"),
    (FLAG_BIZDT_NE_TRADDT, "informational", "D05 §5; D05 §3.1"),
    (FLAG_ORPHAN_NO_BASE_ROW, "informational", "D05 §5; D05 §3.5.4"),
    (FLAG_OVERLAY_QTY_GT_BASE, "informational (additivity evidence)", "D05 §5; D05 §3.5.1"),
)
FLAG_SEVERITY = {name: severity for name, severity, _ref in VALIDITY_FLAGS}
FLAG_REFERENCE = {name: ref for name, _severity, ref in VALIDITY_FLAGS}

GATING_FLAG_NAMES = ()  # D05 §5 hard rule: no flag gates anything. Deliberately empty.

# ------------------------------------------------------------------ quarantine reasons
# Structural parse failures only (D05 §5: "Quarantine handling applies only to
# structural parse failures ... quarantined raw lines remain in L1 evidence").
# These are NOT semantic categories and carry no interpretation of market meaning.
QUARANTINE_REASONS = (
    (
        "row_fieldcount_mismatch",
        "parsed physical width differs from the member family's width variant after the D05 §7.1 tolerance",
        (FLAG_ROW_FIELDCOUNT_MISMATCH,),
    ),
    (
        "empty_interior_line",
        "blank line inside the data region; D05 §7.5 one-row-per-logical-record assumption not satisfiable",
        (),
    ),
    (
        "csv_syntax_error",
        "line is not RFC-4180 parseable (D05 §7.4); raw line retained",
        (),
    ),
    (
        "legacy_timestamp_blank",
        "legacy TIMESTAMP is blank; canonical business_date cannot be established (no defaulting)",
        (),
    ),
    (
        "legacy_timestamp_unparseable",
        "legacy TIMESTAMP matches neither DD-Mon-YY nor DD-Mon-YYYY (D05 §7.2); no other timestamp form is authorized",
        (),
    ),
    (
        "legacy_two_digit_year_unresolvable",
        "DD-Mon-YY row whose (day, month) does not match the governed source date, or no source date supplied; "
        "the century is NOT invented (D05 §7.2: expansion is display-normalization only)",
        (),
    ),
    (
        "udiff_traddt_unparseable",
        "UDiFF TradDt is not an ISO YYYY-MM-DD date; canonical business_date cannot be established",
        (),
    ),
    (
        "numeric_field_unparseable",
        "a typed canonical numeric field is non-blank but unparseable in its governed type; no coercion is permitted "
        "(D05 §3.1, §10.1)",
        (),
    ),
)
QUARANTINE_REASON_CODES = tuple(entry[0] for entry in QUARANTINE_REASONS)
QUARANTINE_REASON_FLAGS = {code: flags for code, _desc, flags in QUARANTINE_REASONS}
QUARANTINE_REASON_DESCRIPTION = {code: desc for code, desc, _flags in QUARANTINE_REASONS}

# ------------------------------------------------------------------ governance dependencies
# D07 §9 "Nine unresolved canonical semantics — carried forward OPEN" (identical to
# D06 §8). Identifiers are used to annotate canonical records (D07 §13-G).
GOVERNANCE_DEPENDENCIES = (
    ("D07-OPEN-1", "T0 volume-inclusion semantics"),
    ("D07-OPEN-2", "IT series definition/semantics"),
    ("D07-OPEN-3", "SF code"),
    ("D07-OPEN-4", "BE rights-entitlement vs T2T row-level split"),
    ("D07-OPEN-5", "SGB-STK documentation contradiction"),
    ("D07-OPEN-6", "XCONT 83/122 boundary residuals"),
    ("D07-OPEN-7", "FinInstrmId namespace semantics"),
    ("D07-OPEN-8", "three unexplained calendar dates (2024-11-20, 2025-10-20, 2026-01-15)"),
    ("D07-OPEN-9", "SME surveillance-stage detail for the corpus era"),
    ("DEC-1", "DEC-1 master acquisition (eligibility predicate, ETF register, master snapshots) — DEFERRED"),
)
GOVERNANCE_DEPENDENCY_LABEL = {dep_id: label for dep_id, label in GOVERNANCE_DEPENDENCIES}

#: Row-level annotation rules. Each rule attaches an unresolved-semantics identifier to
#: the canonical record; it changes no value and gates nothing.
#: ``kind``: ``series_literal`` (exact verbatim series token) or ``family`` (whole family).
ROW_GOVERNANCE_DEPENDENCY_RULES = (
    (
        "series_literal",
        "T0",
        "D07-OPEN-1",
        "row series token is the literal T0; volume-inclusion semantics unresolved (D05 §3.5.3)",
    ),
    (
        "series_literal",
        "IT",
        "D07-OPEN-2",
        "row series token is the literal IT; no authoritative series definition obtained (D05 §12 F11)",
    ),
    (
        "series_literal",
        "SF",
        "D07-OPEN-3",
        "row series token is the literal SF; SF code unclassified (D05 §12 F12)",
    ),
    (
        "series_literal",
        "BE",
        "D07-OPEN-4",
        "row series token is the literal BE; rights-entitlement vs T2T row split unresolved (D05 §12 F13)",
    ),
    (
        "family",
        FAMILY_UDIFF,
        "D07-OPEN-7",
        "listing_symbol is sourced from the opaque FinInstrmId column (D05 §6.2, §12 F2); "
        "namespace semantics unresolved — not used as identity, never joined",
    ),
)

#: Unresolved-semantics identifiers that W1 deliberately does NOT attach, with the reason.
GOVERNANCE_IDS_NOT_ATTACHED_BY_W1 = {
    "D07-OPEN-5": (
        "SGB-STK contradiction concerns a security-class reading; mapping it to a series token would "
        "require an SGB<->series inference not established by the governed contract [NON-ASSUMPTION]"
    ),
    "D07-OPEN-6": (
        "XCONT 83/122 residuals are a cross-era boundary property; W1 parses single members and performs "
        "no cross-era continuity work"
    ),
    "D07-OPEN-8": (
        "the three CAL dates are calendar-scope; calendar derivation is not part of W1 "
        "(D07 §14 W1 scope = parse/row-build/flags/provenance)"
    ),
    "D07-OPEN-9": (
        "SME surveillance-stage detail would require classifying ST/SM/SO rows as SME stages; that "
        "classification is not established by the governed contract, so W1 does not attach it"
    ),
}

# ------------------------------------------------------------------ overlay observations
# D05 §3.5.2: the set is a *data observation*, not an eligibility/microstructure contract.
OVERLAY_SERIES_OBSERVED = ("BL", "BO", "T0", "IT", "IL")
OVERLAY_SERIES_CAVEAT = (
    "D05 §3.5.2: observed series-set membership is a data observation only and is NOT an eligibility or "
    "microstructure inclusion contract [NON-ASSUMPTION]; D05 §3.5.5: no merge/drop/dedupe/volume-aggregation "
    "rule may be applied to overlay rows"
)
MATCH_TYPE_BASE_SAME_ISIN = "BASE_SAME_ISIN"
MATCH_TYPE_NO_BASE_ORPHAN = "NO_BASE_ORPHAN"
MATCH_TYPES = (MATCH_TYPE_BASE_SAME_ISIN, MATCH_TYPE_NO_BASE_ORPHAN)
QTY_RELATIONS = ("lt", "eq", "gt")
#: D05 §3.5.1 does not define a same-ISIN base-selection rule when several base rows carry
#: the ISIN; the published evidence structure used the first non-overlay row for that ISIN
#: in member order. W1 uses exactly that rule and records candidate cardinality so the
#: ambiguity is visible instead of hidden.
BASE_SELECTION_RULE = "first_non_overlay_row_for_isin_in_member_order"
MATCH_BASIS_SERIES_VERBATIM = "series_token_verbatim"
MATCH_BASIS_ISIN_NORMALIZED = "isin_normalized_upper_trim"

# ------------------------------------------------------------------ units provenance note
# D05 §10.2: "every consumer display MUST carry the provenance note".
UNITS_PROVENANCE_NOTE = (
    "Value fields are rupee totals and quantity fields are shares; scale is supported by sample test + "
    "official field definitions, not by in-file metadata (D05 §10.2). Numeric fields are stored as "
    "published: no rescale, no rounding, no reformat."
)

# ------------------------------------------------------------------ known evidence divergences
# Reality-reporting records (D05 §14 / D07 §7: "Report reality exactly where task text and
# evidence diverge"). These change no frozen D01/D03 metric and amend no governed document;
# they record where a W1 implementation cannot reproduce a published figure.
KNOWN_EVIDENCE_DIVERGENCES = (
    {
        "id": "W1-DIV-1",
        "subject": "isin_invalid_checkdigit census figure",
        "governed_text": (
            "D05 §5 defines the flag as 'ISIN fails mod-10 check digit' and cites 'Legacy era: 215,393 rows "
            "~5.4%; corpus-proven'."
        ),
        "finding": (
            "The published census figure was produced by the D03 evidence tool's check-digit routine, which "
            "evaluates the mod-10 sum over ISIN characters 2..11 (v[1:11]) instead of the ISO 6166 body "
            "(characters 1..11, v[0:11]) -- it drops the leading country-code character, which shifts the "
            "Luhn doubling parity. The routine round-trips against its own make_isin() helper, so the D03 "
            "selftest could not detect it."
        ),
        "measurement": (
            "On the 3,554 published FIX-UD-ROW-SAMPLE-01 rows (1,588 legacy + 1,966 udiff), the ISO 6166 "
            "check finds 0 invalid check digits; the D03-era formula finds 713 (284 legacy + 429 udiff). "
            "A known-valid external ISIN (US0378331005) is classified INVALID by the D03-era formula and "
            "VALID by the ISO 6166 check."
        ),
        "w1_behaviour": (
            "W1 implements the flag per its governed definition (ISO 6166 mod-10 check digit) and does NOT "
            "reproduce the D03-era formula. The D05 §5 parenthetical count is therefore not reproducible by "
            "W1 and should be treated as superseded by a future governance note; no frozen D01/D03 artifact "
            "and no governed document is modified by W1."
        ),
        "recommendation": (
            "At a later governance gate, record an evidence-divergence note against D05 §5 (and optionally "
            "correct the D03 census tool) so the flag's evidence qualifier matches the governed definition. "
            "Gate: not part of W1; no re-scan of the corpus is performed."
        ),
    },
)

# ------------------------------------------------------------------ engine configuration default
#: D05 §9.4: fields explicitly declared run-metadata are excluded from rerun determinism.
RUN_METADATA_FIELDS = ("provenance.run_id",)
RUN_METADATA_PLACEHOLDER = "<run-metadata:excluded>"
