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


# ================================================================== W2 / I2 evidence adapters
W2_EVIDENCE = {
    "aggregate": "FIX-OVERLAY-SEM-01__aggregate.json",
    "cal_partial": None,  # evidence/d03/FIX-CAL-01_arena_partial.json
    "dec2_cal": None,     # evidence/d04/DEC2_CAL_LABELS.json
    "dec2_q8": None,      # evidence/d04/DEC2_Q8_OVERLAY_AGG.json
    "inventory": None,    # evidence/inventory/file_inventory.json
    "leg_census_per_file": "FIX-LEG-CENSUS-01__per_file.csv",
    "leg_census_per_year": "FIX-LEG-CENSUS-01__per_year.csv",
    "leg_census_summary": "FIX-LEG-CENSUS-01__summary.json",
    "formulas": "FIX-SEM-DEF-01__formula_definitions.json",
    "metrics_oracle": "FIX-SEM-DEF-01__metrics.csv",
    "overlay_rows": "FIX-OVERLAY-SEM-01__per_overlay_row.csv",
    "sem_def": "FIX-SEM-DEF-01__d01_definition_verdict.json",
    "symbol_hist": "FIX-SYMBOL-HIST-01__summary.json",
    "udiff_groups": "FIX-UD-CENSUS-01__groups.csv",
    "xcont": "FIX-XCONT-01__summary.json",
}
D02_METRICS_PATH = os.path.join(REPO_ROOT, "evidence", "identity", "d02_metrics.json")
SERIES_UNIVERSE_PATH = os.path.join(REPO_ROOT, "evidence", "identity", "d02_series_universe.csv")
SERIES_CLASS_ROLLUP_PATH = os.path.join(REPO_ROOT, "evidence", "identity", "d02_series_class_rollup.csv")
MISSING_WEEKDAYS_PATH = os.path.join(REPO_ROOT, "evidence", "identity", "d02_missing_weekdays.txt")
INVENTORY_PATH = os.path.join(REPO_ROOT, "evidence", "inventory", "file_inventory.json")
DEC2_CAL_PATH = os.path.join(REPO_ROOT, "evidence", "d04", "DEC2_CAL_LABELS.json")
DEC2_Q8_PATH = os.path.join(REPO_ROOT, "evidence", "d04", "DEC2_Q8_OVERLAY_AGG.json")
CAL_PARTIAL_PATH = os.path.join(REPO_ROOT, "evidence", "d03", "FIX-CAL-01_arena_partial.json")


