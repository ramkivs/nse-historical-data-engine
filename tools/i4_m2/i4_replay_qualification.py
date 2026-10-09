#!/usr/bin/env python3
"""I4 deterministic-replay qualification gate (corrections K1/K2/K3).

This module is the **qualification layer** of the I4 replay procedure. It sits between the
runner's own `verify`/`replay` commands and the acceptance of a replay verdict:

* **K1 — completeness precondition.** A replay comparison is only *permitted* after both
  packages pass the existing package verification (`i4_output.verify_package`, checks
  `verify-01`..`verify-07`) and both carry a completion marker bound to their own package
  manifest. When a precondition fails the comparison is **not executed at all** and the
  qualification result is FAIL. Nothing in `i4_output.py` is changed: the comparison mechanism
  is untouched, and it keeps its total, exclusion-free semantics.
* **K2 — exact revision pin.** The qualification record captures the repository, authoritative
  ref, revision (commit), tree, engine fingerprint, runner fingerprint, run id and corpus
  identity, and enforces — from the executed bytes as recorded inside the packages — that both
  runs used one and the same engine/runner revision, the same declared run id and the same
  corpus archive set. A replay executed from a different revision (for example the pre-bounded
  -memory `origin/main` revision) fails closed at `RQ-04`/`RQ-05` before any comparison.
* **K3 — genuine independent replay.** Each package must be accompanied by its **own**
  execution-evidence bundle: the Phase-I evidence facts, the monitor summary that records the
  monitored execution, and the package file listing. The bundle is bound per package (paths,
  counts, digests, identities, marker, listing == total inventory) so a byte copy of package A
  cannot be presented as a fresh replay. Byte identity is never accepted as proof of execution.

The gate performs no comparison and writes nothing unless it is invoked with a verdict path
outside both packages; it never writes into either package root and it never modifies them.

Operator sequence (fail-closed, one step at a time):

    python -B "tools\\i4_runner\\i4_runner.py" verify --package "<A>"
    python -B "tools\\i4_runner\\i4_runner.py" verify --package "<B>"
    python -B "tools\\i4_m2\\i4_replay_qualification.py" ^
      --a "<A>" --b "<B>" ^
      --facts-a "<A evidence facts.json>" --facts-b "<B evidence facts.json>" ^
      --summary-a "<A monitor summary.json>" --summary-b "<B monitor summary.json>" ^
      --trace-a "<A monitor trace.jsonl>"     --trace-b "<B monitor trace.jsonl>" ^
      --listing-a "<A package files.tsv>"     --listing-b "<B package files.tsv>" ^
      --expect-repository "ramkivs/nse-historical-data-engine" ^
      --expect-ref "arena/9021d1a1-nse-historical-data-engine" ^
      --expect-commit "<commit whose blobs are the executed module bytes>" ^
      --expect-tree "<tree of that commit>" ^
      --expect-engine-fingerprint "<sha256>" ^
      --expect-runner-fingerprint "<sha256>" ^
      --expect-run-id "<the baseline run id>" ^
      --expect-corpus-archive-set-digest "<sha256 from the baseline run record>" ^
      --verdict "<path outside both roots>"

Exit codes: `0` qualified and comparison PASS · `2` not qualified (or comparison FAIL) ·
`1` usage (incomplete expectation, bad arguments, verdict inside a package, same directory).

No clock, host, environment value or randomness enters the verdict document; package roots are
reduced to their final path component, so the document is transferable between hosts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

if __name__ == "__main__" and not __package__:
    # direct script execution from any working directory: put the repository root on the path
    # (``tools`` is a namespace package; ``src`` is bootstrapped by i4_identity).
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.i4_runner import i4_output  # noqa: E402

QUALIFICATION_CONTRACT_VERSION = "i4-replay-qualification/1.0"

EXIT_QUALIFIED = 0
EXIT_USAGE = 1
EXIT_NOT_QUALIFIED = 2

#: `<run-id>.PACKAGE_FILES.tsv` header written by the delivered Phase-I evidence script.
LISTING_HEADER = ("path", "size_bytes", "sha256")

RUNNER_EXIT_CODE_NOTE = (
    "the M2 monitor recorded a null runner exit code (documented, non-gating anomaly): 0 and "
    "null are both accepted here and the observed value is recorded, never reinterpreted"
)

QUALIFICATION_NOTE = (
    "A replay PASS requires both packages to be complete and verified, both runs to share one "
    "declared revision/run-id/corpus identity, and both packages to carry their own "
    "execution-evidence bundle (K1/K2/K3). Byte identity is never treated as proof that the "
    "second package was produced by a fresh execution; that proof is the execution evidence "
    "bundle recorded per package (monitor summary, evidence facts, package listing)."
)


class QualificationError(RuntimeError):
    """Usage-level refusal (incomplete expectation or unusable arguments). Exit code 1."""


# ------------------------------------------------------------------ expectations


@dataclass(frozen=True)
class RevisionExpectation:
    """Everything the qualification record must capture (K2). All fields are declared."""

    repository: str
    ref: str
    commit: str
    tree: str
    engine_fingerprint: str
    runner_fingerprint: str
    run_id: str
    corpus_archive_set_digest: str
    #: when True the recorded host checkout (``repo_head``/``repo_tree`` in the evidence facts)
    #: must equal the declared commit/tree. When False the recorded values are still required,
    #: still recorded, and still required to agree between A and B (same procedure on one host
    #: state is the default expectation; applying the payload onto a different base commit is a
    #: recorded, reviewable deviation).
    require_same_recorded_head: bool = False

    REQUIRED_FIELDS = (
        "repository",
        "ref",
        "commit",
        "tree",
        "engine_fingerprint",
        "runner_fingerprint",
        "run_id",
        "corpus_archive_set_digest",
    )

    def missing_fields(self) -> Tuple[str, ...]:
        return tuple(name for name in self.REQUIRED_FIELDS if not str(getattr(self, name)).strip())

    def as_record(self) -> Dict[str, Any]:
        return {
            "repository": self.repository,
            "authoritative_ref": self.ref,
            "revision_commit": self.commit,
            "revision_tree": self.tree,
            "engine_fingerprint": self.engine_fingerprint,
            "runner_fingerprint": self.runner_fingerprint,
            "run_id": self.run_id,
            "corpus_archive_set_digest": self.corpus_archive_set_digest,
            "recorded_head_must_equal_revision": bool(self.require_same_recorded_head),
        }


# ------------------------------------------------------------------ evidence bundle


@dataclass(frozen=True)
class RunEvidence:
    """One package's independent execution-evidence bundle (K3).

    Four documents, all small and transferable: the Phase-I evidence facts, the monitor summary,
    the monitor's sampled trace (`<prefix>.jsonl`, one line per sample) and the package file
    listing. The trace is what makes the bundle an *execution* record rather than a manifest
    copy: its samples, count, peak and ordering must agree with the summary, and a genuine second
    run's trace can never be A's trace.
    """

    facts: Mapping[str, Any]
    summary: Mapping[str, Any]
    listing: Mapping[str, Tuple[int, str]]
    monitor_log: Tuple[Mapping[str, Any], ...]
    facts_sha256: str
    summary_sha256: str
    listing_sha256: str
    monitor_log_sha256: str

    def documents(self) -> Dict[str, Any]:
        return {
            "evidence_facts_sha256": self.facts_sha256,
            "monitor_summary_sha256": self.summary_sha256,
            "monitor_log_sha256": self.monitor_log_sha256,
            "package_listing_sha256": self.listing_sha256,
            "evidence_facts_result": self.facts.get("result"),
            "package_file_count_declared": self.facts.get("package_file_count"),
            "listing_rows": len(self.listing),
        }


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def _read_json_document(path: str, label: str) -> Tuple[Optional[Mapping], Optional[str]]:
    try:
        raw = _read_bytes(path)
    except OSError as exc:
        return None, "%s unavailable: %s (%s)" % (label, _normalised_basename(path), exc.strerror or exc)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        return None, "%s is not valid UTF-8: %s (%s)" % (label, _normalised_basename(path), exc)
    try:
        document = json.loads(text)
    except ValueError as exc:
        return None, "%s is not valid JSON: %s (%s)" % (label, _normalised_basename(path), exc)
    if not isinstance(document, dict):
        return None, "%s is not a JSON object: %s" % (label, _normalised_basename(path))
    return document, None


def _read_listing(path: str, label: str) -> Tuple[Optional[Dict[str, Tuple[int, str]]], Optional[str]]:
    try:
        raw = _read_bytes(path)
    except OSError as exc:
        return None, "%s unavailable: %s (%s)" % (label, _normalised_basename(path), exc.strerror or exc)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        return None, "%s is not valid UTF-8: %s (%s)" % (label, _normalised_basename(path), exc)
    lines = [line for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip()]
    if not lines:
        return None, "%s is empty: %s" % (label, _normalised_basename(path))
    header = tuple(lines[0].split("\t"))
    if header[: len(LISTING_HEADER)] != LISTING_HEADER:
        return None, "%s header is %r, expected %r" % (label, header, LISTING_HEADER)
    entries: Dict[str, Tuple[int, str]] = {}
    for number, line in enumerate(lines[1:], start=2):
        parts = line.split("\t")
        if len(parts) != 3:
            return None, "%s line %d is malformed: %r" % (label, number, line)
        relative, size_text, digest = parts
        try:
            size = int(size_text)
        except ValueError:
            return None, "%s line %d has a non-integer size: %r" % (label, number, size_text)
        if relative in entries:
            return None, "%s lists %r twice" % (label, relative)
        entries[relative] = (size, digest.lower())
    return entries, None


def _read_monitor_log(path: str, label: str) -> Tuple[Optional[Tuple[Mapping[str, Any], ...]], Optional[str]]:
    try:
        raw = _read_bytes(path)
    except OSError as exc:
        return None, "%s unavailable: %s (%s)" % (label, _normalised_basename(path), exc.strerror or exc)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        return None, "%s is not valid UTF-8: %s (%s)" % (label, _normalised_basename(path), exc)
    lines = [line for line in text.replace("\r\n", "\n").split("\n") if line.strip()]
    if not lines:
        return None, "%s is empty: %s" % (label, _normalised_basename(path))
    samples = []
    for number, line in enumerate(lines, start=1):
        try:
            sample = json.loads(line)
        except ValueError as exc:
            return None, "%s line %d is not valid JSON: %s" % (label, number, exc)
        if not isinstance(sample, dict):
            return None, "%s line %d is not a JSON object" % (label, number)
        samples.append(sample)
    return tuple(samples), None


def load_evidence(
    facts_path: str, summary_path: str, listing_path: str, monitor_log_path: str, label: str
) -> Tuple[Optional[RunEvidence], Optional[str]]:
    """Load one package's evidence bundle. Returns ``(evidence, problem)``; never raises."""
    facts, problem = _read_json_document(facts_path, "%s evidence facts" % label)
    if problem:
        return None, problem
    summary, problem = _read_json_document(summary_path, "%s monitor summary" % label)
    if problem:
        return None, problem
    listing, problem = _read_listing(listing_path, "%s package listing" % label)
    if problem:
        return None, problem
    monitor_log, problem = _read_monitor_log(monitor_log_path, "%s monitor trace" % label)
    if problem:
        return None, problem
    return (
        RunEvidence(
            facts=facts,
            summary=summary,
            listing=listing,
            monitor_log=monitor_log,
            facts_sha256=hashlib.sha256(_read_bytes(facts_path)).hexdigest(),
            summary_sha256=hashlib.sha256(_read_bytes(summary_path)).hexdigest(),
            listing_sha256=hashlib.sha256(_read_bytes(listing_path)).hexdigest(),
            monitor_log_sha256=hashlib.sha256(_read_bytes(monitor_log_path)).hexdigest(),
        ),
        None,
    )


