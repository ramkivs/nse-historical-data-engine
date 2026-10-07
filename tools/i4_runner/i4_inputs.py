"""I4 runner inputs: bounded IO, governed fact binding, ArchiveError-free member extraction.

This module is the runner's IO layer. It performs only what R1-R3 require:

* discover the corpus archive set under the two declared roots;
* read the governed D01 inventory (2,462 records) and the governed evidence inputs;
* verify archive bytes against the inventory (Tier A);
* read each archive's single ``.csv`` member **verbatim** (never derived from the archive
  file name — RD-5);
* build ``SourceDescriptor`` values from governed inventory facts, with
  ``archive_sha256_basis="D01-inventory"`` (R3).

It contains **no** parsing, header, field-mapping, numeric, flag, calendar, identity,
continuity, overlay or metric semantics: every such transformation belongs to
``nse_engine``, which this module never reimplements.

No network access, no clock, no randomness, no corpus mutation.

Shared failure types live here because every runner module already depends on this layer:

``I4RunnerError``      — base (includes usage errors)
``GoverningFailure``   — fail-closed condition: the run must abort and retain evidence
``PreflightFailure``   — a preflight (Tier A / Tier G gating) condition failed
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import zipfile
from dataclasses import dataclass

if __package__:
    from . import i4_identity as identity
else:  # direct script execution (python tools/i4_runner/i4_runner.py)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import i4_identity as identity  # type: ignore

REPO_ROOT = identity.REPO_ROOT
SRC_DIR = identity.SRC_DIR

from nse_engine import contract  # noqa: E402
from nse_engine.evidence_inputs import (  # noqa: E402
    CalendarLabelRecord,
    CircularHolidayRecord,
    FileMetricRecord,
    InventoryFileRecord,
)
from nse_engine.parsing import SourceDescriptor  # noqa: E402

#: D01 inventory record contract (D01 baseline). Every field is required; a record missing
#: any of them fails closed (the runner never guesses an inventory fact).
REQUIRED_INVENTORY_KEYS = (
    "root",
    "relative_path",
    "file_name",
    "size_bytes",
    "date_from_filename",
    "sha256",
    "detected_format",
    "row_count",
    "bad_rows",
    "headers",
    "header_signature",
    "date_values",
    "series_counts",
    "symbol_count",
    "isin_count",
)

#: D01 root label -> governed canonical family (the engine's own mapping is authoritative).
ROOT_LABELS = ("LEGACY", "UDIFF")
ISO_DATE_RE = re.compile(contract.ISO_DATE_PATTERN)
ARCHIVE_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

INVENTORY_SUMMARY_NAME = "inventory_summary.json"
DEFAULT_INVENTORY = "evidence/inventory/file_inventory.json"
DEFAULT_LABELS = "evidence/d04/DEC2_CAL_LABELS.json"
DEFAULT_D01_METRICS = "evidence/d03/windows_run/FIX-SEM-DEF-01__metrics.csv"
DEFAULT_D01_VERDICT = "evidence/d03/windows_run/FIX-SEM-DEF-01__d01_definition_verdict.json"
DEFAULT_SERIES_UNIVERSE = "evidence/identity/d02_series_universe.csv"
DEFAULT_SERIES_ROLLUP = "evidence/identity/d02_series_class_rollup.csv"


class I4RunnerError(Exception):
    """Base runner error (includes usage errors)."""


class GoverningFailure(I4RunnerError):
    """A fail-closed condition: abort the run and retain failure evidence."""


class PreflightFailure(GoverningFailure):
    """A preflight condition failed (Tier A / gating Tier G)."""


# ------------------------------------------------------------------ facts / hashing


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_facts(path: str) -> dict:
    """Deterministic facts for one repository/governed input file.

    Three byte domains are recorded, each with its own basis: raw-bytes, LF-text and the
    git blob id. The declared comparison basis for governed text inputs is **lf-text**,
    which is invariant under the Windows CRLF working-tree conversion (D03 §15 lesson).
    """
    with open(path, "rb") as handle:
        body = handle.read()
    return {
        "size_bytes": len(body),
        "raw_sha256": sha256_bytes(body),
        "lf_sha256": sha256_bytes(identity.lf_normalize(body)),
        "git_blob_sha1": identity.sha1_git_blob(body),
    }


def governed_input_fact(role: str, path_label: str, path: str, present: bool) -> dict:
    fact = {
        "role": role,
        "path_label": path_label,
        "present": bool(present),
        "comparison_basis": "lf-text",
        "size_bytes": None,
        "raw_sha256": None,
        "lf_sha256": None,
        "git_blob_sha1": None,
    }
    if present:
        fact.update(file_facts(path))
    return fact


# ------------------------------------------------------------------ corpus discovery


@dataclass(frozen=True)
class ArchiveRef:
    """One discovered corpus archive (content identity, never path identity)."""

    root: str
    relative_path: str
    file_name: str
    path: str
    size_bytes: int


def discover_archives(root_paths: dict) -> tuple:
    """Discover every archive under each declared root, deterministically sorted.

    ``root_paths`` maps the governed root label (``LEGACY``/``UDIFF``) to a directory.
    Relative paths are root-relative with forward slashes; ordering is by
    ``(root, relative_path)`` — never filesystem enumeration order.
    """
    refs = []
    for root in ROOT_LABELS:
        root_path = root_paths.get(root)
        if not root_path:
            raise PreflightFailure("corpus root not declared for %s" % root)
        if not os.path.isdir(root_path):
            raise PreflightFailure("corpus root is not a directory: %s" % root)
        for dirpath, dirnames, filenames in os.walk(root_path):
            dirnames.sort()
            for name in sorted(filenames):
                full = os.path.join(dirpath, name)
                relative = os.path.relpath(full, root_path).replace(os.sep, "/")
                if not os.path.isfile(full):
                    continue
                refs.append(
                    ArchiveRef(
                        root=root,
                        relative_path=relative,
                        file_name=name,
                        path=full,
                        size_bytes=os.path.getsize(full),
                    )
                )
    refs.sort(key=lambda ref: (ref.root, ref.relative_path))
    return tuple(refs)


def corpus_archive_pairs(refs) -> tuple:
    """``(root, relative_path)`` identity pairs (used for the both-directions set check)."""
    return tuple((ref.root, ref.relative_path) for ref in refs)


# ------------------------------------------------------------------ archive reading


def archive_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1 << 20)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def csv_member_names(archive_path: str) -> tuple:
    """The archive's ``.csv`` member names, in the archive's own stored order.

    The name is read verbatim from the ZIP central directory (RD-5). No archive file name
    is ever parsed, and no member name is ever derived or repaired.
    """
    try:
        with zipfile.ZipFile(archive_path, "r") as handle:
            bad = handle.testzip()
            if bad is not None:
                raise PreflightFailure(
                    "archive member failed CRC: %s :: %s" % (os.path.basename(archive_path), bad)
                )
            names = [info.filename for info in handle.infolist() if not info.is_dir()]
    except PreflightFailure:
        raise
    except (zipfile.BadZipFile, OSError) as exc:
        raise PreflightFailure(
            "malformed archive %s: %s" % (os.path.basename(archive_path), exc)
        )
    return tuple(names)


def read_member_bytes(archive_path: str, member_name: str) -> bytes:
    """Read exactly one member's bytes, verbatim (R2). Never decodes, never rewrites."""
    try:
        with zipfile.ZipFile(archive_path, "r") as handle:
            return handle.read(member_name)
    except (zipfile.BadZipFile, KeyError, OSError) as exc:
        raise GoverningFailure(
            "cannot read member %s from %s: %s"
            % (member_name, os.path.basename(archive_path), exc)
        )


