"""Deterministic serialization of canonical output (D05 §9).

Conventions (D05 §9.1–§9.4):

* stored text artifacts use LF endings and end with a final newline;
* two artifacts are identical iff their LF-normalized forms and line counts match;
* rerun determinism means byte-identical output except fields explicitly declared
  run-metadata — here exactly ``provenance.run_id`` (``contract.RUN_METADATA_FIELDS``);
* numeric fields are emitted as *published text* (never as floats), so no platform
  float formatting can introduce nondeterminism or silent reformatting.

JSON is emitted with sorted keys, compact separators, ``ensure_ascii=False`` and
``allow_nan=False`` (NaN/Infinity would be a silent corruption, so they raise).
"""

from __future__ import annotations

import hashlib
import json
from typing import Iterable

from . import contract
from .pipeline import CanonicalBuild
from .rows import SecurityRow


def canonical_json(obj) -> str:
    return json.dumps(
        obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )


def canonical_row_dict(row: SecurityRow, include_run_metadata: bool = True) -> dict:
    data = row.to_dict()
    if not include_run_metadata:
        data["provenance"]["run_id"] = contract.RUN_METADATA_PLACEHOLDER
    return data


def rows_jsonl(rows: Iterable[SecurityRow], include_run_metadata: bool = True) -> str:
    """One canonical row per line, LF endings, final newline (D05 §9.1)."""
    lines = [
        canonical_json(canonical_row_dict(row, include_run_metadata)) for row in rows
    ]
    return "".join(line + "\n" for line in lines)


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_evidence(build: CanonicalBuild) -> dict:
    """Deterministic evidence document for one canonical build.

    Contains no clock value, no hostname, no path and no randomness: identical input plus
    identical governed configuration yields identical evidence, including under a different
    declared run id. ``rows_jsonl_sha256`` is therefore the hash of the run-metadata-excluded
    canonical view; the hash of the run-metadata-carrying artifact is recorded by callers
    that emit that artifact (see ``tests/determinism_check.py`` MANIFEST.sha256), so this
    evidence document itself never varies with declared run metadata (D05 §9.4).
    """
    determinism_view = rows_jsonl(build.rows, include_run_metadata=False)
    observations = [observation.to_dict() for observation in build.observations]
    return {
        "archive_sha256": build.source.archive_sha256,
        "archive_sha256_basis": build.source.archive_sha256_basis,
        "config_fingerprint": build.config.fingerprint(),
        "format_family": build.parse.header.family,
        "header_line": build.parse.header_line,
        "governed_config": build.config.to_dict(),
        "member_name": build.source.member_name,
        "observations": observations,
        "parse_report": build.parse.report.to_dict(),
        "quarantine": [record.to_dict() for record in build.quarantined],
        "quarantine_by_reason": build.quarantine_by_reason(),
        "row_count": len(build.rows),
        "rows_jsonl_sha256": text_sha256(determinism_view),
        "run_metadata_fields": list(contract.RUN_METADATA_FIELDS),
        "source_archive": build.source.source_archive,
        "spec_version": contract.SPEC_VERSION,
        "tool_name": contract.TOOL_NAME,
        "tool_sha256": build.rows[0].provenance.tool_sha256 if build.rows else None,
        "tool_version": contract.TOOL_VERSION,
    }


def evidence_json(build: CanonicalBuild) -> str:
    return canonical_json(build_evidence(build)) + "\n"

