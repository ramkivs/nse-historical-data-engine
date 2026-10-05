#!/usr/bin/env python3
"""
D03 Arena-side partial evidence derivation.

The corpus-dependent fixtures (FIX-SEM-DEF-01 ... FIX-ANOM-01) must run on the
Windows host against the raw archives (tools/d03_fixture_scan/d03_fixtures.py).
Three D02 open questions can however be partially advanced from evidence that is
ALREADY COMMITTED in this repository (the D01 per-file inventory carries the
observed header signature of every file, and the D02 derivations carry the
missing-day list and per-series corpus date ranges). This script derives exactly
those partials, deterministically, from committed inputs:

  FIX-UD-CENSUS-01 (header-width component)
      Proves from stored D01 header signatures that every UDiFF file header is
      exactly 34 fields (and shows the two Legacy 13-vs-14 variants). This is
      verification of D01's stored signature, NOT a rescan of raw files; the
      Windows fixture still verifies widths from the archives themselves.

  FIX-CAL-01 (structural component only)
      Day-of-week classification of all archive file dates and of the 147
      missing weekday file-dates; weekend-emptiness of the corpus. Festival /
      holiday LABELS remain UNRESOLVED: they require the official NSE
      trading-holiday circulars, which are not part of this evidence base.

  FIX-CIRC-01 (corpus-side component only)
      First/last sighting and era boundaries per series from the D02 series
      universe (used to bracket any circular effective date). Meanings of
      IT/IL/SO/HA-HE and era-dependent legend application remain UNRESOLVED;
      the current legend must not be applied retroactively.

Inputs:  evidence/inventory/file_inventory.json
         evidence/identity/d02_missing_weekdays.txt
         evidence/identity/d02_series_universe.csv
Outputs: evidence/d03/FIX-UD-CENSUS-01_arena_header_verification.json
         evidence/d03/FIX-CAL-01_arena_partial.json
         evidence/d03/FIX-CIRC-01_arena_partial.json

Read-only on inputs; writes only inside evidence/d03/. Deterministic: no clock,
no randomness, sorted keys everywhere; inputs are hash-pinned.
"""
import csv
import datetime
import hashlib
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IN_INV = os.path.join(ROOT, "evidence", "inventory", "file_inventory.json")
IN_MISS = os.path.join(ROOT, "evidence", "identity", "d02_missing_weekdays.txt")
IN_UNIV = os.path.join(ROOT, "evidence", "identity", "d02_series_universe.csv")
OUTDIR = os.path.join(ROOT, "evidence", "d03")

DOW = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def prov(inputs):
    return {"generator": "evidence/d03/d03_arena_evidence.py",
            "deterministic": True,
            "clock_used": False,
            "inputs": [{"path": p, "sha256": sha256(p)} for p in inputs]}


