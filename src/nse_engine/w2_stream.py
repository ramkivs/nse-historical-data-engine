"""W2 bounded-memory streaming composition (G-I4-M1).

The governed W2 derivations are:

* ``member_date_facts``  — per-member date facts (:mod:`nse_engine.calendar`);
* ``derive_calendar``    — row-free calendar derivation over governed evidence;
* ``compute_row_metrics``— D01 level-A metric fold (:mod:`nse_engine.metrics`);
* ``build_associations`` — identity correlation scopes and dated associations
  (:mod:`nse_engine.identity`).

`nse_engine.pipeline.build_w2()` composes all four over a tuple of complete
:class:`~nse_engine.pipeline.CanonicalBuild` objects. That is the reference composition and it
retains every build (and therefore every canonical row's ``values``/``raw_line``/``flags``) until
the single W2 call, which is what exhausted memory on the 2,462-archive corpus run.

:class:`W2Accumulator` composes the *same four* derivations incrementally, one member at a time,
without retaining builds or rows:

* member facts come from the engine's own :func:`nse_engine.calendar.member_date_fact`;
* metrics come from the engine's own :class:`nse_engine.metrics.RowMetricAccumulator` (the class
  ``compute_row_metrics`` is a wrapper around);
* associations come from the engine's own :class:`nse_engine.identity.AssociationAccumulator`
  (the class ``build_associations`` is a wrapper around), which holds a packed projection per
  identity and streams the identity documents in the governed order;
* the calendar is produced by the existing :func:`nse_engine.calendar.derive_calendar`.

Nothing here re-derives a governed formula, and ``build_w2()`` is itself expressed over this
module, so there is exactly one semantic implementation of W2 (G-I4-M1 §ENGINE BOUNDARY G).

Bounded state is packed and interned, not object-per-row: for a corpus of *N* rows the accumulator
holds ``7`` packed ``uint32`` per row, one row index per row, and one index per identity, plus one
interned copy of each **distinct** value (ISIN, symbol) that the two consumers share — instead of
a complete :class:`~nse_engine.rows.SecurityRow` graph per row, one container object per identity,
or duplicate metric-side sets of the same strings (G-I4-M1-CORRECTIVE).

This module performs no IO, consults no clock and reads no environment value.
"""

from __future__ import annotations

from typing import Iterable, Optional, Sequence, Tuple

from . import contract
from .compact import RowTokens
from .calendar import (
    CalendarLabelRecord,
    CalendarResult,
    CircularHolidayRecord,
    MemberDateFact,
    derive_calendar,
    member_date_fact,
)
from .evidence_inputs import InventoryFileRecord
from .identity import AssociationAccumulator, AssociationSummary, IdentityStream
from .metrics import RowMetricAccumulator, RowMetrics
from .rows import SecurityRow


class W2Accumulator:
    """Incremental W2 composition over canonical rows (bounded memory).

    Usage::

        accumulator = W2Accumulator()
        for build in builds:
            accumulator.add_member(build.rows, build.parse.header.family)
            # the build may be released here
        calendar = accumulator.calendar(inventory, labels, circular_holidays)
        metrics = accumulator.metrics()
        for identity in accumulator.identity_stream():
            ...
    """

    def __init__(self, overlay_series: Tuple[str, ...] = contract.OVERLAY_SERIES_OBSERVED) -> None:
        # one shared intern table set: the D01 distinct-ISIN count and the identity key space are
        # the same values, and the D01 distinct-symbol count is the chain's symbol token space, so
        # sharing stores each distinct string once (G-I4-M1-CORRECTIVE)
        self._tokens = RowTokens()
        self._metrics = RowMetricAccumulator(self._tokens)
        self._associations = AssociationAccumulator(overlay_series, self._tokens)
        self._facts: list = []
        self._members = 0

    # ---------------------------------------------------------------- ingestion
    def add_member(self, rows: Sequence[SecurityRow], family: str) -> None:
        """Add one member's canonical rows (``family`` = parse-level format family)."""
        self._members += 1
        fact = member_date_fact(family, rows)
        if fact.business_date:
            self._facts.append(fact)
        self.add_rows(rows)

    def add_rows(self, rows: Sequence[SecurityRow]) -> None:
        """Add canonical rows without a member date fact (metrics + associations only)."""
        self._metrics.add_rows(rows)
        self._associations.add_security_rows(rows)

    # ---------------------------------------------------------------- results
    def member_count(self) -> int:
        return self._members

    def member_facts(self) -> Tuple[MemberDateFact, ...]:
        """The same facts, in the same order, that ``member_date_facts(builds)`` returns."""
        return tuple(self._facts)

    def metrics(self) -> RowMetrics:
        return self._metrics.result()

    def calendar(
        self,
        inventory: Sequence[InventoryFileRecord],
        labels: Iterable[CalendarLabelRecord] = (),
        circular_holidays: Iterable[CircularHolidayRecord] = (),
    ) -> CalendarResult:
        return derive_calendar(inventory, labels, circular_holidays, self.member_facts())

    def identity_documents(self):
        """Ordered iterator over identity documents (``SecurityIdentity``), one at a time."""
        return self._associations.identity_documents()

    def identity_stream(self) -> IdentityStream:
        """Single-pass identity stream that also accumulates ``totals()``."""
        return self._associations.identity_stream()

    def association_summary(self) -> AssociationSummary:
        """Method, overlay exclusions and unkeyed groups (row-bounded; no identity pass)."""
        return self._associations.summary()

    def association_build(self):
        """Materialise the batch association result (reference composition only)."""
        return self._associations.association_build()

    def identity_count(self) -> int:
        return self._associations.identity_count()

    def row_count(self) -> int:
        return self._metrics.rows
