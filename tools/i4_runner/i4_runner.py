#!/usr/bin/env python3
"""I4 runner — corpus-side orchestration for the authorized I4 historical replay.

Entry point (R1-R8):

    python tools/i4_runner/i4_runner.py run    --legacy-root <dir> --udiff-root <dir> ...
    python tools/i4_runner/i4_runner.py verify --package <run dir>
    python tools/i4_runner/i4_runner.py replay --a <run dir> --b <run dir> [--verdict <file>]

Boundary (non-production; RD-1..RD-10 as authorized):

* the runner orchestrates, performs bounded IO, validates, reconciles, partitions and writes
  deterministic evidence — it reimplements **no** engine semantics (no parsing, header
  tolerance, field mapping, numeric, flag, calendar, identity, continuity, overlay, metric or
  serialization rule);
* the engine is consumed unmodified (``build_canonical``, ``build_w2``,
  ``rows_jsonl``, ``build_evidence``, ``tool_fingerprint``);
* the retained package is clock-free; the only run-specific field anywhere in canonical
  output is ``provenance.run_id``;
* no storage technology is selected, no API/UI/serving path exists, no network access occurs,
  no corpus mutation occurs, and the corpus is read-only.

Fail-closed policy (RD-9): the first governing failure aborts the run; a completion marker is
written only for a complete, self-checked package; a failed output root is never reused, and a
pre-existing non-empty output root is never written to at all (F5).
"""

from __future__ import annotations

import argparse
import os
import sys

if __name__ == "__main__" and not __package__:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __package__:
    from . import i4_identity as identity
    from . import i4_inputs as inputs
    from . import i4_output as output
    from . import i4_preflight as preflight
    from . import i4_reconcile as reconcile
else:
    import i4_identity as identity  # type: ignore
    import i4_inputs as inputs  # type: ignore
    import i4_output as output  # type: ignore
    import i4_preflight as preflight  # type: ignore
    import i4_reconcile as reconcile  # type: ignore

from nse_engine import contract  # noqa: E402
from nse_engine.pipeline import (  # noqa: E402
    DEFAULT_CONFIG,
    build_canonical,
    build_w2,
)
from nse_engine.errors import NseEngineError  # noqa: E402
from nse_engine.calendar import CalendarEvidenceError  # noqa: E402
from nse_engine.metrics import fold_file_metrics  # noqa: E402
from nse_engine.serialize import build_evidence, rows_jsonl  # noqa: E402

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_FAILED = 2


# ------------------------------------------------------------------ run


