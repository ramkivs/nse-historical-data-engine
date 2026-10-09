# D23 — FIRST-RELEASE SERVING IMPLEMENTATION AUTHORITY DECISION

## 1. Title / identifier

**D23** — The explicit first-release serving implementation authority decision identified by **D16-13 item (1)** ("first-release implementation authorization (read-only serving + first-release UI, contract = D16-08/09/10/11/12)") and confirmed **ready for decision** by **D22** (determination: "IMPLEMENTATION AUTHORITY READY FOR DECISION"; prerequisites D22 §12 entirely authority content). This record is a governance/authority decision only: NO implementation, NO serving/API/UI/persistence code, NO technology selection, NO registry, NO migration, NO resolution mechanism, NO canonical-data mutation.

## 2. Status

**DECISION = GRANTED WITH EXPLICIT BOUNDARIES/CONDITIONS** — first-release serving/application implementation authority is granted, bounded to the D16-12 first-release scope, under the contracts of D16-08/09/10/11/12 + D16-07 + D21 §14–§19, under the technology-selection delegation and binding constraints of §12–§14 (no concrete technology selected), under the D21 and canonical/engine safety constraints of §15–§16, and subject to the closure-evidence requirements of §18. This record itself authorizes no implementation activity; it is the instrument under which a future, separate first-release implementation activity may proceed.

## 3. Date

2026-10-09.

## 4. Authority boundary

This record is the "later explicit authority decision for a stated scope" that D16 §20 required ("Implementation may begin only under a later explicit authority decision for a stated scope (§7 D16-13(5)), following the house pattern of decision input → explicit authorization → scoped implementation → evidence → remote verification"). It discharges D16-13 item (1) and D22 §12 prerequisites (1)–(3) — the authorization decision itself, the bounded handling of technology selection, and the scope restatement that delegated operation (a) stays out. It does **not** discharge D16-13 items (2)–(6) or D21 §22's per-instance item, all of which remain separate future authority decisions (§19). D14's non-authorizations stand unchanged.

## 5. Authoritative baseline (verified before decision)

| Item | Value |
|---|---|
| `origin/main` (remote-verified) | `665f6b34e484cdc5a68f6db4fb4783e88f870511` = D21 — **exact match with expected baseline**; D20 + D21 jointly promoted; D16-03a RESOLVED on main |
| Session branch `arena/9021d1a1-nse-historical-data-engine` | `4224f4e12467fdea912b36b548f5a6abf34a8e38` = D22 (NOT promoted — remains unpromoted by this decision) |
| D22 artifact (session branch) | `docs/investigations/D22_FIRST_RELEASE_SERVING_IMPLEMENTATION_READINESS_INVESTIGATION.md`, blob `962cda5579774f42ba10e837bdcc8fc87c6a6934` (27,900 B) — verified present at session HEAD |
| D21 on main | blob `d1c127bddf0ad2b4405fe0abb50063ec212b9739` (32,455 B) — verified unchanged |
| D16 / intent | blobs `1b6e2faf9bdf7cdd6da0210f0ebb48c1d2109b5c` / `41ad2740dd01620e547fc5a4659cafd53f28d534` — verified unchanged |
| Local state | 13th sandbox `.git` rollback at start; repaired non-destructively (unshallow → ancestry YES → `update-ref` → `read-tree`); worktree clean except pre-existing untracked `_transfer_delivery/` |
| Negative searches at baseline | zero serving/API/UI/persistence/registry/frontend code (151 tracked files; no `web`/`ui`/`frontend` trees) — implementation has not begun |
| M2 baseline identifiers (as recorded in D12/D14/D15) | package `i4-20261008-M2`; 4,948 files / 21,119,807,344 bytes; manifest `e7c7e4c8…`; engine `d3269b73…`; runner `f3ebf624…`; corpus `54d81507…`; composite run identity `9609c7fc…`; R6 verdict `d8e33f13…`; I4: 2,462 members, 5,689,949 rows, 12 partitions, 0 gating divergences |

