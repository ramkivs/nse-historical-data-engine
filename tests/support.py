"""Shared helpers for the W1 test suite.

The suite runs on the repository's published fixture evidence (``evidence/d03/windows_run/``)
plus synthetic corpus-shaped inputs. Fixture *tools* are evidence-only and are never
imported (D07 §13-E); the published artifact files are read as data.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from nse_engine import SourceDescriptor, build_canonical  # noqa: E402
from nse_engine import contract  # noqa: E402

FIXTURE_DIR = os.path.join(REPO_ROOT, "evidence", "d03", "windows_run")
SAMPLE_PREFIX = "FIX-UD-ROW-SAMPLE-01__sample_"

#: The eight published row-sample fixtures (frozen, MANIFEST.sha256-anchored evidence).
PUBLISHED_SAMPLES: Tuple[str, ...] = (
    "FIX-UD-ROW-SAMPLE-01__sample_legacy_2016-09-20.csv",
    "FIX-UD-ROW-SAMPLE-01__sample_legacy_2022-10-03.csv",
    "FIX-UD-ROW-SAMPLE-01__sample_legacy_2024-03-28.csv",
    "FIX-UD-ROW-SAMPLE-01__sample_legacy_2024-07-05.csv",
    "FIX-UD-ROW-SAMPLE-01__sample_udiff_2024-07-08.csv",
    "FIX-UD-ROW-SAMPLE-01__sample_udiff_2025-07-14.csv",
    "FIX-UD-ROW-SAMPLE-01__sample_udiff_2025-10-30.csv",
    "FIX-UD-ROW-SAMPLE-01__sample_udiff_2026-08-25.csv",
)

PUBLISHED_EVIDENCE_FILES = {
    "coverage": "FIX-UD-ROW-SAMPLE-01__selection_and_coverage.json",
    "overlay_rows": "FIX-OVERLAY-SEM-01__per_overlay_row.csv",
    "udiff_groups": "FIX-UD-CENSUS-01__groups.csv",
    "legacy_per_file": "FIX-LEG-CENSUS-01__per_file.csv",
    "legacy_census_summary": "FIX-LEG-CENSUS-01__summary.json",
    "legacy_unusual": "FIX-LEG-CENSUS-01__unusual_files_top100.csv",
    "anomaly": "FIX-ANOM-01__report.json",
    "run_info": "RUN_INFO.json",
}


def sample_family(member_name: str) -> str:
    return contract.FAMILY_LEGACY if "_legacy_" in member_name else contract.FAMILY_UDIFF


def sample_date(member_name: str) -> str:
    return os.path.basename(member_name).rsplit("_", 1)[1][: -len(".csv")]


def fixture_bytes(name: str) -> bytes:
    with open(os.path.join(FIXTURE_DIR, name), "rb") as handle:
        return handle.read()


def published_evidence(key: str) -> object:
    path = os.path.join(FIXTURE_DIR, PUBLISHED_EVIDENCE_FILES[key])
    if key.endswith("rows") or key.endswith("unusual") or key in ("udiff_groups", "legacy_per_file"):
        with open(path, newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def expected_sample_rows(member_name: str) -> int:
    coverage = published_evidence("coverage")
    family = "LEGACY" if sample_family(member_name) == contract.FAMILY_LEGACY else "UDIFF"
    key = "%s|%s" % (family, sample_date(member_name))
    return int(coverage["per_date"][key]["sampled_rows"])


def source_for(
    member_name: str,
    expected_source_date: Optional[str] = None,
    run_id: Optional[str] = None,
) -> SourceDescriptor:
    """Published fixtures are extracts, so the governed source archive is the fixture itself."""
    return SourceDescriptor(
        source_archive="<published-fixture:%s>" % member_name,
        member_name=member_name,
        archive_sha256=None,
        archive_sha256_basis="not-supplied (published fixture extract; not a D01 inventory archive)",
        expected_source_date=expected_source_date if expected_source_date is not None else sample_date(member_name),
        evidence_refs=("FIX-UD-ROW-SAMPLE-01",),
        run_id=run_id,
    )


def build_sample(member_name: str, config=None, run_id: Optional[str] = None):
    return build_canonical(fixture_bytes(member_name), source_for(member_name, run_id=run_id), config)


def all_published_builds(config=None, run_id: Optional[str] = None):
    return [(name, build_sample(name, config=config, run_id=run_id)) for name in PUBLISHED_SAMPLES]


# ------------------------------------------------------------------ synthetic corpus builders
#: Corpus-shaped template rows (values taken from the published fixtures) used as defaults
#: so synthetic cases stay realistic; each field can be overridden per test.
LEGACY_TEMPLATE = {
    "SYMBOL": "20MICRONS",
    "SERIES": "EQ",
    "OPEN": "37.4",
    "HIGH": "39",
    "LOW": "33.9",
    "CLOSE": "37",
    "LAST": "36.8",
    "PREVCLOSE": "36.85",
    "TOTTRDQTY": "191700",
    "TOTTRDVAL": "6928949.55",
    "TIMESTAMP": "20-SEP-2016",
    "TOTALTRADES": "820",
    "ISIN": "INE144J01027",
}

UDIFF_TEMPLATE = {
    "TradDt": "2024-07-08",
    "BizDt": "2024-07-08",
    "Sgmt": "CM",
    "Src": "NSE",
    "FinInstrmTp": "STK",
    "FinInstrmId": "20092",
    "ISIN": "INE488B01017",
    "TckrSymb": "TASTYBITE",
    "SctySrs": "EQ",
    "XpryDt": "",
    "FininstrmActlXpryDt": "",
    "StrkPric": "",
    "OptnTp": "",
    "FinInstrmNm": "TASTY BITE EATABLES LTD",
    "OpnPric": "10400.10",
    "HghPric": "10534.50",
    "LwPric": "10191.00",
    "ClsPric": "10273.20",
    "LastPric": "10299.95",
    "PrvsClsgPric": "10374.25",
    "UndrlygPric": "",
    "SttlmPric": "10272.10",
    "OpnIntrst": "",
    "ChngInOpnIntrst": "",
    "TtlTradgVol": "2793",
    "TtlTrfVal": "28877900.75",
    "TtlNbOfTxsExctd": "1046",
    "SsnId": "F1",
    "NewBrdLotQty": "1",
    "Rmks": "",
    "Rsvd1": "",
    "Rsvd2": "",
    "Rsvd3": "",
    "Rsvd4": "",
}


def legacy_row(**overrides) -> Tuple[str, ...]:
    values = dict(LEGACY_TEMPLATE)
    values.update(overrides)
    return tuple(values[name] for name in contract.LEGACY_HEADER_FIELDS)


def udiff_row(**overrides) -> Tuple[str, ...]:
    values = dict(UDIFF_TEMPLATE)
    values.update(overrides)
    return tuple(values[name] for name in contract.UDIFF_HEADER_FIELDS)


def _encode(fields: Sequence[str], line_ending: str) -> str:
    return ",".join(fields) + line_ending


def legacy_member(
    rows: Sequence[Sequence[str]],
    trailing_empty_header: bool = True,
    line_ending: str = "\n",
    trailing_newline: bool = True,
    header: Optional[Sequence[str]] = None,
) -> bytes:
    """Build an in-memory legacy member.

    ``trailing_empty_header`` selects the member's physical variant: the 14-physical-field
    serialization (default) or the 13-physical-field serialization.
    """
    if header is None:
        header_fields: List[str] = list(contract.LEGACY_HEADER_FIELDS)
        if trailing_empty_header:
            header_fields.append("")
    else:
        header_fields = list(header)
    lines = [_encode(header_fields, line_ending).rstrip("\r\n")]
    for row in rows:
        fields = list(row)
        if trailing_empty_header and len(fields) == contract.LEGACY_LOGICAL_WIDTH:
            fields = fields + [""]
        lines.append(_encode(fields, line_ending).rstrip("\r\n"))
    text = line_ending.join(lines)
    if trailing_newline:
        text += line_ending
    return text.encode("utf-8")


def udiff_member(
    rows: Sequence[Sequence[str]],
    line_ending: str = "\n",
    trailing_newline: bool = True,
    header: Optional[Sequence[str]] = None,
) -> bytes:
    header_fields = list(header) if header is not None else list(contract.UDIFF_HEADER_FIELDS)
    lines = [_encode(header_fields, line_ending).rstrip("\r\n")]
    for row in rows:
        lines.append(_encode(list(row), line_ending).rstrip("\r\n"))
    text = line_ending.join(lines)
    if trailing_newline:
        text += line_ending
    return text.encode("utf-8")


def synthetic_source(
    member_name: str = "synthetic.csv",
    expected_source_date: Optional[str] = None,
    run_id: Optional[str] = None,
) -> SourceDescriptor:
    return SourceDescriptor(
        source_archive="<synthetic>",
        member_name=member_name,
        expected_source_date=expected_source_date,
        evidence_refs=("synthetic",),
        run_id=run_id,
    )


def parse_synthetic(
    data: bytes,
    expected_source_date: Optional[str] = None,
    config=None,
    member_name: str = "synthetic.csv",
    run_id: Optional[str] = None,
):
    return build_canonical(
        data, synthetic_source(member_name, expected_source_date, run_id=run_id), config
    )


def rows_by_line(build) -> Dict[int, object]:
    return {row.line_number: row for row in build.rows}
