"""Q3 instrument query (D16-10) — the slice's single query category.

Semantics, verified against the governing contract (D16-10 Q3; D05 §§3.1/5/6/8):

* instrument = (listing_symbol, series) — dated attributes, never durable identity
  (D05 §3.1: "SYMBOL never durable"; 845 ISINs with multiple symbols); ISIN is a
  non-identity attribute and is NOT a query key here;
* match = exact equality of the as-published ``listing_symbol`` and ``series``
  values (no case/whitespace normalisation, no expression language — D23 §10: no
  arbitrary query semantics outside the established Q1–Q10/saved-query boundary);
* results carry the canonical row exactly as stored: as-published field values
  (``source_values``; ``None`` = absent in that family, ``""`` = blank — neither is
  ever defaulted, D05 §2 rule 3), non-gating flags, ``business_date``, and the row's
  own D05 §8 provenance block;
* ``raw_line`` (retained raw text, L1 retention) is NOT part of the served view:
  serving exposes verbatim as-published field values; raw row text exposure would
  require a future explicit decision in the spirit of D16-08 class-5 exclusions;
* ordering is deterministic: (business_date, format_family, year, source file,
  source line number);
* read-only: the query streams class-(1) files and writes nothing; a query failure
  can never corrupt durable data (D16-09 invariant).
"""

from __future__ import annotations

import json
from typing import Optional, Tuple

from .baseline import Baseline, BaselineError
from .index import ServingIndexError

QUERY_ID = "Q3-instrument"


class QueryError(Exception):
    """Fail-closed query failure (bad input/contract violation; nothing served)."""


def query_instrument(
    baseline: Baseline,
    index: dict,
    symbol: str,
    series: str,
    year: Optional[int] = None,
) -> Tuple[dict, ...]:
    """Return the canonical rows for one (symbol, series) instrument, oldest first.

    ``year`` (optional) restricts the result to that calendar-year partition.
    An unknown instrument yields an empty tuple (not an error).
    """
    if not isinstance(symbol, str) or not isinstance(series, str):
        raise QueryError("query-input", "symbol and series must be strings")
    year_str: Optional[str] = None
    if year is not None:
        if not (isinstance(year, int) and not isinstance(year, bool) and 1000 <= year <= 9999):
            raise QueryError("query-input", "year must be a 4-digit integer")
        year_str = str(year)

    pair = [symbol, series]
    candidates = []
    for relative, meta in index.get("files", {}).items():
        if pair not in meta.get("instruments", []):
            continue
        if year_str is not None and meta.get("year") != year_str:
            continue
        candidates.append(relative)

    results = []
    for relative in sorted(candidates):
        meta = index["files"][relative]
        with open(baseline.path(relative), "r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except ValueError as exc:
                    raise QueryError("query-scan", "unparseable canonical row in %s: %s" % (relative, exc))
                values = obj.get("source_values")
                if not isinstance(values, dict):
                    raise QueryError("query-scan", "canonical row without contract keys in %s" % relative)
                if values.get("listing_symbol") != symbol or values.get("series") != series:
                    continue
                served = {key: value for key, value in obj.items() if key != "raw_line"}
                served["serving"] = {
                    "query": QUERY_ID,
                    "series": series,
                    "source_file": relative,
                    "source_file_family": meta.get("family"),
                    "source_file_year": meta.get("year"),
                    "symbol": symbol,
                }
                results.append(served)
    results.sort(
        key=lambda row: (
            row.get("business_date") or "",
            row.get("format_family") or "",
            row["serving"]["source_file_year"] or "",
            row["serving"]["source_file"],
            row.get("source_line_number") or 0,
        )
    )
    return tuple(results)


def partitions_listing(index: dict) -> dict:
    """Diagnostic partition table (internal support for Q3's year filter; D16-12
    Dashboard data is a later slice, not a product query exposed here)."""
    return dict(index.get("partitions", {}))