## 6. Decision authority / source records (re-verified at baseline)

1. **D16** `docs/architecture/POST_I5_SERVING_INCREMENTAL_PRODUCT_ARCHITECTURE_AUTHORITY_DECISION.md` — D16-07 (persistence classes), D16-08 (serving dataset), D16-09 (responsibility boundary + invariants), D16-10 (Q1–Q10 + saved queries), D16-11 (UI boundary + two delegated operations), D16-12 (first-release scope), D16-13 (controlling non-grant + later-authority enumeration), §13 non-goals, §14 (TECHNOLOGY = UNDECIDED), §15/§20 — all re-read verbatim at baseline.
2. **D21** `docs/architecture/D21_D16_03A_CHANGED_CONTENT_DISPOSITION_AUTHORITY_DECISION.md` — §14 (permanent disposition), §15 (CHANGED semantics), §16 (prior-data authority), §17 (registry-state requirements, contract-only), §18 (serving/trust semantics), §22 (per-instance authority item), §23 (no implementation authority), §24 (non-goal preservation) — re-read verbatim at baseline.
3. **D22** `docs/investigations/D22_FIRST_RELEASE_SERVING_IMPLEMENTATION_READINESS_INVESTIGATION.md` — §4 (contract verification), §5/§6 (canonical-source + Q1–Q10 readiness), §7 (delegated operations), §8 (UI), §9 (persistence), §10 (D21 implications), §11 (no blocking gaps), §12 (prerequisites), §13 (determination) — re-read at baseline.
4. **Intent** `docs/product/HISTORICAL_ENGINE_PRODUCT_AND_SERVING_ARCHITECTURE_INTENT.md` — adopted unmodified by D16 §4; §5/§8/§9/§10 (boundaries), §12 (single-user simplicity), §16 (lifecycle), §17.
5. **D05/D08/D12/D14 + I4/M2 evidence** — the canonical-model consumer obligations (MD-07/MD-09/MD-10/MD-12) and qualification evidence on which D16/D21/D22 rely; durable, hash-pinned, verified at baseline.

## 7. Decision statement

> ### **DECISION: GRANTED WITH EXPLICIT BOUNDARIES/CONDITIONS.**
> First-release serving/application implementation authority is **GRANTED**: authority to implement the first release defined by **D16-12** — read-only serving + presentation over the qualified M2 baseline — under the contracts **D16-08/09/10/11/12 + D16-07 + D21 §14–§19**, under the technology-selection delegation and binding constraints of §12–§14, under the safety constraints of §15–§16, and subject to the closure-evidence requirements of §18. Incremental ingestion/processing, changed-content resolution, requalification, raw-content serving, and every item in §19 remain **withheld** and are separate future authority decisions.

Grounds for the grant (evidence, not technical possibility):
- (a) the first-release architecture is fully decided and verified (D16-08/09/10/11/12; D16-07; D21 §14–§19) — D16 §7, D22 §4;
- (b) every first-release data need is backed by durable, qualified, hash-pinned artifacts (D15 §14; D12/D14) — D22 §5/§6;
- (c) no blocking evidence gaps exist (D22 §11);
- (d) the only open architecture item (D16-03a) is RESOLVED on authoritative main (D21 §14/§26);
- (e) D22's determination is IMPLEMENTATION AUTHORITY READY FOR DECISION, and its complete prerequisite list (§12) consists entirely of authority content discharged by this record: (1) the explicit authorization decision — §7; (2) technology selection within/alongside the authorization — §12–§14 (delegated within bounded criteria, recorded at implementation); (3) scope restatement that delegated operation (a) stays out — §8.

## 8. First-release scope (authorized — bounded to D16-12 + D22)

