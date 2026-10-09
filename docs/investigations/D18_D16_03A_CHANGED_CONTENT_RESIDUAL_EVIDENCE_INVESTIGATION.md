# D18 — D16-03a CHANGED-CONTENT RESIDUAL EVIDENCE INVESTIGATION (G1–G4)

**Date:** 2026-10-09
**Mode:** INVESTIGATION-ONLY. Documentation-only mutation (this artifact only). No implementation of any kind (no serving, incremental ingestion, persistence, registry change, UI, API, or product behavior). No implementation authority granted. The governed historical dataset was not altered in any way.
**Disposition summary (full statement in "Final disposition"):** G1 = NOT ESTABLISHED; G2 = NOT ESTABLISHED; G3 = PARTIALLY ESTABLISHED; G4 = PARTIALLY ESTABLISHED. D16-03a reconciliation outcome: **B — PARTIALLY RESOLVED — SPECIFIC REMAINING EVIDENCE REQUIRED**. A controlled synthetic changed-content test is determined to be the only remaining evidence path (documented in the Controlled-test determination; NOT performed).

---

## 1. Baseline verification (Phase 0)

| Item | Value |
|---|---|
| Repository | `ramkivs/nse-historical-data-engine` (GitHub) |
| Remote | `https://github.com/ramkivs/nse-historical-data-engine` |
| Ref | `refs/heads/main` |
| Expected HEAD | `6784efdc7173e1684df44bc8b4f7a1cc7d40e238` |
| Verified `origin/main` | `6784efdc7173e1684df44bc8b4f7a1cc7d40e238` — **MATCH** (gh api, 2026-10-09) |
| Remote session branch `arena/9021d1a1-nse-historical-data-engine` | `6784efd…` (same commit) |
| `6784efd` parent | `0c2102425d9995e07d1f57a08715435c3f0bc7f9` (D16 commit) — chain intact |
| Local state at start | 8th sandbox `.git` rollback (shallow @ `89ce965c`, stale marks); repaired non-destructively (unshallow → ancestry check YES → `update-ref` → `read-tree`); no destructive operations |
| Local HEAD after repair | `6784efd…`, tree `3287b190d80d79da450d51e2fc3a52a56a3fbeeb` |
| Worktree state | clean except pre-existing untracked `_transfer_delivery/` (never committed) |

**Governing artifacts verified (local HEAD blob = remote main blob = worktree bytes):**

| Artifact | Blob |
|---|---|
| `docs/product/HISTORICAL_ENGINE_PRODUCT_AND_SERVING_ARCHITECTURE_INTENT.md` | `41ad2740dd01620e547fc5a4659cafd53f28d534` (SHA-256 `7e4a14f4e6fd667d415b7351b58a266c5f0f15d494ba903fd132a15222830096`) |
| `docs/investigations/POST_I5_SERVING_INCREMENTAL_PRODUCT_ARCHITECTURE_INVESTIGATION.md` (D15) | `79157b82355caf7579ec63b126a23e1a133b79ba` |
| `docs/architecture/POST_I5_SERVING_INCREMENTAL_PRODUCT_ARCHITECTURE_AUTHORITY_DECISION.md` (D16) | `1b6e2faf9bdf7cdd6da0210f0ebb48c1d2109b5c` |
| `docs/investigations/D17_POST_D16_RESIDUAL_EVIDENCE_AUTHORITY_INVESTIGATION.md` (D17) | `3eef98b8f24bdc7a0fade56d32d4a2d1e7370b99` |

Historical relationship intact: `6784efd (D17) → 0c21024 (D16) → d60eb3d (D15) → e81baef (intent preservation) → e7a9deb (D14) → 5db377e (D13) → 8105e76 (D12) → 1507b74 (D11) → … → 410135d (D01 baseline)`.

