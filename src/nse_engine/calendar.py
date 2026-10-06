"""W2 / I2 — calendar derivation (D05 §3.4; D07 §13-A).

Derives ``CalendarDay`` facts from governed evidence only:

* **file presence** from the D01 inventory (one record per corpus member) — the trading-session
  signal (D05 §3.4);
* **labels** from the sourced circular evidence (``DEC2_CAL_LABELS.json`` /
  ``DEC12_CIRCULAR_REGISTRY.json``) — labels only, never a prediction of file presence.

The three dates whose absence is not explained by the obtained circulars (2024-11-20,
2025-10-20, 2026-01-15 — D07 §9 item 8) are carried as an explicit unresolved state
(``label_status = unexplained-by-obtained-circulars``). No cause is assigned, no holiday is
invented, and legacy-era gaps are ``not-retrieved`` (D05 §3.4 non-assumption).

Fail-closed rules:

* a label for a date that is not a missing weekday of the corpus span is a contradiction -> raise;
* a missing weekday after the labelling scope begins with no governed label -> raise (a silent
  ``null`` there would look like "not a holiday");
* a parsed-member fact for a date with no inventory file -> raise;
* a weekend file date -> raise (D03: zero weekend files; a weekend file would break the span
  arithmetic the calendar reports).

This module performs no IO: callers supply :mod:`nse_engine.evidence_inputs` records.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Iterable, Mapping, Optional, Sequence, Tuple

from . import contract
from .evidence_inputs import CalendarLabelRecord, CircularHolidayRecord, InventoryFileRecord

WEEKDAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")


class CalendarEvidenceError(ValueError):
    """Raised when supplied calendar evidence is internally contradictory (fail-closed)."""


@dataclass(frozen=True)
class MemberDateFact:
    """A parsed-member fact for one date (things only a parsed member can establish)."""

    business_date: str
    format_family: str
    trad_dt_eq_biz_dt: Optional[bool] = None


@dataclass(frozen=True)
class CalendarDay:
    """D05 §3.4 ``CalendarDay`` (structural; labels per the governed registry)."""

    trade_date: str
    file_present: bool
    weekday: str
    missing_weekday: bool
    official_holiday_label: Optional[str]
    label_status: str
    label_circular: Optional[str]
    label_registry_id: Optional[str]
    formats_present: Tuple[str, ...]
    member_names: Tuple[str, ...]
    trad_dt_eq_biz_dt: Optional[bool]
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "file_present": self.file_present,
            "formats_present": list(self.formats_present),
            "label_circular": self.label_circular,
            "label_registry_id": self.label_registry_id,
            "label_status": self.label_status,
            "member_names": list(self.member_names),
            "missing_weekday": self.missing_weekday,
            "notes": list(self.notes),
            "official_holiday_label": self.official_holiday_label,
            "trad_dt_eq_biz_dt": self.trad_dt_eq_biz_dt,
            "trade_date": self.trade_date,
            "weekday": self.weekday,
        }


@dataclass(frozen=True)
class CalendarResult:
    days: Tuple[CalendarDay, ...]
    first_date: str
    last_date: str
    span_weekdays: int
    files: int
    formats: Tuple[Tuple[str, int], ...]
    label_scope_start: Optional[str]
    provenance_inputs: Tuple[Tuple[str, str], ...] = ()

    @property
    def present_days(self) -> Tuple[CalendarDay, ...]:
        return tuple(day for day in self.days if day.file_present)

    @property
    def missing_days(self) -> Tuple[CalendarDay, ...]:
        return tuple(day for day in self.days if not day.file_present)

    def weekday_histogram(self) -> Mapping[str, int]:
        counts = {name: 0 for name in WEEKDAY_NAMES}
        for day in self.days:
            if day.file_present:
                counts[day.weekday] += 1
        return counts

    def label_status_counts(self) -> Mapping[str, int]:
        counts: dict = {}
        for day in self.days:
            counts[day.label_status] = counts.get(day.label_status, 0) + 1
        return {key: counts[key] for key in sorted(counts)}

    def unresolved_dates(self) -> Tuple[str, ...]:
        return tuple(
            day.trade_date
            for day in self.days
            if day.label_status == contract.CALENDAR_LABEL_UNEXPLAINED
        )

    def totals(self) -> dict:
        return {
            "days": len(self.days),
            "files": self.files,
            "first_date": self.first_date,
            "last_date": self.last_date,
            "missing_weekdays": len(self.missing_days),
            "present_days": len(self.present_days),
            "span_weekdays": self.span_weekdays,
            "unresolved_dates": list(self.unresolved_dates()),
        }


def _iso(value: str) -> _dt.date:
    try:
        return _dt.date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
    except (TypeError, ValueError, IndexError) as exc:  # pragma: no cover - defensive
        raise CalendarEvidenceError("not an ISO date: %r" % (value,)) from exc


def _weekdays_between(first: _dt.date, last: _dt.date) -> Tuple[_dt.date, ...]:
    days = []
    cursor = first
    step = _dt.timedelta(days=1)
    while cursor <= last:
        if cursor.weekday() < 5:  # Monday..Friday — D03: zero weekend file dates
            days.append(cursor)
        cursor += step
    return tuple(days)


def derive_calendar(
    inventory: Sequence[InventoryFileRecord],
    labels: Iterable[CalendarLabelRecord] = (),
    circular_holidays: Iterable[CircularHolidayRecord] = (),
    member_facts: Iterable[MemberDateFact] = (),
) -> CalendarResult:
    """Derive the governed calendar over the D01 file-date span.

    ``labels`` must cover every missing weekday after the labelling scope begins; the scope
    begins the day after the last legacy-era file date (the DEC2 labelling scope is the UDiFF-era
    years for which circulars were retrieved). Missing weekdays before that are ``not-retrieved``.
    """
    if not inventory:
        raise CalendarEvidenceError("calendar derivation requires at least one inventory file record")

    by_date: dict = {}
    for record in inventory:
        if record.date in by_date:
            by_date[record.date].append(record)
        else:
            by_date[record.date] = [record]

    dates = sorted(by_date)
    first, last = _iso(dates[0]), _iso(dates[-1])
    for date in dates:
        if _iso(date).weekday() > 4:
            raise CalendarEvidenceError(
                "weekend file date %s: the corpus has zero weekend files (D03), so this record "
                "contradicts the governed calendar arithmetic" % date
            )

    legacy_dates = [r.date for r in inventory if r.root == "LEGACY"]
    label_scope_start = (max(legacy_dates) if legacy_dates else None)
    scope_next = None
    if label_scope_start is not None:
        scope_next = (_iso(label_scope_start) + _dt.timedelta(days=1)).isoformat()

    label_map: dict = {}
    for label in labels:
        if label.missing_date in label_map:
            raise CalendarEvidenceError("duplicate calendar label for %s" % label.missing_date)
        label_map[label.missing_date] = label
    holiday_map = {record.holiday_date: record for record in circular_holidays}

    facts_map: dict = {}
    for fact in member_facts:
        if fact.business_date not in by_date:
            raise CalendarEvidenceError(
                "parsed-member fact for %s, which has no inventory file" % fact.business_date
            )
        if fact.business_date in facts_map:
            previous = facts_map[fact.business_date]
            if previous.trad_dt_eq_biz_dt != fact.trad_dt_eq_biz_dt:
                raise CalendarEvidenceError(
                    "conflicting member facts for %s" % fact.business_date
                )
        facts_map[fact.business_date] = fact

    days = []
    for cursor in _weekdays_between(first, last):
        date = cursor.isoformat()
        records = by_date.get(date, [])
        present = bool(records)
        weekday = WEEKDAY_NAMES[cursor.weekday()]
        notes = []
        label_value = None
        label_status = contract.CALENDAR_LABEL_NOT_APPLICABLE
        label_circular = None
        label_registry = None

        if present:
            if date in holiday_map:
                label_status = contract.CALENDAR_LABEL_OFFICIAL_HOLIDAY
                label_value = date
                label_circular = "circular holiday with file present"
                notes.append(contract.CALENDAR_DIVERGENCE_NOTE)
            if date in label_map:
                raise CalendarEvidenceError(
                    "governed label supplied for %s, which HAS a file: labels apply to missing "
                    "weekdays only (D05 §3.4)" % date
                )
        else:
            notes.append(contract.CALENDAR_MISSING_WEEKDAY_NOTE)
            label = label_map.get(date)
            if label is not None:
                if label.label == "OFFICIAL-HOLIDAY":
                    label_status = contract.CALENDAR_LABEL_OFFICIAL_HOLIDAY
                    label_value = label.circular or "official holiday (circular)"
                    label_circular = label.circular or None
                    label_registry = label.registry_id or None
                elif label.label == "UNEXPLAINED-BY-OBTAINED-CIRCULARS":
                    label_status = contract.CALENDAR_LABEL_UNEXPLAINED
                    label_value = None
                    notes.append(
                        "absence not explained by the obtained circulars; kept unresolved "
                        "(%s) and never assigned a cause" % contract.CALENDAR_UNRESOLVED_DEPENDENCY
                    )
                else:
                    raise CalendarEvidenceError(
                        "unknown governed calendar label %r for %s" % (label.label, date)
                    )
            elif scope_next is not None and date >= scope_next:
                raise CalendarEvidenceError(
                    "missing weekday %s is inside the labelled scope but has no governed label "
                    "(fail-closed: a silent null would masquerade as 'not a holiday')" % date
                )
            else:
                label_status = contract.CALENDAR_LABEL_NOT_RETRIEVED
                notes.append(
                    "legacy-era gap: cause NOT retrieved and MUST NOT be invented (D05 §3.4)"
                )

        fact = facts_map.get(date)
        trad_dt_eq_biz_dt = fact.trad_dt_eq_biz_dt if fact is not None else None
        if trad_dt_eq_biz_dt is not None:
            notes.append(contract.CALENDAR_TRADDT_BIZDT_NOTE)
        if present:
            notes.append(contract.CALENDAR_PRESENCE_RULE)

        days.append(
            CalendarDay(
                trade_date=date,
                file_present=present,
                weekday=weekday,
                missing_weekday=not present,
                official_holiday_label=label_value,
                label_status=label_status,
                label_circular=label_circular,
                label_registry_id=label_registry,
                formats_present=tuple(sorted({r.root for r in records})),
                member_names=tuple(sorted(r.file_name for r in records)),
                trad_dt_eq_biz_dt=trad_dt_eq_biz_dt,
                notes=tuple(notes),
            )
        )

    for date in sorted(label_map):
        if date in by_date:
            raise CalendarEvidenceError(
                "governed label %s is for a date that HAS a file (contradiction)" % date
            )
        if not (first <= _iso(date) <= last):
            raise CalendarEvidenceError(
                "governed label %s falls outside the corpus span %s..%s" % (date, dates[0], dates[-1])
            )
        if _iso(date).weekday() > 4:
            raise CalendarEvidenceError("governed label %s is not a weekday" % date)

    formats: dict = {}
    for record in inventory:
        formats[record.root] = formats.get(record.root, 0) + 1

    return CalendarResult(
        days=tuple(days),
        first_date=dates[0],
        last_date=dates[-1],
        span_weekdays=len(days),
        files=len(inventory),
        formats=tuple(sorted(formats.items())),
        label_scope_start=label_scope_start,
        # what the derivation consumed (document-level identity of the evidence files is the
        # caller's input contract; these counts make the consumed set explicit and auditable)
        provenance_inputs=(
            ("calendar_labels", str(len(label_map))),
            ("circular_holidays", str(len(holiday_map))),
            ("inventory_records", str(len(inventory))),
            ("member_facts", str(len(facts_map))),
        ),
    )


def arithmetic_closes(result: CalendarResult) -> bool:
    """D03 arithmetic: span weekdays = present files (one per date) + missing weekdays."""
    return result.span_weekdays == len(result.present_days) + len(result.missing_days) and (
        result.files == len(result.present_days) or _duplicate_date_count(result) > 0
    )


def _duplicate_date_count(result: CalendarResult) -> int:
    return sum(1 for day in result.days if len(day.member_names) > 1)
