# D21 — D16-03a PERMANENT CHANGED-CONTENT DISPOSITION AUTHORITY DECISION

## 1. Title / identifier

**D21** — Permanent authority decision for **D16-03a (changed-content disposition)**: an archive whose governed archive identity/date is unchanged but whose content (byte SHA-256) differs from the previously accepted content. Supersedes D16-03a's interim status (EVIDENCE REQUIRED / quarantine-from-automatic-processing default) **as to the permanent disposition only**; D16-03's classification semantics and all other D16 decisions stand unchanged.

## 2. Status

**D16-03a = RESOLVED** — a permanent disposition is established by this authority decision, made against the D20 controlled-test evidence (R1–R4) per D18/D19. This record is a governance/authority decision only: NO implementation, NO registry/schema implementation, NO serving/API/UI change, NO canonical-data mutation, NO test execution, NO D20 rerun.

## 3. Date

2026-10-09.

## 4. Scope

Defines, at the architecture/governance level and permanently: the classification of same-identity/different-content archives; their disposition; the authority of previously accepted canonical data; the durable registry-information requirements for the CHANGED state; serving visibility and trust semantics for the unresolved state; the requalification/changed-content distinction; the semantic-equivalence determination; and the boundary for any future resolution of an actual CHANGED conflict. It does not implement anything, select any technology, or authorize any implementation.

## 5. Authority boundary

This record is the future authority decision that D16-03a reserved ("decided by a future authority decision when and only when a changed archive actually presents" — D16 §7 D16-03a; the controlled presentation was supplied by D19's authorization and D20's execution). It binds as permanent governance authority over the changed-content disposition. It does **not** expand implementation authority: D16 §15/§20 ("IMPLEMENTATION AUTHORITY = NOT GRANTED") stand verbatim; the D16-13 later-authority enumeration is updated only by (a) marking item 3 (D16-03a) as RESOLVED by this record and (b) adding the single new item "resolution of an individual CHANGED conflict instance" (§22).

## 6. Baseline identity (verified before decision)

| Item | Value |
|---|---|
| `origin/main` (remote-verified) | `ba6bc956be1a1bdce6c69ca0ebfe487b1cf80707` = D19 — exact match with expected; D20 intentionally **not** promoted |
| Session branch `arena/9021d1a1-nse-historical-data-engine` | `6782c6bf43db214ffa57ffb3d5bc9bfc61197003` = D20 |
| D20 commit / parent | `6782c6b…` / parent `ba6bc95…` (= D19) — chain intact |
| D20 artifact (session branch) | `docs/investigations/D20_CHANGED_CONTENT_CONTROLLED_TEST_EVIDENCE.md`, blob **`82a7248487e5daa68d0d25c478fd7fa027d2d715`** (21,910 B) — verified unchanged |
| D19 on main | blob `6e588304026128cfd93fd9839a6debe315cd948d` (22,798 B) — verified |
| Local state | 11th sandbox `.git` rollback at start; repaired non-destructively (unshallow → ancestry YES → `update-ref` → `read-tree`); D20/D19 worktree blobs verified; worktree clean except pre-existing untracked `_transfer_delivery/` |

## 7. Governing records (read and reconciled)