**Exact artifacts inspected this investigation (read-only):** D01 `evidence/inventory/` (`file_inventory.json` — programmatic analysis; `inventory_summary.json`; `duplicate_dates.json`; `INVENTORY_REPORT.md`); full repository history (27 commits — deletion census, per-commit semantic sweeps, file-touch history); `tools/i4_runner/` (`i4_preflight.py` PF-10/11/12; `i4_reconcile.py` module contract; `i4_runner.py`/`i4_inputs.py` context from D17); `tests/test_i4_runner.py` (mismatch test fixtures); `tests/test_w2_stream_equivalence.py` (module contract); `tests/test_i4_replay_qualification.py` (mismatch test names); `src/nse_engine/` (`rows.py`, `w2_stream.py`, `calendar.py`, `reconcile` absence check; registry-code absence sweep); D05 `docs/specs/D05_CANONICAL_MODEL_SPEC.md` (supersession/invalidation sweep); D16 §7 (D16-02/03/03a/04/05/07/08/09/10/12/13), §10/§15; D17 §5/§13; intent §6.

## 2. Scope / non-goals

**Scope:** resolve, as far as the repository and its durable evidence permit, the four evidence gaps G1–G4 identified by D17 for D16-03a; reconcile D16-03a's disposition; determine whether a controlled synthetic test is the remaining evidence path (document, do not perform); produce the final evidence matrix.

**Non-goals (binding for this record):** no implementation of serving / incremental ingestion / persistence / registry / UI / API / product behavior; no implementation authority granted or implied; no alteration of the governed historical dataset; no creation, modification, replacement, deletion, quarantine, reprocessing, or republication of any production/canonical archive or canonical output; no invented evidence; absence of evidence is never treated as proof of a policy; no authentication / RBAC / multi-user / PostgreSQL / enterprise architecture introduced or implied; no search for or introduction of internal conversational NP/D8 identifiers (not repository facts); no policy selected for convenience; D16's interim fail-closed hold is NOT promoted to a permanent policy by this record; no modification of any file other than this artifact.

## 3. G1 findings — changed-archive instance (Phase 1)

**Question:** is there durable repository evidence that an archive with the same governed archive identity/date but different content has actually existed or been processed?

**Positive evidence inspected (and what it shows):**

1. **D01 live inventory (programmatic analysis of `evidence/inventory/file_inventory.json`, 2,462 records):**
   - distinct archive sha256 = **2,462** (0 duplicate checksums — matches `inventory_summary.json` `duplicate_checksum_count: 0`);
   - distinct `date_from_filename` = **2,462** (0 duplicate dates — `duplicate_date_count: 0`; `duplicate_dates.json` = `[]`);
   - **same apparent identity (root, file_name, date_from_filename) with a different content sha256 = 0 records**;
   - same (root, relative_path) with a different content sha256 = 0 records.
   The D01 baseline contains no same-identity/different-content pair, and nothing has ever been added to it.
2. **Inventory history:** `evidence/inventory/` was touched by exactly **one** commit in all 27 commits of the repository — `410135d "Establish NSE 10Y archive evidence baseline"` — and has never been modified since.
3. **Corpus pinning:** PF-10 (discovered set == D01 set, both directions, gating), PF-11 (0 duplicate checksums / 0 duplicate dates, gating), PF-12 (per-archive observed sha256 == D01 sha256, gating, `raise _fail` on any mismatch) — any corpus drift, including a content change under an existing identity, is a run-halting gated divergence in the existing design.
4. **Full-history deletion census:** across all 27 commits (all refs, including the `d08-transfer-2026-10-06` tag commit `a1f0b58`, which is in mainline history), **zero files were ever deleted** — no historical artifact was removed that could have concealed a changed-content record.
5. **Full-history semantic sweep** (all commits, keywords: changed / modified / replacement / replaced / supersede / superseded / reprocess / reprocessed / requalification / quarantine / CHANGED / semantic equivalence / same archive / same date / same filename / content mismatch / sha256 mismatch / hash mismatch): every hit for "changed archive", "different content", "same archive", "reprocessed" occurs **only in the newest commit** (`6784efd`) — i.e., in the D16/D17/intent contract language itself. No earlier commit records a changed-content event. "sha256 mismatch" / "hash mismatch" hits are confined to: `i4_preflight.py` (gate code), `tests/test_i4_runner.py` (hypothetical gate tests — see 6), the Windows launch script guard wording, `i4_output.py` (package-manifest hash verification), the runner README (gate documentation), and `d03_fixtures.py` (fixture-scan counters).
6. **The only "different bytes under same identity" anywhere in the repository is a hypothetical test fixture:** `tests/test_i4_runner.py` rewrites one archive of a **synthetic in-test corpus** with different bytes ("Rewrite one archive with different bytes but keep the D01 sha256 (stale expectation)") and asserts the preflight **fails closed** with "sha256 mismatch". Per the task's own rule, this hypothetical test is **not** evidence that an actual changed archive instance occurred: it exercises the detection gate on a fixture, records a halt, and records **no disposition** of any kind. (All other "mismatch" tests — replay-qualification fingerprint/run-id/corpus-identity mismatches, row-width mismatch quarantine — are likewise detection-of-drift or parse-failure records, not changed-archive instances.)
7. **Run/package records:** the closed I4/M2 run evidence (`INPUT_MANIFEST.jsonl`, `GOVERNED_INPUTS.json`, `RUN_RECORD.json`, `PACKAGE_MANIFEST.sha256`, reconciliation, D11/D12/D14) records a single pinned corpus (`archive_set_digest 54d81507…`), 2,462/2,462 members, 0 quarantined, 0 gating divergences — no changed-content event in any run or package record. I4 and I5 are closed.

