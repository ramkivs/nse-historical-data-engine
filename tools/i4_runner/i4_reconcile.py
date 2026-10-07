"""I4 runner reconciliation (RD-4, exactly as authorized: three tiers, no invented gates).

Tier A — AUTHORITATIVE INPUT / EXPECTATION (gating).
    Definition-free facts, directly verifiable from the same corpus bytes: archive SHA-256,
    archive-set identity, one governed archive per expected date, exactly one CSV member,
    member identity, format-family mapping, governed header shape, ``expected_source_date``.

Tier G — GOVERNING CROSS-CHECK (disposition declared per check).
    Comparisons where the same bytes and a governing definition permit an unambiguous
    comparison (e.g. the engine's own recorded member hashes versus the runner's independently
    computed hashes; the D01 header list versus the engine's parsed header view; frozen D03
    evidence versus a recomputation from another frozen artifact). Every mismatch is recorded
    with an explicit ``disposition`` field: ``gating`` or ``non-gating``.

Tier C — DEFINITION-DEPENDENT (non-gating, always recorded).
    ``row_count``, ``bad_rows``, ``isin_count``, ``symbol_count``, ``series_counts`` and the
    other definition-dependent D01 counters. Their definitions are **not governed in-repo**,
    so they are never turned into gates, never "made to match", never given a tolerance and
    never given an expected-divergence list.

Tier E — EVIDENCE-ONLY (non-gating).
    Corroborating observations with no governing counterpart.

Every record identifies: input identity, comparison basis, governing definition (or the
explicit statement that none exists in-repo), result, gating/non-gating disposition, and any
unresolved state. Nothing in this module alters a value produced by the engine.
"""

from __future__ import annotations

import os
import sys

if __package__:
    from . import i4_identity as identity
else:  # direct script execution
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import i4_identity as identity  # type: ignore

from nse_engine import contract  # noqa: E402
from nse_engine.parsing import HEADER_TOLERANCE_TRAILING_EMPTY  # noqa: E402

TIER_A = "A"
TIER_G = "G"
TIER_C = "C"
TIER_E = "E"

GATING = "gating"
NON_GATING = "non-gating"

MATCH = "match"
DIVERGENCE = "divergence"
NOT_COMPARABLE = "not-comparable"
OBSERVED = "observed"

TIER_DESCRIPTION = {
    TIER_A: "authoritative input / expectation (definition-free, verifiable from the same bytes)",
    TIER_G: "governing cross-check (disposition declared per check)",
    TIER_C: "definition-dependent counter (non-gating; D01 definitions are not governed in-repo)",
    TIER_E: "evidence-only observation (non-gating; no governing counterpart)",
}

NOT_GOVERNED_IN_REPO = (
    "D01 counter definition is not governed in this repository (the D01 inventory tool is not "
    "part of the repository); the comparison is recorded, never enforced"
)


def make_record(
    tier: str,
    check: str,
    scope: dict,
    basis: str,
    governing_definition: str,
    expected,
    observed,
    result: str,
    disposition: str,
    unresolved_state=None,
    note: str = "",
) -> dict:
    """One reconciliation record (the schema every tier shares)."""
    return {
        "tier": tier,
        "tier_description": TIER_DESCRIPTION[tier],
        "check": check,
        "input_identity": scope,
        "comparison_basis": basis,
        "governing_definition": governing_definition,
        "expected": expected,
        "observed": observed,
        "delta": _delta(expected, observed),
        "result": result,
        "disposition": disposition,
        "unresolved_state": unresolved_state,
        "note": note,
    }


def _delta(expected, observed):
    if isinstance(expected, int) and isinstance(observed, int) and not isinstance(expected, bool):
        return observed - expected
    return None


def member_scope(record: dict, member_name: str) -> dict:
    return {
        "scope": "member",
        "root": record["root"],
        "relative_path": record["relative_path"],
        "file_name": record["file_name"],
        "member_name": member_name,
        "date_from_filename": record["date_from_filename"],
    }


def corpus_scope(label: str) -> dict:
    return {"scope": "corpus", "label": label}


def gating_failures(records) -> tuple:
    """Records that must abort the run (Tier A divergence, or gating Tier G divergence)."""
    failures = []
    for record in records:
        if record["result"] != DIVERGENCE:
            continue
        if record["tier"] == TIER_A or (
            record["tier"] == TIER_G and record["disposition"] == GATING
        ):
            failures.append(record)
    return tuple(failures)


# ------------------------------------------------------------------ Tier A (gating)


