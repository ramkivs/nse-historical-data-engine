#!/usr/bin/env python3
"""
D02 read-only derivation script.

Regenerates every derived evidence artifact in evidence/identity/ strictly from
the committed D01 inventory evidence in evidence/inventory/.

It reads the repository evidence only. It does not touch, and cannot see, the
Windows raw NSE archives. It writes only into evidence/identity/.

Usage (from repository root):
    python3 evidence/identity/d02_derivation.py
"""

import collections
import csv
import datetime
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
INV_PATH = os.path.join(HERE, "..", "inventory", "file_inventory.json")

# ---------------------------------------------------------------------------
# Provisional series classification, grounded in the NSE "Legend of series"
# (https://www.nseindia.com/static/market-data/legend-of-series, updated
# 2024-09-19) as public documentation of NSE capital-market series codes.
# Every class here is PROVISIONAL and does not constitute an implementation
# rule (D02 authority boundary).
# ---------------------------------------------------------------------------
def classify(series: str):
    s = series
    if s == "EQ":
        return ("EQUITY_COMMON",
                "NSE legend: fully paid equity shares/ETFs (rolling). Legend row explicitly includes ETFs.")
    if s == "SM":
        return ("EQUITY_SME", "NSE legend: fully paid equity shares SME (rolling).")
    if s == "BE":
        return ("EQUITY_T2T_RIGHTS_AMBIGUOUS",
                "NSE legend dual use: fully-paid equity T2T variant AND Rights Entitlement. Row-level disambiguation required.")
    if s == "BZ":
        return ("EQUITY_T2T", "NSE legend: mainboard equity/ETF moved to Trade-for-Trade (Z category).")
    if s in ("ST", "SZ"):
        return ("EQUITY_SME_T2T", "NSE legend: SME equity T2T variants. Corpus shows large ST distribution shift at the format transition (unexplained).")
    if re.fullmatch(r"E[1-9A-Z]", s):
        return ("EQUITY_PARTLYPAID", "NSE legend: partly paid equity shares (rolling), E@.")
    if re.fullmatch(r"X[1-9A-Z]", s):
        return ("EQUITY_PARTLYPAID_T2T", "NSE legend: partly paid equity T2T variants, X@.")
    if s == "BL":
        return ("OVERLAY_BLOCK_DEALS",
                "NSE legend: Block Deals sub-segment. D02 aggregate evidence: BL rows coincide with per-file distinct-ISIN deficits (rows do not introduce new securities).")
    if s == "BO":
        return ("OVERLAY_BUYBACK_WINDOW", "NSE legend: buyback of equity shares via stock-exchange route.")
    if s == "T0":
        return ("OVERLAY_T0_SETTLEMENT",
                "NSE T+0 settlement FAQ: same securities trade in a separate T0 series (first corpus sighting 2024-03-28 matches the optional T+0 pilot window).")
    if s in ("IT", "IL"):
        return ("OVERLAY_INSTITUTIONAL_WINDOW_HYPOTHESIS",
                "Not in NSE legend. Third-party mapping: IL = FII-to-FII trading window. Treat as hypothesis pending fixtures.")
    if re.fullmatch(r"P[1-9A-Z]", s):
        return ("EQUITY_LINKED_PREFERRED_NC", "NSE legend: non-convertible preference shares (rolling), P@.")
    if re.fullmatch(r"Q[1-9A-Z]", s):
        return ("EQUITY_LINKED_PREFERRED_FC", "NSE legend: fully convertible preference shares (rolling), Q@.")
    if re.fullmatch(r"W[1-9A-Z]", s):
        return ("EQUITY_LINKED_WARRANT", "NSE legend: convertible warrants (rolling), W@.")
    if re.fullmatch(r"K[1-9A-Z]", s):
        return ("EQUITY_LINKED_WARRANT_T2T", "NSE legend: warrants T2T variants, K@.")
    if s == "MF":
        return ("NON_EQUITY_MUTUAL_FUND", "NSE legend: close-ended mutual fund units (rolling).")
    if s == "ME":
        return ("NON_EQUITY_MUTUAL_FUND_T2T", "NSE legend: mutual fund units T2T.")
    if s in ("IV", "ID"):
        return ("NON_EQUITY_INVIT",
                "NSE legend: InvIT units (IV rolling / ID T2T). CAUTION: first corpus IV sighting 2017-05-18 predates NSE InvIT listings; possible earlier different meaning (code reuse).")
    if s in ("RR", "RT"):
        return ("NON_EQUITY_REIT", "NSE legend: REIT units (RR rolling / RT T2T).")
    if s == "GB":
        return ("NON_EQUITY_GOLD_BOND", "NSE legend: Gold Bond (incl. Sovereign Gold Bonds).")
    if s == "GS":
        return ("NON_EQUITY_GOVT_SEC", "NSE legend: Government Securities.")
    if s == "TB":
        return ("NON_EQUITY_TREASURY_BILL", "NSE legend: Treasury Bills.")
    if s == "SG":
        return ("NON_EQUITY_SDL", "NSE legend: State Development Loans.")
    if re.fullmatch(r"(N|Y|Z|A)[0-9A-Z]", s):
        return ("NON_EQUITY_CORP_BOND_NC", "NSE legend: non-convertible debt instruments (rolling); N@/Y@/Z@/A@ per-issue letter series.")
    if re.fullmatch(r"B[0-9A-Z]", s) and s not in ("BE", "BZ", "BL", "BO"):
        return ("NON_EQUITY_CORP_BOND_NC", "NSE legend: non-convertible debt instruments (rolling), B@ minus named specials.")
    if re.fullmatch(r"(U|M)[0-9A-Z]", s) and not s.startswith("MF") and not s.startswith("ME"):
        return ("NON_EQUITY_CORP_BOND_NC_T2T", "NSE legend: non-convertible debt T2T variants (@@/U@/M@).")
    if re.fullmatch(r"D[0-9A-Z]", s):
        return ("NON_EQUITY_CORP_BOND_FC", "NSE legend: fully convertible debt instruments (rolling), D@.")
    if s == "SF":
        return ("NON_EQUITY_CORP_BOND_FC_T2T", "NSE legend: fully convertible debt T2T (S@ minus excluded SM/ST/SP/SL/SI/SO/SQ/SG).")
    return ("UNCLASSIFIED", "Not resolvable from the NSE legend or D01 evidence. Requires row-level inspection and/or NSE circular search.")


