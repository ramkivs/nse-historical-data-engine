# D05 — Canonical Data Model Specification (NSE CM Historical Bhavcopy)

Version: 1.0 · Date: 2026-10-06 · Branch: `arena/01a10c83-nse-historical-data-engine`
Nature: **SPECIFICATION ONLY.** This document defines the canonical model, flags, parser tolerances and
determinism conventions for the NSE CM historical bhavcopy corpus. It is not an implementation, grants no
implementation authority, and performs no writes to the raw corpus.

Evidence base (authoritative for this spec):
- `docs/investigations/D02_EQUITY_ELIGIBILITY_AND_IDENTITY.md` (corpus-level eligibility/identity findings)
- `docs/investigations/D03_BOUNDED_FIXTURE_INVESTIGATION.md` §§1–15 (bounded fixture investigation, frozen dispositions, post-run reconciliation)
- `docs/investigations/D04_CANONICAL_MODEL_DECISION_INVESTIGATION.md` (DEC gate authorization record)
- `docs/investigations/D04B_DEC12_DOCUMENTATION_AND_MASTER_INVESTIGATION.md` (DEC-1/DEC-2 outcomes)
- `evidence/d03/windows_run/` (39 published fixture artifacts, `MANIFEST.sha256`-anchored; see `RUN_INFO.json`)
- `evidence/d04/DEC2_CAL_LABELS.json`, `DEC2_Q7_UNIT_SCALE.json`, `DEC2_Q8_OVERLAY_AGG.json`,
  `DEC2_CIRC_MEANINGS.json`, `DEC1_SECMASTER_FEASIBILITY.json`, `DEC12_CIRCULAR_REGISTRY.json`
- D01 inventory: `evidence/inventory/file_inventory.json`, `evidence/identity/d02_missing_weekdays.txt`

## 1. Status vocabulary

| Tag | Meaning |
|---|---|
| [ADOPTED] | Governed by this specification; future implementations MUST conform. Adoption here is specification-level only; it does not implement or run anything. |
| [DEFERRED] | Intentionally not decided; requires a named external input and/or a later gate. Implementations MUST NOT substitute a default. |
| [OPEN-SEMANTICS] | Exchange meaning not established by corpus + retrieved official documentation; recorded as observation only, never silently resolved. |
| [NON-ASSUMPTION] | Explicitly frozen non-assumption carried from D03/D04B (§12 register); MUST NOT be promoted to a rule without new evidence. |

Evidence-strength qualifiers used with [ADOPTED]: *corpus-proven* (measured over the full corpus via D02/D03),
*evidence-backed* (derived from published fixture evidence plus official documentation), *documented*
(official circular/definition text), *sample-supported* (bounded stratified sample; not full-corpus proven).

## 2. Layered model and provenance [ADOPTED]

- **L0 — Raw archive** (read-only): ZIP members as published. Never mutated, never stored in Git.
- **L1 — Derived evidence** (Git-committed): fixture artifacts (`evidence/d03/windows_run/`), inventories
  (`evidence/inventory/`), DEC evidence (`evidence/d04/`). Reproducible; hash-anchored.
- **L2 — Canonical layer** (defined by this spec, not built): normalized row/entity records carrying, in every
  record, a provenance reference (§8) that resolves to exactly one L0 member + the L1 tools version that parsed it.

Rules:
1. Every canonical record MUST carry: source archive file name, archive sha256 (as recorded in the D01
   inventory), member format family (`legacy13` | `udiff34`), parser/normalizer contract version (this spec
   ID + tool version), and the member's *raw-bytes* sha256 and *LF-normalized text* sha256 (§9). [ADOPTED — determinism conventions]
2. Derived artifacts are evidence, not production code paths; fixtures (tools/d03_fixture_scan) remain
   evidence-only and are not the canonical parser. [ADOPTED — carried from standing constraints]
3. No field may be inferred, imputed, or defaulted unless this spec says so explicitly. Blank stays blank. [ADOPTED]

## 3. Logical field mapping (literal headers) [ADOPTED — corpus-proven schemas]

Observed, exhaustive, stable across the corpus: **legacy = 13 named fields (+ trailing empty 14th physical
field in some files; §7 header tolerance)**; **UDiFF = exactly 34 fields (width 34; never 33)**.

