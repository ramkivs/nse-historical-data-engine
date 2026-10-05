#!/usr/bin/env python3
"""
D03 fixture-tool selftest.

Builds a SYNTHETIC mini-corpus in a temp directory (never the repository, never
the raw archives), runs every fixture generator, and checks behaviour against
hand-computed expectations. Also proves determinism: two runs with a frozen
timestamp must be byte-identical across all outputs including RUN_INFO.

Synthetic data is tool-verification data only. It is NOT corpus evidence.

Run:  python3 tools/d03_fixture_scan/d03_selftest.py
"""
import csv
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import d03_fixtures as D  # noqa: E402

UDIFF_COLS = D.__dict__.get("_UDIFF_COLS") or ["TradDt", "BizDt", "Sgmt", "Src", "FinInstrmTp", "FinInstrmId", "ISIN",
    "TckrSymb", "SctySrs", "XpryDt", "FininstrmActlXpryDt", "StrkPric", "OptnTp", "FinInstrmNm", "OpnPric",
    "HghPric", "LwPric", "ClsPric", "LastPric", "PrvsClsgPric", "UndrlygPric", "SttlmPric", "OpnIntrst",
    "ChngInOpnIntrst", "TtlTradgVol", "TtlTrfVal", "TtlNbOfTxsExctd", "SsnId", "NewBrdLotQty", "Rmks",
    "Rsvd1", "Rsvd2", "Rsvd3", "Rsvd4"]
LEGACY_COLS = ["SYMBOL", "SERIES", "OPEN", "HIGH", "LOW", "CLOSE", "LAST", "PREVCLOSE", "TOTTRDQTY",
               "TOTTRDVAL", "TIMESTAMP", "TOTALTRADES", "ISIN"]

FAILURES = []


def check(name, got, exp):
    if got != exp:
        FAILURES.append("%s: got %r want %r" % (name, got, exp))
        print("FAIL %-58s got=%r want=%r" % (name, got, exp))
    else:
        print("ok   %-58s %r" % (name, got))


