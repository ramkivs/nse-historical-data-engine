"""Compact, exact containers shared by the W2 streaming accumulator (G-I4-M1-CORRECTIVE).

The bounded-memory W2 composition retains two things per corpus: the association/identity state
and the D01 level-A distinct-value state. On an identity-dominated corpus (one distinct ISIN per
row, which is the corpus shape) the direct Python-object representation of that state dominated
the retained footprint — one ``array`` object and one key string per identity, a ``set`` of tuples
for the D01 symbol/series pairs, and separate (duplicate) normalization tables for the metric fold
and the association chain.

This module provides the three primitives that make the retained state compact **without changing
any governed value**:

* :func:`normalize_upper_trim` — the single ``strip().upper()`` normalization the D01 distinct
  rule and the ISIN correlation key both use (previously written twice);
* :class:`TokenIntern` — a ``value -> dense int id`` intern with a lazily built reverse table, so
  metric and association code can share **one** copy of each distinct string;
* :class:`Uint64Set` — an exact, allocation-free-set-of-Python-ints replacement for the D01
  ``(symbol, series)`` pair set: an open-addressed table of unsigned 64-bit integers.

Everything here is exact (no probabilistic membership, no truncation, no collision-based
approximation): the pair set stores the full 64-bit key and compares it on probe, so a key is
"present" only if the identical key was inserted. Hashing is a fixed integer mix, so membership is
independent of ``PYTHONHASHSEED``, platform or clock.

This module performs no IO, consults no clock and reads no environment value.
"""

from __future__ import annotations

from array import array
from typing import Dict, Iterator, List, Optional, Tuple

__all__ = ["normalize_upper_trim", "TokenIntern", "Uint64Set", "RowTokens"]

_MASK64 = (1 << 64) - 1  # 2**64 - 1


def normalize_upper_trim(value: Optional[str]) -> str:
    """The governed ``value or "" -> strip() -> upper()`` normalization.

    One implementation for both users of it: the D01 distinct-value rule
    (``distinct_nonblank_isin`` / ``distinct_nonblank_symbol``) and the adopted identity
    correlation key (``security_isin`` upper/trim — D05 §6.1). The expressions were identical
    before this module existed; keeping them identical is what lets the metric fold and the
    association chain share one intern table.
    """
    return (value or "").strip().upper()


class TokenIntern:
    """Insertion-ordered ``value -> int`` intern with a lazily built reverse table.

    * ids are dense and assigned in first-appearance order (deterministic for a given input);
    * :meth:`by_id` builds the reverse list **once** and caches it (it is invalidated by any new
      insertion), so reconstruction cost does not grow with the number of identities;
    * :meth:`keys` returns a fresh list the caller may sort in place.

    Values must be hashable; ids are never exposed in any governed output.
    """

    __slots__ = ("_ids", "_reverse")

    def __init__(self) -> None:
        self._ids: Dict[object, int] = {}
        self._reverse: Optional[List[object]] = None

    def id(self, token) -> int:
        """Return the id for ``token``, assigning the next dense id if it is new."""
        existing = self._ids.get(token)
        if existing is None:
            existing = len(self._ids)
            self._ids[token] = existing
            self._reverse = None
        return existing

    def lookup(self, token) -> Optional[int]:
        """Return the id for ``token`` or ``None`` (never inserts)."""
        return self._ids.get(token)

    def by_id(self) -> List[object]:
        """The cached reverse table (``reverse[id] == token``). Do not mutate the result."""
        reverse = self._reverse
        if reverse is None:
            reverse = [None] * len(self._ids)
            for token, token_id in self._ids.items():
                reverse[token_id] = token
            self._reverse = reverse
        return reverse

    def keys(self) -> List[object]:
        """A fresh list of the interned values (safe to sort in place)."""
        return list(self._ids)

    def items(self) -> Iterator[Tuple[object, int]]:
        return iter(self._ids.items())

    def __len__(self) -> int:
        return len(self._ids)