Legacy header (verbatim): `SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,TOTALTRADES,ISIN`
UDiFF header (verbatim): `TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,XpryDt,FininstrmActlXpryDt,StrkPric,OptnTp,FinInstrmNm,OpnPric,HghPric,LwPric,ClsPric,LastPric,PrvsClsgPric,UndrlygPric,SttlmPric,OpnIntrst,ChngInOpnIntrst,TtlTradgVol,TtlTrfVal,TtlNbOfTxsExctd,SsnId,NewBrdLotQty,Rmks,Rsvd1,Rsvd2,Rsvd3,Rsvd4`

### 3.1 Canonical record: `SecurityRow` (one per physical bhavcopy data row) [ADOPTED]

| Canonical field | Legacy source | UDiFF source | Type/Presence | Rule |
|---|---|---|---|---|
| `security_isin` | `ISIN` | `ISIN` | string(12), always present in both eras (0 blanks / 5,689,949 rows UDiFF era) | Stored **verbatim**; normalization for matching = uppercase, strip whitespace only [ADOPTED]. Never used as a join key across namespaces other than ISIN↔ISIN. Validity is a flag (§5), never a gate. |
| `listing_symbol` | `SYMBOL` | `finInstrmId` | string, always | Dated attribute only — **never durable identity** [ADOPTED — corpus-proven: 845 ISINs with multiple symbols; SYMBOL never durable]. |
| `series` | `SERIES` | `SctySrs` | string, always | Dated attribute; time-variance is proven fact (2,431/7,633 multi-series ISINs) [ADOPTED as observation]; exchange meaning per §11 registry. |
| `security_name` | (absent) | `FinInstrmNm` | UDiFF only; legacy has no name column | Stored as published; do not backfill legacy names from any master unless [DEFERRED] DEC-1 join is later authorized. |
| `business_date` | date part of `TIMESTAMP` | `TradDt` | ISO date, always | Legacy: parsed per §7 timestamp tolerance, cross-checked vs filename date; UDiFF: `TradDt==BizDt` always (corpus-proven) → store both raw, canonical = `TradDt`, flag §5. |
| `raw_biz_dt` | `TIMESTAMP` | `BizDt` | string verbatim | Retain original text; parser never mutates the raw row store (§2 rule at L1 raw-line retention). |
| `prices.open/high/low/close/last/prev_close` | `OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE` | `OpnPric,HghPric,LwPric,ClsPric,LastPric,PrvsClsgPric` | decimal as-published | Stored **as published**, no rescaling, no defaulting of zeros (zeros are meaningful in overlay windows) [ADOPTED — units §10]. |
| `traded_quantity` | `TOTTRDQTY` | `TtlTradgVol` | integer as-published | Shares (units: no embedded metadata; official field definition + §10 sample test) [evidence-backed]. |
| `traded_value` | `TOTTRDVAL` | `TtlTrfVal` | decimal, rupees | [sample-supported] rupee value (0/1,589 lakh-scaled rows across 4 dates both eras; official definition "rupee value", VWAP=f9/f8). Provenance note mandatory. |
| `trades_count` | `TOTALTRADES` | `TtlNbOfTxsExctd` | integer | Official definition: normal market only, **excludes auction market trades** (documented) — do not reconcile against auction events. |
| `lot_size` | (absent) | `NewBrdLotQty` | UDiFF only | as-published. |
| `remarks` | (absent) | `Rmks` | UDiFF only | as-published opaque string. |
| `segment`, `source`, `instrument_type` | (absent) | `Sgmt`, `Src`, `FinInstrmTp` | UDiFF only | Stored as *descriptive* attributes. Non-discriminative for equity eligibility (corpus-proven: Sgmt=CM/Src=NSE everywhere; `FinInstrmTp=STK` ≠ equity — contradicted) [NON-ASSUMPTION — do not use as type filters beyond exact stored value]. |
| `expiry`, `actual_expiry`, `strike`, `option_type`, `undrlyg_pric`, `sttlm_pric`, `open_interest`, `oi_change`, `session_id`, `rsvd1..4`, `underlying_symbol` (`TckrSymb`) | (absent) | corresponding columns | UDiFF only, mostly blank for CM equity rows | Stored verbatim; blank stays blank; **no semantics inferred from non-blank patterns** [OPEN-SEMANTICS where seen]. |
| `format_family` | — | — | enum `legacy13`/`udiff34` | Assigned per §7. |

