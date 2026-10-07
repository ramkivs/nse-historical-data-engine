"""Reference member parser — name-keyed / header-aware, fail-closed (D05 §7, D07 §13-A).

Authorized tolerances, and only these:

* legacy header/row *trailing empty field* variant (D05 §7.1; D03 §15 FIX-ANOM-01, which
  closed as a serialization/format variation: 1,917 files carry a 14th empty physical
  field on every line, 2 files — 2017-07-10, 2020-07-13 — carry 13 physical fields);
* the two documented legacy timestamp forms ``DD-MON-YYYY`` and ``DD-Mon-YY`` (D05 §7.2);
  the month token is matched case-insensitively because both spellings are governed
  (D05/D07 write ``DD-Mon-YY|YYYY``; D02-F2 records the literal corpus value ``13-Jul-20``);
* RFC-4180 quoting, including embedded commas in quoted fields (D05 §7.4); non-conforming
  quoting is quarantined, never silently repaired;
* CRLF and LF line endings (D05 §9) — raw lines are retained LF-normalized;
* blank numeric fields remain blank (D05 §3.1, §7.4).

Everything else fails closed: mapping is by column name (never by position), a member whose
header matches neither family header raises, a row whose physical width does not match its
member's width variant is quarantined with the raw line retained, and no field is ever
defaulted, trimmed, coerced or repaired. No BOM tolerance exists (raising, not stripping).

Column names are compared *exactly* (no whitespace stripping): the governed headers are
verbatim literals (D05 §3) and D05 §7 authorizes no header-whitespace tolerance.
"""

from __future__ import annotations

import csv
import datetime as _dt
import re
from dataclasses import dataclass
from typing import Optional, Tuple

from . import contract
from .errors import (
    BomNotToleratedError,
    CarriageReturnNotFollowedByLineFeedError,
    EmptyMemberError,
    HeaderUnrecognizedError,
    MemberDecodeError,
)
from .provenance import dual_hash

_HAS_CR = re.compile(r"\r")

_MONTHS = {
    "JAN": 1,
    "FEB": 2,
    "MAR": 3,
    "APR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AUG": 8,
    "SEP": 9,
    "OCT": 10,
    "NOV": 11,
    "DEC": 12,
}

#: D05 §7.2 tolerated legacy timestamp forms (case-insensitive month token; 2- or 4-digit year).
LEGACY_TIMESTAMP_RE = re.compile(r"^(?P<day>\d{2})-(?P<mon>[A-Za-z]{3})-(?P<year>\d{2}|\d{4})$")

HEADER_TOLERANCE_TRAILING_EMPTY = "legacy13_trailing_empty_field"


# ------------------------------------------------------------------ source identity
@dataclass(frozen=True)
class SourceDescriptor:
    """Identity of the source member, supplied by the caller.

    W1 deliberately does not derive any of this from file names: archive/member naming is a
    D01 inventory fact, and inventing name-parsing semantics here would be an unauthorized
    interpretation. The caller passes the governed facts it holds.

    ``expected_source_date`` is the governed cross-check basis for the legacy timestamp
    tolerance (D05 §7.2 "cross-checked against the filename date") and for the
    ``date_source_conflict`` flag. When it is absent, those behaviours are *not* applied
    (never guessed).
    """

    source_archive: str
    member_name: str
    archive_sha256: Optional[str] = None
    archive_sha256_basis: str = "not-supplied"
    expected_source_date: Optional[str] = None
    evidence_refs: Tuple[str, ...] = ()
    run_id: Optional[str] = None


# ------------------------------------------------------------------ header
@dataclass(frozen=True)
class HeaderSpec:
    family: str
    logical_fields: Tuple[str, ...]
    physical_width: int
    row_physical_widths: Tuple[int, ...]
    tolerance_applied: Optional[str]
    tolerance_note: str

    @property
    def index(self) -> dict:
        return {name: position for position, name in enumerate(self.logical_fields)}