# ------------------------------------------------------------------ package facts


@dataclass(frozen=True)
class PackageFacts:
    root: str
    dir_name: str
    run_record: Mapping[str, Any]
    marker: Mapping[str, Any]
    manifest_sha256: str
    files: Mapping[str, Tuple[int, str]]
    total_bytes: int
    run_id: str
    composite_run_identity: str
    archive_set_digest: str
    engine_fingerprint: str
    runner_fingerprint: str
    engine_module_count: int
    engine_modules_digest: str
    counts: Mapping[str, Any]
    marker_problem: str = ""

    def as_record(self) -> Dict[str, Any]:
        return {
            "directory_name": self.dir_name,
            "files": len(self.files),
            "total_bytes": self.total_bytes,
            "run_id": self.run_id,
            "composite_run_identity": self.composite_run_identity,
            "corpus_archive_set_digest": self.archive_set_digest,
            "engine_fingerprint": self.engine_fingerprint,
            "runner_fingerprint": self.runner_fingerprint,
            "engine_module_count": self.engine_module_count,
            "engine_modules_digest": self.engine_modules_digest,
            "counts": dict(self.counts),
            "package_manifest_sha256": self.manifest_sha256,
            "completion_marker_run_id": self.marker.get("run_id"),
            "completion_marker_manifest": self.marker.get("package_manifest_sha256"),
            "completion_marker_problem": self.marker_problem,
        }


