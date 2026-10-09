# D14 — I5 Authority Decision: 10-Year Full Qualification Established and Determined

**Gate:** `I5 — 10-year full qualification (qualification-determination gate; no execution scope)`
**Recorded:** 2026-10-09 (Arena side, recording an explicit authority decision).
**Decision authority:** Ramki (application decision authority), via the explicit post-I4
authority-decision directive that commissioned this task ("Perform the explicit post-I4 authority
decision required to reconcile: Historical/original roadmap: I5 = 10-year full qualification, with:
Current repository state: I5 = undefined").
**Decision input record:** `docs/investigations/D13_POST_I4_DECISION_INPUT_INVESTIGATION.md` (D13,
durable at `origin/main` since commit `5db377ed…`).
**This record is an authority/governance act. It is NOT the 10-year execution, and it contains no
execution scope.**

---

## 1. Purpose and strict scope

D13 (investigation only) established the decision inputs and pre-authorized nothing. This record
performs the authority decision D13 §12 reserved to Ramki: it reconciles the original roadmap intent
("I5 = 10-year full qualification") with the authoritative repository state ("I5 = UNDEFINED") and
formally establishes I5 — **only as the evidence supports** (D13 §5/Phase 5 discipline: nothing is
invented; where evidence is silent, the item is marked so, not filled).

**Strict scope (per the directive's hard boundary):** no 10-year execution; no serving/API/UI/
transport/hosting/export implementation; no persistence-technology selection; no deferred technical
question resolved by assumption; no silent promotion of historical planning material; no invented
I5 requirement; no implementation gate created from unresolved items; conversational task labels are
not treated as repository facts (Phase 3 records exactly what the repository does and does not
contain).

## 2. Authority and basis

* The decision is issued under the explicit authority directive quoted in the header; it follows the
  house pattern of D06 (Decision A/B), D07 (§4 verbatim authority), D08 (§2 authorization provenance,
  MD dispositions), D11/D12 (closure ratification conditional on remote verification).
* Evidence considered: **only** artifacts in the authoritative repository at
  `origin/main@5db377ed899ed93ec7805c9c3efd4b3b4ee053ae` (tree `684eb744…`, 141 blobs), read-only:
  D13 (complete, all sections), D08 (§§4–18), D07 (§§8–13), D06 (§§8–11), D04B §2 +
  `evidence/d04/DEC1_SECMASTER_FEASIBILITY.json`, D05 spec (§§3.4/5/10/11/13), D09 §1, D11
  (§1/§5/§11–12), D12 (§2–§3/§6/§9–11), `src/nse_engine/contract.py`
  (`KNOWN_EVIDENCE_DIVERGENCES`), `evidence/D11_REPLAY_QUALIFICATION_20261009/`, README (status,
  evidence baseline), `evidence/inventory/INVENTORY_REPORT.md`, `tools/i4_runner/README.md`.
* No Windows access, no corpus access, no execution, no measurement, no external retrieval occurred
  in preparing or recording this decision.

## 3. Verified baseline (read-only)

| Check | Observed | Verdict |
|---|---|---|
| Authoritative ref | `origin/main` = `5db377ed899ed93ec7805c9c3efd4b3b4ee053ae` ("D13: post-I4 next-gate decision-input investigation…", parent `8105e761…`) | PASS |
| Tree | `684eb744da401b906a0369e89abcd5a187b5d21f`, 141 blobs | PASS |
| I4 state | `I4 = CLOSED / DURABLE / REMOTELY VERIFIED` (D12 §11; README status) | PASS |
| D13 state | D13 = RECORDED (investigation only); durable on main; "NO NEW GATE IS DEFINED OR AUTHORIZED BY THIS INVESTIGATION" | PASS |
| Working tree at publication | clean; only untracked `_transfer_delivery/` (staging, never committed) preserved untouched | PASS |
| Mutation set for this record | exactly 2 paths: this file (new) + README (status-line I5 clause + one record bullet) | bounded |

## 4. Original roadmap reconciliation (repository evidence, not assumption)

**A. Authoritative current repository state.** I4 (the 10-year full corpus run) is CLOSED / DURABLE /
REMOTELY VERIFIED. I5 is UNDEFINED — stated at README status, D12 §10, D13 §1/§11. No next gate is
formally authorized (D13 §1, Task 26 finding).

**B. Historical roadmap / planning intent — what the repository actually contains.**
1. The **10-year scope** is documented in the repository exclusively as **I4's scope**: D08 §13
   (MD-13) — "Authorize the **non-production** 10-year historical corpus replay / full historical run
   under the approved I3 contract" — plus the product/archive naming (README:5 "10-year NSE
   historical market-data engine"; `NSE_CM_UDiFF_10Y` archive; `NSE 10-Year Archive Inventory v2`)
   and the evidenced corpus coverage **2016-09-20 through 2026-09-18** (README evidence baseline;
   `INVENTORY_REPORT.md`).
2. The **I5 label** appears in the repository only as: (i) the **chain terminus** of the I4
   qualification chain — D11 §1 and I4_REPLAY_E2E header: `I4 → replay / E2E determinism
   qualification → I5` (I5 positioned as the stage after the qualification work, scope unstated);
   and (ii) explicit UNDEFINED markers (README status, D12 §10, D13).
3. **No repository artifact states "I5 = 10-year full qualification"**, and the compound "full
   qualification" appears nowhere in the tree. The I# increment sequence has no documented I1…I5
   plan in the tree (D07 defines only GATE-I1; W1/I1, W2/I2, I3, I4 are evidenced as executed
   increments/gates).
4. The **10-year full run's work content is complete in the repository**: executed as
   `i4-20261008-M2` (2,462/2,462 members; 5,689,949 rows; 12 partitions; 0 gating divergences),
   memory-qualified under M2 (peak RSS 318.1 MB ≤ the unchanged 2.5 GB M1 criterion and the 6,144 MB
   declared limit), determinism-qualified by the R6 replay (byte-exact; 4,948 == 4,948 files;
   `first_difference: null`), evidence-qualified (MD-11/E1–E10 durable; package SHA256
   `8e78fcc8…`; D11 remote reconciliation ACCEPT with C.1–C.7 carried), and closure-ratified (D12).

**C. D13 decision inputs.** Q0–Q7 (D13 §10) are the decision surface; D13 pre-authorized nothing.
D13 Q0 explicitly noted the label choice ("M/N… is the authority's choice; I5 remains UNDEFINED and
is not offered as an option") — this decision resolves Q0 by **adopting the existing I5 label**
rather than inventing M/N.

**D. Unresolved technical semantics.** D07 §9 nine OPEN items, W1-DIV-1 (preserved), three calendar
dates (`null`) — all carried fail-closed; none is closed by this record (§8).

**E. Future/deferred work.** MD-08, MD-09, MD-12, MD-16/DEC-1, MD-17 — all remain deferred/out of
scope per D08 §16/§17 (§8); none enters I5 scope.

**F. Actual authority to establish I5.** The authority's explicit directive (header) is the
authority act. This record records it, graded strictly against repository evidence (§5–§7).

**Reconciliation result.** The original intent ("10-year full qualification") is materially
satisfied by completed, durable, independently re-proven I4/M2/R6/D12 work; the only outstanding
matter is the **formal label/governance binding**. The coherent, minimal, non-invented
establishment is: **I5 := the 10-year full qualification, constituted as a qualification-determination
gate over the completed 10-year corpus result** — no new execution scope, because the 10-year full
run is already executed and closed. Defining I5 as a further execution gate would be unsupported
(the execution exists and is closed) and would violate the hard boundary ("do not create an
implementation gate merely because an unresolved item exists"). Defining I5 to include serving/
consumption/product scope would be invention (no repository evidence supports it; D13 §5.1–5.4).

## 5. I5 definition — the minimum authoritative contract

**I5 is ESTABLISHED as follows.** Each item is set only where repository evidence supports it; where
the definition makes an item inapplicable, the reason is stated (not a value invented).

1. **I5 objective.** Formally qualify the **10-year full corpus result** — the complete, non-
   production execution of the governed 10-year archive — and record the authority's qualification
   determination for it. (Basis: §4.B.1 MD-13 scope; §4.B.2 chain terminus; authority directive.)
2. **Qualification scope.** Determination-only: evaluation of the completed run
   `i4-20261008-M2` and its replay against the qualification criteria of §5.7. **No new corpus
   execution, no replay re-run, no re-measurement.** (Basis: §4.B.4; hard boundary.)
3. **10-year corpus/time boundary.** The governed corpus coverage **2016-09-20 through 2026-09-18**
   as evidenced by the archive inventory and README baseline — the "10-year" designation of the
   archive (`NSE 10-Year Archive`; `NSE_CM_UDiFF_10Y`), not a separately measured 3,650-day claim.
   (Basis: `INVENTORY_REPORT.md`; README evidence baseline.)
4. **Required input population/corpus.** The governed 2,462-member corpus (1,919 Legacy + 543
   UDiFF), Windows-custody L0 archives, read-only, corpus archive-set digest
   `54d8150706ccf5d813a6f0af668e8230e147a7e370db20ea15dda1b72bf8b100`. (Basis: README baseline;
   D12 §3.)
5. **Qualification execution boundary.** **There is no I5 execution.** The qualification was
   produced by the already-executed, already-closed gates: I4 (M2 run), M2 memory qualification,
   `verify --package`, R6 replay qualification, D11 remote reconciliation, D12 closure. I5 consumes
   their durable evidence read-only. (Basis: §4.B.4.)
6. **Required outputs.** None new. The qualification record is this document (D14) plus the README
   status update; all underlying outputs already exist and are durable (D11 package, verdict,
   E1–E10, D12 closure). (Basis: D11 §11; D12 §3/§9.)
7. **Acceptance criteria.** The set of **already-decided, already-passed** criteria (no new
   criterion is introduced):
   (i) completeness — 2,462/2,462 members processed, 0 quarantined, 12 partitions, 5,689,949 rows
   (D12 §3); (ii) integrity — `verify --package` PASS (verify-01…verify-07); package manifest digest
   `e7c7e4c8…` (D12 §3); (iii) determinism — R6 replay qualification PASS, byte-exact total
   comparison, 4,948 == 4,948 files, `first_difference: null`, K1 completeness precondition, K2
   revision pin (engine `d3269b73…` 17 modules; runner `f3ebf624…` 6 modules, recomputed from
   executed bytes), K3 execution evidence, G6 path-scan correction (D11; D12 §6.2); (iv) memory —
   peak RSS 318.1 MB ≤ 6,144 MB declared limit **and** ≤ the unchanged 2.5 GB M1 criterion (D12 §3;
   D09/D10; monitor `null` exit-code anomaly carried verbatim, non-gating, D11 §5/D12 §6.5);
   (v) evidence — MD-11 retained-output requirements #1–#11 satisfied; E1–E10 captured and durable
   (`evidence/D11_REPLAY_QUALIFICATION_20261009/`, package SHA256 `8e78fcc8…`); (vi)
   reconciliation — 39,402 reconciliation records, 0 gating divergences; D11 remote reconciliation
   ACCEPT (86-item battery; findings C.1–C.7 carried without suppression); (vii) run identity —
   `i4-20261008-M2` bound in both packages (C.7.3: replay root is B's label, not the run id);
   composite run identity `9609c7fc…`; (viii) traceability — content-level under the adopted
   D05/W1 contract, per D08 §4.3 (the unadopted D02 `row_offset`/`raw_row_hash` proposal is never
   claimed).
8. **Reconciliation criteria.** The D11 reconciliation battery stands as the reconciliation
   standard: E1–E10 artifacts reconciled against the published run; three-source digest
   cross-checks; physical corroboration; C.1–C.7 findings recorded, not suppressed. I5 ratifies
   that reconciliation as the 10-year result's reconciliation evidence. (Basis: D11 §12; D12 §2/§6.)
9. **Replay/determinism requirements.** Satisfied by R6 (D11 K1/K2/K3 + G6; byte-exact; no
   exclusion list; no normalization; verdict outside both packages; fail-closed exit codes).
   **No replay is re-run or required to be re-run by I5.** (Basis: D11 §1/§5/§12.)
10. **Resource/memory requirements.** The unchanged 2.5 GB M1 acceptance criterion and the 6,144 MB
    declared monitor limit, as evidenced by the M2 monitor record (peak 318.1 MB). No new resource
    requirement is introduced. (Basis: D09/D10/D12 §3.)
11. **Evidence requirements.** The durable set: D11 package tar + publication note (SHA256
    `8e78fcc8…`/blob `03d5cbed…`), R6 verdict document (sha `d8e33f13…`), E1–E10, D12 closure
    record, this D14 record. All are on `origin/main`. No new evidence is required or captured.
    (Basis: D11 §11; D12 §9.)
12. **Manifest/hash requirements.** The pins above (manifest `e7c7e4c8…`; fingerprints
    `d3269b73…`/`f3ebf624…`; corpus digest `54d81507…`; run identity `9609c7fc…`; D11 package
    `8e78fcc8…`; verdict `d8e33f13…`) constitute the I5 pin set. No re-hash or re-pin occurs.
    (Basis: D11 §1.1; D12 §3/§6.)
13. **Failure/stop conditions.** Inapplicable at determination (no I5 execution). The fail-closed
    conditions of the constituent gates remain on record and binding for any future execution:
    R6 exit 2 = finding, never repair (D11); I4 stop-past-failed-phase and no-marker-after-governing-
    failure rules (D08 §13 pattern); any future gate that re-runs corpus work must stop and report
    on any verification failure. (Basis: D11 §5/§12; D08 §13.)
14. **Prerequisites.** All satisfied before this decision: I4 execution closed (D12); R6 PASS (D11);
    D11 reconciliation ACCEPT; D11 evidence durable on main; D13 decision inputs recorded. **No
    outstanding prerequisite.**
15. **Dependencies that must remain unresolved before execution.** There is no I5 execution, so
    nothing is "unresolved before execution"; for completeness and non-weakening, the carried
    register stands **unchanged**: D07 §9 nine OPEN semantics (fail-closed), DEC-1/MD-16 deferred,
    MD-12 UNDECIDED, W1-DIV-1 preserved, three calendar dates `null`, monitor `null` anomaly
    verbatim (D13 §8; D12 §10). **None is closed, reinterpreted, or consumed by I5.** The I5
    qualification claim is explicitly **content-level under the adopted D05/W1 contract** (D08
    §4.3) and makes no claim that depends on any of them.
16. **Explicit exclusions / non-goals.** I5 is NOT: a new or second corpus run; a replay; a
    product/serving/consumption readiness statement; a storage-technology decision; an API/UI/
    transport/hosting/exports decision; a semantic-closure act; a DEC-1 act; an M or N gate; any
    production/credential/live-NSE activity; any modification of engine/runner/`i4_output.py`,
    corpus files, or frozen evidence. I5 authorizes no downstream use of the data beyond what the
    D05/D08 contracts already state. (Basis: D08 §16/§17; D12 §10; D13 §11.)
17. **Authority boundary.** I5 authorizes exactly one thing: the recorded qualification
    determination over the completed 10-year corpus result, and the label binding
    "I5 = 10-year full qualification". It authorizes nothing else (§9). Only a subsequent explicit
    authority decision may establish any further gate (the D08 §16 "future M/N gate" remains a
    deferral label for that purpose).

## 6. Qualification determination (graded against §5.7, from durable evidence only)

| # | Criterion (source) | Recorded result | Durable evidence |
|---|---|---|---|
| i | Completeness 2,462/2,462, 0 quarantined, 12 partitions, 5,689,949 rows (D12 §3) | MET | D12 §3; RUN_RECORD (E8) |
| ii | `verify --package` PASS; manifest `e7c7e4c8…` (D12 §3) | MET | D12 §3; E2/E7 |
| iii | R6 replay qualification PASS — byte-exact, 4,948 == 4,948, `first_difference: null`, K1/K2/K3, G6 (D11; D12 §6.2) | MET | D11 §12; verdict `d8e33f13…`; D12 §6 |
| iv | Memory: 318.1 MB ≤ 6,144 MB declared and ≤ 2.5 GB M1 criterion; `null` anomaly carried verbatim (D11 §5; D12 §3/§6.5) | MET | E4/E5 monitor documents; D12 §6.5 |
| v | MD-11 retained evidence #1–#11; E1–E10 durable (D11 §11) | MET | `evidence/D11_REPLAY_QUALIFICATION_20261009/` (`8e78fcc8…`) |
| vi | Reconciliation: 39,402 records, 0 gating divergences; D11 reconciliation ACCEPT; C.1–C.7 carried without suppression (D12 §2/§6) | MET | D12 §2/§6 |
| vii | Run identity `i4-20261008-M2` both packages; composite `9609c7fc…` (D12 §3/§6.3) | MET | D12 §3; E3/E8 |
| viii | Content-level traceability boundary (D08 §4.3) | MET (claim scoped as decided) | D08 §4.3; D12 §3 |

**Carried findings (non-suppressed, per D12 §6):** (1) recorded `repo_head` differs from the
declared executed revision — revision identity enforced from executed bytes (RQ-04/05), A == B held;
(2) E7/E8 single-copy justified by proven A/B whole-tree byte identity; (3) replay root is B's
output-root label, not the run id; (4) A's Phase-I facts re-captured during R5; (5) A's exit-code
`null` anomaly preserved verbatim (B: `0`); (6) residual operator-attestation boundary carried.
None of these fails a criterion; all are recorded here as part of the qualified result, without
suppression or reinterpretation.

> ### **DETERMINATION: 10-YEAR FULL QUALIFICATION = PASS.**
> The 10-year corpus result (run `i4-20261008-M2`, corpus 2016-09-20 through 2026-09-18, 2,462
> members) **meets every qualification criterion in §5.7**, each from durable, independently
> re-proven evidence on `origin/main`. I5 = 10-year full qualification is thereby **achieved**.

**Closure condition (house pattern, D08 §15 / D12 §9):** I5 is ratified **only after** remote
verification of this publication (commit, tree, artifact, reachability from `origin/main`, exact
delta). Until then: `I5 = RECORDED — ratification pending remote verification`. Upon success:

> ### **I5 = CLOSED / DURABLE / REMOTELY VERIFIED**

## 7. Q0–Q7 reconciliation (D13 §10 → this decision)

| Q | D13 question (abridged) | Disposition in this decision | Classification |
|---|---|---|---|
| Q0 | Next gate — exist? name? | **YES — established as I5** (existing chain-terminus label adopted; M/N labels not used, not defined), chartered as the 10-year full qualification, determination-only | **ESTABLISHED** |
| Q1 | Scope items (a)–(g)? | **None enter I5 scope.** I5 = determination over the completed 10-year result. (a) MD-08, (b) MD-09, (c) MD-12, (d) MD-17, (e) DEC-1, (f) nine-semantic closure, (g) W1-DIV-1 note: all remain exactly as carried (§8) | **ESTABLISHED** (scope fixed); (a)–(g) each **OUT OF SCOPE** for I5 |
| Q2 | Boundary type per item | Determination-only: decision-record-only boundary; no investigation beyond D11/D12-established evidence, no implementation, no execution | **ESTABLISHED** |
| Q3 | Consumer identity (if (a)/(b)/(d) in scope) | Not applicable to I5 (no consumption in scope); consumer identity remains an undocumented input for any future serving gate | **OUT OF SCOPE** for I5; **DEFERRED** beyond I5 |
| Q4 | Semantic handling (close / re-defer / leave OPEN) | All nine **left OPEN** with fail-closed stubs preserved; I5's claim is content-level (D08 §4.3) and requires no closure | **ESTABLISHED** (leave OPEN); no new decision required |
| Q5 | MD-10 as persistence grading standard | Not applicable to I5 (no storage in scope); MD-10 standard stands; `STORAGE TECHNOLOGY = UNDECIDED` unchanged | **OUT OF SCOPE** for I5; **DEFERRED** beyond I5 |
| Q6 | Evidence/acceptance criteria before closure | Fixed to the already-decided, already-passed criterion set (§5.7/§6); closure = this record + remote verification (D08 §14/§15, D12 §9 pattern) | **ESTABLISHED** |
| Q7 | Non-inference ledger in the decision record | Applied: §8 (deferred items untouched) + §9 (authority NOT granted) state exactly what is not authorized | **ESTABLISHED** (applied in this record) |

## 8. Disposition of D13-listed areas (required for I5? prerequisite? independent? deferred?)

| Item | Relation to I5 | Disposition (unchanged unless stated) |
|---|---|---|
| MD-08 serving ownership/runtime | **Independent of I5** (not required, not a prerequisite) | **DEFERRED beyond I5** — future gate (D08 §16 pointer stands) |
| MD-09 consumer result contract | Independent (I5 makes no consumption claim) | **DEFERRED beyond I5**; D05 consumer obligations remain binding meanwhile |
| MD-12 storage technology | Independent (no persistence in I5) | **DEFERRED beyond I5**; `STORAGE TECHNOLOGY = UNDECIDED` unchanged |
| MD-17 UI/API/transport/hosting/exports | Independent (no serving surface in I5) | **DEFERRED beyond I5** (out of scope, D08 §16) |
| D07 §9 nine OPEN semantics | **Not prerequisites** — I5's content-level claim (D08 §4.3) requires none of them; they are not resolved | Remain **OPEN**, fail-closed, carried unchanged; closure only by future explicit decision with stated evidence |
| DEC-1 / MD-16 master acquisition | Independent (eligibility/master work not in I5) | **DEFERRED beyond I5**; acquisition not started; three authority checks stand |
| W1-DIV-1 governance note | Independent (documentation governance) | Remains **PRESERVED**; note decision pending; D05 §5 text and frozen artifacts untouched |
| Three calendar dates (2024-11-20 / 2025-10-20 / 2026-01-15) | Not required — I5 makes no calendar-completeness or cause-attribution claim | Remain `null` / `unexplained-by-obtained-circulars`; never filled in |
| Monitor `null` exit-code anomaly | Carried fact inside the qualified evidence (criterion iv) | **Verbatim, non-gating** — no reinterpretation |
| `i4-20261007` + M2/replay roots | Evidence inputs to the determination (used read-only) | **Untouched**; no re-run, no mutation, no reuse |

## 9. Authority granted / NOT granted

**Granted by this record (exhaustive):**
1. The label binding **I5 := 10-year full qualification** (reconciling the original roadmap intent
   with the repository; §4).
2. The **qualification determination PASS** over the completed 10-year corpus result, graded per
   §6, effective upon remote verification of this record (house closure pattern).
3. Nothing else.

**NOT granted by this record (exhaustive; misinterpretation prevention):**
* **I5 authorization does NOT authorize serving, API, UI, transport, hosting, exports, or
  persistence work of any kind** (MD-08/MD-09/MD-12/MD-17 remain deferred/out of scope; D08 §16/§17
  stand). "Qualified 10-year corpus result" is a data-execution qualification, **not** a product,
  serving, or consumption-readiness statement.
* I5 does NOT authorize any storage-technology selection; `STORAGE TECHNOLOGY = UNDECIDED`.
* I5 does NOT authorize production ingestion, deployment, live NSE access, provider integration, or
  credential work.
* I5 does NOT authorize any corpus execution, replay, re-run, or re-measurement (including of
  `i4-20261007`, M2, or the replay roots).
* I5 does NOT close, reinterpret, weaken, or normalize any D07 §9 semantic, the three calendar
  dates, W1-DIV-1, DEC-1, or the monitor `null` anomaly.
* I5 does NOT modify engine, runner, or `i4_output.py` bytes, any corpus file, or any frozen
  evidence artifact.
* I5 does NOT create, define, or authorize any M gate, N gate, or any other next gate; the D08 §16
  "future M/N gate" remains a deferral label for a future, separately authorized gate.
* No deferral, OPEN item, or boundary from any prior record is silently consumed by this record.

## 10. Resulting disposition

**D14 = RECORDED.** Upon successful remote verification of this publication:

> ### **I5 = 10-YEAR FULL QUALIFICATION — QUALIFICATION DETERMINATION: PASS.**
> ### **I5 = CLOSED / DURABLE / REMOTELY VERIFIED.**

I5 ratification is claimed **only after** that verification passes (verifying commit SHA and tree
hash reported in the publication report, D08 §14 / D12 §9 pattern). No execution task results from
I5: the 10-year full run is already executed and closed (I4), and I5 contains no execution scope.
The next gate after I5 (if any — serving/consumption/persistence per the D08 §16 deferral) is
**not** established by this record and requires a separate explicit authority decision.

> ### **NO SERVING, API, UI, PERSISTENCE, PRODUCTION, SEMANTIC, OR EXECUTION AUTHORITY IS GRANTED BY THIS RECORD.**
