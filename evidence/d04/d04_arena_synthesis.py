#!/usr/bin/env python3
"""
D04B Arena-side synthesis for the DEC-1 / DEC-2 investigations.

Deterministic derivations from COMMITTED evidence only (windows_run fixtures + D01 inventory +
D02 derivations) plus a recorded registry of fetched official NSE documentation. No raw corpus
access. No network calls in this script (documentation facts are recorded inputs; their fetch
provenance is declared in the registry).

Outputs (evidence/d04/):
  DEC2_CAL_LABELS.json      missing-weekday labeling reconciliation vs official holiday circulars
                            for the years actually obtained (2024/2025/2026), incl. discrepancies
  DEC2_Q7_UNIT_SCALE.json   rupee-vs-lakhs scaling test on published row samples (both eras)
  DEC2_Q8_OVERLAY_AGG.json  qty_rel distribution computed from published per-overlay evidence
  DEC2_CIRC_MEANINGS.json   documentation-backed series meanings + still-open codes
  DEC1_SECMASTER_FEASIBILITY.json  security-master feasibility & acquisition status

Reproduce: python3 evidence/d04/d04_arena_synthesis.py   (byte-identical on rerun)
"""
import csv
import datetime
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WR = os.path.join(ROOT, "evidence", "d03", "windows_run")
INV = os.path.join(ROOT, "evidence", "inventory", "file_inventory.json")
MISS = os.path.join(ROOT, "evidence", "identity", "d02_missing_weekdays.txt")
OUTDIR = os.path.dirname(os.path.abspath(__file__))


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Registry of fetched OFFICIAL documentation (recorded inputs with provenance).
# Fetch method: Arena-side retrieval of nsearchives.nseindia.com documents on 2026-10-06
# (session log). Where only a table excerpt was captured, that is stated.
CIRCULARS = [
    {"id": "NSE/CMTR/59722", "file": "https://nsearchives.nseindia.com/content/circulars/CMTR59722.pdf",
     "date": "2023-12-12", "title": "Trading holidays for the calendar year 2024 (CM segment)",
     "excerpt_scope": "table items 1-14 weekdays + weekend addenda; full weekday list also includes "
                      "July 17 2024 Moharram and Dec 25 Christmas (confirmed via retrieved content)"},
    {"id": "NSE/CMTR/61518", "file": "https://nsearchives.nseindia.com/content/circulars/CMTR61518.pdf",
     "date": "2024-04-08", "title": "Trading holiday on May 20, 2024 on account of Parliamentary Elections",
     "note": "in-partial-modification to NSE/CMTR/59722"},
    {"id": "NSE/CMTR/65587", "file": "https://nsearchives.nseindia.com/content/circulars/CMTR65587.pdf",
     "date": "2024-12-13", "title": "Trading holidays for the calendar year 2025 (CM segment)",
     "weekday_list": ["2025-02-26", "2025-03-14", "2025-03-31", "2025-04-10", "2025-04-14", "2025-04-18",
                      "2025-05-01", "2025-08-15", "2025-08-27", "2025-10-02", "2025-10-21", "2025-10-22",
                      "2025-11-05", "2025-12-25"]},
    {"id": "NSE/CMTR/71775", "file": "https://nsearchives.nseindia.com/content/circulars/CMTR71775.pdf",
     "date": "2025-12-12", "title": "Trading Holidays for Calendar Year 2026 (CM segment)",
     "note": "retrieved excerpt showed only the Saturday/Sunday-falling addenda"},
    {"id": "NSE/FAOP/71777", "file": "https://nsearchives.nseindia.com/content/circulars/FAOP71777.pdf",
     "date": "2025-12-12", "title": "Trading holidays for the calendar year 2026 (F&O segment)",
     "weekday_list": ["2026-01-26", "2026-03-03", "2026-03-26", "2026-03-31", "2026-04-03", "2026-04-14",
                      "2026-05-01", "2026-05-28", "2026-06-26", "2026-09-14", "2026-10-02", "2026-10-20",
                      "2026-11-10", "2026-11-24", "2026-12-25"]},
    {"id": "NSE/FAOP/70320", "file": "https://nsearchives.nseindia.com/content/circulars/FAOP70320.pdf",
     "date": "2025-09-22", "title": "Muhurat Trading session on account of Diwali (special live session "
             "Tuesday 2025-10-21, normal market 13:45-14:45)",
     "note": "all trades settle; relevant to the 2025-10-21 file existence"},
    {"id": "NSE/CMTR/7864", "file": "https://archives.nseindia.com/content/circulars/cmtr7864.htm",
     "date": "2006-09-13", "title": "Automation of Bulk/Block deals data",
     "key_fact": "block deals = trades executed in the odd lot market 'BL' series; bulk computation combines "
                 "BL-series and normal-market client combinations ONLY for reporting"},
    {"id": "NSE/SURV/74008", "file": "https://nsearchives.nseindia.com/content/circulars/SURV74008.pdf",
     "date": "2026-04-30", "title": "Surveillance and Investigation Consolidated Circular",
     "key_facts": ["T2T segment scrips trade under BE series (ref NSE/SURV/33844 2016-12-19; NSE/SURV/58561 2023-09-25)",
                   "GSM stages II-IV = Trade for Trade; ESM stage I = 100% margin + T2T w/ price bands",
                   "illiquid-securities turnover computation considers trades across EQ, BE, BT, IL and BL series",
                   "E1/W1 etc. are equity-linked non-common (partly-paid/warrants), excluded from illiquid shortlist"]},
    {"id": "NSE/CMTR/37880", "file": "cited-on: https://www.nseindia.com/static/products-services/equity-market-segment",
     "date": "2018-05-30", "title": "Trading in IL series discontinued w.e.f 2018-07-01 (CM segment)",
     "key_fact": "IL = inter-institutional deals segment window (institutional-only; FII ceiling management), "
                 "trades settled under market type 'N', series IL — a SEPARATE market segment from normal market"},
    {"id": "NSE-EMERGE-PAGE", "file": "https://www.nseindia.com/static/products-services/emerge-sme-market-segment",
     "date": "accessed 2026-10-06", "title": "Market Sub-Segments (SME)",
     "key_facts": ["SME rolling settlement securities trade under SM series",
                   "SME Trade-for-Trade securities trade under ST series",
                   "odd-lot market on SME uses series SO, market type O"]},
    {"id": "NSE-ESM-2026", "file": "cited-in-search: NSE ESM applicability circular (Jan 2026)",
     "date": "2026-01-14", "title": "ESM framework", "key_fact":
     "securities under ESM shifted from rolling settlement segment (series EQ/SM) to trade-for-trade segment "
     "(series BE/ST) — official movement mechanism for the EQ<->BE / SM<->ST transitions measured in D03"},
    {"id": "NSE-INTER-INST-PAGE", "file": "https://www.nseindia.com/products/content/equities/equities/inter_inst_deals.htm",
     "date": "accessed 2026-10-06", "title": "Inter-Institutional Deals and Block Deals",
     "key_facts": ["block deal window: minimum order Rs 10 crore; trades settled under market type 'N', series 'BL'; "
                   "T+2 rolling, compulsory demat", "inter-institutional segment: institutional-only, FII sell-side "
                   "restriction; settlement type N, series IL"]},
    {"id": "NSE-DATA-HIST-DOC", "file": "https://archives.nseindia.com/content/press/Data_details_CM.pdf",
     "date": "accessed 2026-10-06", "title": "Historical Data Dissemination of Capital Market Segment from NSE",
     "key_facts": ["Masters database: monthly snapshot (end of preceding month) with fields ISIN, Symbol, Series, "
                   "Name, Deleted flag — historical coverage from the late 1990s",
                   "field definitions: Number of trades = normal market only (excludes auction market); "
                   "Value of shares traded = rupee value; VWAP = field9/field8",
                   "'Once a symbol and a series have been specified, a security is uniquely known' (Masters-based "
                   "unique key in that document's model)"]},
    {"id": "NSE-ETF-MASTER", "file": "https://nsearchives.nseindia.com/content/equities/eq_etfseclist.csv",
     "date": "accessed 2026-10-06", "title": "ETF securities master list",
     "schema": "Symbol,Underlying,SecurityName,DateofListing,MarketLot,ISINNumber,FaceValue",
     "note": "official complete ETF register incl. ISINs — the DEC-1 disambiguation key for EQ-vs-ETF; direct "
             "fetch from sandbox returned HTTP 500; content verified via search index (real rows incl. NIFTYBEES)"}
]


