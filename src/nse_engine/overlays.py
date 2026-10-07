"""Overlay observation linking (D05 §3.5.1, §3.5.4, §5).

Observations only. This module computes, for rows whose *verbatim* series token is in the
governed observed set, the published-evidence structure

    (overlay_series, business_date, isin, qty_rel) + match_type in {BASE_SAME_ISIN, NO_BASE_ORPHAN}

against the same-day base row carrying the same ISIN (D05 §6.1 matching = ISIN uppercase
+ trim). It applies **no** merge, drop, dedupe or volume-aggregation rule, and it makes no
series-semantics claim: D05 §3.5.2 records the observed set as a data observation that is
*not* an eligibility or microstructure inclusion contract [NON-ASSUMPTION].

Determinism: base selection is the first non-overlay row for that ISIN in member order
(the published evidence structure's selection); when several base rows carry the ISIN the
candidate count is recorded, so the ambiguity is visible rather than hidden. Series tokens
are compared verbatim — no case folding is authorized for series.

Documented non-behaviour: symbol-only base matching is NOT implemented. The published
overlay fixture recorded zero ``BASE_BY_SYMBOL_ONLY`` cases, symbol is not durable identity
(D05 §12 F5) and the governed match-type enum does not contain it.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Tuple

from . import contract
from .rows import Flag, SecurityRow

QTY_REL_UNDETERMINED_OVERLAY = "overlay_quantity_blank_or_unparseable"
QTY_REL_UNDETERMINED_BASE = "base_quantity_blank_or_unparseable"


@dataclass(frozen=True)
class OverlayObservation:
    overlay_series: str
    business_date: str
    isin: str
    match_type: str
    qty_rel: Optional[str]
    base_line_number: Optional[int]
    base_candidate_count: int
    base_selection_rule: str = contract.BASE_SELECTION_RULE
    qty_rel_undetermined_reason: Optional[str] = None
    series_match_basis: str = contract.MATCH_BASIS_SERIES_VERBATIM
    isin_match_basis: str = contract.MATCH_BASIS_ISIN_NORMALIZED
    caveat: str = contract.OVERLAY_SERIES_CAVEAT

    def to_dict(self) -> dict:
        return {
            "base_candidate_count": self.base_candidate_count,
            "base_line_number": self.base_line_number,
            "base_selection_rule": self.base_selection_rule,
            "business_date": self.business_date,
            "caveat": self.caveat,
            "isin": self.isin,
            "isin_match_basis": self.isin_match_basis,
            "match_type": self.match_type,
            "overlay_series": self.overlay_series,
            "qty_rel": self.qty_rel,
            "qty_rel_undetermined_reason": self.qty_rel_undetermined_reason,
            "series_match_basis": self.series_match_basis,
        }


@dataclass(frozen=True)
class OverlayLinkResult:
    rows: Tuple[SecurityRow, ...]
    observations: Tuple[OverlayObservation, ...]


def _compare_quantity(overlay: Optional[int], base: Optional[int]) -> Tuple[Optional[str], Optional[str]]:
    if overlay is None:
        return None, QTY_REL_UNDETERMINED_OVERLAY
    if base is None:
        return None, QTY_REL_UNDETERMINED_BASE
    left, right = Decimal(overlay), Decimal(base)
    if left == right:
        return "eq", None
    if left < right:
        return "lt", None
    return "gt", None


def link_overlay_observations(rows: Tuple[SecurityRow, ...], overlay_series: Tuple[str, ...]) -> OverlayLinkResult:
    """Attach overlay observations and their non-gating flags. Retains every row."""
    overlay_tokens = tuple(overlay_series)
    base_rows_by_isin = {}
    for row in rows:
        if row.series in overlay_tokens:
            continue
        if row.isin_normalized != "":
            base_rows_by_isin.setdefault(row.isin_normalized, []).append(row)

    linked_rows = []
    observations = []
    for row in rows:
        if row.series not in overlay_tokens:
            linked_rows.append(row)
            continue

        candidates = base_rows_by_isin.get(row.isin_normalized, []) if row.isin_normalized else []
        if not candidates:
            reason = (
                "overlay row carries no non-blank ISIN; same-ISIN base matching is impossible "
                "(symbol-only matching is not authorized)"
                if row.isin_normalized == ""
                else "no non-overlay row with the same ISIN in this member"
            )
            observation = OverlayObservation(
                overlay_series=row.series,
                business_date=row.business_date,
                isin=row.isin_normalized,
                match_type=contract.MATCH_TYPE_NO_BASE_ORPHAN,
                qty_rel=None,
                base_line_number=None,
                base_candidate_count=0,
                qty_rel_undetermined_reason=reason,
            )
            row = row.with_flags(
                (
                    Flag(
                        name=contract.FLAG_ORPHAN_NO_BASE_ROW,
                        severity=contract.FLAG_SEVERITY[contract.FLAG_ORPHAN_NO_BASE_ROW],
                        detail="%s row has no same-day base row with the same ISIN (%s); row retained and "
                        "flagged, interpretation is [OPEN-SEMANTICS] (D05 §3.5.4)"
                        % (row.series, reason),
                        reference=contract.FLAG_REFERENCE[contract.FLAG_ORPHAN_NO_BASE_ROW],
                    ),
                )
            )
        else:
            base = candidates[0]
            qty_rel, undetermined = _compare_quantity(row.traded_quantity, base.traded_quantity)
            observation = OverlayObservation(
                overlay_series=row.series,
                business_date=row.business_date,
                isin=row.isin_normalized,
                match_type=contract.MATCH_TYPE_BASE_SAME_ISIN,
                qty_rel=qty_rel,
                base_line_number=base.line_number,
                base_candidate_count=len(candidates),
                qty_rel_undetermined_reason=undetermined,
            )
            if qty_rel == "gt":
                row = row.with_flags(
                    (
                        Flag(
                            name=contract.FLAG_OVERLAY_QTY_GT_BASE,
                            severity=contract.FLAG_SEVERITY[contract.FLAG_OVERLAY_QTY_GT_BASE],
                            detail="overlay traded quantity exceeds the same-day base-row quantity for the "
                            "same ISIN (additivity evidence; D05 §3.5.3) — no aggregation is applied",
                            reference=contract.FLAG_REFERENCE[contract.FLAG_OVERLAY_QTY_GT_BASE],
                        ),
                    )
                )
        linked_rows.append(row.with_overlay(observation.to_dict()))
        observations.append(observation)

    observations.sort(key=lambda item: (item.business_date, item.overlay_series, item.isin, item.base_line_number or 0))
    return OverlayLinkResult(rows=tuple(linked_rows), observations=tuple(observations))
