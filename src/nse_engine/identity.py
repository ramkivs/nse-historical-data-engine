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

from array import array
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple

from . import contract
from .compact import RowTokens, TokenIntern, normalize_upper_trim
from .provenance import Provenance
from .rows import SecurityRow


class AssociationStreamError(ValueError):
    """Fail-closed error for the streaming association accumulator (G-I4-M1)."""


@dataclass(frozen=True)
class AssociationRow:
    """The exact projection of a canonical row that association building reads.

    Association building (D05 §3.2/§3.3) reads only these seven facts. The projection exists so
    the bounded-memory accumulator can hold a packed form of them instead of complete
    ``SecurityRow`` objects (whose ``values``/``raw_line``/``flags`` are never needed here).
    """

    business_date: str
    line_number: int
    listing_symbol: str
    series: str
    security_isin: str
    isin_validity: str
    provenance: Provenance


def project_row(row: SecurityRow) -> AssociationRow:
    """Project a canonical row to the fields association building consumes."""
    return AssociationRow(
        business_date=row.business_date,
        line_number=row.line_number,
        listing_symbol=row.listing_symbol,
        series=row.series,
        security_isin=row.security_isin,
        isin_validity=row.isin_validity,
        provenance=row.provenance,
    )


def _pack_date(value: str) -> int:
    """Pack an ISO business date to ``YYYYMMDD`` for the accumulator's packed rows.

    Canonical rows only ever carry validated ISO dates (W1 parsing), so this round-trips exactly;
    anything else fails closed rather than being coerced.
    """
    if len(value) != 10 or value[4] != "-" or value[7] != "-":
        raise AssociationStreamError("business_date is not ISO YYYY-MM-DD: %r" % (value,))
    digits = value[0:4] + value[5:7] + value[8:10]
    if not digits.isdigit():
        raise AssociationStreamError("business_date is not ISO YYYY-MM-DD: %r" % (value,))
    return int(digits)


def _unpack_date(value: int) -> str:
    text = "%08d" % value
    return "%s-%s-%s" % (text[0:4], text[4:6], text[6:8])


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
        multi_symbol = 0
        multi_series = 0
        same_day = 0
        associations = 0
        for identity in self.identities:
            count, several_symbols, several_series, has_same_day = _identity_totals_flags(identity)
            associations += count
            multi_symbol += 1 if several_symbols else 0
            multi_series += 1 if several_series else 0
            same_day += 1 if has_same_day else 0
        return {
            "associations": associations,
            "identities": len(self.identities),
            "identities_with_multiple_series": multi_series,
            "identities_with_multiple_symbols": multi_symbol,
            "identities_with_same_day_parallel_states": same_day,
            "overlay_rows_excluded": sum(count for _series, count in self.overlay_rows_excluded),
            "unkeyed_groups": len(self.unkeyed),
            "unkeyed_rows": sum(len(group.line_numbers) for group in self.unkeyed),
        }


def _identity_totals_flags(identity: SecurityIdentity) -> Tuple[int, bool, bool, bool]:
    """The four per-identity facts ``totals()`` counts — one implementation for both paths."""
    symbols = {entry.symbol for entry in identity.associations}
    series = {entry.series for entry in identity.associations}
    same_day = False
    for key, value in identity.observations:
        if key == "same_day_parallel_states" and value != "0":
            same_day = True
    return (len(identity.associations), len(symbols) > 1, len(series) > 1, same_day)


@dataclass(frozen=True)
class AssociationSummary:
    """The small, row-bounded part of an association result (method, exclusions, unkeyed)."""

    method: str
    overlay_rows_excluded: Tuple[Tuple[str, int], ...]
    unkeyed: Tuple[UnkeyedRowGroup, ...]


def _normalize(isin: str) -> str:
    """The adopted correlation-key normalization (D05 §6.1) — one shared implementation."""
    return normalize_upper_trim(isin)


def _provenance_key(entry: Provenance) -> Tuple[str, str, str]:
    return (entry.member_name, entry.member_sha256_raw_bytes, entry.format_family)


def _dedupe_provenance(rows: Iterable[AssociationRow]) -> Tuple[Provenance, ...]:
    seen: Dict[Tuple[str, str, str], Provenance] = {}
    for row in rows:
        key = _provenance_key(row.provenance)
        seen.setdefault(key, row.provenance)
    return tuple(seen[key] for key in sorted(seen))