1. **Intent** — `docs/product/HISTORICAL_ENGINE_PRODUCT_AND_SERVING_ARCHITECTURE_INTENT.md` (blob `41ad2740…`, SHA-256 `7e4a14f4…`): §6 (changed content "must **not** be silently treated as an ordinary duplicate"; "The precise disposition for changed content remains a future contract/governance question. Possible outcomes could include explicit conflict, reprocessing, replacement/versioning, or quarantine, **but this document does not select one**"); §7 (version awareness: "seen before" ≠ "permanently valid under every future contract"); §12 (single-user simplicity).
2. **D15** — (blob `79157b82…`): serving ABSENT (§13); environment boundary — raw bytes in Windows custody (§15 #15); data-backing mapping (§14).
3. **D16** — (blob `1b6e2faf…`): D16-02 (registry content contract: identity, content sha256, result, version bindings, run provenance, status processed/pending/flagged; single authoritative "processed under"; updated only by approved publication); D16-03 (classification: NEW / UNCHANGED / **CHANGED** = never unchanged, never silently reprocessed, prior result stays intact, held as flagged finding; **D16-03a = EVIDENCE REQUIRED**, interim quarantine-from-automatic-processing default); D16-04 (processed = content × version bindings; staleness = deterministic registry census); D16-05 (incremental publications never requalify the baseline; derived state re-derived, never re-processed); D16-07 (four durable-state classes; (1) qualified baseline **immutable**; (4) serving state pure derivation; conflict rule: (1)/(2)/(3) beat (4)); D16-08 (five-class exposure; raw content NOT by default); D16-09 (serving read-only; invariants); D16-10 (Q1–Q10 incl. Q8 quality views, Q9 archive inventory + registry status); D16-13 (six later-authority items; IMPLEMENTATION AUTHORITY = NOT GRANTED); §13 non-goals.
4. **D17** — (blob `3eef98b8…`): D16-03a = EVIDENCE REQUIRED, gaps G1–G4.
5. **D18** — (blob `e1e7cab0…`): G1 NOT ESTABLISHED / G2 NOT ESTABLISHED / G3 PARTIALLY ESTABLISHED / G4 PARTIALLY ESTABLISHED; residual requirements **R1** (concrete same-identity/different-content byte pair), **R2** (semantic-equivalence definition only if a chosen outcome depends on it), **R3** (post-disposition registry record shape), **R4** (prior-data authority / serving visibility / trust statement); controlled synthetic test determined necessary, isolable, and not performed.
6. **D19** — (blob `6e588304…`): disposition **A — AUTHORIZED — NARROW CONTROLLED TEST**; authorized scope items 1–5; explicit exclusions; canonical-data protection invariants; AUTHORITY TO RUN A CONTROLLED TEST explicitly distinguished from IMPLEMENTATION AUTHORITY.
7. **D20** — (blob `82a72484…`): the controlled-test evidence (§11 below).

## 8. D16-03a question

For an archive with unchanged governed identity/date but different content from the previously accepted content: what is the **permanent** disposition — in particular (per D16-03a and the intent's candidate list) explicit conflict, reprocessing, replacement/versioning, or quarantine — and what are the permanent rules for prior-data authority, registry representation, serving visibility, and trust?

## 9. D18 residual requirements R1–R4 (status as decided)

| Requirement | D18 status | Status at D21 |
|---|---|---|
| R1 — concrete same-identity/different-content evidence | missing (G1) | **SATISFIED** by D20 (synthetic controlled instance — see §11/§12) |
| R2 — semantic-equivalence definition, only if the outcome depends on it | missing (G2) | **NOT REQUIRED for the permanent disposition** (§20); future path only |
| R3 — post-disposition registry representation | partial (G3) | **SATISFIED as a durable-information requirement** — the required durable information is fixed by §17; physical schema remains an implementation detail (no schema designed or implemented) |
| R4 — prior-data authority / serving / trust statement | partial (G4) | **SATISFIED** by the governing rules fixed in §16 and §18 |

## 10. D19 authorization (consumed, not reopened)

D19 authorized exactly five scope items (isolated synthetic B1/B2 creation; test-scoped seed/observation state; test-scoped classification/disposition observation; R1–R4 evidence capture; preservation of test evidence), with explicit exclusions and canonical-data protection invariants. D20 executed within that scope (D20 §2/§4/§14/§18). D19 granted no implementation authority; none was exercised. That authorization is **consumed and closed** by this decision; nothing in D21 reopens D19 or D20.

## 11. D20 evidence reconciliation (verified against the D20 artifact)

**R1 — ESTABLISHED (synthetic only).** Governed identity I = root `LEGACY`, archive `d20SYN01JUL2024.csv.zip`, member `d20SYN01JUL2024.csv`, date `2024-07-01`. B1: archive SHA-256 **`8ea4dae41d2a783cb5bc2e9d662765584dbc4d458b5fff99965c7fc855738400`**, member **`27ed18b6…951d`**; B2: same identity field-by-field, deliberate content change (row-2 SYMBOL `SYM1→SYMX`), archive SHA-256 **`1f3f8f5dd4d0dfc943f6c8a15b313b83d7472d921fe1e4c97095b929af033122`**, member **`ea2524f8…32`**; identity equality established field-by-field; `hashes_differ: true`; byte-pair evidence preserved and hash-pinned.

**Runtime observation (existing, unmodified I4 mechanics).** S2 (B2 under identity I, expectation stale at B1): preflight **PF-12** (Tier A, **gating**) — expected `8ea4dae4…` vs observed `1f3f8f5d…` → **DIVERGENCE** → `RUN FAILED` (exit 2). `s2_out/` contained **only** `PREFLIGHT.jsonl` + `RUN_FAILED.json` — no replacement output, no `RUN_COMPLETE`. I.e., the existing pinned-corpus mechanics **block** a same-identity/different-content presentation fail-closed, before any processing. The incremental classifier/registry do not exist as code (contract-only), so the CHANGED classification observation was a **documented derivation of the D16-03 contract semantics** against the test-scoped state — labeled as such, and so treated here.

**R2 — NOT REQUIRED FOR THE TEST.** No semantic-equivalence framework was authorized or established; none was needed.

**R3 — PARTIALLY ESTABLISHED (6/8).** The D16-02 field ingredients directly represent: archive identity; prior content SHA; current content SHA (as a second entry); processing status/result; version binding; run provenance. They do **not**, by themselves, represent: an explicit CHANGED-specific disposition state (status set is processed/pending/flagged); an explicit relationship to the prior accepted state (pairing implicit via identity). No production registry/schema exists.

**R4 — HOLD observed.** Prior package/output **byte-identical** after B2 presentation (15-file digest manifests equal); **no replacement output**; **no invalidation/supersession mechanism exists** (D05 append-only; D18 G4 sweep); **no serving implementation exists** (D15 §13 — fact, not invented result); **no trust/status marker implemented or specified**. D20 explicitly distinguishes observed behavior from permanent policy.

**Isolation (D20 §14).** Final protected-artifact comparison **identical** (405/405 worktree files digest-identical; D01 inventory, M2 package staging, all I4/I5 evidence, source, docs unchanged); no real archive reprocessed; no replacement/supersession occurred; the only initial discrepancy was 26 git-ignored `__pycache__` byproducts, rectified and re-verified (attestation PASS, full audit trail preserved).

**Reconciliation statement:** D20 provides the concrete instance (R1), the observed fail-closed runtime behavior, the prior-data integrity fact, and the precise R3/R4 observations that D18 said cannot be obtained from existing durable evidence. It supports — but by itself does not establish — a permanent policy: **this record makes the permanent governance decision explicitly** (§14). What is *authoritative* (this record's rules) is distinguished throughout from what is *merely observed* (D20 runtime facts).

## 12. Evidence limitations (binding on this decision)

1. The D20 instance is **synthetic**; no real changed archive has ever occurred in this repository (D18 G1 negative proof stands). The decision is therefore made against a controlled instance, which is exactly the condition D16-03a reserved ("when and only when a changed archive actually presents") as supplied by D19's authorized controlled presentation.
2. The incremental classification observation is a documented contract-derivation (the classifier is contract-only); the runtime observation is the existing single-run mechanics' fail-closed halt. Neither is an executed production incremental path.
3. D20 observed the **hold state** only; no resolution of a CHANGED conflict has ever been observed (none has ever existed). The resolution boundary in §22 is a governance rule, not an observed behavior.
4. No serving implementation exists; §18's serving semantics are the governing rules for the serving layer D16-08/09/10 already fixed (they do not describe an existing implementation).
5. This decision consumes D20 as evidence; it does not re-run, re-measure, or reinterpret D20.

## 13. Candidate disposition analysis (per D16-03a's reserved candidate set, evaluated against the actually established evidence)

| Candidate | Determination | Basis |
|---|---|---|
| **Automatic reprocessing** | **REJECTED as permanent automatic behavior** | Intent §6 (never silently treated as an ordinary duplicate); D16-03 (never silently reprocessed over the prior result); the qualified baseline and every incremental publication are qualified against **exact pinned bytes** with hash-pinned evidence (M2/D11/D14 discipline; R6 byte-exact rebuild equivalence is a property of identical bytes + versions, not of different bytes); D20 runtime shows the existing mechanics block, not reprocess; reprocessing different bytes under the prior record's provenance would corrupt canonical-data integrity and the evidence chain |
| **Automatic replacement / versioning (supersession)** | **REJECTED as permanent automatic behavior** | D20 R4: no replacement output was produced and **no supersession/invalidation mechanism exists**; D05 rows are append-only per observed with no supersession/invalidation rule; D16-07 class (1) is immutable and (1)/(2)/(3) beat (4); silent replacement would void the qualification, reconciliation, and provenance of the previously accepted bytes; the product is a historical record — what a file contained on a date is a fact to be recorded, not a blob to be overwritten |
| **Terminal automatic quarantine (permanent exclusion)** | **REJECTED as an automatic terminal outcome** | No evidence establishes that a changed archive is to be permanently excluded or disposed; D20's observed behavior is a **hold** (block), not a terminal exclusion; the repository's existing "quarantine" concept is row-level parse failure (different scope); making exclusion automatic would be a terminal policy the evidence does not support and the intent does not mandate |
| **Explicit conflict + permanent fail-closed hold** | **ADOPTED as the permanent disposition** | The intent's first candidate; mandated by the non-silence obligation (intent §6); fully consistent with the D16 architecture (immutability of (1); registry as single authoritative record; serving as pure derivation; conflict rule) and with every D20 observation (prior data byte-identical and intact; no replacement output; fail-closed block; prior data remains the only canonical state); it makes the interim hold **explicit and permanent as an unresolved state with a durable conflict record**, while keeping every terminal outcome (accept / reject / reprocess / replace) available through the per-instance resolution boundary (§22) — inventing nothing the evidence does not support |

No policy element below is chosen because it is conventional: each is either (a) mandated by the adopted intent (non-silence), (b) required by the D16 architecture or an existing contract (immutability, append-only, registry single-writer, serving derivation, conflict rule), (c) established by the D20 evidence, or (d) the minimal fail-closed governance rule the D16-03a authority decision was reserved to fix (conflict recording, hold, resolution boundary).

## 14. Permanent D16-03a decision

> ### **PERMANENT DISPOSITION OF CHANGED CONTENT: EXPLICIT CONFLICT + PERMANENT FAIL-CLOSED HOLD, WITH PRIOR-DATA AUTHORITY PRESERVED AND PER-INSTANCE RESOLUTION BY FUTURE EXPLICIT AUTHORITY DECISION.**
>
> An archive whose governed identity/date matches a previously accepted archive but whose content SHA-256 differs is a **CHANGED archive** and constitutes an **explicit, durable conflict** against the previously accepted record. It is (and remains, until an explicit resolution decision) **held out of all automatic processing and out of all canonical serving**; it **never** silently becomes "already processed", "unchanged", or "reprocessed"; it **never** replaces, supersedes, or invalidates the previously accepted canonical result; and the previously accepted canonical data **remains authoritative, intact, and fully in force** (and fully visible through serving) for as long as the conflict is unresolved. The conflict — and the relationship between the changed candidate and the prior accepted record — **must be durably recorded in the registry** (§17). Resolution of the conflict (acceptance, rejection, reprocessing, replacement-versioning, or a documented alternative) is possible **only through a future explicit authority decision** for that instance (§22).

The D16-03 interim default (quarantine from automatic processing) is hereby **confirmed as the permanent behavior for the unresolved state**, and is hereby given its explicit semantics: the hold is not a silent quarantine but a **recorded, explicit, durable conflict** — the "flagged" state becomes the governed **CHANGED-CONFLICT-UNRESOLVED** state of §17.

## 15. CHANGED classification semantics (permanent)

- **CHANGED** = apparent governed identity matches a registry entry (or the previously accepted record for that identity) **and** content SHA-256 differs from the entry's recorded content SHA-256. The classification is deterministic and content-identity-governing (D16-03 stands).
- **Answer to decision point 3 — may changed content ever be silently accepted as UNCHANGED? NO. Never.** A CHANGED archive is never classified UNCHANGED, under any binding, in any run, by any future implementation. (Intent §6 + D16-03, now permanent.)
- **Answer to decision point 4 — may changed content be silently reprocessed? NO. Never.** Reprocessing of a CHANGED archive's content is never automatic or silent; it can occur, if ever, only as the **outcome of an explicit resolution decision** for that instance (§22), with its own run identity, publication, and evidence.
- **Compound case (explicit):** if the prior entry's version bindings are also stale (D16-04) **and** the content differs, the **content axis governs**: the archive is classified **CHANGED** (an explicit conflict), and the binding staleness is recorded alongside in the registry entry (§19). Staleness alone (same content, changed bindings) is **not** a conflict.

## 16. Prior canonical-data authority (permanent)

**Answer to decision point 6:** while a CHANGED conflict is unresolved, the previously accepted canonical data **remains authoritative, intact, and fully in force** — D20 observed this (byte-identical prior output, no replacement, no invalidation), and this record fixes it as governing rule. Its qualification/evidence chain (which is a chain over **its bytes**) stands untouched. The mere existence of a conflicting candidate **does not** invalidate, downgrade, retract, or mark the prior data: a conflict is a finding about the **candidate and the pair**, not an established defect in the prior data. If a future resolution decision finds the prior data defective or superseded in any sense, that finding — and any consequent marking — belongs to **that** authority decision and to no default. After resolution, the prior data's authority is whatever the resolving decision explicitly states; absent that statement, the default is unchanged (prior data stands).

## 17. Registry-state requirements (durable information only — NO schema, NO implementation)

**Answer to decision point 8 (and the R3 gaps).** Any future implementation of the D16-02 registry must be **capable of durably representing**, for a CHANGED archive:

1. **An explicit CHANGED-specific disposition state** — distinct from the generic `flagged`: a state expressing **CHANGED-CONFLICT-UNRESOLVED**, and, after a resolution decision, **CHANGED-CONFLICT-RESOLVED** carrying a reference to the resolving authority decision and its outcome. (D20's observed test-scoped state used `flagged` + a test-observation note; the permanent requirement is that the disposition state itself be first-class.)
2. **An explicit relationship to the prior accepted record** — the changed entry must durably record which prior accepted entry it conflicts with: the prior identity, the prior content SHA-256, the prior result reference (partition/contribution/publication), and the prior entry's run provenance. The pairing must not depend on an implicit identity match alone. (Closes D20's second R3 gap.)
3. **The observed new content SHA-256** of the candidate (already representable in the D16-02 content contract — D20: criterion met).
4. **The discovering run's provenance** (which run/scan observed the changed content).
5. **The version-binding context at discovery** (whether the prior entry's bindings were applicable — relevant to the compound case of §15).
6. **For the resolved state:** the reference to the resolving authority decision, the outcome (accept / reject / reprocess / replace-versioning / documented alternative), and any consequent statements on the prior data's authority.

This is a **durable-information requirement** on any future implementation (what it must be capable of representing); it does **not** design, select, or implement a schema, storage format, or technology (MD-12 and TECHNOLOGY = UNDECIDED stand; the physical registry format remains an implementation detail of a future implementation authorization).

## 18. Serving / trust semantics (permanent)

**Answer to decision point 9:** while the conflict is unresolved, the previously accepted canonical data **remains fully visible and queryable** through the serving layer exactly as authoritative canonical data (serving reflects durable classes (1)+(2)+(3); the prior data sits in them; nothing removes or hides it — D16-07/09; D20 R4 at the state-class level).

**Answer to decision point 10:** the changed candidate **is not eligible for canonical serving before explicit resolution**. It is never served as canonical historical data; it is visible only as a **processing/quality finding** — the conflict record and its registry status — within the D16-08 exposure classes (processing metadata; data-quality views Q8; archive inventory + registry status Q9; evidence views Q10). Raw candidate bytes remain excluded per D16-08 (Windows custody; environment boundary).

**Answer to decision point 11:** trust/status semantics for the unresolved CHANGED state: (a) the previously accepted data **retains the authority and trust it had at acceptance** — its qualification is over its bytes, and the conflict does not mark it; no trust-downgrade or status marker is applied to prior data by the mere existence of a conflict, and introducing one would itself require a future authority decision; (b) the changed candidate carries an explicit, durable status — **CHANGED-CONFLICT-UNRESOLVED: not canonical; not for canonical serving; held** — that is visible through the Q8/Q9/Q10 exposure classes; (c) the conflict finding itself is durably visible as a quality/processing record (consistent with D16-10 Q8's quarantined/unresolved-state views). These are governing rules for the serving layer D16 already fixed; no serving implementation exists (D15 §13), and this record authorizes none.

## 19. Requalification semantics (explicit distinction — decision point 12)

The two cases are **distinct concepts** and must not be collapsed:

- **STALE (D16-04 — version axis):** the **same content** (identical content SHA-256) under a **changed** engine/contract/version binding. The entry is stale by deterministic registry census (no execution); its results may not serve under the new contract until the archive is **reprocessed and re-validated under the new bindings** (requalification). No conflict is involved; the bytes are identical; provenance updates through a new publication. D16-04's applicability condition and its deferred migration mechanism stand exactly as D16 fixed them.
- **CHANGED (this decision — content axis):** the **same identity** under applicable (or identical) bindings but **different content**. Explicit conflict; permanent fail-closed hold; no automatic reprocessing; prior data stays authoritative. Resolution only by explicit authority decision (§22).
- **Compound:** stale **and** changed → the content axis governs the classification (**CHANGED conflict**, §15); the staleness is recorded in the entry; the conflict is resolved by the per-instance authority decision, which may then direct reprocessing under new bindings as part of the resolution.

## 20. Semantic-equivalence determination (decision point 13)

**Semantic equivalence is NOT required by the permanent disposition.** The permanent conflict/hold semantics are defined entirely at the byte-identity level (content SHA-256), consistent with D16-03's byte-level classification and D20's R2 result (no semantic-equivalence work was needed). **No semantic-equivalence capability exists in the repository** (D18 G2: NOT ESTABLISHED), and this record claims none. If a **future** resolution decision selects a path conditioned on semantic equivalence (e.g., accepting a changed archive as a corrected re-issue of "the same data"), then (a) a governed definition of semantic equivalence for this corpus and (b) the capability to apply it are **future evidence/capability requirements** requiring their own explicit authority decision first — marked here as a future requirement, not an existing capability.

## 21. Replacement / supersession / reprocessing determination (decision point 14)

- **Replacement / supersession:** no automatic replacement or supersession is established or permitted. A changed candidate never replaces or supersedes the previously accepted canonical result. (D20 R4: no such mechanism exists or was produced; D05 append-only; D16-07 (1) immutability.)
- **Reprocessing:** no automatic reprocessing is established or permitted (§15).
- **Both remain possible outcomes of a future explicit per-instance resolution decision** (as is acceptance, rejection, or a documented alternative) — the intent's four candidates stay available as resolution paths; D21 fixes the **unresolved state**, not the terminal menu. Any resolution that changes canonical data must itself follow the house pattern (explicit authorization → scoped change → its own run identity/publication/evidence → verification) and must state the prior data's consequent authority.

## 22. Future-change authority boundary

- **D16-13 item 3 (D16-03a): RESOLVED by this record.**
- **New later-authority item:** **resolution of an individual CHANGED conflict instance** — when a CHANGED archive is held (in test or in a real incremental run), deciding what happens to it (accept / reject / reprocess / replace-versioning / documented alternative), including any statements on the prior data's authority and any registry/derived-state consequences. This is a per-instance governance decision, not an implementation task.
- **Future capability requirement (not a gap):** the semantic-equivalence definition/capability of §20, only if a future resolution path is conditioned on it.
- **Unchanged:** all other D16-13 items (first-release implementation authorization; incremental-ingestion implementation authorization; requalification migration mechanism; MD-12; raw-content serving) stand exactly as D16 fixed them. D14's non-authorizations stand.

## 23. Implementation authority boundary (decision point 15)

**D21 grants NO implementation authority.** It establishes permanent architecture/governance authority over the changed-content disposition only. D16 §15/§20 stand verbatim: serving/API implementation may NOT begin; incremental-ingestion implementation may NOT begin; persistence implementation may NOT begin; UI implementation may NOT begin. The §17 registry-state requirements are **contract content** for any future incremental-ingestion implementation (its governing contracts are now D16-01–06 + D16-02 + **D21 §14–§19**); they authorize no store, no format, no code. TECHNOLOGY = UNDECIDED stands (MD-12). No registry/schema/implementation of any kind was created, modified, or implied by this record.

## 24. Product-scope / non-goal preservation (decision point 16)

Single-user personal-use scope preserved. D16 §13 non-goals stand unchanged: no authentication; no RBAC; no multi-user support; no PostgreSQL; no enterprise deployment/identity infrastructure; no tenant isolation; no organization/team administration; no distributed architecture; no implementation libraries/frameworks selected or implied; no rerun of I4 or I5; no modification of the qualified dataset or existing engine behavior; no authority expansion beyond this record. This decision introduces no technology of any kind.

## 25. Residual gaps

**None blocking D16-03a's resolution.** R1 satisfied (D20); R2 not required (§20); R3 satisfied as a durable-information requirement (§17); R4 satisfied (§16/§18). Standing boundary facts (not gaps): (a) no real changed archive has ever occurred (D18 G1) — the first real instance, if it occurs, is handled under this decision's rules and resolved under §22; (b) the incremental classifier/registry remain contract-only until implementation authorization; (c) the physical registry schema remains an implementation detail; (d) the semantic-equivalence capability does not exist and would require a future authority decision if ever needed.

## 26. Closure determination

> ### **D16-03a = RESOLVED.**
> The permanent changed-content disposition — **EXPLICIT CONFLICT + PERMANENT FAIL-CLOSED HOLD with prior-data authority preserved, explicit durable conflict recording (§17), prior data fully visible and the candidate excluded from canonical serving (§18), the version-axis/content-axis distinction fixed (§19), semantic equivalence determined not required (§20), and per-instance resolution reserved to future explicit authority (§22)** — is established by this record against the D20 evidence. Closure is not manufactured: every rule is traceable to (a) the adopted intent's non-silence mandate, (b) the D16 architecture and existing contracts (immutability, append-only, registry single-writer, serving derivation, conflict rule), or (c) the D20 evidence, with the explicit-conflict/hold/resolution-boundary governance rule being precisely what D16-03a reserved to a future authority decision once a changed archive presented (the controlled presentation supplied by D19/D20).
>
> **D21 = COMPLETE / DURABLE / REMOTELY VERIFIED** (subject to the remote verification record in §27).

## 27. Artifact inventory / verification record

**This record:** `docs/architecture/D21_D16_03A_CHANGED_CONTENT_DISPOSITION_AUTHORITY_DECISION.md` (the only mutation of this task).
**Governing inputs (verified §6):** intent (blob `41ad2740dd01620e547fc5a4659cafd53f28d534`, SHA-256 `7e4a14f4e6fd667d415b7351b58a266c5f0f15d494ba903fd132a15222830096`); D15 (blob `79157b82355caf7579ec63b126a23e1a133b79ba`); D16 (blob `1b6e2faf9bdf7cdd6da0210f0ebb48c1d2109b5c`); D17 (blob `3eef98b8f24bdc7a0fade56d32d4a2d1e7370b99`); D18 (blob `e1e7cab083c03c8d732578b0d07fe03f35c81636`); D19 (blob `6e588304026128cfd93fd9839a6debe315cd948d`); D20 (blob `82a7248487e5daa68d0d25c478fd7fa027d2d715`, session commit `6782c6bf43db214ffa57ffb3d5bc9bfc61197003`).
**D20 evidence package (test root, preserved, not re-run):** `/home/user/d20_controlled_test/` — 53 files, `manifest.sha256` (test run `D20-CCT-20261009`); designation TEST-ONLY / NON-CANONICAL / D20.
**Baseline at decision time:** `origin/main` = `ba6bc956be1a1bdce6c69ca0ebfe487b1cf80707` (D19); session branch = `6782c6bf43db214ffa57ffb3d5bc9bfc61197003` (D20). D20 and this record (D21) are on the session branch only; promotion of the D20+D21 chain to main is a separate later activity.
**Verification record:** pre-mutation baseline verification (§6); D20 artifact verified unchanged (blob `82a72484…`); candidate analysis against the actually established evidence (§13); post-mutation remote verification to be recorded in the task's final report (commit, parent = D20, D20 blob intact, D21 blob, cumulative delta from D19 = exactly the D20 + D21 artifacts, worktree state).
