# D03 — Bounded NSE Archive Fixture Investigation

Record status: **D03 COMPLETE — post-run reconciled 2026-10-06. Windows corpus execution done; evidence
durable on `origin/main@094105b` (`evidence/d03/windows_run`, 39 files, 37/37 manifest payloads verified);
every fixture carries an explicit disposition in §15. Investigation-only boundary unchanged: no
implementation authority.**

- Gate: D03 (evidence generation and semantic investigation). **No implementation authority is granted or
  implied by anything in this record.**
- Authoritative baseline: `main @ 46c81f849645ba05e6d96e2d26adb33438b26378` (D02 Rev-2 merge).
- Working branch: `arena/01a10c83-nse-historical-data-engine`.
- Corpus (unchanged, from D01): 1,919 Legacy bhav copies 2016-09-20…2024-07-05
  (`C:\IIPS_Data\NSE_Legacy_Acquisition\archives`) + 543 UDiFF files 2024-07-08…2026-09-18
  (`C:\IIPS_Data\NSE_CM_UDiFF_10Y\archives`) = 2,462 archives, 5,689,949 rows. **Not accessed from Arena.**

## 1. Scope and rules honored

D03 SHALL generate bounded, deterministic, provenance-complete evidence fixtures over the read-only corpus
and use them to resolve or explicitly freeze D02's open questions. D03 SHALL NOT implement the engine,
ingestion, persistence, or any pipeline; SHALL NOT modify/rename/copy raw archives or commit them; SHALL NOT
acquire the security master (authorization-gated); SHALL NOT convert proposed semantics into contracts.
"Unknown" is recorded as UNRESOLVED / INSUFFICIENT EVIDENCE; no semantics were manufactured from intuition
(calendar or otherwise). Every statement below is tagged as **observed**, **semantic conclusion**,
**proposed implication**, **unresolved**, or **implementation decision** — and the categories are not mixed.

## 2. Baseline integrity

- At session start this working tree was byte-identical to the merged `46c81f8` tree (verified per-file with
  `git show 46c81f8:<f> | diff - <f>` after staging; empty staged diff). Checkpoint commit `930af1c`.
- The D02 record (`docs/investigations/D02_EQUITY_ELIGIBILITY_AND_IDENTITY.md`) and all `evidence/`
  artifacts are inherited unchanged. D01 evidence is treated as read-only; nothing here redefines it —
  where D01 ambiguity exists (Q1), the resolution is a *new derived fixture*, never an edit.

## 3. Corpus assumptions verified without raw access, and what remains assumption until the Windows run

| Assumption used by fixtures | Status | Evidence basis |
|---|---|---|
| UDiFF header = 34 fields, every file, same names/order | **VERIFIED for stored signatures** (Arena-side): all 543 files share ONE 34-field `header_signature` (`FIX-UD-CENSUS-01_arena_header_verification.json`) | D01 per-file header capture; not a rescan of bytes — tool additionally re-verifies from files at fixture runtime |
| Legacy header = 13 named fields + trailing empty field, with exactly 2 files having a 13-field header | **VERIFIED for stored signatures**: 1,917 files @14 names, 2 files @13 names; 2 distinct signatures total | same |
| One file per date; no Saturday/Sunday files; every missing file-date is a weekday | **VERIFIED** from 2,462 stored dates: Mon–Fri only (488–496 files per weekday); span contains 2,609 weekdays = 2,462 present + **147 missing (arithmetic closes exactly)** | `FIX-CAL-01_arena_partial.json` |
| Column-name presence per format (ISIN idx 12 / ISIN idx 6 in UDiFF order, FinInstrmId idx 5, etc.) | **observed (stored signatures)** | D01 |
| All *values-level* facts (ISIN validity, FinInstrmTp distribution, symbol histories, overlay rows, anomaly raw content) | **UNVERIFIED — fixture outputs pending**; tool logic selftested on synthetic data only | this record §8 |

## 4. Fixture inventory and per-fixture status

Corpus-dependent fixtures are implemented in `tools/d03_fixture_scan/d03_fixtures.py`
(sha256 `d36924844a88ce40d9d5b2924062c095e4d243dc53963f71f64ccd7b53315291`, v1.1.0, stdlib-only,
read-only, deterministic) and are **PREPARED-BLOCKED**: one Windows invocation produces all of them.
Tool correctness is established by `d03_selftest.py` (sha256 `30f2edee…9e7679`): **65/65 checks PASSED**
against hand-computed expectations on a synthetic mini-corpus (`D03_TOOL_SELFTTEST_output.txt`).
The selftest also proves the determinism contract: two runs at the same frozen timestamp are
**byte-identical across every output including RUN_INFO**, and `MANIFEST.sha256` verifies on rerun
(`verify` mode exit 0). Synthetic data validates the tool ONLY — it is not corpus evidence.