def main():
    with open(INV_PATH) as f:
        inv = json.load(f)
    inv.sort(key=lambda e: e["date_from_filename"])

    leg = [e for e in inv if e["root"] == "LEGACY"]
    udf = [e for e in inv if e["root"] == "UDIFF"]
    total_rows = sum(e["row_count"] for e in inv)

    # ---- per-series lifecycle profile -------------------------------------
    prof = {}
    for e in inv:
        d = e["date_from_filename"]
        for s, c in e["series_counts"].items():
            p = prof.setdefault(s, {
                "leg": 0, "udf": 0, "legdays": 0, "udfdays": 0,
                "first": d, "last": d, "maxperday": 0,
                "firstleg": None, "lastleg": None, "firstudf": None, "lastudf": None,
            })
            if e["root"] == "LEGACY":
                p["leg"] += c
                p["legdays"] += 1
                p["firstleg"] = p["firstleg"] or d
                p["lastleg"] = d
            else:
                p["udf"] += c
                p["udfdays"] += 1
                p["firstudf"] = p["firstudf"] or d
                p["lastudf"] = d
            p["maxperday"] = max(p["maxperday"], c)
            p["first"] = min(p["first"], d)
            p["last"] = max(p["last"], d)

    with open(os.path.join(HERE, "d02_series_universe.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["series", "provisional_class", "total_obs", "legacy_obs", "udiff_obs",
                    "legacy_days", "udiff_days", "first_seen", "last_seen",
                    "legacy_first", "legacy_last", "udiff_first", "udiff_last",
                    "max_rows_per_day", "format_presence", "classification_basis"])
        for s, p in sorted(prof.items(), key=lambda kv: -(kv[1]["leg"] + kv[1]["udf"])):
            cls, why = classify(s)
            presence = "BOTH" if p["leg"] and p["udf"] else ("LEGACY_ONLY" if p["leg"] else "UDIFF_ONLY")
            w.writerow([s, cls, p["leg"] + p["udf"], p["leg"], p["udf"],
                        p["legdays"], p["udfdays"], p["first"], p["last"],
                        p["firstleg"] or "", p["lastleg"] or "", p["firstudf"] or "", p["lastudf"] or "",
                        p["maxperday"], presence, why])

    # ---- class rollup --------------------------------------------------------
    cl = collections.Counter()
    ob = collections.Counter()
    for s, p in prof.items():
        c, _ = classify(s)
        cl[c] += 1
        ob[c] += p["leg"] + p["udf"]
    with open(os.path.join(HERE, "d02_series_class_rollup.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["provisional_class", "n_codes", "total_obs", "pct_of_all_rows"])
        for k in sorted(ob, key=lambda k: -ob[k]):
            w.writerow([k, cl[k], ob[k], round(100.0 * ob[k] / total_rows, 3)])

    # ---- transition table ----------------------------------------------------
    def by_date(d):
        for e in inv:
            if e["date_from_filename"] == d:
                return e
        return None

    L, U = by_date("2024-07-05"), by_date("2024-07-08")
    series_union = sorted(set(L["series_counts"]) | set(U["series_counts"]),
                          key=lambda s: -(L["series_counts"].get(s, 0) + U["series_counts"].get(s, 0)))
    with open(os.path.join(HERE, "d02_transition_20240705_vs_20240708.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["series", "legacy_20240705_rows", "udiff_20240708_rows"])
        for s in series_union:
            w.writerow([s, L["series_counts"].get(s, 0), U["series_counts"].get(s, 0)])

    # ---- distribution shift across the transition ----------------------------
    def avg_rows(fs, head_or_tail):
        fs = fs[-250:] if head_or_tail == "tail" else fs[:250]
        c = collections.Counter()
        for e in fs:
            for s, v in e["series_counts"].items():
                c[s] += v
        return {s: v / len(fs) for s, v in c.items()}

    La, Ua = avg_rows(leg, "tail"), avg_rows(udf, "head")
    with open(os.path.join(HERE, "d02_series_distribution_shift.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["series", "legacy_avg_rows_per_day_last250", "udiff_avg_rows_per_day_first250", "delta"])
        for s in sorted(set(La) | set(Ua),
                        key=lambda s: -(abs(Ua.get(s, 0) - La.get(s, 0)))):
            l, u = La.get(s, 0.0), Ua.get(s, 0.0)
            w.writerow([s, round(l, 2), round(u, 2), round(u - l, 2)])

    # ---- ISIN-deficit residual analysis --------------------------------------
    def deficits(fs):
        d0 = d1 = d2 = 0
        resid = collections.Counter()
        for e in fs:
            deficit = e["row_count"] - e["isin_count"]
            bl = e["series_counts"].get("BL", 0)
            t0 = e["series_counts"].get("T0", 0)
            if deficit == bl:
                d0 += 1
            if deficit == bl + t0:
                d1 += 1
            resid[deficit - bl - t0] += 1
        r = collections.Counter({str(k): v for k, v in sorted(resid.items())})
        return {"deficit_eq_BL_files": d0, "deficit_eq_BL_plus_T0_files": d1, "residual_dist": r}

    # ---- anomalies -------------------------------------------------------------
    anomalies = {
        "legacy_header_variant_files": [
            {"file": e["file_name"], "date": e["date_from_filename"],
             "trailing_empty_field": e["header_signature"].endswith("ISIN|")}
            for e in inv
            if e["root"] == "LEGACY" and not e["header_signature"].endswith("ISIN|")
        ],
        "legacy_timestamp_2digit_year_files": [
            {"file": e["file_name"], "date": e["date_from_filename"], "date_values": list(e["date_values"])}
            for e in inv
            if any(re.fullmatch(r"\d{2}-[A-Za-z]{3}-\d{2}", v) for v in e["date_values"])
        ],
        "files_with_BL_rows_but_zero_isin_deficit": [
            {"file": e["file_name"], "date": e["date_from_filename"], "BL": e["series_counts"].get("BL", 0)}
            for e in inv
            if e["series_counts"].get("BL", 0) > 0 and e["row_count"] == e["isin_count"]
        ],
    }
    with open(os.path.join(HERE, "d02_anomalies.json"), "w") as f:
        json.dump(anomalies, f, indent=2)

    # ---- coverage gap list (missing weekdays vs filename dates) -----------------
    alld = sorted(datetime.date.fromisoformat(e["date_from_filename"]) for e in inv)
    have = set(alld)
    missing = []
    if alld:
        d = alld[0]
        while d <= alld[-1]:
            if d.weekday() < 5 and d not in have:
                missing.append(d.isoformat())
            d += datetime.timedelta(days=1)
    with open(os.path.join(HERE, "d02_missing_weekdays.txt"), "w") as f:
        f.write("# Missing weekday file-dates within 2016-09-20..2026-09-18 (D02 derivation).\n")
        f.write("# Requires reconciliation against the official NSE trading-holiday calendar (Windows fixture CAL-01).\n")
        for m in missing:
            f.write(m + "\n")

    # ---- metrics ----------------------------------------------------------------
    lset = set(s for e in leg for s in e["series_counts"])
    uset = set(s for e in udf for s in e["series_counts"])
    metrics = {
        "total_files": len(inv),
        "total_rows": total_rows,
        "legacy_files": len(leg),
        "legacy_rows": sum(e["row_count"] for e in leg),
        "udiff_files": len(udf),
        "udiff_rows": sum(e["row_count"] for e in udf),
        "files_series_sum_equals_row_count": sum(1 for e in inv if sum(e["series_counts"].values()) == e["row_count"]),
        "distinct_series_codes": len(prof),
        "series_shared_across_formats": len(lset & uset),
        "series_legacy_only": sorted(lset - uset),
        "series_udiff_only": sorted(uset - lset),
        "eq_rows": sum(e["series_counts"].get("EQ", 0) for e in inv),
        "files_with_eq": sum(1 for e in inv if e["series_counts"].get("EQ")),
        "files_with_zero_duplicate_symbols": sum(1 for e in inv if e["symbol_count"] == e["row_count"]),
        "files_isin_deficit": sum(1 for e in inv if e["isin_count"] < e["row_count"]),
        "files_isin_excess": sum(1 for e in inv if e["isin_count"] > e["row_count"]),
        "isin_deficit_legacy": deficits(leg),
        "isin_deficit_udiff": deficits(udf),
        "transition": {
            "legacy_20240705_rows": L["row_count"], "udiff_20240708_rows": U["row_count"],
            "legacy_20240705_eq": L["series_counts"].get("EQ", 0), "udiff_20240708_eq": U["series_counts"].get("EQ", 0),
            "series_shared_on_boundary": len(set(L["series_counts"]) & set(U["series_counts"])),
        },
        "missing_weekdays_count": len(missing),
    }
    with open(os.path.join(HERE, "d02_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print("D02 derivation complete. metrics:")
    print(json.dumps({k: v for k, v in metrics.items() if not isinstance(v, list)}, indent=2))


if __name__ == "__main__":
    main()