def run_command(args) -> int:
    declaration = preflight.RunDeclaration(
        repo_root=os.path.abspath(args.repo_root or identity.REPO_ROOT),
        legacy_root=os.path.abspath(args.legacy_root) if args.legacy_root else "",
        udiff_root=os.path.abspath(args.udiff_root) if args.udiff_root else "",
        out=os.path.abspath(args.out) if args.out else "",
        run_id=args.run_id or "",
        inventory=os.path.abspath(args.inventory) if args.inventory else "",
        labels=os.path.abspath(args.labels) if args.labels else "",
        d01_metrics=os.path.abspath(args.d01_metrics) if args.d01_metrics else "",
        d01_verdict=os.path.abspath(args.d01_verdict) if args.d01_verdict else "",
        series_universe=os.path.abspath(args.series_universe) if args.series_universe else "",
        series_rollup=os.path.abspath(args.series_rollup) if args.series_rollup else "",
        expect_records=args.expect_records or 0,
        expect_inventory_lf_sha256=args.expect_inventory_lf_sha256 or "",
        expect_tool_fingerprint=args.expect_tool_fingerprint or "",
        expect_runner_fingerprint=args.expect_runner_fingerprint or "",
        min_free_bytes=args.min_free_bytes or 0,
    )

    # The declared output root is a new, run-scoped directory (RD-7). Two conditions must hold
    # before ANYTHING is written — including failure evidence: the root must not be inside a
    # corpus root (D03 read-only custody, F4) and it must be new or empty, so that a
    # pre-existing directory can never be contaminated or reinterpreted as this run's root (F5).
    # When either fails, no writer and no directory exist at all; the condition is reported on
    # stderr and the exit code is EXIT_FAILED.
    contamination = preflight.output_root_contamination_problems(declaration)
    writer = None if contamination else output.OutputWriter(declaration.out)
    stage = "preflight"
    processed = 0
    try:
        print("I4 runner %s :: run %s" % (identity.RUNNER_VERSION, declaration.run_id))
        outcome = preflight.run_preflight(declaration)
        writer.write_jsonl("PREFLIGHT.jsonl", outcome.records)
        print(
            "preflight: PASS (%d checks, %d archives, %d inventory records)"
            % (len(outcome.records), len(outcome.archives), len(outcome.inventory_records))
        )

        labels, holidays, registry_ids, labels_document = _load_labels(declaration)
        governed_input_facts = list(outcome.governed_input_facts)
        governed_input_facts.extend(_labels_facts(declaration, labels_document))

        stage = "processing"
        all_records = []
        input_manifest = []
        builds = []
        partition_files = {}
        stems = set()
        rows_total = 0
        quarantined_total = 0
        for index, archive in enumerate(outcome.archives, start=1):
            record = outcome.inventory_index[(archive.root, archive.relative_path)]
            member_name = outcome.member_names[archive.path]
            data = inputs.read_member_bytes(archive.path, member_name)
            observed_archive_sha256 = inputs.archive_sha256(archive.path)
            runner_raw_sha256 = inputs.sha256_bytes(data)
            source = inputs.build_source(record, member_name, declaration.run_id)

            try:
                build = build_canonical(data, source, DEFAULT_CONFIG)
            except NseEngineError as exc:
                raise inputs.GoverningFailure(
                    "parser/canonical rejection for %s :: %s: %s: %s"
                    % (archive.root, archive.relative_path, type(exc).__name__, exc)
                )

            report = build.parse.report.to_dict()
            if not build.rows:
                # A member with zero usable rows cannot contribute to the W2 composition (the
                # engine derives no member-date fact for it). Fail closed with an explicit
                # governed condition instead of an uncontrolled IndexError further down (F3).
                raise inputs.GoverningFailure(
                    "member produced no usable canonical rows: %s :: %s "
                    "(%d data line(s), all quarantined)"
                    % (archive.root, archive.relative_path, report["quarantined"])
                )
            records = list(
                _member_records(
                    record,
                    member_name,
                    source,
                    build,
                    report,
                    runner_raw_sha256,
                    len(data),
                    archive,
                )
            )
            failures = reconcile.gating_failures(records)
            if failures:
                raise inputs.GoverningFailure(
                    "gating reconciliation failure for %s :: %s: %s"
                    % (archive.root, archive.relative_path, failures[0]["check"])
                )

            family, year = inputs.partition_of(record)
            stem = _stem(record["file_name"])
            key = (family, year, stem)
            if key in stems:
                raise inputs.GoverningFailure("duplicate output stem within partition: %s" % (key,))
            stems.add(key)

            rows_path = output.OutputWriter.rows_path(family, year, stem)
            evidence_path = output.OutputWriter.evidence_path(family, year, stem)
            writer.write_text(rows_path, rows_jsonl(build.rows))
            writer.write_json(evidence_path, build_evidence(build))
            partition_files.setdefault((family, year), []).extend((rows_path, evidence_path))

            input_manifest.append(
                {
                    "sequence": index,
                    "root": archive.root,
                    "relative_path": archive.relative_path,
                    "file_name": record["file_name"],
                    "member_name": member_name,
                    "date_from_filename": record["date_from_filename"],
                    "detected_format": record["detected_format"],
                    "engine_family": report["format_family"],
                    "partition": inputs.partition_id(family, year),
                    "archive_sha256_d01": record["sha256"],
                    "archive_sha256_basis": "D01-inventory",
                    "archive_sha256_observed_raw_bytes": observed_archive_sha256,
                    "member_sha256_raw_bytes": report["member_sha256_raw_bytes"],
                    "member_sha256_lf_text": report["member_sha256_lf_text"],
                    "member_size_bytes": report["member_size_bytes"],
                    "header_physical_width": report["header_physical_width"],
                    "header_tolerance_applied": report["header_tolerance_applied"],
                    "data_lines": report["data_lines"],
                    "rows": len(build.rows),
                    "quarantined": report["quarantined"],
                }
            )
            all_records.extend(records)
            builds.append(build)
            rows_total += len(build.rows)
            quarantined_total += report["quarantined"]
            processed = index
            if index % 250 == 0 or index == len(outcome.archives):
                print("  processed %d/%d archives" % (index, len(outcome.archives)))

        stage = "w2"
        # The engine's W2 composition takes the canonical builds themselves; the engine derives
        # the member-date facts from those builds. Nothing about W2 is reconstructed here (F2).
        w2 = build_w2(
            tuple(builds),
            inputs.to_inventory_records(outcome.inventory_records),
            labels=tuple(labels),
            circular_holidays=tuple(holidays),
        )
        fold, corpus_records = _corpus_reconciliation(declaration, outcome, w2)
        all_records.extend(corpus_records)
        _write_w2(writer, w2, fold)
        writer.write_jsonl("RECONCILIATION.jsonl", all_records)
        writer.write_jsonl("INPUT_MANIFEST.jsonl", input_manifest)
        print(
            "corpus: %d members, %d rows, %d quarantined, reconciliation %s"
            % (len(outcome.archives), rows_total, quarantined_total, reconcile.summarize(all_records))
        )

        stage = "evidence"
        archive_pairs = [
            (archive.root, archive.relative_path, outcome.inventory_index[
                (archive.root, archive.relative_path)]["sha256"])
            for archive in outcome.archives
        ]
        corpus_digest = identity.corpus_identity_digest(archive_pairs)
        runner_identity = identity.runner_identity_block()
        engine_identity = identity.engine_identity_block()
        composite = identity.composite_run_identity(
            engine_identity,
            runner_identity,
            governed_input_facts,
            corpus_digest,
            declaration.run_id,
            inputs.partition_definition(),
        )
        writer.write_json(
            "GOVERNED_INPUTS.json",
            {
                "contract_version": identity.CONTRACT_VERSION,
                "run_id": declaration.run_id,
                "files": sorted(governed_input_facts, key=lambda fact: (fact["role"], fact["path_label"])),
                "corpus": {
                    "root_labels": list(inputs.ROOT_LABELS),
                    "archive_count": len(outcome.archives),
                    "archive_set_digest": corpus_digest,
                    "hash_basis": "sha256 of sorted (root, relative_path, archive_sha256)",
                },
                "engine_identity": engine_identity,
                "runner_identity": runner_identity,
                "governed_config": DEFAULT_CONFIG.to_dict(),
                "config_fingerprint": DEFAULT_CONFIG.fingerprint(),
                "partition_definition": inputs.partition_definition(),
                "composite_run_identity": composite,
                "declared_expectations": {
                    "records": declaration.expect_records or None,
                    "inventory_lf_sha256": declaration.expect_inventory_lf_sha256 or None,
                    "tool_fingerprint": declaration.expect_tool_fingerprint or None,
                    "runner_fingerprint": declaration.expect_runner_fingerprint or None,
                    "min_free_bytes": declaration.min_free_bytes,
                },
                "hash_basis_notes": {
                    "archive_sha256": "D01-inventory value, independently recomputed from corpus bytes",
                    "member_sha256": "raw-bytes and lf-text (D05 §9.2 dual hash)",
                    "canonical_rows_jsonl": "run-metadata-excluded view (provenance.run_id excluded)",
                    "repository_files": "declared comparison basis is lf-text (CRLF-invariant)",
                },
            },
        )

        partition_summary = _partition_summary(input_manifest)
        summary = reconcile.summarize(all_records)
        writer.write_json(
            "RUN_RECORD.json",
            {
                "contract_version": identity.CONTRACT_VERSION,
                "run_id": declaration.run_id,
                "authority": {
                    "i4_execution": "D08 §13 (MD-13): non-production 10-year historical corpus replay — authorized",
                    "runner_implementation": "I4 runner implementation authorization (RD-1..RD-10, accepted)",
                    "excluded": [
                        "production execution",
                        "live NSE access",
                        "provider integration",
                        "credentials",
                        "storage-technology selection (MD-12 withheld; STORAGE TECHNOLOGY = UNDECIDED)",
                        "API implementation",
                        "UI implementation",
                        "product deployment",
                    ],
                },
                "boundary": {
                    "production": False,
                    "storage_technology": "UNDECIDED (MD-12; not selected, not implied, by this run)",
                    "traceability": "content-level under the adopted D05/W1 contract (MD-02 §4.3)",
                    "unresolved_semantics": "carried as evidence and never resolved (D08 §18)",
                    "network_access": "none (runner modules declare no network imports; preflight PF-03)",
                },
                "corpus": {
                    "root_labels": list(inputs.ROOT_LABELS),
                    "archive_count": len(outcome.archives),
                    "archive_set_digest": corpus_digest,
                    "partitions": partition_summary,
                    "partition_definition": inputs.partition_definition(),
                },
                "counts": {
                    "members": len(outcome.archives),
                    "rows": rows_total,
                    "quarantined": quarantined_total,
                    "observations": len(w2.observations),
                    "data_lines": sum(item["data_lines"] for item in input_manifest),
                },
                "engine_identity": engine_identity,
                "runner_identity": runner_identity,
                "config": {
                    "spec_version": contract.SPEC_VERSION,
                    "config_fingerprint": DEFAULT_CONFIG.fingerprint(),
                },
                "composite_run_identity": composite,
                "verification": {
                    "reconciliation": summary,
                    "preflight_checks": len(outcome.records),
                    "artifact_classes": [dict(rule) for rule in output.ARTIFACT_CLASS_RULES],
                    "replay_metadata_fields": list(contract.RUN_METADATA_FIELDS),
                },
            },
        )

        stage = "assembly"
        for family, year in sorted(partition_files):
            writer.write_manifest(
                output.OutputWriter.manifest_path(family, year), partition_files[(family, year)]
            )
        manifest_digest = writer.write_package_manifest()
        ok, detail = output.self_check(declaration.out)
        if not ok:
            raise output.OutputError("package self-check failed: %s" % detail)
        writer.write_completion(
            manifest_digest,
            {
                "contract_version": identity.CONTRACT_VERSION,
                "run_id": declaration.run_id,
                "status": "complete",
                "members": len(outcome.archives),
                "rows": rows_total,
                "quarantined": quarantined_total,
                "partitions": len(partition_summary),
                "reconciliation": summary,
                "note": (
                    "written last: presence of this marker means the package is complete and "
                    "self-checked; a package without it is incomplete by construction"
                ),
            },
        )
        print(
            "RUN COMPLETE :: run_id=%s members=%d rows=%d package_manifest=%s"
            % (declaration.run_id, len(outcome.archives), rows_total, manifest_digest)
        )
        return EXIT_OK
    except (inputs.GoverningFailure, output.OutputError, CalendarEvidenceError) as exc:
        _record_failure(writer, declaration, stage, processed, exc)
        print("RUN FAILED (%s): %s: %s" % (stage, type(exc).__name__, exc), file=sys.stderr)
        return EXIT_FAILED
    except NseEngineError as exc:
        _record_failure(writer, declaration, stage, processed, exc)
        print("RUN FAILED (%s): %s: %s" % (stage, type(exc).__name__, exc), file=sys.stderr)
        return EXIT_FAILED
    except KeyboardInterrupt:
        _record_failure(writer, declaration, stage, processed, inputs.GoverningFailure("interrupted"))
        print("RUN FAILED (interrupted)", file=sys.stderr)
        return EXIT_FAILED
    except Exception as exc:  # fail-closed: an unexpected defect must never look like success
        _record_failure(writer, declaration, stage, processed, exc)
        print(
            "RUN FAILED (%s): unexpected %s: %s" % (stage, type(exc).__name__, exc),
            file=sys.stderr,
        )
        return EXIT_FAILED