def detect_header(header_fields: Tuple[str, ...]) -> HeaderSpec:
    """Detect the governed family from a parsed header line (name-keyed, exact match)."""
    if header_fields == contract.LEGACY_HEADER_FIELDS:
        return HeaderSpec(
            family=contract.FAMILY_LEGACY,
            logical_fields=contract.LEGACY_HEADER_FIELDS,
            physical_width=contract.LEGACY_LOGICAL_WIDTH,
            row_physical_widths=(contract.LEGACY_LOGICAL_WIDTH,),
            tolerance_applied=None,
            tolerance_note="legacy 13-physical-field variant; no tolerance applied",
        )
    if header_fields == contract.LEGACY_HEADER_FIELDS + ("",):
        return HeaderSpec(
            family=contract.FAMILY_LEGACY,
            logical_fields=contract.LEGACY_HEADER_FIELDS,
            physical_width=contract.LEGACY_TOLERATED_PHYSICAL_WIDTH,
            row_physical_widths=(contract.LEGACY_TOLERATED_PHYSICAL_WIDTH,),
            tolerance_applied=HEADER_TOLERANCE_TRAILING_EMPTY,
            tolerance_note=(
                "D05 §7.1 trailing empty 14th field tolerated (same logical schema as 13 fields); "
                "rows must match this member's variant"
            ),
        )
    if header_fields == contract.UDIFF_HEADER_FIELDS:
        return HeaderSpec(
            family=contract.FAMILY_UDIFF,
            logical_fields=contract.UDIFF_HEADER_FIELDS,
            physical_width=contract.UDIFF_WIDTH,
            row_physical_widths=(contract.UDIFF_WIDTH,),
            tolerance_applied=None,
            tolerance_note="udiff strict 34-field header; width %d required" % contract.UDIFF_WIDTH,
        )
    raise HeaderUnrecognizedError(
        physical_width=len(header_fields),
        first_fields=tuple(header_fields[:4]),
        detail="no layout tolerance beyond the trailing-empty legacy field is authorized (D05 §7.3)",
    )


# ------------------------------------------------------------------ records
@dataclass(frozen=True)
class RawRecord:
    """One physical data line, parsed into name-keyed verbatim values.

    ``fields`` is the physical field tuple exactly as the CSV layer produced it;
    ``values`` is the logical (name -> verbatim value) mapping derived by column *name*.
    ``raw_line`` is the LF-normalized line text (D05 §9.3) with no trailing line ending.
    """

    line_number: int
    physical_width: int
    fields: Tuple[str, ...]
    values: Tuple[Tuple[str, str], ...]
    raw_line: str

    def get(self, name: str) -> str:
        for key, value in self.values:
            if key == name:
                return value
        raise KeyError(name)

    def as_dict(self) -> dict:
        return dict(self.values)


@dataclass(frozen=True)
class QuarantineRecord:
    """A structural parse failure: the raw line is retained, no canonical row is emitted."""

    line_number: int
    physical_width: Optional[int]
    raw_line: str
    reason_code: str
    reason_detail: str
    flag_names: Tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "flag_names": list(self.flag_names),
            "line_number": self.line_number,
            "physical_width": self.physical_width,
            "raw_line": self.raw_line,
            "reason_code": self.reason_code,
            "reason_detail": self.reason_detail,
            "reason_description": contract.QUARANTINE_REASON_DESCRIPTION.get(self.reason_code, ""),
        }


@dataclass(frozen=True)
class ParseReport:
    format_family: str
    header_physical_width: int
    header_tolerance_applied: Optional[str]
    header_tolerance_note: str
    data_lines: int
    records: int
    quarantined: int
    quarantine_by_reason: Tuple[Tuple[str, int], ...]
    crlf_line_endings: int
    lf_line_endings: int
    member_size_bytes: int
    member_sha256_raw_bytes: str
    member_sha256_lf_text: str
    decode: str
    bom_present: bool

    def to_dict(self) -> dict:
        return {
            "bom_present": self.bom_present,
            "crlf_line_endings": self.crlf_line_endings,
            "data_lines": self.data_lines,
            "decode": self.decode,
            "format_family": self.format_family,
            "header_physical_width": self.header_physical_width,
            "header_tolerance_applied": self.header_tolerance_applied,
            "header_tolerance_note": self.header_tolerance_note,
            "lf_line_endings": self.lf_line_endings,
            "member_sha256_lf_text": self.member_sha256_lf_text,
            "member_sha256_raw_bytes": self.member_sha256_raw_bytes,
            "member_size_bytes": self.member_size_bytes,
            "quarantine_by_reason": {code: count for code, count in self.quarantine_by_reason},
            "quarantined": self.quarantined,
            "records": self.records,
        }


@dataclass(frozen=True)
class MemberParse:
    source: SourceDescriptor
    header: HeaderSpec
    header_line: str
    records: Tuple[RawRecord, ...]
    quarantined: Tuple[QuarantineRecord, ...]
    report: ParseReport


# ------------------------------------------------------------------ legacy timestamps
@dataclass(frozen=True)
class TimestampParse:
    """Outcome of the D05 §7.2 legacy timestamp tolerance (never a guess)."""

    ok: bool
    iso_date: Optional[str]
    basis: Optional[str]
    failure_code: Optional[str]
    failure_detail: str