def cal_labels():
    missing = [l.strip() for l in open(MISS) if l.strip() and not l.startswith("#")]
    inv = json.load(open(INV))
    dates = {e["date_from_filename"] for e in inv}
    hol24 = {"2024-07-17": "Moharram", "2024-08-15": "Independence Day", "2024-10-02": "Mahatma Gandhi Jayanti",
             "2024-11-01": "Diwali Laxmi Pujan", "2024-11-15": "Gurunanak Jayanti", "2024-12-25": "Christmas"}
    hol25 = {d: d for d in CIRCULARS[2]["weekday_list"]}
    hol26 = {d: d for d in CIRCULARS[4]["weekday_list"]}
    allhol = {}
    allhol.update({k: v for k, v in hol24.items()})
    allhol.update(hol25)
    allhol.update({k: "NSE/FAOP/71777 weekday" for k, v in hol26.items() if v == v and k in hol26})
    rows = []
    for d in missing:
        if d < "2024-07-08":
            continue
        lab = "OFFICIAL-HOLIDAY" if d in allhol else ("UNEXPLAINED-BY-OBTAINED-CIRCULARS"
               if not (d.startswith("2024") and d >= "2024-07-08" or d.startswith(("2025", "2026"))) else "UNEXPLAINED-BY-OBTAINED-CIRCULARS")
        rows.append({"missing_date": d, "label": lab, "circular": allhol.get(d, "")})
    # exceptions in the other direction: holiday per circular yet file present
    exceptions = []
    for d in sorted(allhol):
        if d in dates and datetime.date.fromisoformat(d).weekday() < 5 and d >= "2024-07-08":
            exceptions.append({"holiday_per_circular": d, "bhav_file": "PRESENT",
                               "note": "2025-10-21: Muhurat special session (NSE/FAOP/70320); file row_count "
                                       "normal-scale per D01 inventory"})
    return {
        "scope": "missing-weekday labeling for the UDiFF era years where official circulars were retrieved "
                 "(2024-H2, 2025, 2026); Legacy-era years NOT labeled (deferred — not decision-relevant, "
                 "D03 stopping rule)",
        "coverage_note": "2026 CM circular excerpt obtained listed only weekend-falling addenda; the F&O "
                         "sibling circular (same notification date, common exchange holiday set) lists the "
                         "weekday dates; alignment below uses that set",
        "per_missing_day": rows,
        "explained": sum(1 for r in rows if r["label"] == "OFFICIAL-HOLIDAY"),
        "unexplained": [r["missing_date"] for r in rows if r["label"].startswith("UNEXPLAINED")],
        "files_present_on_circular_holiday": exceptions,
        "governance_rule": ("Calendar model MUST treat file-presence as the trading-session signal and annual "
                            "circulars as labels: both directions of divergence are observed (2024-11-01 Diwali "
                            "no file; 2025-10-21 circular-holiday WITH a normal-scale file due to the special "
                            "session; 2025-10-20 file-absent though not in the annual list)."),
        "provenance": {"circular_registry_ids": ["NSE/CMTR/59722", "NSE/CMTR/61518", "NSE/CMTR/65587",
                                                 "NSE/CMTR/71775", "NSE/FAOP/71777", "NSE/FAOP/70320"],
                       "inputs": {"file_inventory.json": sha256_file(INV),
                                  "d02_missing_weekdays.txt": sha256_file(MISS)}},
    }