# ------------------------------------------------------------------ helpers


def _member_records(
    record, member_name, source, build, report, runner_raw_sha256, member_size, archive
) -> tuple:
    records = [
        reconcile.tier_a_member_identity(record, member_name),
        reconcile.tier_a_expected_source_date(record, member_name, source),
        reconcile.tier_a_archive_basis(record, member_name, source),
        reconcile.tier_a_archive_sha256(
            record, member_name, inputs.archive_sha256(archive.path)
        ),
        reconcile.tier_a_family(record, member_name, report["format_family"]),
        reconcile.tier_a_header_shape(record, member_name, report),
    ]
    records.extend(
        reconcile.tier_g_engine_member_hashes(
            record, member_name, report, runner_raw_sha256, member_size
        )
    )
    records.append(reconcile.tier_g_d01_header_list(record, member_name, report))
    records.extend(reconcile.tier_c_member_counters(record, member_name, build, report, build.rows))
    records.append(reconcile.tier_e_size_corroboration(record, member_name, archive.size_bytes))
    return tuple(records)


def _stem(file_name: str) -> str:
    return file_name[:-4] if file_name.lower().endswith(".zip") else file_name


def _load_labels(declaration):
    if not declaration.labels:
        return (), (), (), None
    labels, holidays, registry_ids, document = inputs.load_labels(declaration.labels)
    return labels, holidays, registry_ids, document