def iso_date_valid(value: str) -> bool:
    if len(value) != contract.ISO_DATE_LENGTH or not re.fullmatch(contract.ISO_DATE_PATTERN, value):
        return False
    try:
        _dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def parse_legacy_timestamp(raw_value: str, expected_source_date: Optional[str]) -> TimestampParse:
    """Parse a legacy ``TIMESTAMP`` cell under the governed tolerance.

    * ``DD-MON-YYYY`` -> canonical date is the row's own date.
    * ``DD-Mon-YY``   -> the century is NOT invented: the canonical date is taken from the
      governed source date, and only when the row's (day, month) agrees with it. This is
      the D05 §7.2 cross-check, never a silent repair. Any disagreement, or a missing
      source date, fails closed (the raw text is retained by the caller).
    """
    if raw_value == "":
        return TimestampParse(
            ok=False,
            iso_date=None,
            basis=None,
            failure_code="legacy_timestamp_blank",
            failure_detail="TIMESTAMP is empty",
        )
    match = LEGACY_TIMESTAMP_RE.match(raw_value)
    if match is None:
        return TimestampParse(
            ok=False,
            iso_date=None,
            basis=None,
            failure_code="legacy_timestamp_unparseable",
            failure_detail=(
                "value %r matches neither DD-Mon-YY nor DD-Mon-YYYY; no other timestamp form is "
                "authorized (D05 §7.2)" % raw_value
            ),
        )
    month = _MONTHS.get(match.group("mon").upper())
    if month is None:
        return TimestampParse(
            ok=False,
            iso_date=None,
            basis=None,
            failure_code="legacy_timestamp_unparseable",
            failure_detail="unrecognized month token %r" % match.group("mon"),
        )
    day = int(match.group("day"))
    year_token = match.group("year")
    if len(year_token) == 4:
        candidate = "%04d-%02d-%02d" % (int(year_token), month, day)
        if not iso_date_valid(candidate):
            return TimestampParse(
                ok=False,
                iso_date=None,
                basis=None,
                failure_code="legacy_timestamp_unparseable",
                failure_detail="date %r is not a valid calendar date" % raw_value,
            )
        return TimestampParse(
            ok=True,
            iso_date=candidate,
            basis=contract.DATE_BASIS_LEGACY_FOUR_DIGIT_YEAR,
            failure_code=None,
            failure_detail="",
        )
    # two-digit year: resolution requires the governed source date
    if expected_source_date is None or not iso_date_valid(expected_source_date):
        return TimestampParse(
            ok=False,
            iso_date=None,
            basis=None,
            failure_code="legacy_two_digit_year_unresolvable",
            failure_detail=(
                "two-digit-year value %r with no valid governed source date supplied; the century is not "
                "invented (D05 §7.2)" % raw_value
            ),
        )
    source_day = int(expected_source_date[8:10])
    source_month = int(expected_source_date[5:7])
    if (day, month) != (source_day, source_month):
        return TimestampParse(
            ok=False,
            iso_date=None,
            basis=None,
            failure_code="legacy_two_digit_year_unresolvable",
            failure_detail=(
                "two-digit-year value %r disagrees with governed source date %s on (day, month); the "
                "canonical date cannot be established without inventing a century rule (D05 §7.2)"
                % (raw_value, expected_source_date)
            ),
        )
    return TimestampParse(
        ok=True,
        iso_date=expected_source_date,
        basis=contract.DATE_BASIS_LEGACY_TWO_DIGIT_YEAR_CROSSCHECKED,
        failure_code=None,
        failure_detail="",
    )


# ------------------------------------------------------------------ member parsing
def _split_member_lines(text: str) -> Tuple[list, int, int, int]:
    """Return (LF-normalized lines, crlf_count, lf_only_count, trailing_terminator_dropped).

    The returned lines are LF-normalized (D05 §9.3): a CRLF member and its LF twin yield
    byte-identical ``raw_line`` text and byte-identical canonical rows.
    """
    crlf_count = text.count("\r\n")
    lf_total = text.count("\n")
    lf_only_count = lf_total - crlf_count
    lines = text.replace("\r\n", "\n").split("\n")
    trailing = 0
    if len(lines) > 1 and lines[-1] == "":
        # A single final empty element is the file's terminating newline (D05 §9.1).
        lines = lines[:-1]
        trailing = 1
    return lines, crlf_count, lf_only_count, trailing


def _csv_fields(line: str) -> Tuple[Tuple[str, ...], Optional[str]]:
    """RFC-4180 parse of a single physical line. Returns (fields, error_detail).

    ``strict=True`` is deliberate: the default csv reader silently *repairs* malformed
    quoting (``"a"b`` becomes ``ab``). Silent repair of raw text is not authorized, so a
    line whose quoting is not RFC-4180 conforming is quarantined with its raw text instead.
    """
    try:
        rows = list(csv.reader([line], strict=True))
    except csv.Error as exc:
        return (), str(exc)
    if len(rows) != 1:
        return (), "line did not parse to exactly one record"
    return tuple(rows[0]), None