def unit_scale():
    def test(path, qty, val, close):
        rows = list(csv.DictReader(open(path)))
        n = r = l = o = 0
        for x in rows:
            try:
                q, v, c = float(x[qty]), float(x[val]), float(x[close])
            except Exception:
                continue
            if q <= 0 or c <= 0:
                continue
            n += 1
            if abs(v / q / c - 1.0) < 0.02:
                r += 1
            elif abs(v / q / c - 100000.0) / 100000.0 < 0.02:
                l += 1
            else:
                o += 1
        return {"rows_tested": n, "value_equals_qty_times_close_within_2pct": r,
                "value_equals_lakhs_scaled": l, "other_vwap_differs_from_close": o}
    f = lambda name: os.path.join(WR, name)
    return {
        "method": ("For each published stratified row sample, TOTTRDVAL/TtlTrfVal compared to qty*close "
                    "(2% tolerance; residual rows = legitimate VWAP-vs-close gaps, e.g. strong intraday moves)"),
        "legacy_2016-09-20": test(f("FIX-UD-ROW-SAMPLE-01__sample_legacy_2016-09-20.csv"), "TOTTRDQTY", "TOTTRDVAL", "CLOSE"),
        "legacy_2022-10-03": test(f("FIX-UD-ROW-SAMPLE-01__sample_legacy_2022-10-03.csv"), "TOTTRDQTY", "TOTTRDVAL", "CLOSE"),
        "legacy_2024-07-05": test(f("FIX-UD-ROW-SAMPLE-01__sample_legacy_2024-07-05.csv"), "TOTTRDQTY", "TOTTRDVAL", "CLOSE"),
        "udiff_2024-07-08": test(f("FIX-UD-ROW-SAMPLE-01__sample_udiff_2024-07-08.csv"), "TtlTradgVol", "TtlTrfVal", "ClsPric"),
        "official_definition": "NSE Historical Data Dissemination doc: 'Value of shares traded = the rupee value "
                               "of all shares traded in the day; VWAP = field9/field8'; 'Number of trades = normal "
                               "market only (excludes auction market)'",
        "finding": ("No sample row in either era shows lakh scaling; value columns are rupee totals consistent with "
                    "qty x VWAP. Q7 unit question upgraded: value fields = rupees (sample+definition supported). "
                    "Still no embedded units metadata in files — provenance note required by spec regardless."),
        "input_hashes": {p: sha256_file(f(p)) for p in [
            "FIX-UD-ROW-SAMPLE-01__sample_legacy_2016-09-20.csv", "FIX-UD-ROW-SAMPLE-01__sample_legacy_2022-10-03.csv",
            "FIX-UD-ROW-SAMPLE-01__sample_legacy_2024-07-05.csv", "FIX-UD-ROW-SAMPLE-01__sample_udiff_2024-07-08.csv"]},
    }