| Fixture | Answers | Selection logic (deterministic, documented in tool) | Status |
|---|---|---|---|
| FIX-SEM-DEF-01 | Q1 | all 2,462 files × competing metric definitions (rows / blank ISINs / distinct-nonblank / nonblank-rows / pair dupes), joined to committed D01 inventory via `--d01-inventory`; per-file discriminating flags + `d01_definition_verdict.json` computed only from files where definitions differ | PREPARED-BLOCKED |
| FIX-UD-CENSUS-01 | Q1,Q2,Q4,Q5 | full 543-file row-level scan grouped by (Sgmt,Src,FinInstrmTp,SctySrs) + marginals + blank/equality counts for ISIN & FinInstrmId + header-width re-verification from bytes | PREPARED-BLOCKED (Arena width component DONE) |
| FIX-UD-ROW-SAMPLE-01 | Q2,Q4,Q7, BizDt | 2024-07-08 (first UDiFF) + 2025-10-30 + 2026-08-25; dynamic additions: max-BL-date and first-TradDt≠BizDt date (computed, not hardcoded); ≤2,000 rows/date stratified 1-per-series-class first + special rows (RE-*, ETF-hint, blank-ISIN, blank-FinInstrmId); verbatim raw lines when line/row counts align, else flagged re-serialization | PREPARED-BLOCKED |
| FIX-LEG-CENSUS-01 | Q1,Q2 | full 1,919-file scan: blank/valid/invalid ISIN counts with **real ISO-6166 check-digit validation** (VALID/INVALID_CHECKDIGIT/LEN/PREFIX/CHARSET/BLANK), RE-evidence counters kept deliberately distinct: `RE_prefix` (broad, catches RELIANCE), `RE-dash-or-space`, `EXACT-RE`; (symbol,series) duplicate counts | PREPARED-BLOCKED |
| FIX-XCONT-01 | Q2,Q3,Q6 | ISIN-primary join across 2024-07-05 ↔ 2024-07-08 + (SYMBOL,SERIES) secondary join marked **not-identity**; only-side rosters; price-chain test (UDiFF PrvsClsgPric vs Legacy CLOSE); mechanical match-ratio verdicts labeled as mechanical | PREPARED-BLOCKED |
| FIX-SYMBOL-HIST-01 | Q6 | per-ISIN timeline across ALL 2,462 days; (symbol,series) transition emission with dates; stable-summary only for single-symbol single-base-series ISINs | PREPARED-BLOCKED |
| FIX-SERIES-EVENTS-01 | Q3,(ST) | base-series transition pairs, same-day series co-occurrence counts (ISIN-days), ST distribution-shift **hypothesis test** (D02 regime contrast ≈16.9 vs ≈124.7 rows/day: ST same-day co-occurrence with SM/SZ/EQ per ISIN + ST-adjacent transitions; result remains hypothesis-tagged) | PREPARED-BLOCKED |
| FIX-OVERLAY-SEM-01 | Q8,Q6 | every BL/BO/T0/IT/IL row classified **against observed base rows only** (per-date index, no assumption): BASE_SAME_ISIN / BASE_BY_SYMBOL_ONLY / NO_BASE_ORPHAN, with qty/close relation vs matched base; aggregates + bounded per-row CSV | PREPARED-BLOCKED |
| FIX-ANOM-01 | data-quality | raw verbatim inspection of 2017-07-10 and 2020-07-13 files + ±3/4-day windows (header field counts, timestamp-format histograms) | PREPARED-BLOCKED (D01-stored adjacent facts verified in §3/§8) |
| FIX-CAL-01 | calendar | structural component DONE on Arena (§3, `FIX-CAL-01_arena_partial.json`); holiday/festival labeling needs official circulars — tool intentionally does **not** label | PARTIAL |
| FIX-CIRC-01 | code meanings | corpus-side era brackets DONE (`FIX-CIRC-01_arena_partial.json`); documentation side (circular search, effective dates) is external retrieval — semantics frozen, see §8 | PARTIAL |
| FIX-SECMASTER-01 | external master | scoping-only, **NOT executed**: `FIX-SECMASTER-01_scoping.json` — authorization-gated | GATED |

