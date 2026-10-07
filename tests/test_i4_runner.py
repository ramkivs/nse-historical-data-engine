"""I4 runner tests — fixture-scoped only (synthetic corpora; the real corpus is never touched).

Covers the authorized test surface: runner identity, preflight, archive/member validation,
format-family handling, partitioning, RD-4 reconciliation tiers, fail-closed behaviour, output
manifest generation, deterministic serialization, run_id behaviour and replay verification.

Every corpus used here is synthesised in a temporary directory from the repository's own
synthetic member builders. No test reads ``C:\\IIPS_Data`` or ``G:\\My Engines``, and no test
executes the governed 2,462-archive corpus.
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
import zipfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from nse_engine import contract  # noqa: E402
from nse_engine import w2_stream  # noqa: E402
from nse_engine.evidence_inputs import INVENTORY_ROOT_TO_FAMILY  # noqa: E402
from nse_engine.pipeline import build_w2  # noqa: E402
from nse_engine.rows import SecurityRow  # noqa: E402
from tests import support  # noqa: E402

from tools.i4_runner import (  # noqa: E402
    i4_identity,
    i4_inputs,
    i4_output,
    i4_preflight,
    i4_reconcile,
    i4_runner,
)

GOVERNED_INVENTORY = os.path.join(REPO_ROOT, "evidence", "inventory", "file_inventory.json")
GOVERNED_INVENTORY_LF_SHA256 = (
    "336b9531cd34f48e9a2e7e7593cc4e9c2736b3864d8213bc65d6ab8b488729d2"
)
#: G-I4-M1-CORRECTIVE engine revision: the bounded-memory W2 composition's retained state was
#: compacted (``compact`` joined ``ENGINE_MODULES``; the metric fold and the association chain now
#: share interned tokens, and the association store is one packed row array with index arrays), so
#: the governed engine fingerprint was recalculated. Previous revisions' values:
#: ``7bee84902f8cb0e5c60703acbe1b17d6e85a9b9762289bab1741d9f003df5a52`` (pre-M1) and
#: ``af82485ef4acb82c8e4164b4d39805a2034da00991f27a80ab2fd3a70d613ad2`` (M1, superseded).
GOVERNED_TOOL_FINGERPRINT = (
    "d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9"
)

#: G-I4-M1 runner revision: ``i4_runner.py`` now feeds and releases one member at a time.
GOVERNED_RUNNER_FINGERPRINT = (
    "f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a"
)

LEGACY_INDEX = {name: index for index, name in enumerate(contract.LEGACY_HEADER_FIELDS)}
UDIFF_INDEX = {name: index for index, name in enumerate(contract.UDIFF_HEADER_FIELDS)}

DEFAULT_SPECS = (
    ("LEGACY", "cm01JUL2024bhav.csv.zip", "cm01JUL2024bhav.csv", "01-JUL-2024", "2024-07-01", 3),
    ("LEGACY", "cm02JUL2024bhav.csv.zip", "cm02JUL2024bhav.csv", "02-JUL-2024", "2024-07-02", 2),
    (
        "UDIFF",
        "BhavCopy_NSE_CM_0_0_0_20240703_F_0000.csv.zip",
        "BhavCopy_NSE_CM_0_0_0_20240703_F_0000.csv",
        "2024-07-03",
        "2024-07-03",
        2,
    ),
    (
        "UDIFF",
        "BhavCopy_NSE_CM_0_0_0_20240704_F_0000.csv.zip",
        "BhavCopy_NSE_CM_0_0_0_20240704_F_0000.csv",
        "2024-07-04",
        "2024-07-04",
        1,
    ),
)


# ------------------------------------------------------------------ corpus synthesis


def legacy_member_bytes(date_text, count):
    rows = []
    for index in range(count):
        rows.append(
            support.legacy_row(
                SYMBOL="SYM%d" % index,
                SERIES="EQ",
                ISIN="INE%03dA0101%d" % (index, index),
                TIMESTAMP=date_text,
            )
        )
    return support.legacy_member(rows)


def udiff_member_bytes(date_iso, count):
    rows = []
    for index in range(count):
        rows.append(
            support.udiff_row(
                TckrSymb="USYM%d" % index,
                FinInstrmId="%d" % (900 + index),
                ISIN="INE%03dA0102%d" % (index, index),
                SctySrs="EQ",
                TradDt=date_iso,
                BizDt=date_iso,
            )
        )
    return support.udiff_member(rows)


def member_bytes_for(root_label, date_text, date_iso, count):
    if root_label == "LEGACY":
        return legacy_member_bytes(date_text, count)
    return udiff_member_bytes(date_iso, count)


def inventory_record(root_label, archive_name, member_name, data, date_iso):
    """Derive a D01-shaped inventory record from the synthesised member (test-side only)."""
    text = data.decode("utf-8")
    lines = text.splitlines()
    headers = lines[0].split(",")
    index = LEGACY_INDEX if root_label == "LEGACY" else UDIFF_INDEX
    series_counts = {}
    isins, symbols = set(), set()
    date_values = {}
    data_lines = [line for line in lines[1:] if line.strip()]
    width = contract.LEGACY_LOGICAL_WIDTH if root_label == "LEGACY" else contract.UDIFF_WIDTH
    good = 0
    bad = 0
    for line in data_lines:
        fields = line.split(",")
        if len(fields) < width:
            bad += 1  # a malformed line: counted by bad_rows, excluded from the aggregates
            continue
        if root_label == "LEGACY":
            symbol = fields[index["SYMBOL"]]
            series = fields[index["SERIES"]]
            isin = fields[index["ISIN"]]
            stamp = fields[index["TIMESTAMP"]]
        else:
            symbol = fields[index["TckrSymb"]]
            series = fields[index["SctySrs"]]
            isin = fields[index["FinInstrmId"]] if fields[index["ISIN"]] == "" else fields[index["ISIN"]]
            stamp = fields[index["TradDt"]]
        good += 1
        series_counts[series] = series_counts.get(series, 0) + 1
        date_values[stamp] = date_values.get(stamp, 0) + 1
        if isin.strip():
            isins.add(isin.strip().upper())
        if symbol.strip():
            symbols.add(symbol.strip())
    return {
        "root": root_label,
        "relative_path": archive_name,
        "file_name": archive_name,
        "size_bytes": None,  # filled after the archive is written
        "date_from_filename": date_iso,
        "sha256": None,  # filled after the archive is written
        "detected_format": root_label,
        "row_count": good,
        "bad_rows": bad,
        "headers": headers,
        "header_signature": "|".join(headers),
        "date_values": date_values,
        "series_counts": series_counts,
        "symbol_count": len(symbols),
        "isin_count": len(isins),
    }


class Corpus:
    """A synthesised two-root corpus plus its governed-shaped inventory."""

    def __init__(self, root, specs):
        self.root = root
        self.legacy_root = os.path.join(root, "legacy")
        self.udiff_root = os.path.join(root, "udiff")
        os.makedirs(self.legacy_root)
        os.makedirs(self.udiff_root)
        self.records = []
        for root_label, archive_name, member_name, date_text, date_iso, count in specs:
            data = (
                legacy_member_bytes(date_text, count)
                if root_label == "LEGACY"
                else udiff_member_bytes(date_iso, count)
            )
            self.add_member(root_label, archive_name, member_name, data, date_iso)
        self.inventory_path = os.path.join(root, "inventory", "file_inventory.json")
        os.makedirs(os.path.dirname(self.inventory_path))
        self.write_inventory()

    def root_dir(self, root_label):
        return self.legacy_root if root_label == "LEGACY" else self.udiff_root

    def add_member(self, root_label, archive_name, member_name, data, date_iso, extra_members=()):
        archive_path = os.path.join(self.root_dir(root_label), archive_name)
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as handle:
            handle.writestr(member_name, data)
            for name, payload in extra_members:
                handle.writestr(name, payload)
        with open(archive_path, "rb") as handle:
            raw = handle.read()
        record = inventory_record(root_label, archive_name, member_name, data, date_iso)
        record["size_bytes"] = len(raw)
        record["sha256"] = hashlib.sha256(raw).hexdigest()
        self.records = [entry for entry in self.records
                        if not (entry["root"] == root_label and entry["relative_path"] == archive_name)]
        self.records.append(record)
        return record

    def refresh_record(self, root_label, archive_name):
        """Recompute sha256/size from the archive on disk (keeps a stale expectation)."""
        archive_path = os.path.join(self.root_dir(root_label), archive_name)
        with open(archive_path, "rb") as handle:
            raw = handle.read()
        for record in self.records:
            if record["root"] == root_label and record["relative_path"] == archive_name:
                record["size_bytes"] = len(raw)
                record["sha256"] = hashlib.sha256(raw).hexdigest()
        return archive_path

    def write_inventory(self, records=None, with_summary=True):
        records = self.records if records is None else records
        text = json.dumps(records, indent=1, sort_keys=True) + "\n"
        with open(self.inventory_path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        if with_summary:
            dates = [record["date_from_filename"] for record in records]
            checksums = [record["sha256"] for record in records]
            by_root = {}
            for record in records:
                by_root[record["root"]] = by_root.get(record["root"], 0) + 1
            summary = {
                "read_only": True,
                "file_count": len(records),
                "errors": 0,
                "by_root": by_root,
                "by_format": by_root,
                "duplicate_checksum_count": len(checksums) - len(set(checksums)),
                "duplicate_date_count": len(dates) - len(set(dates)),
                "schema_variant_count": len({record["header_signature"] for record in records}),
                "first_file_date": min(dates),
                "last_file_date": max(dates),
            }
            summary_path = os.path.join(os.path.dirname(self.inventory_path), "inventory_summary.json")
            with open(summary_path, "w", encoding="utf-8", newline="") as handle:
                handle.write(json.dumps(summary, indent=1, sort_keys=True) + "\n")
        return self.inventory_path

    def run_args(self, out, run_id="i4-test", extra=()):
        argv = [
            "run",
            "--legacy-root", self.legacy_root,
            "--udiff-root", self.udiff_root,
            "--inventory", self.inventory_path,
            "--out", out,
            "--run-id", run_id,
        ]
        argv.extend(extra)
        return argv


class RunnerTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="i4-runner-test-")
        self.addCleanup(shutil.rmtree, self._tmp, True)

    def make_corpus(self, specs=DEFAULT_SPECS, name="corpus"):
        return Corpus(os.path.join(self._tmp, name), specs)

    def out_dir(self, name="run"):
        return os.path.join(self._tmp, name)

    def invoke(self, argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = i4_runner.main(list(argv))
        self.last_stdout, self.last_stderr = stdout.getvalue(), stderr.getvalue()
        return code

    def read_jsonl(self, path):
        with open(path, "r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def read_json(self, path):
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)


# ------------------------------------------------------------------ runner identity


class RunnerIdentityTests(RunnerTestCase):
    def test_fingerprint_is_deterministic_and_covers_declared_modules(self):
        first = i4_identity.runner_fingerprint()
        second = i4_identity.runner_fingerprint()
        self.assertEqual(first, second)
        self.assertEqual(len(i4_identity.RUNNER_MODULES), 6)
        self.assertEqual(
            set(i4_identity.RUNNER_MODULES),
            {
                "i4_identity.py",
                "i4_inputs.py",
                "i4_output.py",
                "i4_preflight.py",
                "i4_reconcile.py",
                "i4_runner.py",
            },
        )

    def test_changing_any_declared_module_changes_the_fingerprint(self):
        copy_dir = os.path.join(self._tmp, "modules")
        os.makedirs(copy_dir)
        for name in i4_identity.RUNNER_MODULES:
            shutil.copy(os.path.join(i4_identity.MODULE_DIR, name), os.path.join(copy_dir, name))
        original = i4_identity.runner_fingerprint(copy_dir)
        with open(os.path.join(copy_dir, "i4_reconcile.py"), "a", encoding="utf-8") as handle:
            handle.write("\n# identity invalidation probe\n")
        self.assertNotEqual(original, i4_identity.runner_fingerprint(copy_dir))

    def test_missing_declared_module_fails_closed(self):
        empty = os.path.join(self._tmp, "empty")
        os.makedirs(empty)
        with self.assertRaises(i4_identity.RunnerIdentityError):
            i4_identity.runner_fingerprint(empty)

    def test_runner_declares_no_network_imports(self):
        self.assertEqual(i4_identity.forbidden_import_hits(), ())

    def test_runner_contains_no_clock_randomness_or_environment_usage(self):
        self.assertEqual(i4_preflight.source_token_hits(), ())

    def test_source_guarantee_scan_detects_violations(self):
        copy_dir = os.path.join(self._tmp, "violations")
        os.makedirs(copy_dir)
        for name in i4_identity.RUNNER_MODULES:
            shutil.copy(os.path.join(i4_identity.MODULE_DIR, name), os.path.join(copy_dir, name))
        violation = "stamp = " + "time" + "." + "time()"
        with open(os.path.join(copy_dir, "i4_output.py"), "a", encoding="utf-8") as handle:
            handle.write("\n%s\n" % violation)
        hits = i4_preflight.source_token_hits(copy_dir)
        self.assertTrue(hits)
        self.assertEqual(hits[0][2], "time" + ".time(")

    def test_runner_identity_matches_the_governed_revision(self):
        self.assertEqual(i4_identity.runner_fingerprint(), GOVERNED_RUNNER_FINGERPRINT)

    def test_engine_identity_matches_the_governed_baseline(self):
        self.assertEqual(i4_identity.engine_fingerprint(), GOVERNED_TOOL_FINGERPRINT)
        module_facts = i4_identity.engine_module_facts()
        self.assertEqual(len(module_facts), len(contract.ENGINE_MODULES))
        self.assertTrue(all(fact["raw_sha256"] for fact in module_facts))


# ------------------------------------------------------------------ partitioning (RD-6)


class PartitionTests(RunnerTestCase):
    def test_partition_key_shape(self):
        record = {"root": "LEGACY", "date_from_filename": "2016-09-20"}
        self.assertEqual(i4_inputs.partition_of(record), ("legacy13", "2016"))
        record = {"root": "UDIFF", "date_from_filename": "2025-10-30"}
        self.assertEqual(i4_inputs.partition_of(record), ("udiff34", "2025"))
        self.assertEqual(i4_inputs.partition_id("udiff34", "2025"), "udiff34_2025")

    def test_governed_inventory_yields_exactly_twelve_partitions(self):
        with open(GOVERNED_INVENTORY, "r", encoding="utf-8") as handle:
            records = json.load(handle)
        census = {}
        for record in records:
            census[i4_inputs.partition_id(*i4_inputs.partition_of(record))] = (
                census.get(i4_inputs.partition_id(*i4_inputs.partition_of(record)), 0) + 1
            )
        self.assertEqual(len(census), 12)
        self.assertEqual(sum(census.values()), 2462)
        self.assertEqual(census["legacy13_2016"], 69)
        self.assertEqual(census["legacy13_2024"], 125)
        self.assertEqual(census["udiff34_2024"], 120)
        self.assertEqual(census["udiff34_2026"], 176)

    def test_partition_family_mapping_is_the_engine_mapping(self):
        for root, family in INVENTORY_ROOT_TO_FAMILY.items():
            self.assertEqual(i4_inputs.expected_family(root), family)


# ------------------------------------------------------------------ happy path + package


class RunPackageTests(RunnerTestCase):
    def test_run_produces_a_complete_verifiable_package(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        code = self.invoke(corpus.run_args(out))
        self.assertEqual(code, i4_runner.EXIT_OK, self.last_stderr)
        self.assertTrue(os.path.isfile(os.path.join(out, "RUN_COMPLETE.json")))
        self.assertFalse(os.path.isfile(os.path.join(out, "RUN_FAILED.json")))
        result = i4_output.verify_package(out)
        self.assertEqual(result["result"], "pass", result)

    def test_package_manifest_covers_every_retained_artifact(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        entries = i4_output._parse_manifest(os.path.join(out, "PACKAGE_MANIFEST.sha256"))
        listed = {relative for _digest, relative in entries}
        present = set()
        for dirpath, dirnames, filenames in os.walk(out):
            dirnames.sort()
            for name in filenames:
                relative = os.path.relpath(os.path.join(dirpath, name), out).replace(os.sep, "/")
                if relative not in i4_output.UNMANIFESTED:
                    present.add(relative)
        self.assertEqual(listed, present)
        for relative in sorted(listed):
            i4_output.classify_artifact(relative)  # exactly one MD-05 class per artifact

    def test_partition_manifests_exist_per_partition(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        manifests = sorted(os.listdir(os.path.join(out, "manifests")))
        self.assertEqual(manifests, ["legacy13_2024.sha256", "udiff34_2024.sha256"])
        self.assertEqual(len(self.read_jsonl(os.path.join(out, "w2", "calendar.jsonl"))), 4)

    def test_run_record_declares_identity_counts_and_boundaries(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        record = self.read_json(os.path.join(out, "RUN_RECORD.json"))
        self.assertEqual(record["run_id"], "i4-test")
        self.assertEqual(record["engine_identity"]["tool_sha256"], GOVERNED_TOOL_FINGERPRINT)
        self.assertEqual(record["runner_identity"]["runner_sha256"], i4_identity.runner_fingerprint())
        self.assertEqual(record["counts"]["members"], 4)
        self.assertEqual(record["counts"]["rows"], 8)
        self.assertEqual(record["boundary"]["production"], False)
        self.assertIn("UNDECIDED", record["boundary"]["storage_technology"])
        self.assertEqual(len(record["corpus"]["partitions"]), 2)

    def test_input_manifest_records_governed_identity_and_hash_bases(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        entries = self.read_jsonl(os.path.join(out, "INPUT_MANIFEST.jsonl"))
        self.assertEqual(len(entries), 4)
        for entry in entries:
            self.assertEqual(entry["archive_sha256_basis"], "D01-inventory")
            self.assertEqual(entry["archive_sha256_d01"], entry["archive_sha256_observed_raw_bytes"])
            self.assertTrue(entry["member_name"].endswith(".csv"))
            self.assertEqual(entry["data_lines"], entry["rows"] + entry["quarantined"])

    def test_rows_carry_governed_provenance_and_declared_run_id(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out, run_id="i4-prov")), i4_runner.EXIT_OK,
                         self.last_stderr)
        rows = self.read_jsonl(
            os.path.join(out, "partitions", "legacy13", "2024", "rows", "cm01JUL2024bhav.csv.rows.jsonl")
        )
        self.assertEqual(len(rows), 3)
        provenance = rows[0]["provenance"]
        self.assertEqual(provenance["archive_sha256_basis"], "D01-inventory")
        self.assertEqual(provenance["run_id"], "i4-prov")
        self.assertEqual(provenance["source_archive"], "cm01JUL2024bhav.csv.zip")
        self.assertEqual(provenance["member_name"], "cm01JUL2024bhav.csv")
        self.assertEqual(provenance["tool_sha256"], GOVERNED_TOOL_FINGERPRINT)

    def test_member_name_is_read_verbatim_and_never_derived(self):
        corpus = self.make_corpus()
        corpus.add_member(
            "LEGACY",
            "cm05JUL2024bhav.csv.zip",
            "unexpected-inner-name.csv",
            legacy_member_bytes("05-JUL-2024", 1),
            "2024-07-05",
        )
        corpus.write_inventory()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        entries = self.read_jsonl(os.path.join(out, "INPUT_MANIFEST.jsonl"))
        match = [entry for entry in entries if entry["file_name"] == "cm05JUL2024bhav.csv.zip"]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0]["member_name"], "unexpected-inner-name.csv")

    def test_w2_outputs_and_unresolved_state_are_present(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        metrics = self.read_json(os.path.join(out, "w2", "metrics.json"))
        self.assertIn("row_metrics", metrics)
        self.assertEqual(metrics["row_metrics"]["rows"], 8)
        self.assertIsNone(metrics["d01_metric_fold"])
        unresolved = self.read_jsonl(os.path.join(out, "w2", "unresolved.jsonl"))
        kinds = {entry["kind"] for entry in unresolved}
        self.assertIn("identity-non-promotion", unresolved[0]["kind"] and kinds or kinds)
        self.assertIn("identity-non-promotion", kinds)
        self.assertIn("cross-era-boundary-residual", kinds)
        self.assertIn("calendar-label-status-counts", kinds)
        self.assertTrue(self.read_jsonl(os.path.join(out, "w2", "associations.jsonl")))

    def test_script_mode_invocation_works(self):
        import subprocess

        corpus = self.make_corpus()
        out = self.out_dir()
        script = os.path.join(REPO_ROOT, "tools", "i4_runner", "i4_runner.py")
        completed = subprocess.run(
            [sys.executable, "-B", script] + corpus.run_args(out),
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, i4_runner.EXIT_OK, completed.stderr[-2000:])
        self.assertTrue(os.path.isfile(os.path.join(out, "RUN_COMPLETE.json")))


# ------------------------------------------------------------------ preflight / Tier A


class PreflightFailureTests(RunnerTestCase):
    def assert_failed_closed(self, corpus, out, needle=""):
        code = self.invoke(corpus.run_args(out))
        self.assertEqual(code, i4_runner.EXIT_FAILED, self.last_stdout + self.last_stderr)
        self.assertFalse(os.path.isfile(os.path.join(out, "RUN_COMPLETE.json")))
        self.assertTrue(os.path.isfile(os.path.join(out, "RUN_FAILED.json")))
        failure = self.read_json(os.path.join(out, "RUN_FAILED.json"))
        self.assertEqual(failure["status"], "failed")
        self.assertIn("incomplete", failure["note"])
        if needle:
            self.assertIn(needle, failure["condition"] + json.dumps(failure.get("failed_check")))

    def test_missing_archive_fails_the_complete_run(self):
        corpus = self.make_corpus()
        os.remove(os.path.join(corpus.legacy_root, "cm02JUL2024bhav.csv.zip"))
        self.assert_failed_closed(corpus, self.out_dir(), "missing")

    def test_unexpected_archive_fails_the_complete_run(self):
        corpus = self.make_corpus()
        with zipfile.ZipFile(os.path.join(corpus.legacy_root, "cm09JUL2024bhav.csv.zip"), "w") as handle:
            handle.writestr("cm09JUL2024bhav.csv", legacy_member_bytes("09-JUL-2024", 1))
        self.assert_failed_closed(corpus, self.out_dir(), "unexpected")

    def test_archive_hash_mismatch_fails_the_complete_run(self):
        corpus = self.make_corpus()
        # Rewrite one archive with different bytes but keep the D01 sha256 (stale expectation).
        path = os.path.join(corpus.legacy_root, "cm01JUL2024bhav.csv.zip")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as handle:
            handle.writestr("cm01JUL2024bhav.csv", legacy_member_bytes("01-JUL-2024", 5))
        self.assert_failed_closed(corpus, self.out_dir(), "sha256 mismatch")

    def test_multiple_csv_members_fail_closed(self):
        corpus = self.make_corpus()
        path = os.path.join(corpus.legacy_root, "cm01JUL2024bhav.csv.zip")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as handle:
            handle.writestr("cm01JUL2024bhav.csv", legacy_member_bytes("01-JUL-2024", 1))
            handle.writestr("second.csv", legacy_member_bytes("01-JUL-2024", 1))
        corpus.refresh_record("LEGACY", "cm01JUL2024bhav.csv.zip")
        corpus.write_inventory()
        self.assert_failed_closed(corpus, self.out_dir(), "exactly one .csv member")

    def test_missing_csv_member_fails_closed(self):
        corpus = self.make_corpus()
        path = os.path.join(corpus.legacy_root, "cm01JUL2024bhav.csv.zip")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as handle:
            handle.writestr("not-a-csv.txt", "hello")
        corpus.refresh_record("LEGACY", "cm01JUL2024bhav.csv.zip")
        corpus.write_inventory()
        self.assert_failed_closed(corpus, self.out_dir(), "exactly one .csv member")

    def test_malformed_archive_fails_closed(self):
        corpus = self.make_corpus()
        path = os.path.join(corpus.legacy_root, "cm02JUL2024bhav.csv.zip")
        with open(path, "wb") as handle:
            handle.write(b"this is not a zip archive")
        corpus.refresh_record("LEGACY", "cm02JUL2024bhav.csv.zip")
        corpus.write_inventory()
        self.assert_failed_closed(corpus, self.out_dir(), "malformed archive")

    def test_non_empty_output_root_fails_closed(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        os.makedirs(out)
        with open(os.path.join(out, "leftover.txt"), "w", encoding="utf-8") as handle:
            handle.write("previous run\n")
        code = self.invoke(corpus.run_args(out))
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        self.assertFalse(os.path.isfile(os.path.join(out, "RUN_COMPLETE.json")))

    def test_output_root_inside_the_corpus_fails_closed(self):
        corpus = self.make_corpus()
        out = os.path.join(corpus.legacy_root, "run-output")
        code = self.invoke(corpus.run_args(out))
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        self.assertFalse(os.path.isdir(out))

    def test_declared_expectations_are_enforced(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        code = self.invoke(corpus.run_args(out, extra=("--expect-records", "2462")))
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        code = self.invoke(corpus.run_args(out, extra=("--expect-tool-fingerprint", "0" * 64)))
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        self.assertFalse(os.path.isfile(os.path.join(out, "RUN_COMPLETE.json")))

    def test_missing_declared_evidence_input_fails_closed(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        code = self.invoke(corpus.run_args(out, extra=("--labels", os.path.join(self._tmp, "nope.json"))))
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        self.assertIn("missing", self.last_stderr)

    def test_inventory_internal_inconsistency_fails_closed(self):
        corpus = self.make_corpus()
        corpus.records[0]["date_values"] = {"01-JUL-2024": 999}
        corpus.write_inventory(with_summary=False)
        self.assert_failed_closed(corpus, self.out_dir(), "internally inconsistent")

    def test_inventory_summary_disagreement_fails_closed(self):
        corpus = self.make_corpus()
        corpus.write_inventory()
        summary_path = os.path.join(os.path.dirname(corpus.inventory_path), "inventory_summary.json")
        summary = self.read_json(summary_path)
        summary["file_count"] = 999
        with open(summary_path, "w", encoding="utf-8", newline="") as handle:
            handle.write(json.dumps(summary) + "\n")
        self.assert_failed_closed(corpus, self.out_dir(), "summary")

    def test_preflight_records_cover_every_gate(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        checks = self.read_jsonl(os.path.join(out, "PREFLIGHT.jsonl"))
        ids = {check["check_id"] for check in checks}
        for expected in ("PF-00", "PF-01", "PF-02", "PF-03", "PF-04", "PF-05", "PF-06",
                         "PF-07", "PF-08", "PF-09", "PF-10", "PF-11", "PF-12", "PF-13"):
            self.assertIn(expected, ids)
        for check in checks:
            self.assertIn(check["disposition"], ("gating", "non-gating"))
            self.assertIn(check["tier"], ("A", "G", "C", "E"))


# ------------------------------------------------------------------ format / parser failures


class FormatFamilyTests(RunnerTestCase):
    def test_family_mismatch_fails_closed(self):
        corpus = self.make_corpus()
        # A legacy member declared as UDIFF: the governed mapping no longer holds.
        corpus.add_member(
            "UDIFF",
            "BhavCopy_NSE_CM_0_0_0_20240705_F_0000.csv.zip",
            "BhavCopy_NSE_CM_0_0_0_20240705_F_0000.csv",
            legacy_member_bytes("05-JUL-2024", 1),
            "2024-07-05",
        )
        corpus.write_inventory()
        out = self.out_dir()
        code = self.invoke(corpus.run_args(out))
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        self.assertFalse(os.path.isfile(os.path.join(out, "RUN_COMPLETE.json")))

    def test_unrecognized_header_fails_closed(self):
        corpus = self.make_corpus()
        data = support.legacy_member([("A", "B")], header=["A", "B", "C"])
        corpus.add_member("LEGACY", "cm05JUL2024bhav.csv.zip", "cm05JUL2024bhav.csv", data, "2024-07-05")
        corpus.write_inventory()
        out = self.out_dir()
        code = self.invoke(corpus.run_args(out))
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        self.assertIn("HeaderUnrecognizedError", self.last_stderr)
        self.assertFalse(os.path.isfile(os.path.join(out, "RUN_COMPLETE.json")))

    def test_calendar_fail_closed_when_a_labelled_scope_gap_has_no_label(self):
        specs = (
            ("LEGACY", "cm01JUL2024bhav.csv.zip", "cm01JUL2024bhav.csv", "01-JUL-2024", "2024-07-01", 2),
            ("LEGACY", "cm02JUL2024bhav.csv.zip", "cm02JUL2024bhav.csv", "02-JUL-2024", "2024-07-02", 2),
            ("UDIFF", "BhavCopy_NSE_CM_0_0_0_20240704_F_0000.csv.zip",
             "BhavCopy_NSE_CM_0_0_0_20240704_F_0000.csv", "2024-07-04", "2024-07-04", 1),
        )
        corpus = self.make_corpus(specs=specs)
        out = self.out_dir()
        code = self.invoke(corpus.run_args(out))
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        self.assertIn("CalendarEvidenceError", self.last_stderr)
        self.assertIn("no governed label", self.last_stderr)
        self.assertTrue(os.path.isfile(os.path.join(out, "RUN_FAILED.json")))
        self.assertFalse(os.path.isfile(os.path.join(out, "RUN_COMPLETE.json")))


# ------------------------------------------------------------------ RD-4 reconciliation tiers


class ReconciliationTierTests(RunnerTestCase):
    def test_tier_a_records_are_gating_and_complete(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        records = self.read_jsonl(os.path.join(out, "RECONCILIATION.jsonl"))
        tier_a = [record for record in records if record["tier"] == "A"]
        self.assertTrue(tier_a)
        for record in tier_a:
            self.assertEqual(record["disposition"], "gating")
            self.assertIn(record["result"], ("match", "divergence"))
            for key in ("input_identity", "comparison_basis", "governing_definition", "result",
                        "disposition", "unresolved_state"):
                self.assertIn(key, record)
        checks = {record["check"] for record in tier_a}
        for expected in ("archive_sha256_vs_d01", "family_vs_detected_format",
                         "header_shape_governed_variant", "member_identity_single_csv",
                         "expected_source_date_supplied", "archive_sha256_basis_declared"):
            self.assertIn(expected, checks)

    def test_definition_dependent_counters_are_recorded_and_never_gate(self):
        corpus = self.make_corpus()
        for record in corpus.records:
            record["bad_rows"] = 7
            record["isin_count"] = record["row_count"] + 5
            record["symbol_count"] = record["row_count"] + 5
            # preserve the self-consistency sums PF-07 checks
            series = dict(record["series_counts"])
            victim = sorted(series)[0]
            series[victim] = series[victim] - 1
            series["ZZ"] = series.get("ZZ", 0) + 1
            record["series_counts"] = series
            keys = sorted(record["date_values"])
            first = keys[0]
            record["date_values"] = {first: record["row_count"]}
            if record["root"] == "UDIFF":
                record["date_values"] = {"2099-01-01": record["row_count"]}
        corpus.write_inventory()
        out = self.out_dir()
        code = self.invoke(corpus.run_args(out))
        self.assertEqual(code, i4_runner.EXIT_OK, self.last_stderr)
        self.assertTrue(os.path.isfile(os.path.join(out, "RUN_COMPLETE.json")))
        records = self.read_jsonl(os.path.join(out, "RECONCILIATION.jsonl"))
        tier_c = [record for record in records if record["tier"] == "C"]
        divergences = {record["check"] for record in tier_c if record["result"] == "divergence"}
        self.assertIn("bad_rows_vs_quarantined", divergences)
        self.assertIn("isin_count_vs_distinct_nonblank_normalised", divergences)
        self.assertIn("symbol_count_vs_distinct_nonblank_symbols", divergences)
        self.assertIn("series_counts_vs_canonical_tally", divergences)
        for record in tier_c:
            self.assertEqual(record["disposition"], "non-gating")
        summary = self.read_json(os.path.join(out, "RUN_RECORD.json"))["verification"]["reconciliation"]
        self.assertEqual(summary["gating_divergence_count"], 0)
        self.assertTrue(summary["by_result"].get("divergence"))

    def test_definition_comparisons_are_not_kind_to_the_counters(self):
        """A definition-dependent mismatch must not be 'made to match' anywhere."""
        corpus = self.make_corpus()
        corpus.records[0]["row_count"] = corpus.records[0]["row_count"] + 4
        corpus.records[0]["date_values"] = {
            key: value + 4 for key, value in corpus.records[0]["date_values"].items()
        }
        corpus.records[0]["series_counts"] = {
            key: (value + 4 if key == sorted(corpus.records[0]["series_counts"])[0] else value)
            for key, value in corpus.records[0]["series_counts"].items()
        }
        corpus.write_inventory()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        records = self.read_jsonl(os.path.join(out, "RECONCILIATION.jsonl"))
        match = [record for record in records
                 if record["check"] == "row_count_vs_data_lines"
                 and record["input_identity"]["file_name"] == "cm01JUL2024bhav.csv.zip"]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0]["result"], "divergence")
        self.assertEqual(match[0]["delta"], -4)  # delta = observed - expected; never normalised
        evidence = self.read_json(
            os.path.join(out, "partitions", "legacy13", "2024", "evidence",
                         "cm01JUL2024bhav.csv.evidence.json")
        )
        self.assertEqual(evidence["parse_report"]["data_lines"], 3)

    def test_legacy_date_values_are_not_mapped_by_an_invented_rule(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        records = self.read_jsonl(os.path.join(out, "RECONCILIATION.jsonl"))
        legacy = [record for record in records
                  if record["check"] == "date_values_vs_parsed_business_date"
                  and record["input_identity"]["root"] == "LEGACY"]
        self.assertTrue(legacy)
        for record in legacy:
            self.assertEqual(record["result"], i4_reconcile.NOT_COMPARABLE)
            self.assertIn("raw_keys", record["expected"])
            self.assertIn("date-text mapping", record["unresolved_state"])

    def test_udiff_date_values_are_compared(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        records = self.read_jsonl(os.path.join(out, "RECONCILIATION.jsonl"))
        udiff = [record for record in records
                 if record["check"] == "date_values_vs_parsed_business_date"
                 and record["input_identity"]["root"] == "UDIFF"]
        self.assertTrue(udiff)
        for record in udiff:
            self.assertEqual(record["result"], i4_reconcile.MATCH)

    def test_quarantined_row_is_recorded_but_is_not_a_run_failure(self):
        corpus = self.make_corpus()
        rows = [support.legacy_row(SYMBOL="SYM0", ISIN="INE000A01010", TIMESTAMP="05-JUL-2024"),
                ("too", "few")]
        data = support.legacy_member(rows)
        corpus.add_member("LEGACY", "cm05JUL2024bhav.csv.zip", "cm05JUL2024bhav.csv", data, "2024-07-05")
        corpus.write_inventory()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        record = self.read_json(os.path.join(out, "RUN_RECORD.json"))
        self.assertEqual(record["counts"]["quarantined"], 1)
        evidence = self.read_json(
            os.path.join(out, "partitions", "legacy13", "2024", "evidence",
                         "cm05JUL2024bhav.csv.evidence.json")
        )
        self.assertEqual(evidence["parse_report"]["quarantined"], 1)
        self.assertTrue(evidence["quarantine"])

    def test_corpus_level_fold_and_verdict_are_compared_when_declared(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        metrics_csv = os.path.join(self._tmp, "metrics.csv")
        header = (
            "format,file,rows,blank_symbol_rows,blank_isin_rows,nonblank_isin_rows,"
            "distinct_nonblank_isin,isins_extra_duplicate_rows,distinct_nonblank_symbol,"
            "distinct_symbol_series_pairs,symbol_series_duplicate_rows,is_d02_target,"
            "requested_date,selection,d01_isin_count,d01_symbol_count,"
            "d01_isin_eq_distinct_nonblank,d01_isin_eq_nonblank_rows,"
            "d01_sym_eq_distinct_nonblank,d01_sym_eq_rows,discriminating_file\n"
        )
        line = (
            "LEGACY,cm01JUL2024bhav.csv.zip,3,0,0,3,3,0,3,3,0,True,2024-07-01,exact,"
            "3,3,True,True,True,True,False\n"
        )
        with open(metrics_csv, "w", encoding="utf-8", newline="") as handle:
            handle.write(header + line)
        verdict = os.path.join(self._tmp, "verdict.json")
        with open(verdict, "w", encoding="utf-8", newline="") as handle:
            handle.write(json.dumps({"discriminating_files": 0, "match_distinct_nonblank": 0,
                                     "match_nonblank_rows": 0, "verdict": "UNDETERMINED"}) + "\n")
        code = self.invoke(
            corpus.run_args(
                out,
                extra=("--d01-metrics", metrics_csv, "--d01-verdict", verdict),
            )
        )
        self.assertEqual(code, i4_runner.EXIT_OK, self.last_stderr)
        records = self.read_jsonl(os.path.join(out, "RECONCILIATION.jsonl"))
        checks = {record["check"] for record in records}
        self.assertIn("corpus_metric_rows_fold_vs_rows", checks)
        self.assertIn("d03_definition_verdict_vs_recomputed_fold", checks)
        self.assertIn("corpus_distinct_metrics_not_comparable", checks)
        for record in records:
            if record["tier"] in ("C", "E"):
                self.assertEqual(record["disposition"], "non-gating")

    def test_record_shape_helper_is_stable(self):
        record = i4_reconcile.make_record(
            i4_reconcile.TIER_C, "probe", {"scope": "corpus"}, "basis", "definition",
            1, 2, i4_reconcile.DIVERGENCE, i4_reconcile.NON_GATING, unresolved_state="open",
        )
        self.assertEqual(
            sorted(record),
            sorted(["tier", "tier_description", "check", "input_identity", "comparison_basis",
                    "governing_definition", "expected", "observed", "delta", "result",
                    "disposition", "unresolved_state", "note"]),
        )
        self.assertEqual(record["delta"], 1)
        self.assertEqual(i4_reconcile.gating_failures([record]), ())


# ------------------------------------------------------------------ determinism / replay


class DeterminismTests(RunnerTestCase):
    def test_same_run_id_produces_byte_identical_packages(self):
        corpus = self.make_corpus()
        out_a, out_b = self.out_dir("a"), self.out_dir("b")
        self.assertEqual(self.invoke(corpus.run_args(out_a, run_id="i4-det")), i4_runner.EXIT_OK)
        self.assertEqual(self.invoke(corpus.run_args(out_b, run_id="i4-det")), i4_runner.EXIT_OK)
        result = i4_output.replay_compare(out_a, out_b)
        self.assertEqual(result["result"], "pass", result)
        self.assertEqual(result["manifest_sha256_a"], result["manifest_sha256_b"])

    def test_replay_reports_the_first_difference(self):
        corpus = self.make_corpus()
        out_a, out_b = self.out_dir("a"), self.out_dir("b")
        self.assertEqual(self.invoke(corpus.run_args(out_a, run_id="i4-det")), i4_runner.EXIT_OK)
        self.assertEqual(self.invoke(corpus.run_args(out_b, run_id="i4-det")), i4_runner.EXIT_OK)
        target = os.path.join(out_b, "w2", "metrics.json")
        with open(target, "a", encoding="utf-8") as handle:
            handle.write("\n")
        result = i4_output.replay_compare(out_a, out_b)
        self.assertEqual(result["result"], "fail")
        self.assertIn("w2/metrics.json", result["first_difference"]["differing"])

    def test_replay_command_exit_codes_and_verdict_file(self):
        corpus = self.make_corpus()
        out_a, out_b = self.out_dir("a"), self.out_dir("b")
        self.assertEqual(self.invoke(corpus.run_args(out_a, run_id="i4-r")), i4_runner.EXIT_OK)
        self.assertEqual(self.invoke(corpus.run_args(out_b, run_id="i4-r")), i4_runner.EXIT_OK)
        verdict = os.path.join(self._tmp, "verdict.json")
        code = self.invoke(["replay", "--a", out_a, "--b", out_b, "--verdict", verdict])
        self.assertEqual(code, i4_runner.EXIT_OK)
        self.assertEqual(self.read_json(verdict)["result"], "pass")
        code = self.invoke(["replay", "--a", out_a, "--b", out_b,
                            "--verdict", os.path.join(out_a, "verdict.json")])
        self.assertEqual(code, i4_runner.EXIT_USAGE)

    def test_replay_requires_two_distinct_directories(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK)
        code = self.invoke(["replay", "--a", out, "--b", out])
        self.assertEqual(code, i4_runner.EXIT_USAGE)

    def test_different_run_id_changes_only_the_declared_run_metadata(self):
        corpus = self.make_corpus()
        out_a, out_c = self.out_dir("a"), self.out_dir("c")
        self.assertEqual(self.invoke(corpus.run_args(out_a, run_id="i4-one")), i4_runner.EXIT_OK)
        self.assertEqual(self.invoke(corpus.run_args(out_c, run_id="i4-two")), i4_runner.EXIT_OK)
        self.assertEqual(i4_output.replay_compare(out_a, out_c)["result"], "fail")

        def normalise(path, run_id):
            with open(path, "r", encoding="utf-8") as handle:
                return handle.read().replace('"%s"' % run_id, '"<run_id>"')

        for relative in (
            "partitions/legacy13/2024/rows/cm01JUL2024bhav.csv.rows.jsonl",
            "w2/associations.jsonl",
        ):
            self.assertEqual(
                normalise(os.path.join(out_a, relative), "i4-one"),
                normalise(os.path.join(out_c, relative), "i4-two"),
                relative,
            )
        # the run-metadata-excluded evidence is identical byte for byte
        relative = "partitions/legacy13/2024/evidence/cm01JUL2024bhav.csv.evidence.json"
        with open(os.path.join(out_a, relative), "rb") as handle:
            first = handle.read()
        with open(os.path.join(out_c, relative), "rb") as handle:
            second = handle.read()
        self.assertEqual(first, second)

    def test_retained_package_is_clock_free_and_path_free(self):
        import re

        corpus = self.make_corpus()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        clock_like = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")
        absolute = re.compile(r"(^[A-Za-z]:\\\\|/(home|tmp|Users|mnt|var)/)")
        for dirpath, dirnames, filenames in os.walk(out):
            for name in filenames:
                path = os.path.join(dirpath, name)
                with open(path, "r", encoding="utf-8") as handle:
                    text = handle.read()
                self.assertIsNone(clock_like.search(text), path)
                self.assertIsNone(absolute.search(text), path)
                for key in ("generated_at", "generated_utc", "hostname", "pid", "duration"):
                    self.assertNotIn('"%s"' % key, text, path)

    def test_jsonl_artifacts_end_with_a_final_newline_and_use_lf(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        for relative in ("INPUT_MANIFEST.jsonl", "RECONCILIATION.jsonl", "PREFLIGHT.jsonl"):
            with open(os.path.join(out, relative), "rb") as handle:
                body = handle.read()
            self.assertTrue(body.endswith(b"\n"), relative)
            self.assertNotIn(b"\r\n", body, relative)


# ------------------------------------------------------------------ run_id behaviour


class RunIdTests(RunnerTestCase):
    def test_run_id_is_required(self):
        corpus = self.make_corpus()
        argv = corpus.run_args(self.out_dir())
        index = argv.index("--run-id")
        del argv[index:index + 2]
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                i4_runner.main(argv)

    def test_invalid_run_id_fails_closed_without_a_completion_marker(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        code = self.invoke(corpus.run_args(out, run_id="bad id!"))
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        self.assertFalse(os.path.isfile(os.path.join(out, "RUN_COMPLETE.json")))

    def test_run_id_is_recorded_in_canonical_provenance_and_run_record(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out, run_id="i4-2026")), i4_runner.EXIT_OK)
        record = self.read_json(os.path.join(out, "RUN_RECORD.json"))
        self.assertEqual(record["run_id"], "i4-2026")
        rows = self.read_jsonl(
            os.path.join(out, "partitions", "udiff34", "2024", "rows",
                         "BhavCopy_NSE_CM_0_0_0_20240703_F_0000.csv.rows.jsonl")
        )
        self.assertTrue(all(row["provenance"]["run_id"] == "i4-2026" for row in rows))


# ------------------------------------------------------------------ verify behaviour


class VerifyTests(RunnerTestCase):
    def run_package(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        return out

    def test_verify_passes_and_reports_each_check(self):
        out = self.run_package()
        code = self.invoke(["verify", "--package", out])
        self.assertEqual(code, i4_runner.EXIT_OK)
        result = json.loads(self.last_stdout)
        self.assertEqual(result["result"], "pass")
        self.assertEqual([check["result"] for check in result["checks"]], ["pass"] * len(result["checks"]))

    def test_verify_detects_artifact_tampering(self):
        out = self.run_package()
        target = os.path.join(out, "w2", "metrics.json")
        with open(target, "a", encoding="utf-8") as handle:
            handle.write("\n")
        code = self.invoke(["verify", "--package", out])
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        result = json.loads(self.last_stdout)
        self.assertIn("verify-02", result["failures"])

    def test_verify_detects_an_unlisted_artifact(self):
        out = self.run_package()
        with open(os.path.join(out, "extra.json"), "w", encoding="utf-8") as handle:
            handle.write("{}\n")
        code = self.invoke(["verify", "--package", out])
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        result = json.loads(self.last_stdout)
        self.assertIn("verify-03", result["failures"])

    def test_verify_fails_without_the_completion_marker(self):
        out = self.run_package()
        os.remove(os.path.join(out, "RUN_COMPLETE.json"))
        code = self.invoke(["verify", "--package", out])
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        result = json.loads(self.last_stdout)
        self.assertIn("verify-04", result["failures"])

    def test_verify_detects_a_partition_manifest_inconsistency(self):
        out = self.run_package()
        target = os.path.join(out, "partitions", "legacy13", "2024", "rows",
                              "cm01JUL2024bhav.csv.rows.jsonl")
        with open(target, "a", encoding="utf-8") as handle:
            handle.write("\n")
        result = i4_output.verify_package(out)
        self.assertEqual(result["result"], "fail")

    def test_verify_detects_identity_drift_in_the_run_record(self):
        out = self.run_package()
        record_path = os.path.join(out, "RUN_RECORD.json")
        record = self.read_json(record_path)
        record["runner_identity"]["runner_sha256"] = "0" * 64
        with open(record_path, "w", encoding="utf-8", newline="") as handle:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        # refresh the manifest entry so the failure can only come from the identity check
        manifest_path = os.path.join(out, "PACKAGE_MANIFEST.sha256")
        lines = []
        with open(manifest_path, "r", encoding="utf-8") as manifest_handle:
            manifest_lines = manifest_handle.read().splitlines()
        for line in manifest_lines:
            digest, relative = line.split("  ", 1)
            if relative == "RUN_RECORD.json":
                digest = i4_output.sha256_file(record_path)
            lines.append("%s  %s" % (digest, relative))
        with open(manifest_path, "w", encoding="utf-8", newline="") as handle:
            handle.write("\n".join(lines) + "\n")
        result = i4_output.verify_package(out)
        self.assertEqual(result["result"], "fail")
        self.assertIn("verify-07", result["failures"])


# ------------------------------------------------------------------ failure retention


class FailureRetentionTests(RunnerTestCase):
    def test_failed_run_retains_evidence_and_no_marker(self):
        corpus = self.make_corpus()
        os.remove(os.path.join(corpus.udiff_root, "BhavCopy_NSE_CM_0_0_0_20240704_F_0000.csv.zip"))
        out = self.out_dir()
        code = self.invoke(corpus.run_args(out))
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        self.assertFalse(os.path.isfile(os.path.join(out, "RUN_COMPLETE.json")))
        failure = self.read_json(os.path.join(out, "RUN_FAILED.json"))
        self.assertEqual(failure["stage"], "preflight")
        self.assertIn("incomplete", failure["note"])
        self.assertEqual(failure["preflight_checks_retained"], len(self.read_jsonl(
            os.path.join(out, "PREFLIGHT.jsonl"))))
        checks = self.read_jsonl(os.path.join(out, "PREFLIGHT.jsonl"))
        failed = [check for check in checks if check["result"] == "divergence"]
        self.assertTrue(failed)
        self.assertEqual(failed[0]["tier"], "A")
        self.assertEqual(failed[0], failure["failed_check"])

    def test_failed_output_root_is_not_reused(self):
        corpus = self.make_corpus()
        os.remove(os.path.join(corpus.legacy_root, "cm01JUL2024bhav.csv.zip"))
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_FAILED)
        # a second attempt into the same (now non-empty) root must fail closed
        code = self.invoke(corpus.run_args(out))
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        self.assertIn("not empty", self.last_stderr + self.last_stdout)

    def test_verify_refuses_an_incomplete_package(self):
        corpus = self.make_corpus()
        os.remove(os.path.join(corpus.legacy_root, "cm01JUL2024bhav.csv.zip"))
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_FAILED)
        code = self.invoke(["verify", "--package", out])
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        result = json.loads(self.last_stdout)
        self.assertEqual(result["result"], "fail")


# ------------------------------------------------------------------ W2 interface (F2)


class W2InterfaceTests(RunnerTestCase):
    """The engine's bounded-memory W2 composition receives the engine's own rows (G-I4-M1).

    The runner retains no ``CanonicalBuild``: each member's rows are fed to the engine's
    ``W2Accumulator`` and then released. These pins hold the boundary — every W2 value in the
    package is produced by the engine, the runner reconstructs nothing, and no fabricated
    row-holder can satisfy the engine.
    """

    def capture_feeds(self, corpus, out, run_id="i4-w2"):
        """Run the CLI with ``W2Accumulator.add_member`` wrapped (engine class, not runner code).

        Returns ``(exit code, [(rows, family), ...])`` in the order the engine received them.
        """
        captured = []
        real_add_member = w2_stream.W2Accumulator.add_member

        def spy(self, rows, family):
            captured.append((rows, family))
            return real_add_member(self, rows, family)

        w2_stream.W2Accumulator.add_member = spy
        self.addCleanup(lambda: setattr(w2_stream.W2Accumulator, "add_member", real_add_member))
        code = self.invoke(corpus.run_args(out, run_id=run_id))
        return code, captured

    def test_members_are_fed_to_the_engine_accumulator_one_at_a_time(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        code, feeds = self.capture_feeds(corpus, out)
        self.assertEqual(code, i4_runner.EXIT_OK, self.last_stderr)
        self.assertEqual(len(feeds), 4, "one engine feed per discovered member")
        for rows, family in feeds:
            self.assertTrue(rows, "the engine receives the member's canonical rows")
            self.assertIsInstance(rows, tuple)
            for row in rows:
                self.assertIsInstance(row, SecurityRow)
            self.assertIn(family, (contract.FAMILY_LEGACY, contract.FAMILY_UDIFF))

    def test_engine_composition_over_the_fed_rows_reproduces_the_package(self):
        """An independent engine composition over the same rows must equal the written package."""
        corpus = self.make_corpus()
        out = self.out_dir()
        code, feeds = self.capture_feeds(corpus, out)
        self.assertEqual(code, i4_runner.EXIT_OK, self.last_stderr)

        # snapshot first: the spy stays installed for the rest of the test and appends to feeds
        feed_snapshot = list(feeds)
        accumulator = w2_stream.W2Accumulator()
        for rows, family in feed_snapshot:
            accumulator.add_member(rows, family)
        calendar = accumulator.calendar(
            i4_inputs.to_inventory_records(tuple(corpus.records))
        )
        metrics = accumulator.metrics()
        stream = accumulator.identity_stream()
        identities = [document.to_dict() for document in stream]
        totals = stream.totals()

        written_calendar = [
            json.loads(line) for line in
            open(os.path.join(out, "w2", "calendar.jsonl"), encoding="utf-8").read().splitlines()
            if line.strip()
        ]
        written_identities = [
            json.loads(line) for line in
            open(os.path.join(out, "w2", "associations.jsonl"), encoding="utf-8").read().splitlines()
            if line.strip()
        ]
        summary = self.read_json(os.path.join(out, "w2", "identity_summary.json"))
        metrics_document = self.read_json(os.path.join(out, "w2", "metrics.json"))
        record = self.read_json(os.path.join(out, "RUN_RECORD.json"))

        self.assertEqual(written_calendar, [day.to_dict() for day in calendar.days])
        self.assertEqual(written_identities, identities)
        self.assertEqual(summary["totals"], totals)
        self.assertEqual(summary["method"], accumulator.association_summary().method)
        self.assertEqual(metrics_document["row_metrics"], metrics.to_dict())
        self.assertEqual(record["counts"]["members"], len(feed_snapshot))
        self.assertEqual(record["counts"]["rows"], sum(len(rows) for rows, _f in feed_snapshot))
        # the runner's observation counter is the additive sum of the engine's per-member
        # observation tuples; the dedicated pin below compares it against an independent build
        self.assertGreaterEqual(record["counts"]["observations"], 0)

    def test_observations_counter_is_additive_over_engine_member_counts(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        code, _feeds = self.capture_feeds(corpus, out)
        self.assertEqual(code, i4_runner.EXIT_OK, self.last_stderr)
        record = self.read_json(os.path.join(out, "RUN_RECORD.json"))
        # the runner only sums each member's engine-derived observation tuple length; an
        # independent batch composition over the same members must agree exactly
        builds = []
        index = i4_inputs.inventory_index(i4_inputs.load_inventory(corpus.inventory_path))
        for archive in i4_inputs.discover_archives(
            {"LEGACY": corpus.legacy_root, "UDIFF": corpus.udiff_root}
        ):
            record_entry = index[(archive.root, archive.relative_path)]
            member = i4_inputs.member_identity(archive.path)
            data = i4_inputs.read_member_bytes(archive.path, member)
            builds.append(i4_runner.build_canonical(
                data, i4_inputs.build_source(record_entry, member, "i4-pin"),
                i4_runner.DEFAULT_CONFIG,
            ))
        self.assertEqual(
            record["counts"]["observations"], sum(len(build.observations) for build in builds)
        )
        self.assertEqual(record["counts"]["rows"], sum(len(build.rows) for build in builds))

    def test_a_row_only_substitute_cannot_satisfy_the_engine(self):
        """Regression pin: the substituted holder the audit found cannot satisfy the engine.

        The engine derives member facts from real builds and reads real canonical rows; a
        row-only holder fails outright, and the runner never constructs one.
        """
        import dataclasses

        corpus = self.make_corpus()
        builds = []
        index = i4_inputs.inventory_index(i4_inputs.load_inventory(corpus.inventory_path))
        for archive in i4_inputs.discover_archives(
            {"LEGACY": corpus.legacy_root, "UDIFF": corpus.udiff_root}
        ):
            record_entry = index[(archive.root, archive.relative_path)]
            member = i4_inputs.member_identity(archive.path)
            data = i4_inputs.read_member_bytes(archive.path, member)
            builds.append(i4_runner.build_canonical(
                data, i4_inputs.build_source(record_entry, member, "i4-pin"),
                i4_runner.DEFAULT_CONFIG,
            ))

        @dataclasses.dataclass(frozen=True)
        class RowOnlyHolder:
            rows: tuple

        # the engine's own builds satisfy the reference composition
        engine_w2 = build_w2(tuple(builds), i4_inputs.to_inventory_records(tuple(corpus.records)))
        self.assertEqual(len(engine_w2.observations), sum(len(b.observations) for b in builds))

        # a row-only substitute does not: the reference composition reads the parse result
        holders = tuple(RowOnlyHolder(build.rows) for build in builds)
        with self.assertRaises(AttributeError):
            build_w2(holders, i4_inputs.to_inventory_records(tuple(corpus.records)))

        # and the streaming composition cannot be fed objects that are not engine rows either
        accumulator = w2_stream.W2Accumulator()
        with self.assertRaises((AttributeError, TypeError)):
            accumulator.add_member([object()], contract.FAMILY_LEGACY)

        # the previous compensation is gone from the runner and its call site cannot recur
        with open(os.path.join(REPO_ROOT, "tools", "i4_runner", "i4_runner.py"),
                  encoding="utf-8") as handle:
            source = handle.read()
        self.assertNotIn("member_facts=", source)
        self.assertNotIn("MemberRows", source)
        self.assertNotIn("RowOnlyHolder", source)

    def test_no_runner_side_w2_reconstruction_remains(self):
        with open(os.path.join(REPO_ROOT, "tools", "i4_runner", "i4_runner.py"),
                  encoding="utf-8") as handle:
            source = handle.read()
        # no retained builds and no batch composition call: the engine's accumulator is consumed
        self.assertNotIn("builds = []", source)
        self.assertNotIn("build_w2(", source)
        self.assertIn("w2_stream.W2Accumulator()", source)
        self.assertIn("accumulator.identity_stream()", source)
        # the runner reads W2 values off engine objects only
        self.assertIn("products.calendar", source)
        self.assertIn("products.metrics", source)
        self.assertIn("products.associations", source)


# ------------------------------------------------------------------ all-quarantined member (F3)


class AllQuarantinedMemberTests(RunnerTestCase):
    def test_member_with_no_usable_rows_fails_closed_with_an_explicit_condition(self):
        corpus = self.make_corpus()
        malformed = support.legacy_member([("too", "few"), ("also", "too", "few", "fields")])
        corpus.add_member(
            "LEGACY", "cm05JUL2024bhav.csv.zip", "cm05JUL2024bhav.csv", malformed, "2024-07-05"
        )
        corpus.write_inventory()
        out = self.out_dir()
        code = self.invoke(corpus.run_args(out, run_id="i4-quarantine"))
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        self.assertIn("no usable canonical rows", self.last_stderr)
        self.assertNotIn("IndexError", self.last_stderr)
        self.assertNotIn("Traceback", self.last_stderr)
        failure = self.read_json(os.path.join(out, "RUN_FAILED.json"))
        self.assertEqual(failure["stage"], "processing")
        self.assertIn("no usable canonical rows", failure["condition"])
        self.assertIn("cm05JUL2024bhav.csv.zip", failure["condition"])
        self.assertEqual(failure["members_processed"], 2)  # the members before it were processed
        self.assertFalse(os.path.isfile(os.path.join(out, "RUN_COMPLETE.json")))

    def test_quarantined_rows_within_a_member_still_succeed(self):
        """Zero usable rows is a governed stop; a member with some usable rows is not."""
        corpus = self.make_corpus()
        rows = [support.legacy_row(SYMBOL="SYM0", ISIN="INE000A01010", TIMESTAMP="05-JUL-2024"),
                ("too", "few")]
        corpus.add_member(
            "LEGACY", "cm05JUL2024bhav.csv.zip", "cm05JUL2024bhav.csv",
            support.legacy_member(rows), "2024-07-05",
        )
        corpus.write_inventory()
        out = self.out_dir()
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        record = self.read_json(os.path.join(out, "RUN_RECORD.json"))
        self.assertEqual(record["counts"]["quarantined"], 1)
        self.assertTrue(os.path.isfile(os.path.join(out, "RUN_COMPLETE.json")))


# ------------------------------------------------------------------ Windows custody (F4)


class PathCustodyTests(RunnerTestCase):
    """Output-root custody must not be defeatable by path case (F4)."""

    def declare(self, out, legacy, udiff):
        return i4_preflight.RunDeclaration(
            repo_root=REPO_ROOT, legacy_root=legacy, udiff_root=udiff, out=out,
            run_id="i4-custody", inventory=GOVERNED_INVENTORY,
        )

    def test_exact_same_path_is_rejected(self):
        corpus_root = os.path.join(self._tmp, "corpus")
        os.makedirs(corpus_root)
        declaration = self.declare(corpus_root, corpus_root, os.path.join(self._tmp, "udiff"))
        problems = i4_preflight.output_placement_problems(declaration)
        self.assertTrue(problems)
        self.assertIn("inside the LEGACY corpus root", problems[0])

    def test_child_path_is_rejected(self):
        corpus_root = os.path.join(self._tmp, "corpus")
        os.makedirs(corpus_root)
        out = os.path.join(corpus_root, "runs", "i4-token")
        declaration = self.declare(out, corpus_root, os.path.join(self._tmp, "udiff"))
        self.assertTrue(i4_preflight.output_placement_problems(declaration))

    def test_sibling_prefix_is_not_a_child(self):
        corpus_root = os.path.join(self._tmp, "corpus")
        sibling = os.path.join(self._tmp, "corpus-archive")
        os.makedirs(corpus_root)
        os.makedirs(sibling)
        declaration = self.declare(sibling, corpus_root, os.path.join(self._tmp, "udiff"))
        self.assertEqual(i4_preflight.output_placement_problems(declaration), [])

    def test_unrelated_path_is_accepted(self):
        corpus_root = os.path.join(self._tmp, "corpus")
        udiff_root = os.path.join(self._tmp, "udiff")
        os.makedirs(corpus_root)
        os.makedirs(udiff_root)
        declaration = self.declare(os.path.join(self._tmp, "runs", "a"), corpus_root, udiff_root)
        self.assertEqual(i4_preflight.output_placement_problems(declaration), [])

    def test_case_different_equivalent_path_is_rejected(self):
        corpus_root = os.path.join(self._tmp, "CorpusRoot")
        os.makedirs(corpus_root)
        # same directory, differently-cased spelling of the parent component
        out = os.path.join(self._tmp, "corpusroot", "runs", "a")
        declaration = self.declare(out, corpus_root, os.path.join(self._tmp, "udiff"))

        self.assertTrue(i4_preflight.path_is_within(out, corpus_root, case_insensitive=True),
                        "case-folded comparison must detect the same directory")
        if os.name == "nt":
            self.assertTrue(i4_preflight.path_is_within(out, corpus_root, case_insensitive=False),
                            "Windows realpath resolves equivalent case spellings to the same directory")
        else:
            self.assertFalse(i4_preflight.path_is_within(out, corpus_root, case_insensitive=False),
                             "a case-sensitive filesystem keeps genuinely distinct paths distinct")
        self.assertEqual(
            i4_preflight.comparison_key(out, True), i4_preflight.comparison_key(out, True)
        )

    def test_case_different_containment_helper_matrix(self):
        base = os.path.join(self._tmp, "CorpusRoot")
        os.makedirs(base)
        cases = [
            (base, base, True),                                   # exact same path
            (os.path.join(base, "runs", "x"), base, True),         # child
            (os.path.join(self._tmp, "corpusroot", "runs", "x"), base, True),  # case-different child
            (os.path.join(self._tmp, "corpusroot"), base, True),   # case-different same path
            (os.path.join(self._tmp, "elsewhere"), base, False),   # unrelated
            (os.path.join(self._tmp, "CorpusRootX"), base, False),  # sibling prefix
        ]
        for child, parent, expected in cases:
            self.assertEqual(
                i4_preflight.path_is_within(child, parent, case_insensitive=True), expected,
                "case-insensitive: %s within %s" % (child, parent),
            )

    def test_cli_refuses_an_output_root_inside_the_corpus(self):
        corpus = self.make_corpus()
        out = os.path.join(corpus.legacy_root, "run-output")
        code = self.invoke(corpus.run_args(out))
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        self.assertFalse(os.path.exists(out))
        self.assertIn("inside the LEGACY corpus root", self.last_stderr)

    def test_legacy_and_udiff_root_equality_is_case_insensitive_on_folding_filesystems(self):
        declaration = self.declare(
            os.path.join(self._tmp, "out"), os.path.join(self._tmp, "Root"),
            os.path.join(self._tmp, "Root"),
        )
        self.assertIn("same directory", " ".join(i4_preflight.output_placement_problems(declaration)))


# ------------------------------------------------------------------ output-root contamination (F5)


class OutputRootContaminationTests(RunnerTestCase):
    def test_pre_existing_non_empty_root_is_never_written_to(self):
        corpus = self.make_corpus()
        out = self.out_dir()
        os.makedirs(os.path.join(out, "unrelated"))
        with open(os.path.join(out, "unrelated", "notes.txt"), "w", encoding="utf-8") as handle:
            handle.write("someone else's data\n")
        before = {}
        for dirpath, dirnames, filenames in os.walk(out):
            for name in filenames:
                path = os.path.join(dirpath, name)
                with open(path, "rb") as handle:
                    before[os.path.relpath(path, out)] = handle.read()

        code = self.invoke(corpus.run_args(out, run_id="i4-contaminate"))
        self.assertEqual(code, i4_runner.EXIT_FAILED)
        self.assertIn("not empty", self.last_stderr)
        self.assertFalse(os.path.isfile(os.path.join(out, "RUN_COMPLETE.json")))
        self.assertFalse(os.path.isfile(os.path.join(out, "RUN_FAILED.json")))
        self.assertFalse(os.path.isfile(os.path.join(out, "PREFLIGHT.jsonl")))

        after = {}
        for dirpath, dirnames, filenames in os.walk(out):
            for name in filenames:
                path = os.path.join(dirpath, name)
                with open(path, "rb") as handle:
                    after[os.path.relpath(path, out)] = handle.read()
        self.assertEqual(before, after, "a pre-existing directory must be left byte-identical")

    def test_contamination_gate_matches_the_declared_contract(self):
        corpus = self.make_corpus()
        empty = self.out_dir("empty")
        os.makedirs(empty)
        declaration = i4_preflight.RunDeclaration(
            repo_root=REPO_ROOT, legacy_root=corpus.legacy_root, udiff_root=corpus.udiff_root,
            out=empty, run_id="i4-gate", inventory=corpus.inventory_path,
        )
        self.assertEqual(i4_preflight.output_root_contamination_problems(declaration), [])

        with open(os.path.join(empty, "leftover.json"), "w", encoding="utf-8") as handle:
            handle.write("{}\n")
        problems = i4_preflight.output_root_contamination_problems(declaration)
        self.assertTrue(problems)
        self.assertIn("not empty", problems[0])

        file_root = os.path.join(self._tmp, "a-file")
        with open(file_root, "w", encoding="utf-8") as handle:
            handle.write("not a directory\n")
        declaration = i4_preflight.RunDeclaration(
            repo_root=REPO_ROOT, legacy_root=corpus.legacy_root, udiff_root=corpus.udiff_root,
            out=file_root, run_id="i4-gate", inventory=corpus.inventory_path,
        )
        self.assertIn("not a directory",
                      " ".join(i4_preflight.output_root_contamination_problems(declaration)))

    def test_empty_pre_existing_root_is_still_usable(self):
        corpus = self.make_corpus()
        out = self.out_dir("new-but-empty")
        os.makedirs(out)
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        self.assertTrue(os.path.isfile(os.path.join(out, "RUN_COMPLETE.json")))

    def test_missing_root_is_created(self):
        corpus = self.make_corpus()
        out = os.path.join(self.out_dir("parent"), "nested", "run")
        self.assertEqual(self.invoke(corpus.run_args(out)), i4_runner.EXIT_OK, self.last_stderr)
        self.assertTrue(os.path.isdir(out))


# ------------------------------------------------------------------ fingerprint bases / CRLF (F6)


class FingerprintBasisTests(RunnerTestCase):
    """The fingerprint is defined over source-controlled canonical bytes (F6)."""

    def prepare_modules(self):
        copy_dir = os.path.join(self._tmp, "modules")
        os.makedirs(copy_dir)
        for name in i4_identity.RUNNER_MODULES:
            shutil.copy(os.path.join(i4_identity.MODULE_DIR, name), os.path.join(copy_dir, name))
        return copy_dir

    def test_lf_basis_is_crlf_invariant_and_the_blob_id_is_the_committed_bytes(self):
        canonical = i4_identity.runner_fingerprint()
        copy_dir = self.prepare_modules()
        self.assertEqual(i4_identity.runner_fingerprint(copy_dir), canonical)
        facts = {fact["module"]: fact for fact in i4_identity.runner_module_facts(copy_dir)}

        target = os.path.join(copy_dir, "i4_output.py")
        with open(target, "rb") as handle:
            body = handle.read()
        self.assertNotIn(b"\r\n", body)
        with open(target, "wb") as handle:
            handle.write(body.replace(b"\n", b"\r\n"))

        converted = {fact["module"]: fact for fact in i4_identity.runner_module_facts(copy_dir)}
        self.assertNotEqual(
            converted["i4_output.py"]["raw_sha256"], facts["i4_output.py"]["raw_sha256"]
        )
        self.assertEqual(
            converted["i4_output.py"]["lf_sha256"], facts["i4_output.py"]["lf_sha256"],
            "the LF basis (and therefore the published transfer verifier) is CRLF-invariant",
        )
        self.assertNotEqual(i4_identity.runner_fingerprint(copy_dir), canonical,
                            "a CRLF-converted module must be detected, not silently accepted")
        self.assertNotEqual(
            converted["i4_output.py"]["git_blob_sha1"], facts["i4_output.py"]["git_blob_sha1"],
            "the blob id reflects the git-committed bytes, so CRLF changes it",
        )

    def test_canonical_bytes_are_the_committed_blob_bytes(self):
        import subprocess

        for name in i4_identity.RUNNER_MODULES:
            path = os.path.join(i4_identity.MODULE_DIR, name)
            with open(path, "rb") as handle:
                body = handle.read()
            self.assertNotIn(b"\r\n", body, name)
            self.assertEqual(
                i4_identity.sha1_git_blob(body),
                subprocess.run(["git", "hash-object", "--no-filters", "--", path],
                               cwd=REPO_ROOT, capture_output=True, text=True,
                               check=True).stdout.strip(),
                "the module bytes in this checkout are the git blob bytes (no filter applied)",
            )

    def test_a_normalised_checkout_is_detected_by_the_fingerprint_and_verifiable_on_the_lf_basis(self):
        """A CRLF checkout must fail the fingerprint gate while staying verifiable per file."""
        canonical_names = {fact["module"]: fact for fact in i4_identity.runner_module_facts()}
        canonical = i4_identity.runner_fingerprint()

        copy_dir = self.prepare_modules()
        target = os.path.join(copy_dir, "i4_identity.py")
        with open(target, "rb") as handle:
            body = handle.read()
        with open(target, "wb") as handle:
            handle.write(body.replace(b"\n", b"\r\n"))

        converted_names = {fact["module"]: fact for fact in i4_identity.runner_module_facts(copy_dir)}
        # raw basis: differs -> the declaration gate fails closed (the intended detection)
        self.assertNotEqual(
            converted_names["i4_identity.py"]["raw_sha256"],
            canonical_names["i4_identity.py"]["raw_sha256"],
        )
        self.assertNotEqual(i4_identity.runner_fingerprint(copy_dir), canonical)
        # LF basis: identical -> a per-file transfer verifier can still prove content identity
        self.assertEqual(
            {module: fact["lf_sha256"] for module, fact in converted_names.items()},
            {module: fact["lf_sha256"] for module, fact in canonical_names.items()},
        )


if __name__ == "__main__":
    unittest.main()