def overlay_agg():
    from collections import Counter
    rows = list(csv.DictReader(open(os.path.join(WR, "FIX-OVERLAY-SEM-01__per_overlay_row.csv"))))
    c = Counter((r["overlay_series"], r["qty_rel"]) for r in rows if r["match_type"] == "BASE_SAME_ISIN")
    orph = Counter(r["overlay_series"] for r in rows if r["match_type"] == "NO_BASE_ORPHAN")
    return {
        "per_row_published_rows": len(rows),
        "qty_rel_vs_same_day_base_row_for_same_isin": {"%s|%s" % k: v for k, v in sorted(c.items())},
        "orphans": dict(sorted(orph.items())),
        "superset_argument": ("Where overlay volume were INCLUDED in the normal-market row aggregate, every "
                              "overlay row would satisfy overlay_qty <= base_row_qty. Observed: BL qty > base qty "
                              "in %d rows and IL > base in %d rows — inclusion is impossible for those rows. "
                              "Combined with the official segment definitions (BL/IL are separate market windows; "
                              "'number of trades' field defined as normal market only), the evidence supports "
                              "DISJOINT markets for BL/IL: overlay rows ADD to base totals (no double counting)."
                              % (c.get(("BL", "gt"), 0), c.get(("IL", "gt"), 0))),
        "t0_status": "T0 rows: qty always < base (237/237) — consistent with both disjoint-window and "
                     "included models; T0 inclusion semantics NOT established (documentation remains: T+0 "
                     "FAQ says separate series; FAQ does not address totals). Remains OPEN.",
        "bo_status": "BO (buyback) lt only (112): buyback tenders are not exchange-market volume at all; "
                      "treated as separate event rows; inclusion question moot in-corpus.",
        "governance": "Spec may record BL/IL disjointness as EVIDENCE-BACKED (observation + official definition); "
                      "T0 stays OPEN; no aggregate rule may silently sum or drop overlay rows without the flag.",
        "input_hash": {"FIX-OVERLAY-SEM-01__per_overlay_row.csv":
                       sha256_file(os.path.join(WR, "FIX-OVERLAY-SEM-01__per_overlay_row.csv"))},
    }


