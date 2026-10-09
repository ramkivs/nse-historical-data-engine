"""I4 replay qualification gate tests (corrections K1/K2/K3) — synthetic fixtures only.

These tests exercise `tools/i4_m2/i4_replay_qualification.py`, the qualification layer that sits
between the runner's `verify`/`replay` commands and the acceptance of a replay verdict:

* **K1** — no byte comparison is permitted unless both packages pass the existing package
  verification and carry a completion marker bound to their manifest;
* **K2** — both runs must share one declared revision/run-id/corpus identity;
* **K3** — each package must carry its own execution-evidence bundle (facts, monitor summary,
  monitor trace, package listing), so a byte copy of package A cannot be presented as a replay.

The evidence bundles built here follow the *documented contract* of the delivered Phase-I
evidence script (`I4_M2_EVIDENCE_WINDOWS.ps1`) and of the memory monitor's summary and trace
(`<prefix>.summary.json`, `<prefix>.jsonl`). They are synthetic documents produced in a
temporary directory: **they prove the procedural precondition is enforceable and satisfiable,
and they prove nothing about any Windows execution.** No test reads ``C:\\IIPS_Data`` or
``G:\\My Engines``, and no test executes the governed corpus.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.i4_m2 import i4_replay_qualification as qualification  # noqa: E402
from tools.i4_runner import i4_output, i4_runner  # noqa: E402

from tests.test_i4_runner import DEFAULT_SPECS, Corpus  # noqa: E402

RUN_ID = "i4-qualification-test"
M2_REVISION_COMMIT = "8ade8372e150e541a52206baa377a02249a308f4"
M2_REVISION_TREE = "8e1557de766d4c952be7261c4f72aa743f81de0b"
M2_ENGINE_FINGERPRINT = "d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9"
M2_RUNNER_FINGERPRINT = "f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a"
PRE_M1_ENGINE_FINGERPRINT = "7bee84902f8cb0e5c60703acbe1b17d6e85a9b9762289bab1741d9f003df5a52"
PRE_M1_RUNNER_FINGERPRINT = "618bfd4c4919f3224a3e0f64682c21617c356580ebccd807f8abce528302c904"
SAMPLE_COUNT = 24


# ------------------------------------------------------------------ fixture helpers


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, document):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(i4_output.canonical_json(document) + "\n")


def rebuild_manifests(package):
    """Re-derive every manifest and the marker from the package's current bytes.

    Used to build the adversarial case the gate must still catch: a package that is internally
    consistent again (verification passes) but is no longer byte-identical to its baseline.
    """

    def rebuild(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as handle:
            lines = [line for line in handle.read().splitlines() if line]
        rebuilt = []
        for line in lines:
            _digest, relative = line.split("  ", 1)
            rebuilt.append(i4_output.manifest_line(relative, sha256_file(os.path.join(package, relative))))
        with open(manifest_path, "w", encoding="utf-8", newline="") as handle:
            handle.write("".join(rebuilt))

    manifest_path = os.path.join(package, i4_output.PACKAGE_MANIFEST)
    with open(manifest_path, "r", encoding="utf-8") as handle:
        entries = [line.split("  ", 1)[1] for line in handle.read().splitlines() if line]
    partition_manifests = [
        relative for relative in entries if relative.startswith("manifests/") and relative.endswith(".sha256")
    ]
    for _round in range(2):
        for relative in partition_manifests:
            rebuild(os.path.join(package, relative))
        rebuild(manifest_path)
    marker_path = os.path.join(package, i4_output.COMPLETION_MARKER)
    marker = read_json(marker_path)
    marker["package_manifest_sha256"] = sha256_file(manifest_path)
    write_json(marker_path, marker)


def package_files(package):
    files = {}
    for dirpath, _dirnames, filenames in os.walk(package):
        for name in filenames:
            path = os.path.join(dirpath, name)
            files[os.path.relpath(path, package).replace(os.sep, "/")] = (
                os.path.getsize(path),
                sha256_file(path),
            )
    return files


def tree_digest(package):
    digest = hashlib.sha256()
    for relative, (_size, file_digest) in sorted(package_files(package).items()):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(file_digest.encode("ascii"))
        digest.update(b"\x00")
    return digest.hexdigest()


# ------------------------------------------------------------------ test case


class QualificationTestCase(unittest.TestCase):
    """Builds verified packages plus their synthetic evidence bundles."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="i4-qual-test-")
        self.addCleanup(shutil.rmtree, self._tmp, True)
        self.corpus = Corpus(os.path.join(self._tmp, "corpus"), DEFAULT_SPECS)

    # -- packages -------------------------------------------------------------
    def make_package(self, name, run_id=RUN_ID):
        out = os.path.join(self._tmp, name)
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = i4_runner.main(self.corpus.run_args(out, run_id=run_id))
        self.assertEqual(code, i4_runner.EXIT_OK, stderr.getvalue())
        self.assertEqual(i4_output.verify_package(out)["result"], "pass")
        return out

    def copy_package(self, source, name):
        target = os.path.join(self._tmp, name)
        shutil.copytree(source, target)
        return target

    # -- evidence bundles -----------------------------------------------------
    def write_evidence(self, package, prefix, run_id=RUN_ID, mutate=None, peak_rss=318.1, exit_code=None):
        """Write the four evidence documents the delivered tooling produces for one run.

        `mutate` is an optional callable(documents) that perturbs the synthetic documents so a
        test can model a specific deviation (breach, exit code, stale listing, broken trace, ...).
        """
        paths = {
            "facts": os.path.join(self._tmp, "%s.EVIDENCE_FACTS.json" % prefix),
            "summary": os.path.join(self._tmp, "%s.summary.json" % prefix),
            "trace": os.path.join(self._tmp, "%s.jsonl" % prefix),
            "listing": os.path.join(self._tmp, "%s.PACKAGE_FILES.tsv" % prefix),
        }
        record = read_json(os.path.join(package, "RUN_RECORD.json"))
        marker_path = os.path.join(package, i4_output.COMPLETION_MARKER)
        manifest_path = os.path.join(package, i4_output.PACKAGE_MANIFEST)
        reconciliation_path = os.path.join(package, "RECONCILIATION.jsonl")
        entries = package_files(package)
        out_root = os.path.join("G:\\My Engines\\I4_RUNS", os.path.basename(package))

        rss_values = [round(64.0 + (peak_rss - 64.0) * index / SAMPLE_COUNT, 1) for index in range(1, SAMPLE_COUNT + 1)]
        available_values = [round(2048.0 - index * 1.5, 1) for index in range(1, SAMPLE_COUNT + 1)]
        # Two genuine runs never produce the same transcript: the monitor stamps wall-clock time
        # and the runner's process id into every sample. The fixture models that by deriving a
        # stable per-run stamp from the prefix.
        stamp = int(hashlib.sha256(prefix.encode("utf-8")).hexdigest()[:6], 16)
        runner_pid = 4000 + stamp % 1000
        at_hour = 10 + stamp % 6
        trace = [
            {
                "at": "2026-10-08T%02d:%02d:%02d.0000000+05:30" % (at_hour + index // 60, index % 60, index % 60),
                "sample": index + 1,
                "runner_pid": runner_pid,
                "rss_mb": rss_values[index],
                "available_mb": available_values[index],
                "free_disk_bytes": 18000000000,
                "sampling_failures": 0,
            }
            for index in range(SAMPLE_COUNT)
        ]
        facts = {
            "repo_head": M2_REVISION_COMMIT,
            "repo_tree": M2_REVISION_TREE,
            "repo_status_entries": 0,
            "engine_fingerprint": record["engine_identity"]["tool_sha256"],
            "runner_fingerprint": record["runner_identity"]["runner_sha256"],
            "run_id": run_id,
            "out_root": out_root,
            "completion_marker_present": True,
            "completion_marker_sha256": sha256_file(marker_path),
            "run_record_sha256": sha256_file(os.path.join(package, "RUN_RECORD.json")),
            "record_members": record["counts"]["members"],
            "record_rows": record["counts"]["rows"],
            "record_observations": record["counts"]["observations"],
            "record_quarantined": record["counts"]["quarantined"],
            "record_engine_tool_sha256": record["engine_identity"]["tool_sha256"],
            "record_runner_sha256": record["runner_identity"]["runner_sha256"],
            "record_composite_identity": record["composite_run_identity"],
            "record_archive_set_digest": record["corpus"]["archive_set_digest"],
            "package_manifest_sha256": sha256_file(manifest_path),
            "package_file_count": len(entries),
            "package_total_bytes": sum(size for size, _digest in entries.values()),
            "reconciliation_sha256": sha256_file(reconciliation_path),
            "peak_process_rss_mb": max(rss_values),
            "rss_limit_mb": 6144,
            "rss_breach": False,
            "monitor_summary_path": paths["summary"],
            "result": "PASS",
            "problems": [],
        }
        summary = {
            "recorded_at": "2026-10-08T00:00:00.0000000+05:30",
            "run_id": run_id,
            "out_root": out_root,
            "rss_limit_mb": 6144,
            "available_floor_mb": 1024,
            "min_free_bytes": 15000000000,
            "sample_seconds": 5,
            "samples": SAMPLE_COUNT,
            "peak_rss_mb": max(rss_values),
            "min_available_mb": min(available_values),
            "min_free_disk_bytes": 18000000000,
            "breach": False,
            "breach_reason": "",
            "runner_exit_code": exit_code,
            "completion_marker_present": True,
        }
        listing = ["path\tsize_bytes\tsha256"]
        for relative in sorted(entries):
            size, digest = entries[relative]
            listing.append("%s\t%d\t%s" % (relative, size, digest))

        documents = {"facts": facts, "summary": summary, "trace": trace, "listing": listing}
        if mutate is not None:
            mutate(documents)

        write_json(paths["facts"], documents["facts"])
        write_json(paths["summary"], documents["summary"])
        with open(paths["trace"], "w", encoding="utf-8", newline="") as handle:
            for sample in documents["trace"]:
                handle.write(i4_output.canonical_json(sample) + "\n")
        with open(paths["listing"], "w", encoding="utf-8", newline="") as handle:
            handle.write("\r\n".join(documents["listing"]) + "\r\n")

        return qualification.load_evidence(
            paths["facts"], paths["summary"], paths["listing"], paths["trace"], prefix
        )

    def evidence_paths(self, prefix):
        return {
            "facts": os.path.join(self._tmp, "%s.EVIDENCE_FACTS.json" % prefix),
            "summary": os.path.join(self._tmp, "%s.summary.json" % prefix),
            "trace": os.path.join(self._tmp, "%s.jsonl" % prefix),
            "listing": os.path.join(self._tmp, "%s.PACKAGE_FILES.tsv" % prefix),
        }

    def load_evidence(self, prefix):
        paths = self.evidence_paths(prefix)
        return qualification.load_evidence(
            paths["facts"], paths["summary"], paths["listing"], paths["trace"], prefix
        )

    # -- invocation -----------------------------------------------------------
    def expectation(self, package_a, **overrides):
        record = read_json(os.path.join(package_a, "RUN_RECORD.json"))
        values = {
            "repository": "ramkivs/nse-historical-data-engine",
            "ref": "arena/9021d1a1-nse-historical-data-engine",
            "commit": M2_REVISION_COMMIT,
            "tree": M2_REVISION_TREE,
            "engine_fingerprint": record["engine_identity"]["tool_sha256"],
            "runner_fingerprint": record["runner_identity"]["runner_sha256"],
            "run_id": record["run_id"],
            "corpus_archive_set_digest": record["corpus"]["archive_set_digest"],
        }
        values.update(overrides)
        return qualification.RevisionExpectation(**values)

    def qualify(self, package_a, package_b, evidence_a, evidence_b, expected, **kwargs):
        problem_a = evidence_a[1] if isinstance(evidence_a, tuple) else None
        problem_b = evidence_b[1] if isinstance(evidence_b, tuple) else None
        return qualification.qualification_report(
            package_a,
            package_b,
            evidence_a[0] if isinstance(evidence_a, tuple) else evidence_a,
            evidence_b[0] if isinstance(evidence_b, tuple) else evidence_b,
            problem_a,
            problem_b,
            expected,
            **kwargs,
        )

    def cli(self, package_a, package_b, prefix_a="a", prefix_b="b", expected=None, verdict=None, **extra):
        expected = expected or self.expectation(package_a)
        arguments = [
            "--a", package_a, "--b", package_b,
            "--facts-a", self.evidence_paths(prefix_a)["facts"],
            "--facts-b", self.evidence_paths(prefix_b)["facts"],
            "--summary-a", self.evidence_paths(prefix_a)["summary"],
            "--summary-b", self.evidence_paths(prefix_b)["summary"],
            "--trace-a", self.evidence_paths(prefix_a)["trace"],
            "--trace-b", self.evidence_paths(prefix_b)["trace"],
            "--listing-a", self.evidence_paths(prefix_a)["listing"],
            "--listing-b", self.evidence_paths(prefix_b)["listing"],
            "--expect-repository", expected.repository,
            "--expect-ref", expected.ref,
            "--expect-commit", expected.commit,
            "--expect-tree", expected.tree,
            "--expect-engine-fingerprint", expected.engine_fingerprint,
            "--expect-runner-fingerprint", expected.runner_fingerprint,
            "--expect-run-id", expected.run_id,
            "--expect-corpus-archive-set-digest", expected.corpus_archive_set_digest,
        ]
        if expected.require_same_recorded_head:
            arguments.append("--strict-recorded-head")
        for name, value in extra.items():
            arguments.extend(["--" + name.replace("_", "-"), str(value)])
        if verdict:
            arguments.extend(["--verdict", verdict])
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = qualification.main(arguments)
        self.last_stdout = stdout.getvalue()
        return code

    def check(self, report, check_id):
        for record in report["checks"]:
            if record["check_id"] == check_id:
                return record
        raise AssertionError("check %s not present" % check_id)


# ------------------------------------------------------------------ K1


class CompletenessPreconditionTests(QualificationTestCase):
    """K1 — no comparison without two complete, verified packages."""

    def test_two_complete_packages_are_qualified_and_comparison_runs(self):
        a = self.make_package("pkg_a")
        b = self.make_package("pkg_b")
        evidence_a = self.write_evidence(a, "a")
        evidence_b = self.write_evidence(b, "b")

        report = self.qualify(a, b, evidence_a, evidence_b, self.expectation(a))

        self.assertEqual(report["result"], "pass", report["failures"])
        self.assertTrue(report["comparison_permitted"])
        self.assertEqual(report["comparison"]["result"], "pass")
        self.assertEqual(self.check(report, "RQ-13")["result"], "pass")

    def test_incomplete_package_a_fails_and_the_comparison_is_not_executed(self):
        a = self.make_package("pkg_a")
        b = self.make_package("pkg_b")
        evidence_a = self.write_evidence(a, "a")
        evidence_b = self.write_evidence(b, "b")
        os.remove(os.path.join(a, i4_output.COMPLETION_MARKER))

        report = self.qualify(a, b, evidence_a, evidence_b, self.expectation(a))

        self.assertEqual(report["result"], "fail")
        self.assertFalse(report["comparison_permitted"])
        self.assertIsNone(report["comparison"], "the comparison must not be executed at all")
        self.assertEqual(self.check(report, "RQ-13")["result"], "not-run")
        self.assertIn("RQ-01", report["failures"])

    def test_incomplete_package_b_fails(self):
        a = self.make_package("pkg_a")
        b = self.make_package("pkg_b")
        evidence_a = self.write_evidence(a, "a")
        evidence_b = self.write_evidence(b, "b")
        os.remove(os.path.join(b, i4_output.COMPLETION_MARKER))

        report = self.qualify(a, b, evidence_a, evidence_b, self.expectation(a))

        self.assertEqual(report["result"], "fail")
        self.assertIsNone(report["comparison"])
        self.assertIn("RQ-02", report["failures"])

    def test_missing_completion_marker_is_reported_by_name(self):
        a = self.make_package("pkg_a")
        b = self.make_package("pkg_b")
        evidence_a = self.write_evidence(a, "a")
        evidence_b = self.write_evidence(b, "b")
        os.remove(os.path.join(b, i4_output.COMPLETION_MARKER))

        report = self.qualify(a, b, evidence_a, evidence_b, self.expectation(a))

        self.assertIn("verify-04", self.check(report, "RQ-02")["observed"]["failures"])
        self.assertFalse(self.check(report, "RQ-08")["observed"]["b"]["bound"])
        self.assertIn("RUN_COMPLETE.json", report["packages"]["b"]["completion_marker_problem"])
        self.assertIn("unavailable", report["packages"]["b"]["completion_marker_problem"])

    def test_marker_not_bound_to_the_manifest_fails(self):
        a = self.make_package("pkg_a")
        b = self.make_package("pkg_b")
        evidence_a = self.write_evidence(a, "a")
        evidence_b = self.write_evidence(b, "b")
        marker_path = os.path.join(b, i4_output.COMPLETION_MARKER)
        marker = read_json(marker_path)
        marker["package_manifest_sha256"] = "0" * 64
        write_json(marker_path, marker)

        report = self.qualify(a, b, evidence_a, evidence_b, self.expectation(a))

        self.assertEqual(report["result"], "fail")
        self.assertIn("verify-04", self.check(report, "RQ-02")["observed"]["failures"])
        self.assertFalse(self.check(report, "RQ-08")["observed"]["b"]["bound"])

    def test_corrupted_package_fails_either_side(self):
        for side in ("a", "b"):
            with self.subTest(side=side):
                a = self.make_package("pkg_a_%s" % side)
                b = self.make_package("pkg_b_%s" % side)
                evidence_a = self.write_evidence(a, "a_%s" % side)
                evidence_b = self.write_evidence(b, "b_%s" % side)
                target = os.path.join(b if side == "b" else a, "w2", "metrics.json")
                with open(target, "ab") as handle:
                    handle.write(b"\n")

                report = self.qualify(a, b, evidence_a, evidence_b, self.expectation(a))

                self.assertEqual(report["result"], "fail")
                self.assertIsNone(report["comparison"])
                self.assertIn(
                    "verify-02",
                    self.check(report, "RQ-02" if side == "b" else "RQ-01")["observed"]["failures"],
                )

    def test_internally_consistent_tamper_is_caught_by_the_comparison(self):
        """Verification passes because the manifests were rebuilt — replay still fails."""
        a = self.make_package("pkg_a")
        b = self.make_package("pkg_b")
        self.assertEqual(tree_digest(a), tree_digest(b))
        target = os.path.join(b, "partitions", "legacy13", "2024", "rows", "cm01JUL2024bhav.csv.rows.jsonl")
        with open(target, "ab") as handle:
            handle.write(b"\n")
        rebuild_manifests(b)
        self.assertEqual(i4_output.verify_package(b)["result"], "pass")
        evidence_a = self.write_evidence(a, "a")
        evidence_b = self.write_evidence(b, "b")

        report = self.qualify(a, b, evidence_a, evidence_b, self.expectation(a))

        self.assertTrue(report["comparison_permitted"])
        self.assertEqual(report["result"], "fail")
        comparison = self.check(report, "RQ-13")["observed"]
        self.assertEqual(comparison["result"], "fail")
        self.assertIn(
            "partitions/legacy13/2024/rows/cm01JUL2024bhav.csv.rows.jsonl",
            comparison["first_difference"]["differing"],
        )

    def test_every_artifact_mutated_one_at_a_time_is_caught(self):
        """Artifact-by-artifact coverage: no artifact of the package escapes the gate."""
        a = self.make_package("pkg_a")
        baseline = self.make_package("pkg_b")
        evidence_a = self.write_evidence(a, "a")
        files = sorted(package_files(a))
        self.assertGreaterEqual(len(files), 20)
        for index, relative in enumerate(files):
            with self.subTest(artifact=relative):
                b = self.copy_package(baseline, "pkg_b_mutated_%02d" % index)
                try:
                    target = os.path.join(b, relative.replace("/", os.sep))
                    with open(target, "ab") as handle:
                        handle.write(b"\n")
                    evidence_b = self.write_evidence(b, "b_mutated_%02d" % index)
                    report = self.qualify(a, b, evidence_a, evidence_b, self.expectation(a))
                    self.assertEqual(report["result"], "fail", "artifact %s escaped the gate" % relative)
                    if report["comparison_permitted"]:
                        comparison = self.check(report, "RQ-13")["observed"]
                        self.assertEqual(comparison["result"], "fail")
                        self.assertIn(relative, comparison["first_difference"]["differing"])
                    else:
                        # a mutation of a manifest/marker artifact is caught by K1 verification
                        self.assertIn("RQ-02", report["failures"])
                finally:
                    shutil.rmtree(b, True)

    def test_unlisted_extra_file_fails(self):
        a = self.make_package("pkg_a")
        b = self.make_package("pkg_b")
        evidence_a = self.write_evidence(a, "a")
        with open(os.path.join(b, "extra_artifact.json"), "w", encoding="utf-8") as handle:
            handle.write("{}\n")
        evidence_b = self.write_evidence(b, "b")

        report = self.qualify(a, b, evidence_a, evidence_b, self.expectation(a))

        self.assertEqual(report["result"], "fail")
        self.assertIsNone(report["comparison"])
        self.assertIn("verify-03", self.check(report, "RQ-02")["observed"]["failures"])

    def test_hidden_unlisted_file_fails(self):
        a = self.make_package("pkg_a")
        b = self.make_package("pkg_b")
        evidence_a = self.write_evidence(a, "a")
        with open(os.path.join(b, ".hidden"), "w", encoding="utf-8") as handle:
            handle.write("x\n")
        evidence_b = self.write_evidence(b, "b")

        report = self.qualify(a, b, evidence_a, evidence_b, self.expectation(a))

        self.assertEqual(report["result"], "fail")
        self.assertIsNone(report["comparison"])

    def test_removed_artifact_fails(self):
        a = self.make_package("pkg_a")
        b = self.make_package("pkg_b")
        evidence_a = self.write_evidence(a, "a")
        os.remove(os.path.join(b, "w2", "metrics.json"))
        evidence_b = self.write_evidence(b, "b")

        report = self.qualify(a, b, evidence_a, evidence_b, self.expectation(a))

        self.assertEqual(report["result"], "fail")
        self.assertIsNone(report["comparison"])

    def test_run_id_difference_fails(self):
        """A different run id must fail (the run id is the one declared run-metadata field)."""
        a = self.make_package("pkg_a")
        b = self.make_package("pkg_b", run_id="i4-qualification-test-OTHER")
        evidence_a = self.write_evidence(a, "a")
        evidence_b = self.write_evidence(b, "b", run_id="i4-qualification-test-OTHER")
        expected = self.expectation(a)

        report = self.qualify(a, b, evidence_a, evidence_b, expected)

        self.assertEqual(report["result"], "fail")
        self.assertIn("RQ-03", report["failures"])


# ------------------------------------------------------------------ K2


class RevisionPinTests(QualificationTestCase):
    """K2 — one declared revision, run id and corpus identity for both runs."""

    def setUp(self):
        super().setUp()
        self.a = self.make_package("pkg_a")
        self.b = self.make_package("pkg_b")
        self.evidence_a = self.write_evidence(self.a, "a")
        self.evidence_b = self.write_evidence(self.b, "b")

    def test_matching_revision_and_fingerprints_pass(self):
        report = self.qualify(self.a, self.b, self.evidence_a, self.evidence_b, self.expectation(self.a))
        self.assertEqual(report["result"], "pass", report["failures"])
        for check_id in ("RQ-03", "RQ-04", "RQ-05", "RQ-06", "RQ-07", "RQ-12"):
            self.assertEqual(self.check(report, check_id)["result"], "pass", check_id)

    def test_engine_fingerprint_mismatch_fails(self):
        expected = self.expectation(self.a, engine_fingerprint="0" * 64)
        report = self.qualify(self.a, self.b, self.evidence_a, self.evidence_b, expected)
        self.assertEqual(report["result"], "fail")
        self.assertIn("RQ-04", report["failures"])
        self.assertIsNone(report["comparison"])

    def test_runner_fingerprint_mismatch_fails(self):
        expected = self.expectation(self.a, runner_fingerprint="f" * 64)
        report = self.qualify(self.a, self.b, self.evidence_a, self.evidence_b, expected)
        self.assertEqual(report["result"], "fail")
        self.assertIn("RQ-05", report["failures"])

    def test_pre_m1_main_revision_fingerprints_fail_closed(self):
        """`origin/main` (6a60583f, pre-bounded-memory) must never qualify as the replay revision."""
        expected = self.expectation(
            self.a,
            engine_fingerprint=PRE_M1_ENGINE_FINGERPRINT,
            runner_fingerprint=PRE_M1_RUNNER_FINGERPRINT,
        )
        report = self.qualify(self.a, self.b, self.evidence_a, self.evidence_b, expected)
        self.assertEqual(report["result"], "fail")
        self.assertEqual(self.check(report, "RQ-04")["observed"]["expected"][:8], "7bee8490")
        self.assertEqual(self.check(report, "RQ-05")["observed"]["expected"][:8], "618bfd4c")

    def test_run_id_mismatch_fails(self):
        expected = self.expectation(self.a, run_id="i4-some-other-run")
        report = self.qualify(self.a, self.b, self.evidence_a, self.evidence_b, expected)
        self.assertEqual(report["result"], "fail")
        self.assertIn("RQ-03", report["failures"])

    def test_corpus_identity_mismatch_fails(self):
        expected = self.expectation(self.a, corpus_archive_set_digest="1" * 64)
        report = self.qualify(self.a, self.b, self.evidence_a, self.evidence_b, expected)
        self.assertEqual(report["result"], "fail")
        self.assertIn("RQ-06", report["failures"])

    def test_recorded_host_revision_mismatch_fails(self):
        evidence_b = self.write_evidence(
            self.b,
            "b_other_head",
            mutate=lambda document: document["facts"].update(
                {"repo_head": "6a60583f62905c1fbda9cc7529019e2a9ed0b097",
                 "repo_tree": "ad882becd89992e3c62a2bdff00a78bc6d80dbc0"}
            ),
        )
        report = self.qualify(self.a, self.b, self.evidence_a, evidence_b, self.expectation(self.a))
        self.assertEqual(report["result"], "fail")
        self.assertIn("RQ-12", report["failures"])

    def test_strict_recorded_head_requires_the_declared_revision(self):
        evidence_a = self.write_evidence(
            self.a,
            "a_other_head",
            mutate=lambda document: document["facts"].update(
                {"repo_head": "6a60583f62905c1fbda9cc7529019e2a9ed0b097",
                 "repo_tree": "ad882becd89992e3c62a2bdff00a78bc6d80dbc0"}
            ),
        )
        expected = self.expectation(self.a, require_same_recorded_head=True)
        report = self.qualify(self.a, self.b, evidence_a, self.evidence_b, expected)
        self.assertEqual(report["result"], "fail")
        self.assertIn("RQ-12", report["failures"])

    def test_revision_record_is_captured_in_the_report(self):
        report = self.qualify(self.a, self.b, self.evidence_a, self.evidence_b, self.expectation(self.a))
        revision = report["revision"]
        self.assertEqual(revision["repository"], "ramkivs/nse-historical-data-engine")
        self.assertEqual(revision["revision_commit"], M2_REVISION_COMMIT)
        self.assertEqual(revision["revision_tree"], M2_REVISION_TREE)
        self.assertEqual(revision["run_id"], RUN_ID)
        self.assertEqual(revision["engine_fingerprint"][:8], "d3269b73")
        self.assertEqual(revision["runner_fingerprint"][:8], "f3ebf624")
        self.assertIn("composite_run_identity", report["packages"]["a"])


# ------------------------------------------------------------------ K3


class ExecutionEvidenceTests(QualificationTestCase):
    """K3 — a copy of A is not a replay; the execution-evidence bundle is the discriminator."""

    def setUp(self):
        super().setUp()
        self.a = self.make_package("pkg_a")
        self.evidence_a = self.write_evidence(self.a, "a")

    def test_copy_of_a_without_evidence_bundle_is_not_qualified(self):
        b = self.copy_package(self.a, "pkg_b")
        self.assertEqual(tree_digest(a := self.a), tree_digest(b), "the copy is byte-identical")
        self.assertEqual(i4_output.verify_package(b)["result"], "pass")
        missing = os.path.join(self._tmp, "missing")
        evidence_b, problem = qualification.load_evidence(
            missing + ".EVIDENCE_FACTS.json", missing + ".summary.json", missing + ".tsv", missing + ".jsonl", "package B"
        )
        self.assertIsNone(evidence_b)
        report = self.qualify(self.a, b, self.evidence_a, (evidence_b, problem), self.expectation(self.a))
        self.assertEqual(report["result"], "fail")
        self.assertIn("RQ-10", report["failures"])
        self.assertIsNone(report["comparison"])
        self.assertFalse(self.check(report, "RQ-10")["observed"]["evidence_bundle_available"]["result"])

    def test_copy_of_a_with_as_evidence_reused_is_not_qualified(self):
        b = self.copy_package(self.a, "pkg_b")
        report = self.qualify(self.a, b, self.evidence_a, self.evidence_a, self.expectation(self.a))
        self.assertEqual(report["result"], "fail")
        self.assertIn("RQ-10", report["failures"])
        self.assertIn("RQ-11", report["failures"])
        binding = self.check(report, "RQ-10")["observed"]
        self.assertFalse(binding["out_root_binds_to_package"]["result"])
        self.assertTrue(binding["package_listing_covers_package"]["result"])
        self.assertTrue(self.check(report, "RQ-11")["observed"]["monitor_trace_identical"])

    def test_transcript_reuse_is_detected_for_each_document(self):
        for document in ("facts", "summary", "trace"):
            with self.subTest(document=document):
                b = self.copy_package(self.a, "pkg_b_reuse_%s" % document)
                evidence_b = self.write_evidence(b, "b_reuse_%s" % document)
                # overwrite B's document with A's bytes: a transcript carrying A's root/host/time
                shutil.copyfile(self.evidence_paths("a")[document], self.evidence_paths("b_reuse_%s" % document)[document])
                evidence_b = self.load_evidence("b_reuse_%s" % document)
                report = self.qualify(self.a, b, self.evidence_a, evidence_b, self.expectation(self.a))
                self.assertEqual(report["result"], "fail")
                self.assertIn("RQ-11", report["failures"])
                self.assertTrue(
                    self.check(report, "RQ-11")["observed"][
                        {
                            "facts": "evidence_facts_identical",
                            "summary": "monitor_summary_identical",
                            "trace": "monitor_trace_identical",
                        }[document]
                    ]
                )
                shutil.rmtree(b, True)

    def test_copy_of_a_with_its_own_execution_evidence_satisfies_the_procedure(self):
        """The procedural preconditions are satisfiable for a genuine second run.

        This asserts only that the gate's requirements are enforceable and satisfiable: a package
        accompanied by a complete, package-bound execution-evidence bundle passes K3. Whether that
        bundle was genuinely produced by an execution on the Windows host is an operator
        attestation the gate cannot cryptographically verify — recorded as a residual limit in the
        correction record.
        """
        b = self.copy_package(self.a, "pkg_b")
        evidence_b = self.write_evidence(b, "b")
        report = self.qualify(self.a, b, self.evidence_a, evidence_b, self.expectation(self.a))
        self.assertEqual(report["result"], "pass", report["failures"])
        self.assertTrue(report["comparison_permitted"])
        self.assertEqual(report["comparison"]["result"], "pass")
        for key in ("evidence_facts_sha256", "monitor_summary_sha256", "monitor_log_sha256"):
            self.assertNotEqual(report["evidence"]["a"][key], report["evidence"]["b"][key])
        # the listing is a deterministic function of the package and is expected to be identical
        self.assertEqual(report["evidence"]["a"]["package_listing_sha256"],
                         report["evidence"]["b"]["package_listing_sha256"])

    def test_monitor_breach_is_not_qualified(self):
        b = self.copy_package(self.a, "pkg_b")

        def breach(document):
            document["summary"]["breach"] = True
            document["summary"]["breach_reason"] = "synthetic breach"

        evidence_b = self.write_evidence(b, "b", mutate=breach)
        report = self.qualify(self.a, b, self.evidence_a, evidence_b, self.expectation(self.a))
        self.assertEqual(report["result"], "fail")
        self.assertFalse(self.check(report, "RQ-10")["observed"]["monitor_no_breach"]["result"])

    def test_monitor_nonzero_exit_code_is_not_qualified(self):
        b = self.copy_package(self.a, "pkg_b")
        evidence_b = self.write_evidence(b, "b", exit_code=3)
        report = self.qualify(self.a, b, self.evidence_a, evidence_b, self.expectation(self.a))
        self.assertEqual(report["result"], "fail")
        self.assertFalse(self.check(report, "RQ-10")["observed"]["monitor_runner_exit_code"]["result"])

    def test_monitor_null_exit_code_is_accepted_and_recorded(self):
        """The documented M2 anomaly: a null runner exit code is carried, never reinterpreted."""
        b = self.copy_package(self.a, "pkg_b")
        evidence_b = self.write_evidence(b, "b", exit_code=None)
        report = self.qualify(self.a, b, self.evidence_a, evidence_b, self.expectation(self.a))
        self.assertEqual(report["result"], "pass", report["failures"])
        observed = self.check(report, "RQ-10")["observed"]["monitor_runner_exit_code"]
        self.assertTrue(observed["result"])
        self.assertIn("documented", observed["detail"]["note"])

    def test_trace_count_must_match_the_summary(self):
        b = self.copy_package(self.a, "pkg_b")
        evidence_b = self.write_evidence(b, "b", mutate=lambda document: document["trace"].pop())
        report = self.qualify(self.a, b, self.evidence_a, evidence_b, self.expectation(self.a))
        self.assertEqual(report["result"], "fail")
        observed = self.check(report, "RQ-10")["observed"]["monitor_trace_count_matches_summary"]
        self.assertFalse(observed["result"])

    def test_trace_peak_must_match_the_summary(self):
        b = self.copy_package(self.a, "pkg_b")

        def lower_peak(document):
            document["trace"][-1]["rss_mb"] = 10.0

        evidence_b = self.write_evidence(b, "b", mutate=lower_peak)
        report = self.qualify(self.a, b, self.evidence_a, evidence_b, self.expectation(self.a))
        self.assertEqual(report["result"], "fail")
        self.assertFalse(self.check(report, "RQ-10")["observed"]["monitor_trace_peak_matches_summary"]["result"])

    def test_trace_sample_over_the_declared_limit_is_not_qualified(self):
        b = self.copy_package(self.a, "pkg_b")

        def overshoot(document):
            document["trace"][len(document["trace"]) // 2]["rss_mb"] = 9000.0
            document["summary"]["peak_rss_mb"] = 9000.0
            document["facts"]["peak_process_rss_mb"] = 9000.0

        evidence_b = self.write_evidence(b, "b", mutate=overshoot)
        report = self.qualify(self.a, b, self.evidence_a, evidence_b, self.expectation(self.a))
        self.assertEqual(report["result"], "fail")
        observed = self.check(report, "RQ-10")["observed"]["monitor_trace_within_declared_limit"]
        self.assertFalse(observed["result"])
        self.assertGreaterEqual(observed["detail"]["samples_over_limit"], 1)

    def test_trace_sample_numbering_must_be_sequential(self):
        b = self.copy_package(self.a, "pkg_b")

        def break_numbering(document):
            document["trace"][3]["sample"] = 99

        evidence_b = self.write_evidence(b, "b", mutate=break_numbering)
        report = self.qualify(self.a, b, self.evidence_a, evidence_b, self.expectation(self.a))
        self.assertEqual(report["result"], "fail")
        self.assertFalse(self.check(report, "RQ-10")["observed"]["monitor_trace_numbering"]["result"])

    def test_listing_that_does_not_cover_the_package_is_not_qualified(self):
        b = self.copy_package(self.a, "pkg_b")
        evidence_b = self.write_evidence(b, "b", mutate=lambda document: document["listing"].pop())
        report = self.qualify(self.a, b, self.evidence_a, evidence_b, self.expectation(self.a))
        self.assertEqual(report["result"], "fail")
        self.assertFalse(self.check(report, "RQ-10")["observed"]["package_listing_covers_package"]["result"])

    def test_listing_with_a_stale_digest_is_not_qualified(self):
        b = self.copy_package(self.a, "pkg_b")

        def stale(document):
            row = document["listing"][3].split("\t")
            row[2] = "0" * 64
            document["listing"][3] = "\t".join(row)

        evidence_b = self.write_evidence(b, "b", mutate=stale)
        report = self.qualify(self.a, b, self.evidence_a, evidence_b, self.expectation(self.a))
        self.assertEqual(report["result"], "fail")
        self.assertFalse(self.check(report, "RQ-10")["observed"]["package_listing_covers_package"]["result"])

    def test_evidence_facts_result_fail_is_not_qualified(self):
        b = self.copy_package(self.a, "pkg_b")

        def failed(document):
            document["facts"]["result"] = "FAIL"
            document["facts"]["problems"] = ["synthetic problem"]

        evidence_b = self.write_evidence(b, "b", mutate=failed)
        report = self.qualify(self.a, b, self.evidence_a, evidence_b, self.expectation(self.a))
        self.assertEqual(report["result"], "fail")
        observed = self.check(report, "RQ-10")["observed"]
        self.assertFalse(observed["evidence_facts_result_pass"]["result"])
        self.assertFalse(observed["evidence_facts_problems_empty"]["result"])
        self.assertIn("RQ-10", report["failures"])

    def test_evidence_bound_to_the_wrong_run_id_is_not_qualified(self):
        b = self.copy_package(self.a, "pkg_b")
        evidence_b = self.write_evidence(b, "b", mutate=lambda document: document["facts"].update({"run_id": "other"}))
        report = self.qualify(self.a, b, self.evidence_a, evidence_b, self.expectation(self.a))
        self.assertEqual(report["result"], "fail")
        self.assertFalse(self.check(report, "RQ-10")["observed"]["run_id_binds_to_package"]["result"])

    def test_package_record_digests_must_bind(self):
        b = self.copy_package(self.a, "pkg_b")
        evidence_b = self.write_evidence(
            b, "b", mutate=lambda document: document["facts"].update({"package_manifest_sha256": "0" * 64})
        )
        report = self.qualify(self.a, b, self.evidence_a, evidence_b, self.expectation(self.a))
        self.assertEqual(report["result"], "fail")
        self.assertFalse(self.check(report, "RQ-10")["observed"]["package_manifest_sha256_binds"]["result"])


# ------------------------------------------------------------------ usage / CLI


class QualificationCliTests(QualificationTestCase):
    """The gate's own fail-closed behaviour: usage errors and the verdict guard."""

    def test_same_directory_is_refused(self):
        a = self.make_package("pkg_a")
        code = self.cli(a, a)
        self.assertEqual(code, qualification.EXIT_USAGE)

    def test_symlink_to_the_same_package_is_refused(self):
        a = self.make_package("pkg_a")
        link = os.path.join(self._tmp, "link_to_pkg_a")
        os.symlink(a, link)
        code = self.cli(a, link)
        self.assertEqual(code, qualification.EXIT_USAGE)

    def test_incomplete_expectation_is_refused(self):
        a = self.make_package("pkg_a")
        b = self.make_package("pkg_b")
        expected = self.expectation(a, run_id="")
        code = self.cli(a, b, expected=expected)
        self.assertEqual(code, qualification.EXIT_USAGE)

    def test_verdict_inside_a_package_is_refused(self):
        a = self.make_package("pkg_a")
        b = self.make_package("pkg_b")
        code = self.cli(a, b, verdict=os.path.join(a, "verdict.json"))
        self.assertEqual(code, qualification.EXIT_USAGE)

    def test_verdict_inside_package_b_is_refused(self):
        """The guard is symmetric: a verdict inside either package is refused (gap G5)."""
        a = self.make_package("pkg_a")
        b = self.make_package("pkg_b")
        code = self.cli(a, b, verdict=os.path.join(b, "verdict.json"))
        self.assertEqual(code, qualification.EXIT_USAGE)
        self.assertFalse(os.path.exists(os.path.join(b, "verdict.json")))

    def test_end_to_end_cli_pass_and_verdict_outside_both_packages(self):
        a = self.make_package("pkg_a")
        b = self.make_package("pkg_b")
        self.write_evidence(a, "a")
        self.write_evidence(b, "b")
        verdict = os.path.join(self._tmp, "replay-qualification-verdict.json")

        code = self.cli(a, b, verdict=verdict)

        self.assertEqual(code, qualification.EXIT_QUALIFIED)
        self.assertIn("I4 REPLAY QUALIFICATION = PASS", self.last_stdout)
        with open(verdict, "r", encoding="utf-8") as handle:
            body = handle.read()
        document = json.loads(body)
        self.assertEqual(document["result"], "pass")
        self.assertEqual(document["comparison"]["result"], "pass")
        # the verdict is a reviewed document: canonical, path-free, clock-free, host-free
        self.assertNotIn(self._tmp, body)
        self.assertNotIn("\\", body)
        for key in ("recorded_at", "captured_at", "generated_at", "hostname", "pid", "sampled_at"):
            self.assertNotIn('"%s"' % key, body)
        self.assertEqual(body, i4_output.canonical_json(document) + "\n")

    def test_script_mode_invocation_works(self):
        """The Windows operator runs the gate as a script; the module must work in that mode."""
        import subprocess

        a = self.make_package("pkg_a")
        b = self.make_package("pkg_b")
        self.write_evidence(a, "a")
        self.write_evidence(b, "b")
        expected = self.expectation(a)
        arguments = [
            sys.executable, "-B", os.path.join("tools", "i4_m2", "i4_replay_qualification.py"),
            "--a", a, "--b", b,
            "--facts-a", self.evidence_paths("a")["facts"],
            "--facts-b", self.evidence_paths("b")["facts"],
            "--summary-a", self.evidence_paths("a")["summary"],
            "--summary-b", self.evidence_paths("b")["summary"],
            "--trace-a", self.evidence_paths("a")["trace"],
            "--trace-b", self.evidence_paths("b")["trace"],
            "--listing-a", self.evidence_paths("a")["listing"],
            "--listing-b", self.evidence_paths("b")["listing"],
            "--expect-repository", expected.repository,
            "--expect-ref", expected.ref,
            "--expect-commit", expected.commit,
            "--expect-tree", expected.tree,
            "--expect-engine-fingerprint", expected.engine_fingerprint,
            "--expect-runner-fingerprint", expected.runner_fingerprint,
            "--expect-run-id", expected.run_id,
            "--expect-corpus-archive-set-digest", expected.corpus_archive_set_digest,
        ]
        completed = subprocess.run(arguments, cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(completed.returncode, qualification.EXIT_QUALIFIED, completed.stderr)
        self.assertIn("I4 REPLAY QUALIFICATION = PASS", completed.stdout)

    def test_end_to_end_cli_failure_returns_not_qualified(self):
        a = self.make_package("pkg_a")
        b = self.make_package("pkg_b")
        self.write_evidence(a, "a")
        self.write_evidence(b, "b")
        os.remove(os.path.join(b, i4_output.COMPLETION_MARKER))

        code = self.cli(a, b)

        self.assertEqual(code, qualification.EXIT_NOT_QUALIFIED)
        self.assertIn("I4 REPLAY QUALIFICATION = FAIL", self.last_stdout)
        self.assertIn("RQ-02", self.last_stdout)


if __name__ == "__main__":
    unittest.main()
