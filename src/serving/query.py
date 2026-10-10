"""Serving query surface (D16-10) — the slice's query categories.

Q1 dataset/partition selection + yearly summaries, Q2 date-range query, Q3
instrument query, Q4 exact-value filters, and Q5 identity/association queries.
Semantics of Q3, verified against the governing contract
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
import os
import re
from typing import Optional, Tuple

from .baseline import Baseline, BaselineError
from .index import ServingIndexError

QUERY_ID = "Q3-instrument"
DATASET_QUERY_ID = "Q1-dataset"
DATE_RANGE_QUERY_ID = "Q2-date-range"
FILTER_QUERY_ID = "Q4-filter"
ASSOCIATIONS_QUERY_ID = "Q5-association"

#: Q5's single source: the class-(2) W2 derived output the runner writes from the
#: engine's identity stream (one SecurityIdentity document per line, in the engine's
#: sorted normalized-ISIN key order). Already a recognized durability-class pattern
#: in ``serving.baseline``; verified at open by verify-02/verify-03.
ASSOCIATIONS_FILE = "w2/associations.jsonl"

# ---------------------------------------------------------------------------
# Pinned schema for Q5's source (D05 §3.2/§3.3; nse_engine.identity
# ``SecurityIdentity.to_dict()`` / ``DatedAssociation.to_dict()`` /
# ``Provenance.to_dict()``). Literals, with the contract citation: the serving
# layer does not import nse_engine (D24 boundary). Malformed present data
# fails closed against exactly these sets — a schema drift is a contract
# violation, never silently absorbed.
IDENTITY_DOC_KEYS = frozenset(
    (
        "associations",  # [DatedAssociation] — the dated-association intervals
        "first_observed",  # ISO business date (min over the identity's keyed observations)
        "identity_basis",  # "isin_correlation_key_upper_trim" (D05 §6.1 [ADOPTED])
        "is_valid_isin_format",  # true only when every observation is VALID; else null
        "isin_list",  # list of as-published ISIN strings (normally one)
        "last_observed",  # ISO business date (max)
        "non_promotion_note",  # D05 §3.2 NON-ASSUMPTION standing note
        "observations",  # governed census facts (str -> str)
        "provenance",  # [D05 §8 provenance block]
        "security_id",  # the D05 §6.1 correlation key (normalized ISIN; NOT identity)
    )
)
ASSOCIATION_ENTRY_KEYS = frozenset(
    (
        "association_type",  # present set: corpus-observed only (others DEC-1-deferred)
        "contributing_rows",  # [{business_date, line_number, member_name}]
        "interval_basis",  # "observed-range" (observed first/last presence, NOT validity)
        "observations",  # str -> str
        "observed_from",  # ISO business date
        "observed_to",  # ISO business date
        "provenance",  # [D05 §8 provenance block]
        "security_id",  # must equal the containing identity's security_id
        "series",
        "symbol",
    )
)
PROVENANCE_BLOCK_KEYS = frozenset(
    (
        "archive_sha256",
        "archive_sha256_basis",
        "evidence_refs",
        "format_family",
        "member_name",
        "member_sha256_lf_text",
        "member_sha256_raw_bytes",
        "run_id",
        "source_archive",
        "spec_version",
        "tool_name",
        "tool_sha256",
        "tool_version",
    )
)
CONTRIBUTING_ROW_KEYS = frozenset(("business_date", "line_number", "member_name"))
IDENTITY_KEY_BASIS = "isin_correlation_key_upper_trim"  # D05 §6.1 adopted basis
INTERVAL_BASIS_OBSERVED_RANGE = "observed-range"  # D05 §3.3
#: D05 §3.3: "Only the first exists today." master-snapshot / etf-register-membership
#: are DEC-1-deferred; a document carrying either is a contract violation here.
ASSOCIATION_TYPES_PRESENT = ("corpus-observed",)

#: Q4's filterable fields, pinned by the D05 §3.1 field table (as-published
#: values only; D05 NON-ASSUMPTION: descriptive attributes are never used for
#: inferred type semantics — exact stored-value equality only):
#: * ``series`` — present in both format families (D05 §3.1 "string, always");
#: * ``segment`` (``Sgmt``), ``source`` (``Src``), ``instrument_type``
#:   (``FinInstrmTp``) — UDiFF-only descriptive attributes; on legacy rows the
#:   values are absent (``None``) and can never match any requested value.
#: No other field is a Q4 filter: a requested name outside this tuple fails
#: closed (no undocumented aliases, no synonyms).
Q4_FILTER_FIELDS = ("series", "segment", "source", "instrument_type")

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
    stored in the class-(4) index (serving-index/1.2); a file whose bounds are
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


def query_filters(
    baseline: Baseline,
    index: dict,
    filters: dict,
) -> Tuple[dict, ...]:
    """Q4 segment / market-type / series / trading-status filtering
    (D16-10 Q4: "as-published field values").

    ``filters`` maps one or more of :data:`Q4_FILTER_FIELDS` to the exact
    as-published value to match. Semantics, per the governing contract
    (D16-10 Q4; D05 §3.1; D22 §5 E1; D23 §10):

    * **exact-value equality only** — no normalisation, translation, case or
      whitespace folding, and no expression language; the requested value must
      be a string (the empty string matches exactly-blank stored values);
    * **absent never matches** — a row whose field value is absent (``None``,
      the legacy family for the UDiFF-only fields) can never match any
      requested value, including the empty string;
    * **AND semantics** — a row is served only when every requested field
      matches exactly (the single contract-supported composition);
    * **format-family handling** — ``series`` is checked on every row of both
      families; ``segment``/``source``/``instrument_type`` match only where
      the family stores them (UDiff), by the same absent-never-matches rule.

    There is no per-field index census, so every row file is a candidate and
    each row is re-checked against its exact as-published values (the index
    supplies the file set only — no index extension is required, and the
    deterministic rebuild/stale-index behavior is untouched). Malformed
    requests (non-dict, empty, unknown field, non-string value) fail closed
    with :class:`QueryError` before any row is served. Results carry the
    canonical row exactly as stored (``raw_line`` never served) plus the Q4
    serving envelope; ordering is the established deterministic 5-tuple
    shared with Q2/Q3. Read-only: files are streamed, nothing is written.
    """
    if not isinstance(filters, dict):
        raise QueryError("query-input", "filters must be a mapping of Q4 field -> exact value")
    if not filters:
        raise QueryError("query-input", "Q4 requires at least one filter (an unfiltered scan is not a Q4 request)")
    for field in filters:
        if field not in Q4_FILTER_FIELDS:
            raise QueryError(
                "query-input",
                "unknown Q4 filter field %r (supported: %s)" % (field, ", ".join(Q4_FILTER_FIELDS)),
            )
    for field, value in filters.items():
        if not isinstance(value, str):
            raise QueryError("query-input", "Q4 filter value for %r must be a string (as-published value), got %r" % (field, value))

    results = []
    for relative in sorted(index.get("files", {})):
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
                if any(values.get(field) != value for field, value in filters.items()):
                    continue
                served = {key: value for key, value in obj.items() if key != "raw_line"}
                served["serving"] = {
                    "query": FILTER_QUERY_ID,
                    "filters": dict(filters),
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


def _require_iso_date_in_scan(value: object, context: str) -> None:
    """ISO business-date check under the associations-scan check id (a malformed
    present record is a scan failure, not a request-input failure)."""
    if not isinstance(value, str) or not _ISO_DATE_RE.match(value):
        raise QueryError("associations-scan", "field must be an ISO business date (YYYY-MM-DD), got %r in %s" % (value, context))
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        raise QueryError("associations-scan", "field is not a valid calendar date: %r in %s" % (value, context))


def _validate_provenance_block(block: object, context: str) -> None:
    if not isinstance(block, dict) or set(block) != PROVENANCE_BLOCK_KEYS:
        raise QueryError("associations-scan", "provenance block with a non-contract key set in %s" % context)
    for name in ("archive_sha256_basis", "format_family", "member_name", "source_archive", "spec_version", "tool_name", "tool_sha256", "tool_version"):
        if not isinstance(block.get(name), str):
            raise QueryError("associations-scan", "provenance block field %r must be a string in %s" % (name, context))
    if block.get("archive_sha256") is not None and not isinstance(block["archive_sha256"], str):
        raise QueryError("associations-scan", "provenance field archive_sha256 must be null or a string in %s" % context)
    if block.get("run_id") is not None and not isinstance(block["run_id"], str):
        raise QueryError("associations-scan", "provenance field run_id must be null or a string in %s" % context)
    refs = block.get("evidence_refs")
    if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
        raise QueryError("associations-scan", "provenance field evidence_refs must be a list of strings in %s" % context)


def _validate_association_entry(entry: object, context: str, parent_key: str) -> None:
    if not isinstance(entry, dict) or set(entry) != ASSOCIATION_ENTRY_KEYS:
        raise QueryError("associations-scan", "dated-association entry with a non-contract key set in %s" % context)
    for name in ("association_type", "interval_basis", "series", "symbol"):
        if not isinstance(entry.get(name), str):
            raise QueryError("associations-scan", "dated-association field %r must be a string in %s" % (name, context))
    security_id = entry.get("security_id")
    if not isinstance(security_id, str) or not security_id:
        raise QueryError("associations-scan", "dated-association field security_id must be a non-empty string in %s" % context)
    if security_id != parent_key:
        raise QueryError(
            "associations-scan",
            "dated-association for identity %r belongs to a different identity %r in %s" % (security_id, parent_key, context),
        )
    if entry["association_type"] not in ASSOCIATION_TYPES_PRESENT:
        raise QueryError(
            "associations-scan",
            "dated-association carries association_type %r outside the present set %s in %s"
            % (entry["association_type"], "/".join(ASSOCIATION_TYPES_PRESENT), context),
        )
    if entry["interval_basis"] != INTERVAL_BASIS_OBSERVED_RANGE:
        raise QueryError(
            "associations-scan",
            "dated-association carries interval_basis %r (the contract pins %r) in %s"
            % (entry["interval_basis"], INTERVAL_BASIS_OBSERVED_RANGE, context),
        )
    for name in ("observed_from", "observed_to"):
        _require_iso_date_in_scan(entry.get(name), "%s.%s" % (context, name))
    rows = entry.get("contributing_rows")
    if not isinstance(rows, list):
        raise QueryError("associations-scan", "dated-association field contributing_rows must be a list in %s" % context)
    for row in rows:
        if not isinstance(row, dict) or set(row) != CONTRIBUTING_ROW_KEYS:
            raise QueryError("associations-scan", "contributing row with a non-contract key set in %s" % context)
        _require_iso_date_in_scan(row.get("business_date"), "%s.contributing_rows.business_date" % context)
        if not isinstance(row.get("line_number"), int) or isinstance(row["line_number"], bool):
            raise QueryError("associations-scan", "contributing row line_number must be an integer in %s" % context)
        if not isinstance(row.get("member_name"), str):
            raise QueryError("associations-scan", "contributing row member_name must be a string in %s" % context)
    observations = entry.get("observations")
    if not isinstance(observations, dict) or any(
        not isinstance(key, str) or not isinstance(value, str) for key, value in observations.items()
    ):
        raise QueryError("associations-scan", "dated-association observations must map strings to strings in %s" % context)
    provenance = entry.get("provenance")
    if not isinstance(provenance, list):
        raise QueryError("associations-scan", "dated-association field provenance must be a list in %s" % context)
    for block in provenance:
        _validate_provenance_block(block, context)


def _validate_identity_document(doc: object, context: str) -> str:
    if not isinstance(doc, dict) or set(doc) != IDENTITY_DOC_KEYS:
        raise QueryError("associations-scan", "identity document with a non-contract key set in %s" % context)
    security_id = doc.get("security_id")
    if not isinstance(security_id, str) or not security_id:
        raise QueryError("associations-scan", "identity document field security_id must be a non-empty string in %s" % context)
    if doc.get("identity_basis") != IDENTITY_KEY_BASIS:
        raise QueryError(
            "associations-scan",
            "identity document carries identity_basis %r (the contract pins %r) in %s"
            % (doc.get("identity_basis"), IDENTITY_KEY_BASIS, context),
        )
    if doc.get("is_valid_isin_format") not in (True, None):
        raise QueryError(
            "associations-scan",
            "identity document field is_valid_isin_format must be true or null (never asserted false) in %s" % context,
        )
    isin_list = doc.get("isin_list")
    if not isinstance(isin_list, list) or not isin_list or any(not isinstance(isin, str) for isin in isin_list):
        raise QueryError("associations-scan", "identity document field isin_list must be a non-empty list of strings in %s" % context)
    _require_iso_date_in_scan(doc.get("first_observed"), "%s.first_observed" % context)
    _require_iso_date_in_scan(doc.get("last_observed"), "%s.last_observed" % context)
    if not isinstance(doc.get("non_promotion_note"), str):
        raise QueryError("associations-scan", "identity document field non_promotion_note must be a string in %s" % context)
    observations = doc.get("observations")
    if not isinstance(observations, dict) or any(
        not isinstance(key, str) or not isinstance(value, str) for key, value in observations.items()
    ):
        raise QueryError("associations-scan", "identity document observations must map strings to strings in %s" % context)
    provenance = doc.get("provenance")
    if not isinstance(provenance, list):
        raise QueryError("associations-scan", "identity document field provenance must be a list in %s" % context)
    for block in provenance:
        _validate_provenance_block(block, context)
    associations = doc.get("associations")
    if not isinstance(associations, list):
        raise QueryError("associations-scan", "identity document field associations must be a list in %s" % context)
    for entry in associations:
        _validate_association_entry(entry, context, security_id)
    return security_id


def parse_associations(baseline: Baseline) -> Optional[list]:
    """Parse ``w2/associations.jsonl`` (class-(2) W2 output) or report it absent.

    Returns ``None`` when the file is **absent** — a legitimate package state
    (no derived identities; served as explicitly absent, never fabricated,
    never an error). Returns a list of ``(line_number, document)`` pairs, in
    file order, when the file is present. A **present** file that is malformed
    fails closed with ``QueryError("associations-scan")`` — including a
    non-object line, a non-contract key set, a non-ISO interval bound, an
    association_type outside the present set, an association belonging to a
    different identity, or a duplicate ``security_id`` (the engine emits
    exactly one document per active key, sorted; a repeat is corruption).
    Read-only: the file is streamed and nothing is written.
    """
    path = baseline.path(ASSOCIATIONS_FILE)
    if not os.path.exists(path):
        return None
    documents = []
    seen = set()
    with open(path, "r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            context = "%s line %d" % (ASSOCIATIONS_FILE, line_number)
            try:
                doc = json.loads(line)
            except ValueError as exc:
                raise QueryError("associations-scan", "unparseable identity document in %s: %s" % (context, exc))
            security_id = _validate_identity_document(doc, context)
            if security_id in seen:
                raise QueryError(
                    "associations-scan",
                    "duplicate identity document for security_id %r in %s (the engine emits one document per key)" % (security_id, context),
                )
            seen.add(security_id)
            documents.append((line_number, doc))
    return documents


_UNPARSE = object()  # sentinel: documents not supplied by the caller


def query_associations(
    baseline: Baseline,
    index: dict,
    security_id: Optional[str] = None,
    symbol: Optional[str] = None,
    series: Optional[str] = None,
    documents: object = _UNPARSE,
) -> Tuple[dict, ...]:
    """Q5 identity/association query (D16-10 Q5: "related records" = the
    instrument's dated-association intervals; no overlay aggregation — D05).

    Two governed selector forms over ``w2/associations.jsonl`` (the class-(2)
    W2 output; D05 §3.2/§3.3), plus their composition:

    * **identity** — ``security_id`` only: the identity document for that exact
      as-published correlation key (normalized ISIN; D05 §6.1) with all of its
      dated-association intervals as published;
    * **instrument** — ``symbol`` **and** ``series`` (both, exact as-published
      strings): every dated-association interval in every identity document
      whose (symbol, series) matches exactly — the instrument's "related
      records", across identities;
    * **combined** — all three: that identity's intervals restricted to the
      (symbol, series) pair (the single contract-supported composition).

    Semantics, per the governing contract (D05 §3.2/§3.3/§3.5; D16-10 Q5;
    D23 §8/§10):

    * **exact-value matching only** — selectors are compared verbatim to the
      as-published stored values (the engine already normalized the key; no
      case/whitespace folding, no expression language, no aliasing or
      inference of relationships);
    * **absent is never an error** — a missing ``w2/associations.jsonl``, an
      unknown identity, or an unknown instrument all yield an empty result
      (served with ``associations_present`` at the CLI level);
    * **as-published serving** — the document is served exactly as stored
      (its 10-key ``SecurityIdentity`` / 10-key ``DatedAssociation`` shape,
      including ``is_valid_isin_format: null`` where undetermined and the
      non-promotion note) plus the Q5 ``serving`` envelope;
    * **overlay rows appear in no document** (the engine excludes them at
      ingestion, D05 §3.5) — Q5 neither aggregates nor exposes overlay
      observations;
    * **ordering is file order** — the engine's sorted normalized-ISIN key
      order with published association order within each document; never
      re-sorted;
    * **fail closed** — malformed selectors or a malformed present file raise
      :class:`QueryError` before anything is served (no partial output).

    ``index`` is accepted for boundary consistency (every Q path takes the
    verified class-(4) index) but supplies no Q5 file narrowing: Q5's file
    set is fixed (the single class-(2) file) and the index format is
    unchanged. ``documents`` may carry a result already returned by
    :func:`parse_associations` (the CLI does so to serve the
    ``associations_present`` marker from the same single pass); omitted
    callers get the parse performed here. Read-only: the file is streamed
    and nothing is written.
    """
    if security_id is not None and not isinstance(security_id, str):
        raise QueryError("query-input", "security_id must be a string (exact as-published correlation key)")
    for label, value in (("symbol", symbol), ("series", series)):
        if value is not None and not isinstance(value, str):
            raise QueryError("query-input", "%s must be a string (exact as-published value)" % label)
    if (symbol is None) != (series is None):
        raise QueryError(
            "query-input", "the Q5 instrument selector requires both symbol and series (an ordered pair; a single field is not a selector)"
        )
    if security_id is None and symbol is None:
        raise QueryError(
            "query-input",
            "Q5 requires at least one selector: security_id, or symbol and series",
        )

    if documents is _UNPARSE:
        documents = parse_associations(baseline)
    if documents is None:
        return ()

    results = []
    for line_number, doc in documents:
        if security_id is not None and doc["security_id"] != security_id:
            continue
        if symbol is not None:
            for entry in doc["associations"]:
                if entry["symbol"] != symbol or entry["series"] != series:
                    continue
                served = dict(entry)
                served["serving"] = {
                    "query": ASSOCIATIONS_QUERY_ID,
                    "security_id": doc["security_id"],
                    "series": series,
                    "source_file": ASSOCIATIONS_FILE,
                    "source_line_number": line_number,
                    "symbol": symbol,
                }
                results.append(served)
        else:
            served = dict(doc)
            served["serving"] = {
                "query": ASSOCIATIONS_QUERY_ID,
                "security_id": security_id,
                "source_file": ASSOCIATIONS_FILE,
                "source_line_number": line_number,
            }
            results.append(served)
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
        raise QueryError("query-input", "index must be the class-(4) index document (serving-index/1.2)")
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