**Evidence that exists:** the complete negative proof of non-occurrence *within the pinned corpus and its history* (items 1–5, 7): the corpus has contained exactly 2,462 distinct-content archives with 2,462 distinct dates since the D01 baseline; every mechanism that could have observed a change is fail-closed; nothing was ever deleted from the repository; no run processed or recorded a changed archive.

**Evidence that is absent:** any actual (non-hypothetical) instance of an archive with the same governed identity and different content — its existence, observation, processing, or recorded disposition. The hypothetical test fixture (item 6) is expressly not such evidence.

**G1 = NOT ESTABLISHED.**

## 4. G2 findings — semantic-equivalence definition/capability (Phase 2)

**Question:** does the repository define or implement a governed method for determining whether two different-content archives are semantically equivalent?

**Five-level distinction (each level assessed against repository evidence):**

| Level | Meaning | Status | Evidence |
|---|---|---|---|
| A. Byte/content identity | "are these the same bytes" | **ESTABLISHED (at this level only)** | Archive sha256 (D01 per-archive `sha256`; PF-12 observed-vs-expected, gating); member raw/LF digests (engine-recorded vs runner-computed, Tier G cross-check, `i4_reconcile.py`) |
| B. Archive identity | "is this the same archive (apparent identity)" | **ESTABLISHED (at this level only)** | (root, relative_path, file_name, date_from_filename) — D01 record shape; `discover_archives`; PF-10 set equality |
| C. Row-level equality | "do these rows match" | **NOT established as a comparison method** | The canonical row model (D05) is a **verbatim as-published** model — no normalization step exists anywhere (nothing reinterprets, re-derives, or extends governed output — D08 MD-07). The only row-level fail-closed concept is structural parse quarantine (D05 §7/§8; `rows.py` `QuarantineRecord`). The D02 `row_offset`/`raw_row_hash` proposal was **never adopted** (D08 §4/§18; D15 §12 boundary). No cross-archive row comparison capability exists. |
| D. Canonical-data equivalence | "are these two canonical datasets equivalent" | **Exists only incidentally, as determinism — not as an equivalence method** | R6 replay qualification proves **byte-exact rebuild from identical pinned bytes + identical versions** (same-input determinism). `test_w2_stream_equivalence.py` proves byte-level equivalence of **two implementations of the same computation** (batch vs streaming W2) over the **same** inputs. Neither compares two *different* canonical datasets; neither is a governed equivalence method. |
| E. Semantic equivalence of source archives | "do these two different-content archives mean the same data" | **NOT ESTABLISHED** | No rule, tool, contract, or record anywhere in the repository (docs, src, tools, tests, evidence) defines when two different byte sequences are semantically equivalent, nor provides any capability to decide it (e.g., re-zip/re-encode equivalence, re-stamped-date equivalence). The corpus is documented as **not byte-uniform** (D02: two header variants, a 2-digit-year date file) with the argument that reprocessing "must be detectable" — detectability, not equivalence, is what that record addresses. |

Nothing in A–D is promoted into E by this record; A–D are recorded at their own levels only.

**G2 = NOT ESTABLISHED** (no governed semantic-equivalence method or definition exists for different-content source archives).