def _normalised_basename(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    return value.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]


def _scan_package(package: str) -> Dict[str, Tuple[int, str]]:
    entries: Dict[str, Tuple[int, str]] = {}
    for dirpath, dirnames, filenames in os.walk(package):
        dirnames.sort()
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            relative = os.path.relpath(path, package).replace(os.sep, "/")
            entries[relative] = (os.path.getsize(path), i4_output.sha256_file(path))
    return entries


def read_package_facts(package: str) -> Tuple[Optional[PackageFacts], Optional[str]]:
    """Read the identity facts a *package* carries. Returns ``(facts, problem)``; never raises."""
    if not os.path.isdir(package):
        return None, "package directory does not exist: %s" % _normalised_basename(package)
    record, problem = _read_json_document(os.path.join(package, "RUN_RECORD.json"), "RUN_RECORD.json")
    if problem:
        return None, problem
    marker_path = os.path.join(package, i4_output.COMPLETION_MARKER)
    marker, marker_problem = _read_json_document(marker_path, i4_output.COMPLETION_MARKER)
    if marker is None:
        # a missing or unreadable marker must not hide the rest of the package's identity facts:
        # it is reported by name in RQ-02 (verify-04) and RQ-08 and keeps the record complete.
        marker = {}
        marker_problem = marker_problem or "completion marker unavailable"
    manifest_path = os.path.join(package, i4_output.PACKAGE_MANIFEST)
    if not os.path.isfile(manifest_path):
        return None, "package manifest is missing in %s" % _normalised_basename(package)
    engine = record.get("engine_identity") or {}
    runner = record.get("runner_identity") or {}
    corpus = record.get("corpus") or {}
    modules = engine.get("engine_modules") or []
    files = _scan_package(package)
    return (
        PackageFacts(
            root=package,
            dir_name=_normalised_basename(package),
            run_record=record,
            marker=marker,
            manifest_sha256=i4_output.sha256_file(manifest_path),
            files=files,
            total_bytes=sum(size for size, _digest in files.values()),
            run_id=str(record.get("run_id") or ""),
            composite_run_identity=str(record.get("composite_run_identity") or ""),
            archive_set_digest=str(corpus.get("archive_set_digest") or ""),
            engine_fingerprint=str(engine.get("tool_sha256") or ""),
            runner_fingerprint=str(runner.get("runner_sha256") or ""),
            engine_module_count=int(engine.get("engine_module_count") or 0),
            engine_modules_digest=hashlib.sha256(i4_output.canonical_json(modules).encode("utf-8")).hexdigest(),
            counts=dict(record.get("counts") or {}),
            marker_problem=marker_problem,
        ),
        None,
    )


# ------------------------------------------------------------------ check records


def _check(
    records: list,
    check_id: str,
    tier: str,
    result: str,
    expected: Any,
    observed: Any,
    basis: str,
    note: str = "",
    disposition: str = "gating",
) -> None:
    records.append(
        {
            "check_id": check_id,
            "tier": tier,
            "disposition": disposition,
            "result": result,
            "expected": expected,
            "observed": observed,
            "comparison_basis": basis,
            "note": note,
        }
    )


def _equal(left: Any, right: Any) -> bool:
    return left == right


def _numbers_equal(left: Any, right: Any) -> bool:
    try:
        return float(left) == float(right)
    except (TypeError, ValueError):
        return False