def circ_meanings():
    return {
        "documented_now": {
            "BE": "Trade-for-Trade (surveillance) — mainboard T2T securities trade under BE (NSE/SURV/74008; "
                  "ref 33844/58561). Dual use with Rights Entitlement (legend 2024) still needs row-level "
                  "disambiguation; EQ<->BE round-trips (5738/5653) are now explained as surveillance entries/exits.",
            "ST": "SME Trade-for-Trade (official NSE EMERGE page) — SM<->ST round-trips (869/1368) mirror "
                  "mainboard EQ<->BE surveillance moves.",
            "SM": "SME rolling settlement series (official NSE EMERGE page).",
            "SO": "SME odd-lot market series (official NSE EMERGE page: 'series for odd lot market is SO, market O').",
            "IL": "Inter-institutional deals window (institutional-only, FII ceiling management); DISCONTINUED "
                  "w.e.f. 2018-07-01 per NSE/CMTR/37880 — consistent with corpus IL span ending 2018-06.",
            "BL": "Block-deal window trades ('odd lot market BL series' per NSE/CMTR/7864; block window per "
                  "inter-institutional page).",
            "T0": "Optional T+0 settlement series (D02 E3 FAQ) — settlement-state variant of same security; "
                  "separate bhavcopy series; first corpus sighting 2024-03-28 matches the Mar-2024 pilot.",
            "ESM": "2026 ESM applicability circular: qualifying securities SHIFT from EQ/SM to BE/ST — the "
                   "official movement mechanism for the transition pairs D03 measured."},
        "still_open": {"SF": "no official definition obtained this session; corpus span 2025-10..11 (D02); remains UNCLASSIFIED",
                       "HA-HE": "not in current legend; retrieval not attempted (no corpus impact)",
                       "IT": "institutional-window rows w/o same-day base (333 orphans incl UDiFF 4) consistent with "
                             "block/institutional venue trades; NO authoritative series definition obtained — stays FROZEN",
                       "legacy-era BE rights-vs-T2T split rule": "needs row evidence (RE-prefix heuristic stays "
                             "evidence-only)"},
        "retroactivity_rule": "definitions above carry the dates of their sources; do NOT apply 2024+ legend/ESM "
                              "framework text to 2016-2023 semantics beyond noting consistency",
        "registry_ref": "see evidence/d04/DEC2_CAL_LABELS.json provenance + CIRCULARS registry in d04_arena_synthesis.py",
    }