### 3.2 `SecurityIdentity` (entity) [ADOPTED — per D04 proposal]

| Field | Rule |
|---|---|
| `security_id` | Surrogate key of the canonical model. **Proposed** identity anchor = ISIN *within era* + explicit continuity policy (below). [ADOPTED as structure only — see non-promotion constraint] |
| `is_valid_isin_format` | §5 flags stored here; informational. |
| `isin_list` | Normally one; multi-symbol/multi-name facts hang off dated associations, not this list. |
| continuity across legacy↔UDiFF boundary | ISIN-based cross-era continuity measured 2,692 matched / only_L 83 / only_U 122 — residuals remain **[OPEN-SEMANTICS — UNINTERPRETED]**; do not classify boundary rows as listings/delistings without DEC-1 master evidence. |
| ISIN promotion constraint | **ISIN is the strongest identity candidate but MUST NOT be promoted to exchange-authoritative identity from census evidence alone** [NON-ASSUMPTION, standing]. This spec adopts ISIN as *the canonical correlation key* (a model decision), not as an exchange-confirmed identity. |

### 3.3 `DatedAssociation` (symbol/series validity structure) [ADOPTED — structure]

One row per `(security_id, symbol, series, observed_from, observed_to, provenance)`; corpus-derived intervals
are **observed first/last presence ranges, not official validity periods** — label field `interval_basis =
"observed-range"`. `association_type`: `corpus-observed` | `master-snapshot` | `etf-register-membership`.
Only the first exists today. `master-snapshot` rows are **[DEFERRED — DEC-1]**: monthly Masters snapshots
(ISIN, Symbol, Series, Name, Deleted) and `eq_etfseclist.csv` (official ETF register incl. ISINs) are the
identified authoritative sources; acquisition is blocked from the sandbox (HTTP 500/TLS; recorded), the join
fixture (design FIX-ETF-JOIN-02) is specced but not built, and **the master is not assumed authoritative**
until provenance capture + corpus cross-consistency + explicit acceptance (§11 of D04B). The official
statement that a security is "uniquely known by symbol+series" (pre-ISIN-era Masters model) is recorded as
documentation context supporting dated-association modeling — not as an adopted identity rule.

Transitions between (symbol,series) states are events, not mutations: rows are append-only per observed
interval; the same ISIN appearing as `EQ` then `BE` then `EQ` yields three dated rows [ADOPTED]. The
EQ↔BE / SM↔ST surveillance shift mechanism is *documented* (§11 registry: SURV74008, ESM circular, EMERGE
page) — stored as annotation vocabulary on dated rows (`documented_cause: ESM/GSM settlement-regime shift`),
while transitions with no matching documented action stay **[OPEN-SEMANTICS]**.

### 3.4 `CalendarDay` [ADOPTED — structural; labels per §11]

| Field | Rule |
|---|---|
| `trade_date` | ISO date from filename set (D01). |
| `file_present` | boolean — **the trading-session signal** (both-direction circular divergences observed: 2024-11-01 holiday w/o file; 2025-10-21 circular-holiday WITH 3,039-row file due to Muhurat special session). |
| `weekday` | derived. |
| `missing_weekday` | true iff a weekday has no file (147 total; 2,609 = 2,462 files + 147 gaps reconciled). |
| `official_holiday_label` | nullable; populated **only** where a retrieved circular names the date (registry §11); 2024-H2/2025/2026: 29/32 gaps explained; 2024-11-20, 2025-10-20, 2026-01-15 unexplained → `null` with `label_status="unexplained-by-obtained-circulars"`. Legacy era (2016–2023) `label_status="not-retrieved"` [NON-ASSUMPTION: never invent legacy holiday causes]. |
| `trad_dt_eq_biz_dt` | UDiFF always true (corpus-proven); legacy N/A. |

Parser/consumers MUST NOT use annual circulars to predict file presence; calendar is **derived from the
corpus, labeled by circulars where sourced** [ADOPTED].

### 3.5 Overlay handling [ADOPTED — restricted to observable relations]