def _labels_facts(declaration, document) -> tuple:
    if not declaration.labels or document is None:
        return ()
    facts = []
    registry_ids = tuple(document.get("provenance", {}).get("circular_registry_ids", ()))
    facts.append(
        {
            "role": "calendar_label_registry_ids",
            "path_label": "(in DEC2_CAL_LABELS.json)",
            "present": True,
            "comparison_basis": "declared",
            "size_bytes": None,
            "raw_sha256": None,
            "lf_sha256": None,
            "git_blob_sha1": None,
            "count": len(registry_ids),
        }
    )
    return tuple(facts)


def _corpus_reconciliation(declaration, outcome, w2):
    records = []
    fold = None
    if outcome.present_inputs.get("d01_metric_evidence"):
        metric_records = inputs.load_metric_records(declaration.d01_metrics)
        fold = fold_file_metrics(metric_records)
        records.extend(
            reconcile.tier_c_corpus_fold(
                fold,
                w2.metrics.to_dict(),
                _path_label(declaration, declaration.d01_metrics),
            )
        )
    if outcome.present_inputs.get("d01_definition_verdict") and fold is not None:
        verdict_document = inputs.load_json_document(declaration.d01_verdict)
        records.append(
            reconcile.tier_g_verdict_vs_fold(
                verdict_document, fold, _path_label(declaration, declaration.d01_metrics)
            )
        )
    rows = w2.rows
    records.append(
        reconcile.make_record(
            reconcile.TIER_E,
            "flag_census",
            reconcile.corpus_scope("canonical-rows"),
            "count of canonical rows carrying each governed validity flag",
            "D05 §5 flags (informational; no flag gates anything; GATING_FLAG_NAMES is empty)",
            None,
            reconcile.flag_census(rows),
            reconcile.OBSERVED,
            reconcile.NON_GATING,
            note="observed census only; no D01 counterpart is asserted",
        )
    )
    records.append(
        reconcile.make_record(
            reconcile.TIER_E,
            "governance_dependency_census",
            reconcile.corpus_scope("canonical-rows"),
            "count of canonical rows carrying each unresolved-semantics identifier",
            "D07 §9 / D08 §18 (carried, never resolved)",
            None,
            reconcile.governance_dependency_census(rows),
            reconcile.OBSERVED,
            reconcile.NON_GATING,
            note="unresolved-state evidence (MD-11 #9)",
        )
    )
    return fold, tuple(records)