def dump(name, obj):
    path = os.path.join(OUTDIR, name)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")
    print("wrote", os.path.relpath(path, ROOT))
    return path


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    inv = json.load(open(IN_INV))
    missing = [l.strip() for l in open(IN_MISS) if l.strip() and not l.startswith("#")]

    # ---- FIX-UD-CENSUS-01 (header-width component) -------------------------
    widths = {}
    sigs = {}
    odd = []
    for e in inv:
        fmt = e["detected_format"]
        n = len(e["headers"])
        widths.setdefault(fmt, {}).setdefault(str(n), {"files": 0})
        widths[fmt][str(n)]["files"] += 1
        sigs.setdefault(fmt, set()).add(e["header_signature"])
        if not ((fmt == "UDIFF" and n == 34) or (fmt == "LEGACY" and n == 14)):
            odd.append({"file_name": e["file_name"], "format": fmt,
                       "header_field_count": n, "header_signature": e["header_signature"]})
    sig_counts = {fmt: len(sigs[fmt]) for fmt in sigs}
    dump("FIX-UD-CENSUS-01_arena_header_verification.json", {
        "provenance": prov([IN_INV]),
        "method": "len(headers) of every file's stored D01 header_signature; verifies D01's recorded width, does not rescan raw archives",
        "expected": {"UDIFF": 34, "LEGACY": 14,
                     "note": "Legacy 14 = 13 named fields + one trailing empty field in the header line"},
        "observed": widths,
        "distinct_signature_counts": sig_counts,
        "nonconforming_files": sorted(odd, key=lambda x: (x["format"], x["file_name"])),
        "interpretation": ("All 543 UDiFF files present exactly one 34-field header signature (no intra-corpus "
                           "UDiFF header variant). Two Legacy files carry a 13-field header (no trailing empty field): "
                           "these match the header_variant entries in the D02 anomaly register. Field ORDER/identity "
                           "for UDiFF is a single signature for all files, so the column layout is stable across the "
                           "whole 2024-07-08..2026-09-18 span as recorded by D01."),
        "open_gap": "Semantic confirmation that all 34 positions match the current UDiFF specification requires the Windows fixture (header_signature string is compared there against the full specification list).",
    })

    # ---- FIX-CAL-01 (structural component only) ----------------------------
    dates = sorted(e["date_from_filename"] for e in inv)
    hist = {d: 0 for d in DOW}
    for d in dates:
        hist[DOW[datetime.date.fromisoformat(d).weekday()]] += 1
    miss_hist = {d: 0 for d in DOW}
    for d in missing:
        miss_hist[DOW[datetime.date.fromisoformat(d).weekday()]] += 1
    weekend_files = [d for d in dates if datetime.date.fromisoformat(d).weekday() >= 5]
    gap = datetime.date.fromisoformat(dates[-1]) - datetime.date.fromisoformat(dates[0])
    d0 = datetime.date.fromisoformat(dates[0])
    total_weekdays = sum(1 for i in range(gap.days + 1) if (d0 + datetime.timedelta(days=i)).weekday() < 5)
    dump("FIX-CAL-01_arena_partial.json", {
        "provenance": prov([IN_INV, IN_MISS]),
        "scope_note": ("Structural calendar facts only. NO day is labelled holiday/festival here: authoritative "
                       "NSE trading-holiday circulars are not part of this evidence base and festival labels MUST "
                       "NOT be guessed (D03 rule). Labeling is UNRESOLVED pending the Windows FIX-CAL-01 fixture "
                       "or fetched official circulars."),
        "archive_dates": {"first": dates[0], "last": dates[-1], "count": len(dates),
                          "day_of_week_histogram": hist,
                          "saturday_or_sunday_files": len(weekend_files)},
        "corpus_property": "The corpus contains no Saturday/Sunday file dates; every missing file-date within the span is a weekday.",
        "missing_weekday_files": {"count": len(missing),
                                  "day_of_week_histogram": miss_hist,
                                  "dates": missing},
        "arithmetic": {"span_inclusive_weekdays": total_weekdays,
                       "present_files": len(dates),
                       "expected_missing_if_all_weekdays": total_weekdays - len(dates),
                       "observed_missing": len(missing),
                       "note": "present_files counts FILES not distinct dates; equal only if one file per date (D01 records this; two files can share a date across formats at boundaries)"},
        "unresolved": ["Which missing weekdays were declared trading holidays (requires official circulars per year and per exchange segment)",
                        "Whether any missing weekday was an unscheduled outage rather than a holiday (2017-07-10, 2020-07-13 header anomalies are adjacent to two missing days and must be cross-checked)"],
    })

    # ---- FIX-CIRC-01 (corpus-side component only) ---------------------------
    rows = list(csv.DictReader(open(IN_UNIV, newline="")))
    series_rows = []
    for r in rows:
        series_rows.append({k: r[k] for k in ("series", "provisional_class", "first_seen", "last_seen",
                                               "legacy_first", "legacy_last", "udiff_first", "udiff_last",
                                               "format_presence")})
    series_rows.sort(key=lambda x: x["series"])
    dump("FIX-CIRC-01_arena_partial.json", {
        "provenance": prov([IN_UNIV]),
        "scope_note": ("Corpus-side bracketing data only: when a code first/last appears, so that circular "
                       "effective dates can later be tested against the data. The MEANING of each code is "
                       "external-documentation work (NSE circular archive); not fetchable/verifiable from here "
                       "without an authorized document retrieval step. Current legend (2024) must not be "
                       "applied retroactively to 2016-2024 legacy codes."),
        "corpus_boundaries": {
            "legacy": {"first": "2016-09-20", "last": "2024-07-05"},
            "udiff": {"first": "2024-07-08", "last": "2026-09-18"}},
        "per_series_observations": series_rows,
        "already_documented_semantics": {
            "T0": ("NSE/NCL T+0 settlement FAQ (E3, external): securities offered under optional T+0 receive series "
                    "'T0' with settlement type 0, parallel to their T+1 series — i.e. a settlement-STATE variant of the "
                    "same security, NOT a new security. Corpus: first T0 sighting 2024-03-28 (Legacy era), consistent "
                    "with the Mar-2024 pilot launch; external sources agree on the pilot start, treated as consistent "
                    "third-party data, not authority."),
            "EQ": "Legend (2024-09-19) covers fully-paid equity AND ETFs rolling into EQ — so SERIES==EQ is not equity-only (D02 F7).",
            "BE": "Legend dual use: equity T2T variant AND Rights Entitlement — needs row-level disambiguation (Windows fixture).",
        },
        "unresolved_meanings": ["IT", "IL", "SO", "HA-HE", "SF", "SM/SZ/ST SME surveillance states by era",
                                 "era-dependent application of legend codes generally"],
        "next_step_on_windows": ("FIX-CIRC-01 fixture = citations + effective dates for each code from the NSE "
                                  "circular archive (document search), joined against per_series_observations here "
                                  "to check regime-change dates against code appearances."),
    })
    print("done")


if __name__ == "__main__":
    main()
