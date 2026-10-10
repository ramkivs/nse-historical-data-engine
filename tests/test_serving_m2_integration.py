"""Serving slice — qualified M2 baseline identity + real-package integration (D23 §18 #2).

Two distinct kinds of evidence, kept strictly separate (D24 record §13):

1. *Identity of the qualified baseline* (always executed): the pinned M2 spec
   (``serving.baseline.DEFAULT_M2_SPEC``) is verified against the repository-durable
   D11 transfer evidence (manifest digest, file count, total bytes, run/engine/runner
   identity, archive count). This is an identity check over recorded evidence — it
   does not touch the 21 GB package.

2. *Real-package integration* (executed only when the environment provides the
   qualified M2 package via ``D24_M2_ROOT``): full verification with the pinned spec,
   index build, Q1 dataset summaries, Q2 date-range query, Q3 query, rebuild.
   When the environment does not provide the package, this test is SKIPPED and
   reported as such — it is never represented as passed, and the fixture tests
   never stand in for it.
"""

from __future__ import annotations

import json
import os
import tarfile
import tempfile
import unittest

from tests import support
from serving.archive import load_d01_inventory, query_archive_inventory
from serving.baseline import DEFAULT_M2_SPEC, BaselineError, open_baseline
from serving.detail import query_record_detail
from serving.index import build_index, load_index, write_index
from serving.query import DATE_RANGE_QUERY_ID, query_date_range, query_dataset_summary, query_instrument
from serving.rebuild import rebuild_state

TRANSFER = "evidence/D11_REPLAY_QUALIFICATION_20261009/D11_E1_E10_TRANSFER_20261009.tar.gz"


class M2BaselineIdentityTests(unittest.TestCase):
    """The pinned spec must agree with the repository-durable transfer evidence."""

    @classmethod
    def setUpClass(cls):
        transfer_path = os.path.join(support.REPO_ROOT, TRANSFER)
        with tarfile.open(transfer_path, "r:gz") as tar:
            cls.members = {
                m.name: tar.extractfile(m).read()
                for m in tar.getmembers()
                if m.isfile()
            }

    def _tsv(self):
        text = self.members["D11_E1_E10_TRANSFER_20261009/A.PACKAGE_FILES.tsv"].decode("utf-8")
        return [line.rsplit("\t", 2) for line in text.replace("\r", "").splitlines()[1:] if line]

    def test_pin_file_count_and_total_bytes(self):
        entries = self._tsv()
        self.assertEqual(len(entries), DEFAULT_M2_SPEC.file_count)
        self.assertEqual(sum(int(size) for _p, size, _s in entries), DEFAULT_M2_SPEC.total_bytes)

    def test_pin_manifest_digest(self):
        recorded = dict((path, sha.lower()) for path, _size, sha in self._tsv())
        self.assertEqual(DEFAULT_M2_SPEC.manifest_sha256, recorded["PACKAGE_MANIFEST.sha256"])
        import hashlib

        manifest_bytes = self.members["D11_E1_E10_TRANSFER_20261009/PACKAGE_MANIFEST.sha256"]
        self.assertEqual(DEFAULT_M2_SPEC.manifest_sha256, hashlib.sha256(manifest_bytes).hexdigest())

    def test_pin_run_and_tool_identity(self):
        import json

        record = json.loads(self.members["D11_E1_E10_TRANSFER_20261009/RUN_RECORD.json"].decode("utf-8"))
        self.assertEqual(DEFAULT_M2_SPEC.run_id, record["run_id"])
        self.assertEqual(DEFAULT_M2_SPEC.composite_run_identity, record["composite_run_identity"])
        self.assertEqual(
            DEFAULT_M2_SPEC.engine_tool_sha256,
            record["engine_identity"]["tool_sha256"],
        )
        self.assertEqual(DEFAULT_M2_SPEC.runner_sha256, record["runner_identity"]["runner_sha256"])
        self.assertEqual(DEFAULT_M2_SPEC.archive_count, record["corpus"]["archive_count"])

    def test_pin_row_count_matches_run_record(self):
        import json

        record = json.loads(self.members["D11_E1_E10_TRANSFER_20261009/RUN_RECORD.json"].decode("utf-8"))
        self.assertEqual(record["counts"]["rows"], 5689949)
        self.assertEqual(record["counts"]["members"], DEFAULT_M2_SPEC.archive_count)