## 5. G3 findings — post-disposition registry record shape (Phase 3)

**Question:** does existing repository evidence define the durable registry representation after an archive is classified CHANGED?

**What the D16-02 content contract establishes (re-verified verbatim, D16 §7 D16-02):** each registry entry records — archive identity (root, relative_path, file_name, date_from_filename); content identity (archive byte sha256); processing result (partition, rows, quarantined); **version bindings** (engine fingerprint, runner fingerprint, canonical `spec_version`, processing contract version); run provenance (run_id, package manifest digest); and **status (processed / pending / flagged)**. The registry is the single authoritative "processed under X" statement, updated only by a successful validated incremental publication.

**Field-by-field determination against the task's eight criteria:**

| Required distinction | Defined by existing evidence? |
|---|---|
| Archive identity | **YES** — D16-02 identity fields (backed by D01 record shape) |
| Observed content identity | **YES** — D16-02 "content identity (archive byte sha256)" |
| **Prior processed content identity (distinct from observed)** | **NO** — the contract carries one content sha256 per entry (the processed one); there is no field pair expressing "processed as X, now observed as Y" |
| Current disposition | **PARTIAL** — status set is (processed / pending / flagged); "flagged" can carry a CHANGED hold, but no CHANGED-specific disposition state exists, and no post-disposition state (conflict-acked / replaced / superseded / quarantined-terminal) is defined |
| Processing status/result | **YES** — result fields (partition, rows, quarantined) + status |
| Quarantine/hold status | **PARTIAL** — "flagged" expresses a hold; no quarantine-specific status or reason field is defined |
| Version bindings | **YES** — D16-02 binding fields (backed by `GOVERNED_INPUTS.json`/`RUN_RECORD.json` structure) |
| Run provenance | **YES** — run_id + package manifest digest |
| **Relationship to previously accepted canonical data** | **NO** — no field links a registry entry (or a new entry for the same identity) to the previously accepted entry's canonical data, partition contribution, or publication |