class RowTokens:
    """The intern tables one corpus's rows share between its two W2 consumers.

    Both consumers previously kept their **own** copy of the same distinct strings:

    * the D01 metric fold kept a ``set`` of normalized ISINs and a ``set`` of normalized symbols;
    * the association chain kept a ``dict`` keyed by normalized ISIN and a ``dict`` of symbols.

    With one shared :class:`TokenIntern` per value class the corpus stores each distinct string
    once, and the D01 counts become exact lengths/counters of the shared tables instead of
    duplicate sets:

    * ``isin`` — normalized non-blank ISINs; ``len(isin)`` **is** ``distinct_nonblank_isin``, and
      the intern id is the identity key used by the association store;
    * ``symbol`` — normalized symbols (the blank token included); the id is the association
      chain's symbol token, and the non-blank insertion counter **is**
      ``distinct_nonblank_symbol``;
    * ``raw_symbol`` — verbatim symbols that differ from their normalized form. The association
      output must carry the verbatim ``listing_symbol``; when the verbatim value equals its
      normalized form (the overwhelmingly common case, and the only case the governed corpus
      produces for clean symbols) no second copy of the string is retained at all. Its ids are
      stored 1-based so that packed field value ``0`` means "same as the normalized token".

    The counters are exact for every consumer that reads them: the metric fold ingests every row
    (including overlay rows, which it must count), so every distinct symbol the association chain
    could add is already interned by the time the chain looks it up; a chain-only consumer simply
    does not read the counters.
    """

    __slots__ = ("isin", "symbol", "raw_symbol", "_distinct_symbol")

    def __init__(self) -> None:
        self.isin = TokenIntern()
        self.symbol = TokenIntern()
        self.raw_symbol = TokenIntern()
        self._distinct_symbol = 0

    # ---------------------------------------------------------------- ingestion
    def isin_id(self, normalized_isin: str) -> int:
        """Intern a normalized non-blank ISIN (the caller decides blankness)."""
        return self.isin.id(normalized_isin)

    def symbol_id(self, normalized_symbol: str) -> int:
        """Intern a normalized symbol; a new non-blank token counts for D01."""
        existing = self.symbol.lookup(normalized_symbol)
        if existing is not None:
            return existing
        token_id = self.symbol.id(normalized_symbol)
        if normalized_symbol:
            self._distinct_symbol += 1
        return token_id

    def raw_symbol_id(self, raw_symbol) -> int:
        """Intern a verbatim symbol that differs from its normalized form (1-based id)."""
        return self.raw_symbol.id(raw_symbol) + 1

    # ---------------------------------------------------------------- reading
    def distinct_symbol_count(self) -> int:
        return self._distinct_symbol

    def raw_symbol_by_exception_id(self, exception_id: int):
        return self.raw_symbol.by_id()[exception_id - 1]


class Uint64Set:
    """Exact set of unsigned 64-bit integers in one ``array('Q')`` open-addressed table.

    Each slot holds ``key + 1`` (0 marks an empty slot), so membership is *exact*: a probe
    compares the stored key with the searched key and only then reports presence. Capacity is a
    power of two and grows by doubling at a 0.7 load factor; the table is the only Python object
    retained, so per-key overhead is the array slot (8 bytes plus load-factor slack) instead of a
    boxed ``int`` object plus a ``set`` entry.

    Keys are mixed with a fixed 64-bit integer mixer (no ``hash()``, no ``PYTHONHASHSEED``
    dependence), and the table is rebuilt deterministically on growth, so two runs over the same
    keys retain the same state and compute the same cardinality.
    """

    __slots__ = ("_slots", "_mask", "_count")

    _MIN_CAPACITY = 1 << 10
    _MAX_LOAD_NUMERATOR = 7
    _MAX_LOAD_DENOMINATOR = 10

    def __init__(self, capacity: int = _MIN_CAPACITY) -> None:
        size = self._MIN_CAPACITY
        while size < capacity:
            size <<= 1
        self._slots: array = array("Q", bytes(8 * size))
        self._mask = size - 1
        self._count = 0

    @staticmethod
    def _mix(key: int) -> int:
        """splitmix64 finalizer: deterministic, avalanche, no built-in ``hash``."""
        key = (key + 0x9E3779B97F4A7C15) & _MASK64
        key = ((key ^ (key >> 30)) * 0xBF58476D1CE4E5B9) & _MASK64
        key = ((key ^ (key >> 27)) * 0x94D049BB133111EB) & _MASK64
        return key ^ (key >> 31)

    def add(self, key: int) -> bool:
        """Insert ``key``; return ``True`` when it was not present before."""
        if key < 0 or key > _MASK64 - 1:
            raise ValueError("Uint64Set keys must be in [0, 2**64 - 2]: %r" % (key,))
        if (self._count + 1) * self._MAX_LOAD_DENOMINATOR > (self._mask + 1) * self._MAX_LOAD_NUMERATOR:
            self._grow()
        stored = key + 1
        slots = self._slots
        index = self._mix(key) & self._mask
        while True:
            current = slots[index]
            if current == 0:
                slots[index] = stored
                self._count += 1
                return True
            if current == stored:
                return False
            index = (index + 1) & self._mask

    def __contains__(self, key: int) -> bool:
        if key < 0 or key > _MASK64 - 1:
            return False
        stored = key + 1
        slots = self._slots
        index = self._mix(key) & self._mask
        while True:
            current = slots[index]
            if current == 0:
                return False
            if current == stored:
                return True
            index = (index + 1) & self._mask

    def __len__(self) -> int:
        return self._count

    def capacity(self) -> int:
        """The current slot count (evidence/diagnostic only; never a governed value)."""
        return self._mask + 1

    def _grow(self) -> None:
        old_slots = self._slots
        size = (self._mask + 1) << 1
        self._slots = array("Q", bytes(8 * size))
        self._mask = size - 1
        for stored in old_slots:
            if stored:
                key = stored - 1
                index = self._mix(key) & self._mask
                while self._slots[index]:
                    index = (index + 1) & self._mask
                self._slots[index] = stored