**Authorized** (exhaustive):
- **Read-only serving over the qualified M2 baseline** (plus any approved incremental publication present at implementation time; none exists as of this decision — if one appears, it is served under the identical contracts, never under looser ones).
- **Presentation/application consumption** of served data: the D16-12 Dashboard tiles (run identity/status, archive count, canonical rows, identity records, calendars, errors, rows by year, archives by exchange segment, data coverage, archive inventory + details, reconciliation summary) and the Data Explorer, all from durable data classes (1)–(3).
- **Query categories Q1–Q10** (D16-10) — semantic scope fixed; nothing beyond them (§10).
- **Saved queries + query history** (D16-10; D22 E2: READY BY EXISTING CONTRACT) as serving state class (4); single-user; mechanism = implementation detail.
- **Serving-state rebuild** as delegated operation (b) (D16-09/11; D22 §7: within first-release scope, contract-sufficient) — a user-initiated, serving-boundary-executed maintenance operation, never a query side effect.

**Withheld from this authority** (binding; restated, not re-decided, per D16-12/D22 §12(3)):
- **Delegated operation (a) — archive discovery/processing trigger: OUT of the first release** (D16-12 excludes incremental-processing operations).
- **Incremental ingestion/processing implementation** (D16-13 item (2); contract D16-01–06 + D16-02 + D21 §14–§19).
- **Requalification workflow / migration mechanism** (D16-13 item (4)).
- **Changed-content resolution workflow or mechanism of any kind** (D21 §22 per-instance authority; §15).
- **Raw archive content serving** (D16-13 item (6); D16-08 class 5).
- **DEC-1/eligibility features** (DEFERRED — D16-10).
- **Any expansion of canonical write-path ownership** (D16-09: the engine remains owner of the write path).

## 9. Serving data boundary (D16-08 adopted/confirmed)

D16-08's exposure boundary is **adopted verbatim as the binding serving-data contract** for the first release:
1. **Canonical historical data — MAY be exposed:** partition canonical rows (verbatim-published fields + non-gating flags), identity/association data, calendar (with `label_status`; the three unexplained dates displayed as unexplained — never filled in), metrics — subject to the D05 consumer obligations (MD-09).
2. **Provenance/evidence — MAY be exposed:** per-record provenance blocks (D05 §8), `INPUT_MANIFEST` records, reconciliation records, unresolved-state records, preflight records, run identity/fingerprints, package manifests/hashes, qualification records, registry entries (if any exist).
3. **Processing metadata — MAY be exposed:** partition definitions, registry status + version bindings, per-archive processing facts, incremental run records.
4. **Operational metadata — MAY be exposed (minimal single-user form):** run status, what was processed when under which run, error/finding records. No multi-user operational concepts.
5. **Raw archive content — NOT included by default:** raw bytes remain in Windows corpus custody (environment boundary); a future explicit decision plus a cross-environment mechanism would be required (withheld — §19).

First-release scoping fact (D22 §5/§6, confirmed): in an M2-only first release, classes (2)/(3) are absent/empty; serving reads class (1) plus (2)/(3) only if approved publications/registry entries exist — it never fabricates (2)/(3) content. **Relationship to D21 (confirmed, §15):** prior accepted data stays fully visible and authoritative; a CHANGED candidate is never canonical-serving-eligible while unresolved; no CHANGED state can exist in an M2-only first release, and the implementation must not create a path by which one could become serving-eligible.

## 10. Query boundary (D16-09/10 confirmed)

- **D16-09 confirmed verbatim:** the serving/query layer is a **read-only consumer** of (1)+(2)+(3); owns query execution, result shaping, and derived serving state (4); it **never invokes or schedules** historical processing and **never treats (4) as a source of truth**. D16-09's invariants are binding: a query never mutates durable data; a processing run never reads (4) as input; a query failure can never corrupt (1)–(3); a processing failure leaves (4) at its last approved publication state.
- **D16-10 confirmed:** **Q1–Q10 + saved queries/query history** constitute the complete first-release semantic query scope, each category data-backed by verified existing artifacts (D15 §14).
- **Serving remains read-only; the engine remains owner of the write path.**
- **Arbitrary query semantics outside the Q1–Q10/saved-query boundary are NOT authorized:** no eligibility/DEC-1 queries; no computed analytics beyond as-published values + derived state; no raw-byte serving.

