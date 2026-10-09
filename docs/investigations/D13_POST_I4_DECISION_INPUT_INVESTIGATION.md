# D13 — Post-I4 Decision-Input Investigation (next-gate definition preparation)

**Status: RECORDED — investigation only. NO NEW GATE IS DEFINED OR AUTHORIZED BY THIS INVESTIGATION.**
**Gate:** `I4 = CLOSED / DURABLE / REMOTELY VERIFIED → (no defined next gate) → next-gate definition, authority pending`
**Produced:** 2026-10-09 (Arena side, read-only investigation over `origin/main`).
**Downstream product:** none in this repository — the deliverable is decision input for a future Ramki
authority decision. This record creates no gate, no authorization, no I5 definition, no M gate, no N
gate, and no storage-technology selection.

---

## 1. Purpose and strict scope

Task 26 (post-I4 authoritative next-gate discovery, read-only over `origin/main@8105e761…`) established:

> **NO NEXT IMPLEMENTATION GATE FORMALLY AUTHORIZED.** I5 is UNDEFINED. The repository's only forward
> pointer is D08 §16's "future M/N gate", which is a deferral label only and carries no implementation
> authority.

This record prepares, **investigation-only**, the decision inputs that Ramki (application decision
authority) would need to define and authorize the next post-I4 gate. It:

1. inventories the decided facts any future gate inherits (with citations);
2. analyzes each carried-open / carried-deferred item (A–H per item, §5);
3. produces a decision matrix (§6), dependency graph (§7), open/deferred register (§8), evidence
   requirements (§9), and **proposed decision questions** for the future authority decision (§10) —
   questions only, with blank decision fields, in the D08 §2 authorization-sheet pattern;
4. states the explicit non-authorizations (§11).

**Prohibited by this record's scope (and performed nowhere in it):** creating, defining, authorizing or
implementing any next gate; any I5 definition (I5 remains UNDEFINED; this record neither names it as a
stage nor infers its meaning); any M or N gate definition; storage-technology selection, persistence
implementation, API/serving implementation, UI implementation; corpus execution or replay; production
work; any modification of engine/runner/`i4_output.py` bytes; any reinterpretation of a carried item.

## 2. Authority and basis

* This investigation was commissioned by the authority's D13 directive ("investigation-only preparation
  of the decision inputs that Ramki would need in order to define and authorize the next post-I4 gate;
  this task MUST NOT create, define, authorize, or implement the next gate").
* It relies **only** on artifacts in the authoritative repository at `origin/main@8105e761…`:
  D06 (adoption record), D07 §8–§13 (DEC-1 status, nine OPEN semantics, scope boundary), D08
  §§4–18 (MD-02…MD-17 dispositions, authority boundaries, carried-forward items), D04B §2 (DEC-1
  feasibility + `DEC1_SECMASTER_FEASIBILITY.json`), D05 spec §§3.4/5/10/11/13 (governed consumer
  obligations, ADOPTED set), D09 §1 (failed-run history), D11 (§1, §5, §11–12: K1/K2/K3/G6, carried
  null anomaly, E1–E10), D12 (§2–§3, §6, §10–11: closure, C.7 findings, carried-forward block),
  `src/nse_engine/contract.py` (`KNOWN_EVIDENCE_DIVERGENCES`, W1-DIV-1), and the published D11
  evidence package (`evidence/D11_REPLAY_QUALIFICATION_20261009/`).
* No external retrieval, no execution, no measurement, no Windows access occurred in this
  investigation.

## 3. Verified baseline (read-only)

| Check | Observed | Verdict |
|---|---|---|
| Authoritative ref | `origin/main` = `8105e76175edd2ae4d490602f37242aed1d28d14` ("D12: I4 closure decision record…", parents `edbda829…` + `1507b740…`) | PASS |
| Tree | `3777ae1d…`, 140 blobs, `truncated: false`; full tree re-fetched and all 140 blobs byte-verified against the commit (Task 26 snapshot, re-verified this session) | PASS |
| I4 state in tree | README status line + D12 §11: `I4 = CLOSED / DURABLE / REMOTELY VERIFIED` | PASS |
| Working tree at publication | clean; only untracked `_transfer_delivery/` (staging, never committed) preserved untouched | PASS |
| Mutation set for this record | exactly 2 paths: this file (new) + one README record bullet (status paragraph **unchanged** — no gate state changed) | bounded |

## 4. Decided facts any future gate inherits (facts already decided)