def _read_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _read_csv(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def w2_evidence(key: str) -> object:
    """Read one frozen W2 evidence artifact from the published fixture directory."""
    name = W2_EVIDENCE[key]
    if name is None:
        raise KeyError("evidence %r is not inside the published fixture directory" % key)
    path = os.path.join(FIXTURE_DIR, name)
    if name.endswith(".csv"):
        return _read_csv(path)
    return _read_json(path)


def load_inventory_records():
    """D01 inventory -> governed file records (the calendar/metrics input)."""
    from nse_engine.evidence_inputs import InventoryFileRecord

    records = []
    for entry in _read_json(INVENTORY_PATH):
        records.append(
            InventoryFileRecord(
                file_name=entry["file_name"],
                date=entry["date_from_filename"],
                root=entry["root"],
                sha256=entry["sha256"],
                row_count=int(entry["row_count"]),
                series_counts=tuple(sorted(entry.get("series_counts", {}).items())),
            )
        )
    return tuple(records)


def load_file_metric_records():
    """Frozen per-file D01 metric evidence -> records."""
    from nse_engine.evidence_inputs import FileMetricRecord

    records = []
    for row in _read_csv(os.path.join(FIXTURE_DIR, W2_EVIDENCE["metrics_oracle"])):
        records.append(
            FileMetricRecord(
                format_family=row["format"],
                file_name=row["file"],
                rows=int(row["rows"]),
                blank_symbol_rows=int(row["blank_symbol_rows"]),
                blank_isin_rows=int(row["blank_isin_rows"]),
                nonblank_isin_rows=int(row["nonblank_isin_rows"]),
                distinct_nonblank_isin=int(row["distinct_nonblank_isin"]),
                isins_extra_duplicate_rows=int(row["isins_extra_duplicate_rows"]),
                distinct_nonblank_symbol=int(row["distinct_nonblank_symbol"]),
                distinct_symbol_series_pairs=int(row["distinct_symbol_series_pairs"]),
                symbol_series_duplicate_rows=int(row["symbol_series_duplicate_rows"]),
                d01_isin_count=int(row["d01_isin_count"]),
                d01_symbol_count=int(row["d01_symbol_count"]),
                discriminating_file=row["discriminating_file"] == "True",
                d01_isin_eq_distinct_nonblank=row["d01_isin_eq_distinct_nonblank"] == "True",
                d01_isin_eq_nonblank_rows=row["d01_isin_eq_nonblank_rows"] == "True",
                d01_sym_eq_distinct_nonblank=row["d01_sym_eq_distinct_nonblank"] == "True",
                d01_sym_eq_rows=row["d01_sym_eq_rows"] == "True",
                requested_date=row["requested_date"] or None,
            )
        )
    return tuple(records)


def load_calendar_labels():
    """DEC2_CAL_LABELS.json -> (labels, circular holidays, registry ids)."""
    from nse_engine.evidence_inputs import CalendarLabelRecord, CircularHolidayRecord

    document = _read_json(DEC2_CAL_PATH)
    registry_ids = document.get("provenance", {}).get("circular_registry_ids", ())
    labels = []
    for entry in document["per_missing_day"]:
        circular = entry.get("circular", "")
        registry_id = circular if circular.startswith("NSE/") else ""
        labels.append(
            CalendarLabelRecord(
                missing_date=entry["missing_date"],
                label=entry["label"],
                circular=circular,
                registry_id=registry_id,
            )
        )
    holidays = tuple(
        CircularHolidayRecord(holiday_date=entry["holiday_per_circular"], note=entry.get("note", ""))
        for entry in document.get("files_present_on_circular_holiday", ())
    )
    return tuple(labels), holidays, tuple(registry_ids), document


def load_overlay_fixture_rows():
    from nse_engine.evidence_inputs import OverlayFixtureRow

    rows = []
    for row in _read_csv(os.path.join(FIXTURE_DIR, W2_EVIDENCE["overlay_rows"])):
        rows.append(
            OverlayFixtureRow(
                format_family=row["format"],
                date=row["date"],
                overlay_series=row["overlay_series"],
                overlay_symbol=row["overlay_symbol"],
                overlay_isin=row["overlay_isin"],
                match_type=row["match_type"],
                base_symbol=row["base_symbol"],
                base_series=row["base_series"],
                base_isin=row["base_isin"],
                qty_rel=row["qty_rel"],
            )
        )
    return tuple(rows)


def load_series_classes():
    """D02 provisional classification (evidence input, carried not re-derived)."""
    classes = {}
    for row in _read_csv(SERIES_UNIVERSE_PATH):
        classes[row["series"]] = (row["provisional_class"], row["classification_basis"])
    return classes


def load_series_universe_rows():
    return _read_csv(SERIES_UNIVERSE_PATH)


def load_series_class_rollup():
    return _read_csv(SERIES_CLASS_ROLLUP_PATH)


def load_legacy_census_per_year():
    return _read_csv(os.path.join(FIXTURE_DIR, W2_EVIDENCE["leg_census_per_year"]))


def load_legacy_census_per_file():
    return _read_csv(os.path.join(FIXTURE_DIR, W2_EVIDENCE["leg_census_per_file"]))


def load_missing_weekdays():
    dates = []
    with open(MISSING_WEEKDAYS_PATH, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#"):
                dates.append(line)
    return tuple(dates)


def build_w2_samples(config=None, run_id=None):
    """W1 builds for the 8 published samples -> W2 derivation."""
    from nse_engine.pipeline import build_w2

    builds = tuple(
        build_sample(name, config=config, run_id=run_id) for name in PUBLISHED_SAMPLES
    )
    labels, holidays, _registry, _document = load_calendar_labels()
    return build_w2(builds, load_inventory_records(), labels, holidays)