# ------------------------------------------------------------------ K3 binding


def _bind_evidence(package: PackageFacts, evidence: Optional[RunEvidence], problem: Optional[str]) -> Dict[str, Any]:
    """Evaluate the K3 predicates for one package. Returns a per-predicate result mapping."""
    if evidence is None:
        return {"evidence_bundle_available": {"result": False, "detail": problem or "unavailable"}}

    facts = evidence.facts
    summary = evidence.summary
    counts = package.counts
    predicates: Dict[str, Any] = {}

    def predicate(name: str, outcome: bool, detail: Any = "") -> None:
        predicates[name] = {"result": bool(outcome), "detail": detail}

    predicate("evidence_bundle_available", True, "loaded")
    predicate(
        "evidence_facts_result_pass",
        str(facts.get("result")) == "PASS",
        "result=%r problems=%r" % (facts.get("result"), facts.get("problems")),
    )
    predicate("evidence_facts_problems_empty", list(facts.get("problems") or []) == [], facts.get("problems"))
    predicate(
        "run_id_binds_to_package",
        str(facts.get("run_id") or "") == package.run_id and package.run_id != "",
        "facts=%r package=%r" % (facts.get("run_id"), package.run_id),
    )
    predicate(
        "out_root_binds_to_package",
        _normalised_basename(facts.get("out_root")) == package.dir_name
        and _normalised_basename(summary.get("out_root")) == package.dir_name,
        "facts=%r summary=%r package=%r"
        % (_normalised_basename(facts.get("out_root")), _normalised_basename(summary.get("out_root")), package.dir_name),
    )
    predicate(
        "recorded_repository_revision_present",
        bool(str(facts.get("repo_head") or "").strip()) and bool(str(facts.get("repo_tree") or "").strip()),
        {"repo_head": facts.get("repo_head"), "repo_tree": facts.get("repo_tree")},
    )
    predicate(
        "evidence_fingerprints_equal_package",
        str(facts.get("engine_fingerprint") or "") == package.engine_fingerprint
        and str(facts.get("runner_fingerprint") or "") == package.runner_fingerprint,
        {
            "facts_engine": facts.get("engine_fingerprint"),
            "facts_runner": facts.get("runner_fingerprint"),
            "package_engine": package.engine_fingerprint,
            "package_runner": package.runner_fingerprint,
        },
    )
    marker_path = os.path.join(package.root, i4_output.COMPLETION_MARKER)
    record_path = os.path.join(package.root, "RUN_RECORD.json")
    manifest_path = os.path.join(package.root, i4_output.PACKAGE_MANIFEST)
    reconciliation_path = os.path.join(package.root, "RECONCILIATION.jsonl")

    def digest_of(path: str) -> str:
        return i4_output.sha256_file(path) if os.path.isfile(path) else ""

    marker_digest = digest_of(marker_path)
    predicate(
        "completion_marker_sha256_binds",
        marker_digest != "" and str(facts.get("completion_marker_sha256") or "").upper() == marker_digest.upper(),
        "facts=%r disk=%r" % (facts.get("completion_marker_sha256"), marker_digest or "(missing)"),
    )
    predicate("completion_marker_present_flag", facts.get("completion_marker_present") is True, facts.get("completion_marker_present"))
    record_digest = digest_of(record_path)
    predicate(
        "run_record_sha256_binds",
        record_digest != "" and str(facts.get("run_record_sha256") or "").upper() == record_digest.upper(),
        "facts=%r disk=%r" % (facts.get("run_record_sha256"), record_digest or "(missing)"),
    )
    predicate(
        "package_manifest_sha256_binds",
        str(facts.get("package_manifest_sha256") or "").upper() == package.manifest_sha256.upper(),
        "facts=%r disk=%r" % (facts.get("package_manifest_sha256"), package.manifest_sha256),
    )
    reconciliation_digest = digest_of(reconciliation_path)
    predicate(
        "reconciliation_sha256_binds",
        str(facts.get("reconciliation_sha256") or "").upper() == reconciliation_digest.upper()
        and reconciliation_digest != "",
        "facts=%r disk=%r" % (facts.get("reconciliation_sha256"), reconciliation_digest),
    )
    predicate(
        "record_counts_bind",
        _numbers_equal(facts.get("record_members"), counts.get("members"))
        and _numbers_equal(facts.get("record_rows"), counts.get("rows"))
        and _numbers_equal(facts.get("record_observations"), counts.get("observations"))
        and _numbers_equal(facts.get("record_quarantined"), counts.get("quarantined")),
        {
            "facts": {
                "members": facts.get("record_members"),
                "rows": facts.get("record_rows"),
                "observations": facts.get("record_observations"),
                "quarantined": facts.get("record_quarantined"),
            },
            "package": dict(counts),
        },
    )
    predicate(
        "record_composite_identity_binds",
        str(facts.get("record_composite_identity") or "") == package.composite_run_identity
        and package.composite_run_identity != "",
        "facts=%r package=%r" % (facts.get("record_composite_identity"), package.composite_run_identity),
    )
    predicate(
        "record_archive_set_digest_binds",
        str(facts.get("record_archive_set_digest") or "") == package.archive_set_digest
        and package.archive_set_digest != "",
        "facts=%r package=%r" % (facts.get("record_archive_set_digest"), package.archive_set_digest),
    )
    predicate(
        "package_listing_covers_package",
        dict(evidence.listing) == dict(package.files),
        {
            "listing_rows": len(evidence.listing),
            "package_files": len(package.files),
            "listing_only": sorted(set(evidence.listing) - set(package.files))[:5],
            "package_only": sorted(set(package.files) - set(evidence.listing))[:5],
            "differing": sorted(
                name
                for name in set(evidence.listing) & set(package.files)
                if evidence.listing[name] != package.files[name]
            )[:5],
        },
    )
    predicate(
        "package_file_count_binds",
        _numbers_equal(facts.get("package_file_count"), len(package.files)),
        "facts=%r package=%r" % (facts.get("package_file_count"), len(package.files)),
    )
    predicate(
        "package_total_bytes_bind",
        _numbers_equal(facts.get("package_total_bytes"), package.total_bytes),
        "facts=%r package=%r" % (facts.get("package_total_bytes"), package.total_bytes),
    )
    predicate(
        "monitor_run_id_binds",
        str(summary.get("run_id") or "") == package.run_id and package.run_id != "",
        "summary=%r package=%r" % (summary.get("run_id"), package.run_id),
    )
    predicate("monitor_completion_marker", summary.get("completion_marker_present") is True, summary.get("completion_marker_present"))
    predicate(
        "monitor_no_breach",
        summary.get("breach") is False and not facts.get("rss_breach"),
        {"summary_breach": summary.get("breach"), "facts_rss_breach": facts.get("rss_breach")},
    )
    predicate(
        "monitor_runner_exit_code",
        "runner_exit_code" in summary and summary.get("runner_exit_code") in (0, None),
        {"runner_exit_code": summary.get("runner_exit_code"), "note": RUNNER_EXIT_CODE_NOTE},
    )
    predicate(
        "monitor_peak_rss_binds",
        _numbers_equal(facts.get("peak_process_rss_mb"), summary.get("peak_rss_mb"))
        and _numbers_equal(facts.get("rss_limit_mb"), summary.get("rss_limit_mb")),
        {
            "facts_peak": facts.get("peak_process_rss_mb"),
            "summary_peak": summary.get("peak_rss_mb"),
            "facts_limit": facts.get("rss_limit_mb"),
            "summary_limit": summary.get("rss_limit_mb"),
        },
    )
    predicate(
        "monitor_summary_path_recorded",
        bool(str(facts.get("monitor_summary_path") or "").strip()),
        _normalised_basename(facts.get("monitor_summary_path")),
    )

    # ---- the monitor trace: sampled evidence of a monitored execution, not a manifest copy
    log = evidence.monitor_log
    sample_numbers = [sample.get("sample") for sample in log]
    rss_values = [sample.get("rss_mb") for sample in log if isinstance(sample.get("rss_mb"), (int, float))]
    available_values = [
        sample.get("available_mb") for sample in log if isinstance(sample.get("available_mb"), (int, float))
    ]
    declared_samples = summary.get("samples")
    predicate(
        "monitor_trace_present",
        len(log) >= 2,
        {"samples": len(log)},
    )
    predicate(
        "monitor_trace_numbering",
        sample_numbers == list(range(1, len(log) + 1)),
        {"first": sample_numbers[:3], "last": sample_numbers[-3:], "count": len(sample_numbers)},
    )
    predicate(
        "monitor_trace_count_matches_summary",
        _numbers_equal(declared_samples, len(log)),
        {"summary_samples": declared_samples, "trace_lines": len(log)},
    )
    predicate(
        "monitor_trace_peak_matches_summary",
        bool(rss_values) and _numbers_equal(max(rss_values), summary.get("peak_rss_mb")),
        {"trace_peak_mb": max(rss_values) if rss_values else None, "summary_peak_mb": summary.get("peak_rss_mb")},
    )
    predicate(
        "monitor_trace_within_declared_limit",
        bool(rss_values) and _numbers_equal(summary.get("rss_limit_mb"), facts.get("rss_limit_mb"))
        and all(value <= float(summary.get("rss_limit_mb") or 0) for value in rss_values),
        {
            "trace_peak_mb": max(rss_values) if rss_values else None,
            "declared_limit_mb": summary.get("rss_limit_mb"),
            "samples_over_limit": sum(
                1 for value in rss_values if value > float(summary.get("rss_limit_mb") or 0)
            ),
        },
    )
    predicate(
        "monitor_trace_min_available_matches_summary",
        summary.get("min_available_mb") is None
        or (bool(available_values) and _numbers_equal(min(available_values), summary.get("min_available_mb"))),
        {
            "trace_min_available_mb": min(available_values) if available_values else None,
            "summary_min_available_mb": summary.get("min_available_mb"),
        },
    )
    return predicates


