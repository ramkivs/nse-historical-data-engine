# D17 — POST-D16 RESIDUAL EVIDENCE / AUTHORITY INVESTIGATION

**Date:** 2026-10-09
**Mode:** READ-ONLY INVESTIGATION — documentation-only mutation (this artifact only).
**Implementation authority:** NONE granted by this record (and none exists for this record to grant — see §11/§19).
**Disposition summary (full statement §19):** residual evidence is **INCOMPLETE** — the primary unresolved item, D16-03a (changed-content disposition), remains **EVIDENCE REQUIRED**; all other D16 residuals classify as RESOLVED BY EXISTING EVIDENCE (architecture), AUTHORITY REQUIRED (implementation gates), DEFERRED BY D16 (trigger-based), or OUT OF SCOPE (environment boundary).

---

## 1. Purpose

Resolve — by repository-internal evidence only — the residual evidence and authority items explicitly left open by the authoritative D16 Architecture Authority Decision (`docs/architecture/POST_I5_SERVING_INCREMENTAL_PRODUCT_ARCHITECTURE_AUTHORITY_DECISION.md`, commit `0c21024`):

1. **Primary:** D16-03a — CHANGED-CONTENT DISPOSITION (status at D16: EVIDENCE REQUIRED). Determine whether repository evidence establishes any of: semantic equivalence, replacement, reprocessing, quarantine, rejection, historical supersession, requalification, provenance requirements, impact on existing canonical data, impact on serving visibility. If not, preserve EVIDENCE REQUIRED and state exactly what evidence is missing.
2. **Secondary:** every later-authority item enumerated by D16 (D16-13 item 5, cross-referenced from D16 §15 and inventoried in D16 §19), classified as RESOLVED BY EXISTING EVIDENCE / EVIDENCE REQUIRED / AUTHORITY REQUIRED / DEFERRED BY D16 / OUT OF SCOPE.

This record **does not** reopen D15 or redo D16, does not redesign the architecture, and does not implement anything. It is decision input for future authority decisions, not an authorization.

## 2. Authority and scope