def wzip(d, name, lines):
    """Write <d>/<name>.zip containing member <name>."""
    os.makedirs(d, exist_ok=True)
    with zipfile.ZipFile(os.path.join(d, name + ".zip"), "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(name, "\n".join(lines) + "\n")


def leg(sym, ser, close="100.00", prevc="99.00", qty="1000", val="100000", trd="10", isin="", ts=None, trailing=True):
    row = [sym, ser, close, close, close, close, close, prevc, qty, val, "", trd, isin]
    return row + ([""] if trailing else [])


def lline(fields, ts):
    fields = list(fields)
    fields[10] = ts
    return ",".join(fields) + ("," if len(fields) == 14 else "")


def urow(sym, ser, isin="", fid="", sgmt="0", src="NSE", typ="EQIT", close="100.00", prevc="99.00",
          qty="1000", val="100000", trd="10", trad=None, biz=None):
    d = {c: "" for c in UDIFF_COLS}
    d.update({"TradDt": trad, "BizDt": biz, "Sgmt": sgmt, "Src": src, "FinInstrmTp": typ,
              "FinInstrmId": fid, "ISIN": isin, "TckrSymb": sym, "SctySrs": ser, "ClsPric": close,
              "PrvsClsgPric": prevc, "TtlTradgVol": qty, "TtlTrfVal": val, "TtlNbOfTxsExctd": trd})
    return ",".join(d[c] if d[c] is not None else "" for c in UDIFF_COLS)


def build(root):
    I = {("X%d" % i): D.make_isin("IN00000000%d" % i) for i in range(1, 17)}
    L = os.path.join(root, "legacy")
    U = os.path.join(root, "udiff")

    # L1: 2019-01-01, trailing-pipe header, 10 hand-specified rows
    rows = [
        leg("RELIANCE", "EQ", close="105.00", isin=I["X1"]),
        leg("TATASTEEL", "EQ", close="200.00", isin=I["X2"]),
        leg("RELIANCE", "EQ", close="105.00", isin=I["X3"]),
        leg("RELIANCE", "N6", close="100.00", isin=I["X4"]),
        leg("RE-TATAMOTORS", "BE", close="10.00", isin=I["X5"]),
        leg("XYZ", "BL", close="105.00", qty="5000", isin=""),
        leg("XYZ", "EQ", close="105.00", qty="9000", isin=I["X6"]),
        leg("XYZ", "BL", close="105.00", qty="1500", isin=I["X6"]),
        leg("ABC", "T0", close="50.00", qty="10", isin=I["X7"]),
        leg("", "BE", close="1.00", qty="1", isin=""),
    ]
    wzip(L, "cm01JAN2019bhav.csv", [",".join(LEGACY_COLS + [""])] + [lline(r, "01-JAN-2019") for r in rows])

    wzip(L, "cm31DEC2018bhav.csv", [",".join(LEGACY_COLS + [""])] +
         [lline(leg("IRRCON", "EQ", isin=I["X1"], close="50.00"), "31-DEC-2018")])

    # anomaly window 2017 (header variants)
    wzip(L, "cm07JUL2017bhav.csv", [",".join(LEGACY_COLS + [""])] + [lline(leg("AAA", "EQ", isin=I["X2"]), "07-JUL-2017")])
    wzip(L, "cm10JUL2017bhav.csv", [",".join(LEGACY_COLS)] +
         [",".join(leg("BBB", "EQ", isin=I["X3"], trailing=False)), ",".join(leg("CCC", "SM", isin=I["X4"], trailing=False))])
    for d in ("11", "12", "13"):
        wzip(L, "cm%sJUL2017bhav.csv" % d, [",".join(LEGACY_COLS + [""])] + [lline(leg("DDD", "EQ", isin=I["X5"]), "%s-JUL-2017" % d)])

    # 2020 anomaly: 2-digit-year timestamps + no trailing pipe
    wzip(L, "cm10JUL2020bhav.csv", [",".join(LEGACY_COLS + [""])] + [lline(leg("EEE", "EQ", isin=I["X6"]), "10-JUL-2020")])
    row2020 = leg("FFF", "EQ", isin=I["X7"], trailing=False)
    row2020[10] = "13-Jul-20"          # two-digit-year timestamp (D01 anomaly)
    wzip(L, "cm13JUL2020bhav.csv", [",".join(LEGACY_COLS)] + [",".join(row2020)])
    wzip(L, "cm14JUL2020bhav.csv", [",".join(LEGACY_COLS + [""])] + [lline(leg("GGG", "EQ", isin=I["X8"]), "14-JUL-2020")])

    # last legacy day (xcont left side)
    lr = [lline(leg("RELIANCE", "EQ", close="105.00", prevc="104.00", isin=I["X1"]), "05-JUL-2024"),
          lline(leg("TATAMOTORS", "EQ", close="300.00", isin=I["X8"]), "05-JUL-2024"),
          lline(leg("ANIL", "A1", close="10.00", isin=I["X2"]), "05-JUL-2024"),
          lline(leg("WIPRO", "EQ", close="40.00", prevc="39.00", isin=I["X10"]), "05-JUL-2024"),
          lline(leg("VEDL", "EQ", close="30.00", isin=I["X11"]), "05-JUL-2024")]
    wzip(L, "cm05JUL2024bhav.csv", [",".join(LEGACY_COLS + [""])] + lr)

    # UDiFF first day
    u1 = [
        urow("RELIANCE", "EQ", isin=I["X1"], fid=I["X1"], close="105.00", prevc="105.00", trad="2024-07-08", biz="2024-07-08"),
        urow("TATAMOTORS", "EQ", isin="", fid="FID2", trad="2024-07-08", biz="2024-07-08"),
        urow("GOLDBEES", "EQ", isin=I["X12"], fid=I["X12"], typ="ETUF", trad="2024-07-08", biz="2024-07-08"),
        urow("RELIANCE", "BL", isin="", trad="2024-07-08", biz="2024-07-08"),
        urow("RELIANCE", "T0", isin=I["X1"], close="105.00", qty="500", trad="2024-07-08", biz="2024-07-08"),
        urow("RE-WIPRO", "BE", isin=I["X13"], trad="2024-07-08", biz="2024-07-08"),
        urow("WIPROLTD", "EQ", isin=I["X10"], close="40.00", prevc="41.00", trad="2024-07-08", biz="2024-07-08"),
        urow("VEDL", "ST", isin=I["X11"], close="30.00", prevc="30.00", trad="2024-07-08", biz="2024-07-08"),
        urow("NEWLIST", "EQ", isin=I["X14"], trad="2024-07-08", biz="2024-07-08"),
        urow("ABCDEF", "EQ", isin=I["X15"], trad="2024-07-08", biz="2024-07-09"),
        urow("DEF", "IT", isin=I["X16"], trad="2024-07-08", biz="2024-07-08"),
    ]
    wzip(U, "BhavCopy_NSE_CM_0_0_0_20240708_F_0000.csv", [",".join(UDIFF_COLS)] + u1)
    wzip(U, "BhavCopy_NSE_CM_0_0_0_20240709_F_0000.csv", [",".join(UDIFF_COLS)] +
         [urow("RELIANCE", "EQ", isin=I["X1"], trad="2024-07-09", biz="2024-07-09")])
    return I


def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def run_tests():
    tmp = tempfile.mkdtemp(prefix="d03_selftest_")
    try:
        root = os.path.join(tmp, "corpus")
        I = build(root)
        # isin helper checks first
        check("validate_isin valid", D.validate_isin(I["X1"]), "VALID")
        flipped = I["X1"][:-1] + str((int(I["X1"][-1]) + 1) % 10)
        check("validate_isin bad checkdigit", D.validate_isin(flipped), "INVALID_CHECKDIGIT")
        check("validate_isin blank", D.validate_isin("  "), "BLANK")

        d01 = os.path.join(tmp, "file_inventory.json")
        # first compute metrics to build a truthful fake D01 entry (distinct semantics)
        fake = os.path.join(root, "legacy", "cm01JAN2019bhav.csv.zip")
        m = D.file_metrics(fake)
        with open(d01, "w") as f:
            json.dump([{"file_name": "cm01JAN2019bhav.csv.zip",
                        "isin_count": m["distinct_nonblank_isin"],
                        "symbol_count": m["distinct_nonblank_symbol"]}], f)

        argv_ns = ["run", "--legacy-root", os.path.join(root, "legacy"), "--udiff-root", os.path.join(root, "udiff"),
                   "--d01-inventory", d01, "--frozen-time", "2026-10-05T00:00:00+00:00"]
        a1 = os.path.join(tmp, "out1")
        a2 = os.path.join(tmp, "out2")
        args = D.parse_args(argv_ns + ["--out", a1])
        info1 = D.generate(args, a1)
        args2 = D.parse_args(argv_ns + ["--out", a2])
        info2 = D.generate(args2, a2)

        # determinism: all files byte-identical
        names = sorted(os.listdir(a1))
        check("file set equal", names == sorted(os.listdir(a2)), True)
        same = all(
            open(os.path.join(a1, n), "rb").read() == open(os.path.join(a2, n), "rb").read()
            for n in names)
        check("determinism: byte-identical rerun", same, True)

        # manifest verify mode
        vargv = ["verify", "--legacy-root", os.path.join(root, "legacy"), "--udiff-root", os.path.join(root, "udiff"),
                 "--d01-inventory", d01, "--frozen-time", "2026-10-05T00:00:00+00:00", "--out", a1]
        rc = D.main(vargv)
        check("manifest verify", rc, 0)

        # FIX-SEM-DEF-01 expectations for L1
        r = {x["file"]: x for x in read_csv(os.path.join(a1, "FIX-SEM-DEF-01__metrics.csv"))}
        x = r["cm01JAN2019bhav.csv.zip"]
        check("semdef rows", int(x["rows"]), 10)
        check("semdef blank_isin", int(x["blank_isin_rows"]), 2)
        check("semdef distinct_isin", int(x["distinct_nonblank_isin"]), 7)
        check("semdef nonblank_rows", int(x["nonblank_isin_rows"]), 8)
        check("semdef dup_extra", int(x["isins_extra_duplicate_rows"]), 1)
        check("semdef distinct_sym", int(x["distinct_nonblank_symbol"]), 5)
        check("semdef pairs", int(x["distinct_symbol_series_pairs"]), 8)
        check("semdef pair_dupes", int(x["symbol_series_duplicate_rows"]), 2)
        check("semdef d01 matches distinct", x["d01_isin_eq_distinct_nonblank"], "True")
        check("semdef d01 != nonblank rows", x["d01_isin_eq_nonblank_rows"], "False")

        # FIX-UD-CENSUS-01
        groups = read_csv(os.path.join(a1, "FIX-UD-CENSUS-01__groups.csv"))
        g = {("%s|%s|%s|%s" % (row["Sgmt"], row["Src"], row["FinInstrmTp"], row["SctySrs"])): row for row in groups}
        check("census EQ rows", int(g["0|NSE|EQIT|EQ"]["row_count"]), 6)
        check("census EQ blank isin", int(g["0|NSE|EQIT|EQ"]["blank_or_ws_isin_rows"]), 1)
        check("census T0 rows", int(g["0|NSE|EQIT|T0"]["row_count"]), 1)
        check("census fid_eq isin rows (EQ)", int(g["0|NSE|EQIT|EQ"]["finstrmid_eq_isin_rows"]), 1)
        etuf = [row for row in groups if row["FinInstrmTp"] == "ETUF"]
        check("census ETUF group present", len(etuf), 1)
        hw = json.load(open(os.path.join(a1, "FIX-UD-CENSUS-01__header_width_check.json")))
        check("header width verdict", hw["verdict"].startswith("VERIFIED"), True)
        check("header width 34", hw["observed_width_counts"], {"34": 2})

        # FIX-XCONT-01
        s = json.load(open(os.path.join(a1, "FIX-XCONT-01__summary.json")))
        check("xcont matched", s["isin_matched"], 3)
        check("xcont only_legacy", s["isin_only_legacy"], 2)
        check("xcont only_udiff", s["isin_only_udiff"], 5)
        check("xcont symbol changes", s["matched_symbol_changes"], 1)
        check("xcont series changes", s["matched_series_changes"], 1)
        check("xcont chain eq", s["price_chain_prev_close_eq_legacy_close"], 2)
        check("xcont chain ne", s["price_chain_prev_close_ne_legacy_close"], 1)
        check("xcont udiff blank isin rows", s["blank_isin_rows"]["udiff"], 2)

        # FIX-OVERLAY-SEM-01
        o = json.load(open(os.path.join(a1, "FIX-OVERLAY-SEM-01__aggregate.json")))["counts_by_format_series_matchtype"]
        check("overlay LEG BL by symbol", o.get("LEGACY|BL|BASE_BY_SYMBOL_ONLY"), 1)
        check("overlay LEG BL same isin", o.get("LEGACY|BL|BASE_SAME_ISIN"), 1)
        check("overlay LEG T0 orphan", o.get("LEGACY|T0|NO_BASE_ORPHAN"), 1)
        check("overlay UD BL by symbol", o.get("UDIFF|BL|BASE_BY_SYMBOL_ONLY"), 1)
        check("overlay UD T0 same isin", o.get("UDIFF|T0|BASE_SAME_ISIN"), 1)
        check("overlay UD IT orphan", o.get("UDIFF|IT|NO_BASE_ORPHAN"), 1)
        rows = read_csv(os.path.join(a1, "FIX-OVERLAY-SEM-01__per_overlay_row.csv"))
        xyz = [r for r in rows if r["overlay_symbol"] == "XYZ" and r["overlay_isin"] == I["X6"]][0]
        check("overlay xyz qty rel lt", xyz["qty_rel"], "lt")
        check("overlay xyz close rel eq", xyz["close_rel"], "eq")
        check("overlay xyz isin cmp", xyz["isin_cmp"], "isin_eq")

        # FIX-SYMBOL-HIST-01
        sh = json.load(open(os.path.join(a1, "FIX-SYMBOL-HIST-01__summary.json")))
        check("symbolhist multi_symbol", sh["isins_with_multiple_symbols"] >= 1, True)
        trans = read_csv(os.path.join(a1, "FIX-SYMBOL-HIST-01__transitions.csv"))
        wipro = [t for t in trans if t["isin"] == I["X10"]]
        check("symbolhist WIPRO symbol-change row", len(wipro) == 1 and wipro[0]["symbol_before"] == "WIPRO"
              and wipro[0]["symbol_after"] == "WIPROLTD" and wipro[0]["transition_type"] == "SEQUENCE", True)
        irr = [t for t in trans if t["isin"] == I["X1"]]
        check("symbolhist X1 transitions (IRRCON->RELIANCE)", len(irr) >= 1, True)

        # FIX-SERIES-EVENTS-01
        tc = {r["transition"]: int(r["count"]) for r in read_csv(os.path.join(a1, "FIX-SERIES-EVENTS-01__transition_pair_counts.csv"))}
        check("seriesevents EQ->ST count", tc.get("EQ->ST"), 1)
        cooc = {("%s,%s" % (r["series_a"], r["series_b"])): int(r["isin_days"])
                for r in read_csv(os.path.join(a1, "FIX-SERIES-EVENTS-01__same_day_series_cooccurrence.csv"))}
        check("seriesevents BL/EQ same-day cooc", cooc.get("BL,EQ"), 1)
        check("seriesevents EQ/T0 same-day cooc", cooc.get("EQ,T0"), 1)

        # FIX-ANOM-01
        an = json.load(open(os.path.join(a1, "FIX-ANOM-01__report.json")))
        rep = an["reports"]
        by_target = {r["target"]: r["per_file"] for r in rep}
        check("anom 2017-07-10 header fields", by_target["2017-07-10"]["2017-07-10"]["header_fields"], 13)
        check("anom 2017-07-07 header fields (neighbor)", by_target["2017-07-10"]["2017-07-07"]["header_fields"], 14)
        check("anom 2020-07-13 timestamp format", by_target["2020-07-13"]["2020-07-13"]["timestamp_format_hist"],
              {"DD-Mon-YY_2digit_year": 1})
        check("anom window includes neighbors", len(by_target["2017-07-10"]) >= 3, True)

        # row-sample fallbacks + NOT_FOUND recording
        rs = json.load(open(os.path.join(a1, "FIX-UD-ROW-SAMPLE-01__selection_and_coverage.json")))
        per = rs["per_date"]
        check("rowsample udiff 0708 exact", per["UDIFF|2024-07-08"]["selection"], "exact")
        check("rowsample udiff biz date dynamic", rs["udiff_dates_dynamic_added"]["first_traddt_ne_bizdt"], "2024-07-08")
        check("rowsample udiff max BL", rs["udiff_dates_dynamic_added"]["max_BL_rows"], 1)
        check("rowsample legacy 2024-07-05 exact", per["LEGACY|2024-07-05"]["selection"], "exact")
        absent = per["UDIFF|2024-07-08"].get("classes_absent_full_file", [])
        check("rowsample absent classes recorded", all(k in absent for k in ("MF", "GB", "GS", "TB", "BO")), True)
        check("rowsample ETF hint found", "SYMBOL_ETF_hint" in per["UDIFF|2024-07-08"]["full_file_coverage"], True)
        check("rowsample TradDt!=BizDt covered", "TRADDT_NE_BIZDT" in per["UDIFF|2024-07-08"]["full_file_coverage"], True)

        # legacy census on L1
        lc = {r["file"]: r for r in read_csv(os.path.join(a1, "FIX-LEG-CENSUS-01__per_file.csv"))}
        check("legcensus L1 blanks", int(lc["cm01JAN2019bhav.csv.zip"]["blank_isin_rows"]), 2)
        # RE-prefix counter is deliberately broad (RELIANCE matches startswith RE);
        # the dash/exact counters are the rights-entitlement evidence signals:
        check("legcensus L1 RE prefix rows (broad)", int(lc["cm01JAN2019bhav.csv.zip"]["rows_symbol_RE_prefix"]), 4)
        check("legcensus L1 RE-dash rows", int(lc["cm01JAN2019bhav.csv.zip"]["rows_symbol_RE_dash_or_space"]), 1)
        check("legcensus L1 exact RE rows", int(lc["cm01JAN2019bhav.csv.zip"]["rows_symbol_EXACT_RE"]), 0)
        check("legcensus L1 pair dups", int(lc["cm01JAN2019bhav.csv.zip"]["symbol_series_duplicate_rows"]), 2)
        check("legcensus L1 invalid isins", int(lc["cm01JAN2019bhav.csv.zip"]["invalid_isin_rows"]), 0)

        # sample file emitted & bounded
        sf = os.path.join(a1, "FIX-UD-ROW-SAMPLE-01__sample_udiff_2024-07-08.csv")
        lines = open(sf).read().splitlines()
        check("rowsample file header verbatim", lines[0].split(",")[:9], UDIFF_COLS[:9])
        check("rowsample bounded <=2000", len(lines) - 1 <= 2000, True)

        print()
        if FAILURES:
            print("SELFTEST FAILURES: %d" % len(FAILURES))
            for f in FAILURES:
                print("  -", f)
            return 1
        print("SELFTEST: ALL CHECKS PASSED (synthetic data; no corpus involved)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(run_tests())
