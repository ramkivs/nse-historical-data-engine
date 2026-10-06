"""W2 / I2 — overlay evidence reconciliation (W1-DIV-OVERLAY; D07 §13-A overlays).

Two responsibilities, both evidence-only:

**1. Published-fixture accounting.** ``account_overlay_fixture`` folds the published per-row
overlay comparison fixture (``FIX-OVERLAY-SEM-01__per_overlay_row.csv``, 3,692 rows) into its
aggregate buckets so the published aggregate / DEC-2 evidence can be verified as internally
consistent. No matching semantics are involved.

**2. Disposition of the W1 overlay discrepancy.** W1 recorded that the engine's member-scoped
observations could not reproduce the published corpus-wide fixture on the published extract.
``determine_overlay_disposition`` re-derives that comparison with a **decisive base-presence
test** and mechanically classifies the cause:

* ``fixture_rows_row_not_in_extract`` — the fixture's overlay row is not in the published
  extract at all (extract coverage);
* ``unreproducible_with_base_absent`` — the fixture asserts ``BASE_SAME_ISIN`` but the asserted
  base row is absent from the extract, so no member-scoped engine can produce that verdict;
* ``unreproducible_with_base_present`` — a non-overlay same-ISIN row **is** in the extract and
  was still not matched: a genuine defect (must be zero);
* ``engine_observation_missing_for_sampled_row`` — the overlay row is in the extract but the
  engine produced no observation: a genuine defect (must be zero);
* ``engine_observations_without_fixture_row`` — the engine observed an overlay the fixture does
  not report at that key: a genuine defect (must be zero).

The cause is set to ``fixture_truncation_source_coverage`` only when every defect bucket is
zero; otherwise it stays ``unresolved``. The disagreement counts are always preserved: nothing
here tunes, forces or eliminates a match, and no historical count is coerced.

This module performs no IO and consults no clock.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Sequence, Tuple

from . import contract
from .errors import NseEngineError
from .evidence_inputs import (
    INVENTORY_ROOT_TO_FAMILY,
    ExtractCoverageRecord,
    FileMetricRecord,
    InventoryFileRecord,
    OverlayFixtureRow,
)
from .overlays import OverlayObservation
from .rows import SecurityRow


class OverlayEvidenceError(NseEngineError):
    """A governed evidence input needed for the reconciliation is missing (fail closed)."""


@dataclass(frozen=True)
class OverlayFixtureAccounting:
    """Aggregate buckets recomputed from the published per-row overlay fixture."""

    total_rows: int
    counts_by_format_series_match_type: Tuple[Tuple[str, int], ...]
    orphans_by_series: Tuple[Tuple[str, int], ...]
    qty_rel_counts: Tuple[Tuple[str, int], ...]
    base_same_isin_rows: int
    no_base_orphan_rows: int

    def to_dict(self) -> dict:
        return {
            "base_same_isin_rows": self.base_same_isin_rows,
            "counts_by_format_series_match_type": {
                key: value for key, value in self.counts_by_format_series_match_type
            },
            "no_base_orphan_rows": self.no_base_orphan_rows,
            "orphans_by_series": {key: value for key, value in self.orphans_by_series},
            "qty_rel_counts": {key: value for key, value in self.qty_rel_counts},
            "total_rows": self.total_rows,
        }


@dataclass(frozen=True)
class OverlayFixtureDisposition:
    """The W1-DIV-OVERLAY determination (preserved, classified, never eliminated)."""

    engine_observations: int
    fixture_rows_on_extract_dates: int
    matched_same_verdict: int
    matched_diff_verdict: int
    fixture_rows_row_not_in_extract: int
    unreproducible_with_base_absent: int
    unreproducible_with_base_present: int
    engine_observation_missing_for_sampled_row: int
    engine_observations_without_fixture_row: int
    coverage: Tuple[ExtractCoverageRecord, ...]
    cause: str
    divergence_id: str = contract.W1_DIV_OVERLAY_ID

    @property
    def defect_count(self) -> int:
        return (
            self.unreproducible_with_base_present
            + self.engine_observation_missing_for_sampled_row
            + self.engine_observations_without_fixture_row
        )

    def to_dict(self) -> dict:
        coverage_min = min(
            (record.coverage_ratio for record in self.coverage), default=0.0
        )
        coverage_max = max(
            (record.coverage_ratio for record in self.coverage), default=0.0
        )
        return {
            "cause": self.cause,
            "coverage": [
                {
                    "coverage_ratio": round(record.coverage_ratio, 6),
                    "date": record.date,
                    "extract_rows": record.extract_rows,
                    "full_file_rows": record.full_file_rows,
                    "member_name": record.member_name,
                }
                for record in self.coverage
            ],
            "coverage_max": round(coverage_max, 6),
            "coverage_min": round(coverage_min, 6),
            "defect_count": self.defect_count,
            "determination": dict(contract.W1_DIV_OVERLAY_DETERMINATION),
            "divergence_id": self.divergence_id,
            "engine_observation_missing_for_sampled_row": self.engine_observation_missing_for_sampled_row,
            "engine_observations": self.engine_observations,
            "engine_observations_without_fixture_row": self.engine_observations_without_fixture_row,
            "fixture_rows_on_extract_dates": self.fixture_rows_on_extract_dates,
            "fixture_rows_row_not_in_extract": self.fixture_rows_row_not_in_extract,
            "matched_diff_verdict": self.matched_diff_verdict,
            "matched_same_verdict": self.matched_same_verdict,
            "preserved_not_eliminated": True,
            "unreproducible_with_base_absent": self.unreproducible_with_base_absent,
            "unreproducible_with_base_present": self.unreproducible_with_base_present,
        }


def _normalize(value: Optional[str]) -> str:
    return (value or "").strip().upper()


def account_overlay_fixture(rows: Sequence[OverlayFixtureRow]) -> OverlayFixtureAccounting:
    """Fold the published per-row overlay fixture into aggregate buckets."""
    buckets: Dict[str, int] = {}
    orphans: Dict[str, int] = {}
    qty_rels: Dict[str, int] = {}
    base_same = 0
    orphan = 0
    for row in rows:
        key = "%s|%s|%s" % (row.format_family, row.overlay_series, row.match_type)
        buckets[key] = buckets.get(key, 0) + 1
        if row.match_type == contract.MATCH_TYPE_NO_BASE_ORPHAN:
            orphan += 1
            orphans[row.overlay_series] = orphans.get(row.overlay_series, 0) + 1
        elif row.match_type == contract.MATCH_TYPE_BASE_SAME_ISIN:
            base_same += 1
            qty_key = "%s|%s" % (row.overlay_series, row.qty_rel or "undetermined")
            qty_rels[qty_key] = qty_rels.get(qty_key, 0) + 1
    return OverlayFixtureAccounting(
        total_rows=len(rows),
        counts_by_format_series_match_type=tuple(sorted(buckets.items())),
        orphans_by_series=tuple(sorted(orphans.items())),
        qty_rel_counts=tuple(sorted(qty_rels.items())),
        base_same_isin_rows=base_same,
        no_base_orphan_rows=orphan,
    )


def assemble_disposition(
    builds: Sequence[object],
    inventory_records: Sequence[InventoryFileRecord],
    file_metric_records: Sequence[FileMetricRecord],
    fixture_rows: Sequence[OverlayFixtureRow],
) -> OverlayFixtureDisposition:
    """Assemble the published-evidence reconciliation from W1 builds + D01 records (no IO).

    The member identity/coverage come from the D01 inventory and the frozen D01 per-file metric
    evidence; the engine side comes from the W1 canonical builds (``source.member_name`` and
    ``observations``). Members without both records contribute their observations but no coverage
    row (nothing is estimated).
    """
    metric_by_name = {record.file_name: record for record in file_metric_records}
    inventory_by_date_root = {
        (record.date, record.root): record for record in inventory_records
    }
    family_to_root = {family: root for root, family in INVENTORY_ROOT_TO_FAMILY.items()}
    rows_by_date: Dict[str, list] = {}
    observations: list = []
    coverage: list = []
    for build in builds:
        build_rows = tuple(build.rows)
        if not build_rows:
            continue
        business_date = build_rows[0].business_date
        rows_by_date.setdefault(business_date, []).extend(build_rows)
        observations.extend(build.observations)
        root = family_to_root.get(build.parse.header.family)
        inventory = inventory_by_date_root.get((business_date, root))
        metric = metric_by_name.get(inventory.file_name) if inventory is not None else None
        if inventory is None or metric is None:
            raise OverlayEvidenceError(
                "no D01 evidence record (inventory + per-file metric) for member %s on %s"
                % (build.source.member_name, business_date)
            )
        coverage.append(
            ExtractCoverageRecord(
                date=business_date,
                member_name=inventory.file_name,
                extract_rows=len(build_rows),
                full_file_rows=metric.rows,
            )
        )
    return determine_overlay_disposition(
        tuple(observations),
        {date: tuple(rows) for date, rows in rows_by_date.items()},
        fixture_rows,
        tuple(coverage),
    )


def determine_overlay_disposition(
    observations: Sequence[OverlayObservation],
    rows_by_date: Mapping[str, Sequence[SecurityRow]],
    fixture_rows: Sequence[OverlayFixtureRow],
    coverage: Sequence[ExtractCoverageRecord],
    overlay_series: Tuple[str, ...] = contract.OVERLAY_SERIES_OBSERVED,
) -> OverlayFixtureDisposition:
    """Classify the member-scoped vs corpus-wide overlay discrepancy (decisive test)."""
    overlay_tokens = tuple(overlay_series)
    observation_index: Dict[Tuple[str, str, str], OverlayObservation] = {}
    for observation in observations:
        key = (
            observation.business_date,
            observation.overlay_series,
            _normalize(observation.isin),
        )
        observation_index[key] = observation

    fixture_index: Dict[Tuple[str, str, str], list] = {}
    for row in fixture_rows:
        key = (row.date, row.overlay_series, _normalize(row.overlay_isin))
        fixture_index.setdefault(key, []).append(row)

    extract_dates = set(rows_by_date)
    matched_same = 0
    matched_diff = 0
    not_in_extract = 0
    base_absent = 0
    base_present = 0
    engine_missing_for_sampled_row = 0

    for row in fixture_rows:
        if row.date not in extract_dates:
            continue
        key = (row.date, row.overlay_series, _normalize(row.overlay_isin))
        observation = observation_index.get(key)
        if observation is not None and observation.match_type == row.match_type:
            matched_same += 1
            continue
        member_rows = rows_by_date[row.date]
        same_isin_rows = [
            candidate
            for candidate in member_rows
            if _normalize(candidate.security_isin) == _normalize(row.overlay_isin)
        ]
        if observation is not None:
            matched_diff += 1
            base_rows = [
                candidate for candidate in same_isin_rows if candidate.series not in overlay_tokens
            ]
            if base_rows:
                base_present += 1
            else:
                base_absent += 1
            continue
        if not same_isin_rows:
            not_in_extract += 1
        else:
            engine_missing_for_sampled_row += 1

    without_fixture_row = sum(1 for key in observation_index if key not in fixture_index)

    defects = base_present + engine_missing_for_sampled_row + without_fixture_row
    cause = (
        contract.W1_DIV_OVERLAY_CAUSE_FIXTURE_TRUNCATION
        if defects == 0
        else contract.W1_DIV_OVERLAY_CAUSE_UNRESOLVED
    )
    return OverlayFixtureDisposition(
        engine_observations=len(observation_index),
        fixture_rows_on_extract_dates=sum(
            1 for row in fixture_rows if row.date in extract_dates
        ),
        matched_same_verdict=matched_same,
        matched_diff_verdict=matched_diff,
        fixture_rows_row_not_in_extract=not_in_extract,
        unreproducible_with_base_absent=base_absent,
        unreproducible_with_base_present=base_present,
        engine_observation_missing_for_sampled_row=engine_missing_for_sampled_row,
        engine_observations_without_fixture_row=without_fixture_row,
        coverage=tuple(sorted(coverage, key=lambda record: record.date)),
        cause=cause,
    )