## 11. UI boundary (D16-11 confirmed)

D16-11 is **confirmed verbatim**:
- **The UI may own:** presentation, navigation, query construction (Q1–Q10), result display, status/evidence display, report presentation, user interaction, saved-query management.
- **The UI must not own:** parsing, classification, processing, validation, evidence generation, publication, registry mutation, derived-state re-derivation, or direct access to durable data (always via serving). **It must not own engine state or silently introduce a new persistence/write path.**
- **Delegated operations the UI may expose** (explicit user-initiated invocations of their owning boundary): (a) archive discovery/processing trigger — **not available in the first release** (§8); (b) serving-state rebuild trigger — **in scope** (§8). Everything else is read-only through serving.
- **Target presentation:** the demonstrated I4 application (D16 non-drift #12; mockups out-of-repo — D15 §14). Concrete presentation remains implementation-level detail bounded by D16-12's scope; no screens are specified by this decision.

## 12. Persistence / read-model authority

- **D16-07's logical boundary is confirmed verbatim and binding:** exactly four named classes with fixed owners; class (4) serving/derived state is **always a pure derivation of (1)+(2)+(3)**, rebuildable at any time with no loss — **deleting (4) is never a data event**; conflict rule: if (4) ever disagrees with (1)/(2)/(3), (1)/(2)/(3) win and (4) is rebuilt.
- **This decision DELEGATES the physical selection of class-(4) serving state** (serving store/read-model) to implementation, under the bounded criteria of §13. This delegation discharges D22 §12(2) for the serving store as an **exercise of the D16-13 item (1) gate authority** (D22 §12(2): the authorization gate "makes the scoped technology choices against established contracts"; MD-12 lineage graded by MD-10 under single-user simplicity).
- **MD-12 remains OPEN for every physical concern other than class-(4) serving state** (canonical/qualified-baseline persistence; registry storage format; ingestion-scheduler/archive-watcher mechanism). This decision selects, names, ranks, or implies **no** store or format.
- Class (4) must remain physically and logically **distinct** from (1): serving persistence never absorbs, shadows, or reinterprets the qualified baseline (D16-07, preserved).

## 13. Technology-selection delegation and boundary (decision: DELEGATED)

D23 decides **option 1 — technology selection is DELEGATED to implementation within bounded criteria** for every technology selection within the authorized scope (serving store/read-model; query mechanism; frontend/presentation technology; hosting/runtime).
- **No concrete technology is selected, named, ranked, or implied by this decision.** The governing evidence selected none (D16 §14: TECHNOLOGY = UNDECIDED for every physical concern; D21 §24), and this decision does not fill a blank.
- **Binding constraints on every selection (all mandatory):**
  1. **Single-user/personal-use scope** (intent §12 simplicity principle: durability, correctness, deterministic processing, queryability, provenance, evidence).
  2. **No authentication, no RBAC, no multi-user or tenant architecture** (D16 §13 non-goals).
  3. **No PostgreSQL or other enterprise/production database or deployment architecture unless separately authorized** (D16 §13).
  4. **Serving read-model consistency** with D16-07/D16-09 ownership and boundaries: class (4), pure derivation, rebuildable, never a source of truth.
  5. **Canonical data must not be reinterpreted or mutated** (MD-07: a persistence implementation must preserve the governed output, provenance, evidence, determinism and durability contracts — it may not reinterpret, re-derive, mutate, or extend them).
  6. **Rebuildable serving state:** always derivable from the authoritative source data (1)+(2)+(3); deletion/rebuild is never a data event.
  7. **If a physical persistence technology is selected, it is graded against MD-10's 7 criteria under the single-user simplicity constraint** (D16-07), and the grading is recorded (§18 item 3).
  8. **Recording:** every selection is recorded in the implementation record with its constraint-compliance rationale (§18 item 3).
  9. **No live market-data access:** the serving/application operates against the durable qualified baseline (plus any approved publication); live NSE/provider access of any kind is outside this authority (incremental ingestion is withheld — §8/§19).
- A proposed selection that cannot satisfy a constraint is **out of this authority**; a conforming alternative selection or a separate authority decision is required.

## 14. Hosting / frontend / query-mechanism boundary

Bounded implementation-level selections for **hosting/runtime**, **frontend/presentation technology**, and **query mechanism** are **delegated under this authority** (same constraints as §13; no separate authority gate), with:
- **Hosting/runtime:** single-user, personal hosting/deployment; no enterprise deployment/identity infrastructure; no multi-tenant; the serving runtime operates against the local qualified M2 baseline (plus any approved publication) with no live market-data access.
- **Frontend:** bounded by D16-11/12 (Dashboard tiles + Data Explorer Q1–Q10 + saved queries); target intent = the demonstrated I4 application.
- **Query mechanism:** semantics fixed by D16-10; no query-engine semantics beyond Q1–Q10/saved queries; serving stays read-only.
- Each selection is recorded at implementation time with its constraint-compliance rationale (§18 item 3).

## 15. D21 changed-content constraints (binding on the implementation)

The first-release implementation **must preserve D21 in full**:
- **CHANGED is permanently content-identity-governing** (D21 §15): identity matches, content SHA-256 differs ⇒ CHANGED; the classification is never silently overridden.
- **CHANGED-CONFLICT-UNRESOLVED is fail-closed** (D21 §14): the candidate is held out of all automatic processing **and out of all canonical serving**; it never silently becomes "already processed", "unchanged", or "reprocessed".
- **Candidate content is NOT canonical-serving-eligible while unresolved** (D21 §18): it is never served as canonical historical data; it is visible only as a processing/quality finding within the D16-08 exposure classes (Q8 data-quality views; Q9 archive inventory + registry status; Q10 evidence views).
- **Prior canonical data remains authoritative, intact, fully in force, and fully visible** (D21 §16/§18); it **retains the authority and trust it had at acceptance** — no marker, downgrade, retraction, or hiding is applied to prior data by the mere existence of a conflict.
- **No silent reprocessing; no silent replacement/supersession** (D21 §15/§21): reprocessing of a CHANGED archive, if ever, only as the outcome of an explicit per-instance resolution decision.
- **Per-instance resolution requires future explicit authority** (D21 §22).
- **D23 authorizes NO implementation of changed-content resolution** — no resolver, no resolution workflow, no registry disposition machinery (D21 §17's registry-state requirements are contract content for a future incremental-ingestion implementation, which is withheld — §19).
- **Path prohibition:** in an M2-only first release no class-(3) content exists, so no CHANGED state can occur; the implementation must not introduce any data path, state, or operation by which changed candidate content could become canonical-serving-eligible.

## 16. Canonical-data and engine safety constraints (binding on the implementation)

The first-release implementation is **explicitly prohibited** from:
- **mutating D01/M2 canonical historical data** (class (1) is immutable — D16-07; no component may mutate, re-derive, or re-qualify it);
- **changing D05 semantics** (field contract, as-published values, non-gating flags, §8 provenance, calendar `label_status` treatment);
- **changing identity semantics** (`SecurityIdentity`/`DatedAssociation` append-only; ISIN a non-identity attribute; no `FinInstrmId` identity);
- **changing qualification results** (D11/D12/D14 records; I4/I5 determinations);
- **changing I4/I5 evidence** (byte-pinned artifacts, fingerprints, manifests, R6 verdict);
- **rewriting historical archives** (raw corpus remains in Windows custody; never rewritten, repaired, or normalized from any environment);
- **silently reprocessing existing qualified data**;
- **introducing a second canonical source of truth** (class (4) is a derivation, never authoritative — D16-07/09).

No implementation under D23 may modify D16, D21, D22, D05, D08, D12, D14, the intent record, or any I4/I5 evidence; any change to a governing contract requires its own future authority decision.

## 17. Explicit implementation authority: granted vs withheld (limit statement)

**GRANTED by D23 (exhaustive):** implementation of (a) the first-release read-only serving/query layer over the qualified M2 baseline (D16-12; contracts §9/§10); (b) the first-release presentation/UI within D16-11/12 (target intent: the demonstrated I4 application); (c) serving state class (4) (indexes/rollups/saved-query store), rebuildable per D16-07; (d) serving-state rebuild as delegated operation (b) (D16-09/11; D22 §7); (e) the technology selections of §13/§14, made within bounded criteria and recorded.

**WITHHELD by D23 (exhaustive):** incremental ingestion/processing implementation (D16-13 item (2)); requalification migration mechanism (D16-13 item (4)); per-instance CHANGED conflict resolution and any resolution mechanism (D21 §22); raw archive content serving (D16-13 item (6)); any alteration of the historical engine, canonical data, or governing contracts; any scope change away from single-user. **These authorities are not automatically bundled together:** authority to implement the first-release serving/application architecture ≠ authority to alter the historical engine ≠ authority to perform incremental ingestion ≠ authority to resolve CHANGED conflicts. Each withheld item requires its own future explicit authority decision under the house pattern.

## 18. Implementation evidence / closure requirements (binding on any implementation acting under D23)

A first-release implementation is closed **only** by evidence of the following (no test counts, tolerances, or implementation details are invented here — the implementation record states them):
1. **Authoritative source/repo/ref** — repository, branch, and commit lineage of the implementation.
2. **Baseline identity** — the qualified M2 baseline identifiers it serves (package/manifest/engine/runner/run identities as recorded in §5) verified unchanged.
3. **Technology decisions recorded** — each §13/§14 selection, its constraint-compliance rationale, and the MD-10 grading (item 7) where a physical persistence technology was selected.
4. **Contract conformance** — D16-08/09/10/11/12, D16-07, D21 §14–§19, D05 consumer obligations (MD-09), demonstrated against the implementation.
5. **Canonical-data immutability proof** — pre/post digests of the qualified baseline and I4/I5 evidence: no mutation.
6. **D21 changed-content handling proof** — no data path, state, or operation by which changed candidate content is canonical-serving-eligible; prior-data visibility and at-acceptance trust preserved.
7. **Deterministic/rebuildable serving state proof** — rebuilding class (4) from the authoritative source data (1)+(2)+(3) reproduces the served content; deletion/rebuild is never a data event.
8. **Query-boundary proof** — serving executes only Q1–Q10 + saved-query semantics; no other query path exists.
9. **UI boundary proof** — the UI reads only through serving; no direct durable-data access; no engine-state ownership; only delegated operation (b) is exposed.
10. **Tests** — the implementation's test suite passes under the repository's established test discipline; the record states the suite, runner, and results.
11. **Complete artifact inventory** — every implementation artifact with path and digest.
12. **Remote durability + independent remote verification** — commit/tree/blob/path verified against the remote per house discipline; prior governing blobs (D16/D21/D22/intent/D05/D08/D12/D14) intact.

Failure of any item ⇒ the implementation is not closed; the gap is reported, not papered over.

## 19. Explicitly excluded / deferred authority (remains open)

- **Incremental ingestion/processing implementation** — D16-13 item (2); contract = D16-01–06 + D16-02 + D21 §14–§19.
- **Per-instance CHANGED conflict resolution** — D21 §22 (new later-authority item): accept / reject / reprocess / replace-versioning / documented alternative, including any statements on prior-data authority.
- **Requalification migration mechanism** — D16-13 item (4); first version change.
- **MD-12 physical concerns other than class-(4) serving state** — canonical/qualified-baseline persistence, registry storage format, ingestion-scheduler/archive-watcher mechanism (D16-13 item (5), as narrowed by §12).
- **Raw archive content serving** — D16-13 item (6); requires a future explicit decision **plus** a cross-environment mechanism.
- **DEC-1/eligibility features** — DEFERRED (D16-10).
- **Any single-user scope change** (multi-user, authentication, RBAC, enterprise architecture, tenant isolation, distributed architecture) — D16 §13/§16.
- **D14 non-authorizations** — stand unchanged.
- **Promotion of D22 to main** — the user's separate step; not performed or implied by this decision (D22 remains on the session branch).

## 20. Non-drift statement

D23 does **not** modify, reinterpret, or re-open any decision in D16, D21, D22, D05, D08, D12, D14, D15, D17, D18, D19, D20, or the intent record. It discharges exactly D16-13 item (1) and the D22 §12 prerequisites by (1) explicit authorization (§7), (2) bounded technology delegation with recorded constraints (§12–§14), and (3) scope restatement that delegated operation (a) stays out (§8). D23 grants no implementation activity within this record: zero code, zero schema, zero registry, zero migration, zero serving/API/UI/persistence artifact, zero test is created by D23. No technology is selected, named, ranked, or implied. No canonical data, package, inventory, or evidence artifact was touched (read-only inspection; worktree verified clean except pre-existing untracked `_transfer_delivery/`). Single-user personal-use scope and all D16 §13 non-goals preserved. The only mutation is this artifact.

## 21. Artifact inventory

- **This record:** `docs/architecture/D23_FIRST_RELEASE_SERVING_IMPLEMENTATION_AUTHORITY_DECISION.md` (exactly ONE new artifact; no other file changed; no README change).
- **Consumed (verified, unmodified) at baseline:** D16 (blob `1b6e2faf…`); D21 (blob `d1c127bd…`); D22 (blob `962cda55…`); intent (blob `41ad2740…`, SHA-256 `7e4a14f4…`); D05 spec, D08 (MD-02…MD-17), D12, D14; I4/M2 evidence (§5 identifiers).
- **Not created by this record:** serving code, API, frontend, persistence, registry, migration, changed-content resolution mechanism, tests, or any implementation artifact of any kind.

## 22. Verification record

Pre-decision (this task): baseline verified (§5) — `origin/main` exactly `665f6b3…` (D21); D22 `4224f4e…` verified on the session branch with artifact path; D16/D21/D22/intent contract texts re-read verbatim at baseline (§6); fresh negative searches at baseline confirmed zero serving/API/UI/persistence/registry/frontend code; worktree clean (13th rollback repaired non-destructively). Post-mutation (recorded in the task's final report): complete diff inspected; exactly one artifact path added; no implementation, code, canonical-data, or contract change; commit on `arena/9021d1a1-nse-historical-data-engine` with parent = D22 `4224f4e…`; fast-forward push to the session branch only; independent remote verification of commit/parent/tree/blob/path; prior D22/D21/D20/D16/D15/intent blobs intact; worktree clean except pre-existing untracked `_transfer_delivery/`. **D22 NOT promoted. D23 NOT promoted to main** (separate later activity).

## 23. Final determination

> ### **D23 DECISION: GRANTED WITH EXPLICIT BOUNDARIES/CONDITIONS.**
> First-release serving/application implementation authority is **GRANTED**, bounded to the D16-12 first-release scope (read-only serving + presentation over the qualified M2 baseline; Q1–Q10; saved queries; serving-state rebuild as delegated operation (b)) under the contracts D16-08/09/10/11/12 + D16-07 + D21 §14–§19; technology selection for the serving store/read-model, query mechanism, frontend, and hosting is **delegated within the bounded constraints of §13/§14** (no concrete technology selected; MD-12 remains open for all other physical concerns); the D21 changed-content constraints (§15) and the canonical/engine safety constraints (§16) bind the implementation; closure requires the §18 evidence; and the withheld items of §17/§19 each remain a separate future authority decision. This decision is the "later explicit authority decision for a stated scope" that D16 §20 required, and it discharges D16-13 item (1). It implements nothing, selects no technology, and grants nothing beyond the enumerated scope.
>
> **D23 = COMPLETE / DURABLE / REMOTELY VERIFIED** (subject to the §22 verification record completed in the task's final report).