def tier_a_archive_sha256(record: dict, member_name: str, observed_sha256: str) -> dict:
    return make_record(
        TIER_A,
        "archive_sha256_vs_d01",
        member_scope(record, member_name),
        "sha256 of the archive's raw bytes, recomputed at processing time",
        "D01-inventory sha256 (declared basis: archive_sha256_basis=D01-inventory)",
        record["sha256"],
        observed_sha256,
        MATCH if record["sha256"] == observed_sha256 else DIVERGENCE,
        GATING,
        note="detects archive drift between preflight and processing",
    )


def tier_a_family(record: dict, member_name: str, engine_family: str) -> dict:
    expected = _expected_family(record["root"])
    return make_record(
        TIER_A,
        "family_vs_detected_format",
        member_scope(record, member_name),
        "engine family detection on the member bytes vs the governed mapping of the D01 root",
        "D01 root label -> canonical family mapping (nse_engine.evidence_inputs)",
        expected,
        engine_family,
        MATCH if engine_family == expected else DIVERGENCE,
        GATING,
    )


def tier_a_header_shape(record: dict, member_name: str, report: dict) -> dict:
    """Governed header shapes: legacy13 (13 tokens) or legacy13 with the tolerated trailing
    empty 14th token; udiff34 strictly 34 tokens."""
    family = report["format_family"]
    width = report["header_physical_width"]
    tolerance = report["header_tolerance_applied"]
    if family == contract.FAMILY_LEGACY:
        allowed = {(contract.LEGACY_LOGICAL_WIDTH, None),
                   (contract.LEGACY_TOLERATED_PHYSICAL_WIDTH, HEADER_TOLERANCE_TRAILING_EMPTY)}
    elif family == contract.FAMILY_UDIFF:
        allowed = {(contract.UDIFF_WIDTH, None)}
    else:
        allowed = set()
    observed = (width, tolerance)
    return make_record(
        TIER_A,
        "header_shape_governed_variant",
        member_scope(record, member_name),
        "engine-parsed header physical width + applied tolerance vs the governed variants",
        "D05 §7.1 legacy13 (13 logical, tolerated trailing empty 14th); D05 §7.3 udiff34 width 34",
        sorted(str(item) for item in allowed),
        str(observed),
        MATCH if observed in allowed else DIVERGENCE,
        GATING,
    )


def tier_a_member_identity(record: dict, member_name: str) -> dict:
    ok = bool(member_name) and member_name.lower().endswith(".csv")
    return make_record(
        TIER_A,
        "member_identity_single_csv",
        member_scope(record, member_name),
        "member name read verbatim from the ZIP central directory (RD-5; never derived)",
        "one governed CSV member per archive (R1/R2)",
        "exactly one .csv member",
        member_name if ok else "absent",
        MATCH if ok else DIVERGENCE,
        GATING,
    )


def tier_a_expected_source_date(record: dict, member_name: str, source) -> dict:
    """The value actually handed to the engine must be the governed D01 file-date."""
    expected = record["date_from_filename"]
    observed = source.expected_source_date
    return make_record(
        TIER_A,
        "expected_source_date_supplied",
        member_scope(record, member_name),
        "SourceDescriptor.expected_source_date (as constructed) vs D01 date_from_filename",
        "D05 §3.4 file-date mapping (D01) / D05 §7.2 legacy timestamp cross-check",
        expected,
        observed,
        MATCH if observed == expected else DIVERGENCE,
        GATING,
        note="the engine's legacy timestamp tolerance cross-checks against this value",
    )


def tier_a_archive_basis(record: dict, member_name: str, source) -> dict:
    """The archive hash basis handed to the engine must be the declared D01 basis (R3)."""
    expected = "D01-inventory"
    return make_record(
        TIER_A,
        "archive_sha256_basis_declared",
        member_scope(record, member_name),
        "SourceDescriptor.archive_sha256_basis vs the declared governed basis",
        "MD-03 #8 declared hash basis (in-band); R3",
        expected,
        source.archive_sha256_basis,
        MATCH if source.archive_sha256_basis == expected else DIVERGENCE,
        GATING,
        note="and archive_sha256 must equal the D01 value",
    )


def _expected_family(root: str) -> str:
    from nse_engine.evidence_inputs import INVENTORY_ROOT_TO_FAMILY

    return INVENTORY_ROOT_TO_FAMILY[root]


# ------------------------------------------------------------------ Tier G (cross-checks)


