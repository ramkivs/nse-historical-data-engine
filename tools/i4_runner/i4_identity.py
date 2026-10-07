"""I4 runner identity (RD-3).

Runner-level identity for the I4 corpus-side orchestration layer. This module is a member of
``RUNNER_MODULES``: changing it, or any other declared runner module, changes
``runner_fingerprint()`` and therefore invalidates a run's recorded identity.

Design rules (RD-3):

* the fingerprint covers exactly the declared runner implementation modules, read as raw
  bytes, with the same construction the engine uses for ``tool_fingerprint()``
  (``name \\x00 length \\x00 bytes \\x00``, modules sorted by name);
* no clock, hostname, environment value, checkout path or other filesystem state enters the
  identity — only the declared modules' bytes and the declared engine module set;
* runner identity is **run-level evidence only** and is never injected into canonical rows
  (the frozen provenance field set carries engine identity);
* the composite run identity binds engine + runner + governed inputs + corpus archive set,
  so any change invalidates a run.

This module performs no corpus IO and no network access.
"""

from __future__ import annotations

import hashlib
import os
import sys

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(MODULE_DIR))
SRC_DIR = os.path.join(REPO_ROOT, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from nse_engine import contract  # noqa: E402  (path bootstrap immediately above)

#: Declared runner implementation modules. Order is irrelevant (sorted before hashing);
#: membership is the contract: adding/removing/renaming a file here changes the identity.
RUNNER_MODULES = (
    "i4_identity.py",
    "i4_inputs.py",
    "i4_output.py",
    "i4_preflight.py",
    "i4_reconcile.py",
    "i4_runner.py",
)

RUNNER_NAME = "i4-runner"
RUNNER_VERSION = "i4-runner-1.0.0"
CONTRACT_VERSION = "I4-runner/1.0"

#: The runner performs no network access (D07 §13-D boundary). Import roots that would
#: enable it are forbidden and are checked at preflight.
FORBIDDEN_IMPORT_ROOTS = (
    "socket",
    "ssl",
    "urllib",
    "http",
    "requests",
    "ftplib",
    "smtplib",
    "telnetlib",
    "asyncio",
)


class RunnerIdentityError(RuntimeError):
    """A declared runner module is missing or unreadable (fail-closed, never guessed)."""


def sha1_git_blob(data: bytes) -> str:
    """git blob object id of raw bytes — what ``git hash-object`` reports for those bytes."""
    header = b"blob %d\x00" % len(data)
    return hashlib.sha1(header + data).hexdigest()


def lf_normalize(data: bytes) -> bytes:
    """CRLF -> LF. The CRLF-invariant content-identity form (D05 §9.3)."""
    return data.replace(b"\r\n", b"\n")


def _read(path: str) -> bytes:
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError as exc:  # fail closed: an unreadable declared module is not "unknown"
        raise RunnerIdentityError("cannot read declared module %s: %s" % (path, exc))


def module_file(directory: str, name: str) -> str:
    """Module path for a declared module name (``pipeline`` and ``i4_inputs.py`` both work)."""
    file_name = name if name.endswith(".py") else name + ".py"
    return os.path.join(directory, file_name)


def module_facts(module_names, directory: str) -> tuple:
    """Deterministic per-module facts (size, raw/LF hashes, git blob id), sorted by name."""
    facts = []
    for name in sorted(module_names):
        path = module_file(directory, name)
        if not os.path.isfile(path):
            raise RunnerIdentityError("declared module missing: %s" % name)
        body = _read(path)
        facts.append(
            {
                "module": name,
                "size_bytes": len(body),
                "raw_sha256": hashlib.sha256(body).hexdigest(),
                "lf_sha256": hashlib.sha256(lf_normalize(body)).hexdigest(),
                "git_blob_sha1": sha1_git_blob(body),
            }
        )
    return tuple(facts)


def fingerprint(module_names, directory: str) -> str:
    """sha256 over the declared module set (engine construction, D05 §9 tool identity)."""
    digest = hashlib.sha256()
    for name in sorted(module_names):
        body = _read(module_file(directory, name))
        digest.update(name.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(str(len(body)).encode("ascii"))
        digest.update(b"\x00")
        digest.update(body)
        digest.update(b"\x00")
    return digest.hexdigest()


def runner_module_facts(directory: str = None) -> tuple:
    return module_facts(RUNNER_MODULES, directory or MODULE_DIR)


def runner_fingerprint(directory: str = None) -> str:
    """Deterministic runner identity. Never cached, so a changed module is always detected."""
    return fingerprint(RUNNER_MODULES, directory or MODULE_DIR)


def engine_module_facts() -> tuple:
    """Facts for the declared engine module set (read-only evidence, engine is frozen)."""
    engine_dir = os.path.dirname(os.path.abspath(contract.__file__))
    return module_facts(contract.ENGINE_MODULES, engine_dir)


def engine_fingerprint() -> str:
    """The engine's own governed fingerprint (``nse_engine.provenance.tool_fingerprint``)."""
    from nse_engine.provenance import tool_fingerprint

    return tool_fingerprint()


def forbidden_import_hits(directory: str = None) -> tuple:
    """Return ``((module, line_number, root), ...)`` for forbidden import statements.

    Only import statements are inspected (never comments or docstrings), so prose that
    merely mentions a network term is not flagged.
    """
    hits = []
    for name in sorted(RUNNER_MODULES):
        path = module_file(directory or MODULE_DIR, name)
        text = _read(path).decode("utf-8", "replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            roots = []
            if stripped.startswith("import "):
                roots = [
                    part.strip().split(" ")[0].split(".")[0]
                    for part in stripped[len("import ") :].split(",")
                    if part.strip()
                ]
            elif stripped.startswith("from "):
                parts = stripped.split()
                if len(parts) >= 2:
                    roots = [parts[1].split(".")[0]]
            for root in roots:
                if root in FORBIDDEN_IMPORT_ROOTS:
                    hits.append((name, line_number, root))
    return tuple(hits)


def runner_identity_block() -> dict:
    """Run-level runner identity block (evidence only; never part of canonical output)."""
    return {
        "contract_version": CONTRACT_VERSION,
        "runner_name": RUNNER_NAME,
        "runner_version": RUNNER_VERSION,
        "runner_sha256": runner_fingerprint(),
        "runner_modules": list(runner_module_facts()),
        "module_dir": "tools/i4_runner",  # repo-relative label; no absolute paths retained
    }


def engine_identity_block() -> dict:
    """Run-level engine identity block (the engine's own governed values, re-read)."""
    return {
        "spec_version": contract.SPEC_VERSION,
        "tool_name": contract.TOOL_NAME,
        "tool_version": contract.TOOL_VERSION,
        "tool_sha256": engine_fingerprint(),
        "engine_modules": list(engine_module_facts()),
        "engine_module_count": len(contract.ENGINE_MODULES),
    }


def corpus_identity_digest(archive_identity_pairs) -> str:
    """sha256 over the sorted ``(root, relative_path, archive_sha256)`` corpus identity.

    Content-derived: identical corpus content at any path yields the same digest.
    """
    digest = hashlib.sha256()
    for root, relative_path, sha256 in sorted(archive_identity_pairs):
        digest.update(("%s\x00%s\x00%s\x00" % (root, relative_path, sha256)).encode("utf-8"))
    return digest.hexdigest()


def composite_run_identity(
    engine_identity: dict,
    runner_identity: dict,
    governed_input_facts,
    corpus_digest: str,
    run_id: str,
    partition_definition: dict,
) -> str:
    """Composite identity binding every declared component of a run.

    Changing any component (engine bytes, runner bytes, a governed input file, one corpus
    archive, the partition definition or the run id) changes this digest, so a replay is only
    comparable against a run with an identical composite identity.
    """
    digest = hashlib.sha256()
    digest.update(b"i4-runner-composite\x00")
    for label, value in (
        ("engine", engine_identity.get("tool_sha256")),
        ("runner", runner_identity.get("runner_sha256")),
        ("run_id", run_id),
        ("corpus", corpus_digest),
        ("partitions", repr(sorted(partition_definition.items()))),
    ):
        digest.update(("%s\x00%s\x00" % (label, value)).encode("utf-8"))
    for fact in sorted(governed_input_facts, key=lambda item: item["role"]):
        digest.update(
            (
                "input\x00%s\x00%s\x00%s\x00"
                % (fact["role"], fact["path_label"], fact["lf_sha256"] or "absent")
            ).encode("utf-8")
        )
    return digest.hexdigest()