Overlay rows keep their own `(business_date, series, isin)` rows in `SecurityRow`; this model defines only:
1. `OverlayObservation`: `(overlay_series, business_date, isin, qty_rel)` where `qty_rel ∈ {lt,eq,gt}` vs
   same-day base row for the same ISIN, plus `match_type ∈ {BASE_SAME_ISIN, NO_BASE_ORPHAN}` — exactly the
   published evidence structure [ADOPTED — corpus-proven, 3,356+336=3,692 reconciled].
2. Set membership **observed** in corpus: {BL, BO, T0, IT, IL}. This is a data observation, **not** an
   eligibility/microstructure inclusion contract [NON-ASSUMPTION, standing].
3. Additivity: for **BL** and **IL**, overlay volume is NOT contained in base-row totals — proven by the
   superset argument (gt-counts 1,037 BL / 23 IL) + official separate-window definitions [ADOPTED as
   evidence-backed]: summing base+BL/IL does not double-count. **T0: [OPEN-SEMANTICS]** (237/237 lt is
   consistent with both models; no official totals statement retrieved). **BO: buyback event rows**, not
   market volume (documented; 0/112 gt).
4. Orphans (no same-day base row; e.g. 3 BL + 333 IT observed) are **retained and flagged**
   `orphan_no_base_row=true`; interpretation [OPEN-SEMANTICS] — the 4 UDiFF-era IT orphans and era
   boundaries of IL (discontinued 2018-07-01, documented) are annotations, not rules.
5. No merge, drop, dedupe or volume-aggregation rule may be applied to overlay rows by a canonical-model
   consumer without an explicit later governance decision [ADOPTED prohibition].

## 4. Metric semantics inherited from D01 [ADOPTED]

All "distinct" counts in inventory/canonical summaries mean **distinct non-blank values** (e.g.
`isin_count` = distinct non-blank ISINs; 1,078/1,078 fixture agreement). Zero distinct-blank inclusion,
zero positional counts. D01's per-file definitions are restated verbatim in
`FIX-SEM-DEF-01__d01_definition_verdict.json`; implementations reuse that definition, not a re-scan [ADOPTED].

## 5. Validity flags [ADOPTED — non-gating]

| Flag | Condition | Severity |
|---|---|---|
| `isin_invalid_checkdigit` | ISIN fails mod-10 check digit (Legacy era: 215,393 rows ≈5.4%; corpus-proven) | informational |
| `isin_invalid_length` | length ≠ 12 after trim (1 row corpus-proven) | informational |
| `row_fieldcount_mismatch` | parsed width ≠ family width after §7 tolerance | quarantine row-level, keep raw |
| `date_source_conflict` | row-derived date ≠ filename date (0 observed) | informational, keep both |
| `bizdt_ne_traddt` | UDiFF only (0 observed) | informational |
| `orphan_no_base_row` | §3.5.4 | informational |
| `overlay_qty_gt_base` | §3.5.1 `gt` | informational (additivity evidence) |

**Hard rule:** validity flags NEVER gate, filter, reject or de-rank a row for identity, eligibility, or
aggregation purposes; ISIN validity is **informational only** [ADOPTED — this is the governing disposition for
the legacy invalid-checkdigit population: keep, flag, never assume defect implies non-security]. Quarantine
handling applies only to structural parse failures (per D01's own parse discipline), and quarantined raw lines
remain in L1 evidence.

## 6. Identifier treatment rules [ADOPTED]

1. `security_isin` is the only cross-format/cross-era correlation key; matching is exact-string after
   uppercase/trim [ADOPTED].
2. **FinInstrmId is an opaque secondary attribute.** It is the UDiFF symbol-bearing column; on 1,700,650/1,700,650
   UDiFF rows it never equals the ISIN and never carries ISIN structure; its namespace relationship to ISIN is
   **not inferable** and is FROZEN [NON-ASSUMPTION]. Consumers MUST NOT join on it, hash it as identity, or
   interpret prefixes/suffixes. Its surface form is stored verbatim; the canonical `listing_symbol` records the
   same text with a provenance pointer to this column.
3. `TckrSymb` (underlying symbol) and `Rmks` are stored, never interpreted [ADOPTED].
4. SYMBOL never durable identity; dated association only (§3.3) [ADOPTED].
5. Eligibility: **no eligibility predicate is part of the canonical model.** The candidate rule "Series==EQ
   minus official ETF register" is [DEFERRED — DEC-1]: EQ contains ETFs (documented legend 2024 + corpus
   contradiction of SERIES==EQ sufficiency: 1,188,443 rows / 3,078 ISINs), and the disambiguating ISIN join is
   not yet acquired/validated. UDiFF observed groups are **not** an eligibility contract [NON-ASSUMPTION].

