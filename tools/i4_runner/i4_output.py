"""I4 runner output: deterministic LF artifacts, manifests, verification and replay compare.

Design rules (R6/R7/R8, RD-6, RD-7, RD-8):

* every stored text artifact uses LF endings and ends with a final newline; platform newline
  translation is disabled explicitly (``newline=""``);
* every JSON document is canonical (sorted keys, compact separators, ``ensure_ascii=False``,
  ``allow_nan=False``) via the engine's own serializer;
* JSONL artifacts are streamed line by line so a corpus-scale run never holds a whole
  artifact's text in memory;
* the retained package is clock-free: no timestamp, hostname, absolute path, process id,
  duration or environment value is written anywhere (execution progress goes to stdout/stderr
  only, and transient scratch files are never retained);
* ``PACKAGE_MANIFEST.sha256`` covers every retained artifact except itself and the completion
  marker; ``RUN_COMPLETE.json`` is written **last** and carries the manifest's own hash, so a
  package without it is incomplete by construction (RD-9);
* every retained artifact is labelled with its MD-05 logical durability class by an exhaustive
  rule set, and an artifact matching no rule or more than one rule fails closed.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import sys

if __package__:
    from . import i4_identity as identity
    from . import i4_inputs as inputs
else:  # direct script execution
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import i4_identity as identity  # type: ignore
    import i4_inputs as inputs  # type: ignore

from nse_engine.serialize import canonical_json  # noqa: E402

PACKAGE_MANIFEST = "PACKAGE_MANIFEST.sha256"
COMPLETION_MARKER = "RUN_COMPLETE.json"
FAILURE_RECORD = "RUN_FAILED.json"
UNMANIFESTED = (PACKAGE_MANIFEST, COMPLETION_MARKER)

#: MD-05 logical durability classes, applied by exhaustive rule (RD-7, MD-05).
ARTIFACT_CLASS_RULES = (
    {"class": 1, "label": "authoritative engine output", "pattern": "partitions/*/*/rows/*.rows.jsonl"},
    {"class": 2, "label": "derived output (W2)", "pattern": "w2/calendar.jsonl"},
    {"class": 2, "label": "derived output (W2)", "pattern": "w2/associations.jsonl"},
    {"class": 2, "label": "derived output (W2)", "pattern": "w2/identity_summary.json"},
    {"class": 2, "label": "derived output (W2)", "pattern": "w2/metrics.json"},
    {"class": 3, "label": "provenance / evidence", "pattern": "partitions/*/*/evidence/*.evidence.json"},
    {"class": 3, "label": "provenance / evidence", "pattern": "w2/unresolved.jsonl"},
    {"class": 3, "label": "provenance / evidence", "pattern": "INPUT_MANIFEST.jsonl"},
    {"class": 3, "label": "provenance / evidence", "pattern": "PREFLIGHT.jsonl"},
    {"class": 3, "label": "provenance / evidence", "pattern": "RECONCILIATION.jsonl"},
    {"class": 3, "label": "provenance / evidence", "pattern": "GOVERNED_INPUTS.json"},
    {"class": 3, "label": "provenance / evidence", "pattern": "RUN_RECORD.json"},
    {"class": 3, "label": "provenance / evidence", "pattern": "manifests/*.sha256"},
    {"class": 3, "label": "provenance / evidence", "pattern": PACKAGE_MANIFEST},
    {"class": 3, "label": "provenance / evidence", "pattern": COMPLETION_MARKER},
)

#: Transient (MD-05 class 4) — must never be retained inside the package.
TRANSIENT_PATTERNS = ("*.tmp", "*.log", "*.part", "scratch/*")


class OutputError(inputs.GoverningFailure):
    """A package assembly condition failed (fail-closed: no completion marker)."""


def classify_artifact(relative_path: str) -> dict:
    """Return the single matching MD-05 class rule; fail closed on 0 or >1 matches."""
    matches = [
        rule for rule in ARTIFACT_CLASS_RULES if fnmatch.fnmatch(relative_path, rule["pattern"])
    ]
    if len(matches) != 1:
        raise OutputError(
            "artifact %r matches %d durability-class rules (exactly one required)"
            % (relative_path, len(matches))
        )
    return matches[0]


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1 << 20)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def manifest_line(relative_path: str, digest: str) -> str:
    return "%s  %s\n" % (digest, relative_path)


class OutputWriter:
    """Writes the run package. Every artifact is LF-canonical and clock-free."""

    def __init__(self, out_dir: str):
        self.out_dir = out_dir
        self._handles = {}

    # ---------------------------------------------------------------- primitives
    def path(self, relative_path: str) -> str:
        return os.path.join(self.out_dir, relative_path.replace("/", os.sep))

    def _ensure_parent(self, relative_path: str) -> None:
        parent = os.path.dirname(self.path(relative_path))
        if parent:
            os.makedirs(parent, exist_ok=True)

    def write_text(self, relative_path: str, text: str) -> None:
        self._ensure_parent(relative_path)
        with open(self.path(relative_path), "w", encoding="utf-8", newline="") as handle:
            handle.write(text)

    def write_json(self, relative_path: str, document) -> None:
        self.write_text(relative_path, canonical_json(document) + "\n")

    def append_jsonl(self, relative_path: str, document) -> None:
        handle = self._handles.get(relative_path)
        if handle is None:
            self._ensure_parent(relative_path)
            handle = open(
                self.path(relative_path), "w", encoding="utf-8", newline=""
            )
            self._handles[relative_path] = handle
        handle.write(canonical_json(document) + "\n")

    def write_jsonl(self, relative_path: str, documents) -> None:
        for document in documents:
            self.append_jsonl(relative_path, document)
        self.close_jsonl()

    def close_jsonl(self) -> None:
        for handle in self._handles.values():
            handle.close()
        self._handles = {}

    # ---------------------------------------------------------------- layout
    @staticmethod
    def partition_dir(family: str, year: str) -> str:
        return "partitions/%s/%s" % (family, year)

    @staticmethod
    def rows_path(family: str, year: str, stem: str) -> str:
        return "%s/rows/%s.rows.jsonl" % (OutputWriter.partition_dir(family, year), stem)

    @staticmethod
    def evidence_path(family: str, year: str, stem: str) -> str:
        return "%s/evidence/%s.evidence.json" % (OutputWriter.partition_dir(family, year), stem)

    @staticmethod
    def manifest_path(family: str, year: str) -> str:
        return "manifests/%s_%s.sha256" % (family, year)

    def retained_files(self) -> tuple:
        """Every retained file (relative paths, sorted); excludes manifest and marker."""
        found = []
        for dirpath, dirnames, filenames in os.walk(self.out_dir):
            dirnames.sort()
            for name in sorted(filenames):
                relative = os.path.relpath(
                    os.path.join(dirpath, name), self.out_dir
                ).replace(os.sep, "/")
                if relative in UNMANIFESTED:
                    continue
                found.append(relative)
        return tuple(sorted(found))

    # ---------------------------------------------------------------- manifests
    def write_manifest(self, relative_path: str, files) -> str:
        lines = [manifest_line(path, sha256_file(self.path(path))) for path in sorted(files)]
        text = "".join(lines)
        self.write_text(relative_path, text)
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def write_package_manifest(self) -> str:
        files = self.retained_files()
        for path in files:
            classify_artifact(path)  # fail closed on an unclassifiable artifact
        return self.write_manifest(PACKAGE_MANIFEST, files)

    def write_completion(self, manifest_digest: str, payload: dict) -> None:
        document = dict(payload)
        document["package_manifest_sha256"] = manifest_digest
        self.write_json(COMPLETION_MARKER, document)

    def write_failure(self, payload: dict) -> None:
        self.close_jsonl()
        self.write_json(FAILURE_RECORD, payload)


# ------------------------------------------------------------------ verification


def _parse_manifest(path: str) -> tuple:
    entries = []
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    if text and not text.endswith("\n"):
        raise OutputError("manifest does not end with a final newline: %s" % path)
    for line in text.splitlines():
        if not line:
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2:
            raise OutputError("malformed manifest line: %r" % line)
        digest, relative = parts
        entries.append((digest, relative))
    return tuple(entries)


def self_check(out_dir: str) -> tuple:
    """In-run self-check of the freshly written package (before the completion marker).

    Verifies every manifest entry against the artifact bytes and that no unlisted artifact
    exists. Returns ``(ok, detail)``; a failure is a package-assembly failure (RD-9 case 4/5).
    """
    manifest_path = os.path.join(out_dir, PACKAGE_MANIFEST)
    if not os.path.isfile(manifest_path):
        return False, {"reason": "package manifest missing"}
    entries = _parse_manifest(manifest_path)
    mismatch = []
    for digest, relative in entries:
        path = os.path.join(out_dir, relative.replace("/", os.sep))
        if not os.path.isfile(path):
            mismatch.append({"path": relative, "reason": "missing"})
        elif sha256_file(path) != digest:
            mismatch.append({"path": relative, "reason": "hash mismatch"})
    listed = {relative for _digest, relative in entries}
    unlisted = []
    for dirpath, dirnames, filenames in os.walk(out_dir):
        dirnames.sort()
        for name in sorted(filenames):
            relative = os.path.relpath(os.path.join(dirpath, name), out_dir).replace(os.sep, "/")
            if relative in UNMANIFESTED:
                continue
            if relative not in listed:
                unlisted.append(relative)
    detail = {
        "manifest_entries": len(entries),
        "mismatches": mismatch[:20],
        "unlisted": sorted(unlisted)[:20],
    }
    return (not mismatch and not unlisted), detail


def verify_package(out_dir: str, check_identity: bool = True) -> dict:
    """Verify a completed package against its own manifests (offline; no corpus access)."""
    checks = []

    def add(check_id: str, ok: bool, detail) -> None:
        checks.append({"check_id": check_id, "result": "pass" if ok else "fail", "detail": detail})

    manifest_path = os.path.join(out_dir, PACKAGE_MANIFEST)
    if not os.path.isfile(manifest_path):
        add("verify-01", False, "package manifest missing")
        return {"result": "fail", "checks": tuple(checks)}
    entries = _parse_manifest(manifest_path)
    add("verify-01", True, {"manifest_entries": len(entries)})

    missing, mismatched = [], []
    for digest, relative in entries:
        path = os.path.join(out_dir, relative.replace("/", os.sep))
        if not os.path.isfile(path):
            missing.append(relative)
            continue
        if sha256_file(path) != digest:
            mismatched.append(relative)
    add("verify-02", not missing and not mismatched,
        {"missing": sorted(missing)[:20], "hash_mismatch": sorted(mismatched)[:20]})

    listed = {relative for _digest, relative in entries}
    present = []
    for dirpath, dirnames, filenames in os.walk(out_dir):
        dirnames.sort()
        for name in sorted(filenames):
            relative = os.path.relpath(os.path.join(dirpath, name), out_dir).replace(os.sep, "/")
            if relative in UNMANIFESTED:
                continue
            present.append(relative)
    unlisted = sorted(set(present) - listed)
    add("verify-03", not unlisted, {"unlisted": unlisted[:20]})

    manifest_digest = sha256_file(manifest_path)
    marker_path = os.path.join(out_dir, COMPLETION_MARKER)
    marker_ok = False
    marker_detail = "completion marker missing (an incomplete package must not be verified as complete)"
    run_id = None
    if os.path.isfile(marker_path):
        with open(marker_path, "r", encoding="utf-8") as handle:
            marker = json.load(handle)
        run_id = marker.get("run_id")
        marker_ok = marker.get("package_manifest_sha256") == manifest_digest
        marker_detail = {
            "marker_manifest_sha256": marker.get("package_manifest_sha256"),
            "computed_manifest_sha256": manifest_digest,
            "run_id": run_id,
        }
    add("verify-04", marker_ok, marker_detail)

    partition_bad = []
    for digest, relative in entries:
        if not relative.startswith("manifests/") or not relative.endswith(".sha256"):
            continue
        for entry_digest, entry_relative in _parse_manifest(os.path.join(out_dir, relative)):
            target = os.path.join(out_dir, entry_relative.replace("/", os.sep))
            if not os.path.isfile(target) or sha256_file(target) != entry_digest:
                partition_bad.append("%s :: %s" % (relative, entry_relative))
    add("verify-05", not partition_bad, {"partition_manifest_inconsistencies": partition_bad[:20]})

    class_bad = []
    for relative in present:
        try:
            classify_artifact(relative)
        except OutputError as exc:
            class_bad.append(str(exc))
    add("verify-06", not class_bad, {"unclassifiable": class_bad[:20]})

    if check_identity:
        record_path = os.path.join(out_dir, "RUN_RECORD.json")
        identity_ok, identity_detail = False, "run record missing"
        if os.path.isfile(record_path):
            with open(record_path, "r", encoding="utf-8") as handle:
                recorded = json.load(handle)
            engine_recorded = recorded.get("engine_identity", {}).get("tool_sha256")
            runner_recorded = recorded.get("runner_identity", {}).get("runner_sha256")
            engine_now = identity.engine_fingerprint()
            runner_now = identity.runner_fingerprint()
            identity_ok = engine_recorded == engine_now and runner_recorded == runner_now
            identity_detail = {
                "engine_recorded": engine_recorded,
                "engine_now": engine_now,
                "runner_recorded": runner_recorded,
                "runner_now": runner_now,
            }
        add("verify-07", identity_ok, identity_detail)

    failures = [check for check in checks if check["result"] == "fail"]
    return {
        "result": "fail" if failures else "pass",
        "checks": tuple(checks),
        "failures": tuple(check["check_id"] for check in failures),
        "run_id": run_id,
    }


def replay_compare(dir_a: str, dir_b: str) -> dict:
    """Byte-for-byte comparison of two completed packages (RD-9 case 6, MD-03 #11)."""
    if os.path.abspath(dir_a) == os.path.abspath(dir_b):
        raise OutputError("replay requires two distinct package directories")

    def listing(root: str) -> dict:
        found = {}
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames.sort()
            for name in sorted(filenames):
                full = os.path.join(dirpath, name)
                relative = os.path.relpath(full, root).replace(os.sep, "/")
                found[relative] = sha256_file(full)
        return found

    files_a, files_b = listing(dir_a), listing(dir_b)
    only_a = sorted(set(files_a) - set(files_b))
    only_b = sorted(set(files_b) - set(files_a))
    differing = sorted(
        relative
        for relative in set(files_a) & set(files_b)
        if files_a[relative] != files_b[relative]
    )
    first_difference = None
    if only_a or only_b or differing:
        first_difference = {
            "only_in_a": only_a[:20],
            "only_in_b": only_b[:20],
            "differing": differing[:20],
            "differing_count": len(differing),
        }
    return {
        "result": "fail" if first_difference else "pass",
        "run_metadata_declared": ["provenance.run_id"],
        "files_a": len(files_a),
        "files_b": len(files_b),
        "first_difference": first_difference,
        "manifest_sha256_a": files_a.get(PACKAGE_MANIFEST),
        "manifest_sha256_b": files_b.get(PACKAGE_MANIFEST),
        "note": (
            "total comparison: no exclusion list is consulted. A mismatch is REPLAY-FAILED and "
            "must not be normalised away (RD-9 case 6)."
        ),
    }