def _write_w2(writer, w2, fold) -> None:
    rows = w2.rows
    calendar_path = "w2/calendar.jsonl"
    for day in w2.calendar.days:
        writer.append_jsonl(calendar_path, day.to_dict())
    for identity_entry in w2.associations.identities:
        writer.append_jsonl("w2/associations.jsonl", identity_entry.to_dict())
    writer.close_jsonl()
    writer.write_json(
        "w2/identity_summary.json",
        {
            "method": w2.associations.method,
            "totals": w2.associations.totals(),
            "overlay_rows_excluded": [
                {"series": series, "rows": count}
                for series, count in w2.associations.overlay_rows_excluded
            ],
            "unkeyed": [group.to_dict() for group in w2.associations.unkeyed],
            "non_promotion_note": contract.IDENTITY_NON_PROMOTION_NOTE,
            "interval_rule": contract.ASSOCIATION_INTERVAL_RULE,
        },
    )
    writer.write_json(
        "w2/metrics.json",
        {
            "row_metrics": w2.metrics.to_dict(),
            "calendar_totals": w2.calendar.totals(),
            "label_status_counts": dict(w2.calendar.label_status_counts()),
            "d01_metric_fold": fold,
        },
    )
    for record in _unresolved_records(w2, rows):
        writer.append_jsonl("w2/unresolved.jsonl", record)
    writer.close_jsonl()