def build_associations(
    rows: Sequence[SecurityRow],
    overlay_series: Tuple[str, ...] = contract.OVERLAY_SERIES_OBSERVED,
) -> AssociationBuild:
    """Build correlation scopes and dated associations from canonical rows.

    This is the reference composition. It is expressed over
    :class:`AssociationAccumulator` so the incremental and the batch paths share one
    implementation of every rule below (G-I4-M1).
    """
    accumulator = AssociationAccumulator(overlay_series)
    accumulator.add_rows(rows)
    return accumulator.association_build()


class AssociationAccumulator:
    """Incremental form of :func:`build_associations` (D05 §3.2/§3.3).

    Rules preserved exactly (the batch path is expressed over this class, so there is one
    implementation of every rule below):

    * rows whose ``series`` is an observed overlay token are excluded from the transition chain
      and counted per series (never dropped, never silent);
    * a row whose normalized ISIN (upper/trim) is blank is recorded in an ``UnkeyedRowGroup``
      keyed by ``(reason, business_date, member_name)`` with its line numbers — never keyed;
    * remaining rows are keyed by the normalized ISIN; per identity the observations are
      ``(business_date, line_number)`` ordered and split into contiguous ``(symbol, series)``
      runs with observed-range intervals, same-day parallel states and
      ``other_states_within_observed_range`` observations;
    * provenance is deduplicated by ``(member_name, member_sha256_raw_bytes, format_family)``
      keeping the first entry in observation order, then sorted by that key.

    Retained state (G-I4-M1-CORRECTIVE). The previous revision kept one ``array('I')`` object and
    one dict entry per identity; that per-identity object overhead dominated the retained
    footprint on an identity-dominated corpus. This revision stores **one** packed row store plus
    two index arrays, and interns each distinct value once through
    :class:`~nse_engine.compact.RowTokens`:

    * ``_data`` — one ``array('I')`` with seven uint32 per row: packed ``YYYYMMDD`` date, line
      number, symbol token id, series token id, member id, validity token id, and a
      zero-means-none verbatim-symbol exception id;
    * ``_next`` — one signed int per row: the next row index of the same identity, forming an
      intrusive singly linked list (``-1`` terminates). Rows are prepended and the list is
      reversed during reconstruction, which restores arrival order — the order the batch path
      sorts from — so ties in ``(business_date, line_number)`` resolve identically;
    * ``_head`` — one signed int per identity: the first row index of that identity, ``-1`` when
      the identity has no keyed row (an ISIN seen only in overlay-excluded rows is interned for
      D01 but must never produce an identity document);
    * ``_tokens`` — the shared intern tables (see :class:`RowTokens`): the normalized ISIN table
      doubles as the D01 ``distinct_nonblank_isin`` source, and the normalized symbol table as the
      chain's symbol token space. A verbatim symbol is stored a second time **only** when it
      differs from its normalized form (an exception entry); otherwise the normalized token is
      itself the verbatim value.

    Complete ``SecurityRow`` objects are never retained, and reverse tables are built once per
    stream rather than once per identity.
    """

    _FIELDS_PER_ROW = 7

    def __init__(
        self,
        overlay_series: Tuple[str, ...] = contract.OVERLAY_SERIES_OBSERVED,
        tokens: "RowTokens | None" = None,
    ) -> None:
        self._overlay_tokens = tuple(overlay_series)
        self._tokens = tokens if tokens is not None else RowTokens()
        self._series_tokens = TokenIntern()
        self._validity_tokens = TokenIntern()
        self._member_index: Dict[Tuple[str, str, str], int] = {}
        self._member_provenance: List[Provenance] = []
        self._unkeyed: Dict[Tuple[str, str, str], List[Tuple[int, str]]] = {}
        self._excluded: Dict[str, int] = {}
        self._data = array("I")
        self._next = array("i")
        self._head = array("i")
        self._identity_count = 0

    # ---------------------------------------------------------------- ingestion
    def _member_id(self, provenance: Provenance) -> int:
        key = _provenance_key(provenance)
        member_id = self._member_index.get(key)
        if member_id is None:
            member_id = len(self._member_provenance)
            self._member_index[key] = member_id
            self._member_provenance.append(provenance)
        return member_id

    def add_row(self, row: AssociationRow) -> None:
        series_token = row.series
        if series_token in self._overlay_tokens:
            self._excluded[series_token] = self._excluded.get(series_token, 0) + 1
            return
        isin = _normalize(row.security_isin)
        member_id = self._member_id(row.provenance)
        if not isin:
            key = (
                contract.UNKEYED_REASON_BLANK_ISIN,
                row.business_date,
                row.provenance.member_name,
            )
            self._unkeyed.setdefault(key, []).append((row.line_number, series_token))
            return
        identity_id = self._tokens.isin_id(isin)
        normalized_symbol = normalize_upper_trim(row.listing_symbol)
        symbol_id = self._tokens.symbol_id(normalized_symbol)
        raw_symbol = row.listing_symbol
        exception_id = 0 if raw_symbol == normalized_symbol else self._tokens.raw_symbol_id(raw_symbol)
        index = len(self._next)
        self._data.extend(
            (
                _pack_date(row.business_date),
                row.line_number,
                symbol_id,
                self._series_tokens.id(series_token),
                member_id,
                self._validity_tokens.id(row.isin_validity),
                exception_id,
            )
        )
        self._next.append(-1)
        while len(self._head) <= identity_id:
            self._head.append(-1)
        head = self._head[identity_id]
        if head == -1:
            self._head[identity_id] = index
            self._identity_count += 1
        else:
            self._next[index] = head
            self._head[identity_id] = index

    def add_rows(self, rows: Sequence[AssociationRow]) -> None:
        for row in rows:
            self.add_row(row)

    def add_security_rows(self, rows: Sequence[SecurityRow]) -> None:
        """Convenience entry point: project canonical rows and ingest them."""
        for row in rows:
            self.add_row(project_row(row))

    # ---------------------------------------------------------------- reconstruction
    def _observations(self, identity_id: int, security_id: str) -> List[AssociationRow]:
        """Reconstruct one identity's observations (they are released after use)."""
        data = self._data
        links = self._next
        fields = self._FIELDS_PER_ROW
        symbols = self._tokens.symbol.by_id()
        exceptions = self._tokens.raw_symbol.by_id()
        series_tokens = self._series_tokens.by_id()
        validity = self._validity_tokens.by_id()
        provenance = self._member_provenance
        observations = []
        index = self._head[identity_id]
        while index != -1:
            base = index * fields
            symbol_id = data[base + 2]
            exception_id = data[base + 6]
            observations.append(
                AssociationRow(
                    business_date=_unpack_date(data[base]),
                    line_number=data[base + 1],
                    listing_symbol=(
                        exceptions[exception_id - 1] if exception_id else symbols[symbol_id]
                    ),
                    series=series_tokens[data[base + 3]],
                    security_isin=security_id,
                    isin_validity=validity[data[base + 5]],
                    provenance=provenance[data[base + 4]],
                )
            )
            index = links[index]
        # rows were prepended; restoring arrival order keeps tie-breaking identical to the batch
        # path (which sorts the rows in the order they were added) — see the class docstring
        observations.reverse()
        observations.sort(key=lambda row: (row.business_date, row.line_number))
        return observations

    def _identity_for(self, security_id: str, identity_id: int) -> SecurityIdentity:
        return _identity_record(security_id, self._observations(identity_id, security_id))

    def identity_keys(self) -> List[str]:
        """Active identity keys (normalized ISINs with at least one keyed row), sorted.

        An ISIN that appears only in overlay-excluded or unkeyed rows is interned for D01 but has
        no identity document, exactly as the batch path produced no identity for it.
        """
        heads = self._head
        head_count = len(heads)
        active = [
            key
            for key, token_id in self._tokens.isin.items()
            if token_id < head_count and heads[token_id] != -1
        ]
        active.sort()
        return active

    def identity_count(self) -> int:
        """Number of identities with at least one keyed row (never the intern length)."""
        return self._identity_count

    def keyed_row_count(self) -> int:
        """Rows held in the packed store (keyed rows; overlay/unkeyed rows are counted apart)."""
        return len(self._next)

    # ---------------------------------------------------------------- results
    def identity_documents(self) -> Iterator[SecurityIdentity]:
        """Ordered iterator over identity documents, one identity at a time."""
        isin_ids = self._tokens.isin
        for security_id in self.identity_keys():
            yield self._identity_for(security_id, isin_ids.id(security_id))

    def identity_stream(self) -> "IdentityStream":
        """A single-pass stream that also accumulates the ``totals()`` counters."""
        return IdentityStream(self)

    def unkeyed_groups(self) -> Tuple[UnkeyedRowGroup, ...]:
        return tuple(
            UnkeyedRowGroup(
                reason=key[0],
                business_date=key[1],
                member_name=key[2],
                line_numbers=tuple(sorted(line for line, _series in group)),
                series_tokens=tuple(sorted({series for _line, series in group})),
            )
            for key, group in sorted(self._unkeyed.items())
        )

    def overlay_rows_excluded(self) -> Tuple[Tuple[str, int], ...]:
        return tuple(sorted(self._excluded.items()))

    def summary(self) -> AssociationSummary:
        return AssociationSummary(
            method=contract.ASSOCIATION_CHAIN_METHOD,
            overlay_rows_excluded=self.overlay_rows_excluded(),
            unkeyed=self.unkeyed_groups(),
        )

    def association_build(self) -> AssociationBuild:
        """Materialise the batch result (used by the reference composition)."""
        return AssociationBuild(
            identities=tuple(self.identity_documents()),
            unkeyed=self.unkeyed_groups(),
            overlay_rows_excluded=self.overlay_rows_excluded(),
        )


