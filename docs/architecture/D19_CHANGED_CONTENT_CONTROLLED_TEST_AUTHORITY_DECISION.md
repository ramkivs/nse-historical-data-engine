# D19 — CHANGED-CONTENT CONTROLLED TEST AUTHORITY DECISION

**Date:** 2026-10-09
**Mode:** GOVERNANCE / AUTHORITY DECISION ONLY. Documentation-only mutation (this artifact only). The controlled test is NOT executed by this record; nothing is implemented; the canonical dataset is not touched.
**Controlling distinction (binding throughout):** this record grants **AUTHORITY TO RUN A CONTROLLED TEST** — a narrowly isolated, evidence-producing synthetic experiment. It does **NOT** grant **IMPLEMENTATION AUTHORITY** of any kind. D16 §15/§20 ("ARCHITECTURE DECISION = ESTABLISHED. IMPLEMENTATION AUTHORITY = NOT GRANTED.") stand unchanged. These two authorities are different things and are not conflated in this record.

---

## 1. Purpose

Make the narrowly scoped authority decision required by D18 (`docs/investigations/D18_D16_03A_CHANGED_CONTENT_RESIDUAL_EVIDENCE_INVESTIGATION.md`): whether a tightly isolated, evidence-producing synthetic changed-content experiment should be authorized to close the remaining D16-03a evidence gaps (R1–R4), and — if so — exactly what narrow scope that authority covers.

The only question decided here is the controlled test's authorization and scope. No disposition of D16-03a is made; no policy is selected; no implementation of any kind is authorized.

## 2. Authoritative baseline (Phase 0 — re-verified read-only)

| Item | Value |
|---|---|
| Repository | `ramkivs/nse-historical-data-engine` |
| Authoritative branch | `refs/heads/main` |
| Expected authoritative main | `6784efdc7173e1684df44bc8b4f7a1cc7d40e238` |
| Verified `origin/main` | `6784efdc7173e1684df44bc8b4f7a1cc7d40e238` — **MATCH** |
| Session branch `arena/9021d1a1-nse-historical-data-engine` | `80fc3b8dd3ec814e24b7f76d1d383bc10b5de59c` (D18) |
| D18 commit / parent | `80fc3b8…` / parent `6784efdc7173e1684df44bc8b4f7a1cc7d40e238` = authoritative main — chain intact |
| D18 exact delta vs main | ahead 1 / behind 0; exactly one file: `docs/investigations/D18_D16_03A_CHANGED_CONTENT_RESIDUAL_EVIDENCE_INVESTIGATION.md` (+212) |
| D18 remote blob | `e1e7cab083c03c8d732578b0d07fe03f35c81636` (34,940 B) — worktree byte-identical |
| Local state | 9th sandbox `.git` rollback at start; repaired non-destructively (unshallow → ancestry YES → `update-ref` → `read-tree`); worktree clean except pre-existing untracked `_transfer_delivery/` |

Main has not moved; no STOP condition triggered. No promotion of D18 or D19 to main is performed by this task (the D18 → D19 chain is promoted by the authority separately, afterward).

## 3. Governing evidence

