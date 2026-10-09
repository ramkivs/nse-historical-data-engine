"""Serving query surface (D16-10) — the slice's query categories.

Q1 dataset/partition selection + yearly summaries, Q2 date-range query, and the
Q3 instrument query. Semantics of Q3, verified against the governing contract
(D16-10 Q3; D05 §§3.1/5/6/8):

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

import datetime
import json
import re
from typing import Optional, Tuple

from .baseline import Baseline, BaselineError
from .index import ServingIndexError

QUERY_ID = "Q3-instrument"
DATASET_QUERY_ID = "Q1-dataset"
DATE_RANGE_QUERY_ID = "Q2-date-range"

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class QueryError(Exception):
    """Fail-closed query failure (bad input/contract violation; nothing served)."""

    def __init__(self, check: str, detail: str) -> None:
        super().__init__("%s: %s" % (check, detail))
        self.check = check
        self.detail = detail


def _validate_iso_date(label: str, value: object) -> str:
    """Fail closed unless ``value`` is a valid ISO calendar date (YYYY-MM-DD)."""
    if not isinstance(value, str) or not _ISO_DATE_RE.match(value):
        raise QueryError("query-input", "%s must be an ISO date (YYYY-MM-DD), got %r" % (label, value))
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        raise QueryError("query-input", "%s is not a valid calendar date: %r" % (label, value))
    return value


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


def query_date_range(
    baseline: Baseline,
    index: dict,
    date_from: str,
    date_to: str,
) -> Tuple[dict, ...]:
    """Q2 date-range query over canonical rows (D16-10 Q2).

    Both bounds are **inclusive** ISO business dates (YYYY-MM-DD) compared by
    exact as-published value — no normalisation, no expression language.
    Candidate files are narrowed with the per-file ``business_date`` bounds
    stored in the class-(4) index (serving-index/1.1); a file whose bounds are
    unknown (no dated row) or disjoint from the range cannot match and is
    skipped. Every row of a candidate file is then re-checked against its exact
    as-published ``business_date``: a row whose business_date is absent, blank,
    or not an ISO date can never match (it is never served by a date-range
    query, and never modified). ``date_from > date_to`` is an empty range and
    returns an empty result (not an error); malformed bounds fail closed with
    :class:`QueryError`.

    Results carry the canonical row exactly as stored (``source_values``
    as-published text, non-gating flags, the row's own D05 §8 provenance block)
    plus the Q2 serving envelope; ``raw_line`` is never served. Ordering is the
    established deterministic 5-tuple shared with Q3. Read-only: candidate files
    are streamed and nothing is written.
    """
    _validate_iso_date("date_from", date_from)
    _validate_iso_date("date_to", date_to)
    if date_from > date_to:
        return ()

    candidates = []
    for relative, meta in index.get("files", {}).items():
        lo = meta.get("business_date_min")
        hi = meta.get("business_date_max")
        if lo is None or hi is None:
            continue
        if hi < date_from or lo > date_to:
            continue
        candidates.append(relative)

    results = []
    for relative in sorted(candidates):
        meta = index["files"][relative]
        with open(baseline.path(relative), "r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except ValueError as exc:
                    raise QueryError("query-scan", "unparseable canonical row in %s: %s" % (relative, exc))
                values = obj.get("source_values")
                if not isinstance(values, dict):
                    raise QueryError("query-scan", "canonical row without contract keys in %s" % relative)
                business_date = obj.get("business_date")
                if not isinstance(business_date, str) or not _ISO_DATE_RE.match(business_date):
                    continue
                if not (date_from <= business_date <= date_to):
                    continue
                served = {key: value for key, value in obj.items() if key != "raw_line"}
                served["serving"] = {
                    "query": DATE_RANGE_QUERY_ID,
                    "date_from": date_from,
                    "date_to": date_to,
                    "source_file": relative,
                    "source_file_family": meta.get("family"),
                    "source_file_year": meta.get("year"),
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
    """Diagnostic partition table (raw class-(4) partition data; the product Q1
    query is :func:`query_dataset_summary`, which shapes this data per D16-10)."""
    return dict(index.get("partitions", {}))


def query_dataset_summary(
    index: dict,
    family: Optional[str] = None,
    year: Optional[int] = None,
) -> dict:
    """Q1 dataset/partition selection and yearly summaries (D16-10 Q1).

    Pure derivation over the class-(4) index (a D16-06 derived view): **no
    canonical row is scanned** — the function takes the index document alone
    and never receives a baseline handle.

    Selection: no argument selects all partitions; ``family`` (exact,
    as-published family name) and/or ``year`` (4-digit integer) narrow the
    selection. An unknown selection yields an **empty result** (no partitions,
    zeroed summary), never an error. A missing (``None``) or non-document
    index fails closed with :class:`QueryError`.

    Returns a document shaped for canonical-JSON serving:

    * ``partitions`` — the selected partitions sorted by (family, year), each
      with ``row_files``, ``row_count`` and ``instrument_pairs`` (the union of
      the per-file instrument sets, counted once per partition);
    * ``summary`` — totals over the selection, where ``instrument_pairs`` is
      the union over the selected files (a pair present in two partitions is
      counted once);
    * ``selection`` — the selection that was applied (for the served envelope
      of the result).
    """
    if not isinstance(index, dict):
        raise QueryError("query-input", "index must be the class-(4) index document (serving-index/1.1)")
    if family is not None and not isinstance(family, str):
        raise QueryError("query-input", "family must be a string")
    year_str: Optional[str] = None
    if year is not None:
        if not (isinstance(year, int) and not isinstance(year, bool) and 1000 <= year <= 9999):
            raise QueryError("query-input", "year must be a 4-digit integer")
        year_str = str(year)

    partitions: dict = {}
    for meta in index.get("files", {}).values():
        if family is not None and meta.get("family") != family:
            continue
        if year_str is not None and meta.get("year") != year_str:
            continue
        key = "%s/%s" % (meta.get("family"), meta.get("year"))
        partition = partitions.setdefault(
            key,
            {
                "family": meta.get("family"),
                "year": meta.get("year"),
                "row_files": 0,
                "row_count": 0,
                "instruments": set(),
            },
        )
        partition["row_files"] += 1
        partition["row_count"] += meta.get("row_count", 0)
        partition["instruments"].update(tuple(pair) for pair in meta.get("instruments", []))

    listed = [
        {
            "family": partition["family"],
            "year": partition["year"],
            "row_files": partition["row_files"],
            "row_count": partition["row_count"],
            "instrument_pairs": len(partition["instruments"]),
        }
        for key, partition in sorted(partitions.items())
    ]
    union = set()
    for partition in partitions.values():
        union.update(partition["instruments"])
    return {
        "query": DATASET_QUERY_ID,
        "selection": {"family": family, "year": int(year_str) if year_str is not None else None},
        "partitions": listed,
        "summary": {
            "row_files": sum(partition["row_files"] for partition in listed),
            "row_count": sum(partition["row_count"] for partition in listed),
            "instrument_pairs": len(union),
        },
    }