# ------------------------------------------------------------------ qualification


def qualification_report(
    package_a: str,
    package_b: str,
    evidence_a: Optional[RunEvidence],
    evidence_b: Optional[RunEvidence],
    problem_a: Optional[str],
    problem_b: Optional[str],
    expected: RevisionExpectation,
    allow_recorded_head_difference: bool = False,
) -> Dict[str, Any]:
    """Evaluate every qualification precondition and (only if permitted) the byte comparison."""
    records: list = []
    missing = expected.missing_fields()
    if missing:
        raise QualificationError("the declared expectation is incomplete: %s" % ", ".join(missing))

    facts_a, load_problem_a = read_package_facts(package_a)
    facts_b, load_problem_b = read_package_facts(package_b)

    # ---- RQ-01 / RQ-02: K1 — the existing package verification, per package
    verification: Dict[str, Dict[str, Any]] = {}
    for label, package in (("a", package_a), ("b", package_b)):
        try:
            verification[label] = i4_output.verify_package(package)
        except Exception as exc:  # a malformed manifest must fail closed, never raise out of the gate
            verification[label] = {
                "result": "fail",
                "failures": ("verification-raised", "%s: %s" % (type(exc).__name__, exc)),
                "checks": (),
            }
    _check(
        records, "RQ-01", "A", "pass" if verification["a"]["result"] == "pass" else "fail",
        "package A passes verify_package (verify-01..verify-07)",
        {"result": verification["a"]["result"], "failures": list(verification["a"].get("failures") or ())},
        "i4_output.verify_package on package A (K1: the comparison is never reached without it)",
    )
    _check(
        records, "RQ-02", "A", "pass" if verification["b"]["result"] == "pass" else "fail",
        "package B passes verify_package (verify-01..verify-07)",
        {"result": verification["b"]["result"], "failures": list(verification["b"].get("failures") or ())},
        "i4_output.verify_package on package B (K1)",
    )

    # ---- RQ-03..RQ-07: K2 — one declared identity for both runs
    def pair(attr: str, expected_attr: str = "") -> Dict[str, Any]:
        return {
            "a": getattr(facts_a, attr) if facts_a else None,
            "b": getattr(facts_b, attr) if facts_b else None,
            "expected": getattr(expected, expected_attr or attr),
        }

    run_ids = pair("run_id")
    _check(
        records, "RQ-03", "G",
        "pass" if run_ids["a"] and run_ids["a"] == run_ids["b"] == run_ids["expected"] else "fail",
        "one declared run id: A == B == expectation (RD-10: the run id is the only run-metadata field)",
        run_ids,
        "run id recorded in RUN_RECORD.json vs the declared run id",
    )
    engine_pairs = pair("engine_fingerprint")
    _check(
        records, "RQ-04", "G",
        "pass" if engine_pairs["a"] and engine_pairs["a"] == engine_pairs["b"] == engine_pairs["expected"] else "fail",
        "one executed engine revision: A == B == expectation (K2); a different revision cannot reproduce a package",
        engine_pairs,
        "engine_identity.tool_sha256 recorded inside each package (bytes actually executed)",
    )
    runner_pairs = pair("runner_fingerprint")
    _check(
        records, "RQ-05", "G",
        "pass" if runner_pairs["a"] and runner_pairs["a"] == runner_pairs["b"] == runner_pairs["expected"] else "fail",
        "one executed runner revision: A == B == expectation (K2)",
        runner_pairs,
        "runner_identity.runner_sha256 recorded inside each package",
    )
    corpus_pairs = pair("archive_set_digest", "corpus_archive_set_digest")
    _check(
        records, "RQ-06", "G",
        "pass" if corpus_pairs["a"] and corpus_pairs["a"] == corpus_pairs["b"] == corpus_pairs["expected"] else "fail",
        "one corpus identity: A == B == expectation (same governed archive set)",
        corpus_pairs,
        "corpus.archive_set_digest recorded inside each package",
    )
    composite_pairs = {
        "a": facts_a.composite_run_identity if facts_a else None,
        "b": facts_b.composite_run_identity if facts_b else None,
    }
    _check(
        records, "RQ-07", "G",
        "pass"
        if composite_pairs["a"] and composite_pairs["a"] == composite_pairs["b"]
        else "fail",
        "one composite run identity: A == B (engine + runner + governed inputs + corpus + run id)",
        composite_pairs,
        "composite_run_identity recorded inside each package",
    )

    # ---- RQ-08: the completion marker bindings (K1 precondition 3/4)
    marker_observations = {}
    for label, facts in (("a", facts_a), ("b", facts_b)):
        if facts is None:
            marker_observations[label] = {"present": False, "bound": False, "detail": "package unreadable"}
            continue
        recorded = str(facts.marker.get("package_manifest_sha256") or "")
        marker_observations[label] = {
            "present": True,
            "run_id": facts.marker.get("run_id"),
            "marker_manifest_field": recorded,
            "manifest_sha256_on_disk": facts.manifest_sha256,
            "bound": recorded.upper() == facts.manifest_sha256.upper() and facts.marker.get("run_id") == facts.run_id,
        }
    _check(
        records, "RQ-08", "A",
        "pass" if all(obs["bound"] for obs in marker_observations.values()) else "fail",
        "both packages carry a completion marker bound to their own manifest and run id",
        marker_observations,
        "RUN_COMPLETE.json package_manifest_sha256/run_id vs the manifest on disk (RD-9)",
    )

    # ---- RQ-09 / RQ-10: K3 — independent execution evidence per package
    binding_a = _bind_evidence(facts_a, evidence_a, problem_a) if facts_a else {
        "evidence_bundle_available": {"result": False, "detail": problem_a or "package unreadable"}
    }
    binding_b = _bind_evidence(facts_b, evidence_b, problem_b) if facts_b else {
        "evidence_bundle_available": {"result": False, "detail": problem_b or "package unreadable"}
    }
    _check(
        records, "RQ-09", "G",
        "pass" if all(item["result"] for item in binding_a.values()) else "fail",
        "package A is accompanied by its own execution-evidence bundle, bound to A (K3)",
        binding_a,
        "evidence facts + monitor summary + package listing, each digest-bound to package A",
        note="a byte copy of another package cannot satisfy these bindings (paths, counts, digests, marker)",
    )
    _check(
        records, "RQ-10", "G",
        "pass" if all(item["result"] for item in binding_b.values()) else "fail",
        "package B is accompanied by its own execution-evidence bundle, bound to B (K3)",
        binding_b,
        "evidence facts + monitor summary + package listing, each digest-bound to package B",
        note="byte identity is not accepted as proof of execution; this bundle is",
    )

    # ---- RQ-11: the two evidence bundles must be distinct documents
    distinct: Dict[str, Any] = {"available": evidence_a is not None and evidence_b is not None}
    if evidence_a is not None and evidence_b is not None:
        distinct.update(
            {
                "evidence_facts_identical": evidence_a.facts_sha256 == evidence_b.facts_sha256,
                "monitor_summary_identical": evidence_a.summary_sha256 == evidence_b.summary_sha256,
                "monitor_trace_identical": evidence_a.monitor_log_sha256 == evidence_b.monitor_log_sha256,
                "package_listing_identical": evidence_a.listing_sha256 == evidence_b.listing_sha256,
            }
        )
        # The listing is a deterministic function of the package bytes, so it IS expected to be
        # identical when the two packages are byte-identical (that is the point of determinism).
        # The facts, the summary and the sampled trace carry host/time/root fields: for two
        # genuine runs they can never be byte-identical documents.
        distinct["distinct"] = not any(
            distinct[key]
            for key in (
                "evidence_facts_identical",
                "monitor_summary_identical",
                "monitor_trace_identical",
            )
        )
    else:
        distinct["distinct"] = False
    _check(
        records, "RQ-11", "G",
        "pass" if distinct.get("distinct") else "fail",
        "the two execution transcripts are distinct documents (evidence facts and monitor "
        "summary+trace; the package listing is a deterministic function of the package and is "
        "expected to be identical for a deterministic replay)",
        distinct,
        "sha256 of each evidence document pair; a transcript carrying a root/host/timestamp cannot "
        "be the same bytes for two runs",
    )

    # ---- RQ-12: the recorded host checkout (revision metadata)
    heads = {
        "a": {"head": (evidence_a.facts.get("repo_head") if evidence_a else None), "tree": (evidence_a.facts.get("repo_tree") if evidence_a else None)},
        "b": {"head": (evidence_b.facts.get("repo_head") if evidence_b else None), "tree": (evidence_b.facts.get("repo_tree") if evidence_b else None)},
    }
    heads["declared_revision"] = {"commit": expected.commit, "tree": expected.tree}
    heads["recorded_head_must_equal_revision"] = bool(expected.require_same_recorded_head)
    heads["allowed_to_differ"] = bool(allow_recorded_head_difference)
    same_head = (
        bool(heads["a"]["head"])
        and heads["a"]["head"] == heads["b"]["head"]
        and heads["a"]["tree"] == heads["b"]["tree"]
    )
    if expected.require_same_recorded_head:
        same_head = same_head and heads["a"]["head"] == expected.commit and heads["a"]["tree"] == expected.tree
    if allow_recorded_head_difference:
        # an explicitly authorized deviation: still recorded, still required to be present
        same_head = bool(heads["a"]["head"]) and bool(heads["b"]["head"]) and not expected.require_same_recorded_head
    _check(
        records, "RQ-12", "G",
        "pass" if same_head else "fail",
        "the recorded repository revision is present and identical for A and B"
        + (" and equal to the declared revision" if expected.require_same_recorded_head else ""),
        heads,
        "repo_head/repo_tree recorded by the Phase-I evidence script in each bundle; the executed "
        "revision is pinned by RQ-04/RQ-05, which read the bytes that actually ran",
    )

    gating_failures = [
        record["check_id"] for record in records if record["disposition"] == "gating" and record["result"] != "pass"
    ]
    comparison_permitted = not gating_failures

    # ---- RQ-13: the byte-exact comparison, executed only when every precondition holds (K1)
    comparison: Optional[Dict[str, Any]] = None
    if not comparison_permitted:
        _check(
            records, "RQ-13", "A", "not-run",
            "byte-exact replay comparison of the two package trees",
            {"reason": "preconditions failed", "failures": list(gating_failures)},
            "i4_output.replay_compare is NOT invoked while any gating precondition fails (K1)",
            note="no comparison means no verdict: a FAIL here is a contract failure, not a byte failure",
        )
    else:
        try:
            comparison = i4_output.replay_compare(package_a, package_b)
            result = "pass" if comparison.get("result") == "pass" else "fail"
            observed: Any = comparison
        except Exception as exc:  # OutputError and any other refusal: fail closed
            result = "fail"
            observed = {"error": "%s: %s" % (type(exc).__name__, exc)}
        _check(
            records, "RQ-13", "A", result,
            "byte-exact replay comparison of the two package trees: result pass",
            observed,
            "i4_output.replay_compare (total comparison: no exclusion list, no normalisation)",
            note="a mismatch is REPLAY-FAILED and is never normalised away (RD-9 case 6)",
        )

    failures = [record["check_id"] for record in records if record["disposition"] == "gating" and record["result"] != "pass"]
    qualified = not failures
    return {
        "contract_version": QUALIFICATION_CONTRACT_VERSION,
        "result": "pass" if qualified else "fail",
        "comparison_permitted": comparison_permitted,
        "failures": failures,
        "checks": records,
        "revision": expected.as_record(),
        "packages": {
            "a": facts_a.as_record() if facts_a else {"unreadable": load_problem_a},
            "b": facts_b.as_record() if facts_b else {"unreadable": load_problem_b},
        },
        "evidence": {
            "a": evidence_a.documents() if evidence_a else {"unavailable": problem_a},
            "b": evidence_b.documents() if evidence_b else {"unavailable": problem_b},
        },
        "comparison": comparison,
        "note": QUALIFICATION_NOTE,
    }


