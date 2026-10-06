"""Canonical ``SecurityRow`` construction (D05 §3.1, §5).

Rules implemented here, all verbatim from the governed contract:

* field mapping is by *name* through :data:`nse_engine.contract.CANONICAL_FIELD_MAP`;
* values are stored as published — never rescaled, rounded, reformatted or defaulted
  (D05 §3.1, §10.1); blank stays blank; ``None`` means *absent in that family*, which is
  not the same as blank;
* ``business_date`` is the legacy ``TIMESTAMP`` date part (D05 §7.2 tolerance) or UDiFF
  ``TradDt``; ``raw_biz_dt`` retains the original text untouched;
* ISIN is stored verbatim plus a normalization (uppercase, strip) used only for matching
  (D05 §3.1, §6.1); ISIN validity is informational and never gates (D05 §5);
* every validity flag is non-gating; no flag, and no ISIN validity value, filters,
  rejects, re-ranks or drops a row;
* records carry the unresolved-semantics identifier(s) that apply to them (D07 §13-G).

Rows that cannot be built truthfully are NOT emitted: they are quarantined with the raw
line retained and a structural reason code (fail-closed).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Optional, Tuple

from . import contract
from .parsing import MemberParse, QuarantineRecord, RawRecord, iso_date_valid, parse_legacy_timestamp
from .provenance import Provenance

_STRICT_DECIMAL_RE = re.compile(r"^-?\d+(\.\d+)?$")
_STRICT_INTEGER_RE = re.compile(r"^-?\d+$")

#: D03 census vocabulary for ISIN data quality, reused for comparability of observations.
#: Informational only. Only two of these categories have a governed flag (D05 §5).
ISIN_VALIDITY_BLANK = "BLANK"
ISIN_VALIDITY_VALID = "VALID"
ISIN_VALIDITY_INVALID_LEN = "INVALID_LEN"
ISIN_VALIDITY_INVALID_PREFIX = "INVALID_PREFIX"
ISIN_VALIDITY_INVALID_CHARSET = "INVALID_CHARSET"
ISIN_VALIDITY_INVALID_CHECKDIGIT = "INVALID_CHECKDIGIT"


# ------------------------------------------------------------------ numeric helpers (strict)
def strict_decimal(text: Optional[str]) -> Optional[Decimal]:
    """Parse published text as a decimal literal; ``None`` when blank or not literal.

    No coercion, no rounding, no float round-trip: the returned Decimal is exact for the
    published text.
    """
    if text is None or text == "":
        return None
    if not _STRICT_DECIMAL_RE.match(text):
        return None
    return Decimal(text)


def strict_integer(text: Optional[str]) -> Optional[int]:
    """Parse published text as an integer literal; ``None`` when blank or not literal."""
    if text is None or text == "":
        return None
    if not _STRICT_INTEGER_RE.match(text):
        return None
    return int(text)


# ------------------------------------------------------------------ ISIN (D05 §5, §6.1)
def normalize_isin(value: str) -> str:
    """D05 §3.1/§6.1 normalization for matching: uppercase + strip whitespace only."""
    return value.strip().upper()


def iso6166_check_digit(body11: str) -> Optional[int]:
    """ISO 6166 mod-10 (Luhn) check digit over the 11-character ISIN body.

    NOTE — evidence divergence W1-DIV-1 (see ``contract.KNOWN_EVIDENCE_DIVERGENCES``): the
    D03 census tool evaluated the same Luhn sum over ``body[1:]`` (dropping the leading
    country-code character, shifting the doubling parity), which is not the ISO 6166 check.
    W1 implements the governed definition ("fails mod-10 check digit") and does not
    reproduce the D03-era formula.
    """
    digits = []
    for char in body11.upper():
        if char.isdigit():
            digits.append(char)
        elif "A" <= char <= "Z":
            digits.append(str(ord(char) - 55))
        else:
            return None
    total = 0
    double = True
    for char in reversed("".join(digits)):
        value = int(char)
        if double:
            value *= 2
            if value > 9:
                value -= 9
        total += value
        double = not double
    return (10 - total % 10) % 10


def isin_validity(value: str) -> str:
    """ISIN data-quality category (informational; never gating)."""
    candidate = normalize_isin(value)
    if candidate == "":
        return ISIN_VALIDITY_BLANK
    if len(candidate) != 12:
        return ISIN_VALIDITY_INVALID_LEN
    if not candidate.startswith("IN"):
        return ISIN_VALIDITY_INVALID_PREFIX
    if not re.fullmatch(r"IN[A-Z0-9]{9}[0-9]", candidate):
        return ISIN_VALIDITY_INVALID_CHARSET
    check = iso6166_check_digit(candidate[:11])
    if check is None:
        return ISIN_VALIDITY_INVALID_CHARSET
    return ISIN_VALIDITY_VALID if check == int(candidate[11]) else ISIN_VALIDITY_INVALID_CHECKDIGIT


# ------------------------------------------------------------------ record types
@dataclass(frozen=True)
class Flag:
    name: str
    severity: str
    detail: str
    reference: str

    def to_dict(self) -> dict:
        return {
            "detail": self.detail,
            "name": self.name,
            "reference": self.reference,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class SecurityRow:
    """One canonical row per physical bhavcopy data row (D05 §3.1)."""

    format_family: str
    business_date: str
    business_date_basis: str
    values: Tuple[Tuple[str, Optional[str]], ...]
    isin_normalized: str
    isin_validity: str
    governance_dependencies: Tuple[str, ...]
    flags: Tuple[Flag, ...]
    observations: Tuple[Tuple[str, str], ...]
    provenance: Provenance
    line_number: int
    physical_width: int
    raw_line: str
    units_provenance_note: str = contract.UNITS_PROVENANCE_NOTE
    overlay: Optional[dict] = None

    # -- accessors -------------------------------------------------------
    def value(self, canonical_key: str) -> Optional[str]:
        for key, published in self.values:
            if key == canonical_key:
                return published
        raise KeyError(canonical_key)

    def decimal(self, canonical_key: str) -> Optional[Decimal]:
        if canonical_key not in contract.DECIMAL_FIELDS:
            raise KeyError("%s is not a governed decimal field" % canonical_key)
        return strict_decimal(self.value(canonical_key))

    def integer(self, canonical_key: str) -> Optional[int]:
        if canonical_key not in contract.INTEGER_FIELDS:
            raise KeyError("%s is not a governed integer field" % canonical_key)
        return strict_integer(self.value(canonical_key))

    @property
    def security_isin(self) -> str:
        return self.value("security_isin") or ""

    @property
    def listing_symbol(self) -> str:
        return self.value("listing_symbol") or ""

    @property
    def series(self) -> str:
        return self.value("series") or ""

    @property
    def security_name(self) -> Optional[str]:
        return self.value("security_name")

    @property
    def raw_biz_dt(self) -> str:
        return self.value("raw_biz_dt") or ""

    @property
    def traded_quantity(self) -> Optional[int]:
        return self.integer("traded_quantity")

    @property
    def traded_value(self) -> Optional[Decimal]:
        return self.decimal("traded_value")

    @property
    def trades_count(self) -> Optional[int]:
        return self.integer("trades_count")

    def flag_names(self) -> Tuple[str, ...]:
        return tuple(flag.name for flag in self.flags)

    def with_flags(self, extra: Tuple[Flag, ...]) -> "SecurityRow":
        merged = {flag.name: flag for flag in self.flags}
        for flag in extra:
            merged[flag.name] = flag
        return replace(self, flags=tuple(merged[name] for name in sorted(merged)))

    def with_overlay(self, overlay: Optional[dict]) -> "SecurityRow":
        return replace(self, overlay=overlay)

    def to_dict(self) -> dict:
        listing_source_column = _source_columns(self.format_family)["listing_symbol"]
        return {
            "business_date": self.business_date,
            "business_date_basis": self.business_date_basis,
            "flags": [flag.to_dict() for flag in self.flags],
            "format_family": self.format_family,
            "governance_dependencies": list(self.governance_dependencies),
            "isin_normalized": self.isin_normalized,
            "isin_validity": self.isin_validity,
            "listing_symbol_source_column": listing_source_column,
            "observations": {key: value for key, value in self.observations},
            "overlay": self.overlay,
            "physical_width": self.physical_width,
            "provenance": self.provenance.to_dict(),
            "raw_biz_dt": self.raw_biz_dt,
            "raw_line": self.raw_line,
            "source_line_number": self.line_number,
            "source_values": {key: published for key, published in self.values},
            "source_values_basis": (
                "published text per canonical field, mapped by column NAME through "
                "contract.CANONICAL_FIELD_MAP; derived fields (business_date) are excluded"
            ),
            "units_provenance_note": self.units_provenance_note,
        }


@dataclass(frozen=True)
class RowBuildResult:
    rows: Tuple[SecurityRow, ...]
    quarantined: Tuple[QuarantineRecord, ...]


def _source_columns(family: str) -> dict:
    """canonical key -> source column name for the family (``None`` = absent in family)."""
    position = contract.FORMAT_FAMILIES.index(family) + 1
    return {entry[0]: entry[position] for entry in contract.CANONICAL_FIELD_MAP}


def _row_governance_dependencies(family: str, series_value: str) -> Tuple[str, ...]:
    attached = []
    for kind, token, dependency_id, _reason in contract.ROW_GOVERNANCE_DEPENDENCY_RULES:
        if kind == "series_literal" and series_value == token:
            attached.append(dependency_id)
        elif kind == "family" and family == token:
            attached.append(dependency_id)
    return tuple(sorted(set(attached)))


def _quarantine_for_row(record: RawRecord, reason: str, detail: str) -> QuarantineRecord:
    return QuarantineRecord(
        line_number=record.line_number,
        physical_width=record.physical_width,
        raw_line=record.raw_line,
        reason_code=reason,
        reason_detail=detail,
        flag_names=contract.QUARANTINE_REASON_FLAGS.get(reason, ()),
    )


def build_security_row(
    record: RawRecord,
    parse: MemberParse,
    provenance: Provenance,
) -> Tuple[Optional[SecurityRow], Optional[QuarantineRecord]]:
    """Build one canonical row. Returns ``(row, None)`` or ``(None, quarantine_record)``."""
    family = parse.header.family
    columns = _source_columns(family)
    raw = record.as_dict()

    # ---- business date (fail-closed: no defaulting, no invented century) ----
    if family == contract.FAMILY_LEGACY:
        timestamp = parse_legacy_timestamp(
            raw["TIMESTAMP"], parse.source.expected_source_date
        )
        if not timestamp.ok:
            return None, _quarantine_for_row(record, timestamp.failure_code, timestamp.failure_detail)
        business_date = timestamp.iso_date
        business_date_basis = timestamp.basis
    else:
        trad_dt = raw["TradDt"]
        if not iso_date_valid(trad_dt):
            return None, _quarantine_for_row(
                record,
                "udiff_traddt_unparseable",
                "TradDt=%r is not an ISO YYYY-MM-DD date; canonical business_date cannot be established "
                "(no defaulting)" % trad_dt,
            )
        business_date = trad_dt
        business_date_basis = contract.DATE_BASIS_UDIFF_TRADDT

    # ---- canonical values, as published ----
    values = []
    for canonical_key, source_column in columns.items():
        if canonical_key in contract.DERIVED_FIELDS:
            # business_date is derived above (never a verbatim source column value)
            continue
        if source_column is None:
            values.append((canonical_key, None))
            continue
        published = raw[source_column]
        if canonical_key in contract.DECIMAL_FIELDS:
            if published != "" and strict_decimal(published) is None:
                return None, _quarantine_for_row(
                    record,
                    "numeric_field_unparseable",
                    "field %s (source column %s) value %r is not a decimal literal; coercion is not "
                    "permitted (D05 §3.1, §10.1)" % (canonical_key, source_column, published),
                )
        elif canonical_key in contract.INTEGER_FIELDS:
            if published != "" and strict_integer(published) is None:
                return None, _quarantine_for_row(
                    record,
                    "numeric_field_unparseable",
                    "field %s (source column %s) value %r is not an integer literal; coercion is not "
                    "permitted (D05 §3.1, §10.1)" % (canonical_key, source_column, published),
                )
        values.append((canonical_key, published))

    value_map = dict(values)
    flags = []
    observations = []

    # ---- ISIN validity: informational, never gating (D05 §5) ----
    isin_raw = value_map["security_isin"] or ""
    isin_state = isin_validity(isin_raw)
    if isin_state == ISIN_VALIDITY_INVALID_LEN:
        flags.append(
            Flag(
                name=contract.FLAG_ISIN_INVALID_LENGTH,
                severity=contract.FLAG_SEVERITY[contract.FLAG_ISIN_INVALID_LENGTH],
                detail="ISIN %r length %d != 12 after trim (informational; row retained)"
                % (isin_raw, len(normalize_isin(isin_raw))),
                reference=contract.FLAG_REFERENCE[contract.FLAG_ISIN_INVALID_LENGTH],
            )
        )
    elif isin_state == ISIN_VALIDITY_INVALID_CHECKDIGIT:
        flags.append(
            Flag(
                name=contract.FLAG_ISIN_INVALID_CHECKDIGIT,
                severity=contract.FLAG_SEVERITY[contract.FLAG_ISIN_INVALID_CHECKDIGIT],
                detail="ISIN %r fails the ISO 6166 mod-10 check digit (informational; row retained; "
                "validity never implies non-security — D05 §5)" % isin_raw,
                reference=contract.FLAG_REFERENCE[contract.FLAG_ISIN_INVALID_CHECKDIGIT],
            )
        )

    # ---- date vs governed source date (informational; keep both) ----
    expected = parse.source.expected_source_date
    if expected is not None:
        observations.append(("date_source_conflict_evaluated", "true"))
        if expected != business_date:
            flags.append(
                Flag(
                    name=contract.FLAG_DATE_SOURCE_CONFLICT,
                    severity=contract.FLAG_SEVERITY[contract.FLAG_DATE_SOURCE_CONFLICT],
                    detail="row-derived date %s != governed source date %s; both retained, nothing "
                    "repaired (D05 §5, §7.2)" % (business_date, expected),
                    reference=contract.FLAG_REFERENCE[contract.FLAG_DATE_SOURCE_CONFLICT],
                )
            )
    else:
        observations.append(("date_source_conflict_evaluated", "false"))
        observations.append(
            (
                "date_source_conflict_not_evaluated_reason",
                "no governed source date supplied by the caller; not guessed",
            )
        )

    # ---- UDiFF TradDt/BizDt comparison (informational) ----
    if family == contract.FAMILY_UDIFF:
        biz_dt = value_map["raw_biz_dt"] or ""
        if biz_dt == "":
            observations.append(("bizdt_traddt_comparison", "undetermined_blank_bizdt"))
        else:
            observations.append(("bizdt_traddt_comparison", "verbatim_text_equality"))
            if biz_dt != business_date:
                flags.append(
                    Flag(
                        name=contract.FLAG_BIZDT_NE_TRADDT,
                        severity=contract.FLAG_SEVERITY[contract.FLAG_BIZDT_NE_TRADDT],
                        detail="BizDt=%r != TradDt=%r; canonical business_date remains TradDt and both "
                        "are retained (D05 §3.1)" % (biz_dt, business_date),
                        reference=contract.FLAG_REFERENCE[contract.FLAG_BIZDT_NE_TRADDT],
                    )
                )

    series_value = value_map["series"] or ""
    return (
        SecurityRow(
            format_family=family,
            business_date=business_date,
            business_date_basis=business_date_basis,
            values=tuple(values),
            isin_normalized=normalize_isin(isin_raw),
            isin_validity=isin_state,
            governance_dependencies=_row_governance_dependencies(family, series_value),
            flags=tuple(sorted(flags, key=lambda flag: flag.name)),
            observations=tuple(sorted(observations)),
            provenance=provenance,
            line_number=record.line_number,
            physical_width=record.physical_width,
            raw_line=record.raw_line,
        ),
        None,
    )


def provenance_for(parse: MemberParse) -> Provenance:
    """One provenance block per source member (identical for all its rows)."""
    return Provenance(
        source_archive=parse.source.source_archive,
        member_name=parse.source.member_name,
        format_family=parse.header.family,
        member_sha256_raw_bytes=parse.report.member_sha256_raw_bytes,
        member_sha256_lf_text=parse.report.member_sha256_lf_text,
        archive_sha256=parse.source.archive_sha256,
        archive_sha256_basis=parse.source.archive_sha256_basis,
        run_id=parse.source.run_id,
        evidence_refs=parse.source.evidence_refs,
    )


def build_rows(parse: MemberParse) -> RowBuildResult:
    """Build all canonical rows for a parsed member (fail-closed per row)."""
    provenance = provenance_for(parse)
    rows = []
    quarantined = []
    for record in parse.records:
        row, quarantine = build_security_row(record, parse, provenance)
        if row is not None:
            rows.append(row)
        if quarantine is not None:
            quarantined.append(quarantine)
    return RowBuildResult(rows=tuple(rows), quarantined=tuple(quarantined))