@unittest.skipIf(
    not os.environ.get("D24_M2_ROOT"),
    "qualified M2 package not present in this environment (D24_M2_ROOT unset); "
    "real-package integration is PENDING baseline provisioning, not passed",
)
class M2RealPackageIntegrationTests(unittest.TestCase):
    """Runs only when the environment provides the qualified M2 package."""

    @classmethod
    def setUpClass(cls):
        cls.pkg_root = os.environ["D24_M2_ROOT"]
        cls.state = tempfile.mkdtemp(prefix="d24-m2-state-")
        cls.handle = open_baseline(cls.pkg_root, spec=DEFAULT_M2_SPEC)
        cls.index = build_index(cls.handle)
        cls.index_sha = write_index(cls.state, cls.index)

    @classmethod
    def tearDownClass(cls):
        import shutil

        shutil.rmtree(cls.state, ignore_errors=True)

    def test_full_verification_passes_with_pinned_spec(self):
        self.assertEqual(self.handle.manifest_digest, DEFAULT_M2_SPEC.manifest_sha256)
        self.assertEqual(self.handle.checks_passed[-1], "verify-07")
        self.assertEqual(self.handle.run_record["corpus"]["archive_count"], DEFAULT_M2_SPEC.archive_count)

    def test_q3_query_over_real_baseline(self):
        document, _digest = load_index(self.state, self.handle)
        rows = query_instrument(self.handle, document, "RELIANCE", "EQ")
        self.assertGreater(len(rows), 0)
        dates = [row["business_date"] for row in rows]
        self.assertEqual(dates, sorted(dates))
        for row in rows:
            self.assertIn("provenance", row)
            self.assertNotIn("raw_line", row)

    def test_q1_dataset_summary_over_real_baseline(self):
        document, _digest = load_index(self.state, self.handle)
        result = query_dataset_summary(document)
        self.assertEqual(len(result["partitions"]), 12)
        counts = document["counts"]
        self.assertEqual(result["summary"]["row_files"], counts["row_files"])
        self.assertEqual(result["summary"]["row_count"], counts["row_count"])
        self.assertEqual(result["summary"]["instrument_pairs"], counts["instrument_pairs"])
        selected = query_dataset_summary(document, family="legacy13", year=2024)
        self.assertEqual([p["family"] for p in selected["partitions"]], ["legacy13"])
        self.assertEqual(selected["summary"]["row_count"], selected["partitions"][0]["row_count"])
        self.assertEqual(
            query_dataset_summary(document, family="nosuchfamily"),
            {
                "query": "Q1-dataset",
                "selection": {"family": "nosuchfamily", "year": None},
                "partitions": [],
                "summary": {"row_files": 0, "row_count": 0, "instrument_pairs": 0},
            },
        )

    def test_q2_date_range_over_real_baseline(self):
        # 2024-06-21..2024-07-05 is a range with known real rows (D26 evidence
        # fragments: legacy13/2024 cmNN members, business dates within this span).
        document, _digest = load_index(self.state, self.handle)
        rows = query_date_range(self.handle, document, "2024-06-21", "2024-07-05")
        self.assertGreater(len(rows), 0)
        dates = [row["business_date"] for row in rows]
        self.assertEqual(dates, sorted(dates))
        for row in rows:
            self.assertGreaterEqual(row["business_date"], "2024-06-21")
            self.assertLessEqual(row["business_date"], "2024-07-05")
            self.assertEqual(row["serving"]["query"], DATE_RANGE_QUERY_ID)
            self.assertIn("provenance", row)
            self.assertNotIn("raw_line", row)
        # a range with no rows is empty, not an error
        self.assertEqual(query_date_range(self.handle, document, "1990-01-01", "1990-01-02"), ())

    def test_rebuild_reproducibility(self):
        report = rebuild_state(self.handle, self.state)
        self.assertTrue(report["identical"], "rebuild over an unchanged M2 baseline must be byte-identical")
        self.assertEqual(report["rows_scanned"], 5689949)

    def test_q9_archive_inventory_over_real_baseline(self):
        # Q9 over the actual qualified M2 baseline: 2,462 archives, a complete
        # D01 join (every archive_sha256_d01 equal to its D01 inventory sha256),
        # the explicit registry absence, and deterministic repeated output.
        d01 = load_d01_inventory()
        result = query_archive_inventory(self.handle, d01=d01)
        self.assertEqual(result["summary"]["archive_count"], 2462)
        self.assertEqual(len(result["archives"]), 2462)
        self.assertEqual(result["summary"]["d01_inventory"]["present"], True)
        self.assertEqual(result["summary"]["d01_inventory"]["record_count"], 2462)
        for archive in result["archives"]:
            self.assertIsNotNone(archive["d01"])
            self.assertEqual(archive["d01"]["sha256"], archive["archive_sha256_d01"])
            self.assertEqual(archive["registry"], {"present": False, "status": "absent-in-m2-only-release"})
        again = query_archive_inventory(self.handle, d01=d01)
        self.assertEqual(json.dumps(again, sort_keys=True), json.dumps(result, sort_keys=True))

    def test_q7_record_detail_over_real_baseline(self):
        # Q7 over the actual qualified M2 baseline: the row-to-archive join
        # succeeds on authoritative package data, the archive facts and the
        # member-scoped reconciliation records are attached as published,
        # raw_line stays excluded, and the output is deterministic.
        document, _digest = load_index(self.state, self.handle)
        rows = query_instrument(self.handle, document, "RELIANCE", "EQ")
        self.assertGreater(len(rows), 0)
        row = rows[0]
        source_file = row["serving"]["source_file"]
        line_number = row["source_line_number"]
        detail = query_record_detail(self.handle, document, source_file, line_number)
        self.assertEqual(detail["row"]["provenance"], row["provenance"])
        self.assertEqual(detail["row"]["source_line_number"], line_number)
        self.assertNotIn("raw_line", detail["row"])
        archive = detail["archive"]
        self.assertEqual(archive["member_name"], row["provenance"]["member_name"])
        self.assertEqual(archive["file_name"], row["provenance"]["source_archive"])
        self.assertEqual(archive["archive_sha256_d01"], row["provenance"]["archive_sha256"])
        self.assertEqual(archive["engine_family"], row["format_family"])
        self.assertGreater(len(detail["reconciliation"]), 0)
        for record in detail["reconciliation"]:
            self.assertEqual(record["input_identity"]["scope"], "member")
            self.assertEqual(record["input_identity"]["relative_path"], archive["relative_path"])
        again = query_record_detail(self.handle, document, source_file, line_number)
        self.assertEqual(json.dumps(again, sort_keys=True), json.dumps(detail, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