**Additional facts:** the registry exists **only as a contract** — no registry code, schema, type, model, or fixture exists anywhere (sweep: the only "registry" in `src/` is the unrelated calendar **label** registry, `DEC12_CIRCULAR_REGISTRY.json`); per-run ingredients (`INPUT_MANIFEST.jsonl`, `GOVERNED_INPUTS.json`, `RUN_RECORD.json`) establish the field *vocabulary* but are run-scoped, not durable cross-run records (D15 gap #4: ABSENT → EXTENSION REQUIRED); anomaly/failure records in the repository (preflight gating divergences, row quarantines) are run-scoped findings, not durable post-disposition registry records.

**Determination:** the pre-disposition ingredients are fully specified (and one CHANGED archive is representable *today* only as a `flagged` entry whose content sha256 would be the **new** observed bytes — with the prior entry's identity/content implicitly "the other one"), but **no durable post-disposition record shape exists**: nothing defines how an observed-but-different content identity is recorded alongside the prior one, how the disposition state is expressed, or how the relationship to previously accepted canonical data is captured.

**G3 = PARTIALLY ESTABLISHED** (ingredients + interim flagged representation YES; post-disposition record shape NO). No new schema is designed or implemented by this record.

## 6. G4 findings — prior-data authority / serving trust (Phase 4)

**Question:** does existing authoritative evidence define what happens to previously accepted canonical data and serving visibility when a later archive with the same governed identity has different content?

**What is governed (re-verified from the cited records):**

1. **During the D16-03 hold (interim state):** the prior result **stays intact** (D16-03: "the prior result stays intact"); the qualified baseline is **immutable** (D16-07 class (1)); unaffected archives are **never re-read or re-parsed** (D16-05). So while a CHANGED archive is held, previously accepted canonical data is, by default, untouched and undisturbed.
2. **Serving visibility during the hold:** serving reflects durable classes (1)+(2)+(3) only, and (4) is always a pure derivation (D16-07/09) — therefore prior canonical rows **remain visible** through serving; the CHANGED state itself is visible as **processing/quality metadata** — registry status + flagged findings are exposed via Q8 (quarantined counts, unresolved-state records), Q9 (archive inventory + registry status/version bindings), Q10 (evidence views) (D16-08/10).
3. **Canonical-model structure:** D05 rows are **append-only per observed** ("Transitions between (symbol, series) states are events, not mutations"); D05 contains **no supersession, invalidation, staleness, retraction, or deprecation rule** (sweep: zero matches). The model has no mechanism to mark an accepted row as un-accepted.
4. **Environment boundary:** raw archive/member bytes remain in Windows corpus custody (D15 #15); nothing about raw-content visibility is in scope (D16-08).

**What is NOT governed (the six task sub-questions):**

| # | Sub-question | Governed? |
|---|---|---|
| 1 | Does previously accepted canonical data remain authoritative (after a CHANGED archive is *resolved*)? | **NO** — governed only during the hold (intact); post-resolution authority is undecided (D16-03a) |
| 2 | Is it invalidated? | **NO** — no invalidation rule exists anywhere (D05 append-only; D16 silent post-hold) |
| 3 | Is it superseded? | **NO** — no supersession semantics exist (sweep: zero; G2-E absent) |
| 4 | Does it remain visible to serving? | **PARTIAL** — visible during the hold by construction (serving reflects (1)+(2)+(3)); post-resolution visibility is undecided |
| 5 | Must serving expose a trust/status marker on prior data? | **NO** — registry status + findings are exposed (Q8/Q9/Q10), but no trust marker on the *prior data itself* is defined |
| 6 | Are any of those outcomes governed? | Only the **hold state** (1-intact / 4-visible / flagged-findings-visible) is governed; every **post-disposition** outcome is open to D16-03a |

No policy is inferred from absence: the statements above record exactly what the cited records do and do not say.

**G4 = PARTIALLY ESTABLISHED** (hold-state prior-data and serving-visibility governance YES; all post-disposition authority/trust outcomes NO).

## 7. D16-03a reconciliation (Phase 5)

Using only verified evidence from Phases 1–4:

- **G1 NOT ESTABLISHED** — no actual changed-archive instance exists in the corpus, its pinned history, its run evidence, or anywhere in the 27-commit repository history; the only same-identity/different-bytes artifact is a hypothetical detection-gate test fixture, which records no disposition.
- **G2 NOT ESTABLISHED** — no governed semantic-equivalence method exists, so no candidate outcome conditioned on semantic equivalence is decidable; A–D-level identity/determinism capabilities exist only at their own levels.
- **G3 PARTIALLY ESTABLISHED** — the registry content contract specifies all pre-disposition fields and an interim `flagged` representation, but no post-disposition record shape (observed-vs-prior content pair, disposition state, prior-data relationship) is defined anywhere.
- **G4 PARTIALLY ESTABLISHED** — the interim hold state (prior data intact; prior data visible; CHANGED visible as flagged finding) is governed; every post-resolution outcome (authority / invalidation / supersession / visibility / trust marker) is open.
- **The governing intent (adopted unmodified by D16 §4) verbatim:** "The precise disposition for changed content remains a future contract/governance question. Possible outcomes could include explicit conflict, reprocessing, replacement/versioning, or quarantine, **but this document does not select one**."

**Interim rule preserved (binding statement):** the PF-12 fail-closed gate behavior and the D16-03 "held + flagged, quarantined from automatic processing by default" treatment remain **interim defaults only**. They are detection + hold mechanics, and this record — like D16 and D17 — does **not** treat them as, or promote them into, proof of a permanent changed-content policy.

**Reconciliation outcome (exactly one, from the task's list):**

> **B — PARTIALLY RESOLVED — SPECIFIC REMAINING EVIDENCE REQUIRED.**

The partial resolution is the precise, verified characterization of each gap: what exists (the complete negative proof of non-occurrence in the pinned corpus and history; A–D-level identity/determinism; the pre-disposition registry contract; the governed hold state), what is specifically missing (the four items below), and why existing durable evidence cannot close them. The specific remaining evidence required for D16-03a:

1. **(R1, from G1)** an actual changed-archive instance — or an authority-directed concrete hypothetical with named identity fields and both byte sequences (B1, B2) — so that a disposition is decided *against* a case rather than in the abstract;
2. **(R2, from G2)** only if the chosen outcome is conditioned on it: a governed definition of semantic equivalence for this corpus (no capability exists to decide equivalence of different bytes);
3. **(R3, from G3)** the post-disposition registry record shape (observed-vs-prior content identity, disposition state, relationship to previously accepted canonical data) — a spec artifact the decision must produce;
4. **(R4, from G4)** the post-disposition statement on prior canonical data (remains authoritative / invalidated / superseded), serving visibility, and any trust/status marker — a spec artifact the decision must produce.

D16-03a is **not** resolved by this record, and this record does not claim it is.

## 8. Controlled-test determination (Phase 6)

Applicability condition met: Phases 1–4 demonstrate that G1–G4 **cannot** be resolved from existing durable evidence (G1: no instance exists and the corpus is pinned; G2: no capability exists; G3/G4: post-disposition shapes are contract gaps, not evidence gaps).

**Determination: resolving D16-03a would require either (a) a real-world changed-archive occurrence (outside repository control), or (b) a controlled synthetic changed-content test. Such a test is NOT performed by this record.** Its required shape, documented as an investigation finding only:

- **Why existing evidence is insufficient:** the corpus has been pinned since D01 (PF-10/11/12 gate any drift; 0 same-identity/different-content pairs; 2,462 unique checksums/dates); I4/I5 are closed; nothing in 27 commits of history records a change; Arena has no filesystem reach to the Windows-custody corpus bytes, so no production byte pair can be assembled here; and the D16-02 registry + D16-03 classification exist only as contracts (no code), so "what happens when CHANGED presents" has never been observed even hypothetically end-to-end.
- **Exactly what experiment would be required:** a two-state synthetic test in a **fresh root, outside the production corpus and the M2 package**:
  - **S1:** a synthetic archive A (governed identity: root, file_name, date_from_filename) with bytes B1, processed under the existing I4 mechanics into a fresh out-root; capture its canonical outputs P1 and its per-run records (INPUT_MANIFEST/GOVERNED_INPUTS/RUN_RECORD); from those records, construct a **synthetic registry seed** entry (D16-02 field shape) stating "processed under" the M2-bound version set.
  - **S2:** the same governed identity with modified bytes B2 (e.g., one data row altered, re-zipped); present S2 to the classification mechanics with the seeded registry; observe and record the full behavior chain.
  - **Capture:** the byte-pair record (identity fields; sha256(B1), sha256(B2); byte-level diff); pre/post registry state; the observed detection + hold behavior (CHANGED detected; flagged; never silent; P1 byte-identical before/after); and — to inform the disposition decision — the data/serving impact of each of the four intent candidate outcomes (explicit conflict flag / reprocessing / replacement-versioning / quarantine) as applied to the concrete pair.
- **What repository/dataset state it would need to touch:** only the new synthetic corpus root, the new out-root, and the synthetic registry seed. It must NOT touch: the production corpus (Windows custody — out of reach here in any case), `evidence/inventory/` (D01), the M2 package, any I4/I5 evidence, the canonical dataset, or any file in the authoritative tree.
- **What authority would be required:** (i) an explicit authority to conduct a controlled synthetic test (test scope, evidence-only outputs); (ii) because the registry and the D16-03 classifier are not implemented, either a test-scoped implementation authorization for a minimal registry seed + classification against the synthetic corpus, or an explicit authority to seed the registry manually and run the existing preflight/runner mechanics as-is (which would demonstrate detection/halt only, not end-to-end hold+publication behavior); (iii) an explicit confirmation that results are evidence-only and never canonical (never enter the production corpus, D01, M2 package, or any I4/I5 evidence).
- **What evidence the experiment would need to produce:** (a) the concrete byte-pair record (R1); (b) pre/post registry state in D16-02 field shape, including the observed-vs-prior content pair (R3 input); (c) observed interim-hold behavior with prior outputs proven byte-identical (G4 hold-state confirmation at runtime); (d) per-candidate-outcome impact statements on prior canonical data and serving visibility (R4 input); (e) an isolation attestation: production corpus / D01 / M2 package / I4-I5 evidence digests before and after, unchanged.
- **Whether the experiment can be isolated from the canonical dataset:** **YES** — entirely, by construction (fresh roots, synthetic corpus, synthetic registry, evidence-only outputs), with the hard boundary that its results never enter the canonical dataset or any qualified evidence, and that no I4/I5 artifact is read-modified or re-run.

## 9. Evidence matrix (Phase 7)

| Gap | Question | Evidence inspected | Finding | Status | Remaining requirement |
|---|---|---|---|---|---|
| G1 | Did a same-identity/different-content archive actually exist or get processed? | D01 live inventory (programmatic: 2,462 records; 0 same-identity/different-content pairs; 2,462 unique sha256; 2,462 unique dates); `inventory_summary.json`/`duplicate_dates.json`; inventory commit history (single baseline commit `410135d`); full 27-commit history (0 deleted files; per-commit semantic sweeps); PF-10/11/12 gate code; `tests/test_i4_runner.py` hypothetical mismatch fixture (excluded per rule); I4/M2 run + package records; D11/D12/D14 | No actual instance anywhere; complete negative proof of non-occurrence in the pinned corpus and its history; only a hypothetical detection-gate fixture exists | **NOT ESTABLISHED** | (R1) an actual instance, or an authority-directed concrete byte pair |
| G2 | Is there a governed semantic-equivalence method for different-content archives? | D01 sha256/member-digest contracts; PF-12; `i4_reconcile.py` (same-bytes verification tiers A/G/C/E); D05 verbatim as-published model (no normalization); D02 `raw_row_hash`/`row_offset` (never adopted); R6 replay (same-input determinism); `test_w2_stream_equivalence.py` (same-computation implementation equivalence); D02 corpus non-uniformity record | A (byte identity) and B (archive identity) established at their own levels; C/D exist only incidentally as determinism; E (semantic equivalence of source archives) absent; nothing promotes A–D into E | **NOT ESTABLISHED** | (R2) only if a chosen outcome is conditioned on it: a governed semantic-equivalence definition |
| G3 | Is the durable post-disposition registry record shape defined? | D16-02 content contract (re-verified verbatim); `INPUT_MANIFEST.jsonl`/`GOVERNED_INPUTS.json`/`RUN_RECORD.json` field vocabulary; registry-code absence sweep (only the unrelated calendar label registry exists); D15 gap #4 (registry ABSENT → EXTENSION REQUIRED) | Pre-disposition fields all specified (identity, content sha256, result, version bindings, run provenance, status processed/pending/flagged); interim `flagged` representation of a CHANGED hold exists; **no** observed-vs-prior content pair field, **no** CHANGED-specific disposition state, **no** relationship-to-prior-canonical-data field; registry is contract-only, not implemented | **PARTIALLY ESTABLISHED** | (R3) the post-disposition record shape, produced by the D16-03a decision |
| G4 | What happens to prior canonical data and serving visibility? | D16-03 (prior result stays intact); D16-07 ((1) immutable; (4) pure derivation; conflict rule); D16-05 (unaffected archives never re-read); D16-08/09/10 (serving reflects (1)+(2)+(3); Q8/Q9/Q10 exposure of registry status + findings); D05 (append-only; zero supersession/invalidation/staleness rules); D15 #15 (environment boundary) | Hold state governed: prior data intact, prior data visible, CHANGED visible as flagged finding via Q8/Q9/Q10; **no** post-resolution outcome governed (authority / invalidation / supersession / visibility / trust marker all open) | **PARTIALLY ESTABLISHED** | (R4) the post-disposition statement on prior-data authority, serving visibility, and trust marking, produced by the D16-03a decision |

## 10. Limitations

1. This record is limited to repository-internal durable evidence; the Windows-custody corpus is unreachable from this environment (D15 #15), so any evidence that could exist only in the corpus environment (e.g., an out-of-repository change event) is not inspectable here — this strengthens, not weakens, the G1 finding, because the repository's own pinning gates (PF-10/11/12) would have recorded any such event as a gated divergence in any run.
2. The hypothetical test fixture in `tests/test_i4_runner.py` was inspected and classified as non-evidence of an instance per the task's rule; its gate behavior (fail-closed halt) is real evidence *about the gate*, nothing more.
3. G3/G4 "PARTIALLY ESTABLISHED" determinations describe exactly which sub-questions are and are not governed; they are not partial resolutions of D16-03a itself — only the gaps are characterized.
4. The controlled-test determination is a documented finding, not a performed test, and authorizes nothing: it states what a future authority decision would need to cover.
5. No file, dataset, or evidence artifact was modified by this investigation; the single mutation is this artifact.

## 11. Final disposition

- **Gap results:** G1 = NOT ESTABLISHED · G2 = NOT ESTABLISHED · G3 = PARTIALLY ESTABLISHED · G4 = PARTIALLY ESTABLISHED.
- **D16-03a current disposition:** **B — PARTIALLY RESOLVED — SPECIFIC REMAINING EVIDENCE REQUIRED** (R1–R4, §7). D16-03a remains open; the D16 interim fail-closed hold (quarantine from automatic processing by default) stands as an interim default and is NOT a permanent policy.
- **Evidence now established:** the complete negative proof of non-occurrence (G1); the A–D identity/determinism boundary (G2); the pre-disposition registry contract + interim `flagged` representation (G3); the governed hold state for prior data and serving visibility (G4).
- **Evidence that remains unavailable:** an actual (or authority-directed concrete) changed-archive byte pair (R1); a semantic-equivalence definition, only if needed (R2); the post-disposition registry record shape (R3); the post-disposition prior-data/serving-trust statement (R4).
- **Separate authority decision required:** yes — to conduct the controlled synthetic test (with its test-scoped implementation question), and thereafter to make the D16-03a disposition decision itself. This record grants no authority.
- **Controlled test necessary:** yes — it is the only remaining evidence path short of a real-world occurrence (§8); not performed.
- **No implementation authority was granted** by this record; none was requested; D16 §15/§20 ("IMPLEMENTATION AUTHORITY = NOT GRANTED") stand unchanged.
- **No canonical dataset or product behavior was mutated:** no archive, canonical output, inventory, run record, evidence artifact, or code file was created, modified, replaced, deleted, quarantined, reprocessed, or republished; the single mutation is this artifact.
- **Final status (evidence-supported vocabulary only):** **COMPLETE / DURABLE / REMOTELY VERIFIED** (for this investigation record). D16-03a itself is **NOT** claimed resolved.

## 12. Artifact inventory

**This record:** `docs/investigations/D18_D16_03A_CHANGED_CONTENT_RESIDUAL_EVIDENCE_INVESTIGATION.md` (the only mutation).
**Governing inputs (verified byte-identical at `origin/main@6784efd`, §1):** intent artifact (blob `41ad2740dd01620e547fc5a4659cafd53f28d534`, SHA-256 `7e4a14f4e6fd667d415b7351b58a266c5f0f15d494ba903fd132a15222830096`); D15 (blob `79157b82355caf7579ec63b126a23e1a133b79ba`); D16 (blob `1b6e2faf9bdf7cdd6da0210f0ebb48c1d2109b5c`); D17 (blob `3eef98b8f24bdc7a0fade56d32d4a2d1e7370b99`).
**Evidence examined (read-only, as detailed in §1–§10):** `evidence/inventory/` (`file_inventory.json` programmatic analysis; `inventory_summary.json`; `duplicate_dates.json`; `INVENTORY_REPORT.md`); full 27-commit repository history (deletion census; per-commit semantic sweeps; `410135d` inventory baseline; `a1f0b58`/`d08-transfer-2026-10-06` mainline check); `tools/i4_runner/i4_preflight.py` (PF-10/11/12); `tools/i4_runner/i4_reconcile.py` (tier contract); `tests/test_i4_runner.py` (hypothetical mismatch fixture); `tests/test_w2_stream_equivalence.py`, `tests/test_i4_replay_qualification.py`, `tests/test_determinism.py`, `tests/test_header_and_widths.py` (mismatch/quarantine test census); `src/nse_engine/` (`rows.py` quarantine; `w2_stream.py`; `calendar.py` label-registry distinction; registry-code absence sweep); `docs/specs/D05_CANONICAL_MODEL_SPEC.md` (append-only structure; supersession/invalidation absence sweep); D16 §7/§10/§15; D17 §5/§13; intent §6; D02 (non-adopted `raw_row_hash`/`row_offset`; corpus non-uniformity); D08 (MD-07; §4/§18); D11/D12/D14 (closed run facts).