## 7. Parser tolerance (observed variations that MUST be accepted) [ADOPTED]

1. **Header variants (legacy):** 13-field header and 14-physical-field header with trailing empty field are
   the same logical schema (FIX-ANOM-01 closed: header serialization/format variation). Parsers MUST accept
   both and normalize by **column name, never by position** [ADOPTED].
2. **Timestamps (legacy):** both `DD-Mon-YY` and `DD-Mon-YYYY` forms occur (e.g. 2,001 rows on 2020-07-13);
   accept both; two-digit year expansion is display-normalization only, and the canonical date is
   cross-checked against the filename date (mismatch → flag, never silent repair). Time-of-day retained in raw.
3. **UDiFF width 34** with a strict header set; a member whose header matches neither family header (after §7.1
   trailing-empty tolerance) is a parse failure → quarantine, not "best-effort map" [ADOPTED fail-closed].
4. Quoted fields with embedded commas (names) — RFC-4180-style quoting is the observed form; blank numeric
   fields occur in overlay rows (zero/blank prices in block windows) — keep as published (§3.1) [ADOPTED].
5. Physical-line assumption: one row per logical record (no embedded newlines observed); if future files break
   this, it is a spec amendment trigger, not an implicit fix [ADOPTED].
6. Encoding: files are ASCII in every sampled/processed member; parsers MUST fail loudly on non-decodable
   bytes rather than drop characters [ADOPTED from fixture-era observation; no broader encoding claim made].
7. FIX-ANOM-01 is CLOSED as format variation — no further header archaeology unless this parser contract
   materially changes [ADOPTED process rule].

## 8. Provenance record fields [ADOPTED]

Every L1/L2 artifact and (conceptually) every canonical row batch carries:
`provenance = { source_archive: filename + sha256(D01 inventory), member_name, format_family,
spec_version: "D05/1.0", tool_version: <name+version+sha256>, run_id: RUN_INFO.json id where applicable,
evidence_refs: [fixture IDs] }`. Official-document citations resolve through
`evidence/d04/DEC12_CIRCULAR_REGISTRY.json` (circular id, date, URL, excerpt scope). A derived fact with no
resolvable provenance entry is invalid [ADOPTED].

## 9. CRLF/LF determinism conventions [ADOPTED — mirrors accepted D03 packaging]

1. Stored derived text artifacts use **LF** endings and end with a final newline [ADOPTED].
2. Determinism hashes: primary = sha256 over the stored (LF) artifact; where an artifact represents raw corpus
   bytes, **both** hashes are recorded: sha256(raw member bytes, CRLF preserved) and sha256(LF-normalized text).
3. Two artifacts are "identical" iff their LF-normalized forms and line counts match — CRLF↔LF round-tripping
   is a serialization detail, not a content difference (this is how the manifest CRLF issue was closed and how
   remote verification passed 37/37 payload matches) [ADOPTED].
4. Rerun determinism criterion: byte-identical outputs except fields explicitly declared run-metadata
   (precedent: D03 `RUN_INFO.generated_utc`, 38/39 → PASS) [ADOPTED].

## 10. Units and numerics [ADOPTED, with §5 flag discipline]

1. Numeric fields stored **as published** (no rescale, no rounding, no reformat) — the original standing rule
   stands [ADOPTED].