def _unresolved_records(w2, rows) -> tuple:
    records = []
    census = reconcile.governance_dependency_census(rows)
    for dependency_id in sorted(census):
        records.append(
            {
                "kind": "governance-dependency",
                "dependency_id": dependency_id,
                "label": contract.GOVERNANCE_DEPENDENCY_LABEL.get(dependency_id, ""),
                "row_count": census[dependency_id],
                "state": "unresolved (carried; never resolved by the runner)",
            }
        )
    records.append(
        {
            "kind": "calendar-label-status-counts",
            "counts": dict(w2.calendar.label_status_counts()),
            "unresolved_dependency": contract.CALENDAR_UNRESOLVED_DEPENDENCY,
            "state": "legacy-era gaps are not retrieved and their causes are never invented",
        }
    )
    for date in w2.calendar.unresolved_dates():
        records.append(
            {
                "kind": "calendar-unresolved-date",
                "trade_date": date,
                "label_status": contract.CALENDAR_LABEL_UNEXPLAINED,
                "dependency_id": contract.CALENDAR_UNRESOLVED_DEPENDENCY,
                "official_holiday_label": None,
                "state": "cause not assigned (D05 §3.4; D07-OPEN-8)",
            }
        )
    records.append(
        {
            "kind": "identity-non-promotion",
            "identities": w2.associations.totals()["identities"],
            "note": contract.IDENTITY_NON_PROMOTION_NOTE,
            "state": "correlation key is not promoted to exchange-authoritative identity",
        }
    )
    if w2.calendar.days:
        records.append(
            {
                "kind": "cross-era-boundary-residual",
                "first_date": w2.calendar.first_date,
                "last_date": w2.calendar.last_date,
                "note": (
                    "cross-era continuity policy is UNINTERPRETED (D08 §18); the run makes no "
                    "continuity claim and resolves no residual"
                ),
            }
        )
    return tuple(records)


def _partition_summary(input_manifest) -> tuple:
    summary = {}
    for item in input_manifest:
        entry = summary.setdefault(
            item["partition"], {"partition": item["partition"], "members": 0, "rows": 0}
        )
        entry["members"] += 1
        entry["rows"] += item["rows"]
    return tuple(summary[key] for key in sorted(summary))


def _path_label(declaration, path: str) -> str:
    try:
        relative = os.path.relpath(os.path.abspath(path), declaration.repo_root)
    except ValueError:
        return "(outside repo)"
    if relative.startswith(".."):
        return "(outside repo)"
    return relative.replace(os.sep, "/")


def _record_failure(writer, declaration, stage: str, processed: int, exc) -> None:
    """Retain failure evidence. No completion marker is ever written for a failed run."""
    if writer is None:
        print(
            "failure record not written: the declared output root is not an acceptable run root "
            "(%s): %s"
            % (declaration.out, "; ".join(preflight.output_root_contamination_problems(declaration))),
            file=sys.stderr,
        )
        return
    check = getattr(exc, "record", None)
    checks = getattr(exc, "records", None)
    try:
        if stage == "preflight" and checks:
            # Retain the preflight checks performed up to and including the failing one.
            writer.write_jsonl("PREFLIGHT.jsonl", checks)
        writer.write_failure(
            {
                "contract_version": identity.CONTRACT_VERSION,
                "run_id": declaration.run_id,
                "status": "failed",
                "stage": stage,
                "condition": "%s: %s" % (type(exc).__name__, exc),
                "failed_check": check,
                "preflight_checks_retained": len(checks) if checks else 0,
                "members_processed": processed,
                "note": (
                    "no completion marker was written; this package is incomplete and must not "
                    "be reused, repaired, appended to or verified as a complete run (RD-9)"
                ),
            }
        )
    except OSError:
        pass  # the failure is still reported on stderr with a non-zero exit code