def parse_member_bytes(data: bytes, source: SourceDescriptor) -> MemberParse:
    """Parse one member's bytes into name-keyed raw records, quarantining structurally
    unparseable lines. Raises on member-level failures (decode, BOM, CR-only, header).
    """
    raw_sha, lf_sha = dual_hash(data)
    if data.startswith(b"\xef\xbb\xbf"):
        raise BomNotToleratedError()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MemberDecodeError(
            "member is not valid UTF-8 at byte offset %d: %s (D05 §7.6: fail loudly, never drop "
            "characters)" % (exc.start, exc.reason)
        ) from exc

    stripped_of_crlf = text.replace("\r\n", "")
    bare_cr = _HAS_CR.search(stripped_of_crlf)
    if bare_cr is not None:
        offending_line = stripped_of_crlf[: bare_cr.start()].count("\n") + 1
        raise CarriageReturnNotFollowedByLineFeedError(offending_line)

    lines, crlf_count, lf_only_count, _trailing = _split_member_lines(text)
    if not lines:
        raise EmptyMemberError()
    header_line = lines[0]
    if header_line == "":
        raise EmptyMemberError()

    header_fields, error_detail = _csv_fields(header_line)
    if error_detail is not None:
        raise HeaderUnrecognizedError(
            physical_width=0,
            first_fields=(),
            detail="header line is not RFC-4180 parseable: %s" % error_detail,
        )
    header = detect_header(header_fields)
    index = header.index

    records = []
    quarantined = []
    for line_number, line in enumerate(lines[1:], start=2):
        if line == "":
            quarantined.append(
                QuarantineRecord(
                    line_number=line_number,
                    physical_width=None,
                    raw_line=line,
                    reason_code="empty_interior_line",
                    reason_detail="blank line inside the data region",
                    flag_names=(),
                )
            )
            continue
        fields, error_detail = _csv_fields(line)
        if error_detail is not None:
            quarantined.append(
                QuarantineRecord(
                    line_number=line_number,
                    physical_width=None,
                    raw_line=line,
                    reason_code="csv_syntax_error",
                    reason_detail=error_detail,
                    flag_names=(),
                )
            )
            continue
        width = len(fields)
        if width not in header.row_physical_widths:
            quarantined.append(
                QuarantineRecord(
                    line_number=line_number,
                    physical_width=width,
                    raw_line=line,
                    reason_code="row_fieldcount_mismatch",
                    reason_detail=(
                        "physical width %d does not match member variant %s (expected %s); fail-closed, "
                        "raw retained (D05 §5, §7.3)"
                        % (width, header.family, ",".join(str(w) for w in header.row_physical_widths))
                    ),
                    flag_names=contract.QUARANTINE_REASON_FLAGS["row_fieldcount_mismatch"],
                )
            )
            continue
        if width == contract.LEGACY_TOLERATED_PHYSICAL_WIDTH and fields[contract.LEGACY_LOGICAL_WIDTH] != "":
            quarantined.append(
                QuarantineRecord(
                    line_number=line_number,
                    physical_width=width,
                    raw_line=line,
                    reason_code="row_fieldcount_mismatch",
                    reason_detail=(
                        "14th physical field is not empty (%r); the trailing-empty-field tolerance is the "
                        "only authorized 14-field variant (D05 §7.1)" % fields[contract.LEGACY_LOGICAL_WIDTH]
                    ),
                    flag_names=contract.QUARANTINE_REASON_FLAGS["row_fieldcount_mismatch"],
                )
            )
            continue
        values = tuple((name, fields[index[name]]) for name in header.logical_fields)
        records.append(
            RawRecord(
                line_number=line_number,
                physical_width=width,
                fields=fields,
                values=values,
                raw_line=line,
            )
        )

    by_reason = {}
    for record in quarantined:
        by_reason[record.reason_code] = by_reason.get(record.reason_code, 0) + 1

    report = ParseReport(
        format_family=header.family,
        header_physical_width=header.physical_width,
        header_tolerance_applied=header.tolerance_applied,
        header_tolerance_note=header.tolerance_note,
        data_lines=len(lines) - 1,
        records=len(records),
        quarantined=len(quarantined),
        quarantine_by_reason=tuple(sorted(by_reason.items())),
        crlf_line_endings=crlf_count,
        lf_line_endings=lf_only_count,
        member_size_bytes=len(data),
        member_sha256_raw_bytes=raw_sha,
        member_sha256_lf_text=lf_sha,
        decode="utf-8",
        bom_present=False,
    )
    return MemberParse(
        source=source,
        header=header,
        header_line=header_line,
        records=tuple(records),
        quarantined=tuple(quarantined),
        report=report,
    )