2. Value fields (`TOTTRDVAL`, `TtlTrfVal`): rupee totals [sample-supported §1 finding; official definition].
   Quantity fields: shares. Prices: ₹/share. Because no units metadata is embedded in files, **every consumer
   display MUST carry the provenance note** ("scale supported by sample test + official field definitions, not
   by in-file metadata") [ADOPTED].
3. `trades_count` excludes auction-market trades (documented official definition) [ADOPTED as annotation].

## 11. External-semantics registry (documented, not silently operationalized) [ADOPTED — record only]

Series meanings, surveillance shift mechanism, IL discontinuation (NSE/CMTR/37880, effective 2018-07-01),
BL origin (NSE/CMTR/7864), T2T "no netting off", ESM stage actions, and holiday circular tables live in
`DEC12_CIRCULAR_REGISTRY.json` / `DEC2_CIRC_MEANINGS.json`. Canonical-model consumers may attach these as
annotations; they MUST NOT alter parsing, keys, or row validity. Retroactivity rule: post-2024 legend/ESM text
is not applied to 2016–2023 semantics beyond consistency notes [ADOPTED — "do not retroactively reinterpret"].

## 12. Non-assumption register (every frozen D03/D04B item, explicit) [NON-ASSUMPTION — all binding]

| # | Frozen item | Status in this spec |
|---|---|---|
| F1 | ISIN not promoted to exchange-authoritative identity | §3.2, §6.1 — correlation key only |
| F2 | FinInstrmId↔ISIN namespace equivalence not inferable | §6.2 — opaque |
| F3 | Series exchange semantics for transitions not matching a documented action | §3.3 — OPEN-SEMANTICS |
| F4 | UDiFF observed groups ≠ eligibility contract | §6.5 — no eligibility predicate |
| F5 | SYMBOL never durable identity | §3.1/§6.4 |
| F6 | Units "as published"; no in-file units metadata | §10.2 |
| F7 | Overlay/orphan observation ≠ microstructure inclusion rule; T0 inclusion | §3.5.2/§3.5.3 — T0 OPEN |
| F8 | Legacy-era (2016–2023) holiday labels | §3.4 — not-retrieved, never invented |
| F9 | XCONT only_L/only_U boundary residuals | §3.2 — UNINTERPRETED |
| F10 | ST parallelism & determinism dispositions (closed, not reopened) | §9.4 — accepted precedent |
| F11 | IT series definition | §3.5 — FROZEN (no authoritative text retrieved) |
| F12 | SF code | DEC2_CIRC_MEANINGS — OPEN |
| F13 | BE rights-entitlement vs T2T row-level split | OPEN-SEMANTICS (heuristic evidence-only) |
| F14 | SGB-STK documentation contradiction (D02-era) | remains OPEN, annotation-only |
| F15 | ETF/EQ overlap counts requiring master join | §6.5 — DEFERRED |
| F16 | Corporate-action symbol co-location semantics | not modeled; DEFERRED |
| F17 | Security master authority | §3.3 — DEFERRED, no-assumption recorded |

## 13. ADOPTED vs DEFERRED summary

**ADOPTED (governs future implementations):** layered provenance model (§2); field mapping & literal schemas
(§3.1); SecurityIdentity + dated associations as *structures* (§3.2–3.3); calendar from file-presence with
circular labels where sourced (§3.4); overlay observables + BL/IL disjointness as evidence-backed (§3.5);
non-gating validity flags (§5); opaque FinInstrmId + name-key parsing (§6–7); CRLF/LF determinism (§9); rupee
scale with mandatory provenance note (§10); registry-as-annotation (§11).

**DEFERRED (each names its blocker):** eligibility predicate & ETF join (DEC-1 master acquisition +
consistency + acceptance); master-snapshot dated associations (same); T0 volume-inclusion semantics (needs
official statement or further evidence); legacy-era calendar labels (needs 2016–2023 circular retrieval —
low value, permitted to stay unresolved); IT/SF/BE-split/SGB-STK semantics (documentation gap); corpus-side
implementation itself (pipeline authority NOT granted — later gate).

## 14. Prohibitions carried into implementations

No code paths shipped by this document; no writes to L0; no silent resolution of any [OPEN-SEMANTICS] item; no
promotion of inferred semantics into governed rules without new evidence appended to the registry; no use of
fixtures as production code; no re-scan of the raw corpus to "improve" D01/D03 metrics (they are frozen facts);
report reality exactly where task text and evidence diverge.

## 15. Next gate

D06 (proposed): presentation of this spec for **canonical-model adoption decision** + optional Windows-side
DEC-1 master acquisition (download → hash → FIX-ETF-JOIN-02). Engine implementation remains a separate, later
authorization. Nothing in D05 pre-empts either.
