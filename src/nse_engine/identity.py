"""W2 / I2 — security identity and dated associations (D05 §3.2–§3.3; D07 §13-A).

Builds, from canonical rows only:

* ``SecurityIdentity`` correlation scopes keyed by the **adopted** correlation key
  (``security_isin`` normalized upper/trim — D05 §6.1), explicitly NOT an exchange-authoritative
  identity (D05 §3.2 non-assumption; continuity policy across eras stays OPEN);
* ``DatedAssociation`` rows — one per contiguous run of an identical ``(symbol, series)`` state
  in observation order (D05 §3.3), with ``interval_basis = "observed-range"`` and
  ``association_type = "corpus-observed"`` (the only type that exists today).

Fail-closed / no-fabrication rules:

* a row whose ISIN is blank cannot key an identity — it is recorded in an ``UnkeyedRowGroup``
  with its member, line numbers and reason instead of being assigned to a fabricated identity;
* rows with a non-blank ISIN are keyed **regardless of ISIN validity flags** (D05 §5: flags never
  gate or de-key anything);
* association intervals are *observed ranges*, never claimed validity periods — the assertion
  that a state was continuously in force between two observations is not made;
* overlay rows are excluded from the transition chain exactly as the governed corpus method does
  (``FIX-SYMBOL-HIST-01`` method string), and the exclusion is counted and reported — never silent
  (D05 §3.5.5 forbids merge/drop/dedupe, and this is neither: the rows keep their own
  ``SecurityRow`` records and are tracked here);
* no many-to-one or one-to-many collapse: two states on one date remain two associations with the
  same ``observed_from`` and an explicit ``same_day_parallel_states`` observation.

This module performs no IO and consults no clock.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from . import contract
from .provenance import Provenance
from .rows import SecurityRow


@dataclass(frozen=True)
class AssociationObservationRow:
    """A single canonical row contributing to an association (traceability)."""

    business_date: str
    line_number: int
    member_name: str


@dataclass(frozen=True)
class DatedAssociation:
    """D05 §3.3 ``DatedAssociation`` (structure adopted; interval basis observed-range)."""

    security_id: str
    symbol: str
    series: str
    observed_from: str
    observed_to: str
    provenance: Tuple[Provenance, ...]
    contributing_rows: Tuple[AssociationObservationRow, ...]
    interval_basis: str = contract.INTERVAL_BASIS_OBSERVED_RANGE
    association_type: str = contract.ASSOCIATION_TYPE_CORPUS_OBSERVED
    observations: Tuple[Tuple[str, str], ...] = ()

    def to_dict(self) -> dict:
        return {
            "association_type": self.association_type,
            "contributing_rows": [
                {
                    "business_date": row.business_date,
                    "line_number": row.line_number,
                    "member_name": row.member_name,
                }
                for row in self.contributing_rows
            ],
            "interval_basis": self.interval_basis,
            "observations": {key: value for key, value in self.observations},
            "observed_from": self.observed_from,
            "observed_to": self.observed_to,
            "provenance": [entry.to_dict() for entry in self.provenance],
            "security_id": self.security_id,
            "series": self.series,
            "symbol": self.symbol,
        }


@dataclass(frozen=True)
class SecurityIdentity:
    """D05 §3.2 ``SecurityIdentity`` (structure adopted; the key is the adopted correlation key)."""

    security_id: str
    identity_basis: str
    isin_list: Tuple[str, ...]
    is_valid_isin_format: Optional[bool]
    first_observed: str
    last_observed: str
    associations: Tuple[DatedAssociation, ...]
    provenance: Tuple[Provenance, ...]
    observations: Tuple[Tuple[str, str], ...] = ()
    non_promotion_note: str = contract.IDENTITY_NON_PROMOTION_NOTE

    def to_dict(self) -> dict:
        return {
            "associations": [entry.to_dict() for entry in self.associations],
            "first_observed": self.first_observed,
            "identity_basis": self.identity_basis,
            "is_valid_isin_format": self.is_valid_isin_format,
            "isin_list": list(self.isin_list),
            "last_observed": self.last_observed,
            "non_promotion_note": self.non_promotion_note,
            "observations": {key: value for key, value in self.observations},
            "provenance": [entry.to_dict() for entry in self.provenance],
            "security_id": self.security_id,
        }


@dataclass(frozen=True)
class UnkeyedRowGroup:
    """Canonical rows that cannot be assigned to any identity correlation scope."""

    reason: str
    business_date: str
    member_name: str
    line_numbers: Tuple[int, ...]
    series_tokens: Tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "business_date": self.business_date,
            "line_numbers": list(self.line_numbers),
            "member_name": self.member_name,
            "reason": self.reason,
            "series_tokens": list(self.series_tokens),
        }


@dataclass(frozen=True)
class AssociationBuild:
    identities: Tuple[SecurityIdentity, ...]
    unkeyed: Tuple[UnkeyedRowGroup, ...]
    overlay_rows_excluded: Tuple[Tuple[str, int], ...]
    method: str = contract.ASSOCIATION_CHAIN_METHOD

    def totals(self) -> dict:
        multi_symbol = sum(1 for identity in self.identities if len(
            {entry.symbol for entry in identity.associations}
        ) > 1)
        multi_series = sum(1 for identity in self.identities if len(
            {entry.series for entry in identity.associations}
        ) > 1)
        same_day = sum(
            1
            for identity in self.identities
            if any(
                key == "same_day_parallel_states" and value != "0"
                for key, value in identity.observations
            )
        )
        return {
            "associations": sum(len(identity.associations) for identity in self.identities),
            "identities": len(self.identities),
            "identities_with_multiple_series": multi_series,
            "identities_with_multiple_symbols": multi_symbol,
            "identities_with_same_day_parallel_states": same_day,
            "overlay_rows_excluded": sum(count for _series, count in self.overlay_rows_excluded),
            "unkeyed_groups": len(self.unkeyed),
            "unkeyed_rows": sum(len(group.line_numbers) for group in self.unkeyed),
        }


def _normalize(isin: str) -> str:
    return isin.strip().upper()


def _provenance_key(entry: Provenance) -> Tuple[str, str, str]:
    return (entry.member_name, entry.member_sha256_raw_bytes, entry.format_family)


def _dedupe_provenance(rows: Iterable[SecurityRow]) -> Tuple[Provenance, ...]:
    seen: Dict[Tuple[str, str, str], Provenance] = {}
    for row in rows:
        key = _provenance_key(row.provenance)
        seen.setdefault(key, row.provenance)
    return tuple(seen[key] for key in sorted(seen))


def build_associations(
    rows: Sequence[SecurityRow],
    overlay_series: Tuple[str, ...] = contract.OVERLAY_SERIES_OBSERVED,
) -> AssociationBuild:
    """Build correlation scopes and dated associations from canonical rows."""
    overlay_tokens = tuple(overlay_series)
    keyed: Dict[str, List[SecurityRow]] = {}
    unkeyed: Dict[Tuple[str, str, str], List[SecurityRow]] = {}
    excluded: Dict[str, int] = {}

    for row in rows:
        series = row.series
        if series in overlay_tokens:
            excluded[series] = excluded.get(series, 0) + 1
            continue
        isin = _normalize(row.security_isin)
        if not isin:
            key = (
                contract.UNKEYED_REASON_BLANK_ISIN,
                row.business_date,
                row.provenance.member_name,
            )
            unkeyed.setdefault(key, []).append(row)
            continue
        keyed.setdefault(isin, []).append(row)

    identities: List[SecurityIdentity] = []
    for security_id in sorted(keyed):
        observations = sorted(
            keyed[security_id],
            key=lambda row: (row.business_date, row.line_number),
        )
        associations = _associations_for(security_id, observations)
        dates = sorted({row.business_date for row in observations})
        isin_validity_values = {row.isin_validity for row in observations}
        identities.append(
            SecurityIdentity(
                security_id=security_id,
                identity_basis=contract.IDENTITY_KEY_BASIS,
                isin_list=(security_id,),
                # D05 §3.2: nullable boolean from the validity flag. True only when every
                # observation is classified VALID; anything else stays UNDETERMINED (None) —
                # W2 does not assert invalidity of an identity from an informational flag
                # (D05 §5: flags never gate or de-key; W1-DIV-1 keeps the flag's census
                # evidence ungoverned). The raw value set is recorded in ``observations``.
                is_valid_isin_format=(
                    True if isin_validity_values == {"VALID"} else None
                ),
                first_observed=dates[0],
                last_observed=dates[-1],
                associations=associations,
                provenance=_dedupe_provenance(observations),
                observations=(
                    ("associations", str(len(associations))),
                    ("observation_rows", str(len(observations))),
                    (
                        "same_day_parallel_states",
                        str(
                            sum(
                                1
                                for entry in associations
                                if dict(entry.observations).get("same_day_parallel_states") == "true"
                            )
                        ),
                    ),
                    ("series_observed", ",".join(sorted({row.series for row in observations}))),
                    ("symbols_observed", str(len({row.listing_symbol for row in observations}))),
                    ("isin_validity_values", ",".join(sorted(isin_validity_values))),
                ),
            )
        )

    unkeyed_groups = tuple(
        UnkeyedRowGroup(
            reason=key[0],
            business_date=key[1],
            member_name=key[2],
            line_numbers=tuple(row.line_number for row in sorted(group, key=lambda r: r.line_number)),
            series_tokens=tuple(sorted({row.series for row in group})),
        )
        for key, group in sorted(unkeyed.items())
    )

    return AssociationBuild(
        identities=tuple(identities),
        unkeyed=unkeyed_groups,
        overlay_rows_excluded=tuple(sorted(excluded.items())),
    )


def _associations_for(
    security_id: str, observations: Sequence[SecurityRow]
) -> Tuple[DatedAssociation, ...]:
    """One association per contiguous run of an identical (symbol, series) state (D05 §3.3)."""
    dates = {row.business_date for row in observations}
    state_dates: Dict[Tuple[str, str], set] = {}
    for row in observations:
        state_dates.setdefault((row.listing_symbol, row.series), set()).add(row.business_date)

    runs: List[List[SecurityRow]] = []
    for row in observations:
        state = (row.listing_symbol, row.series)
        if runs and (runs[-1][0].listing_symbol, runs[-1][0].series) == state:
            runs[-1].append(row)
        else:
            runs.append([row])

    associations = []
    for run in runs:
        symbols = {row.listing_symbol for row in run}
        series = {row.series for row in run}
        if len(symbols) != 1 or len(series) != 1:  # pragma: no cover - defensive
            raise AssertionError("association run must be a single (symbol, series) state")
        symbol = run[0].listing_symbol
        series_token = run[0].series
        observed_from = min(row.business_date for row in run)
        observed_to = max(row.business_date for row in run)
        run_dates = sorted({row.business_date for row in run})
        same_day_parallel = any(
            len(state_dates.get(other, set()) & set(run_dates)) > 0
            for other in state_dates
            if other != (symbol, series_token)
        )
        between = sorted(
            date for date in dates if observed_from <= date <= observed_to and date not in run_dates
        )
        associations.append(
            DatedAssociation(
                security_id=security_id,
                symbol=symbol,
                series=series_token,
                observed_from=observed_from,
                observed_to=observed_to,
                provenance=_dedupe_provenance(run),
                contributing_rows=tuple(
                    AssociationObservationRow(
                        business_date=row.business_date,
                        line_number=row.line_number,
                        member_name=row.provenance.member_name,
                    )
                    for row in run
                ),
                observations=(
                    ("interval_rule", contract.ASSOCIATION_INTERVAL_RULE),
                    ("observed_dates", str(len(run_dates))),
                    ("observation_rows", str(len(run))),
                    ("other_states_within_observed_range", str(len(between))),
                    ("same_day_parallel_states", "true" if same_day_parallel else "false"),
                ),
            )
        )
    return tuple(
        sorted(associations, key=lambda entry: (entry.observed_from, entry.symbol, entry.series))
    )
