"""I4 runner preflight (RD-4 Tier A / gating Tier G) — every gate fails closed.

The preflight establishes, before any canonical output is written, that:

* the engine and runner bytes are the declared ones (identity binding, RD-3);
* the runner contains no clock, randomness, environment or network usage (RD-8/RD-10/RD-7);
* the corpus roots exist, are distinct from the output root, and are readable;
* the output root is new or empty, is not inside a corpus root, and has declared capacity;
* the governed D01 inventory loads, satisfies its record contract, is internally consistent
  and agrees with its companion summary document;
* the declared governed evidence inputs are present and hash-declared;
* the discovered corpus archive set equals the inventory set in **both** directions, with no
  duplicate checksums and no duplicate file dates;
* every archive's bytes hash to the D01 value, every archive opens, and every archive
  contains exactly one governed ``.csv`` member (read verbatim, RD-5).

On any gating failure the run aborts and the records collected so far are retained as failure
evidence (RD-9). No clock, no environment value and no filesystem state beyond the declared
inputs enters any comparison.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from dataclasses import dataclass, field

if __package__:
    from . import i4_identity as identity
    from . import i4_inputs as inputs
else:  # direct script execution
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import i4_identity as identity  # type: ignore
    import i4_inputs as inputs  # type: ignore

from nse_engine import contract  # noqa: E402

if __package__:
    from . import i4_reconcile as reconcile
else:  # direct script execution
    import i4_reconcile as reconcile  # type: ignore

RUN_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")

#: Source-level guarantees (RD-8 / RD-10 / RD-7). Tokens are assembled from fragments so this
#: very check does not trip on its own literals; only the declared runner modules are scanned.
FORBIDDEN_SOURCE_TOKENS = (
    "datetime" + ".now",
    "datetime" + ".utcnow",
    "datetime" + ".today",
    "time" + ".time(",
    "time" + ".monotonic",
    "time" + ".localtime",
    "time" + ".strftime",
    "uuid" + ".uuid",
    "random" + ".random",
    "random" + ".choice",
    "os" + ".environ",
    "os" + ".getenv",
    "getpass" + ".",
    "platform" + ".node",
    "gethostname" + "(",
    "os" + ".getpid",
)


@dataclass(frozen=True)
class RunDeclaration:
    """Everything a run declares. Paths are operator inputs; none is written into evidence."""

    repo_root: str
    legacy_root: str
    udiff_root: str
    out: str
    run_id: str
    inventory: str
    labels: str = ""
    d01_metrics: str = ""
    d01_verdict: str = ""
    series_universe: str = ""
    series_rollup: str = ""
    expect_records: int = 0
    expect_inventory_lf_sha256: str = ""
    expect_tool_fingerprint: str = ""
    expect_runner_fingerprint: str = ""
    min_free_bytes: int = 0


@dataclass(frozen=True)
class PreflightOutcome:
    records: tuple
    archives: tuple
    inventory_records: tuple
    inventory_index: dict
    governed_input_facts: tuple
    present_inputs: dict = field(default_factory=dict)
    archive_pairs: tuple = ()
    member_names: dict = field(default_factory=dict)
    identity: dict = field(default_factory=dict)


def _record(
    check_id: str,
    tier: str,
    result: str,
    disposition: str,
    expected,
    observed,
    basis: str,
    governing_definition: str,
    note: str = "",
) -> dict:
    return {
        "check_id": check_id,
        "tier": tier,
        "tier_description": reconcile.TIER_DESCRIPTION[tier],
        "result": result,
        "disposition": disposition,
        "expected": expected,
        "observed": observed,
        "comparison_basis": basis,
        "governing_definition": governing_definition,
        "note": note,
    }


def _fail(records, record: dict, message: str):
    exc = inputs.PreflightFailure(message)
    exc.records = tuple(records + [record])
    exc.record = record
    return exc


def source_token_hits(directory: str = None) -> tuple:
    """Declared runner modules scanned for clock / randomness / environment usage."""
    hits = []
    for name in sorted(identity.RUNNER_MODULES):
        path = identity.module_file(directory or identity.MODULE_DIR, name)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as handle:
            text = handle.read().decode("utf-8", "replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for token in FORBIDDEN_SOURCE_TOKENS:
                if token in line:
                    hits.append((name, line_number, token))
    return tuple(hits)


def run_preflight(declaration: RunDeclaration) -> PreflightOutcome:
    records = []

    # ---------------------------------------------------------------- phase 1: declarations
    if not RUN_ID_RE.match(declaration.run_id or ""):
        record = _record(
            "PF-00", reconcile.TIER_A, reconcile.DIVERGENCE, reconcile.GATING,
            "run_id matching ^[A-Za-z0-9._:-]{1,64}$", declaration.run_id or "",
            "declared run_id format (RD-10: required, explicit, clock-free)",
            "RD-10 (accepted)",
        )
        raise _fail(records, record, "run_id is missing or malformed: %r" % declaration.run_id)
    records.append(
        _record(
            "PF-00", reconcile.TIER_A, reconcile.MATCH, reconcile.GATING,
            "run_id matching ^[A-Za-z0-9._:-]{1,64}$", declaration.run_id,
            "declared run_id format (RD-10: required, explicit, clock-free)",
            "RD-10 (accepted)",
        )
    )

    if not os.path.isdir(declaration.repo_root):
        raise inputs.PreflightFailure("repo root is not a directory: %s" % declaration.repo_root)
    src_dir = os.path.join(declaration.repo_root, "src")
    if not os.path.isdir(src_dir):
        raise inputs.PreflightFailure("repo root has no src/ package: %s" % declaration.repo_root)

    # PF-01 engine identity (gating Tier G: the engine bytes must be the declared ones)
    engine_fingerprint = identity.engine_fingerprint()
    engine_ok = True
    if declaration.expect_tool_fingerprint:
        engine_ok = engine_fingerprint == declaration.expect_tool_fingerprint
    record = _record(
        "PF-01", reconcile.TIER_G, reconcile.MATCH if engine_ok else reconcile.DIVERGENCE,
        reconcile.GATING,
        declaration.expect_tool_fingerprint or "(not declared)",
        engine_fingerprint,
        "nse_engine.provenance.tool_fingerprint() over contract.ENGINE_MODULES bytes",
        "D05 §9 tool identity; RD-3 composite identity",
        note="engine modules are fingerprinted; a CRLF-converted or edited engine is detected here",
    )
    records.append(record)
    if not engine_ok:
        raise _fail(records, record, "engine fingerprint does not match the declared value")

    # PF-02 runner identity
    runner_fingerprint = identity.runner_fingerprint()
    runner_ok = True
    if declaration.expect_runner_fingerprint:
        runner_ok = runner_fingerprint == declaration.expect_runner_fingerprint
    record = _record(
        "PF-02", reconcile.TIER_G, reconcile.MATCH if runner_ok else reconcile.DIVERGENCE,
        reconcile.GATING,
        declaration.expect_runner_fingerprint or "(not declared)",
        runner_fingerprint,
        "runner_fingerprint() over RUNNER_MODULES bytes (engine construction)",
        "RD-3 (accepted)",
    )
    records.append(record)
    if not runner_ok:
        raise _fail(records, record, "runner fingerprint does not match the declared value")

    # PF-03 runner source guarantees
    token_hits = source_token_hits()
    import_hits = identity.forbidden_import_hits()
    record = _record(
        "PF-03", reconcile.TIER_G,
        reconcile.MATCH if not token_hits and not import_hits else reconcile.DIVERGENCE,
        reconcile.GATING,
        "no clock/randomness/environment token and no network import in RUNNER_MODULES",
        {"token_hits": [list(hit) for hit in token_hits], "import_hits": [list(hit) for hit in import_hits]},
        "source scan of the declared runner modules",
        "RD-8 clock-free package; RD-10 clock-free run_id; RD-7 no network/storage service",
    )
    records.append(record)
    if record["result"] != reconcile.MATCH:
        raise _fail(records, record, "runner source uses a forbidden token or network import")

    # PF-04 corpus roots / output root placement
    problems = []
    for label in inputs.ROOT_LABELS:
        root_path = declaration.legacy_root if label == "LEGACY" else declaration.udiff_root
        if not root_path or not os.path.isdir(root_path):
            problems.append("%s root is not a directory: %r" % (label, root_path))
        elif not os.access(root_path, os.R_OK):
            problems.append("%s root is not readable: %r" % (label, root_path))
    problems.extend(output_placement_problems(declaration))
    record = _record(
        "PF-04", reconcile.TIER_A, reconcile.MATCH if not problems else reconcile.DIVERGENCE,
        reconcile.GATING,
        "two distinct readable corpus roots; output root outside both",
        problems or "ok",
        "declared path structure (read-only corpus custody)",
        "D03 read-only guarantee; RD-7 run-scoped output outside the corpus",
    )
    records.append(record)
    if problems:
        raise _fail(records, record, "; ".join(problems))

    # PF-05 inventory loads and satisfies declared expectations
    inventory_records = inputs.load_inventory(declaration.inventory)
    inventory_facts = inputs.file_facts(declaration.inventory)
    problems = []
    if declaration.expect_records and len(inventory_records) != declaration.expect_records:
        problems.append(
            "inventory record count %d != declared expectation %d"
            % (len(inventory_records), declaration.expect_records)
        )
    if (
        declaration.expect_inventory_lf_sha256
        and inventory_facts["lf_sha256"] != declaration.expect_inventory_lf_sha256
    ):
        problems.append("inventory LF sha256 does not match the declared expectation")
    record = _record(
        "PF-05", reconcile.TIER_A, reconcile.MATCH if not problems else reconcile.DIVERGENCE,
        reconcile.GATING,
        {
            "records": declaration.expect_records or "(not declared)",
            "lf_sha256": declaration.expect_inventory_lf_sha256 or "(not declared)",
        },
        {"records": len(inventory_records), **inventory_facts},
        "declared expectations vs the governed inventory document (LF-text basis)",
        "D01 baseline; MD-03 #8 declared hash basis",
    )
    records.append(record)
    if problems:
        raise _fail(records, record, "; ".join(problems))

    inventory_index = inputs.inventory_index(inventory_records)

    # PF-06 inventory summary document cross-check (gating Tier G, document consistency)
    summary = inputs.load_inventory_summary(declaration.inventory)
    if summary:
        by_root = {}
        for item in inventory_records:
            by_root[item["root"]] = by_root.get(item["root"], 0) + 1
        dates = [item["date_from_filename"] for item in inventory_records]
        checksums = [item["sha256"] for item in inventory_records]
        derived = {
            "file_count": len(inventory_records),
            "by_root": by_root,
            "duplicate_checksum_count": len(checksums) - len(set(checksums)),
            "duplicate_date_count": len(dates) - len(set(dates)),
            "first_file_date": min(dates),
            "last_file_date": max(dates),
            "schema_variant_count": len({item["header_signature"] for item in inventory_records}),
        }
        mismatch = {
            key: {"summary": summary.get(key), "derived": derived[key]}
            for key in sorted(derived)
            if key in summary and summary.get(key) != derived[key]
        }
        record = _record(
            "PF-06", reconcile.TIER_G,
            reconcile.MATCH if not mismatch else reconcile.DIVERGENCE, reconcile.GATING,
            derived, {key: summary.get(key) for key in sorted(derived) if key in summary},
            "companion inventory_summary.json vs facts derived from the inventory records",
            "D01 baseline document consistency",
            note="a stale or inconsistent inventory invalidates the run premise",
        )
        records.append(record)
        if mismatch:
            raise _fail(records, record, "inventory summary disagrees with the inventory records")

    # PF-07 inventory internal consistency (per record)
    inconsistent = []
    for item in inventory_records:
        date_values_total = sum(int(value) for value in item["date_values"].values())
        series_total = sum(int(value) for value in item["series_counts"].values())
        if date_values_total != int(item["row_count"]) or series_total != int(item["row_count"]):
            inconsistent.append(
                {
                    "file_name": item["file_name"],
                    "row_count": item["row_count"],
                    "date_values_total": date_values_total,
                    "series_counts_total": series_total,
                }
            )
    record = _record(
        "PF-07", reconcile.TIER_G,
        reconcile.MATCH if not inconsistent else reconcile.DIVERGENCE, reconcile.GATING,
        "sum(date_values) == row_count and sum(series_counts) == row_count for every record",
        inconsistent[:10] if inconsistent else "consistent for all %d records" % len(inventory_records),
        "inventory record self-consistency",
        "D01 baseline document consistency",
    )
    records.append(record)
    if inconsistent:
        raise _fail(records, record, "inventory records are internally inconsistent")

    # PF-08 governed evidence inputs present when declared
    declared_inputs = (
        ("calendar_labels", declaration.labels, "governed calendar labels (DEC2_CAL_LABELS.json)"),
        ("d01_metric_evidence", declaration.d01_metrics, "frozen per-file D01 metric evidence"),
        ("d01_definition_verdict", declaration.d01_verdict, "frozen D01 definition verdict"),
        ("series_universe", declaration.series_universe, "D02 series universe evidence"),
        ("series_class_rollup", declaration.series_rollup, "D02 series class rollup evidence"),
    )
    governed_input_facts = [
        inputs.governed_input_fact(
            "d01_inventory",
            _path_label(declaration.repo_root, declaration.inventory),
            declaration.inventory,
            True,
        )
    ]
    missing = []
    present_inputs = {}
    for role, path, label in declared_inputs:
        if not path:
            governed_input_facts.append(
                inputs.governed_input_fact(role, "(not declared)", "", False)
            )
            present_inputs[role] = False
            continue
        if not os.path.isfile(path):
            missing.append("%s: %s" % (label, path))
            present_inputs[role] = False
            continue
        present_inputs[role] = True
        governed_input_facts.append(
            inputs.governed_input_fact(role, _path_label(declaration.repo_root, path), path, True)
        )
    record = _record(
        "PF-08", reconcile.TIER_A, reconcile.MATCH if not missing else reconcile.DIVERGENCE,
        reconcile.GATING,
        "every declared governed evidence input is present",
        missing or "all declared inputs present",
        "declared input presence (R1/R5 evidence inputs)",
        "MD-11 #1/#2 input identity and hashes",
    )
    records.append(record)
    if missing:
        raise _fail(records, record, "declared governed evidence input missing: " + "; ".join(missing))

    # PF-09 output root: new or empty, writable, capacity
    out_problems, out_observed, out_transient = _output_root_checks(declaration)
    print(
        "  output root: %s (free=%s bytes, min=%s)"
        % (
            "ok" if not out_problems else "FAILED",
            out_transient.get("free_bytes"),
            declaration.min_free_bytes,
        )
    )
    record = _record(
        "PF-09", reconcile.TIER_A, reconcile.MATCH if not out_problems else reconcile.DIVERGENCE,
        reconcile.GATING,
        "output root is new or empty, writable, and has the declared free space",
        out_observed,
        "os.path checks on the declared output root; shutil.disk_usage for the capacity gate",
        "RD-7 (accepted): run-scoped output, new/empty, fail-closed; not a storage-technology selection",
    )
    records.append(record)
    if out_problems:
        raise _fail(records, record, "; ".join(out_problems))

    # ---------------------------------------------------------------- phase 2: corpus
    archives = inputs.discover_archives(
        {"LEGACY": declaration.legacy_root, "UDIFF": declaration.udiff_root}
    )
    discovered_pairs = set(inputs.corpus_archive_pairs(archives))
    inventory_pairs = set((item["root"], item["relative_path"]) for item in inventory_records)
    missing = sorted(inventory_pairs - discovered_pairs)
    unexpected = sorted(discovered_pairs - inventory_pairs)
    record = _record(
        "PF-10", reconcile.TIER_A,
        reconcile.MATCH if not missing and not unexpected else reconcile.DIVERGENCE,
        reconcile.GATING,
        "discovered archive set == D01 inventory set (both directions)",
        {"missing": [list(pair) for pair in missing[:20]], "unexpected": [list(pair) for pair in unexpected[:20]],
         "missing_count": len(missing), "unexpected_count": len(unexpected),
         "discovered": len(archives), "inventory": len(inventory_records)},
        "archive identity is (root, relative_path); names are never derived or repaired",
        "R1; RD-4 Tier A (missing or unexpected archive fails the complete run)",
    )
    records.append(record)
    if missing or unexpected:
        raise _fail(records, record, "corpus archive set does not match the D01 inventory")

    # PF-11 corpus-level cardinality and uniqueness
    checksums = {}
    dates = {}
    problems = []
    for archive in archives:
        record_item = inventory_index[(archive.root, archive.relative_path)]
        checksums.setdefault(record_item["sha256"], []).append(archive.relative_path)
        dates.setdefault(record_item["date_from_filename"], []).append(archive.relative_path)
    duplicate_checksums = {key: value for key, value in checksums.items() if len(value) > 1}
    duplicate_dates = {key: value for key, value in dates.items() if len(value) > 1}
    if duplicate_checksums:
        problems.append("duplicate archive checksums: %d" % len(duplicate_checksums))
    if duplicate_dates:
        problems.append("duplicate file dates: %d" % len(duplicate_dates))
    record = _record(
        "PF-11", reconcile.TIER_A, reconcile.MATCH if not problems else reconcile.DIVERGENCE,
        reconcile.GATING,
        "0 duplicate archive checksums; 0 duplicate file dates",
        {
            "duplicate_checksums": len(duplicate_checksums),
            "duplicate_dates": len(duplicate_dates),
            "dates": len(dates),
        },
        "inventory sha256 / date_from_filename cardinality",
        "D01 baseline (duplicate_checksum_count=0, duplicate_date_count=0)",
    )
    records.append(record)
    if problems:
        raise _fail(records, record, "; ".join(problems))

    # PF-12 per-archive bytes and structure (hash, single CSV member read verbatim)
    member_names = {}
    for archive in archives:
        record_item = inventory_index[(archive.root, archive.relative_path)]
        observed_sha = inputs.archive_sha256(archive.path)
        if observed_sha != record_item["sha256"]:
            record = _record(
                "PF-12", reconcile.TIER_A, reconcile.DIVERGENCE, reconcile.GATING,
                record_item["sha256"], observed_sha,
                "sha256 of raw archive bytes vs D01-inventory sha256",
                "D01 baseline (declared basis: D01-inventory)",
                note="archive: %s :: %s" % (archive.root, archive.relative_path),
            )
            records.append(record)
            raise _fail(records, record, "archive sha256 mismatch: %s" % archive.relative_path)
        try:
            names = inputs.csv_member_names(archive.path)
        except inputs.PreflightFailure as exc:
            record = _record(
                "PF-12", reconcile.TIER_A, reconcile.DIVERGENCE, reconcile.GATING,
                "readable ZIP archive", str(exc),
                "archive structure check (ZIP central directory)",
                "R1/R2; RD-9 malformed archive fails closed",
                note="archive: %s :: %s" % (archive.root, archive.relative_path),
            )
            records.append(record)
            raise _fail(records, record, "malformed archive: %s" % archive.relative_path)
        csv_names = [name for name in names if name.lower().endswith(".csv")]
        if len(csv_names) != 1:
            record = _record(
                "PF-12", reconcile.TIER_A, reconcile.DIVERGENCE, reconcile.GATING,
                "exactly one .csv member", "%d .csv member(s)" % len(csv_names),
                "ZIP member listing",
                "R1/R2; RD-5 member identity read verbatim",
                note="archive: %s :: %s" % (archive.root, archive.relative_path),
            )
            records.append(record)
            raise _fail(
                records, record, "archive does not contain exactly one CSV member: %s"
                % archive.relative_path
            )
        member_names[archive.path] = csv_names[0]

    records.append(
        _record(
            "PF-12", reconcile.TIER_A, reconcile.MATCH, reconcile.GATING,
            "every archive hashes to its D01 sha256 and contains exactly one .csv member",
            {"archives": len(archives), "members": len(member_names)},
            "per-archive sha256 + ZIP central-directory member listing",
            "R1/R2; D01 baseline",
        )
    )

    # Summary record (gating no-op, retained for auditability)
    records.append(
        _record(
            "PF-13", reconcile.TIER_G, reconcile.MATCH, reconcile.NON_GATING,
            "preflight complete", {"archives": len(archives), "partitions_expected": None},
            "preflight summary", "RD-9 fail-closed preflight",
            note="preflight passed; processing may begin",
        )
    )

    return PreflightOutcome(
        records=tuple(records),
        archives=archives,
        inventory_records=inventory_records,
        inventory_index=inventory_index,
        governed_input_facts=tuple(governed_input_facts),
        present_inputs=present_inputs,
        archive_pairs=tuple((a.root, a.relative_path) for a in archives),
        member_names=dict(member_names),
        identity={
            "engine_fingerprint": engine_fingerprint,
            "runner_fingerprint": runner_fingerprint,
        },
    )


def case_insensitive_filesystem() -> bool:
    """True on filesystems that fold case (Windows, macOS default) — detected, never assumed."""
    return os.path.normcase("A") == "a"


def comparison_key(path: str, case_insensitive: bool = None) -> str:
    """Canonical comparison form of a declared path.

    Symlinks are resolved and the path is normalised, then folded when the target filesystem
    folds case (F4). Folding is applied only in that case so a genuinely case-sensitive
    filesystem keeps its distinguishing power; callers may pass the flag explicitly.
    """
    if case_insensitive is None:
        case_insensitive = case_insensitive_filesystem()
    key = os.path.normpath(os.path.realpath(os.path.abspath(path)))
    return key.casefold() if case_insensitive else key


def path_is_within(child: str, parent: str, case_insensitive: bool = None) -> bool:
    """True when ``child`` is ``parent`` itself or lies beneath it.

    Windows-safe custody comparison: equality and containment are decided on the canonical
    comparison form, so a differently-cased spelling of the same directory cannot defeat the
    read-only corpus-custody gate (F4). Sibling-prefix traps (``/a/corpusX`` vs ``/a/corpus``)
    are excluded by comparing whole path segments.
    """
    if not child or not parent:
        return False
    child_key = comparison_key(child, case_insensitive)
    parent_key = comparison_key(parent, case_insensitive)
    if child_key == parent_key:
        return True
    if not parent_key.endswith(os.sep):
        parent_key += os.sep
    return child_key.startswith(parent_key)


def output_placement_problems(declaration: RunDeclaration) -> list:
    """Placement problems for the declared output root.

    Shared by PF-04 and by the writer gate in the runner entry point: the output root must sit
    outside both corpus roots, so that a run — including its failure record — can never be
    written into the read-only corpus custody. Comparison is case-folding on case-insensitive
    filesystems (F4).
    """
    problems = []
    if not declaration.out:
        return ["no output root declared"]
    for label, root_path in (("LEGACY", declaration.legacy_root), ("UDIFF", declaration.udiff_root)):
        if not root_path:
            continue
        if path_is_within(declaration.out, root_path):
            problems.append("output root is inside the %s corpus root" % label)
    if (
        declaration.legacy_root
        and declaration.udiff_root
        and comparison_key(declaration.legacy_root) == comparison_key(declaration.udiff_root)
    ):
        problems.append("LEGACY and UDIFF roots are the same directory")
    return problems


def output_root_contamination_problems(declaration: RunDeclaration) -> list:
    """Conditions under which the runner must not write anything at all (F5).

    The declared output root is a *new, run-scoped* directory (RD-7). If a run were allowed to
    write into a pre-existing non-empty directory — even only ``RUN_FAILED.json`` — it would
    treat an unrelated directory as its own run root. The gate therefore refuses to write when
    the root is inside a corpus root, is not a directory, or already holds entries.
    """
    problems = list(output_placement_problems(declaration))
    path = declaration.out
    if not path:
        return problems
    if os.path.exists(path):
        if not os.path.isdir(path):
            problems.append("output root exists and is not a directory")
        elif sorted(os.listdir(path)):
            problems.append(
                "output root is not empty (%d entr(y|ies)); a run root must be new or empty "
                "(RD-7) and a pre-existing directory is never treated as this run's root"
                % len(os.listdir(path))
            )
    return problems


def _output_root_checks(declaration: RunDeclaration) -> tuple:
    """Return ``(problems, retained_observed, transient)`` for the declared output root.

    The **retained** record contains only deterministic, declared facts. Observed host state
    (actual free bytes, whether the directory had to be created, entry count) is transient:
    it is reported on stdout for the operator and never written into the package, so two
    replays of the same declared configuration stay byte-identical (RD-8 option A).
    """
    problems = []
    retained = {
        "output_root_condition": "new or empty (RD-7)",
        "writable": None,
        "declared_minimum_bytes": declaration.min_free_bytes,
        "free_space_meets_declared_minimum": None,
    }
    transient = {"free_bytes": None, "created": False, "entries": None}
    path = declaration.out
    if not path:
        return ["no output root declared"], retained, transient
    exists = os.path.exists(path)
    if exists and not os.path.isdir(path):
        return ["output root exists and is not a directory: %s" % path], retained, transient
    if exists:
        entries = sorted(os.listdir(path))
        transient["entries"] = len(entries)
        if entries:
            problems.append("output root is not empty (%d entr(y|ies))" % len(entries))
    else:
        try:
            os.makedirs(path)
        except OSError as exc:
            return ["cannot create output root: %s" % exc], retained, transient
        transient["created"] = True
    retained["writable"] = bool(os.access(path, os.W_OK))
    if not retained["writable"]:
        problems.append("output root is not writable")
    try:
        usage = shutil.disk_usage(path)
        transient["free_bytes"] = usage.free
        retained["free_space_meets_declared_minimum"] = not (
            declaration.min_free_bytes and usage.free < declaration.min_free_bytes
        )
        if not retained["free_space_meets_declared_minimum"]:
            problems.append(
                "free space %d < declared minimum %d" % (usage.free, declaration.min_free_bytes)
            )
    except OSError as exc:
        problems.append("cannot determine free space: %s" % exc)
    return problems, retained, transient


def _path_label(repo_root: str, path: str) -> str:
    """Repo-relative label when possible; otherwise the declared path is NOT retained."""
    try:
        relative = os.path.relpath(os.path.abspath(path), os.path.abspath(repo_root))
    except ValueError:
        return "(outside repo)"
    if relative.startswith(".."):
        return "(outside repo)"
    return relative.replace(os.sep, "/")