Every fixture output carries: fixture ID, frozen-or-run timestamp, **tool sha256**, both roots, file counts,
selection criteria, metric definitions, per-file payload sha256 + `MANIFEST.sha256`; `verify` mode
re-checks. Raw archives are opened read-only and never written (`zipfile` read mode only; the tool has no
write path to the roots — outputs land exclusively under `--out`).

## 5. Results obtainable without raw access (this session)

1. **34-field width: verified** across all 543 stored UDiFF header signatures, one signature (order stable
   across the era). The D03 instruction "do not repeat the 33-field error" is satisfied by *file-derived*
   verification, and the runtime tool re-verifies widths from the bytes themselves (verdict `VERIFIED 34`
   in the selftest; any non-34 file would appear in `header_width_check.json` per-file entries).
2. **Calendar structure: verified.** Zero weekend files; 147 missing dates are all weekdays; the weekday
   arithmetic closes exactly (2,609 = 2,462 + 147). **Semantic conclusion:** missing days are
   *file-absence events on weekdays*; **no** holiday/festival cause is asserted (explicit rule: e.g. no
   "Gandhi Jayanti" style labels without authoritative circulars). 2022-10-03 remains uncharacterized.
3. **Anomaly adjacency:** exactly two files deviate from the standard Legacy header width (2017-07-10,
   2020-07-13 — same dates as the D02 anomaly register's header/date anomalies), confirming D01's
   observation without re-reading raw bytes.
4. **Legacy 2024-03-28 T0 evidence** (D02) remains: T+0 pilot activity began in the Legacy era — carried
   forward, now bracketable: `T0` udiff_first 2024-07-08, legacy_first 2024-03-28
   (`FIX-CIRC-01_arena_partial.json`).

## 6. What the fixtures will decide vs. what no corpus can decide

Mechanically decidable from the corpus alone (once executed): Q1 (exact D01 definition, verdict file),
Q2 (validity census), Q4 (FinInstrmId↔ISIN equality/namespace census + sampled literals), Q5 (Sgmt/Src
value groups), Q6 (ISIN↔symbol ledger; rename rate), overlay match-type distribution (Q8 *input*),
presence/rate of same-ISIN series transitions (Q3 *input*).

**Not fully decidable from the corpus:** Q3's semantic layer (a transition EQ→ST at constant ISIN shows
*continuity*; whether the exchange considers surveillance a state or a new instrument needs the
security-master/circular — corpus output constrains but cannot conclude), Q7 (units are not recorded in any
column — prices show 2-decimals formatting, but `TOTTRDVAL`-vs-`TtlTrfVal` scaling can only be *bounded*
by cross-checking sampled values against per-date aggregates, not proven), Q8 (whether base volume
*includes* overlay volume is a market-microstructure fact about bhavcopy semantics — the fixture supplies
the observable relation (equal / less / absent) and the count of orphan overlays; the exchange-contract
answer needs circulars). These boundaries are stated here so a Windows run is not over-read later.

## 7. Resolved in D03 (with the resolving artifact)

- **R1 (observed):** UDiFF 34-field width + single stable column order — §5.1 / `FIX-UD-CENSUS-01_arena_header_verification.json`.
- **R2 (observed):** No weekend files; missing-day arithmetic closes exactly; all 147 are weekdays — `FIX-CAL-01_arena_partial.json`.
- **R3 (observed, semantic-neutral):** exactly 2 header-variant files, widths consistent with D02's anomaly register — same artifact.
- **R4 (tool-proven):** the fixture tool itself meets the determinism contract (byte-identical double run,
  manifest verify, documented selection/sort rules, explicit caps incl. the ≤2,000/date rule) —
  `D03_TOOL_SELFTTEST_output.txt`.
- **R5 (method resolution):** Q1 is answerable by pure re-derivation with zero new corpus information
  (definition discrimination, not new measurement) — fixture built and joined to D01; *value* pending run.

## 8. Unresolved / INSUFFICIENT EVIDENCE (frozen unless noted) — D02 Q1–Q8 dispositions