- **Authority:** D17 directive (read-only investigation; documentation-only mutation; no implementation authority). D16 stands as the governing architecture decision; D15 stands as the governing post-I5 investigation; the intent artifact stands as governing target intent (adopted unmodified by D16 §4).
- **Scope of inspection:** repository files only (docs, `src/`, `tools/`, `tests/`, `evidence/` manifests) — all read-only. No Windows inspection (corpus bytes are out of Arena reach — D15 #15). No corpus execution. No I4/I5 re-run, re-measure, or reinterpretation (I5 CLOSED/DURABLE).
- **Method:** INVESTIGATE → VERIFY → RE-VERIFY → DOCUMENT → PROVE. Every factual claim below cites the repository record or code location it was read from. No assumption fills any gap.
- **Product scope:** single-user personal-use scope preserved throughout (D16 §13 non-goals stand: no authentication, no RBAC, no multi-user, no PostgreSQL, no enterprise deployment, no distributed architecture). Nothing in this record requires reconsideration of any non-goal.

## 3. Baseline verification (pre-investigation, read-only)

| Check | Result |
|---|---|
| Remote `origin/main` | `0c2102425d9995e07d1f57a08715435c3f0bc7f9` (gh api, 2026-10-09) — matches the task's authoritative main exactly |
| Remote session branch `arena/9021d1a1-nse-historical-data-engine` | `0c21024…` (same commit) |
| `0c21024` parent | `d60eb3d4f51f58347200066d4d41bcd6d78848e0` (the D15 commit) — chain intact |
| `0c21024` subject | `docs: D16 — post-I5 serving / incremental / product architecture authority decision` |
| Local worktree | 7th sandbox `.git` rollback detected at start (shallow @ `89ce965c`, stale marks); repaired non-destructively: `git fetch --unshallow origin` → ancestry check `89ce965c` is ancestor of `0c21024` = YES → `git update-ref` session branch → `git read-tree` → worktree clean except pre-existing untracked `_transfer_delivery/` (never committed) |
| No destructive Git operations | confirmed (fetch/update-ref/read-tree only) |

## 4. D16 decision inputs verified (all three, byte-identical worktree = HEAD = remote main)

| Input | Blob SHA (git) | Other identity | Size |
|---|---|---|---|
| `docs/product/HISTORICAL_ENGINE_PRODUCT_AND_SERVING_ARCHITECTURE_INTENT.md` | `41ad2740dd01620e547fc5a4659cafd53f28d534` | SHA-256 `7e4a14f4e6fd667d415b7351b58a266c5f0f15d494ba903fd132a15222830096` | 595 L / 18,300 B |
| `docs/investigations/POST_I5_SERVING_INCREMENTAL_PRODUCT_ARCHITECTURE_INVESTIGATION.md` (D15) | `79157b82355caf7579ec63b126a23e1a133b79ba` | gap matrix 17 rows present; disposition = INVESTIGATION COMPLETE — ARCHITECTURE DECISION REQUIRED | 361 L / 30,959 B |
| `docs/architecture/POST_I5_SERVING_INCREMENTAL_PRODUCT_ARCHITECTURE_AUTHORITY_DECISION.md` (D16) | `1b6e2faf9bdf7cdd6da0210f0ebb48c1d2109b5c` | 20 sections; 13 decision blocks (D16-01…12 + D16-03a); §15/§20 = IMPLEMENTATION AUTHORITY NOT GRANTED | 684 L / 48,996 B |

All three verified identical at local HEAD `0c21024` and on remote `main` (contents API).

## 5. D16-03a — changed-content evidence investigation

**Scenario under investigation:** archive filename/date identity unchanged + archive content SHA-256 changed + archive was previously processed (the D16-03 **CHANGED** class).

### 5.1 What the governing records already fix (re-verified verbatim)

- **Intent §6 (adopted unmodified by D16 §4):** "If an archive with the same apparent identity has different content, it must **not** be silently treated as an ordinary duplicate." Then, verbatim: "The precise disposition for changed content remains a future contract/governance question. Possible outcomes could include explicit conflict, reprocessing, replacement/versioning, or quarantine, **but this document does not select one**."
- **D16-03 (decided):** classification semantics fixed — CHANGED is **never** classified unchanged; **never** silently reprocessed over the prior result; **the prior result stays intact**; the archive is held as a **flagged finding** pending D16-03a. D16-03a (sub-decision): **EVIDENCE REQUIRED** — "no repository evidence exists to choose among outcomes now, and the intent (§6) deliberately leaves it open. Until D16-03a, CHANGED archives are quarantined from automatic processing by default (the fail-closed reading of the intent)."
- **D16 §10 / §17:** CHANGED CONTENT = "EVIDENCE REQUIRED / quarantined by default. No policy invented; the intent's four candidate outcomes (conflict / reprocessing / replacement-versioning / quarantine) remain open for the future decision when a changed archive actually presents."
- **Existing mechanism (single-run, corpus-pinned):** `i4_preflight.py` PF-12 compares each observed archive sha256 to the D01-inventory sha256; any mismatch is a **GATING DIVERGENCE that halts the run** (`raise _fail`); PF-10 gates discovered set == D01 set both directions; PF-11 gates 0 duplicate checksums / 0 duplicate dates. I.e., in the existing (single-run, pinned-corpus) design, "same apparent identity + different content" is expressible **only** as a hard fail-closed gate — detection + halt, with **no subsequent policy** of any kind.
- **Existing "quarantine" concept (re-verified scope):** `src/nse_engine/rows.py` + D05 §7/§8 — quarantine is a **row-level parse-failure** record (`QuarantineRecord`, structural parse failures, raw kept). M2 baseline: 0 quarantined. This concept is **not** an archive-level changed-content disposition and confers no authority to extend it.

### 5.2 Determinations — each of the 10 candidate evidence questions

| # | Question | Established by repository evidence? | What the evidence actually says |
|---|---|---|---|
| 1 | Semantic equivalence | **NO** | The only identity contracts are byte-level: archive sha256 (D01, PF-12), member raw/LF digests. No rule, tool, or record defines when two different byte sequences are "semantically equivalent" (e.g., re-zipped/re-encoded archive). Not decidable with current evidence. |
| 2 | Replacement | **NO** | No contract authorizes replacing a processed result. Constraints exist: D16-03 (prior result stays intact; never silently reprocessed); D16-07 class (1) immutable; D16-05 (unaffected archives never re-read). Silent replacement is prohibited; **affirmative replacement authority exists nowhere**. |
| 3 | Reprocessing | **PARTIALLY CONstrained — not established as policy** | D16-04 *requires* reprocessing (re-qualification) only when **version bindings** mismatch (stale census). D16-03 prohibits *silent* reprocessing for a CHANGED archive under unchanged bindings. Reprocessing of a CHANGED archive under the **same** bindings is not established in either direction. |
| 4 | Quarantine | **As outcome: NO. As interim default: YES (D16-03)** | The existing "quarantine" is row-level (5.1). Archive-level quarantine exists only as the D16-03 fail-closed **hold until D16-03a** — an interim operational default, not an established terminal disposition. |
| 5 | Rejection | **NO** | No contract defines permanent rejection (exclusion from the dataset + recorded reason) of a changed archive. |
| 6 | Historical supersession | **NO** | No versioned-supersession semantics (keep both, newer wins in queries, history retained) exist anywhere in the repository records. |
| 7 | Requalification | **Condition YES (D16-04); content-change case NO** | D16-04: "processed" = content identity × version bindings; mismatch ⇒ stale; staleness = deterministic registry census. A content change under **unchanged** bindings is **not** a D16-04 staleness event — D16-04 by construction does not cover it. Migration mechanism DEFERRED (D16). |
| 8 | Provenance requirements | **PARTIALLY** | D16-02 registry content contract fixes the fields: identity, content sha256, result (partition/rows/quarantined), version bindings, run provenance (run_id, package manifest digest), status (processed/pending/flagged). A CHANGED archive is representable today only as **flagged** (held). The record shape for any *post-disposition* state (e.g., a replacement entry, a superseded marker) is **unspecified**. |
| 9 | Impact on existing canonical data | **Constrained to "none by default" — nothing beyond** | Prior result stays intact (D16-03); qualified baseline immutable (D16-07 (1)); unaffected archives never re-read (D16-05). Any impact beyond "prior data untouched" is not established. |
| 10 | Impact on serving visibility | **Constrained — trust-marking not established** | Serving reflects classes (1)+(2)+(3) only (D16-09); a held CHANGED archive leaves prior canonical rows visible; registry status + flagged findings are visible via Q8 (quarantined counts) / Q9 (archive inventory + registry status) / Q10 (evidence views). Whether prior data must be **marked** (e.g., "superseded?", "conflict?") in serving is not established. |

### 5.3 Negative-evidence statement (explicit)

**Evidence that exists:** the intent's explicit refusal to select (verbatim, §5.1); D16-03's classification + fail-closed hold; the D16-02 registry content contract; PF-10/11/12 fail-closed gate behavior; the row-level quarantine concept (different scope); D15 gap #6 (classified E = DECISION REQUIRED, "intentionally undecided (intent §6)").

**Evidence that does not exist (verified by exhaustive sweep of `docs/`, `src/`, `tools/`, `tests/`, `evidence/` manifests):**
1. **No changed-archive instance, precedent, or incident record.** The corpus has been pinned since D01 (2,462 archives; 0 duplicate checksums; 0 duplicate file dates; PF-10/11/12 gate any corpus drift). I4/I5 are closed. The CHANGED class has never been instantiated in this repository's history — there is no observation to generalize from.
2. **No semantic-equivalence definition or capability** (byte hashes only).
3. **No archive-level replacement / supersession / rejection / conflict policy** in any contract record (D05, D06, D07, D08 MD-02…MD-17, D11, D12, D14, D15) — sweeps for replacement/supersede/reprocess matched only record-supersession language, D16's own hold, and D02's parser-drift *detectability* argument (not a disposition policy).
4. **No authority intent on the four candidate outcomes** — the governing intent refuses to select, and no later record selected.

**Evidence deliberately deferred (not missing):** none for D16-03a — D16 did not defer any *evidence-gathering* step; it deferred the *decision*, conditioned on a changed archive actually presenting (D16-03a's own text).

**What would resolve it (stated precisely, per the task):** (a) an actual changed-archive instance (or an authority-directed hypothetical with concrete byte pairs); (b) the owner's explicit choice among the four intent candidate outcomes (conflict / reprocessing / replacement-versioning / quarantine) — an authority decision informed by (a); (c) if the choice is conditioned on semantic equivalence, a definition of semantic equivalence for this corpus (no such capability exists); (d) the provenance/registry record shape for the chosen post-disposition state (spec detail the decision must produce); (e) the statement on prior canonical data (authoritative / flagged / superseded) and on serving trust-marking for it.

### 5.4 Result

**D16-03a: EVIDENCE REQUIRED — PRESERVED.** The D16 fail-closed/quarantine hold remains the **interim operational default only**; this record does not convert it into a permanent product policy, because no authoritative evidence supports doing so (the governing intent explicitly leaves the disposition open, and no repository record closed it).

## 6. D16-04 — requalification residual

**What D16 established (re-verified verbatim in §7 D16-04):**
- **Binding principle (decided, ADOPT):** "processed" is always a statement about **(content identity × version bindings)**; an entry is applicable only while current engine fingerprint, runner fingerprint, canonical `spec_version`, and processing contract version **equal** the entry's bindings; any mismatch ⇒ **stale**; stale results may not serve under the new contract until reprocessed and re-validated under the new bindings; **staleness is a deterministic census derived from the registry, not an execution**.
- **Deferred (DEFER, with trigger):** the migration *mechanism* (batch requalification vs per-archive lazy vs versioned coexistence) — deferred **until the first actual contract/tool version change occurs**, when evidence (stale census, scope, cost) will exist to decide against.
- **No requalification performed, ordered, or implied** by D16 (task boundary; I5 boundary).

**Verification that the version bindings exist and are resolvable (D16-04's premise holds):** `GOVERNED_INPUTS.json` / `RUN_RECORD.json` bindings — `contract_version I4-runner/1.0`, engine fingerprint `d3269b73…` (17 modules), runner fingerprint `f3ebf624…` (6 modules), `spec_version D05/1.0`, corpus digest `54d81507…`; no contract/tool version change has occurred since the M2 baseline (D13 §6; D14; D15 §8).

**Residual:** exactly one item remains — the **migration-mechanism decision at the first actual version change** (D16-13(5) item 4). Its evidence (the stale census) does not exist *yet* because no version change has occurred; that is a **trigger-based deferral with a defined evidence source**, not an open gap. **No requalification is performed by this record.**

**Result: DEFERRED BY D16 (trigger: first version change; then evidence = stale census; then authority decision).** No residual evidence item open today.

## 7. D16-05 / D16-06 — incremental composition residuals

**Adopted architecture (re-verified):** D16-05 — per-archive contributions commit to their own partition; corpus-scoped derived state (identity/associations, calendar, metrics) is **re-derived, not re-processed**, as a pure function of all processed archives' canonical rows + contract versions; invariants (i) deterministic byte-identical re-derivation, (ii) always verifiable, (iii) registry updated in the same publication; an incremental publication is **never** a re-qualification of the I5 baseline. D16-06 — partition model extends **unchanged**; invariants: content-derived keys (MD-06), one partition per archive, complete/verifiable manifests, deterministic membership, 12 baseline partitions byte-identical/immutable; per-year rollup = derived view (serving state 4), not a new partitioning.

**Cross-check against existing I4/M2 mechanics (all verified this investigation):**
- `tools/i4_runner/i4_inputs.py::partition_of` = `(format_family, calendar year of date_from_filename)` — content-derived, exactly as D16-06 states (MD-06).
- `tools/i4_runner/i4_runner.py` — per-archive `INPUT_MANIFEST.jsonl` records (2,462: identities, digests, member sizes, header facts, `data_lines`, `rows`, `quarantined`, partition) — the per-archive contribution record D16-05 consumes.
- `src/nse_engine/w2_stream.py` — the corpus-scoped derived state is exactly four folds (calendar derivation, row-metric fold, identity correlation / dated associations, member facts) computed over **all** canonical builds — matching D16-05's "pure function of all processed archives' canonical rows + contract versions" characterization.
- Baseline partition structure: 12 partitions, per-partition manifests, byte-exact R6-proven rebuild (D12/D14/D15).

**Determination — sufficient for a later implementation-authority decision?** **YES.** The semantics and invariants are fixed and testable; the remaining choices (publication mechanics, re-derivation tooling, registry format) are implementation details a later authorization gate may select **within** the fixed invariants — the same D06→D07 house pattern (contract first, implementation authorized separately against it). No algorithm is invented here, and none is needed for the authorization decision.

**Observation (risk note, not a gap):** the baseline path was I5-qualified; the **incremental re-derivation path has never been executed** (no incremental run exists). Its implementation will therefore require its own MD-11-style evidence and verification — which D16-05 invariants (i)/(ii) already require. This is an implementation-risk observation for the future authorization record, not an architecture gap.

**Residual:** none evidence-wise. Implementation = D16-13(5) item 2 (AUTHORITY REQUIRED).

**Result: RESOLVED BY EXISTING EVIDENCE (architecture); AUTHORITY REQUIRED (implementation).**

## 8. D16-07 — persistence residual

**Decided by D16 (re-verified):** exactly four durable-state classes with fixed owners — (1) qualified baseline package, **immutable**; (2) incremental publications (MD-11-style); (3) processed-archive registry, single writer; (4) serving/derived state, **always a pure derivation of (1)+(2)+(3), rebuildable at any time, deletion never a data event**; conflict rule: (1)/(2)/(3) beat (4); the qualified M2 package and future serving persistence remain **distinct** (task-required distinction preserved).

**Intentionally undecided by D16 (re-verified §14):** **TECHNOLOGY = UNDECIDED** for every physical concern — persistence store, API framework, UI technology, hosting/deployment model, ingestion scheduler/watcher mechanism, registry storage format, query engine. MD-12 stands as WITHHOLD/NOT AUTHORIZED (D08 §16: "STORAGE TECHNOLOGY = UNDECIDED; no selection, no implementation"); if a selection ever occurs it is graded against MD-10's standard under the single-user simplicity constraint.

**Residual:** the boundary/ownership/conflict-rule questions are **decided and closed**. The only open persistence question is **physical store selection**, which D16 (and D08 before it) deliberately withhold until an implementation decision makes it necessary — at which point it is an MD-12 authority decision with an existing grading standard (MD-10). This record selects **no** technology.

**Result: boundary = RESOLVED BY EXISTING EVIDENCE; MD-12 physical store = DEFERRED BY D16 (UNDECIDED stands) / AUTHORITY REQUIRED when a physical store is actually needed.**

## 9. D16-08 / D16-09 / D16-10 — serving residuals

**D16-08 (serving dataset) — re-verified:** five-class exposure boundary fixed — canonical historical data (subject to D05 consumer obligations), provenance/evidence, processing metadata, minimal operational metadata: **MAY** be exposed; **raw archive content: NOT by default** (Windows corpus custody; would require a future explicit decision **plus** a cross-environment mechanism — D15 #15 = F, environment boundary). Source-row granularity = member/archive + verbatim fields (row offsets never adopted — a limitation of record, not a gap to fill).

**D16-09 (serving/query boundary) — re-verified:** engine owns the write path; serving = read-only consumer of (1)+(2)+(3), never invokes/schedules processing, never treats (4) as truth; exactly **two** delegated user-initiated operations (processing trigger; serving rebuild); invariants: query never mutates durable data; processing never reads (4) as input; query failure cannot corrupt (1)–(3); processing failure leaves (4) at last approved state.

**D16-10 (query contract) — re-verified:** Q1–Q10 semantic categories + saved queries/query history (serving state 4); each category mapped to verified existing data (D15 §14); explicitly excluded: eligibility/master (DEC-1), analytics beyond as-published + derived, raw-byte serving. Endpoint names, frameworks, schemas = **not decided** (TECHNOLOGY = UNDECIDED — deliberately implementation-level).

**Sufficiency for later implementation authorization (determination):** **YES, all three.** The exposure classes bound what may be exposed; the boundary + invariants make the responsibility split testable; the semantic categories bound query scope. A future implementation-authorization decision can scope the first release precisely against D16-08/09/10 (as D16-12 already does). Creating API schemas or endpoints is not required for the authorization decision and is **not done here** (no serving code exists in the tree — re-verified: 16 engine modules, no http/server/endpoint references; D15 §13 positive evidence of absence stands).

**Residuals:** raw-content serving = OUT OF SCOPE (environment boundary; explicit cross-environment decision + mechanism required — D16-13(5) item 6). Nothing else.

**Result: RESOLVED BY EXISTING EVIDENCE (serving dataset / boundary / query categories); raw-content serving = OUT OF SCOPE.**

## 10. D16-11 / D16-12 — product / UI residuals

**D16-11 (UI boundary) — re-verified:** UI owns presentation, navigation, query construction (Q1–Q10), result display, status/evidence display, report presentation, interaction, saved-query management; UI must **not** own parsing, classification, processing, validation, evidence generation, publication, registry mutation, derived-state re-derivation, or direct durable-data access; the **whitelist of delegated operations is exactly two** (processing trigger; serving rebuild); target presentation = the demonstrated I4 application (non-drift #12).

**D16-12 (first-release scope) — re-verified:** first release = **read-only serving + presentation over the qualified M2 baseline** — Dashboard tiles with D15-verified data backing; Data Explorer Q1–Q10 with record detail + provenance, quality views, yearly summaries, as-published display; saved queries + history. **Explicitly excluded:** the incremental-processing operation, raw-content serving, DEC-1/eligibility, all D16 §13 non-goals. Incremental ingestion is architecturally decided (D16-01–06) but sequenced as a **second implementation gate** (risk-ordered; the intent §16 tracks are parallel, not sequential dependencies).

**Genuine remaining authority gaps (identified, none invented):** exactly one — **implementation authorization for the first release** (D16-13(5) item 1). The scope is fully pinned by existing evidence (D15 §14 verified the data backing for every Dashboard tile and Explorer capability against durable artifacts; D16-12 fixed the scope and exclusions). No evidence gap remains in the UI/product area. No UI is implemented here.

**Result: RESOLVED BY EXISTING EVIDENCE (UI boundary + first-release scope); AUTHORITY REQUIRED (first-release implementation, item 1).**

## 11. D16-13 — implementation-authority residual (the D16 later-authority enumeration, classified)

D16's later-authority enumeration is recorded in **D16-13 item 5** (the §15 pointer "§7 D16-13(5)"; D16 §19 is the artifact/evidence inventory and cross-references it). The six items, classified against repository evidence:

| # | D16 item | Classification | Basis |
|---|---|---|---|
| 1 | First-release implementation authorization (read-only serving + first-release UI; contract = D16-08/09/10/11/12) | **AUTHORITY REQUIRED** | Architecture fully decided and evidence-verified (§7/§9/§10 of this record); no evidence gap; only the explicit authorization is missing (house pattern: decision input → explicit authorization → scoped implementation → evidence → remote verification). |
| 2 | Incremental-ingestion implementation authorization (contract = D16-01–06 + D16-02) | **AUTHORITY REQUIRED** | Architecture fully decided and verified against I4/M2 mechanics (§7). Note for the authority: the CHANGED-class **operational behavior is already fully fixed by D16-03** (held + flagged + never silent; fail-closed quarantine default until D16-03a), so D16-03a does not block an incremental authorization — it only leaves open the eventual *resolution path* of held CHANGED archives. |
| 3 | D16-03a changed-content disposition | **EVIDENCE REQUIRED** | §5 of this record — evidence does not exist (no instance, no semantic-equivalence definition, no policy in any record; the governing intent refuses to select). Preserved as EVIDENCE REQUIRED; not converted to policy. |
| 4 | Requalification migration mechanism | **DEFERRED BY D16** | Trigger = first actual contract/tool version change; at that moment the evidence (stale census, scope, cost) will exist by construction (D16-04). Nothing to do today; no version change has occurred (bindings verified §6). |
| 5 | MD-12 physical store selection | **DEFERRED BY D16** | WITHHOLD/NOT AUTHORIZED per D08 §16; D16 §14 preserves TECHNOLOGY = UNDECIDED; selection point = "if/when needed" at an implementation decision; grading standard already exists (MD-10 + single-user simplicity). |
| 6 | Raw-content serving | **OUT OF SCOPE** | Environment boundary (D15 #15 = F): corpus in Windows custody, Arena has no filesystem reach; would require an explicit cross-environment decision **plus** a cross-environment mechanism — neither exists; not addressable by repository-internal evidence. |

Cross-check of D16 §16 (deferred decisions) and §17 (evidence-required decisions) against this table: §16 items (migration mechanism; registry physical format; new partition key / new format family review; the three implementation scopes) and §17 items (D16-03a; migration mechanism; raw-content serving) are all accounted for by the six classifications above (registry physical format folds into item 5/MD-12; new partition key / format family review is a D16-06 in-review trigger, not a standing residual; implementation scopes fold into items 1/2). No later-authority item exists beyond these six.

**No authority expansion:** D14's non-authorizations stand unchanged; D16's "IMPLEMENTATION AUTHORITY = NOT GRANTED" stands unchanged; this record adds **no** authority of any kind.

## 12. Complete residual decision matrix

| Residual item | Disposition in D16 | D17 classification | Evidence state |
|---|---|---|---|
| D16-03a changed-content disposition | EVIDENCE REQUIRED | **EVIDENCE REQUIRED (preserved)** | No instance; no semantic-equivalence definition; no policy in any record; intent refuses to select |
| D16-04 applicability condition (processed = content × bindings) | ADOPTED | RESOLVED BY EXISTING EVIDENCE | Bindings exist and are resolvable (§6); no version change since M2 |
| D16-04 migration mechanism | DEFERRED | **DEFERRED BY D16** (item 4) | Trigger-based; evidence (stale census) appears at first version change |
| D16-05 incremental corpus composition | ADOPTED | RESOLVED BY EXISTING EVIDENCE | Verified against `i4_runner`/`w2_stream` mechanics (§7) |
| D16-06 partition/per-year semantics | ADOPTED | RESOLVED BY EXISTING EVIDENCE | `partition_of` + 12 immutable baseline partitions verified (§7) |
| D16-07 durable-state boundary (4 classes, conflict rule) | ADOPTED | RESOLVED BY EXISTING EVIDENCE | Closed; no residual boundary question |
| D16-07 / MD-12 physical store selection | UNDECIDED | **DEFERRED BY D16** (item 5) | TECHNOLOGY = UNDECIDED stands; MD-10 grading standard exists |
| D16-08 serving dataset boundary | ADOPTED | RESOLVED BY EXISTING EVIDENCE | 5-class boundary; D05 obligations binding; D15 §12 inventory verified |
| D16-08 raw-content serving | NOT by default | **OUT OF SCOPE** (item 6) | Environment boundary (D15 #15 = F) |
| D16-09 serving/query boundary + invariants | ADOPTED | RESOLVED BY EXISTING EVIDENCE | Boundary + testable invariants; serving ABSENT in tree (verified) |
| D16-10 query semantic categories Q1–Q10 | ADOPTED | RESOLVED BY EXISTING EVIDENCE | Each category data-backed (D15 §14); schemas/tech deliberately undecided (implementation level) |
| D16-11 UI boundary + 2-op whitelist | ADOPTED | RESOLVED BY EXISTING EVIDENCE | Boundary closed; no UI implemented (ABSENT verified) |
| D16-12 first-release scope | ADOPTED | RESOLVED BY EXISTING EVIDENCE (scope) / AUTHORITY REQUIRED (implementation, item 1) | Data backing for every tile/capability verified (D15 §14) |
| Item 1 — first-release implementation authorization | withheld in D16 | **AUTHORITY REQUIRED** | Fully evidence-supported; only explicit authorization missing |
| Item 2 — incremental-ingestion implementation authorization | withheld in D16 | **AUTHORITY REQUIRED** | Fully evidence-supported; CHANGED operational behavior already fixed by D16-03 default |
| D16-02 registry physical format | contract only | **DEFERRED BY D16** (folds into item 5) | Format = implementation detail until an implementation decision |
| D16-06 new (family, year) key / new format family | explicit review | RESOLVED BY EXISTING EVIDENCE (rule fixed) | Review trigger exists; no such key/family has arisen |

## 13. Evidence gaps (exactly what is missing, nothing more)

| Gap | Missing evidence | Why it is missing | When it can close |
|---|---|---|---|
| G1 (D16-03a, primary) | An actual changed-archive instance (or an authority-directed concrete hypothetical with byte pairs) | The corpus has been pinned since D01 (PF-10/11/12 gate any drift; I4/I5 closed); the CHANGED class has never occurred in this repository | When a changed archive actually presents (D16-03a's own condition) |
| G2 (D16-03a) | A definition/capability of semantic equivalence for corpus archives, if any candidate outcome is conditioned on it | Only byte-level identity contracts exist (archive sha256, member digests); no semantic comparison rule or tool exists | At the D16-03a decision, only if needed by the chosen outcome |
| G3 (D16-03a) | Registry record shape for a post-disposition CHANGED state (e.g., replacement entry / superseded marker) | D16-02's status set is (processed/pending/flagged); CHANGED is representable only as flagged+held today | Produced by the D16-03a decision (spec detail, not free evidence) |
| G4 (D16-03a) | Statement on prior canonical data and serving trust-marking once a CHANGED archive is resolved | Constrained only to "prior result stays intact" (D16-03); no record decides what happens next | Produced by the D16-03a decision |

Gaps that are **not** gaps (deliberately deferred, with defined triggers/evidence): the requalification stale census (appears at first version change — D16-04); the registry physical format (until an implementation decision — MD-12); per-year rollup artifact (derivable view — D16-06/D15 #10).

## 14. Authority gaps (decisions that require authority, not evidence)

| # | Authority decision | Blocking? |
|---|---|---|
| A1 | First-release implementation authorization (scope D16-12; contract D16-08/09/10/11/12) | Blocks first-release implementation only |
| A2 | Incremental-ingestion implementation authorization (contract D16-01–06 + D16-02) | Blocks incremental implementation only; **not** blocked by D16-03a (operational CHANGED behavior already fixed by D16-03 default) |
| A3 | D16-03a disposition — after G1–G4 evidence exists, the owner must choose among the four intent candidate outcomes (or a documented alternative) | Resolves only the resolution path of held CHANGED archives |
| A4 | Requalification migration mechanism — at first version change, against the stale census | Future (trigger-based) |
| A5 | MD-12 physical store selection — if/when a physical store is needed, graded by MD-10 + single-user simplicity | Future (implementation-conditional) |
| A6 | Raw-content serving — explicit cross-environment decision + mechanism | Out of scope today (environment boundary) |

No other authority gap exists. No decision in this record requires authority to stand (it decides nothing).

## 15. Deferred items (carried forward, unchanged)

1. Requalification migration mechanism — D16-04 / item 4 (trigger: first version change).
2. Registry physical format — D16-02 / MD-12 (until an implementation decision).
3. MD-12 physical store selection — D08 §16 WITHHOLD stands; D16 §14 UNDECIDED stands.
4. Incremental-ingestion implementation scope — item 2.
5. Serving implementation scope — item 1.
6. First-release UI implementation scope — item 1.
7. New (family, year) partition key / new format family — D16-06 explicit-review trigger.
8. Raw-content serving — D15 #15 environment boundary.
9. DEC-1 / eligibility — DEFERRED per MD-16 (unchanged; no back door).

## 16. Explicit non-goals

No implementation of any kind (serving/incremental/persistence/UI) — none performed or implied. No technology selection of any kind (TECHNOLOGY = UNDECIDED preserved; nothing named, ranked, or implied). No API schema, endpoint, or framework. No re-opening of D15 or D16; no re-run/re-measure/reinterpretation of I4/M2/R6/I5; no modification of the qualified dataset or engine behavior. No conversion of the D16 fail-closed/quarantine default into a permanent policy. No filling of any gap with conventional engineering practice. No authority expansion (D14 non-authorizations and D16's non-grant stand). Product scope unchanged: single-user; no authentication/RBAC/multi-user/PostgreSQL/enterprise/distributed concerns introduced or implied. No destructive Git operations. `_transfer_delivery/` never committed.

## 17. Recommended next authority action (recommendation only — no authority granted)

1. **The first-release implementation-authorization decision (A1) is now fully evidence-supported and may be taken at the authority's discretion** — decision input: D16 (architecture) + D15/D17 (evidence verification); scope: D16-12 (read-only serving + presentation over the qualified M2 baseline); no further investigation is a precondition.
2. **The incremental-ingestion authorization (A2) is likewise fully evidence-supported** — with the recorded observation that CHANGED archives will operate under the D16-03 fail-closed hold (held + flagged + never silent) until A3 is resolved, and that the incremental re-derivation path, never executed, must carry its own MD-11-style evidence per D16-05 invariants.
3. **D16-03a (A3) should remain parked under the fail-closed hold** until a changed archive actually presents (or the authority directs a concrete hypothetical); at that moment the record of the instance + the owner's choice among the four intent outcomes (plus G3/G4 statements) follow the house pattern into a D16-03a decision.
4. Items A4/A5/A6 remain trigger- or condition-based; no scheduling is recommended or implied.
5. Whichever of A1/A2 the authority takes first, it should follow the house pattern: decision input → explicit authorization → scoped implementation → evidence → remote verification; single-user scope binds every choice.

## 18. Artifact / evidence inventory

**This record:** `docs/investigations/D17_POST_D16_RESIDUAL_EVIDENCE_AUTHORITY_INVESTIGATION.md` (the only mutation).
**Authoritative inputs (verified byte-identical at `origin/main@0c21024`, §3/§4):** intent artifact (blob `41ad2740dd01620e547fc5a4659cafd53f28d534`, SHA-256 `7e4a14f4e6fd667d415b7351b58a266c5f0f15d494ba903fd132a15222830096`); D15 investigation (blob `79157b82355caf7579ec63b126a23e1a133b79ba`); D16 decision (blob `1b6e2faf9bdf7cdd6da0210f0ebb48c1d2109b5c`).
**Evidence inspected this investigation (read-only):** D16 §4/§7 (D16-02/03/03a/04/05/06/07/08/09/10/11/12/13)/§10/§13/§14/§15/§16/§17/§19/§20; intent §6/§7 verbatim; D15 §12/§13/§14/§15 (17-row gap matrix); `tools/i4_runner/i4_preflight.py` (PF-10/11/12 fail-closed behavior incl. `raise _fail` on sha256 mismatch); `tools/i4_runner/i4_inputs.py` (`partition_of`); `tools/i4_runner/i4_runner.py` (`INPUT_MANIFEST.jsonl` per-archive records); `src/nse_engine/w2_stream.py` (W2 corpus-scoped folds: calendar/metrics/associations/facts); `src/nse_engine/rows.py` + D05 §7/§8 (row-level quarantine scope); `src/nse_engine/` module inventory (serving/API absence re-verified); `evidence/inventory/file_inventory.json` (2,462 records; per-archive sha256/size/date fields); D08 §16 (MD-12 WITHHOLD; MD-16 DEFERRED; MD-17 OUT OF SCOPE); D13 §6 / D12 / D14 (version-binding stability since M2 baseline).
**Sweeps (negative evidence):** repository-wide case-insensitive sweeps for changed/quarantine/replacement/supersede/reprocess across `docs/`, `src/`, `tools/`, `tests/` — matches confined to: D16's own hold language; record-supersession language (D03/D07/D10/D11); D02 parser-drift detectability argument; row-level quarantine (engine + D05); D15 #6 classification. No archive-level changed-content policy found anywhere.

## 19. Final disposition

This investigation preserved D16 in full, verified every residual against repository evidence, and found: the D16 architecture (D16-01…D16-12) is **sufficiently established** for future implementation-authority decisions on first-release serving/UI and on incremental ingestion; the persistence boundary is closed with technology intentionally UNDECIDED (MD-12); the serving/boundary/query/UI/first-release areas carry no residual evidence gaps; the requalification residual is a trigger-based deferral with a defined evidence source; and the primary unresolved item, **D16-03a changed-content disposition, remains EVIDENCE REQUIRED** — no repository evidence establishes semantic equivalence, replacement, reprocessing, quarantine-as-outcome, rejection, historical supersession, or any prior-data/serving-trust treatment for a changed archive, and the governing intent explicitly refuses to select among the candidate outcomes.

> ### **FINAL DISPOSITION: RESIDUAL EVIDENCE INCOMPLETE — EVIDENCE REQUIRED**
> (Primary: D16-03a. All other residuals: RESOLVED BY EXISTING EVIDENCE (architecture) / AUTHORITY REQUIRED (A1, A2) / DEFERRED BY D16 (A4, A5, registry format) / OUT OF SCOPE (A6).)

**Implementation remains prohibited regardless of this disposition.** No serving/API, incremental-ingestion, persistence, or UI implementation is authorized by this record; none was performed. ARCHITECTURE DECISION (D16) = ESTABLISHED and unchanged. IMPLEMENTATION AUTHORITY = NOT GRANTED — exactly as D16 §15/§20 stand.