| # | Decided fact | Authoritative source |
|---|---|---|
| 1 | Canonical model = D05 §13 ADOPTED set (layered provenance, field mapping, SecurityIdentity + dated associations, calendar from file-presence with sourced labels, overlay observables + BL/IL disjointness, non-gating flags, opaque FinInstrmId + name-key parsing, CRLF/LF determinism, rupee scale + mandatory provenance note, registry-as-annotation) | D06 Decision A (ADOPTED); D05 §13 |
| 2 | Engine implementation authorized within D07 §13-A scope (non-production) — consumed by W1/W2/M1/M2/I4; `src/nse_engine/` + `tools/i4_runner/` exist and are fingerprint-pinned | D07 §§12–13; M2 revision `8ade8372…` |
| 3 | Logical output contracts (technology-neutral, binding on any future persistence/serving): MD-02 provenance completion; MD-03 evidence envelope (11 logical requirements, incl. #11 deterministic replay evidence); MD-04 deterministic versioned logical output package (no invented vocabulary); MD-05 four logical durability classes; MD-06 content-derived partition rule (explicitly includes "future serving"); MD-07 persistence ownership (engine owns the contract; future persistence must preserve, not reinterpret) | D08 §§4–9 |
| 4 | Store-selection standard: any future storage-technology selection must demonstrably satisfy 7 criteria (deterministic representation/retrieval; provenance preservation; integrity verification; replay/reproducibility; durability per MD-05; corpus-scale operation per MD-06; required downstream consumption per MD-03) | D08 §10 (MD-10) |
| 5 | I4 retained-output contract: 11 logical retained-evidence requirements; no persistence technology implied | D08 §12 (MD-11) |
| 6 | I4 executed and closed: run `i4-20261008-M2` — 2,462 members; 5,689,949 rows; 12 partitions; 0 quarantined; 0 gating divergences (39,402 reconciliation records); package 4,948 files / 21,119,807,344 bytes; manifest digest `e7c7e4c8…`; engine fingerprint `d3269b73…` (17 modules); runner fingerprint `f3ebf624…` (6 modules); corpus archive-set digest `54d81507…`; composite run identity `9609c7fc…`; peak RSS 318.1 MB ≤ 6,144 MB declared limit and ≤ the unchanged 2.5 GB M1 criterion; R6 replay qualification PASS (K1/K2/K3 + G6; R0–R7) | D08 §13 (MD-13); D11 §1/§12; D12 §3 |
| 7 | I4 = CLOSED / DURABLE / REMOTELY VERIFIED; D11 evidence durable on main (`evidence/D11_REPLAY_QUALIFICATION_20261009/`, package SHA256 `8e78fcc8…`) | D12 §9/§11; README status |
| 8 | Replay mechanism sound and unchanged; qualification contract (K1 completeness precondition, K2 revision pin, K3 execution evidence) established and proven; fail-closed by design (exit 2 = finding, never a repair) | D11 §1, §5, §12; `tools/i4_m2/i4_replay_qualification.py` |
| 9 | Runner boundary: non-production; selects no storage technology; exposes no API/UI; no network access; never writes to the corpus; contains no semantics (all transformations in fingerprint-pinned engine) | `tools/i4_runner/README.md` |
| 10 | Environment boundary: Windows = raw custody + full-dataset execution; GitHub = authoritative durable record; Arena = investigation/development/publication; raw archives outside Git, never mutated | README "Environment Boundary" |
| 11 | Content-level traceability boundary: I4 claims content-level traceability under the adopted D05/W1 contract; the unadopted D02 `row_offset`/`raw_row_hash` proposal is a recorded historical mismatch, never claimed | D08 §4.3, §18 |

## 5. Decision-input items (per-item analysis A–H)

For each item: **A.** existing authoritative decision — **B.** current disposition — **C.** blocks
definition of a future gate? — **D.** requires a new authority decision? — **E.** decision owner —
**F.** evidence required for that decision — **G.** dependencies — **H.** what must explicitly remain
deferred.

### 5.1 MD-08 — Serving ownership / runtime environment

* **A.** D08 §16: **DEFERRED BY SEQUENCING** — "no serving layer ownership defined; runtime environment
  still undefined; decision belongs to the future M/N gate." D08 §17 row 7: API/serving authorization =
  **NO**.
* **B.** Deferred. Nothing in the repository serves anything; the runner is non-production with no
  API/UI/serving path (§4.9). The only forward reference is MD-06's logical partition rule, which
  anticipates "future serving" as a partition-contract requirement, not a serving design.
* **C.** No — it is a decision *subject* of a future gate, not a precondition for defining one.
* **D.** Yes — serving ownership (who/what serves the governed outputs) and runtime environment
  (where/under what constraints) must be decided before any serving implementation.
* **E.** Ramki.
* **F.** (i) the 11 MD-03 logical evidence requirements and MD-11 retained-output list (what a consumer
  of serving would need to resolve); (ii) MD-05 durability classes and MD-06 partition contract (the
  serving surface must preserve, not reinterpret); (iii) MD-10's 7 store-selection criteria incl.
  "required downstream consumption (per MD-03 envelope)"; (iv) scale facts (§4.6: 4,948 files /
  21,119,807,344-byte package; 12 partitions; 2,462 members); (v) the environment boundary (§4.10);
  (vi) **the identity of the intended consumer(s) — not documented anywhere in the repository**
  (this is itself an open input; no assumption made here).
* **G.** MD-09 (consumer result contract shapes the served interface), MD-12 (retrieval determinism),
  D07 §9 items (consumer-visible handling of unresolved semantics).
* **H.** All serving design, ownership, runtime selection, and implementation remain deferred until
  decided. No serving code is authorized by this record or any prior record.

### 5.2 MD-09 — Consumer result contract

* **A.** D08 §16: **DEFERRED BY SEQUENCING** — "no consumer result shape/ordering/state/traceability
  exposure frozen." D08 §17 row 7: **NO**.
* **B.** Deferred. In the meantime, the governed consumer obligations **remain binding** (D08 §16
  MD-09): units/provenance note mandatory (D05 §10.2), non-gating flags (D05 §5), no `FinInstrmId`
  identity (D05 §§6–7), no overlay aggregation (D05 §3.5/§11), unknown states displayed, no retroactive
  annotations (D05 §11).
* **C.** No — a decision subject, not a gate-definition precondition.
* **D.** Yes — freezing consumer result shape, ordering, state exposure, and traceability exposure.
* **E.** Ramki.
* **F.** (i) MD-03 envelope items; (ii) the MD-04 versioned-package contract (no invented vocabulary);
  (iii) the current deterministic output layout actually produced by I4 (per-partition + package
  manifests, `GOVERNED_INPUTS.json`, `RUN_RECORD.json`, `RECONCILIATION.jsonl`,
  `w2/unresolved.jsonl` — §4.6/§4.9); (iv) D07 §9 — every consumer-visible field touching an OPEN
  semantic is `null`/flagged by fail-closed design, so any consumer contract must specify how those
  states are exposed; (v) MD-11 #9 (unresolved-state evidence carried, never resolved).
* **G.** MD-08 (serving shape), MD-12 (deterministic retrieval per MD-10 #1), D07 §9 (open semantics
  surface as unresolved states).
* **H.** All consumer-result freezing remains deferred; only the existing D05/D08 obligations bind in
  the meantime. No consumer implementation is authorized.

### 5.3 MD-12 — Storage technology (remains UNDECIDED)

* **A.** D08 §16: **WITHHOLD / NOT AUTHORIZED** — "**STORAGE TECHNOLOGY = UNDECIDED**; no selection, no
  implementation, no ingestion, no deployment." D08 §17 rows 5–6: **NO**. D08 §10 (MD-10): the
  7-criterion store-selection standard is ACCEPTED as a *standard*, with the explicit note that nothing
  "names, ranks, prefers or implies any technology; the names appearing in the repository's fail-closed
  stub remain descriptions of an undecided choice, not candidates."
* **B.** UNDECIDED. Every output contract is deliberately logical/technology-neutral (MD-03…MD-07,
  MD-11: "no physical storage technology is selected or implied").
* **C.** No — unless the future gate's stated purpose is persistence/serving, in which case MD-12 is the
  central decision of that gate (still: defining the gate ≠ selecting the technology).
* **D.** Yes — selection (or continued explicit deferral) requires Ramki's decision against MD-10's 7
  criteria.
* **E.** Ramki.
* **F.** (i) MD-10's 7 criteria (the decision standard); (ii) MD-05 durability classes; (iii) MD-06
  content-derived partitioning; (iv) MD-03 envelope; (v) corpus-scale facts (§4.6); (vi) custody
  boundary — raw archives on Windows, outputs run-scoped on Windows, durable record in Git (§4.10);
  (vii) the D03 §15 CRLF↔LF hash-basis lesson (declared hash bases in-band).
* **G.** Feeds MD-08 and MD-09 (retrieval/consumption depend on a satisfying store); depends on the
  MD-10 criteria (decided) and nothing else strictly.
* **H.** Selection, implementation, ingestion, deployment all remain deferred. No technology may be
  ranked, preferred, or implied by any future document until decided.

### 5.4 MD-17 — UI / API / transport / hosting / exports scope

* **A.** D08 §16: **OUT OF SCOPE** — "remain with their future gates." D08 §17 row 8: **NO**.
* **B.** Out of scope (a distinct deferral class from MD-08/MD-09's "deferred by sequencing").
* **C.** No.
* **D.** Yes — UI design, API style, transport, hosting, exports, and technology naming each require
  decisions when brought into a gate's scope.
* **E.** Ramki.
* **F.** The same input family as §5.1–§5.3, plus any consumer-identity input (§5.1 F vi).
* **G.** MD-08, MD-09, MD-12.
* **H.** All of MD-17 remains deferred. This record invents no UI, API, transport, hosting, or export
  design.

### 5.5 D07 §9 — Nine unresolved canonical semantics (carried OPEN)

* **A.** D06 §8 → D07 §9 → D08 §18 → D12 §10: carried forward **OPEN**, unchanged, at every gate since.
  The nine: (1) T0 volume-inclusion; (2) IT definition/semantics (FROZEN, no authoritative text
  retrieved); (3) SF code (no official definition found); (4) BE rights-entitlement vs T2T row-level
  split (heuristic evidence-only); (5) SGB-STK documentation contradiction; (6) XCONT 83/122 boundary
  residuals (mechanics resolved; policy UNINTERPRETED); (7) `FinInstrmId` namespace (FROZEN opaque
  attribute); (8) three unexplained calendar dates (2024-11-20, 2025-10-20, 2026-01-15 — see also
  §5.8); (9) SME surveillance-stage detail for the corpus era.
* **B.** OPEN/frozen. Engine behavior at each (D07 §9): "represent the observable, carry the
  flag/annotation, and FAIL CLOSED (no default) where a semantic decision would be required." D07
  §13-B lists the code paths blocked by them (fail-closed in code); outputs carry governance-dependency
  annotations (D07 §13-G).
* **C.** No — they do not block *defining* a future gate. They block any **consumer-visible decision**
  that would require resolving them (e.g., a consumer contract that asserts continuity, eligibility,
  or calendar causes).
* **D.** Only if the future gate's scope requires closing (or explicitly re-deferring with stated
  conditions) any of the nine. No closure is required to define a gate.
* **E.** Ramki (decisions); official-documentation retrieval in the D04B pattern may feed evidence.
* **F.** Per item: (1) an official T0 totals statement or further corpus evidence (237/237 lt is
  consistent with both models); (2) authoritative IT text (none retrieved); (3) official SF definition
  (none found); (4) evidence separating BE rights-entitlement from T2T rows (currently heuristic);
  (5) resolution of the D02-era SGB-STK documentation contradiction; (6) a continuity POLICY decision
  for the 83/122 residuals (match storage only until then); (7) a namespace governance decision;
  (8) circulars beyond the obtained set, or an explicit presentation policy (see §5.8); (9) SME stage
  tables covering the corpus era (D04B §1).
* **G.** Item (8) ↔ D05 §3.4 calendar governance; item (7) ↔ D05 §§6–7; item (6) ↔ D03 FIX-XCONT-01
  evidence; items (2)/(3)/(4) ↔ D02-era documentation gaps. Each blocks only its own fail-closed stub.
* **H.** All nine remain OPEN/deferred unless individually decided. No default, no normalization, no
  reinterpretation, no "unblocking by assumption" — D08 §18: "nothing below was resolved,
  reinterpreted, weakened or normalized by this record."

### 5.6 DEC-1 / MD-16 — Master acquisition (remains deferred)

* **A.** D06 Decision B: **DEFERRED**. D08 §16 MD-16: **DEFERRED / UNCHANGED** — "eligibility predicate,
  ETF/master-snapshot association, delisting markers, corporate-action co-location all remain deferred;
  nothing in this record may be used as a back door to resolve them." D07 §8: DEC-1 acquisition, master
  joins, live NSE, credentials, production ingestion NOT authorized.
* **B.** Deferred. No acquisition performed from any environment (D06 §10 no-execution statement;
  D04B §2: Arena fetches HTTP 500 / TLS failure; Windows-side route documented but **optional and not
  started**).
* **C.** No — but it *does* block the five D07 §13-C items (eligibility predicate; ETF-exclusion join;
  master-snapshot dated associations; delisting markers; corporate-action co-location) if a future
  gate wants them in scope.
* **D.** Yes — acquisition authorization, plus the three authority checks on the acquired master:
  (i) provenance capture per file, (ii) consistency test against the corpus, (iii) explicit user
  acceptance of its role (`DEC1_SECMASTER_FEASIBILITY.json.authority_disposition`: "cross-check source,
  not source of truth" until accepted).
* **E.** Ramki (authorization + acceptance).
* **F.** (i) `DEC1_SECMASTER_FEASIBILITY.json` — candidates (`eq_etfseclist.csv` ETF register; monthly
  Masters snapshots), acquisition blockers, the YES-partially feasibility answer, and the recorded next
  step (Windows-side read-only download; record URL/date/sha256 per file; store under a NEW directory
  outside the archive roots; no retro-writes; then bounded join fixture FIX-ETF-JOIN-02); (ii) D03
  consistency facts (7,633 ISINs, zero blanks, the 205 one-sided boundary rows a dated master would
  adjudicate); (iii) the D07 §13-C blocked list.
* **G.** Requires Windows-side execution authority (corpus-environment discipline); independent of
  D07 §9 semantics.
* **H.** Acquisition, joins, eligibility activation, and all §13-C items remain deferred. Feasibility
  documentation in D04B is evidence, not authorization.

### 5.7 W1-DIV-1 — Preserved divergence (ISIN census)

* **A.** Machine-readable governed record: `src/nse_engine/contract.py`
  `KNOWN_EVIDENCE_DIVERGENCES` (id `W1-DIV-1`); carried at D08 §18 and D12 §10.
* **B.** **PRESERVED, not reproduced, not altered.** The D03-era census figure (215,393 rows ~5.4% in
  the D05 §5 parenthetical) was produced by a check-digit routine evaluating the mod-10 sum over ISIN
  characters 2..11 instead of the ISO 6166 body (characters 1..11); on the published sample the ISO
  6166 check finds 0 invalid, the D03-era formula 713, and a known-valid external ISIN (US0378331005)
  is INVALID under the D03-era formula. W1 implements the governed ISO 6166 definition and does not
  reproduce the D03 formula; the D05 §5 count "should be treated as superseded by a future governance
  note." ISIN validity remains informational and non-gating.
* **C.** No.
* **D.** A small governance-note decision: record an evidence-divergence note against D05 §5 (and
  optionally correct the D03 census tool) so the flag's evidence qualifier matches the governed
  definition — the record's own recommendation, explicitly "not part of W1; no re-scan of the corpus."
* **E.** Ramki.
* **F.** Already in the repository: the `W1-DIV-1` record itself; `tests/test_flags_and_validity.py`
  (demonstrates non-reproducibility); `tests/test_published_evidence.py` and `tests/test_w2_integration.py`
  (carry-forward assertions).
* **G.** Standalone (documentation governance, not a semantic; touches no D07 §9 item).
* **H.** The D05 §5 text and all frozen D01/D03 artifacts remain unmodified until the governance note
  is decided; no corpus re-scan of any kind.

### 5.8 Three unexplained calendar dates (2024-11-20, 2025-10-20, 2026-01-15)

* **A.** D04B (CAL labels): 29/32 missing weekdays in the retrieved-circular years explained by
  official notified holidays; these three **unexplained**. D05 §3.4: `official_holiday_label = null`
  with `label_status = "unexplained-by-obtained-circulars"`; legacy era (2016–2023) `not-retrieved`.
  Carried at D06 §8.8, D07 §9.8, D08 §18, D12 §10.
* **B.** `null` / unexplained; "never filled in" (D08 §18). Related both-direction divergences are
  documented (2024-11-01 holiday without file; 2025-10-21 Muhurat session WITH a normal-scale
  3,039-row file — governance rule: file-presence is the trading signal, circulars are labels).
* **C.** No — they block no gate definition. They block any claim of calendar completeness and any
  consumer-visible cause attribution for those dates.
* **D.** Only if (i) circulars beyond the obtained set are retrieved and explain them, or (ii) an
  authority presentation policy is decided. Neither is required to define a gate.
* **E.** Ramki.
* **F.** `DEC2_CAL_LABELS.json`; the obtained circular set (`DEC12_CIRCULAR_REGISTRY.json`); any newly
  retrieved circulars (read-only, D04B discipline).
* **G.** Item (8) of §5.5; D05 §3.4 calendar governance; the file-presence rule.
* **H.** Labels remain `null`; D05 NON-ASSUMPTION: never invent legacy holiday causes; no retroactive
  reinterpretation.

### 5.9 Documented monitor `null` exit-code anomaly

* **A.** D11 §5: "The M2 monitor recorded `runner_exit_code: null` — the documented, non-gating
  anomaly. The gate accepts `0` **and** `null`, records which value was …" K3 test suite: "null exit
  code accepted and recorded."
* **B.** Carried **unchanged, verbatim** (D12 §6.5: "A's runner exit-code `null` anomaly is preserved
  verbatim, never reinterpreted (B: `0`)"). A (original M2 run) = `null`; B (replay) = `0`.
* **C.** No.
* **D.** None required for future work. A future monitor revision that would change the acceptance
  set would be a new correction under the D10/D11 pattern (gate-level, evidence-backed) — no such
  change is proposed here.
* **E.** Ramki, only if a change is ever proposed (none is).
* **F.** Already established: A/B monitor `summary.json` documents (D11 E4), the verdict (R6), and
  D12 §6.5.
* **G.** Standalone documented fact; no dependency.
* **H.** Never reinterpreted; preserved verbatim in all future citations.

### 5.10 Failed `i4-20261007` run and M2/replay evidence roots

* **A.** `i4-20261007` — the first Windows corpus attempt, at `G:\My Engines\I4_RUNS\i4-20261007`,
  failed by memory exhaustion (D09 §1) and is **preserved untouched** (G-I4-M1-CORRECTIVE: never
  re-run, never reused). M2 — the successful bounded-memory run `i4-20261008-M2` (root A) — and its
  replay (root label `i4-20261008-M2-REPLAY`, which per D12 §6.3 is **B's output-root label, not the
  run id**) are fully evidenced: D11 package tar durable on main
  (`evidence/D11_REPLAY_QUALIFICATION_20261009/`, SHA256 `8e78fcc8…`), R6 verdict re-proven,
  closure ratified (D12).
* **B.** Historical evidence only; durably published; Windows roots untouched (D12 §10: "The failed
  run `i4-20261007` and the M2/replay roots on Windows remain untouched evidence").
* **C.** No.
* **D.** None.
* **E.** n/a.
* **F.** n/a — the evidence set (E1–E10) is established and durable; no further capture is required.
* **G.** None.
* **H.** No re-run, no mutation, no reuse of failed-run artifacts, no reinterpretation. These roots
  are inputs to *any* future execution decision (baseline memory facts: the unbounded attempt
  projected ≈40 GB; M2 peaked at 318.1 MB).

## 6. Decision matrix (consolidated)

| Item | Current disposition | Blocks gate *definition*? | New authority decision required? | Owner | Evidence available / required | Key dependencies | Must remain deferred |
|---|---|---|---|---|---|---|---|
| MD-08 serving ownership/runtime | DEFERRED BY SEQUENCING (D08 §16) | No | Yes | Ramki | §5.1 F (incl. consumer identity — undocumented) | MD-09, MD-12, §5.5 | All serving design/implementation |
| MD-09 consumer result contract | DEFERRED BY SEQUENCING (D08 §16); D05 obligations binding meanwhile | No | Yes | Ramki | §5.2 F | MD-08, MD-12, §5.5 | All consumer-result freezing |
| MD-12 storage technology | WITHHOLD / UNDECIDED (D08 §16); MD-10 standard decided | No (central subject if gate targets persistence) | Yes | Ramki | §5.3 F (MD-10's 7 criteria) | feeds MD-08/MD-09 | Selection/implementation/ingestion/deployment |
| MD-17 UI/API/transport/hosting/exports | OUT OF SCOPE (D08 §16) | No | Yes (when scoped) | Ramki | §5.4 F | MD-08, MD-09, MD-12 | All of MD-17 |
| D07 §9 nine OPEN semantics | OPEN, fail-closed, carried unchanged (D06→D12) | No (blocks only consumer-visible decisions needing them) | Only if closure/policy is in gate scope | Ramki | §5.5 F (per-item) | per-item (see G) | All nine unless individually decided; no defaults |
| DEC-1 / MD-16 master acquisition | DEFERRED (D06 B; D08 §16); feasibility documented, not started | No (blocks D07 §13-C items if wanted) | Yes (authorization + 3 authority checks) | Ramki | §5.6 F | Windows-side execution authority | Acquisition/joins/eligibility/§13-C items |
| W1-DIV-1 | PRESERVED divergence (contract.py; D08 §18) | No | Small governance-note decision | Ramki | Already in repo (contract.py + 3 test modules) | Standalone | D05 §5 text + frozen artifacts untouched; no re-scan |
| 3 calendar dates | `null` / unexplained-by-obtained-circulars (D05 §3.4) | No | Only on new circulars or presentation policy | Ramki | §5.8 F | §5.5 item (8); D05 §3.4 | Labels stay `null`; no cause invention |
| Monitor `null` exit anomaly | Documented non-gating anomaly (D11 §5; D12 §6.5) | No | None (change would be a new D10/D11-pattern correction) | Ramki (only if proposed) | Already established (E4 docs, R6) | Standalone | Verbatim preservation; no reinterpretation |
| i4-20261007 + M2/replay roots | Historical evidence, durable, roots untouched (D12 §10) | No | None | n/a | E1–E10 durable on main | None | No re-run/mutation/reuse |

**Register summary.** Decided facts: §4 (11 items). Open decisions: D07 §9 (9 semantics), W1-DIV-1
governance note, 3 calendar dates (decision-pending facts). Deferred decisions: MD-08, MD-09, MD-12,
MD-16/DEC-1, MD-17. Nothing else is open or deferred at the gate level.

## 7. Dependency graph

```
FUTURE NEXT GATE — definition pending Ramki authority (NOT created by this record;
                    I5/M/N remain undefined labels; this graph names no gate)
│
├─ MD-08 serving ownership/runtime ──────┐
│    needs: consumer identity input,     │ depends on
│    MD-03/MD-05/MD-06 (decided), §5.5   ├──────────────────────────────┐
├─ MD-09 consumer result contract ───────┤                              │
│    needs: §4.6 output layout, §5.5     │   MD-12 storage technology ──┤  (if the gate
│    (consumer-visible states)           │   needs: MD-10 7 criteria    │  targets
├─ MD-17 UI/API/transport/hosting ───────┘   (decided), §4.6 scale      │  persistence
│    needs: MD-08, MD-09, MD-12 decisions                                │  /serving)
├─ DEC-1/MD-16 master acquisition ────────── needs: Windows-side execution authority +
│                                           3 authority checks (provenance, consistency,
│                                           user acceptance); blocks D07 §13-C items
└─ D07 §9 nine OPEN semantics ──────────── blocks only consumer-visible decisions;
                                           carried otherwise (fail-closed)
Standalone carried items (no gate dependency): W1-DIV-1 note · 3 calendar dates ·
monitor null anomaly (verbatim) · i4-20261007/M2/replay roots (evidence)
```

No decision in this graph is a precondition for *defining* the gate; each is a potential *subject* of
it. The only hard external dependency for any gate scope involving master data is the Windows-side
acquisition route (DEC-1); the only undocumented input is the consumer identity (MD-08 F vi).

## 8. Open / deferred item register

| Class | Item | Governing record | State |
|---|---|---|---|
| OPEN | T0 volume-inclusion | D07 §9.1 (D06 §8.1) | OPEN — both models consistent with 237/237 lt |
| OPEN | IT definition/semantics | D07 §9.2 | FROZEN — no authoritative text retrieved |
| OPEN | SF code | D07 §9.3 | OPEN — no official definition found |
| OPEN | BE rights vs T2T split | D07 §9.4 | OPEN — heuristic evidence-only |
| OPEN | SGB-STK contradiction | D07 §9.5 | OPEN — D02-era documentation |
| OPEN | XCONT 83/122 residuals | D07 §9.6 | mechanics resolved; policy UNINTERPRETED |
| OPEN | FinInstrmId namespace | D07 §9.7 | FROZEN opaque attribute |
| OPEN | 3 calendar dates | D07 §9.8 / D05 §3.4 | `null` / unexplained-by-obtained-circulars |
| OPEN | SME surveillance-stage detail | D07 §9.9 | OPEN — D04B §1 |
| OPEN | W1-DIV-1 governance note | contract.py; D08 §18 | PRESERVED — note decision pending |
| DEFERRED | MD-08 serving ownership/runtime | D08 §16 | DEFERRED BY SEQUENCING |
| DEFERRED | MD-09 consumer result contract | D08 §16 | DEFERRED BY SEQUENCING |
| DEFERRED | MD-12 storage technology | D08 §16/§17 | WITHHOLD / UNDECIDED |
| DEFERRED | MD-16 / DEC-1 master | D06 B; D08 §16 | DEFERRED / UNCHANGED |
| DEFERRED | MD-17 UI/API/transport/hosting/exports | D08 §16 | OUT OF SCOPE |
| CARRIED (fact) | Monitor `null` exit anomaly | D11 §5; D12 §6.5 | verbatim, non-gating |
| CARRIED (evidence) | i4-20261007; M2/replay roots | D09 §1; D12 §10 | untouched evidence |

## 9. Evidence required for the future authority decision

To decide the next gate's scope, the authority will need (all obtainable read-only from the
repository unless noted):

1. **Scale and contract baseline** — §4 items 3–6 (MD-02…MD-11 contracts; I4 run facts; package/
   manifest/fingerprint pins). *In repository.*
2. **Consumer identity and intent** — who/what consumes the governed outputs, and for what use
   (query, analysis, integration, archival). *NOT documented in the repository — must be supplied
   by the authority as an input; no assumption is made in this record.*
3. **The decision standard already decided** — MD-10's 7 store-selection criteria (D08 §10), so any
   persistence/serving decision is graded against an accepted standard, not an ad hoc one. *In
   repository.*
4. **Per-item decision evidence** — §5.1 F … §5.8 F above (per item). *Mostly in repository; DEC-1
   requires the Windows-side acquisition route to generate new evidence (URL/date/sha256 provenance
   per file; corpus consistency test; then acceptance).*
5. **The carried-open register** — §5.5 (nine semantics, per-item evidence status) and §8, so the
   authority can choose, item by item, to close, re-defer, or leave out of scope, with the
   fail-closed boundary stated for each. *In repository.*
6. **The no-inference ledger** — D08 §17 (authority boundaries) + D12 §10 (carried forward) — the
   explicit list of what prior records do NOT authorize, which the future decision must not silently
   exceed. *In repository.*

## 10. Proposed decision questions for the future authority decision

Drafted for a Ramki authorization sheet in the D08 §2 pattern. **These are questions, not decisions;
each carries a blank decision field. Answering them is the future authority act; this record
pre-authorizes nothing.**

* **Q0 (gate existence and name).** Is a next post-I4 gate to be defined at all, and if so under what
  name and charter? (The label "M/N" exists only as D08 §16's deferral pointer; using it, renaming
  it, or inventing a new label is the authority's choice. I5 remains UNDEFINED and is not offered as
  an option.) *Decision: ____________*
* **Q1 (scope selection).** Which of the following, if any, enter the gate's scope: (a) MD-08 serving
  ownership/runtime; (b) MD-09 consumer result contract; (c) MD-12 storage-technology selection
  against MD-10; (d) MD-17 UI/API/transport/hosting/exports; (e) DEC-1 master acquisition
  (+ the three authority checks); (f) closure or re-deferral of any of the nine D07 §9 semantics;
  (g) the W1-DIV-1 governance note? *Decision: ____________*
* **Q2 (boundary type).** For each selected scope item: investigation-only, decision-record-only, or
  implementation — and the exact non-production boundary if implementation (D07 §13 pattern)?
  *Decision: ____________*
* **Q3 (consumer input).** If (a)/(b)/(d) are in scope: what is the intended consumer and use
  (the repository documents none)? *Decision: ____________*
* **Q4 (semantic handling).** For each D07 §9 item touched by the scope: close (with stated
  evidence), explicitly re-defer (with stated condition), or leave OPEN with the fail-closed stub
  preserved? *Decision: ____________*
* **Q5 (persistence standard).** If (c) is in scope: is MD-10's 7-criterion standard adopted as the
  grading standard for any candidate, with the UNDECIDED status lifted only on a stated selection?
  *Decision: ____________*
* **Q6 (evidence and acceptance criteria).** What evidence, run scope (if any execution is
  contemplated — noting I4's corpus facts and the Windows-only execution boundary), and acceptance
  criteria must the gate produce before closure ratification (D08 §14/§15 pattern)?
  *Decision: ____________*
* **Q7 (non-inference).** Confirm the future decision record will state, as D08 §17 does, exactly
  what it does NOT authorize (so no deferral, OPEN item, or boundary is silently consumed)?
  *Decision: ____________*

## 11. Explicit non-authorizations

This record authorizes **nothing**. In particular:

* NO NEW GATE IS DEFINED OR AUTHORIZED BY THIS INVESTIGATION. No gate is named, chartered, or
  scoped; "future M/N gate" remains a deferral label from D08 §16 and is not adopted here as a
  definition.
* No I5 definition is created, inferred, or referenced as a stage; I5 remains UNDEFINED.
* No M gate or N gate is defined.
* No storage technology is selected, ranked, preferred, or implied; `STORAGE TECHNOLOGY = UNDECIDED`
  stands.
* No persistence, API/serving, UI, transport, hosting, or export implementation is authorized.
* No production ingestion, deployment, live NSE access, provider integration, or credential work.
* No corpus execution, replay, or re-run of `i4-20261007`, M2, or the replay; no modification of any
  engine/runner/`i4_output.py` byte, any corpus file, or any frozen evidence artifact.
* No semantic closure: the nine D07 §9 items, the three calendar dates, W1-DIV-1, and DEC-1 remain
  exactly as carried (OPEN / preserved / deferred / verbatim).
* The proposed questions (§10) are inputs to a future decision; they grant no authority, create no
  obligation, and pre-commit nothing.

## 12. Final disposition

**D13 = RECORDED (investigation only).** This record is decision input for the future Ramki
authority decision that may define the next post-I4 gate. Only that future explicit authority
decision may establish the gate, its name, scope, acceptance criteria, evidence requirements, and
its implementation/investigation boundary.

> ### **NO NEW GATE IS DEFINED OR AUTHORIZED BY THIS INVESTIGATION.**