# ------------------------------------------------------------------ command line


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="i4_replay_qualification",
        description=(
            "I4 replay qualification gate: verifies both packages, pins one revision identity and "
            "requires independent execution evidence for both runs before permitting the "
            "byte-exact replay comparison (K1/K2/K3)."
        ),
    )
    parser.add_argument("--a", required=True, help="baseline package root (read-only)")
    parser.add_argument("--b", required=True, help="replay package root (read-only)")
    parser.add_argument("--facts-a", required=True, help="package A <run-id>.EVIDENCE_FACTS.json")
    parser.add_argument("--facts-b", required=True, help="package B <run-id>.EVIDENCE_FACTS.json")
    parser.add_argument("--summary-a", required=True, help="package A monitor summary JSON")
    parser.add_argument("--summary-b", required=True, help="package B monitor summary JSON")
    parser.add_argument("--listing-a", required=True, help="package A <run-id>.PACKAGE_FILES.tsv")
    parser.add_argument("--listing-b", required=True, help="package B <run-id>.PACKAGE_FILES.tsv")
    parser.add_argument("--trace-a", required=True, help="package A monitor trace (<prefix>.jsonl)")
    parser.add_argument("--trace-b", required=True, help="package B monitor trace (<prefix>.jsonl)")
    parser.add_argument("--expect-repository", required=True)
    parser.add_argument("--expect-ref", required=True)
    parser.add_argument("--expect-commit", required=True)
    parser.add_argument("--expect-tree", required=True)
    parser.add_argument("--expect-engine-fingerprint", required=True)
    parser.add_argument("--expect-runner-fingerprint", required=True)
    parser.add_argument("--expect-run-id", required=True)
    parser.add_argument("--expect-corpus-archive-set-digest", required=True)
    parser.add_argument("--verdict", default="", help="optional path for the verdict document")
    parser.add_argument(
        "--strict-recorded-head",
        action="store_true",
        help="require the recorded host checkout (repo_head/repo_tree) to equal --expect-commit/--expect-tree",
    )
    parser.add_argument(
        "--allow-recorded-head-difference",
        action="store_true",
        help=(
            "explicitly authorize different recorded host checkouts for A and B (they must still be "
            "present); the executed revision remains pinned by the fingerprints (RQ-04/RQ-05)"
        ),
    )
    return parser


