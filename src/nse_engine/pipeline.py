"""Reference pipeline for W1: member bytes -> canonical rows -> deterministic evidence.

The governed configuration (:class:`EngineConfig`) is an explicit input: identical input
plus identical configuration yields identical canonical output and evidence (D05 §9.4;
W1 prompt §2 J).

This module performs no persistence, no ingestion, no clock access, no randomness and no
environment inspection. It returns in-memory structures that callers may serialize with
:mod:`nse_engine.serialize`.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Optional, Tuple

from . import contract
from .overlays import OverlayLinkResult, OverlayObservation, link_overlay_observations
from .parsing import MemberParse, QuarantineRecord, SourceDescriptor, parse_member_bytes
from .rows import RowBuildResult, SecurityRow, build_rows


@dataclass(frozen=True)
class EngineConfig:
    """Governed configuration. Defaults transcribe D05; nothing here is a new decision.

    ``overlay_series`` is the D05 §3.5.2 *observed* set. It is configuration (not parser
    logic) precisely because D05 §3.5.2 states it is a data observation and NOT an
    eligibility or microstructure inclusion contract; changing it changes only which rows
    receive an observation, never what a row means.
    """

    overlay_series: Tuple[str, ...] = contract.OVERLAY_SERIES_OBSERVED
    emit_overlay_observations: bool = True
    units_provenance_note: str = contract.UNITS_PROVENANCE_NOTE
    spec_version: str = contract.SPEC_VERSION

    def to_dict(self) -> dict:
        return {
            "emit_overlay_observations": self.emit_overlay_observations,
            "overlay_series": list(self.overlay_series),
            "spec_version": self.spec_version,
            "units_provenance_note": self.units_provenance_note,
        }

    def fingerprint(self) -> str:
        payload = json.dumps(
            self.to_dict(), sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


DEFAULT_CONFIG = EngineConfig()


@dataclass(frozen=True)
class CanonicalBuild:
    source: SourceDescriptor
    config: EngineConfig
    parse: MemberParse
    row_build: RowBuildResult
    overlay_link: OverlayLinkResult

    @property
    def rows(self) -> Tuple[SecurityRow, ...]:
        return self.overlay_link.rows

    @property
    def observations(self) -> Tuple[OverlayObservation, ...]:
        return self.overlay_link.observations

    @property
    def quarantined(self) -> Tuple[QuarantineRecord, ...]:
        records = self.parse.quarantined + self.row_build.quarantined
        return tuple(sorted(records, key=lambda record: record.line_number))

    def quarantine_by_reason(self) -> dict:
        counts = {}
        for record in self.quarantined:
            counts[record.reason_code] = counts.get(record.reason_code, 0) + 1
        return {code: counts[code] for code in sorted(counts)}

    def totals(self) -> dict:
        return {
            "data_lines": self.parse.report.data_lines,
            "observations": len(self.observations),
            "quarantined": len(self.quarantined),
            "rows": len(self.rows),
        }


def build_canonical(
    data: bytes,
    source: SourceDescriptor,
    config: Optional[EngineConfig] = None,
) -> CanonicalBuild:
    """Parse one member and build its canonical rows + overlay observations."""
    effective_config = DEFAULT_CONFIG if config is None else config
    parse = parse_member_bytes(data, source)
    row_build = build_rows(parse)
    if effective_config.emit_overlay_observations:
        overlay_link = link_overlay_observations(row_build.rows, effective_config.overlay_series)
    else:
        overlay_link = OverlayLinkResult(rows=row_build.rows, observations=())
    return CanonicalBuild(
        source=source,
        config=effective_config,
        parse=parse,
        row_build=row_build,
        overlay_link=overlay_link,
    )
