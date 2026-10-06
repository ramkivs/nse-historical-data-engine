"""W2-F: determinism of the W2 derivations (W2 prompt §10 F; D05 §9).

Two independent executions in separate interpreter processes over the same governed inputs must
produce byte-identical W2 artifacts. With different W1 run ids the artifacts must differ *only*
in the single declared run-metadata field (``provenance.run_id``, ``contract.RUN_METADATA_FIELDS``)
— the same governed treatment W1 applies to its own artifacts. Nothing is normalized away: the
comparison uses the declared exclusion, and a control assertion proves the field really differs.

W2 derived records inherit provenance from the W1 rows they were derived from, so the run id can
appear inside a provenance block — never anywhere else (asserted below by walking the JSON).
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

from tests import support
from nse_engine import contract

HARNESS = r'''
import hashlib
import json
import os
import sys

repo_root, out_dir, run_id = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(repo_root, "src"))
sys.path.insert(0, repo_root)

from nse_engine.overlay_evidence import assemble_disposition
from nse_engine.serialize import evidence_json, rows_jsonl
from tests import support


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


os.makedirs(out_dir, exist_ok=True)
w2 = support.build_w2_samples(run_id=run_id)

calendar_document = {
    "days": [day.to_dict() for day in w2.calendar.days],
    "formats": [list(item) for item in w2.calendar.formats],
    "label_status_counts": dict(w2.calendar.label_status_counts()),
    "totals": w2.calendar.totals(),
    "unresolved_dates": list(w2.calendar.unresolved_dates()),
    "weekday_histogram": dict(w2.calendar.weekday_histogram()),
}
association_document = {
    "identities": [identity.to_dict() for identity in w2.associations.identities],
    "method": w2.associations.method,
    "overlay_rows_excluded": [list(item) for item in w2.associations.overlay_rows_excluded],
    "totals": w2.associations.totals(),
    "unkeyed": [group.to_dict() for group in w2.associations.unkeyed],
}
disposition_document = assemble_disposition(
    w2.builds,
    support.load_inventory_records(),
    support.load_file_metric_records(),
    support.load_overlay_fixture_rows(),
).to_dict()
metrics_document = w2.metrics.to_dict()
members_document = {
    "members": [
        {"business_date": build.rows[0].business_date, "member_name": build.source.member_name,
         "rows": len(build.rows), "observations": len(build.observations)}
        for build in w2.builds
    ],
    "totals": w2.totals(),
}

w1_rows = rows_jsonl([row for build in w2.builds for row in build.rows], include_run_metadata=False)
w1_evidence = "".join(evidence_json(build) + "\n" for build in w2.builds)

artifacts = {
    "w2_calendar.json": canonical_json(calendar_document) + "\n",
    "w2_associations.json": canonical_json(association_document) + "\n",
    "w2_disposition.json": canonical_json(disposition_document) + "\n",
    "w2_metrics.json": canonical_json(metrics_document) + "\n",
    "w2_members.json": canonical_json(members_document) + "\n",
    "w1_rows.norunmeta.jsonl": w1_rows,
    "w1_member_evidence.jsonl": w1_evidence,
}
for name, text in artifacts.items():
    write_text(os.path.join(out_dir, name), text)
manifest_lines = []
for name in sorted(artifacts):
    digest = hashlib.sha256(artifacts[name].encode("utf-8")).hexdigest()
    manifest_lines.append("%s  %s" % (digest, name))
write_text(os.path.join(out_dir, "MANIFEST.sha256"), "\n".join(manifest_lines) + "\n")

print(
    "days=%d files=%d missing=%d identities=%d associations=%d rows=%d observations=%d "
    "overlay_excluded=%d unkeyed=%d cause=%s diff=%d"
    % (
        w2.calendar.span_weekdays,
        w2.calendar.files,
        len(w2.calendar.missing_days),
        w2.associations.totals()["identities"],
        w2.associations.totals()["associations"],
        len(w2.rows),
        len(w2.observations),
        w2.associations.totals()["overlay_rows_excluded"],
        w2.associations.totals()["unkeyed_rows"],
        disposition_document["cause"],
        disposition_document["matched_diff_verdict"],
    )
)
'''

EXPECTED_SUMMARY = (
    "days=2609 files=2462 missing=147 identities=1435 associations=2134 rows=3554 "
    "observations=88 overlay_excluded=88 unkeyed=0 cause=fixture_truncation_source_coverage diff=74"
)
RUN_ID_FIELD = contract.RUN_METADATA_FIELDS[0]  # "provenance.run_id"
W2_MODULES = ("calendar", "identity", "metrics", "overlay_evidence", "evidence_inputs")


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _digest(obj) -> str:
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


def _drop_declared_run_metadata(node):
    """Remove exactly the declared run-metadata field (```provenance.run_id``) from a document."""
    if isinstance(node, dict):
        if "provenance" in node:
            provenance = node["provenance"]
            if isinstance(provenance, list):
                node = dict(node)
                node["provenance"] = [
                    {key: value for key, value in block.items() if key != "run_id"}
                    if isinstance(block, dict)
                    else block
                    for block in provenance
                ]
            elif isinstance(provenance, dict) and "run_id" in provenance:
                node = dict(node)
                node["provenance"] = {
                    key: value for key, value in provenance.items() if key != "run_id"
                }
        return {key: _drop_declared_run_metadata(value) for key, value in node.items()}
    if isinstance(node, list):
        return [_drop_declared_run_metadata(item) for item in node]
    return node


def _run_id_paths(node, run_ids, path=""):
    """Every JSON path whose value is one of the supplied run ids."""
    found = []
    if isinstance(node, dict):
        for key, value in node.items():
            found.extend(_run_id_paths(value, run_ids, "%s.%s" % (path, key) if path else key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(_run_id_paths(value, run_ids, "%s[%d]" % (path, index)))
    elif isinstance(node, str) and node in run_ids:
        found.append(path)
    return found


def _run_harness(work_dir, run_id, tag):
    script_path = os.path.join(work_dir, "w2_harness.py")
    with open(script_path, "w", encoding="utf-8", newline="") as handle:
        handle.write(HARNESS)
    out_dir = os.path.join(work_dir, "out-" + tag)
    completed = subprocess.run(
        [sys.executable, script_path, support.REPO_ROOT, out_dir, run_id],
        check=True,
        capture_output=True,
        text=True,
        cwd=support.REPO_ROOT,
    )
    return completed.stdout.strip(), out_dir


class IndependentExecutionDeterminismTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._temp = tempfile.TemporaryDirectory()
        cls.summaries = {}
        cls.outputs = {}
        for tag, run_id in (
            ("same-a", "w2-run"),
            ("same-b", "w2-run"),
            ("diff-a", "w2-a"),
            ("diff-b", "w2-b"),
        ):
            summary, out_dir = _run_harness(cls._temp.name, run_id, tag)
            cls.summaries[tag] = summary
            cls.outputs[tag] = out_dir

    @classmethod
    def tearDownClass(cls):
        cls._temp.cleanup()

    def _read(self, tag, name):
        with open(os.path.join(self.outputs[tag], name), "rb") as handle:
            return handle.read()

    def _names(self, tag):
        return sorted(os.listdir(self.outputs[tag]))

    def test_every_execution_did_the_expected_work(self):
        for tag, summary in self.summaries.items():
            with self.subTest(execution=tag):
                self.assertEqual(summary, EXPECTED_SUMMARY)

    def test_same_run_id_executions_are_byte_identical(self):
        self.assertEqual(self._names("same-a"), self._names("same-b"))
        self.assertIn("MANIFEST.sha256", self._names("same-a"))
        for name in self._names("same-a"):
            with self.subTest(artifact=name):
                self.assertGreater(len(self._read("same-a", name)), 0)
                self.assertEqual(self._read("same-a", name), self._read("same-b", name), name)

    def test_different_run_ids_differ_only_in_the_declared_run_metadata_field(self):
        self.assertEqual(self._names("diff-a"), self._names("diff-b"))
        self.assertEqual(RUN_ID_FIELD, "provenance.run_id")
        self.assertEqual(contract.RUN_METADATA_FIELDS, ("provenance.run_id",))
        identical = []
        differing = []
        for name in self._names("diff-a"):
            first = self._read("diff-a", name).decode("utf-8")
            second = self._read("diff-b", name).decode("utf-8")
            if first == second:
                identical.append(name)
                continue
            differing.append(name)
            if name != "MANIFEST.sha256":  # the manifest hashes a run-id-carrying artifact
                self.assertEqual(
                    first.replace("w2-a", "PLACEHOLDER"),
                    second.replace("w2-b", "PLACEHOLDER"),
                    name,
                )
        # the control: the declared field really does differ, so the exclusion above is meaningful
        self.assertEqual(differing, ["MANIFEST.sha256", "w2_associations.json"])
        self.assertEqual(
            identical,
            [
                "w1_member_evidence.jsonl",
                "w1_rows.norunmeta.jsonl",
                "w2_calendar.json",
                "w2_disposition.json",
                "w2_members.json",
                "w2_metrics.json",
            ],
        )
        self.assertIn("w2-a", self._read("diff-a", "w2_associations.json").decode("utf-8"))
        self.assertNotIn("w2-a", self._read("diff-b", "w2_associations.json").decode("utf-8"))

    def test_run_id_values_appear_only_under_provenance_run_id(self):
        with open(os.path.join(self.outputs["diff-a"], "w2_associations.json"), encoding="utf-8") as handle:
            associations = json.load(handle)
        paths = _run_id_paths(associations, {"w2-a"})
        self.assertGreater(len(paths), 0)
        for path in paths:
            self.assertIsNotNone(
                re.fullmatch(r".*\.provenance\[\d+\]\.run_id", path),
                "run id found outside a provenance block: %s" % path,
            )
        with open(os.path.join(self.outputs["diff-a"], "w2_members.json"), encoding="utf-8") as handle:
            members = json.load(handle)
        self.assertEqual(_run_id_paths(members, {"w2-a"}), [])

    def test_w2_artifacts_carry_no_clock_path_or_foreign_run_metadata(self):
        for name in ("w2_calendar.json", "w2_associations.json", "w2_metrics.json", "w2_disposition.json"):
            with open(os.path.join(self.outputs["diff-a"], name), encoding="utf-8") as handle:
                text = handle.read()
            with self.subTest(artifact=name):
                for token in ("w2-b", "run-aaa", "run-bbb", support.REPO_ROOT, self._temp.name):
                    self.assertNotIn(token, text)
                self.assertIsNone(re.search(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}", text))
                self.assertIsNone(re.search(r"\d{2}:\d{2}:\d{2}", text))
                self.assertIsNone(re.search(r"generated|hostname|platform|cwd|elapsed", text))

    def test_the_overlay_divergence_is_preserved_never_eliminated(self):
        with open(os.path.join(self.outputs["same-a"], "w2_disposition.json"), encoding="utf-8") as handle:
            document = json.load(handle)
        self.assertTrue(document["preserved_not_eliminated"])
        self.assertEqual(document["matched_diff_verdict"], 74)
        self.assertEqual(document["unreproducible_with_base_absent"], 74)
        self.assertEqual(document["unreproducible_with_base_present"], 0)
        self.assertEqual(document["cause"], contract.W1_DIV_OVERLAY_CAUSE_FIXTURE_TRUNCATION)
        self.assertEqual(document["divergence_id"], contract.W1_DIV_OVERLAY_ID)


class InProcessDeterminismTests(unittest.TestCase):
    def test_w2_outputs_are_reproducible_under_different_w1_run_ids(self):
        first = support.build_w2_samples(run_id="run-aaa")
        second = support.build_w2_samples(run_id="run-bbb")
        self.assertEqual(first.calendar.totals(), second.calendar.totals())
        self.assertEqual(
            _digest([day.to_dict() for day in first.calendar.days]),
            _digest([day.to_dict() for day in second.calendar.days]),
        )
        first_identities = [identity.to_dict() for identity in first.associations.identities]
        second_identities = [identity.to_dict() for identity in second.associations.identities]
        self.assertNotEqual(_digest(first_identities), _digest(second_identities))
        self.assertEqual(
            _digest(_drop_declared_run_metadata(first_identities)),
            _digest(_drop_declared_run_metadata(second_identities)),
        )
        self.assertEqual(first.metrics.to_dict(), second.metrics.to_dict())
        self.assertEqual(first.associations.totals()["identities"], 1435)

    def test_repeated_in_process_derivation_is_identical(self):
        first = support.build_w2_samples()
        second = support.build_w2_samples()
        self.assertEqual(first.calendar.totals(), second.calendar.totals())
        self.assertEqual(
            _digest([identity.to_dict() for identity in first.associations.identities]),
            _digest([identity.to_dict() for identity in second.associations.identities]),
        )
        self.assertEqual(first.metrics.to_dict(), second.metrics.to_dict())

    def test_w2_outputs_are_identical_when_the_member_order_changes(self):
        builds = tuple(support.build_sample(name) for name in support.PUBLISHED_SAMPLES)
        labels, holidays, _registry, _document = support.load_calendar_labels()
        from nse_engine.pipeline import build_w2

        forward = build_w2(builds, support.load_inventory_records(), labels, holidays)
        backward = build_w2(
            tuple(reversed(builds)), support.load_inventory_records(), labels, holidays
        )
        self.assertEqual(forward.calendar.totals(), backward.calendar.totals())
        self.assertEqual(
            _digest([day.to_dict() for day in forward.calendar.days]),
            _digest([day.to_dict() for day in backward.calendar.days]),
        )
        self.assertEqual(forward.metrics.to_dict(), backward.metrics.to_dict())
        self.assertEqual(
            _digest([identity.to_dict() for identity in forward.associations.identities]),
            _digest([identity.to_dict() for identity in backward.associations.identities]),
        )

    def test_calendar_and_metric_derivations_are_stable_under_input_reordering(self):
        inventory = support.load_inventory_records()
        labels, holidays, _registry, _document = support.load_calendar_labels()
        from nse_engine.calendar import derive_calendar
        from nse_engine import metrics

        forward = derive_calendar(inventory, labels, holidays)
        backward = derive_calendar(tuple(reversed(inventory)), labels, holidays)
        self.assertEqual(
            _digest([day.to_dict() for day in forward.days]),
            _digest([day.to_dict() for day in backward.days]),
        )
        first = metrics.fold_file_metrics(support.load_file_metric_records())
        second = metrics.fold_file_metrics(tuple(reversed(support.load_file_metric_records())))
        self.assertEqual(first, second)


class W2StaticDeterminismGuardsTests(unittest.TestCase):
    """The W2 modules must stay IO-free, clock-free, randomness-free and environment-free."""

    FORBIDDEN_IMPORTS = (
        "random",
        "uuid",
        "socket",
        "subprocess",
        "urllib",
        "requests",
        "time",
        "os",
        "pathlib",
        "glob",
        "shutil",
        "csv",
        "json",
    )
    FORBIDDEN_CALLS = ("open", "print", "input", "eval", "exec", "__import__", "compile")

    def _source(self, module):
        path = os.path.join(support.SRC_DIR, "nse_engine", module + ".py")
        with open(path, encoding="utf-8") as handle:
            return handle.read()

    def _tree(self, module):
        path = os.path.join(support.SRC_DIR, "nse_engine", module + ".py")
        return ast.parse(self._source(module), filename=path)

    def test_no_forbidden_imports_in_the_w2_modules(self):
        for module in W2_MODULES:
            for node in ast.walk(self._tree(module)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotIn(alias.name.split(".")[0], self.FORBIDDEN_IMPORTS, module)
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    self.assertNotIn((node.module or "").split(".")[0], self.FORBIDDEN_IMPORTS, module)

    def test_no_io_or_evaluation_calls_in_the_w2_modules(self):
        for module in W2_MODULES:
            for node in ast.walk(self._tree(module)):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, self.FORBIDDEN_CALLS, module)

    def test_no_clock_or_randomness_attribute_access(self):
        forbidden = ("now", "today", "utcnow", "monotonic", "random", "getenv", "environ")
        for module in W2_MODULES:
            for node in ast.walk(self._tree(module)):
                if isinstance(node, ast.Attribute):
                    self.assertNotIn(node.attr, forbidden, module)

    def test_w2_modules_do_not_install_hooks_or_run_as_scripts(self):
        for module in W2_MODULES:
            source = self._source(module)
            for token in ("os.environ", "sys.path", "atexit", "signal.", '__main__'):
                self.assertNotIn(token, source, module)


if __name__ == "__main__":
    unittest.main()