def tier_g_engine_member_hashes(
    record: dict, member_name: str, report: dict, runner_raw_sha256: str, runner_size_bytes: int
) -> tuple:
    """The engine's own recorded member identity vs the runner's independent computation.

    Same bytes, same governed functions (D05 §9.2 dual hash) => an unambiguous comparison.
    A mismatch means the bytes were mutated between read and parse, or a defect in one side:
    gating.
    """
    scope = member_scope(record, member_name)
    hash_record = make_record(
        TIER_G,
        "engine_member_sha256_vs_runner",
        scope,
        "nse_engine ParseReport.member_sha256_raw_bytes vs the runner's sha256 of the bytes it read",
        "D05 §9.2 member dual-hash (raw bytes + LF text)",
        runner_raw_sha256,
        report["member_sha256_raw_bytes"],
        MATCH if runner_raw_sha256 == report["member_sha256_raw_bytes"] else DIVERGENCE,
        GATING,
    )
    size_record = make_record(
        TIER_G,
        "engine_member_size_vs_runner",
        scope,
        "nse_engine ParseReport.member_size_bytes vs the runner's observed member size",
        "D05 §9.2 member identity",
        runner_size_bytes,
        report["member_size_bytes"],
        MATCH if runner_size_bytes == report["member_size_bytes"] else DIVERGENCE,
        GATING,
    )
    return hash_record, size_record


def tier_g_d01_header_list(record: dict, member_name: str, report: dict) -> dict:
    """D01 ``headers`` vs the engine's parsed header view (structural, definition-free).

    Divergence is classified **gating**: for a governed corpus the D01 header list and the
    engine's parse of the same bytes agree exactly (verified over all 2,462 records), so a
    disagreement means the inventory or the bytes are not the governed ones.
    """
    logical = 0
    if report["format_family"] == contract.FAMILY_LEGACY:
        logical = contract.LEGACY_LOGICAL_WIDTH
    elif report["format_family"] == contract.FAMILY_UDIFF:
        logical = contract.UDIFF_WIDTH
    d01_headers = list(record["headers"])
    engine_width = report["header_physical_width"]
    ok = (
        len(d01_headers) == engine_width
        and len(d01_headers) >= logical
        and all(entry == "" for entry in d01_headers[logical:])
    )
    return make_record(
        TIER_G,
        "d01_header_list_vs_engine_header_view",
        member_scope(record, member_name),
        "D01 inventory headers list length/consistency vs the engine's parsed physical width",
        "D05 §7 header detection (name-keyed, exact match); D01 baseline header record",
        "len(headers) == engine physical width and any trailing entries empty",
        "len=%d engine_width=%d" % (len(d01_headers), engine_width),
        MATCH if ok else DIVERGENCE,
        GATING,
        note="ungoverned D01 field-splitting conventions are not relied upon; only shape",
    )


def tier_g_verdict_vs_fold(verdict_document: dict, fold: dict, metrics_label: str) -> dict:
    """Frozen D03 definition verdict vs the recomputed fold of the frozen D03 metrics CSV.

    Both sides are governed repository artifacts; the comparison is definition-level, so a
    mismatch is classified **non-gating** (it reports a document/definition state, not a
    corpus data defect).
    """
    recomputed = fold.get("definition_verdict", {})
    fields = ("discriminating_files", "match_distinct_nonblank", "match_nonblank_rows", "verdict")
    expected = {field: verdict_document.get(field) for field in fields}
    observed = {field: recomputed.get(field) for field in fields}
    return make_record(
        TIER_G,
        "d03_definition_verdict_vs_recomputed_fold",
        corpus_scope("d01-definition-verdict"),
        "frozen verdict document vs recomputation from the frozen per-file metrics artifact",
        "D03 frozen evidence (FIX-SEM-DEF-01); D01 definitions not governed in-repo",
        expected,
        observed,
        MATCH if expected == observed else DIVERGENCE,
        NON_GATING,
        unresolved_state=NOT_GOVERNED_IN_REPO,
        note="metrics artifact: %s" % metrics_label,
    )


# ------------------------------------------------------------------ Tier C (non-gating)