def _verdict_inside_package(path: str, package: str) -> bool:
    package_abs = os.path.abspath(package)
    verdict_abs = os.path.abspath(path)
    return verdict_abs == package_abs or verdict_abs.startswith(package_abs + os.sep)


def main(argv: Sequence[str] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if os.path.realpath(args.a) == os.path.realpath(args.b):
            raise QualificationError(
                "replay qualification requires two distinct package directories (resolved paths are identical)"
            )
        if not os.path.isdir(args.a) or not os.path.isdir(args.b):
            raise QualificationError("both --a and --b must be existing package directories")
        if args.verdict and (_verdict_inside_package(args.verdict, args.a) or _verdict_inside_package(args.verdict, args.b)):
            print("qualification error: verdict must be written outside both packages", file=sys.stderr)
            return EXIT_USAGE
        if args.strict_recorded_head and args.allow_recorded_head_difference:
            raise QualificationError("--strict-recorded-head and --allow-recorded-head-difference are exclusive")
        expected = RevisionExpectation(
            repository=args.expect_repository,
            ref=args.expect_ref,
            commit=args.expect_commit,
            tree=args.expect_tree,
            engine_fingerprint=args.expect_engine_fingerprint,
            runner_fingerprint=args.expect_runner_fingerprint,
            run_id=args.expect_run_id,
            corpus_archive_set_digest=args.expect_corpus_archive_set_digest,
            require_same_recorded_head=bool(args.strict_recorded_head),
        )
        missing = expected.missing_fields()
        if missing:
            raise QualificationError("the declared expectation is incomplete: %s" % ", ".join(missing))
        evidence_a, problem_a = load_evidence(
            args.facts_a, args.summary_a, args.listing_a, args.trace_a, "package A"
        )
        evidence_b, problem_b = load_evidence(
            args.facts_b, args.summary_b, args.listing_b, args.trace_b, "package B"
        )
        report = qualification_report(
            args.a,
            args.b,
            evidence_a,
            evidence_b,
            problem_a,
            problem_b,
            expected,
            allow_recorded_head_difference=bool(args.allow_recorded_head_difference),
        )
    except QualificationError as exc:
        print("qualification error: %s" % exc, file=sys.stderr)
        return EXIT_USAGE

    body = i4_output.canonical_json(report)
    if args.verdict:
        try:
            with open(args.verdict, "w", encoding="utf-8", newline="") as handle:
                handle.write(body + "\n")
        except OSError as exc:
            print("qualification error: verdict could not be written (%s)" % exc, file=sys.stderr)
            return EXIT_USAGE
    print(body)
    print()
    for record in report["checks"]:
        print(
            "%-7s %s %-9s %s"
            % (record["check_id"], record["tier"], record["result"], record["comparison_basis"][:92])
        )
    if report["failures"]:
        print("failed preconditions: %s" % ", ".join(report["failures"]))
    else:
        print(
            "comparison: %s (%s files vs %s files)"
            % (
                (report["comparison"] or {}).get("result"),
                (report["comparison"] or {}).get("files_a"),
                (report["comparison"] or {}).get("files_b"),
            )
        )
    print("I4 REPLAY QUALIFICATION = %s" % report["result"].upper())
    return EXIT_QUALIFIED if report["result"] == "pass" else EXIT_NOT_QUALIFIED


if __name__ == "__main__":
    raise SystemExit(main())
