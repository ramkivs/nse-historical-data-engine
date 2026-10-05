# D02 — Historical Equity Eligibility & Identity Investigation Record

Gate: D02 (read-only investigation)
Record revision: **Rev 2 — pre-merge correction pass (2026-10-05)**, implementing review items C1–C9
(precision/wording corrections only: UDiFF field count, ISIN-candidate language, overlay-ISIN wording,
fixture status classification, series-state phrasing, ST characterization, fixture date boundaries,
2022-10-03 neutrality, `security_id` proposal status). No findings, fixtures, boundaries, or open
questions were otherwise altered; see §13 revision log.
Date: 2026-10-05
Baseline: `origin/main` @ `410135d` ("Establish NSE 10Y archive evidence baseline", D01)
Environment: ARENA (no access to Windows raw archive directories)

## 0. Scope, method, and authority boundary

### 0.1 What this investigation is

D02 is a **read-only investigation** of equity eligibility, the series universe, and security-identity
semantics across the Legacy and CM-UDiFF NSE archives, as observable from the D01 evidence committed in
this repository, supplemented by public NSE documentation for *code semantics only*.

No raw archive was accessed, modified, or transformed from this environment. No ingestion, persistence,
schema, or engine code was created or modified. Nothing in this document is an implementation decision.

### 0.2 Evidence base

| Layer | Source | Status |
|---|---|---|
| E1 — D01 inventory evidence | `evidence/inventory/` (file_inventory.json: per-file header, row_count, date_values, per-series row counts, distinct-symbol count, distinct/ISIN count; series_totals; schema_variants) | Committed, authoritative |
| E2 — D02 derived aggregates | `evidence/identity/d02_*` produced read-only by `evidence/identity/d02_derivation.py` from E1 | Committed with this record, reproducible |
| E3 — Public NSE documentation | NSE "Legend of series" page (updated 2024-09-19); NSE/NCL T+0 settlement FAQs | External reference used only to interpret codes; not archive evidence |

Provenance gap (FACT): the D01 inventory *script* was never committed to this repository, and the
documented semantics of its `isin_count` / `symbol_count` fields are not defined anywhere in the repo.
Their meaning must be pinned down before they are relied on (see D02-Q1).

### 0.3 Claim tags

- **[FACT]** — directly supported by E1/E2 repository evidence (or, where marked EXT, by public NSE documentation).
- **[FINDING]** — derived by analysis in this investigation; supportable but interpretive.
- **[HYPOTHESIS]** — plausible, NOT proven; must not be encoded as a rule.
- **[OPEN QUESTION]** — unresolved; blocks any governed decision it touches.
- **[RECOMMENDATION — PROPOSAL PENDING APPROVAL]** — proposed direction; carries zero implementation authority under this gate.

### 0.4 Authority boundary (restated, binding)

This gate grants investigation authority only. It does **not** grant: implementation, production
ingestion, durable persistence, schema finalization, security-master ownership, external data-provider
selection, or corporate-action adjustment authority. Every rule-like statement below is a proposal
pending a later gate.

---

## 1. Corpus shape (context for all sections)

- **[FACT D02-F1]** The corpus is 2,462 single-date archives — Legacy `cm{DDMONYYYY}bhav.csv.zip`
  (1,919 files, 2016-09-20→2024-07-05) and UDiFF `BhavCopy_NSE_CM_0_0_0_{YYYYMMDD}_F_0000.csv.zip`
  (543 files, 2024-07-08→2026-09-18) — with 0 duplicate dates, 0 duplicate checksums, 0 parse errors,
  and 5,689,949 total data rows (Legacy 3,989,299; UDiFF 1,700,650). Filename patterns are 100%
  standard (E2): zero non-standard filenames in either corpus.
- **[FACT D02-F2]** Three schema variants exist: (a) 1,917 Legacy files with header
  `SYMBOL|SERIES|OPEN|HIGH|LOW|CLOSE|LAST|PREVCLOSE|TOTTRDQTY|TOTTRDVAL|TIMESTAMP|TOTALTRADES|ISIN|`
  (13 fields + trailing empty field); (b) 2 Legacy files *without* the trailing empty field
  (`cm10JUL2017bhav.csv.zip`, `cm13JUL2020bhav.csv.zip`); (c) all 543 UDiFF files with the single
  34-field header `TradDt|BizDt|Sgmt|Src|FinInstrmTp|FinInstrmId|ISIN|TckrSymb|SctySrs|XpryDt|
  FininstrmActlXpryDt|StrkPric|OptnTp|FinInstrmNm|OpnPric|HghPric|LwPric|ClsPric|LastPric|PrvsClsgPric|
  UndrlygPric|SttlmPric|OpnIntrst|ChngInOpnIntrst|TtlTradgVol|TtlTrfVal|TtlNbOfTxsExctd|SsnId|
  NewBrdLotQty|Rmks|Rsvd1|Rsvd2|Rsvd3|Rsvd4`.
  The two header-variant Legacy files are *field-identical* to the dominant Legacy schema; only the
  trailing delimiter differs. `cm13JUL2020bhav.csv.zip` additionally carries 2-digit-year date values
  (`13-Jul-20`) while all other Legacy files use `DD-MON-YYYY` and all UDiFF files use ISO `YYYY-MM-DD`.
- **[FACT D02-F3]** In every one of the 2,462 files, the sum of per-series row counts equals `row_count`,
  and every series token is exactly 2 characters. Therefore, in this corpus, **no row lacks a
  SERIES/SctySrs value** and no other instrument-classification column (e.g. UDiFF `Sgmt`, `Src`,
  `FinInstrmTp`) produced an unclassified leftover that the inventory surfaced.
- **[FACT D02-F4]** Coverage contains no weekend files; internal date values are single-valued per file
  and match the filename date for all 2,462 files (E2); 147 weekday dates within the span have no file
  (`evidence/identity/d02_missing_weekdays.txt`). Reconciliation of that list against the official NSE
  trading-holiday calendar has not been performed (fixture FIX-CAL-01); a missing date being a holiday
  is an assumption, not evidence.

---

## 2. Section A — Equity eligibility