def tier_c_member_counters(record: dict, member_name: str, build, report: dict, rows) -> tuple:
    """Definition-dependent D01 counters vs engine-derived values. Never gates."""
    scope = member_scope(record, member_name)
    series_tally = {}
    for row in rows:
        series_tally[row.series] = series_tally.get(row.series, 0) + 1
    isin_values = {row.isin_normalized for row in rows if row.isin_normalized}
    symbol_values = {row.listing_symbol for row in rows if row.listing_symbol}
    records = [
        make_record(
            TIER_C,
            "row_count_vs_data_lines",
            scope,
            "D01 row_count vs ParseReport.data_lines (LF-normalised physical lines minus header)",
            NOT_GOVERNED_IN_REPO,
            int(record["row_count"]),
            report["data_lines"],
            MATCH if int(record["row_count"]) == report["data_lines"] else DIVERGENCE,
            NON_GATING,
            unresolved_state=NOT_GOVERNED_IN_REPO,
        ),
        make_record(
            TIER_C,
            "bad_rows_vs_quarantined",
            scope,
            "D01 bad_rows vs ParseReport.quarantined (the two reason vocabularies differ)",
            NOT_GOVERNED_IN_REPO,
            int(record["bad_rows"]),
            report["quarantined"],
            MATCH if int(record["bad_rows"]) == report["quarantined"] else DIVERGENCE,
            NON_GATING,
            unresolved_state=NOT_GOVERNED_IN_REPO,
        ),
        make_record(
            TIER_C,
            "series_counts_vs_canonical_tally",
            scope,
            "D01 series_counts vs the tally of canonical rows by their series token",
            NOT_GOVERNED_IN_REPO,
            {str(key): int(value) for key, value in dict(record["series_counts"]).items()},
            series_tally,
            MATCH
            if {str(k): int(v) for k, v in dict(record["series_counts"]).items()} == series_tally
            else DIVERGENCE,
            NON_GATING,
            unresolved_state=NOT_GOVERNED_IN_REPO,
        ),
        make_record(
            TIER_C,
            "isin_count_vs_distinct_nonblank_normalised",
            scope,
            "D01 isin_count vs distinct non-blank normalised ISIN values in canonical rows",
            NOT_GOVERNED_IN_REPO,
            int(record["isin_count"]),
            len(isin_values),
            MATCH if int(record["isin_count"]) == len(isin_values) else DIVERGENCE,
            NON_GATING,
            unresolved_state=NOT_GOVERNED_IN_REPO,
            note="D01 verdict evidence (D03) records isin_count as a DISTINCT-NONBLANK reading",
        ),
        make_record(
            TIER_C,
            "symbol_count_vs_distinct_nonblank_symbols",
            scope,
            "D01 symbol_count vs distinct non-blank canonical listing symbols (verbatim)",
            NOT_GOVERNED_IN_REPO,
            int(record["symbol_count"]),
            len(symbol_values),
            MATCH if int(record["symbol_count"]) == len(symbol_values) else DIVERGENCE,
            NON_GATING,
            unresolved_state=NOT_GOVERNED_IN_REPO,
            note="D01 symbol normalisation basis is undeclared; compared verbatim only",
        ),
    ]
    records.append(_tier_c_dates(record, member_name, rows))
    return tuple(records)


def _tier_c_dates(record: dict, member_name: str, rows) -> dict:
    """D01 date_values vs the parsed business-date histogram.

    UDIFF keys are ISO and directly comparable. Legacy keys are raw published text
    (``DD-MON-YYYY``); mapping them would require the parser's own tolerance, so the
    comparison is recorded as **not-comparable** with the reason — no date-text mapping
    rule is invented in the runner (RD-4).
    """
    histogram = {}
    for row in rows:
        histogram[row.business_date] = histogram.get(row.business_date, 0) + 1
    keys = sorted(str(key) for key in dict(record["date_values"]).keys())
    iso_comparable = record["root"] == "UDIFF" and all(
        len(key) == contract.ISO_DATE_LENGTH and key[:4].isdigit() and key[4] == "-" for key in keys
    )
    expected = {str(key): int(value) for key, value in dict(record["date_values"]).items()}
    return make_record(
        TIER_C,
        "date_values_vs_parsed_business_date",
        member_scope(record, member_name),
        "D01 date_values vs the parsed canonical business_date histogram",
        NOT_GOVERNED_IN_REPO,
        expected if iso_comparable else {"raw_keys": keys},
        histogram if iso_comparable else {"parsed_histogram": histogram},
        (MATCH if expected == histogram else DIVERGENCE) if iso_comparable else NOT_COMPARABLE,
        NON_GATING,
        unresolved_state=(
            NOT_GOVERNED_IN_REPO
            if iso_comparable
            else "D01 date keys are raw published text; mapping them would re-implement parser "
            "semantics (no date-text mapping rule is invented)"
        ),
    )