- **D16** (`docs/architecture/POST_I5_SERVING_INCREMENTAL_PRODUCT_ARCHITECTURE_AUTHORITY_DECISION.md`, blob `1b6e2faf…`): the governing architecture decision. Re-verified verbatim for this decision: D16-02 (durable registry content contract; contract only, no code), D16-03 (classification: CHANGED = never unchanged, never silently reprocessed, **prior result stays intact**, held as flagged finding; **fail-closed quarantine from automatic processing by default**), D16-03a (EVIDENCE REQUIRED — "decided by a future authority decision when and only when a changed archive actually presents"; intent §6 leaves the four candidate outcomes open), D16-04 (processed = content × version bindings; staleness = registry census), D16-07 (four durable-state classes; (1) immutable; (4) pure derivation, rebuildable), D16-08 (five-class exposure; raw content NOT by default), D16-09 (serving read-only; invariants; two delegated operations), D16-12 (first release = read-only serving + presentation), D16-13 (six enumerated later-authority items; IMPLEMENTATION AUTHORITY = NOT GRANTED), §15/§20.
- **D17** (blob `3eef98b8…`): residual classification — D16-03a = EVIDENCE REQUIRED (gaps G1–G4).
- **D18** (blob `e1e7cab0…`): the direct decision input. G1–G4 determinations (§3–§6), the specific remaining evidence R1–R4 (§7), and the controlled-test determination (§8): the test is **necessary** as the only remaining evidence path short of a real-world occurrence, **not performed**, fully **isolable** from the canonical dataset, and requires (i) explicit test authority, (ii) a test-scoped answer for the not-yet-implemented registry/classifier mechanics, (iii) evidence-only confirmation.
- **Intent** (blob `41ad2740…`, SHA-256 `7e4a14f4…`): §6 (changed content must not be silently treated as an ordinary duplicate; four candidate outcomes; "this document does not select one").
- **D15** (blob `79157b82…`): serving ABSENT (§13); environment boundary — raw archive bytes in Windows custody, Arena has no filesystem reach (§15 #15).

## 4. D18 G1–G4 findings (Phase 1 — confirmed, not reinterpreted)

| Gap | D18 determination | Confirmed here |
|---|---|---|
| G1 — changed-archive instance | **NOT ESTABLISHED** | Confirmed: no actual changed-archive event exists in the corpus, its pinned history, or any run/package record; 27-commit history contains no such record and no deleted files; the only same-identity/different-bytes artifact is the hypothetical fail-closed gate fixture in `tests/test_i4_runner.py`, which is **detection-only** (asserts a halt; records no disposition) and is not a disposition experiment |
| G2 — semantic-equivalence capability | **NOT ESTABLISHED** | Confirmed: A (byte identity) / B (archive identity) established at their own levels; C/D incidental determinism only; E (semantic equivalence of different-content source archives) absent |
| G3 — post-disposition registry record shape | **PARTIALLY ESTABLISHED** | Confirmed: pre-disposition contract ingredients exist (D16-02); no observed-vs-prior content pair, no CHANGED-specific disposition state, no relationship-to-prior-canonical-data field; registry is contract-only (no code) |
| G4 — prior-data authority / serving trust | **PARTIALLY ESTABLISHED** | Confirmed: hold state governed (prior data intact + visible; CHANGED visible as flagged finding); all post-disposition outcomes open; D05 has no supersession/invalidation rule |

Confirmed: existing repository evidence **cannot** establish R1–R4 without a controlled observation. D18's findings are adopted as the factual basis of this decision, unchanged.

## 5. Authority question

Should a tightly isolated, evidence-producing synthetic experiment be authorized to close R1–R4, and if so, exactly what narrow scope does that authority cover?

## 6. Proposed controlled-test boundary (Phase 2 — defined from D18 only)

The proposed experiment, at the minimum necessary level (per D18 §8):

- **S1:** process synthetic archive **B1** under governed archive identity **I** (synthetic root, `file_name`, `date_from_filename`) with the existing I4 mechanics into a **fresh test out-root**; from its per-run records, construct a **test-scoped registry seed** entry in the D16-02 field shape representing accepted processing ("processed under" the current version bindings).
- **S2:** present synthetic archive **B2** under the **same** governed identity **I** but with **deliberately different** bytes/content (e.g., one data row altered, re-zipped); observe and record the full classification and disposition behavior chain against the seeded test-scoped registry.

**Mandatory isolation (all non-negotiable for the test to remain in scope):**

- fresh isolated roots only (synthetic corpus root + test out-root);
- synthetic data only; test-scoped state only;
- **no** D01 corpus; **no** M2 canonical package; **no** I4/I5 qualified output;
- **no** authoritative archive inventory (`evidence/inventory/` untouched, unmodified, unread-as-input);
- **no** production serving dataset; **no** production registry; **no** production UI/API;
- **no** external provider; no production credentials; **no** Windows-custody production bytes (unreachable here in any case — D15 #15);
- the test **must not become a production implementation by accident**: any machinery the test needs (a minimal test-scoped seed/observation harness) is test-observation instrumentation only — it lives in the test scope, is labeled test-scoped, is never promoted to production paths, and does not implement the D16 architecture components (the production registry and CHANGED classifier remain contract-only).

## 7. R1 decision (Phase 3)

**Decision: AUTHORIZED (within the test scope of §6/§11).**

Authorized **only**: creation of B1 and B2 in isolated test roots; one governed identity I shared by both; deliberately different content; recording of their byte/content hashes (sha256(B1), sha256(B2)) and the byte-level diff; preservation of the byte-pair evidence as a durable, hash-pinned, clearly test-scoped record.

**Not authorized** (binding): creation or modification of any canonical/production archive; use of any real archive bytes; any presentation of B2 outside the isolated test environment.

Rationale: G1 = NOT ESTABLISHED and the corpus is pinned; a controlled, isolated, synthetic byte pair is the minimum concrete case against which D16-03a's disposition can later be decided (D18 §7 R1; D16-03a's own condition — "when and only when a changed archive actually presents" — is met in test scope, not production scope).

## 8. R2 decision (Phase 4)

**Decision: R2 = NOT REQUIRED FOR THIS TEST.**

The test distinguishes and needs only:

- **(A) proving that the content differs** — established by sha256(B1) ≠ sha256(B2) (byte-level; already a governed capability — D18 G2 level A);
- **(B) observing the changed-content classification** — D16-03's CHANGED class is defined **purely by byte-level facts** (apparent identity matches a registry entry AND content sha256 differs); no semantic judgment participates in the classification or in the interim hold behavior;
- **(C) determining whether B1 and B2 are semantically equivalent** — **not required** to observe the classification, the hold, or the data/serving impact of the four intent candidate outcomes.

Consequently: no production semantic-equivalence framework is authorized, developed, or implied by this record (G2's absence is recorded as-is and is not filled). If a future authority considers a candidate disposition genuinely conditioned on semantic equivalence (e.g., "reprocess only if semantically changed"), then a **separate authority decision** is required first, to define such semantics and the capability to apply them. No production semantics are defined in this task (none exists in the governing artifacts to be carried forward).

## 9. R3 decision (Phase 5)

**Decision: AUTHORIZED — test-scoped registry representation, minimum observation.**

The experiment may inspect and create a **test-scoped** registry representation, because observing the disposition requires a "processed under" statement for B1 to exist first (D18 §5: the registry is contract-only; D18 §8: the seed is part of the required experiment). Boundaries:

- the registry state is **explicitly identified as test-scoped** (labeled in every artifact it appears in);
- it **must not become the production registry** (production registry remains unimplemented and contract-only — D16-02);
- **no production persistence technology is selected** by or for the test (the seed's on-test-disk form is a test detail — e.g., a JSONL file in the test root — and confers no technology decision);
- **no durable production schema is established** by the test.

The test must capture the **before/after** test-scoped registry state and evaluate whether the existing D16-02 contract ingredients are sufficient to represent: prior archive identity; prior content identity; **current** content identity; classification/disposition; processing result/status; version binding; provenance; relationship to prior accepted state. The sufficiency determination is a **finding of the test** (evidence for R3) — it does not design a permanent production schema; if ingredients prove insufficient, the D16-03a authority decision (a later gate) produces the post-disposition record shape (R3).

## 10. R4 decision (Phase 6)

**Decision: AUTHORIZED — isolated-test observation only.**

In the isolated test environment only, the test may establish:

- whether the previously accepted synthetic output (P1 from S1) **remains byte-identical** after S2 (digest evidence before/after — the D16-03 "prior result stays intact" obligation observed at runtime);
- whether the changed candidate (B2) is **held/blocked** — i.e., never silently classified unchanged and never silently reprocessed (D16-03 + the fail-closed interim default, observed at runtime);
- whether any **serving representation changes** — since serving is ABSENT (D15 §13), this is observed as the state of the durable test-state classes that D16-07/09 stipulate serving would reflect: the (1)/(2)-equivalent accepted states are unchanged, and the held CHANGED state is representable as a flagged finding in the (3)-equivalent state (registry status), with (4)-equivalent state a pure derivation;
- whether the existing architecture **specifies a trust/status marker** on previously accepted data — a documented record-inspection determination (expected finding: registry status + flagged findings are exposed per D16-08/10 Q8/Q9/Q10, but no trust marker on the prior data itself is specified — the post-disposition statement remains open).

**Not authorized:** any change to production serving (there is none — and none may be created); any creation of a permanent trust-marking policy. If the experiment demonstrates that a post-disposition policy decision remains necessary (the expected outcome), that is recorded as a **subsequent authority decision** — the D16-03a disposition decision itself, which D19 does not make.

## 11. Explicit scope (Phase 7A — exactly what is authorized)

**AUTHORITY TO RUN A CONTROLLED TEST — NARROW SCOPE, EXHAUSTIVE:**

1. **Isolated synthetic B1/B2 creation** in fresh test roots: one governed identity I; deliberately different content; recorded byte/content hashes; byte-pair evidence preserved (R1 — §7).
2. **Test-scoped seed/observation state**: the test-scoped registry seed for B1 (D16-02 field shape, labeled test-scoped) and any other test-scoped state strictly necessary to observe the disposition (R3 — §9).
3. **Test-scoped classification/disposition observation**: S2 presentation under I against the seeded state; observation and recording of classification + disposition behavior per D16-03 semantics and the fail-closed interim default; any minimal harness code is test-observation instrumentation only (test scope, labeled, never promoted).
4. **Capture of R1–R4 evidence**: the byte-pair record (R1); test-scoped registry before/after state + ingredient-sufficiency finding (R3 input); P1 byte-identity proof, held/blocked observation, serving-representation observation, trust-marker record determination (R4 input); R2 confirmed not required (no semantic-equivalence work); full isolation attestation (production corpus / D01 inventory / M2 package / I4-I5 evidence: digests before and after the test, unchanged).
5. **Preservation of test evidence**: a durable, hash-pinned, explicitly test-scoped/non-canonical record following house conventions (a new evidence directory with its own record document, e.g., an `evidence/D20_…` package + a D20 investigation record), clearly stating that the test exercised synthetic data only and produced evidence, not canonical output and not a disposition.

## 12. Explicit exclusions (Phase 7B — exactly what is NOT authorized, exhaustive)

This authority does **NOT** cover, and nothing in this record may be read to authorize:

- production implementation of any kind (serving/API, incremental ingestion, persistence, UI — D16 §15/§20 stand);
- the production registry (remains contract-only, D16-02);
- a production CHANGED classifier (remains contract-only, D16-03);
- production persistence or any persistence technology selection (MD-12 stands; TECHNOLOGY = UNDECIDED);
- canonical dataset mutation of any kind;
- D01 / M2 / I4 / I5 output modification (none is read as test input, let alone modified);
- serving implementation or any change to serving behavior;
- UI/API changes of any kind;
- a permanent CHANGED policy — the test produces evidence, **not** a disposition; D16-03a remains a future authority decision;
- a semantic-equivalence framework or any production semantic definition (R2 — §8);
- reprocessing of real archives; replacement/supersession of canonical data;
- the requalification migration mechanism (D16-04 deferral stands; no version change is involved or implied);
- technology selection of any kind;
- re-run, re-measure, or reinterpretation of I4/I5 (I5 remains closed/durable);
- authentication, RBAC, multi-user support, PostgreSQL, or enterprise architecture;
- use of external providers, production credentials, or Windows-custody production bytes;
- promotion of any commit to `main` (main ref updates remain the authority's separate step).

## 13. Canonical-data protection

Binding invariants for the authorized test (each is a stop-the-test condition if violated):

1. The production corpus (Windows custody), `evidence/inventory/` (D01), the M2 package, and all I4/I5 evidence are **untouched**: no read-as-input, no modification, no deletion; the test's isolation attestation must record before/after digests proving this.
2. The test operates **only** on fresh roots containing synthetic data and test-scoped state.
3. No test output may be published, named, or referenced as canonical, qualified, or durable product state; test evidence is preserved as **evidence of a test**, hash-pinned and labeled non-canonical.
4. No engine/runner behavioral change is introduced by the test; if the existing I4 mechanics are used for S1, they run unmodified against the synthetic corpus (any divergence observed is recorded as a finding, never "fixed" in production code by the test).
5. The D16-03 fail-closed interim default (quarantine from automatic processing by default) is **unchanged** by this authorization: the test observes it; it neither relaxes it nor converts it into a permanent policy.

## 14. Implementation-authority boundary

**This record grants AUTHORITY TO RUN A CONTROLLED TEST. It does not grant IMPLEMENTATION AUTHORITY.**

- D16 §15/§20 stand verbatim: serving/API implementation may NOT begin; incremental-ingestion implementation may NOT begin; persistence implementation may NOT begin; UI implementation may NOT begin.
- The D16-13 later-authority enumeration (six items) is **unmodified** by this record. D19 is a separate, narrower, additive test authority — it is none of those six items and is not the D16-03a disposition decision itself (item 3). When the D20 test evidence exists, D16-03a proceeds to its own future authority decision under the house pattern (decision input → explicit authorization → scoped work → evidence → remote verification).
- The minimal test harness permitted in §11(3) is **test-observation instrumentation**, not an implementation of any D16 architecture component: the production registry and classifier remain contract-only; nothing test-scoped may be promoted to a production path without a separate explicit implementation authorization.
- D14's non-authorizations stand unchanged; D19 removes nothing and expands nothing beyond §11.

## 15. Final authority disposition

> ### **A. AUTHORIZED — NARROW CONTROLLED TEST.**
> Authority to run the isolated synthetic changed-content experiment defined in §6, exactly within the scope of §11 (five items), subject to the exclusions of §12 and the canonical-data protection invariants of §13. The experiment produces **evidence only** (R1; R3 input; R4 input; R2 confirmed not required). It decides **nothing**: D16-03a remains EVIDENCE REQUIRED until a future authority decision made against the test evidence. **IMPLEMENTATION AUTHORITY = NOT GRANTED** — unchanged from D16 §15/§20.

The evidence supports this authorization: D18 established necessity (no other evidence path exists short of a real-world occurrence), full isolatability, the required mechanics (test-scoped seed for the contract-only registry), and the evidence the experiment must produce. The scope is the minimum necessary to observe R1–R4.

## 16. Evidence required from the subsequent test (D20)

The authorized test must produce and durably preserve:

1. **R1 — the concrete byte-pair record:** identity fields of I; sha256(B1), sha256(B2); the byte-level diff; statement that both are synthetic and no production bytes were used.
2. **R3 input — test-scoped registry before/after state:** the D16-02-shaped seed for B1; its state after S2; the recorded determination of whether the existing contract ingredients suffice to represent the eight criteria (§9) — with any insufficiency named precisely.
3. **R4 input — prior-data and serving observations:** P1 digests before/after S2 (byte-identity proof); the held/blocked observation for B2 (never silently unchanged; never silently reprocessed); the serving-representation observation (§10(3)); the documented trust-marker determination (§10(4)); the explicit statement that any post-disposition policy remains a subsequent authority decision.
4. **R2 confirmation:** the record's statement that no semantic-equivalence judgment was required or made (A/B only, per §8).
5. **Isolation attestation:** before/after digests of the production corpus interface, `evidence/inventory/`, the M2 package, and all I4/I5 evidence — all unchanged; fresh roots only; synthetic data only.
6. **Test record:** a D20 investigation record documenting the run, its state, the findings, and the remote-verified preservation of the evidence package (house pattern), with the test explicitly labeled non-canonical.

## 17. Artifact inventory

**This record:** `docs/architecture/D19_CHANGED_CONTENT_CONTROLLED_TEST_AUTHORITY_DECISION.md` (the only mutation).
**Governing inputs (verified, §2/§3):** D16 (blob `1b6e2faf9bdf7cdd6da0210f0ebb48c1d2109b5c`); D17 (blob `3eef98b8f24bdc7a0fade56d32d4a2d1e7370b99`); D18 (commit `80fc3b8dd3ec814e24b7f76d1d383bc10b5de59c`, blob `e1e7cab083c03c8d732578b0d07fe03f35c81636`); intent artifact (blob `41ad2740dd01620e547fc5a4659cafd53f28d534`, SHA-256 `7e4a14f4e6fd667d415b7351b58a266c5f0f15d494ba903fd132a15222830096`); D15 (blob `79157b82355caf7579ec63b126a23e1a133b79ba`).
**Baseline:** `origin/main` = `6784efdc7173e1684df44bc8b4f7a1cc7d40e238` (D17); session branch = `80fc3b8…` (D18) at decision time.
**Next permitted task:** **D20 — controlled changed-content evidence test** (executes exactly the §11 scope; evidence-only; then the D16-03a disposition decision remains a separate future authority gate).