def secmaster():
    return {
        "authorization": "GRANTED (DEC-1) for investigation/acquisition-of-evidence only",
        "authoritative_candidate_identified": {
            "masters_database": ("NSE 'Masters' historical database: monthly point-in-time snapshots (end of prior "
                                 "month) keyed symbol+series with ISIN, Name, Deleted flag — per official NSE "
                                 "historical-dissemination document. Would provide HISTORICAL temporal behavior, "
                                 "listing/delisting markers, and era coverage — the exact missing capability."),
            "etf_register": ("eq_etfseclist.csv (nsearchives) — official ETF master (Symbol, Underlying, "
                             "SecurityName, DateofListing, MarketLot, ISINNumber, FaceValue). Directly resolves "
                             "the EQ-contains-ETFs eligibility ambiguity by ISIN membership."),
        },
        "acquisition_status": {
            "etf_register_fetch": "attempted 2026-10-06 via sandbox fetch: HTTP 500; sandbox network egress to "
                                  "nseindia blocked for direct downloads (curl TLS failure recorded). Content "
                                  "confirmed present via search index (real rows). ACQUISITION NOT COMPLETED from Arena.",
            "masters_monthly_files": "documented path pattern (…/Masters/YYYY/Mon/YYYYMMDD.gz); binary .gz; "
                                     "same egress limitation; not acquired",
            "next_step": "Windows-side download with the same read-only discipline as the corpus (record URL, "
                         "date, sha256 per file; store under a NEW directory outside the archive roots; no "
                         "retro-writes). Then a bounded join fixture (design: FIX-ETF-JOIN-02) computes "
                         "EQ∩ETF-ISIN counts per file.",
        },
        "authority_disposition": ("SECURITY MASTER NOT treated as authoritative for identity/eligibility merely "
                                   "because acquired: authority requires (i) provenance capture per file, (ii) "
                                   "consistency test against corpus (symbol/series/ISIN agreement at overlapping "
                                   "dates), (iii) explicit user acceptance of its role. Until then: cross-check "
                                   "source, not source of truth."),
        "can_it_establish_historical_eligibility_identity": {
            "answer": "YES-partially, on documentation: monthly Masters snapshots + ETF register give era-correct "
                      "symbol/series/ISIN/deleted facts and complete ETF membership → eligibility disambiguation "
                      "and listing-date semantics become decidable; NO for any claim that master fields redefine "
                      "exchange-level identity semantics (that remains governance).",
            "evidence": "official NSE historical-data document field definitions; D03 corpus consistency facts "
                        "(7,633 ISINs; zero blanks; boundary 205 one-sided rows are exactly what dated masters "
                        "would adjudicate as listing/delisting vs defect)"},
        "no_assumption_recorded": True,
    }


def main():
    for name, obj in [("DEC2_CAL_LABELS.json", cal_labels()),
                      ("DEC2_Q7_UNIT_SCALE.json", unit_scale()),
                      ("DEC2_Q8_OVERLAY_AGG.json", overlay_agg()),
                      ("DEC2_CIRC_MEANINGS.json", circ_meanings()),
                      ("DEC1_SECMASTER_FEASIBILITY.json", secmaster()),
                      ("DEC12_CIRCULAR_REGISTRY.json", {"generated_by": "evidence/d04/d04_arena_synthesis.py",
                                                         "deterministic": True,
                                                         "note": "Recorded official-documentation registry; fetch "
                                                                 "date 2026-10-06; excerpts as retrieved; not "
                                                                 "corpus evidence",
                                                         "circulars": CIRCULARS})]:
        p = os.path.join(OUTDIR, name)
        with open(p, "w") as f:
            json.dump(obj, f, indent=2, sort_keys=True)
            f.write("\n")
        print("wrote", name)


if __name__ == "__main__":
    main()
