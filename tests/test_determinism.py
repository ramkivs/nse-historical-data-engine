"""Determinism verification (D05 §9; W1 prompt §2 J, §9).

Two independent executions over the same input and the same governed configuration must
produce byte-identical canonical output and evidence. The only declared run-metadata field
is ``provenance.run_id`` (D05 §9.4) and a test asserts that artifacts differing by a run id
differ *only* in that field — nothing is normalized away to make a comparison pass.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

from tests import support
from nse_engine import contract
from nse_engine.pipeline import EngineConfig
from nse_engine.serialize import canonical_row_dict, build_evidence, evidence_json, rows_jsonl, text_sha256

HARNESS = os.path.join(support.REPO_ROOT, "tests", "determinism_check.py")


class RepeatedExecutionTests(unittest.TestCase):
    def test_every_published_member_is_byte_identical_across_two_runs(self):
        for name in support.PUBLISHED_SAMPLES:
            with self.subTest(member=name):
                first = support.build_sample(name, run_id="w1-run")
                second = support.build_sample(name, run_id="w1-run")
                self.assertEqual(rows_jsonl(first.rows), rows_jsonl(second.rows))
                self.assertEqual(evidence_json(first), evidence_json(second))
                self.assertEqual(
                    text_sha256(evidence_json(first)), text_sha256(evidence_json(second))
                )

    def test_evidence_contains_no_clock_path_or_environment_value(self):
        build = support.build_sample(support.PUBLISHED_SAMPLES[0])
        evidence = build_evidence(build)
        serialized = evidence_json(build)

        def keys_of(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    yield key
                    yield from keys_of(value)
            elif isinstance(node, list):
                for item in node:
                    yield from keys_of(item)

        # no execution-metadata keys anywhere in the evidence document
        for forbidden in ("generated", "utc", "hostname", "cwd", "elapsed", "executed_at", "run_at"):
            self.assertFalse(
                [key for key in keys_of(evidence) if forbidden in key.lower()],
                "evidence carries an execution-metadata key matching %r" % forbidden,
            )
        # no date-with-time value anywhere (the governed column name TIMESTAMP is data, not a clock)
        self.assertIsNone(re.search(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}", serialized))
        self.assertIsNone(re.search(r"\d{2}:\d{2}:\d{2}", serialized))
        self.assertEqual(
            sorted(evidence["governed_config"]),
            ["emit_overlay_observations", "overlay_series", "spec_version", "units_provenance_note"],
        )
        self.assertEqual(evidence["spec_version"], contract.SPEC_VERSION)
        self.assertEqual(evidence["config_fingerprint"], EngineConfig().fingerprint())

    def test_determinism_holds_across_independent_processes(self):
        python = sys.executable
        with tempfile.TemporaryDirectory() as root:
            run_a = os.path.join(root, "a")
            run_b = os.path.join(root, "b")
            for out in (run_a, run_b):
                completed = subprocess.run(
                    [python, HARNESS, "--out", out],
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=support.REPO_ROOT,
                )
                self.assertIn("rows=3554", completed.stdout)
            for artifact in (
                "canonical_rows.jsonl",
                "canonical_rows.norunmeta.jsonl",
                "member_evidence.jsonl",
                "MANIFEST.sha256",
            ):
                with open(os.path.join(run_a, artifact), "rb") as handle:
                    first = handle.read()
                with open(os.path.join(run_b, artifact), "rb") as handle:
                    second = handle.read()
                self.assertEqual(first, second, artifact)
            with open(os.path.join(run_a, "MANIFEST.sha256"), "rb") as handle:
                manifest = handle.read()
            self.assertEqual(manifest.count(b"\n"), 3)
            self.assertTrue(manifest.endswith(b"\n"))

    def test_artifact_hashes_are_stable_and_reported(self):
        build = support.build_sample(support.PUBLISHED_SAMPLES[0])
        evidence = build_evidence(build)
        self.assertEqual(
            evidence["rows_jsonl_sha256"],
            text_sha256(rows_jsonl(build.rows, include_run_metadata=False)),
        )
        self.assertEqual(evidence["run_metadata_fields"], list(contract.RUN_METADATA_FIELDS))
        self.assertEqual(evidence["row_count"], len(build.rows))


class RunMetadataExclusionTests(unittest.TestCase):
    def test_run_id_is_the_only_declared_run_metadata_field(self):
        self.assertEqual(contract.RUN_METADATA_FIELDS, ("provenance.run_id",))

    def test_artifacts_with_different_run_ids_differ_only_in_run_id(self):
        name = support.PUBLISHED_SAMPLES[0]
        first = support.build_sample(name, run_id="run-aaa")
        second = support.build_sample(name, run_id="run-bbb")
        first_text = rows_jsonl(first.rows)
        second_text = rows_jsonl(second.rows)
        self.assertNotEqual(first_text, second_text)
        row_count = len(first.rows)
        self.assertEqual(first_text.count('"run_id":"run-aaa"'), row_count)
        self.assertEqual(second_text.count('"run_id":"run-bbb"'), row_count)
        self.assertEqual(
            first_text.replace('"run_id":"run-aaa"', '"run_id":"X"'),
            second_text.replace('"run_id":"run-bbb"', '"run_id":"X"'),
        )
        self.assertEqual(
            rows_jsonl(first.rows, include_run_metadata=False),
            rows_jsonl(second.rows, include_run_metadata=False),
        )
        self.assertIn(contract.RUN_METADATA_PLACEHOLDER, rows_jsonl(first.rows, include_run_metadata=False))

    def test_evidence_is_byte_identical_under_a_different_run_id(self):
        name = support.PUBLISHED_SAMPLES[5]
        first = evidence_json(support.build_sample(name, run_id="run-aaa"))
        second = evidence_json(support.build_sample(name, run_id="run-bbb"))
        self.assertEqual(first, second)
        evidence = build_evidence(support.build_sample(name, run_id="run-aaa"))
        other = build_evidence(support.build_sample(name, run_id="run-bbb"))
        self.assertEqual(evidence["rows_jsonl_sha256"], other["rows_jsonl_sha256"])
        self.assertEqual(evidence["config_fingerprint"], other["config_fingerprint"])
        self.assertIn("run_id", json.dumps(evidence))
        self.assertNotIn("run-aaa", json.dumps(evidence))

    def test_row_dicts_differ_only_in_the_declared_field(self):
        name = support.PUBLISHED_SAMPLES[3]
        first = support.build_sample(name, run_id="run-aaa")
        second = support.build_sample(name, run_id="run-bbb")
        for row_a, row_b in zip(first.rows, second.rows):
            data_a = canonical_row_dict(row_a)
            data_b = canonical_row_dict(row_b)
            data_a["provenance"]["run_id"] = "X"
            data_b["provenance"]["run_id"] = "X"
            self.assertEqual(data_a, data_b)


class ConfigSensitivityTests(unittest.TestCase):
    def test_same_configuration_reproduces_and_changed_configuration_is_visible(self):
        member = support.legacy_member(
            [support.legacy_row(SERIES="BL"), support.legacy_row(SERIES="EQ")]
        )
        default = support.parse_synthetic(member, expected_source_date="2016-09-20")
        default_again = support.parse_synthetic(member, expected_source_date="2016-09-20")
        changed = support.parse_synthetic(
            member, expected_source_date="2016-09-20", config=EngineConfig(overlay_series=("T0",))
        )
        self.assertEqual(rows_jsonl(default.rows), rows_jsonl(default_again.rows))
        self.assertEqual(evidence_json(default), evidence_json(default_again))
        self.assertNotEqual(rows_jsonl(default.rows), rows_jsonl(changed.rows))
        self.assertNotEqual(evidence_json(default), evidence_json(changed))
        self.assertNotEqual(
            build_evidence(default)["config_fingerprint"],
            build_evidence(changed)["config_fingerprint"],
        )

    def test_all_published_members_are_stable_under_the_default_config(self):
        first = [rows_jsonl(support.build_sample(name).rows) for name in support.PUBLISHED_SAMPLES]
        second = [rows_jsonl(support.build_sample(name).rows) for name in support.PUBLISHED_SAMPLES]
        self.assertEqual(first, second)


class StaticDeterminismGuardsTests(unittest.TestCase):
    ENGINE_MODULES = ("parsing", "rows", "overlays", "pipeline", "serialize", "contract", "provenance")

    def _code(self, module):
        path = os.path.join(support.SRC_DIR, "nse_engine", module + ".py")
        with open(path, encoding="utf-8") as handle:
            return handle.read()

    def test_engine_uses_no_clock_randomness_environment_or_network(self):
        forbidden = (
            "import random",
            "import uuid",
            "import socket",
            "import subprocess",
            "import urllib",
            "import requests",
            "datetime.now",
            "datetime.today",
            "datetime.utcnow",
            "time.time",
            "os.environ",
            "os.getcwd",
            "os.listdir",
            "glob.glob",
        )
        for module in self.ENGINE_MODULES:
            source = self._code(module)
            for token in forbidden:
                self.assertNotIn(token, source, "%s must not use %r" % (module, token))

    def test_parse_path_modules_perform_no_io_and_no_output(self):
        output_call = re.compile(r"(?<![\w.])print\(")
        for module in ("parsing", "rows", "overlays", "pipeline", "serialize", "contract"):
            source = self._code(module)
            self.assertNotIn("open(", source, module)
            self.assertIsNone(output_call.search(source), module)
            self.assertNotIn("Path(", source, module)

    def test_provenance_fingerprint_reads_only_its_own_module_sources(self):
        source = self._code("provenance")
        self.assertEqual(source.count("open("), 1)
        self.assertIn('"rb"', source)

    def test_json_serialization_is_canonical_compact_and_key_sorted(self):
        build = support.build_sample(support.PUBLISHED_SAMPLES[1])
        text = rows_jsonl(build.rows)
        self.assertTrue(text.endswith("\n"))
        self.assertEqual(text.count("\n"), len(build.rows))
        for line in text.splitlines()[:5]:
            parsed = json.loads(line)
            self.assertEqual(
                line,
                json.dumps(
                    parsed, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
                ),
            )
        # numerics are published text, never floats
        for row in build.rows:
            for key in contract.DECIMAL_FIELDS + contract.INTEGER_FIELDS:
                value = row.value(key)
                self.assertIsInstance(value, str)


if __name__ == "__main__":
    unittest.main()