# ------------------------------------------------------------------ verify / replay


def verify_command(args) -> int:
    result = output.verify_package(os.path.abspath(args.package))
    print(_json(result))
    return EXIT_OK if result["result"] == "pass" else EXIT_FAILED


def replay_command(args) -> int:
    try:
        result = output.replay_compare(os.path.abspath(args.a), os.path.abspath(args.b))
    except inputs.I4RunnerError as exc:
        print("replay error: %s" % exc, file=sys.stderr)
        return EXIT_USAGE
    if args.verdict:
        verdict_path = os.path.abspath(args.verdict)
        for package in (os.path.abspath(args.a), os.path.abspath(args.b)):
            if verdict_path == package or verdict_path.startswith(package + os.sep):
                print("replay error: verdict must be written outside both packages", file=sys.stderr)
                return EXIT_USAGE
        directory = os.path.dirname(verdict_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(verdict_path, "w", encoding="utf-8", newline="") as handle:
            handle.write(_json(result) + "\n")
    print(_json(result))
    return EXIT_OK if result["result"] == "pass" else EXIT_FAILED


def _json(document) -> str:
    from nse_engine.serialize import canonical_json

    return canonical_json(document)


# ------------------------------------------------------------------ CLI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="i4_runner",
        description=(
            "I4 corpus-side runner (non-production). Orchestrates the unmodified engine over "
            "the governed corpus and writes a deterministic, clock-free evidence package."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="preflight + corpus run + package assembly")
    run.add_argument("--legacy-root", required=True, help="LEGACY corpus archives root (read-only)")
    run.add_argument("--udiff-root", required=True, help="UDIFF corpus archives root (read-only)")
    run.add_argument("--out", required=True, help="run output root (new or empty; outside the corpus)")
    run.add_argument("--run-id", required=True, help="declared clock-free run id (RD-10)")
    run.add_argument("--inventory", required=True, help="governed D01 inventory JSON")
    run.add_argument("--labels", default="", help="governed calendar labels (DEC2_CAL_LABELS.json)")
    run.add_argument("--d01-metrics", default="", help="frozen per-file D01 metric evidence CSV")
    run.add_argument("--d01-verdict", default="", help="frozen D01 definition verdict JSON")
    run.add_argument("--series-universe", default="", help="D02 series universe evidence (carried)")
    run.add_argument("--series-rollup", default="", help="D02 series class rollup evidence (carried)")
    run.add_argument("--repo-root", default="", help="repository root (default: derived from the runner)")
    run.add_argument("--expect-records", type=int, default=0, help="declared inventory record count")
    run.add_argument("--expect-inventory-lf-sha256", default="", help="declared inventory LF sha256")
    run.add_argument("--expect-tool-fingerprint", default="", help="declared engine fingerprint")
    run.add_argument("--expect-runner-fingerprint", default="", help="declared runner fingerprint")
    run.add_argument("--min-free-bytes", type=int, default=0, help="declared free-space threshold")
    run.set_defaults(func=run_command)

    verify = subparsers.add_parser("verify", help="verify a completed package against its manifests")
    verify.add_argument("--package", required=True, help="package directory")
    verify.set_defaults(func=verify_command)

    replay = subparsers.add_parser("replay", help="byte-compare two packages (determinism evidence)")
    replay.add_argument("--a", required=True, help="first package directory")
    replay.add_argument("--b", required=True, help="second package directory")
    replay.add_argument("--verdict", default="", help="optional verdict file (outside both packages)")
    replay.set_defaults(func=replay_command)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except inputs.I4RunnerError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