def tier_e_size_corroboration(record: dict, member_name: str, observed_archive_size: int) -> dict:
    return make_record(
        TIER_E,
        "size_bytes_vs_observed_archive_size",
        member_scope(record, member_name),
        "D01 size_bytes (archive size) vs the observed archive size on disk",
        "D01 baseline; redundant given archive_sha256 equality",
        int(record["size_bytes"]),
        observed_archive_size,
        MATCH if int(record["size_bytes"]) == observed_archive_size else DIVERGENCE,
        NON_GATING,
        note="corroboration only; never gates (implied by Tier A archive sha256 equality)",
    )


# ------------------------------------------------------------------ Tier C (corpus level)


def tier_c_corpus_fold(fold: dict, row_metrics: dict, metrics_label: str) -> tuple:
    """Frozen per-file metric evidence fold vs canonical row metrics (level A vs level B).

    Comparable totals are compared; per-file *sums* of distinct counts are recorded as
    not-comparable (a sum of per-file distinct values is not a corpus distinct value).
    """
    totals = fold.get("totals", {})
    values = {
        name: row_metrics.get(name)
        for name in contract.D01_METRIC_NAMES
        if name in row_metrics
    }
    comparable = (
        "rows",
        "blank_symbol_rows",
        "blank_isin_rows",
        "nonblank_isin_rows",
        "isins_extra_duplicate_rows",
        "symbol_series_duplicate_rows",
    )
    records = []
    for field in comparable:
        if field not in totals or field not in values:
            continue
        records.append(
            make_record(
                TIER_C,
                "corpus_metric_%s_fold_vs_rows" % field,
                corpus_scope("d01-metric-fold"),
                "frozen D01 per-file metrics fold (level B) vs canonical row metrics (level A)",
                NOT_GOVERNED_IN_REPO,
                int(totals[field]),
                int(values[field]),
                MATCH if int(totals[field]) == int(values[field]) else DIVERGENCE,
                NON_GATING,
                unresolved_state=NOT_GOVERNED_IN_REPO,
                note="metrics artifact: %s" % metrics_label,
            )
        )
    records.append(
        make_record(
            TIER_C,
            "corpus_distinct_metrics_not_comparable",
            corpus_scope("d01-metric-fold"),
            "per-file distinct-count sums vs corpus-level distinct counts",
            NOT_GOVERNED_IN_REPO,
            {
                "distinct_nonblank_isin_sum": totals.get("distinct_nonblank_isin_sum"),
                "distinct_nonblank_symbol_sum": totals.get("distinct_nonblank_symbol_sum"),
                "distinct_symbol_series_pairs_sum": totals.get("distinct_symbol_series_pairs_sum"),
            },
            {
                "distinct_nonblank_isin": values.get("distinct_nonblank_isin"),
                "distinct_nonblank_symbol": values.get("distinct_nonblank_symbol"),
                "distinct_symbol_series_pairs": values.get("distinct_symbol_series_pairs"),
            },
            NOT_COMPARABLE,
            NON_GATING,
            unresolved_state="sum of per-file distinct values is not a corpus distinct value",
        )
    )
    return tuple(records)


def flag_census(rows) -> dict:
    """Observed flag census (evidence only; no gating, no D01 counterpart asserted)."""
    counts = {}
    for row in rows:
        for name in row.flag_names():
            counts[name] = counts.get(name, 0) + 1
    return {name: counts[name] for name in sorted(counts)}


def governance_dependency_census(rows) -> dict:
    counts = {}
    for row in rows:
        for dependency_id in row.governance_dependencies:
            counts[dependency_id] = counts.get(dependency_id, 0) + 1
    return {name: counts[name] for name in sorted(counts)}


def summarize(records) -> dict:
    """Deterministic summary of a reconciliation record set."""
    by_tier = {}
    by_result = {}
    gating_divergences = {}
    for record in records:
        by_tier[record["tier"]] = by_tier.get(record["tier"], 0) + 1
        by_result[record["result"]] = by_result.get(record["result"], 0) + 1
    for record in gating_failures(records):
        gating_divergences[record["check"]] = gating_divergences.get(record["check"], 0) + 1
    return {
        "records": len(records),
        "by_tier": {key: by_tier[key] for key in sorted(by_tier)},
        "by_result": {key: by_result[key] for key in sorted(by_result)},
        "gating_divergences": {key: gating_divergences[key] for key in sorted(gating_divergences)},
        "gating_divergence_count": sum(gating_divergences.values()),
    }