class IdentityStream:
    """Ordered, single-pass identity documents over accumulated state.

    Iterating yields the same ``SecurityIdentity`` objects, in the same order, that
    :meth:`AssociationAccumulator.association_build` would materialise, while accumulating the
    ``totals()`` counters with the same formula the batch result uses. Nothing is materialised
    beyond the identity currently being yielded.
    """

    def __init__(self, accumulator: AssociationAccumulator) -> None:
        self._accumulator = accumulator
        self._identities = 0
        self._associations = 0
        self._multi_symbols = 0
        self._multi_series = 0
        self._same_day = 0
        self._complete = False

    def __iter__(self) -> Iterator[SecurityIdentity]:
        accumulator = self._accumulator
        isin_ids = accumulator._tokens.isin
        for security_id in accumulator.identity_keys():
            identity = accumulator._identity_for(security_id, isin_ids.id(security_id))
            count, several_symbols, several_series, has_same_day = _identity_totals_flags(identity)
            self._identities += 1
            self._associations += count
            self._multi_symbols += 1 if several_symbols else 0
            self._multi_series += 1 if several_series else 0
            self._same_day += 1 if has_same_day else 0
            yield identity
        self._complete = True

    def totals(self) -> dict:
        """The same totals document as ``AssociationBuild.totals()`` (after full iteration)."""
        if not self._complete:
            raise AssociationStreamError(
                "totals() requires the identity stream to be consumed to the end"
            )
        return {
            "associations": self._associations,
            "identities": self._identities,
            "identities_with_multiple_series": self._multi_series,
            "identities_with_multiple_symbols": self._multi_symbols,
            "identities_with_same_day_parallel_states": self._same_day,
            "overlay_rows_excluded": sum(
                count for _series, count in self._accumulator.overlay_rows_excluded()
            ),
            "unkeyed_groups": len(self._accumulator._unkeyed),
            "unkeyed_rows": sum(len(group) for group in self._accumulator._unkeyed.values()),
        }


