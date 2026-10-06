"""Governed evidence input records for W2 (D07 §13-A: repository-held evidence only).

W2 derives calendar facts, dated associations, metric folds and overlay evidence accounting
from evidence that is *committed to the repository* — the D01 inventory and the published D03 /
D04 fixtures. This module holds the input records those derivations consume, so the engine
modules themselves stay pure (no file IO, no clock, no environment): callers read the
committed artifacts and construct these records.

Nothing here interprets a source: each field is a value copied out of a governed artifact, and
``source_ref`` keeps the link back to that artifact (D05 §8: a derived fact with no resolvable
provenance entry is invalid).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Tuple

from . import contract


@dataclass(frozen=True)
class InventoryFileRecord:
    """One D01 inventory member record (`evidence/inventory/file_inventory.json`).

    ``date`` is the D01 ``date_from_filename`` value — the governed file-date mapping (D05 §3.4:
    ``trade_date`` is "the ISO date from the filename set (D01)"). W2 never parses a file name.
    """

    file_name: str
    date: str
    root: str
    sha256: str
    row_count: int
    series_counts: Tuple[Tuple[str, int], ...] = ()

    def series_map(self) -> Mapping[str, int]:
        return {series: count for series, count in self.series_counts}


@dataclass(frozen=True)
class FileMetricRecord:
    """One per-file D01 metric record (`FIX-SEM-DEF-01__metrics.csv`).

    The frozen per-file metric evidence for all 2,462 corpus files. W2 folds these records; it
    does not re-read the corpus (D05 §14: no corpus re-scan to "improve" D01/D03 metrics).
    """

    format_family: str
    file_name: str
    rows: int
    blank_symbol_rows: int
    blank_isin_rows: int
    nonblank_isin_rows: int
    distinct_nonblank_isin: int
    isins_extra_duplicate_rows: int
    distinct_nonblank_symbol: int
    distinct_symbol_series_pairs: int
    symbol_series_duplicate_rows: int
    d01_isin_count: int
    d01_symbol_count: int
    discriminating_file: bool
    d01_isin_eq_distinct_nonblank: bool
    d01_isin_eq_nonblank_rows: bool
    d01_sym_eq_distinct_nonblank: bool
    d01_sym_eq_rows: bool
    requested_date: Optional[str] = None


@dataclass(frozen=True)
class CalendarLabelRecord:
    """One governed missing-weekday label (`evidence/d04/DEC2_CAL_LABELS.json`).

    ``label`` is the published vocabulary value (``OFFICIAL-HOLIDAY`` /
    ``UNEXPLAINED-BY-OBTAINED-CIRCULARS``); ``circular`` is the published circular name where
    one was obtained. The registry id (``NSE/...``) resolves through
    ``DEC12_CIRCULAR_REGISTRY.json`` when supplied.
    """

    missing_date: str
    label: str
    circular: str = ""
    registry_id: str = ""


@dataclass(frozen=True)
class CircularHolidayRecord:
    """A circular holiday that nonetheless carries a file (DEC2_CAL_LABELS
    ``files_present_on_circular_holiday``) — both-direction divergence (D05 §3.4)."""

    holiday_date: str
    note: str = ""


@dataclass(frozen=True)
class OverlayFixtureRow:
    """One published overlay comparison row (`FIX-OVERLAY-SEM-01__per_overlay_row.csv`)."""

    format_family: str
    date: str
    overlay_series: str
    overlay_symbol: str
    overlay_isin: str
    match_type: str
    base_symbol: str
    base_series: str
    base_isin: str
    qty_rel: str


@dataclass(frozen=True)
class ExtractCoverageRecord:
    """Published extract coverage for one date: extract rows vs the full-file D01 row count."""

    date: str
    member_name: str
    extract_rows: int
    full_file_rows: int

    @property
    def coverage_ratio(self) -> float:
        if self.full_file_rows <= 0:
            return 0.0
        return float(self.extract_rows) / float(self.full_file_rows)


#: Field order of the D01 metric record, used by the CSV adapter in tests/harness code.
FILE_METRIC_FIELDS = (
    "format",
    "file",
    "rows",
    "blank_symbol_rows",
    "blank_isin_rows",
    "nonblank_isin_rows",
    "distinct_nonblank_isin",
    "isins_extra_duplicate_rows",
    "distinct_nonblank_symbol",
    "distinct_symbol_series_pairs",
    "symbol_series_duplicate_rows",
    "is_d02_target",
    "requested_date",
    "selection",
    "d01_isin_count",
    "d01_symbol_count",
    "d01_isin_eq_distinct_nonblank",
    "d01_isin_eq_nonblank_rows",
    "d01_sym_eq_distinct_nonblank",
    "d01_sym_eq_rows",
    "discriminating_file",
)

#: The format family a D01 inventory root maps to (D01 root names are LEGACY / UDIFF).
INVENTORY_ROOT_TO_FAMILY = {
    "LEGACY": contract.FAMILY_LEGACY,
    "UDIFF": contract.FAMILY_UDIFF,
}
