"""W2 / I2 — D01 metric re-computation (D05 §4; D07 §13-A).

Two deterministic levels, both anchored to governed evidence (see
``contract.D01_RECOMPUTATION_BOUNDARY``):

**A. Row-level metrics** — ``compute_row_metrics`` applies the D01 formulas
(``FIX-SEM-DEF-01__formula_definitions.json``, restated in D05 §4) to any supplied set of
canonical rows. Definitions are used exactly as governed: distinct counts mean distinct
NON-BLANK values after whitespace-strip + uppercase; blank is not a value; there are no
positional counts; nothing is coerced or defaulted.

**B. Corpus-level metric algebra** — ``fold_file_metrics`` folds the frozen per-file D01 metric
evidence (all 2,462 corpus files) into per-format and corpus totals, and re-derives the D01
definition verdict from the numeric columns (independently of the fixture's own boolean columns,
which are then cross-checked for consistency). This recomputes the published D01 algebra without
re-reading the corpus (D05 §14 forbids a corpus re-scan).

``series_universe`` and ``series_class_rollup`` recompute the D02 series facts from the D01
inventory's per-file ``series_counts``; the series *classification* is evidence input (D02), never
re-derived here.

No new metric definition is introduced, no D01 semantic is altered, and no metric is tuned to
improve agreement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple

from . import contract
from .compact import RowTokens, TokenIntern, Uint64Set, normalize_upper_trim
from .evidence_inputs import FileMetricRecord, InventoryFileRecord, INVENTORY_ROOT_TO_FAMILY
from .rows import SecurityRow


@dataclass(frozen=True)
class RowMetrics:
    """D01 metrics computed from canonical rows (level A)."""

    values: Tuple[Tuple[str, int], ...]

    def get(self, name: str) -> int:
        return dict(self.values)[name]

    def to_dict(self) -> dict:
        data = {name: value for name, value in self.values}
        data["definitions"] = dict(contract.D01_METRIC_DEFINITIONS)
        data["normalization"] = contract.D01_NORMALIZATION
        data["distinct_rule"] = contract.D01_DISTINCT_RULE
        return data


def _norm(value: Optional[str]) -> str:
    """The governed normalization — one implementation, shared with the association chain."""
    return normalize_upper_trim(value)


def _is_blank(value: Optional[str]) -> bool:
    return normalize_upper_trim(value) == ""


class RowMetricAccumulator:
    """Incremental D01 level-A fold (G-I4-M1; compacted in G-I4-M1-CORRECTIVE).

    This class *is* the D01 level-A formula: :func:`compute_row_metrics` is a thin wrapper
    around it, so the governed formula exists exactly once. Every retained structure is exact and
    bounded by the number of **distinct values** the corpus contains, never by the row count:

    * five scalars (rows, blank/non-blank ISIN rows, blank symbol rows);
    * the shared :class:`~nse_engine.compact.RowTokens` tables: ``len(tokens.isin)`` is
      ``distinct_nonblank_isin`` and the interned non-blank symbol counter is
      ``distinct_nonblank_symbol`` (the metric fold previously kept two duplicate
      ``set[str]`` copies of exactly these values);
    * one :class:`~nse_engine.compact.Uint64Set` of ``(symbol_id, series_id)`` pairs for
      ``distinct_symbol_series_pairs`` — previously a ``set`` of ``(str, str)`` tuples, i.e. one
      boxed tuple plus two boxed strings per distinct pair.

    ``symbol_series_duplicate_rows`` stays exact: every row contributes to exactly one pair, so
    ``sum(count - 1) == rows - len(pairs)``.

    When ``tokens`` is supplied the metric fold and the association accumulator share one copy of
    every distinct ISIN and symbol; when it is omitted the accumulator owns a private set (the
    standalone ``compute_row_metrics`` path is unchanged).
    """

    __slots__ = (
        "_pairs",
        "_series",
        "blank_isin",
        "blank_symbol",
        "nonblank_isin",
        "rows",
        "tokens",
    )

    #: pair key stride: ``symbol_id * _SERIES_STRIDE + series_id`` (both ids are uint32)
    _SERIES_STRIDE = 1 << 32

    def __init__(self, tokens: "RowTokens | None" = None) -> None:
        self.tokens = tokens if tokens is not None else RowTokens()
        self.rows = 0
        self.blank_symbol = 0
        self.blank_isin = 0
        self.nonblank_isin = 0
        self._series = TokenIntern()
        self._pairs = Uint64Set()

    def add_row(self, row: SecurityRow) -> None:
        symbol = row.listing_symbol
        isin = row.security_isin
        series = row.series
        self.rows += 1
        normal_symbol = _norm(symbol)
        if not normal_symbol:
            self.blank_symbol += 1
        symbol_id = self.tokens.symbol_id(normal_symbol)
        normal_isin = _norm(isin)
        if not normal_isin:
            self.blank_isin += 1
        else:
            self.nonblank_isin += 1
            self.tokens.isin_id(normal_isin)
        series_id = self._series.id((series or "").strip())
        self._pairs.add(symbol_id * self._SERIES_STRIDE + series_id)

    def add_rows(self, rows: Sequence[SecurityRow]) -> None:
        for row in rows:
            self.add_row(row)

    def result(self) -> "RowMetrics":
        """The governed ``RowMetrics`` values tuple (same names, same order, same assertion)."""
        distinct_isin = len(self.tokens.isin)
        distinct_symbol = self.tokens.distinct_symbol_count()
        distinct_pairs = len(self._pairs)
        duplicate_rows = self.rows - distinct_pairs
        values = (
            ("rows", self.rows),
            ("blank_symbol_rows", self.blank_symbol),
            ("blank_isin_rows", self.blank_isin),
            ("nonblank_isin_rows", self.nonblank_isin),
            ("distinct_nonblank_isin", distinct_isin),
            ("isins_extra_duplicate_rows", self.nonblank_isin - distinct_isin),
            ("distinct_nonblank_symbol", distinct_symbol),
            ("distinct_symbol_series_pairs", distinct_pairs),
            ("symbol_series_duplicate_rows", duplicate_rows),
        )
        if tuple(name for name, _value in values) != contract.D01_METRIC_NAMES:
            raise AssertionError("metric set drifted from the governed D01 name set")
        return RowMetrics(values=values)


def compute_row_metrics(rows: Sequence[SecurityRow]) -> RowMetrics:
    """Apply the governed D01 formulas to canonical rows (exact, deterministic)."""
    accumulator = RowMetricAccumulator()
    accumulator.add_rows(rows)
    return accumulator.result()


@dataclass(frozen=True)
class DefinitionVerdict:
    """Recomputed ``FIX-SEM-DEF-01__d01_definition_verdict.json`` algebra (level B)."""

    discriminating_files: int
    match_distinct_nonblank: int
    match_nonblank_rows: int
    verdict: str

    def to_dict(self) -> dict:
        return {
            "discriminating_files": self.discriminating_files,
            "match_distinct_nonblank": self.match_distinct_nonblank,
            "match_nonblank_rows": self.match_nonblank_rows,
            "verdict": self.verdict,
        }


def fold_file_metrics(records: Sequence[FileMetricRecord]) -> dict:
    """Fold frozen per-file D01 metrics into per-format and corpus totals (level B)."""
    per_format: Dict[str, dict] = {}
    totals = {
        "files": 0,
        "rows": 0,
        "blank_isin_rows": 0,
        "blank_symbol_rows": 0,
        "nonblank_isin_rows": 0,
        "isins_extra_duplicate_rows": 0,
        "symbol_series_duplicate_rows": 0,
    }
    discriminating = 0
    match_isin_distinct = 0
    match_isin_rows = 0
    match_symbol_distinct = 0
    match_symbol_rows = 0
    boolean_consistent = 0

    for record in records:
        bucket = per_format.setdefault(
            record.format_family,
            {
                "files": 0,
                "rows": 0,
                "blank_isin_rows": 0,
                "blank_symbol_rows": 0,
                "nonblank_isin_rows": 0,
                "distinct_nonblank_isin_sum": 0,
                "distinct_nonblank_symbol_sum": 0,
                "distinct_symbol_series_pairs_sum": 0,
                "isins_extra_duplicate_rows": 0,
                "symbol_series_duplicate_rows": 0,
            },
        )
        bucket["files"] += 1
        bucket["rows"] += record.rows
        bucket["blank_isin_rows"] += record.blank_isin_rows
        bucket["blank_symbol_rows"] += record.blank_symbol_rows
        bucket["nonblank_isin_rows"] += record.nonblank_isin_rows
        bucket["distinct_nonblank_isin_sum"] += record.distinct_nonblank_isin
        bucket["distinct_nonblank_symbol_sum"] += record.distinct_nonblank_symbol
        bucket["distinct_symbol_series_pairs_sum"] += record.distinct_symbol_series_pairs
        bucket["isins_extra_duplicate_rows"] += record.isins_extra_duplicate_rows
        bucket["symbol_series_duplicate_rows"] += record.symbol_series_duplicate_rows

        totals["files"] += 1
        totals["rows"] += record.rows
        totals["blank_isin_rows"] += record.blank_isin_rows
        totals["blank_symbol_rows"] += record.blank_symbol_rows
        totals["nonblank_isin_rows"] += record.nonblank_isin_rows
        totals["isins_extra_duplicate_rows"] += record.isins_extra_duplicate_rows
        totals["symbol_series_duplicate_rows"] += record.symbol_series_duplicate_rows

        # Independent re-derivation of the definition booleans from the numeric columns.
        # A file DISCRIMINATES the two readings only when they differ (distinct-nonblank vs
        # nonblank-rows); the fixture's own boolean columns are cross-checked, not trusted.
        isin_eq_distinct = record.d01_isin_count == record.distinct_nonblank_isin
        isin_eq_rows = record.d01_isin_count == record.nonblank_isin_rows
        sym_eq_distinct = record.d01_symbol_count == record.distinct_nonblank_symbol
        sym_eq_rows = record.d01_symbol_count == (
            record.rows - record.blank_symbol_rows
        )
        if isin_eq_distinct == record.d01_isin_eq_distinct_nonblank and isin_eq_rows == (
            record.d01_isin_eq_nonblank_rows
        ) and sym_eq_distinct == record.d01_sym_eq_distinct_nonblank and sym_eq_rows == (
            record.d01_sym_eq_rows
        ):
            boolean_consistent += 1
        if record.distinct_nonblank_isin != record.nonblank_isin_rows:
            discriminating += 1
            if isin_eq_distinct:
                match_isin_distinct += 1
            if isin_eq_rows:
                match_isin_rows += 1
            if sym_eq_distinct:
                match_symbol_distinct += 1
            if sym_eq_rows:
                match_symbol_rows += 1

    if discriminating == 0:
        # The published note: the verdict is derived only from discriminating files, so a set
        # with none cannot select a reading.
        verdict_value = contract.D01_VERDICT_UNDETERMINED
    elif match_isin_distinct == discriminating:
        verdict_value = contract.D01_VERDICT_ISIN_EQ_DISTINCT_NONBLANK
    elif match_isin_rows == discriminating:
        verdict_value = contract.D01_VERDICT_ISIN_EQ_NONBLANK_ROWS
    else:
        verdict_value = contract.D01_VERDICT_MIXED
    verdict = DefinitionVerdict(
        discriminating_files=discriminating,
        match_distinct_nonblank=match_isin_distinct,
        match_nonblank_rows=match_isin_rows,
        verdict=verdict_value,
    )
    return {
        "booleans_re_derived_consistently": boolean_consistent,
        "definition_verdict": verdict.to_dict(),
        "per_format": {key: dict(per_format[key]) for key in sorted(per_format)},
        "symbol_definition_verdict": {
            "discriminating_files": discriminating,
            "match_distinct_nonblank": match_symbol_distinct,
            "match_nonblank_rows": match_symbol_rows,
        },
        "totals": dict(totals),
    }


@dataclass(frozen=True)
class SeriesUniverseEntry:
    """One series in the D02-style universe recomputed from the D01 inventory."""

    series: str
    total_obs: int
    legacy_obs: int
    udiff_obs: int
    legacy_days: int
    udiff_days: int
    first_seen: str
    last_seen: str
    legacy_first: Optional[str]
    legacy_last: Optional[str]
    udiff_first: Optional[str]
    udiff_last: Optional[str]
    max_rows_per_day: int
    format_presence: str
    provisional_class: Optional[str] = None
    classification_basis: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "classification_basis": self.classification_basis,
            "first_seen": self.first_seen,
            "format_presence": self.format_presence,
            "last_seen": self.last_seen,
            "legacy_days": self.legacy_days,
            "legacy_first": self.legacy_first,
            "legacy_last": self.legacy_last,
            "legacy_obs": self.legacy_obs,
            "max_rows_per_day": self.max_rows_per_day,
            "provisional_class": self.provisional_class,
            "series": self.series,
            "total_obs": self.total_obs,
            "udiff_days": self.udiff_days,
            "udiff_first": self.udiff_first,
            "udiff_last": self.udiff_last,
            "udiff_obs": self.udiff_obs,
        }


def series_universe(
    inventory: Sequence[InventoryFileRecord],
    class_by_series: Optional[Mapping[str, Tuple[str, str]]] = None,
) -> Tuple[SeriesUniverseEntry, ...]:
    """Recompute per-series observation facts from the D01 inventory ``series_counts``.

    ``class_by_series`` is *evidence input* (D02's provisional classification) and is carried,
    never re-derived: classifying a series would be a semantic act W2 is not authorized to take.
    """
    observations: Dict[str, Dict[str, object]] = {}
    for record in inventory:
        family = INVENTORY_ROOT_TO_FAMILY.get(record.root, record.root)
        for series, count in record.series_counts:
            entry = observations.setdefault(
                series,
                {
                    "total": 0,
                    "legacy": 0,
                    "udiff": 0,
                    "legacy_days": 0,
                    "udiff_days": 0,
                    "first": None,
                    "last": None,
                    "legacy_first": None,
                    "legacy_last": None,
                    "udiff_first": None,
                    "udiff_last": None,
                    "max_day": 0,
                },
            )
            entry["total"] = int(entry["total"]) + count
            if family == contract.FAMILY_LEGACY:
                entry["legacy"] = int(entry["legacy"]) + count
                entry["legacy_days"] = int(entry["legacy_days"]) + 1
                if entry["legacy_first"] is None or record.date < str(entry["legacy_first"]):
                    entry["legacy_first"] = record.date
                if entry["legacy_last"] is None or record.date > str(entry["legacy_last"]):
                    entry["legacy_last"] = record.date
            else:
                entry["udiff"] = int(entry["udiff"]) + count
                entry["udiff_days"] = int(entry["udiff_days"]) + 1
                if entry["udiff_first"] is None or record.date < str(entry["udiff_first"]):
                    entry["udiff_first"] = record.date
                if entry["udiff_last"] is None or record.date > str(entry["udiff_last"]):
                    entry["udiff_last"] = record.date
            if entry["first"] is None or record.date < str(entry["first"]):
                entry["first"] = record.date
            if entry["last"] is None or record.date > str(entry["last"]):
                entry["last"] = record.date
            entry["max_day"] = max(int(entry["max_day"]), count)

    entries = []
    for series in sorted(observations):
        entry = observations[series]
        has_legacy = int(entry["legacy_days"]) > 0
        has_udiff = int(entry["udiff_days"]) > 0
        if has_legacy and has_udiff:
            presence = "BOTH"
        elif has_legacy:
            presence = "LEGACY_ONLY"
        else:
            presence = "UDIFF_ONLY"
        provisional_class = None
        classification_basis = None
        if class_by_series and series in class_by_series:
            provisional_class, classification_basis = class_by_series[series]
        entries.append(
            SeriesUniverseEntry(
                series=series,
                total_obs=int(entry["total"]),
                legacy_obs=int(entry["legacy"]),
                udiff_obs=int(entry["udiff"]),
                legacy_days=int(entry["legacy_days"]),
                udiff_days=int(entry["udiff_days"]),
                first_seen=str(entry["first"]),
                last_seen=str(entry["last"]),
                legacy_first=entry["legacy_first"],
                legacy_last=entry["legacy_last"],
                udiff_first=entry["udiff_first"],
                udiff_last=entry["udiff_last"],
                max_rows_per_day=int(entry["max_day"]),
                format_presence=presence,
                provisional_class=provisional_class,
                classification_basis=classification_basis,
            )
        )
    return tuple(entries)


def series_class_rollup(entries: Iterable[SeriesUniverseEntry]) -> Tuple[dict, ...]:
    """Fold series entries by their carried provisional class (evidence input, not re-derived)."""
    buckets: Dict[str, dict] = {}
    for entry in entries:
        key = entry.provisional_class or "UNCLASSIFIED"
        bucket = buckets.setdefault(key, {"n_codes": 0, "total_obs": 0})
        bucket["n_codes"] += 1
        bucket["total_obs"] += entry.total_obs
    total = sum(bucket["total_obs"] for bucket in buckets.values())
    rollup = []
    for key in sorted(buckets):
        bucket = buckets[key]
        rollup.append(
            {
                "n_codes": bucket["n_codes"],
                "pct_of_all_rows": round(100.0 * bucket["total_obs"] / total, 3) if total else 0.0,
                "provisional_class": key,
                "total_obs": bucket["total_obs"],
            }
        )
    return tuple(rollup)


def fold_metrics_by_year(
    records: Sequence[FileMetricRecord], date_by_file: Mapping[str, str]
) -> Tuple[dict, ...]:
    """Fold per-file D01 metrics by calendar year using the D01 file-date mapping."""
    buckets: Dict[int, dict] = {}
    for record in records:
        date = date_by_file.get(record.file_name)
        if date is None:
            raise KeyError("no D01 date for file %r (fail-closed)" % record.file_name)
        year = int(date[0:4])
        bucket = buckets.setdefault(
            year,
            {
                "year": year,
                "files": 0,
                "rows": 0,
                "blank_isin_rows": 0,
                "symbol_series_duplicate_rows": 0,
                "nonblank_isin_rows": 0,
            },
        )
        bucket["files"] += 1
        bucket["rows"] += record.rows
        bucket["blank_isin_rows"] += record.blank_isin_rows
        bucket["nonblank_isin_rows"] += record.nonblank_isin_rows
        bucket["symbol_series_duplicate_rows"] += record.symbol_series_duplicate_rows
    return tuple(buckets[year] for year in sorted(buckets))