def _identity_record(security_id: str, observations: Sequence[AssociationRow]) -> SecurityIdentity:
    """Assemble one ``SecurityIdentity`` document from its ordered observations."""
    associations = _associations_for(security_id, observations)
    dates = sorted({row.business_date for row in observations})
    isin_validity_values = {row.isin_validity for row in observations}
    return SecurityIdentity(
        security_id=security_id,
        identity_basis=contract.IDENTITY_KEY_BASIS,
        isin_list=(security_id,),
        # D05 §3.2: nullable boolean from the validity flag. True only when every
        # observation is classified VALID; anything else stays UNDETERMINED (None) —
        # W2 does not assert invalidity of an identity from an informational flag
        # (D05 §5: flags never gate or de-key; W1-DIV-1 keeps the flag's census
        # evidence ungoverned). The raw value set is recorded in ``observations``.
        is_valid_isin_format=(True if isin_validity_values == {"VALID"} else None),
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


def _associations_for(
    security_id: str, observations: Sequence[AssociationRow]
) -> Tuple[DatedAssociation, ...]:
    """One association per contiguous run of an identical (symbol, series) state (D05 §3.3)."""
    dates = {row.business_date for row in observations}
    state_dates: Dict[Tuple[str, str], set] = {}
    # NOTE: one association per contiguous run of an identical (symbol, series) state in
    # ``(business_date, line_number)`` order (D05 §3.3). The batch path and the bounded-memory
    # accumulator both call this function, so the rule exists exactly once (G-I4-M1).
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