| Q | D02 question | D03 disposition |
|---|---|---|
| Q1 | D01 `isin_count`/`symbol_count` definition | **PREPARED, PENDING RUN** — not guessed. All-file discrimination + verdict artifact (§4). After one Windows run this is expected fully decidable; until then any D02 reading stays open. |
| Q2 | ISIN value validity across eras | **PREPARED, PENDING RUN** — full ISO-6166 check-digit census in FIX-LEG-CENSUS-01/FIX-UD-CENSUS-01. ISIN remains *strongest candidate* only; validity, uniqueness, continuity **unproven** until outputs exist. |
| Q3 | Series change → new ISIN? (series-part-of-ISIN) | **NOT DECIDABLE from corpus alone** (§6). Corpus half (transition presence/rate) = PREPARED; semantics = **FROZEN UNRESOLVED** pending circulars/security master. No contract may assume either reading. |
| Q4 | FinInstrmId format/namespace vs ISIN | **INSUFFICIENT EVIDENCE, PENDING RUN** — field present (idx 5, all files); equality census + verbatim samples designed (FIX-UD-CENSUS-01, ROW-SAMPLE). Any "FinInstrmId is/isn't ISIN" claim remains prohibited. |
| Q5 | UDiFF Sgmt/Src as row-level segment discriminator | **PENDING RUN** — census groups by (Sgmt,Src,FinInstrmTp,SctySrs) + marginals answer it mechanically. |
| Q6 | Renames (symbol change, constant ISIN) | **PENDING RUN** — FIX-SYMBOL-HIST-01 ledger is exactly the artifact D02 named as most decision-relevant; rate + dated intervals will come from it. |
| Q7 | Price/volume units and null conventions | **FROZEN as analytical-governance constraint**: no units evidence exists in either format; sampling bounds but cannot prove. Governance rule until further notice: corpus value columns carry **no assumed units metadata beyond "as published"**; any unit-dependent analytics must state the assumption. (Per D03 instruction: unresolved → frozen, honestly.) |
| Q8 | Base-row volume inclusion of overlay volume (double-count) | **PARTIALLY BOUNDED, semantics FROZEN UNRESOLVED** — FIX-OVERLAY-SEM-01 yields observed per-row relations + orphan counts; the *inclusion* question needs exchange documentation (§6). Both readings (independent security rows vs duplicated-base rows; inclusion vs exclusion) stay open; no pipeline rule may adopt either. |
| CAL | missing-day holiday labels | **FROZEN UNRESOLVED** — structural half resolved (R2); labeling requires official NSE trading-holiday circulars; no guessing (2022-10-03 stays uncharacterized). |
| CIRC | IT/IL/SO/HA–HE/SF/era-dependent legend | **FROZEN UNRESOLVED** — corpus brackets done; current legend (2024-09-19) explicitly NOT applied retroactively; documentation retrieval is outside this environment's allowed one-shot fetch budget and was not attempted here; D02's verified legend/T+0 facts carry forward (T0 = settlement-state variant per NSE/NCL FAQ; EQ admits ETFs). |
| SECMASTER | external security master | **GATED — NOT EXECUTED** (§4, scoping JSON). |

## 9. Contradictions and near-misses noticed while building fixtures

- **C-1:** None found in *committed evidence*: D01 signatures, D02 derivations, and the new D03 partials are mutually consistent (counts, dates, anomaly identities).
- **C-2 (method contradiction avoided, recorded):** a naive "RE-prefix" counter would count **RELIANCE** (verified live by the selftest: broad counter = 4 rows vs 1 true `RE-` row). The tool therefore keeps three distinct counters and the record forbids using the broad one for identification. This is a design trap worth remembering for ingestion.
- **C-3 (carried from D02, still open):** third-party filter snippets (FinInstrmTp=STK) vs an unverified SGB-with-STK snippet — STK-sufficiency stays unproven; FIX-UD-CENSUS-01 will settle it *in this corpus* row-wise.

## 10. Frozen decisions (D03 → D04 boundary)

1. UDiFF = 34 fields (verified); Legacy = 13+trailing with the 2 known variants — ingestion must key on observed header names, not positional assumptions.
2. D01 metric semantics are NOT silently redefined; resolution path = FIX-SEM-DEF-01 verdict file.
3. No holiday/festival labeling without official circulars; corpus = "file present per weekday" only.
4. Legend applied only to its own era; pre-2024 unmapped codes stay UNCLASSIFIED.
5. Security-master acquisition remains user-authorization-gated; no D04 stage may *implicitly* require it.
6. `SERIES==EQ` insufficient for equity eligibility (unchanged); provisional classes remain provisional.
7. Proposed `security_id` remains a **proposal**; identity resolution strategy (incl. blank/overlay fallback) remains design-pending on Q1/Q2/Q6 outputs.
8. Fixtures (and this tool) are evidence artifacts, **not** production code; ingestion implementations must not import them.