### 2.1 What the raw records actually expose

- **[FACT D02-F5]** The Legacy record provides exactly these identity-adjacent fields: `SYMBOL`,
  `SERIES`, `TIMESTAMP`, `ISIN`. It has **no** segment field, **no** instrument-type field, **no**
  business-date vs trade-date distinction, **no** security name, **no** expiry/strike/option-type.
- **[FACT D02-F6]** The UDiFF record adds, per row: `Sgmt`, `Src`, `FinInstrmTp`, `FinInstrmId`,
  `TckrSymb` (vs `SYMBOL`), `SctySrs` (vs `SERIES`), `FinInstrmNm`, `BizDt` (vs `TradDt`), plus option/
  debt fields and `Rmks`/`SsnId`/`Rsvd1..4`. The D01 evidence captured UDiFF **headers only** — none of
  the per-row values of `Sgmt`, `Src`, `FinInstrmTp`, `FinInstrmId`, `Rmks` were collected. The
  eligibility-relevant value domains of the two most important UDiFF discriminators (`FinInstrmTp`,
  `Sgmt`) are therefore **unknown from repository evidence**.

### 2.2 What SERIES/SctySrs can and cannot decide

- **[FACT D02-F7 — EXT]** Per the NSE Legend of series (E3): `EQ` covers "fully paid equity shares **and
  ETFs**" (mainboard); `BE`/`BZ` are the trade-for-trade variants of that same class; `SM` is SME equity,
  `ST`/`SZ` its T2T variants; `E@`/`X@` partly-paid equity; `BE` is *additionally* the series used for
  Rights Entitlements; `BL` = block-deal sub-segment rows; `BO` = buyback-via-exchange; `P@/Q@`
  preference shares; `N@/Y@/Z@/A@/B@/U@/M@` non-convertible debt; `D@/S@` convertible debt; `W@/K@`
  warrants; `MF/ME` close-ended mutual-fund units; `GB` gold bonds; `GS`/`TB`/`SG` government
  securities/treasury bills/SDLs; `IV/ID` InvIT; `RR/RT` REITs.
- **[FINDING D02-D1]** `SERIES == "EQ"` therefore conflates at least two analytically different instrument
  classes (company equities vs ETF fund units), and `BE` conflates surveilled equities with rights
  entitlements. **`SERIES == EQ` is not a sufficient equity predicate**, and no single series value is a
  pure "equity" predicate on its own. This confirms and extends the D01 conclusion.
