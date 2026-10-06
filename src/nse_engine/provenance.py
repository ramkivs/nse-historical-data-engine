"""Provenance and hashing primitives (D05 §2.1, §8, §9).

Every canonical record produced by W1 carries a provenance block that resolves to exactly
one source member: source archive name, archive sha256 (as recorded in the D01 inventory),
member name, format family, parser/normalizer contract version, tool identity, run id where
applicable, evidence references, and the member's raw-bytes and LF-normalized text sha256.

The tool fingerprint is a sha256 over the engine's own module sources, so a canonical
record can be tied to the exact implementation that produced it.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional, Tuple

from . import contract

_CHUNK = 1 << 20


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def lf_normalize(data: bytes) -> bytes:
    """CRLF -> LF, per D05 §9.3 (the LF-normalized form is the content-identity form)."""
    return data.replace(b"\r\n", b"\n")


def dual_hash(data: bytes) -> Tuple[str, str]:
    """Return ``(sha256(raw bytes), sha256(LF-normalized text))`` — D05 §9.2."""
    return sha256_bytes(data), sha256_bytes(lf_normalize(data))


@lru_cache(maxsize=1)
def tool_fingerprint() -> str:
    """sha256 over the engine module set (name + bytes), sorted by module name.

    Deterministic; independent of checkout path; changes whenever any engine module
    changes. Binds canonical output to the implementation that produced it.
    """
    package_dir = os.path.dirname(os.path.abspath(__file__))
    digest = hashlib.sha256()
    for module in sorted(contract.ENGINE_MODULES):
        path = os.path.join(package_dir, module + ".py")
        with open(path, "rb") as handle:
            body = handle.read()
        digest.update(module.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(str(len(body)).encode("ascii"))
        digest.update(b"\x00")
        digest.update(body)
        digest.update(b"\x00")
    return digest.hexdigest()


@dataclass(frozen=True)
class Provenance:
    """D05 §8 provenance record (per canonical record)."""

    source_archive: str
    member_name: str
    format_family: str
    member_sha256_raw_bytes: str
    member_sha256_lf_text: str
    archive_sha256: Optional[str] = None
    archive_sha256_basis: str = "not-supplied"
    run_id: Optional[str] = None
    evidence_refs: Tuple[str, ...] = ()
    spec_version: str = contract.SPEC_VERSION
    tool_name: str = contract.TOOL_NAME
    tool_version: str = contract.TOOL_VERSION
    tool_sha256: str = field(default_factory=tool_fingerprint)

    def to_dict(self) -> dict:
        return {
            "archive_sha256": self.archive_sha256,
            "archive_sha256_basis": self.archive_sha256_basis,
            "evidence_refs": list(self.evidence_refs),
            "format_family": self.format_family,
            "member_name": self.member_name,
            "member_sha256_lf_text": self.member_sha256_lf_text,
            "member_sha256_raw_bytes": self.member_sha256_raw_bytes,
            "run_id": self.run_id,
            "source_archive": self.source_archive,
            "spec_version": self.spec_version,
            "tool_name": self.tool_name,
            "tool_sha256": self.tool_sha256,
            "tool_version": self.tool_version,
        }
