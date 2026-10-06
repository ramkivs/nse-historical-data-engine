#!/usr/bin/env python3
"""W1 determinism harness (D05 §9; W1 prompt §9).

Runs the W1 reference pipeline over the eight published row-sample fixtures and writes the
LF-normalized canonical artifacts plus a sha256 manifest, so two independent executions can
be compared byte for byte:

    python3 tests/determinism_check.py --out /tmp/run-a
    python3 tests/determinism_check.py --out /tmp/run-b
    diff -r /tmp/run-a /tmp/run-b

Declared run-metadata is exactly ``provenance.run_id`` (D05 §9.4): with the same run id
(including the default of none) two runs are byte-identical; with different run ids the
canonical rows differ only in that field, and the run-metadata-excluded artifacts are
byte-identical. Neither case is normalized to make a comparison pass.

No clock value, hostname, path, environment variable or randomness enters any artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from nse_engine import build_canonical, contract  # noqa: E402
from nse_engine.serialize import build_evidence, rows_jsonl, text_sha256  # noqa: E402
from tests import support  # noqa: E402


def canonical_json(obj) -> str:
    import json

    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def write_text(path: str, text: str) -> None:
    # LF endings, final newline (D05 §9.1); newline="" disables platform translation.
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def run(out_dir: str, run_id: str | None) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    rows_all = []
    evidence_lines = []
    for member in support.PUBLISHED_SAMPLES:
        build = build_canonical(
            support.fixture_bytes(member), support.source_for(member, run_id=run_id)
        )
        rows_all.extend(build.rows)
        evidence_lines.append(canonical_json(build_evidence(build)))

    rows_text = rows_jsonl(rows_all)
    rows_determinism_view = rows_jsonl(rows_all, include_run_metadata=False)
    evidence_text = "".join(line + "\n" for line in evidence_lines)
    write_text(os.path.join(out_dir, "canonical_rows.jsonl"), rows_text)
    write_text(os.path.join(out_dir, "canonical_rows.norunmeta.jsonl"), rows_determinism_view)
    write_text(os.path.join(out_dir, "member_evidence.jsonl"), evidence_text)

    manifest_lines = []
    for name in ("canonical_rows.jsonl", "canonical_rows.norunmeta.jsonl", "member_evidence.jsonl"):
        manifest_lines.append("%s  %s\n" % (text_sha256(open(os.path.join(out_dir, name), encoding="utf-8").read()), name))
    write_text(os.path.join(out_dir, "MANIFEST.sha256"), "".join(manifest_lines))

    return {
        "rows": len(rows_all),
        "rows_sha256": text_sha256(rows_text),
        "rows_without_run_metadata_sha256": text_sha256(rows_determinism_view),
        "member_evidence_sha256": text_sha256(evidence_text),
        "manifest_sha256": hashlib.sha256(
            open(os.path.join(out_dir, "MANIFEST.sha256"), "rb").read()
        ).hexdigest(),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="W1 determinism harness (read-only)")
    parser.add_argument("--out", default=None, help="output directory (default: a fresh temp dir)")
    parser.add_argument("--run-id", default=None, help="declared run-metadata value")
    args = parser.parse_args(argv)

    out_dir = args.out or tempfile.mkdtemp(prefix="w1-determinism-")
    try:
        summary = run(out_dir, args.run_id)
    except Exception as exc:  # fail loudly, never write a partial success claim
        print("DETERMINISM RUN FAILED: %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        return 2

    print("out=%s" % out_dir)
    print("run_id=%r" % args.run_id)
    print("spec_version=%s tool=%s/%s" % (contract.SPEC_VERSION, contract.TOOL_NAME, contract.TOOL_VERSION))
    for key in (
        "rows",
        "rows_sha256",
        "rows_without_run_metadata_sha256",
        "member_evidence_sha256",
        "manifest_sha256",
    ):
        print("%s=%s" % (key, summary[key]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