- **[FINDING D02-D2]** The corpus is not even "mostly equities" by row share once the full series
  vocabulary is applied (E2 rollup `d02_series_class_rollup.csv`): EQ = 75.09% of all 5.69M rows;
  equity-common+SME+T2T+partly-paid ≈ 90.7%; non-equity debt/govt/fund/REIT/InvIT/gold-bond rows ≈ 9%;
  overlay rows (BL/T0/BO/IT-IL) ≈ 0.06% but concentrated — BL spikes to 313 rows in one file
  (2022-10-03; the spike's market cause is not investigated here).
- **[FINDING D02-D3]** A governed equity eligibility rule must be a **combination** of fields, and the
  minimum defensible combination differs by source format:
  - UDiFF-era: candidate basis = `SctySrs ∈ {EQ, BE, BZ} ∪ {SM, ST, SZ}` (mainboard + SME) **and**
    `FinInstrmTp` (value domain unknown → FIX-UD-CENSUS-01) to separate equity shares from ETFs, **and**
    a rights-entitlement test (row-level evidence suggests `BE` alone is insufficient; NSE convention is
    an `RE…` symbol prefix — unverified here → FIX-LEG-CENSUS-01), with `BL`/`BO`/`IT`/`IL`/`T0` overlay
    series excluded from *security* counting but retained as *observations* of the same security (§5).
  - Legacy-era: only `SERIES` + `SYMBOL` + `ISIN` exist (D02-F5), so ETF-vs-equity and rights-vs-T2T
    separation is **not computable from Legacy rows alone** at aggregate level; it requires an external
    or side-file input (ETF security list / security master; see §7). Any Legacy-only eligibility rule
    that omits this is a documented approximation, not a truth.
- **[HYPOTHESIS D02-H1]** Third-party ingestion practice for UDiFF CM bhavcopy filters on
  `Sgmt`/`Src` ("CM"/"NSE") and `FinInstrmTp = STK` and keeps series EQ>BE>BZ — if the `STK` type also
  covers ETF units (as the label suggests and the legend implies the file's scope does), even
  `FinInstrmTp`+`SctySrs` will not fully isolate company equities, and an ETF list remains necessary.
  Unproven from repository evidence; blocked on FIX-UD-CENSUS-01.
- **[RECOMMENDATION D02-R1 — PROPOSAL PENDING APPROVAL]** Govern eligibility as a versioned, dated
  classification table (series code → class, with effective intervals and evidence citation), reviewed
  whenever a previously-unseen code appears, instead of hard-coded constants. Unknown-code policy:
  fail-closed to a quarantine partition; never silently default to "not equity" or "equity".

### 2.3 ISIN presence/absence

- **[FACT D02-F8]** In the D01 per-file metrics, `isin_count` ≤ `row_count` in all 2,462 files
  (0 files with excess). 1,078 files have `isin_count` strictly below `row_count`.
- **[FINDING D02-D4]** The deficit `row_count − isin_count` tracks overlay rows almost exactly:
  `deficit == rows(BL) + rows(T0)` holds for **2,159/2,462 files (87.7%)**, including **541/543 (99.6%)**
  UDiFF files; the 300 files with residual +1/+2 are all Legacy files from 2016–2018, and 3 files sit at
  −1 (see `d02_metrics.json`). Whatever `isin_count` means (Q1), the *only* rows whose aggregate ISIN
  behavior differs from ordinary security rows are block-deal and T+0 rows. Two interpretations remain
  compatible with the data: (a) BL/T0 rows repeat the base security's ISIN (duplicate distinct values),
  or (b) BL/T0 rows carry empty ISIN values. **The current aggregate evidence cannot determine whether
  BL/T0 rows repeat the base ISIN or carry blank ISIN values; same-day ISIN duplication across
  base/overlay rows therefore remains unproven** (resolved only by FIX-SEM-DEF-01 + row-level blanks/
  duplicates census FIX-LEG-CENSUS-01 / FIX-UD-CENSUS-01). What both readings do support is
  **[FINDING D02-D5]**: **ISIN is populated on essentially all security rows of both formats** — a
  strong continuity asset — but it is *not demonstrated* to be a unique per-date key, and rights/other
  edge cases remain to be seen.
- **[OPEN QUESTION D02-Q1]** Definition of D01's `isin_count`/`symbol_count` (distinct-non-blank vs
  non-blank row count vs other) — the generating script is not in the repository and this is not
  recoverable from the artifacts. Resolvable cheaply: fixture FIX-SEM-DEF-01 (or a one-line answer from
  the D01 script author) plus FIX-LEG-CENSUS-01 / FIX-UD-CENSUS-01 counts of literal blanks.
- **[OPEN QUESTION D02-Q2]** Are the `ISIN` *values* structurally valid (12 chars, `IN…`, check digit)
  across both eras? Header evidence says the column exists; nothing in-repo says the values are clean.
  FIX-LEG-CENSUS-01 answers this.

---

## 3. Section B — Series universe (all 172 observed codes)

Full per-code profile with provisional class, lifecycle dates and counts:
**`evidence/identity/d02_series_universe.csv`** (172 rows, committed, derived deterministically by
`d02_derivation.py`). Rollup: **`evidence/identity/d02_series_class_rollup.csv`**.

Summary of the provisional classification (classes are *proposals*, not rules):

| Provisional class | Codes | Rows | Share |
|---|---:|---:|---:|
| EQUITY_COMMON (EQ — includes ETFs per legend) | 1 | 4,272,478 | 75.09% |
| EQUITY_T2T_RIGHTS_AMBIGUOUS (BE) | 1 | 428,831 | 7.54% |
| EQUITY_SME (SM) | 1 | 322,583 | 5.67% |
| EQUITY_SME_T2T (ST, SZ) | 2 | 65,741 | 1.16% |
| EQUITY_T2T (BZ) | 1 | 64,813 | 1.14% |
| EQUITY_PARTLYPAID (E1–E3) / T2T (X1, X2) | 3+2 | 8,534 | 0.15% |
| OVERLAY: block deals (BL), buyback (BO), T+0 (T0), institutional windows IT/IL (hypothesis) | 5 | 3,692 | 0.06% |
| EQUITY-LINKED but not common equity: P@/Q@ preferred (P1,P2,Q1,Q2), W@ warrants (W1–W3) | 7 | 6,809 | 0.12% |
| NON-EQUITY corporate debt N@/Y@/Z@/A@/B@ + convertible D@/SF | 136 | 343,786 | 6.04% |
| NON-EQUITY govt/gold: GS, TB, SG, GB | 4 | 149,426 | 2.63% |
| NON-EQUITY fund-type: MF, IV/ID (InvIT), RR (REIT) | 4 | 23,234 | 0.41% |
| UNCLASSIFIED: HA, HB, HC, HE, SO (22 rows total) | 5 | 22 | 0.00% |

Universe-structure facts and findings:

- **[FACT D02-F9]** 138 codes appear in **both** formats; 28 Legacy-only codes all end before the
  transition (latest Legacy-only last-sighting 2023-12-27 for BO); 6 UDiFF-only codes (ZM, AK, AO, ZQ,
  SF, ZO) all *start* after 2024-07-08 (ZM from 2024-07-11). The series vocabulary therefore does **not**
  change at the Legacy→UDiFF boundary; new/absent codes reflect ordinary instrument lifecycle (new bond
  issues get new per-issue series letters; retired windows retire their codes).
- **[FACT D02-F10]** Lifecycle events inside the corpus: `T0` first appears 2024-03-28 (14 rows) — the
  optional T+0 settlement pilot — and persists sparsely into the UDiFF era (110 UDiFF days, last
  2026-09-16). `IT` spans 2016-09-20 → 2024-11-14 (dies out *after* the transition, at the start of the
  UDiFF era); `IL` ends 2018-06-27; `BO` exists only 2023-04-13 → 2023-12-27 (112 days, legacy only);
  `MF` persists through the UDiFF era (last 2026-08-25); `IV` first appears 2017-05-18; `GS` from
  2018-12-26; `TB` from 2021-06-16; `SG` from 2020-11-18; `RR` from 2019-04-01.
- **[FINDING D02-D6]** Several observed codes pre-date or contradict the current legend's stated meaning
  (IV before NSE InvIT listings; SO excluded from the legend's own S@ pattern; HA/HB/HC/HE absent from
  the legend entirely). The legend is a *current* document (updated 2024-09-19) and cannot be assumed
  complete for 2016-era practice. Classification must carry a "meaning-by-era" caveat until per-era
  circulars are checked (FIX-CIRC-01).
- **[FINDING D02-D7]** `ST` exhibits a distribution discontinuity at the transition with no vocabulary
  change: 16.9 rows/day average over the last 250 Legacy files vs **124.7 rows/day** over the first 250
  UDiFF files (E2: `d02_series_distribution_shift.csv`), while `SM` moves 197→242. Either SME T2T
  placement genuinely jumped around mid-2024, or the *usage* of `ST` differs between formats. What the
  evidence establishes is a **distribution discontinuity / semantic-interpretation anomaly** at the
  boundary — not a proven semantic break; it cautions against assuming format-independent code
  semantics but does not by itself overturn them. Blocked on FIX-UD-CENSUS-01 + FIX-SERIES-EVENTS-01.
- **[RECOMMENDATION D02-R2 — PROPOSAL PENDING APPROVAL]** Publish `d02_series_universe.csv` as the seed
  of the governed classification table (D02-R1), with each row's `provisional_class` explicitly
  `approval=pending`, `evidence=<legend|corpus-observation|hypothesis>`.

---

## 4. Section C — Identity semantics of candidate fields

Mapping of observed fields to identity roles, per the two schemas (F5, F6) and E2 aggregates:

1. **Durable security identity (candidate — unproven)** — ISIN is currently the **strongest cross-format
   durable-identity candidate** identified by the available evidence: it is the only identity-like field
   present in **both** schemas (F5, F6) and, under either reading of the D01 metric, populated on
   essentially every security row (D02-D5). **Durability, validity, uniqueness, and continuity remain
   unproven pending D03 fixtures**: value validity (D02-Q2, FIX-LEG-CENSUS-01), row-level uniqueness/
   overlay behavior and `isin_count` semantics (D02-Q1, FIX-SEM-DEF-01, FIX-UD-CENSUS-01), and
   cross-format/key-semantics questions — whether the *same company's* shares in a changed series get a
   *new* ISIN (series-part-of-ISIN semantics) is not answerable from E1 — D02-Q3, addressed via
   FIX-SYMBOL-HIST-01 / FIX-UD-CENSUS-01 joined against FIX-XCONT-01. (Series migration between two
   ISINs for one company — e.g. shares trading simultaneously in EQ and a BL/T0/other series — is
   exactly why the *analytical security* may need to be (company, instrument-class) with series-scoped
   ISINs as instrument identities. Unresolved design question, not a decision.)
2. **Source-specific instrument identity** — UDiFF `FinInstrmId`: present in header for all 543 files;
   values never captured by D01; its format/namespace/relationship to ISIN is entirely unknown
   **[OPEN QUESTION D02-Q4]** (FIX-UD-CENSUS-01 / FIX-UD-ROW-SAMPLE-01). Legacy has no equivalent ID
   column at all (F5).
3. **Time-varying trading symbol** — Legacy `SYMBOL`, UDiFF `TckrSymb`. **[FINDING D02-D8]** These are
   *not* per-security keys, and the formats treat them differently: in Legacy, rows-minus-distinct-symbols
   averages 124.1/day (min 3, max 433) — the same ticker is reused across many series (issuer-level
   symbol: e.g. one issuer's multiple bond series share its equity ticker); in UDiFF it averages only
   4.8/day and in 33 files equals exactly the BL row count — UDiFF tickers are near-1:1 with
   instruments (per-issue ticker suffixing on the debt side is the likely mechanism, unverified). Any
   join strategy must therefore differ per format; **"join on ticker" is unsafe on Legacy** at least
   without also joining series.
4. **Time-varying series/classification** — `SERIES`/`SctySrs`. **[FINDING D02-D9]** Series should
   currently be treated as a **potentially time-varying dated classification/state**, and must not be
   used as immutable security identity: the file-level signals (deficit = BL+T0, D02-D4; code lifecycles,
   D02-F10) are *consistent with* per-date regime states (surveillance T2T, T+0 parallel series, rights
   via BE, buyback windows), but **individual security transitions (e.g. EQ↔BE moves) have not been
   proven from D01 aggregates** — row-level per-security histories are absent from E1. FIX-SERIES-EVENTS-01
   is the evidence that would confirm or refute per-security series-transition behavior.
5. **Market-segment identity** — UDiFF `Sgmt` (+`Src`): header-present, values unknown (Q4). **[FACT
   D02-F11]** Legacy has NO segment field; the Legacy filename's `cm` prefix and the corpus itself are
   the only segment evidence. **[OPEN QUESTION D02-Q5]** whether UDiFF `Sgmt` values distinguish
   mainboard/SME/RDMS/block-deal *at row level* — the answer would make `Sgmt` a first-class eligibility
   discriminator. FIX-UD-CENSUS-01.

- **[FINDING D02-D10]** The `BhavCopy_NSE_CM_0_0_0_..._F_0000` filename tokens are constant across all
  543 files (E2), so the filename carries no per-row segment information beyond "CM / final file".
- **[Anomalies in this section (FACT D02-F12)]** one file has BL rows yet zero ISIN deficit
  (`cm22FEB2019bhav.csv.zip`, 2019-02-22, 1 BL row — see `d02_anomalies.json`); 3 files show deficit below
  BL+T0 by 1; the 2016–2018 +1/+2 residual cohort (300 files) has no explanation from field semantics
  alone (candidate causes: badla-era overlay remnants, blank-ISIN corporate-bond rows, or
  inventory-counting edge cases — all unverified).

---

## 5. Section D — Cross-format identity continuity (Legacy → UDiFF)

- **[FACT D02-F13]** Boundary day comparison (`evidence/identity/d02_transition_20240705_vs_20240708.csv`):
  last Legacy file 2024-07-05: 2,775 rows, EQ 1,906, `isin_count == row_count` (2,775); first UDiFF
  file 2024-07-08: 2,815 rows, EQ 1,909, deficit 1 (= its single BL row). 53 series codes appear on
  both sides of the boundary; day-specific bond-series entries differ only by ordinary daily activity
  (12 vs 15 codes present per side among sparse-lifecycle debt codes).
- **[FINDING D02-D14]** At every level observable *without raw rows* — file cadence, schema-per-format
  stability, series vocabulary (F9), EQ scale (±0.2% of rows), ISIN density (D5), overlay behavior
  (D4) — the two formats describe the **same underlying instrument universe** with different column
  names, and the transition shows no re-keying shock. Aggregate evidence is consistent with, but cannot
  *prove*, record-level continuity.
- **[FINDING D02-D15]** Candidate continuity paths, ranked by current support:
  1. **ISIN join** — the only field present-and-populated on both sides (F5, D02-D5). Continuity rate is
     unmeasured (needs FIX-XCONT-01). Expected failure modes: rows with blank ISIN (D02-Q1 semantics),
     series-change-at-boundary securities, securities delisted/listed over the 1-day trading gap.
  2. **(symbol, series) join** — usable for equity rows (where Legacy symbol is ~1:1 per (symbol,
     series) day-row, D8) but structurally ambiguous for Legacy debt where one ticker maps to many
     series; and case/format normalization rules are unknown (e.g. trailing spaces in legacy symbols are
     a known NSE practice — unverified here).
  3. **FinInstrmId↔(anything in Legacy)** — no candidate link is even formulable today because no Legacy
     column resembles a numeric/alphabetic instrument ID other than ISIN (F5) and Q4 is open.
- **[HYPOTHESIS D02-H2]** Continuity will be dominated by ISIN with small, enumerable exception classes;
  the exception classes (not the rule) will determine the security-master and identity design. To be
  proven or broken by FIX-XCONT-01 before any identity schema is finalized.
- **[DO-NOT-ASSUME]** No claim is made that symbol strings match across formats after normalization
  (spaces/casing); no claim that ETFs or bonds preserve symbols across the transition; no claim that
  `FinInstrmId` is stable for securities that changed ISIN. These are exactly what the fixtures ask.

---

## 6. Section E — Symbol/ticker history vs durable identity

- **[FACT D02-F14]** Legacy `SYMBOL` and UDiFF `TckrSymb` are the only name-like trading identifiers in
  the row schemas; the corpus contains **no** dated symbol-history file of its own (the D01 inventory
  captured per-file distinct counts, not per-security timelines).
- **[FINDING D02-D16]** Within-corpus evidence that trading identifiers move independently of security
  identity: (a) the same-day symbol reuse across series (D8) shows symbol is not even a per-day security
  key in Legacy; (b) code-level regime changes (surveillance T2T, T0 pilot, rights) change a security's
  *series* without changing what it is (D9); (c) per-issue tickers on the UDiFF debt side imply ticker
  is derived per instrument, not per issuer (unverified mechanism — Q6).
- **[OPEN QUESTION D02-Q6]** Do actual *renames* occur (symbol change with constant ISIN), and at what
  rate? Not answerable from E1. FIX-SYMBOL-HIST-01 computes the (ISIN → distinct symbols, intervals)
  ledger over the full corpus; this is the single most decision-relevant un-produced artifact for both
  D02-E and the identity model in D03.
- **[RECOMMENDATION D02-R3 — PROPOSAL PENDING APPROVAL]** Model trading symbol as an **effective-dated
  alias** of the security, never as the identity column: `symbol_interval(security_id, symbol,
  series?, valid_from, valid_to, source_format)`, with corpus rows joining to the interval containing
  their date. Historical "symbol as of date" queries then need no archive re-scan. Same pattern for
  series itself (`series_interval`). Both are proposals; no schema authority is exercised here.

---

## 7. Section F — Company-name lookup limitation (Legacy)

- **[FACT D02-F15]** The Legacy schema (D02-F5) contains no company-name field in any of the 1,919
  files (all three Legacy header variants have the same 13 columns). **A direct historical name→data
  lookup is impossible from Legacy bhavcopy rows alone.** UDiFF rows *do* carry `FinInstrmNm` per row
  (header fact, F6), but that covers 2024-07-08 onward only — and its row-level values, and whether it
  is fully populated, were never captured by D01.
- **[FINDING D02-D17]** The capability required for `company name → security identity → historical
  observations` is therefore a **separate time-sliced security master**, holding at minimum: ISIN,
  symbol (with change intervals), series (with change intervals), instrument class, company name (with
  change intervals), listing/delisting dates. NSE's own documentation references exactly such files —
  the "security master" with Series and Settlement-type fields (E3 T+0 FAQ) — confirming this is the
  exchange's own intended mechanism, not an invention of this investigation.
- **[AUTHORITY-BOUND FINDING D02-F18]** Sourcing, licensing, cadence, and storage of such a master is
  **outside** D02 authority (no external-data-provider selection). What D02 can state: *without* it, the
  engine cannot honestly offer name-based search for the 2016→2024 era; *with* UDiFF-only names it can
  only offer post-transition name resolution, which silently biases historical results toward the new
  era. That asymmetry must be a first-class product decision later, not an implementation accident.
- **[RECOMMENDATION D02-R4 — PROPOSAL PENDING APPROVAL, EXTERNAL ACQUISICATION NOT GRANTED]** Keep the
  security master strictly decoupled from the observation store: the canonical model stores ISIN +
  dated identity refs; name search lives in a separate governed component whose provider (NSE files,
  vendor, or manual curation) is chosen at a later gate with explicit authority.

---

## 8. Section G — Implications for a canonical normalized observation (proposal only — NO schema)

Derived requirements, each traceable to a finding above. **Not a schema. No types, no tables, no DDL.
Explicitly pending a later schema-finalization gate.**

| Canonical element | Required? | Evidence driver | Notes |
|---|---|---|---|
| `trading_date` (=TradDt; Legacy TIMESTAMP parsed date) | yes | F2, D02-F2 date-format drift | must be *derived* per-format, not trusted from filename |
| `business_date` (=BizDt) | yes (UDiFF); Legacy = same as trading date (no BizDt exists — F5), must be marked *assumed* | F5, F6 | TradDt≠BizDt cases: count unknown → FIX-UD-ROW-SAMPLE-01 |
| `security_id` | yes | R3 | **proposed durable internal identity concept; resolution strategy pending D03.** `security_id = ISIN` is NOT assumed or approved; ISIN is currently the strongest candidate input (C2 language, §4.1). Fallback strategy for blank-ISIN/overlay rows is design-pending (Q1/Q3) |
| `isin` (nullable, source-verbatim + normalized) | yes | F5, F8 | keep raw string AND validity flag (Q2) |
| `symbol_as_of_date` (alias ref, not identity) | yes | D8, R3 | |
| `series_at_date` (=SERIES/SctySrs, verbatim) | yes | D9, F9 | drives eligibility class via governed table (R1), never hard-coded |
| `eligibility_class` (equity / equity-variant / non-equity / overlay / unknown-quarantine) | yes — *derived at query/normalization time* | D1–D3 | per-row materialization would freeze unapproved rules; keep derived (proposal) |
| `segment_ref` | UDiFF only (Sgmt/Src values); Legacy fixed "NSE CM, no field" (F11) | Q5 | |
| `instrument_type_ref` | UDiFF `FinInstrmTp`; Legacy **unknown per-row** — class must come from series + security-master approximation (D3) | F5, F6, H1 | this asymmetry must be preserved as provenance, not hidden |
| `ohlc` (open/high/low/close) | yes | schemas | field names per format known (F2/F6); Legacy has no settle price — fine |
| `last_price`, `prev_close` | yes | schemas | |
| `traded_quantity`, `traded_value` | yes | schemas | unit normalization (e.g. TOTTRDVAL lakhs vs TtlTrfVal rupees) unresolved in this corpus (Q7) |
| `trade_count` | yes | schemas | |
| `overlay_flag + overlay_basis` (BL/T0/BO/IT/IL row marker; which base row it overlays) | yes | D4 | without it, same-day EQ + T0 + BL rows look like duplicates (D5) and volume attribution is wrong (Q8) |
| `source_format` (LEGACY\|UDIFF) + `source_file` (exact archive name) + `source_file_sha256` + `row_offset` | yes | F1; D01 already stores sha256 per file | full reversibility to raw bytes is cheap here because D01 preserved checksums |
| `raw_row_hash` | yes | parser-drift anomalies (F2) | two header variants and a 2-digit-year date file prove the corpus is not byte-uniform; reprocessing must be detectable |

- **[OPEN QUESTION D02-Q7]** Price/volume units and null conventions (e.g. `0.00` vs blank for
  suspended rows) — not captured by D01 at all.
- **[OPEN QUESTION D02-Q8]** Whether base EQ-row volume already *includes* block-deal / T0 volume for
  the same security-date (double-count risk if overlay rows are added; silent undercount if they are
  dropped). Cannot be answered from aggregates — FIX-OVERLAY-SEM-01.

---

## 9. Section H — Minimum Windows-side fixtures required to close D02 questions

Twelve fixtures are requested (12 IDs below; status classification after the table). Each fixture is,
unless its row states a different source, generated on the Windows environment by read-only scan of the
existing archives into the repository (controlled extracts only; no production ingestion).
`D01-insufficient` explains why this cannot already be answered from committed evidence. These are
**requests for evidence**, not implementation work.

| ID | Purpose | Source | Required fields/aggregates | Question answered | Why D01 evidence is insufficient |
|---|---|---|---|---|---|
| **FIX-SEM-DEF-01** | Pin down `isin_count`/`symbol_count` semantics in the D01 inventory | D01 script (not in repo) or re-emit one file both ways | For 5 sampled files: row count, distinct-ISIN, non-blank-ISIN, distinct-symbol, non-blank-symbol | Q1 | Script absent; metrics underdetermined (both readings fit D02-D4) |
| **FIX-UD-CENSUS-01** | UDiFF identity & eligibility census | all 543 UDiFF archives, row-level scan | Per file, grouped by `(Sgmt, Src, FinInstrmTp, SctySrs)`: row count, blank-ISIN count, blank-FinInstrmId count, `FinInstrmId==ISIN` count, distinct ISIN/symbol | A (governed combination), C2/C5, Q4, Q5, D2-D7 (ST shift census), D02-Q3 partial | D01 captured headers only; zero per-row values for the decisive columns |
| **FIX-UD-ROW-SAMPLE-01** | Ground-truth rows for semantics of special fields, **stratified across both formats** | Dates spanning Legacy and UDiFF: UDiFF — 2024-07-08 (first day), 2025-10-30 (max T0/SF activity), 2026-08-25 (last MF day); Legacy — 2024-03-28 (first/max T0 sighting in corpus, Legacy-era) and 2022-10-03 (max BL spike). Sampling across the format boundary is intentional: the T0 pilot began in the Legacy era, so Legacy T+0 activity and UDiFF-era special-series activity must be compared on equal footing | All fields verbatim (UDiFF: 34 columns; Legacy: 13 fields + trailing empty field), ≤2,000 rows per date, guaranteed inclusion of: ETF tickers (e.g. NIFTYBEES, GOLDBEES), RE-prefixed rows, BL/T0/BO/IT rows, MF/GB/GS/TB rows, any TradDt≠BizDt rows | H1; F18 (FinInstrmNm population); Q7; BizDt semantics; C7 date-boundary evidence | Aggregates cannot show values; sampling design depends on this |
| **FIX-LEG-CENSUS-01** | Legacy identity census | all 1,919 Legacy archives, row-level scan | Per file: rows; rows with blank/whitespace ISIN; ISIN regex violations (`^IN[A-Z0-9]{9}[0-9]$` after trim); `RE`-prefix symbol count per series; ETF-list membership count within EQ (against eq_etfseclist — see FIX-SECMASTER-01); (symbol,series) duplicate count; per-date series counts (already in D01 — keep as cross-check) | A (Legacy-era limits, D3), Q2, D02-D4 alternative readings, rights-issue identification | D01 stored only distinct counts and series totals; value validity and ETF/rights membership never extracted |
| **FIX-XCONT-01** | Cross-format continuity measurement | Legacy 2024-07-05 (and 2024-06-24→07-05 week) vs UDiFF 2024-07-08 (and week) | ISIN join: matched count; legacy-only list; udiff-only list; matched rows with differing (trimmed, uppercased) symbol; per-series breakdown of each class | D (continuity); sizes H2; determines whether ISIN-first identity holds at the boundary | D01 has file-level vectors only (F13); join needs row keys |
| **FIX-SYMBOL-HIST-01** | Rename ledger (time-varying symbol vs durable identity) | all 2,462 files, grouped by ISIN (both formats) | Per ISIN: distinct symbols with first/last date and day-count each; series intervals likewise; output only rows with ≥2 symbols or ≥2 series + summary counts | E; D16; validates R3 alias model | Requires per-row (ISIN, symbol, date) tuples never extracted |
| **FIX-SERIES-EVENTS-01** | Series-transition event census | as above grouped by ISIN | counts of transitions EQ↔BE↔BZ↔SM/ST/SZ↔T0/other with date histogram; include ST census across both eras (explains D7?) | C4 (state-at-date), D7 | Same reason; aggregate files cannot trace one security across days |
| **FIX-OVERLAY-SEM-01** | Overlay row semantics (volume/price vs base row) | 30 dates across both formats (15 Legacy incl. 2022-10-03 and 2024-03-28; 15 UDiFF incl. 2024-07-08 and 2025-10-30) | For every BL/T0/BO/IT/IL row: its OHLCV vs the same-ISIN base row(s) same day; count of overlay rows whose base row is absent | Q8; canonical `overlay_flag` design (G) | Whether overlays duplicate volume is invisible in counts |
| **FIX-CAL-01** | Calendar reconciliation | NSE official holiday calendars 2016–2026 (published) + `evidence/identity/d02_missing_weekdays.txt` | Mark each of the 147 missing weekday-dates: holiday / other; and flag any file-date that falls on a published full-market holiday | F4; durability of business-date model | D01 recorded existence only; no calendar evidence in repo |
| **FIX-ANOM-01** | Schema-anomaly raw inspection | `cm10JUL2017bhav.csv.zip`, `cm13JUL2020bhav.csv.zip` + neighbors | full header, first/last 10 raw rows, count of 2-digit-year TIMESTAMP rows, line-ending/encoding info, plus re-check vs NSE-published copies (size+sha) if obtainable | parser robustness policy for provenance (G `raw_row_hash`) | D01 captured header signature + date map but not raw structure |
| **FIX-CIRC-01** | Meaning-by-era of unmapped/contradictory codes (IT, IL, SO, HA–HE, T0, IV-pre-2019, ST-usage change) | NSE circular archive (document search, not data) | citations + effective dates for each code | B (UNCLASSIFIED bucket), D6, D7 | Legend is single point-in-time (2024); corpus spans 10 years |
| **FIX-SECMASTER-01** *(authorization-gated)* | Security-master capability scoping for name lookup | **Not from local archives**: NSE public security-master / `eq_etfseclist` snapshots for the FIX-UD-ROW-SAMPLE-01 sample dates (both eras, minimum one Legacy-era and one UDiFF-era) (field inventory + ≤500-row samples + schema doc, stored as evidence not as data product) | isin, symbol, series, company name, settlement type, listing/delisting, status; snapshot dates | F (name→identity→observations chain); ETF membership for Legacy eligibility (D3) | Entirely absent from corpus by design (F15); **acquisition/ownership requires explicit separate authorization — not requested as a file fixture, offered as a scoping sample only if approved** |

Fixture status classification (12 total, internally consistent):

* **Directly executable Windows archive scans (8):** FIX-UD-CENSUS-01, FIX-UD-ROW-SAMPLE-01,
  FIX-LEG-CENSUS-01, FIX-XCONT-01, FIX-SYMBOL-HIST-01, FIX-SERIES-EVENTS-01, FIX-OVERLAY-SEM-01,
  FIX-ANOM-01.
* **Directly executable published-evidence tasks (2):** FIX-CAL-01 (official holiday calendars vs the
  committed missing-weekday list) and FIX-CIRC-01 (NSE circular research) — no raw-archive access needed;
  document evidence only.
* **Provenance / semantic reconstruction (1):** FIX-SEM-DEF-01 — resolves the meaning of D01's
  `isin_count`/`symbol_count`; requires the (uncommitted) D01 inventory script or a minimal re-emission,
  not a corpus scan.
* **Authorization-gated (1):** FIX-SECMASTER-01 — scoping sample for the security-master capability;
  acquisition/ownership is **not granted by D02** and must be approved separately before any collection.

Fixture budget note: every row-level scan above is one pass over files Windows already holds; each
produces aggregates or bounded samples — no corpus copies enter the repository.

---

## 10. Anomaly register (un-reconciled, on record)

1. **[FACT]** Two Legacy files without the 13th-pipe header (`2017-07-10`, `2020-07-13`); the latter is
   also the single file with `DD-Mon-YY` dates and an inflated BE count (267 vs 245 neighbors) —
   FIX-ANOM-01. Not silently normalized.
2. **[FACT]** One Legacy file with BL rows but zero ISIN deficit (see `d02_anomalies.json`) — counter-case
   to D02-D4; FIX-SEM-DEF-01 will classify it.
3. **[FACT]** 3 files where deficit = BL+T0−1; 300 Legacy files 2016–2018 with deficit = BL+T0+1/+2
   (cohort; no cause determinable from aggregates).
4. **[FACT]** `ST` rows/day discontinuity at the transition (≈16.9 → 124.7, ≈7.4×) with stable
   vocabulary (D02-D7) — observed distribution change; cause (regime usage vs. semantic re-purposing vs.
   SME growth mix) unresolved.
5. **[FACT]** `IT` survives the transition by 4 months then vanishes (2024-11-14); `BO` vanished
   2023-12-27 mid-Legacy. Window/overlay lifecycles are not synchronized with format change.
6. **[FACT]** 2022-10-03 requires reconciliation against the official NSE trading calendar
   (FIX-CAL-01). Observed archive facts only: a 2,616-row file for that date exists, containing 1,813
   EQ rows **plus** 313 BL rows, with internal TIMESTAMP values of `03-OCT-2022`. Whether the date was
   a trading day, a holiday, or a misdated/misattributed file is **not decided in this record**; D02
   notes only that no calendar reconciliation evidence exists in the repository yet.
7. **[FACT]** 2020-07-13 is the NSE/BSE market-freeze glitch date; its archive differs in *two* ways
   (header + date format) — coincidence or recovery artifact; unproven.

## 11. Unresolved contradictions (explicitly NOT reconciled)

- The NSE legend maps `ST/SZ` to SME T2T, while its own footnote says `BE/ST` was historically used for
  surveillance T2T equities; the corpus shows ST behaving like a mainboard-scale series in the UDiFF era
  (D7). Both statements are current public facts; the data says neither cleanly. Left open.
- `IV` in-corpus life (from 2017-05-18) predates the legend's InvIT-era meaning (D6). Left open pending
  FIX-CIRC-01.
- D02-D4's deficit relation is compatible with **two different identity regimes**. If `isin_count`
  counts distinct non-blank ISINs (reading (a)), then all non-overlay rows carry present ISINs that are
  pairwise distinct within each file, and BL/T0 rows either duplicate a base-security ISIN or are blank —
  indistinguishable from each other in this evidence. If `isin_count` counts non-blank rows
  (reading (b)), the data shows only that BL/T0 rows are the blank ones; non-overlay ISIN *duplication*
  within a day could then exist without surfacing. The readings have opposite implications for ISIN
  uniqueness (D02-Q3), and the aggregate evidence cannot separate them. Left open deliberately;
  FIX-SEM-DEF-01 plus the census fixtures resolve it.

## 12. Disposition — D03 readiness

- **D02 conclusions (investigation):** equity eligibility *cannot* be a single-field predicate
  (D02-D1/D3); the series universe is now mapped, provisionally classified, and lifecycle-profiled
  (§3); the available evidence supports a working role separation — strongest-durable-identity-candidate
  (ISIN; durability/validity/uniqueness/continuity unproven pending D03), source-specific identifier
  (FinInstrmId — opaque), time-varying alias (symbol), potentially time-varying dated
  classification/state (series) — as a *proposal for D03 to test*, not a decision (§4); cross-format
  continuity is *aggregate-supported* via ISIN but unproven at record level (§5); Legacy has no name
  path and will likely need a governed security master (§7); the canonical observation must carry
  dates-as-derived, overlay flags, and full provenance (§8).
- **D02 is NOT a green light for D03 as an implementation gate.** It is a green light for **D03 as a
  fixtures-and-decisions gate**: the twelve FIX-* requests in §9 — **10 directly executable** (8 read-only
  Windows archive scans + 2 published-evidence tasks), **1 provenance/semantic reconstruction**
  (FIX-SEM-DEF-01, needing the D01 script or a minimal re-emission rather than a corpus scan), and
  **1 authorization-gated** security-master scoping sample (FIX-SECMASTER-01) — resolve, or deliberately
  freeze as accepted limitations, the Q1–Q8 open questions. Eligibility classification may be
  **provisionally approved** at that point (it is already complete for 167/172 codes); the 5
  UNCLASSIFIED codes, the ST distribution discontinuity / semantic-interpretation anomaly, and the IT
  lifecycle question must have dispositions; D02-D4's two readings must be resolved before any identity
  fallback rule is written.
- If Windows fixtures cannot be produced, the fallback path is an explicitly-documented
  approximation ("Legacy-era equity universe = series-EQ superset including ETFs") — which this
  investigation recommends **against** accepting silently.

## 13. Revision log

**Rev 2 — pre-merge correction pass** (corrections only; no new conclusions, no removal of findings):

| Item | Disposition |
|---|---|
| C1 | UDiFF header corrected to **34 fields**, verified against committed D01 `file_inventory.json` (`headers` length and `header_signature` split both = 34 for all 543 files). Record §1 (F2) and §9 (FIX-UD-ROW-SAMPLE-01) updated; fixture columns restated per format (UDiFF 34; Legacy 13 + trailing empty). |
| C2 | §4.1 rewritten: ISIN framed as **currently strongest cross-format durable-identity candidate**, durability/validity/uniqueness/continuity explicitly unproven; linked to D02-Q1, D02-Q2, D02-Q3, FIX-XCONT-01, FIX-LEG-CENSUS-01, FIX-UD-CENSUS-01. §12 conclusion aligned. Finding that ISIN is the strongest candidate preserved. |
| C3 | D02-D4/D5 and §11 rewritten: aggregate evidence **cannot distinguish** base-ISIN repetition from blank-ISIN on BL/T0 rows; same-day base/overlay ISIN duplication stated as **unproven**. |
| C4 | §9/§12 fixture classification made explicit: **10 directly executable** (8 Windows read-only scans + 2 published-evidence tasks: FIX-CAL-01, FIX-CIRC-01), **1 provenance/semantic reconstruction** (FIX-SEM-DEF-01), **1 authorization-gated** (FIX-SECMASTER-01). All 12 fixtures retained. |
| C5 | D02-D9 reworded: series treated as **potentially time-varying dated classification/state pending row-level transition evidence**; per-security transitions no longer described as demonstrated; the prohibition on using series as immutable identity retained. |
| C6 | ST finding retained with corrected epistemic status: **distribution discontinuity / semantic-interpretation anomaly** (≈16.9→124.7 rows/day), *not* a proven semantic break (§3 D02-D7, §10.4, §12). FIX-UD-CENSUS-01 and FIX-SERIES-EVENTS-01 remain the resolving evidence. |
| C7 | FIX-UD-ROW-SAMPLE-01 (and FIX-OVERLAY-SEM-01) now explicit about spanning **both formats**; 2024-03-28 re-labeled as its true Legacy-era date (kept, not moved); FIX-SECMASTER-01 references "sample dates (both eras)". |
| C8 | §10.6 holiday characterization removed; neutral statement + observed facts only (2,616 rows / 1,813 EQ / 313 BL / internal `03-OCT-2022`); dating correctness explicitly *not* decided; FIX-CAL-01 unchanged. |
| C9 | §8 `security_id` row rewritten: **proposed durable internal identity concept; resolution strategy pending D03**; `security_id = ISIN` explicitly not assumed; ISIN kept as strongest input candidate. |
| extra | Two internal-reference precision fixes found during review: dangling `FIX-ISIN-SEM-01` → real fixtures (FIX-SYMBOL-HIST-01/FIX-UD-CENSUS-01 vs FIX-XCONT-01); `FIX-CENSUS-01` → `FIX-LEG-CENSUS-01 / FIX-UD-CENSUS-01`. Derived-CSV classification `basis` strings regenerated to match (counts, classes, rows unchanged — text only). |
| extra-2 | Regeneration determinism defect found and fixed in `d02_derivation.py`: tie-ordering in two tables depended on Python set iteration order (unstable across hash seeds). Sort keys now include a stable secondary key; verified byte-identical output under `PYTHONHASHSEED` variation. Row *content* of the two affected CSVs is unchanged vs Rev 1 (only tie row order was restabilized); no metric in `d02_metrics.json`, `d02_anomalies.json`, `d02_series_class_rollup.csv`, or `d02_missing_weekdays.txt` changed. |

*End of D02 record. Produced under read-only investigation authority; all RECOMMENDATION items are
proposals pending approval at a later gate.*