## 11. D04 readiness assessment

**NOT READY.** Gating items: (a) the single Windows fixture run producing all 9 corpus-dependent outputs +
manifest verification (runbook: §12 step 2); (b) Q1/Q2/Q4/Q5/Q6 expected-resolvable from that run;
(c) Q3/Q7/Q8/CAL/CIRC labels carry frozen unresolved states into D04 as *constraints*, not answers;
(d) FIX-SECMASTER-01 decision from the user. D04 must treat every §8 FROZEN row as a standing governance
constraint and may not begin before the user authorizes it.

## 12. Provenance and reproduction

1. **This environment (Arena):** `python3 evidence/d03/d03_arena_evidence.py` regenerates the three partials
   byte-identically from hash-pinned committed inputs (verified double-run). `python3
   tools/d03_fixture_scan/d03_selftest.py` reproduces the 65-check PASS. Inputs: D01 `file_inventory.json`,
   D02 `d02_missing_weekdays.txt`, `d02_series_universe.csv` (sha256 embedded in each output's provenance).
2. **Windows host (raw corpus; run from a checkout at this branch):**
   `python tools\d03_fixture_scan\d03_fixtures.py run --legacy-root "C:\IIPS_Data\NSE_Legacy_Acquisition\archives" --udiff-root "C:\IIPS_Data\NSE_CM_UDiFF_10Y\archives" --d01-inventory evidence\inventory\file_inventory.json --out D:\d03_out`
   then determinism check: rerun with `--frozen-time 2026-10-05T00:00:00+00:00` to a second dir (payloads
   must be byte-identical) and `python … d03_fixtures.py verify … --out D:\d03_out` (exit 0). Commit
   `D:\d03_out` contents under `evidence/d03/windows_run/` — derived fixtures only; archives stay out of Git.
3. Read-only guarantee: the tool opens zips exclusively in read mode, writes nothing outside `--out`, and
   records roots/counts/tool-hash in `RUN_INFO.json`.

## 13. Durability

Session is **closed to remote operations** (PR for D02 merged; `git push`/`gh` will fail and were not
attempted). All D03 work is committed on `arena/01a10c83-nse-historical-data-engine` (on top of baseline
checkpoint `930af1c` — a tree-identical commit to merged `46c81f8`). **Remote durability is therefore NOT
verified from this session**; the user should fetch/merge the branch from the sandbox's pushed state in a
new session if the local commits above are not yet on GitHub. No raw archives, no synthetic data, and no
scratch files were committed; scratchpad outputs live only in `/tmp`.

## 14. Addendum — run-status reconciliation (2026-10-05) [historical — superseded by §15]

A post-run reconciliation request arrived instructing this record be updated with the actual Windows
corpus execution results. Verification found that **no Windows run output exists in this environment**;
the reconciliation therefore could not be performed and this record deliberately remains at its
pre-run state. Facts established by the verification pass:

1. **Windows-run evidence: ABSENT.** `evidence/d03/` contains only the Arena-side partials and the
   tool selftest capture. There is no `windows_run/`, no fixture-run `RUN_INFO.json`, no
   `MANIFEST.sha256` from a corpus run, and no `FIX-*__*` payload files anywhere in the workspace.
   Consequence: no Q1 verdict value, no ISIN validity census numbers, no transition/rename/overlay
   statistics exist yet; recording any would be fabrication. All 12 fixture dispositions below are
   therefore stated as pending-execution, not as post-run statuses.
2. **Environment reset detected and recovered.** The sandbox was re-created: this repository's git
   objects for `930af1c`, `91fd8a6`, `2a4aaf5` are gone and the branch pointer was rewound to
   `410135d`, but all D03 worktree files survived. Each surviving D03 file was verified **byte-exact**
   against the blob hashes recorded in `transfer/extracted/PACKAGE_METADATA.json` (5/5 MATCH), and the
   full transfer integrity chain re-verified: `transfer/*.b64` → tarball sha256 `6407e67a…72178d`
   (`PACKAGE OK`) → 8/8 package `MANIFEST.sha256` checks → selftest **65/65 PASSED** with the surviving
   tool. The D03 state was re-committed locally on this branch (this addendum's commit).
3. **D01/D02 baseline cross-check still closes:** 1,919 Legacy + 543 UDiFF = 2,462 archives,
   5,689,949 rows (recomputed from committed inventory).
4. **FIX-ANOM-01 closing disposition (operator-provided, accepted):** the run operator stated the
   intended classification of both anomalies — 2017-07-10 and 2020-07-13 as *historical header
   serialization / formatting variations* (13 vs 14 fields = trailing empty header field after `ISIN`,
   same named market-data columns; plus `DD-Mon-YY` vs `DD-MON-YYYY` timestamps on 2020-07-13),
   **not** missing economic/market-data columns; root-cause archaeology closed. This is **consistent
   with the stored D01 signatures** (exactly 2 nonconforming widths; variant identity verified in §5.3),
   but since the raw-file fixture output is not present, it is recorded here as the operator's
   disposition statement, not as Arena-verified execution evidence. It may be entered as RESOLVED in
   the run table only once the FIX-ANOM-01 outputs are committed under `evidence/d03/windows_run/`.
5. **Fixture disposition table (as of this verification — all pending the run):**

| Fixture | Disposition now | Post-run vocabulary applies when evidence lands |
|---|---|---|
| FIX-SEM-DEF-01 | PENDING EXECUTION — no verdict recorded | expect RESOLVED (Q1) |
| FIX-UD-CENSUS-01 | PENDING EXECUTION (Arena header component DONE) | Q2/Q4/Q5 census verdicts |
| FIX-UD-ROW-SAMPLE-01 | PENDING EXECUTION | Q2/Q4/Q7 bounding evidence |
| FIX-LEG-CENSUS-01 | PENDING EXECUTION | Q1/Q2 |
| FIX-XCONT-01 | PENDING EXECUTION | Q2/Q3/Q6 inputs |
| FIX-SYMBOL-HIST-01 | PENDING EXECUTION | Q6 |
| FIX-SERIES-EVENTS-01 | PENDING EXECUTION | Q3 inputs, ST hypothesis test |
| FIX-OVERLAY-SEM-01 | PENDING EXECUTION | Q8 observable relations only |
| FIX-ANOM-01 | PENDING EXECUTION (operator disposition recorded at §14.4) | expect closure per operator statement |
| FIX-CAL-01 | PARTIAL — structural DONE; labels **FROZEN UNRESOLVED** | unchanged by run unless circulars fetched |
| FIX-CIRC-01 | PARTIAL — brackets DONE; semantics **FROZEN UNRESOLVED** (no retroactive legend) | unchanged |
| FIX-SECMASTER-01 | **GATED — not executed** (authorization required) | unchanged |

6. **Standing rules restated for whoever executes:** read-only on archives; outputs commit under
   `evidence/d03/windows_run/` with RUN_INFO + MANIFEST; never commit raw archives; the interpretation
   boundaries of §6 still apply — Q3 semantics, Q7 units ("as published", unresolved), Q8 inclusion rule
   (documentation-gated), CAL labels (circular-gated), CIRC meanings (circular-gated) may NOT be
   over-read from census outputs. Series transitions, when produced, establish time-variance
   observationally, not the exchange's semantic intent. ISIN remains strongest-candidate, never
   promoted by census alone.
7. **Durability:** this recovery commit and all D03 files are local to the Arena branch; remote
   operations remain unavailable in this closed session. Durable publication requires the operator to
   push/recreate this branch content from an authorized session (or transfer it as done for the
   Windows package) — the 5-file package plus this record are byte-stable and hash-verified as above.

## 15. Post-run reconciliation and closure (2026-10-06)

Windows execution published; this section carries the final dispositions (history above kept intact for
audit).

**Run provenance.** Two independent executions (`C:\IIPS_Data\D03\windows_run`, `..._repeat`), 39 files
each, produced by tool sha256 `d36924844a88ce40…` = the committed `tools/d03_fixture_scan/d03_fixtures.py`
(byte-verified). Determinism: **38/39 files byte-identical; sole difference `RUN_INFO.generated_utc`** —
operator disposition *expected execution-metadata variation*; **substantive determinism PASS** (recorded
as ruled; not re-litigated). Published to `origin/main` as `094105b935b268a5c2f64327da58f253aeb9c7b7`.
Arena-side verification of the published evidence: **37/37 payload hashes reproduce** (27 exactly; 10
JSONs after git CRLF→LF blob normalization — root cause: the tool's JSON writer used Windows text mode,
so manifest hashes embed CRLF while git stores LF; content identical; packaging note for any future
fixture tool; zero semantic impact). Corpus counts match D01/D02 exactly: 1,919 + 543 = 2,462 files;
3,989,299 + 1,700,650 = 5,689,949 rows. Raw archives in tree: 0.

**Material findings (observed evidence → supported conclusion kept distinct):**

- **Q1 RESOLVED.** `FIX-SEM-DEF-01__d01_definition_verdict.json`: across all **1,078 discriminating
  files**, D01 `isin_count` matches **distinct-nonblank** (1,078/1,078; nonblank-rows matches: 0). The
  D02 ambiguity is closed against D01's own recorded numbers.
- **Q2 PARTIALLY RESOLVED; promotion constraint frozen.** Blanks: **zero blank-ISIN rows in either
  format** (all 5,689,949 rows carry ISIN). Validity: **215,393 Legacy rows INVALID_CHECKDIGIT + 1
  INVALID_LEN** (≈5.4% of Legacy rows); the same phenomenon appears in UDiFF samples. These are genuine
  corpus ISINs failing ISO-6166 Luhn — therefore: check-digit result is an **informational data-quality
  flag, never a rejection or identity key** (parser/DQ constraint carried to D04). ISIN remains the
  *strongest candidate* input only — a failed-Luhn population does not promote it to established durable
  identity, and D03 does not do so.
- **Q3 PARTIALLY RESOLVED (observation) / intent FROZEN.** Series is demonstrably time-varying at
  constant ISIN: **2,431 / 7,633 ISINs** hold ≥2 base series; **3,355** ISIN-days carry same-day
  multi-series rows; dominant transitions **EQ↔BE (5,738 / 5,653)** and **ST↔SM (1,368 / 869)** —
  surveillance/T2T reclassification round-trips, observationally. Whether a transition constitutes the
  "same security" in exchange semantics is documentation-gated and remains unresolved. The D02
  ST-parallelism hypothesis tested **negative**: ST never co-occurs same-day with SM/SZ/EQ for one ISIN
  (empty result) → ST is a standalone series state in this corpus; closed at that level (stopping rule).
- **Q4 RESOLVED at census level / namespace meaning FROZEN.** `FinInstrmId` **never equals `ISIN`**:
  0 equal / 1,700,650 unequal / 0 blank over all UDiFF rows; observed format is a short numeric
  (e.g. `20092`). Distinct-namespace is corpus-proven; identifying it as the exchange security id is
  documentation-gated. No equivalence or substitution contract may be inferred.
- **Q5 RESOLVED.** UDiFF `Sgmt`=`CM` and `Src`=`NSE` on **all** rows; `FinInstrmTp`=`STK` on **all**
  rows — including debt (`GB`/`GS`), mutual funds (`MF`), ETF-hint tickers inside `EQ`, and rights (`BE`).
  Therefore: Sgmt/Src are non-discriminative in-corpus (singletons; the 144 census groups exist purely via
  `SctySrs`), and the third-party "`STK` == equity" filter is **contradicted by the corpus** (D02 C-3
  contradiction closed). `SERIES==EQ` insufficiency (D02-F7) is now row-level confirmed: EQ group =
  1,188,443 rows / 3,078 ISINs with ETF hints present inside it. No eligibility contract may use these
  singletons as discriminators.
- **Q6 RESOLVED (ledger delivered).** **845 ISINs** carry ≥2 symbols corpus-wide; exactly **1** symbol
  change on the boundary day; dated rename/alias intervals are in `FIX-SYMBOL-HIST-01__transitions.csv`.
  SYMBOL is confirmed non-durable; never an identity key. True renames vs re-listing splits:
  documentation-gated, frozen.
- **Q7 FROZEN UNRESOLVED (reconfirmed by run).** No units evidence exists in either format; corpus values
  remain **"as published"**; any unit-dependent analytics must state the scaling assumption explicitly
  (e.g. Legacy `TOTTRDVAL` vs UDiFF `TtlTrfVal`).
- **Q8 PARTIALLY RESOLVED.** Per-row overlay observations (3,692 overlay rows, matching D02's count):
  same-day base found via identical non-blank ISIN in **3,356** cases (BASE_SAME_ISIN — LEGACY BL 1,949,
  BO 112, IL 204, T0 28; UDiFF BL 854, T0 209); `BASE_BY_SYMBOL_ONLY` = 0 (the "overlays carry blank
  ISIN" reading is **disproved**); orphans **336** = IT 329 Legacy + 4 UDiFF (no same-day base at all —
  consistent with institutional/rights windows; recorded, closed) and BL 1 + 2. Volume *inclusion*
  (double-count on add / undercount on drop) is not derivable from bhav copies: remains **FROZEN
  UNRESOLVED**; no inclusion/exclusion rule may be adopted without exchange documentation.
- **CAL**: structural findings final (2,609 weekdays = 2,462 present + 147 missing; zero weekend files).
  Holiday/festival labels remain **FROZEN UNRESOLVED** (official-circular gated; no-labeling rule stands;
  2022-10-03 remains uncharacterized).
- **CIRC**: era brackets stand; current legend not retroactively applied. New in-corpus corroboration for
  BE dual use (EQ↔BE round-trips at constant ISIN). Meanings of IT/IL/SF/HA–HE etc. remain **FROZEN**.
- **ANOM CLOSED** (operator disposition + run evidence): 2017-07-10 and 2020-07-13 = 13-field header
  (trailing-empty-field serialization variation; same named market-data columns; 2020-07-13 additionally
  `DD-Mon-YY` 2-digit-year timestamps on all 2,001 rows). NOT missing economic columns; root-cause
  archaeology closed. Evidence-backed parser constraint (not implementation): tolerate trailing-field
  header variance and both timestamp formats on affected dates.
- **XCONT (boundary continuity input).** Matched ISINs 2,692 (ratio 0.929 — mechanical verdict
  "significant discontinuity"); only-legacy **83** / only-UDiFF **122**; price chain PrvsClsgPric =
  prior Legacy CLOSE in **2,691 / 2,692** (99.96%) — supports market continuity for matched rows across
  the format change with no re-keying shock (1 matched series change set: 8 rows; 1 symbol change).
  The 205 one-sided ISINs are **uninterpreted** (delisting/listing vs defects: documentation-gated).
- **SECMASTER**: **GATED — not executed**; remains a user decision (scoping note unchanged).

**Fixture closure vocabulary:** FIX-SEM-DEF-01 RESOLVED · FIX-UD-CENSUS-01 RESOLVED (census scope) ·
FIX-UD-ROW-SAMPLE-01 RESOLVED (bounded-scope; all 8 dates incl. dynamic max-BL 2025-07-14; dynamic
TradDt≠BizDt target returned **NONE — no such date exists in the UDiFF corpus, so observed
`BizDt == TradDt` throughout**) · FIX-LEG-CENSUS-01 RESOLVED · FIX-XCONT-01 RESOLVED (mechanical) /
semantics open · FIX-SYMBOL-HIST-01 RESOLVED · FIX-SERIES-EVENTS-01 PARTIALLY RESOLVED (observation) /
intent frozen · FIX-OVERLAY-SEM-01 PARTIALLY RESOLVED · FIX-ANOM-01 RESOLVED-CLOSED · FIX-CAL-01
PARTIALLY RESOLVED (labels frozen) · FIX-CIRC-01 PARTIALLY RESOLVED (semantics frozen) ·
FIX-SECMASTER-01 GATED.

**D04 readiness: READY — investigable in Arena.** The §11 gating items resolved as follows: (a) run
complete and durable on main; (b) Q1/Q2(validity)/Q4(census)/Q5/Q6 evidence-backed by published
fixtures; (c) Q3-intent, Q7-units, Q8-inclusion, CAL-labels, CIRC-meanings enter D04 as **standing
governance constraints**, not answers; (d) security-master acquisition remains user-authorization-gated.
No further raw-corpus access is required for D04 investigation — every reconciliation statement above is
derivable from committed evidence (`evidence/d03/windows_run` + this record).

## 16. Post-record pointer (added 2026-10-06)

Subsequent DEC-1/DEC-2 official-documentation work is recorded in `D04B_DEC12_DOCUMENTATION_AND_MASTER_INVESTIGATION.md`
and consumed by `docs/specs/D05_CANONICAL_MODEL_SPEC.md`. Upgrades there change evidence-support levels for some
frozen dispositions (Q7 units, Q8 BL/IL additivity, CAL labels, Q3 mechanism class) and change NO corpus fact
recorded in this document; §8/§15 remain the corpus-side source of truth, and every item listed as FROZEN that
lacks new evidence (F1–F17 register in D05) stays frozen.