def member_identity(archive_path: str) -> str:
    """Resolve the archive's single governed ``.csv`` member, fail-closed on 0 or >=2."""
    names = csv_member_names(archive_path)
    csv_names = tuple(name for name in names if name.lower().endswith(".csv"))
    if len(csv_names) != 1:
        raise PreflightFailure(
            "archive %s must contain exactly one .csv member (found %d)"
            % (os.path.basename(archive_path), len(csv_names))
        )
    return csv_names[0]


# ------------------------------------------------------------------ inventory


def load_inventory(path: str) -> tuple:
    """Load the governed D01 inventory and validate its record contract (fail-closed)."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            document = json.load(handle)
    except OSError as exc:
        raise PreflightFailure("inventory not readable: %s: %s" % (path, exc))
    except ValueError as exc:
        raise PreflightFailure("inventory is not valid JSON: %s: %s" % (path, exc))
    if not isinstance(document, list) or not document:
        raise PreflightFailure("inventory must be a non-empty JSON list of records")
    for index, record in enumerate(document):
        if not isinstance(record, dict):
            raise PreflightFailure("inventory record %d is not an object" % index)
        missing = [key for key in REQUIRED_INVENTORY_KEYS if key not in record]
        if missing:
            raise PreflightFailure(
                "inventory record %d is missing required key(s): %s"
                % (index, ", ".join(sorted(missing)))
            )
        if record["root"] not in ROOT_LABELS:
            raise PreflightFailure("inventory record %d has unknown root %r" % (index, record["root"]))
        if not ISO_DATE_RE.match(str(record["date_from_filename"])):
            raise PreflightFailure(
                "inventory record %d has non-ISO date_from_filename %r"
                % (index, record["date_from_filename"])
            )
        if not ARCHIVE_SHA256_RE.match(str(record["sha256"])):
            raise PreflightFailure("inventory record %d has malformed sha256" % index)
        for key in ("row_count", "bad_rows", "symbol_count", "isin_count", "size_bytes"):
            if not isinstance(record[key], int):
                raise PreflightFailure(
                    "inventory record %d field %s must be an integer" % (index, key)
                )
    return tuple(document)


def inventory_index(records) -> dict:
    """Inventory keyed by ``(root, relative_path)`` — duplicate keys fail closed."""
    index = {}
    for record in records:
        key = (record["root"], record["relative_path"])
        if key in index:
            raise PreflightFailure(
                "inventory contains a duplicate record for %s :: %s" % key
            )
        index[key] = record
    return index


def to_inventory_records(records) -> tuple:
    """D01 inventory records -> the engine's governed ``InventoryFileRecord`` inputs.

    ``date`` is populated from the D01 field ``date_from_filename`` (the governed file-date
    mapping, D05 §3.4). This mirrors the governed mapping; the runner does not import the
    test support module.
    """
    converted = []
    for record in records:
        converted.append(
            InventoryFileRecord(
                file_name=record["file_name"],
                date=record["date_from_filename"],
                root=record["root"],
                sha256=record["sha256"],
                row_count=int(record["row_count"]),
                series_counts=tuple(sorted(record.get("series_counts", {}).items())),
            )
        )
    return tuple(converted)


def load_inventory_summary(inventory_path: str) -> dict:
    """The optional companion ``inventory_summary.json`` (Tier G document cross-check)."""
    path = os.path.join(os.path.dirname(inventory_path), INVENTORY_SUMMARY_NAME)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, ValueError) as exc:
        raise PreflightFailure("inventory summary not readable: %s: %s" % (path, exc))
    if not isinstance(document, dict):
        raise PreflightFailure("inventory summary must be a JSON object")
    return document


# ------------------------------------------------------------------ governed evidence inputs


def load_labels(path: str) -> tuple:
    """``DEC2_CAL_LABELS.json`` -> (labels, circular holidays, registry ids, document)."""
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    registry_ids = tuple(document.get("provenance", {}).get("circular_registry_ids", ()))
    labels = []
    for entry in document.get("per_missing_day", ()):
        circular = entry.get("circular", "")
        labels.append(
            CalendarLabelRecord(
                missing_date=entry["missing_date"],
                label=entry["label"],
                circular=circular,
                registry_id=circular if str(circular).startswith("NSE/") else "",
            )
        )
    holidays = tuple(
        CircularHolidayRecord(holiday_date=entry["holiday_per_circular"], note=entry.get("note", ""))
        for entry in document.get("files_present_on_circular_holiday", ())
    )
    return tuple(labels), holidays, registry_ids, document


def load_metric_records(path: str) -> tuple:
    """Frozen per-file D01 metric evidence -> ``FileMetricRecord`` inputs (IO mapping only)."""
    import csv

    with open(path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        records = []
        for row in reader:
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


def load_json_document(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, dict):
        raise PreflightFailure("expected a JSON object in %s" % path)
    return document


def load_series_classes(path: str) -> dict:
    """D02 provisional series classification — carried evidence input, never re-derived."""
    import csv

    classes = {}
    with open(path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            series = row.get("series", "")
            if series:
                classes[series] = (row.get("class", ""), row.get("basis", ""))
    return classes


# ------------------------------------------------------------------ identity / partition


def expected_family(root: str) -> str:
    """Governed root label -> canonical family (the engine's own mapping table)."""
    from nse_engine.evidence_inputs import INVENTORY_ROOT_TO_FAMILY

    family = INVENTORY_ROOT_TO_FAMILY.get(root)
    if family is None:
        raise GoverningFailure("no governed family mapping for root %r" % root)
    return family


def build_source(record: dict, member_name: str, run_id: str) -> SourceDescriptor:
    """R3: ``SourceDescriptor`` from governed inventory facts only.

    ``archive_sha256`` is the D01 inventory value and its basis is declared as
    ``D01-inventory``. ``expected_source_date`` is the governed ``date_from_filename``
    (D05 §3.4 / §7.2) — the runner never parses a file name to obtain it.
    """
    return SourceDescriptor(
        source_archive=record["file_name"],
        member_name=member_name,
        archive_sha256=record["sha256"],
        archive_sha256_basis="D01-inventory",
        expected_source_date=record["date_from_filename"],
        evidence_refs=("D01-inventory",),
        run_id=run_id,
    )


def partition_of(record: dict) -> tuple:
    """RD-6 partition key: ``(format_family, calendar year of date_from_filename)``."""
    family = expected_family(record["root"])
    year = str(record["date_from_filename"])[:4]
    return family, year


def partition_id(family: str, year: str) -> str:
    return "%s_%s" % (family, year)


def partition_definition() -> dict:
    """The declared partition contract (recorded in the run evidence)."""
    return {
        "key": "(format_family, calendar year of D01 date_from_filename)",
        "family_source": "governed D01 root -> canonical family mapping",
        "year_source": "first four characters of D01 date_from_filename (ISO yyyy-mm-dd)",
        "within_partition_order": "(business_date, root, file_name) total order",
        "content_derived": True,
        "note": (
            "Partitioning is an execution/output organisation mechanism only (RD-6); it "
            "alters no canonical, identity, continuity, calendar, overlay or metric semantics."
        ),
    }
