# Post-I5 Serving / Incremental Ingestion / Product Architecture Investigation

**Status: RECORDED — investigation only. NO IMPLEMENTATION IS AUTHORIZED BY THIS INVESTIGATION.**
**Produced:** 2026-10-09 (Arena side, read-only investigation over `origin/main`).
**Target-intent reference:** `docs/product/HISTORICAL_ENGINE_PRODUCT_AND_SERVING_ARCHITECTURE_INTENT.md`
(verified in §5; **TARGET / INTENT ONLY — not implementation authority**).
**Mode:** READ-ONLY investigation; this record is the only mutation in scope (with the README record
bullet). Arena/Linux evidence domain only — no Windows filesystem, worktree, or execution state was
inspected or is claimed anywhere in this record.

---

## 1. Purpose

Determine, strictly from the authoritative repository plus the verified intent artifact, what already
exists for (a) serving/query, (b) incremental archive processing, (c) archive identity/fingerprint/
deduplication contracts, (d) durable output/persistence contracts, (e) serveable provenance/evidence,
(f) API/query/transport capability, (g) UI/product capability; then classify every gap (EXISTS /
REUSABLE / EXTENSION REQUIRED / ABSENT / DECISION REQUIRED / OUT OF SCOPE) and identify the minimum
future implementation scope **without authorizing it**.

## 2. Authoritative baseline (read-only, verified)

| Check | Observed | Verdict |
|---|---|---|
| Repository | `ramkivs/nse-historical-data-engine` | PASS |
| Origin URL | `https://github.com/ramkivs/nse-historical-data-engine.git` | PASS |
| Authoritative ref | `origin/main` = `e81baef05865e4f45f702b5dc4eb890fc4f6a6a6` ("docs: preserve post-I5 product serving architecture intent", author Ramaki, parent `e7a9deb1…` = D14) | PASS |
| Note on handoff value | The task expected `main = e7a9deb1…` (D14); main had advanced by exactly **one** commit — the intent artifact's own publication commit. Verified: that commit's delta is exactly the single artifact path. Treated as the artifact transfer channel, not a divergence anomaly. | recorded |
| Tree | `5be56154…`, 142 blobs (D14 tree 141 + intent artifact) | PASS |
| Ancestry | `e81baef ← e7a9deb (D14) ← 5db377e (D13) ← 8105e76 (D12) ← …` | PASS |
| I5 state in tree | D14: I5 = 10-year full qualification, determination PASS, CLOSED / DURABLE / REMOTELY VERIFIED on main | PASS |
| Arena worktree | clean; only untracked `_transfer_delivery/` (staging, never committed) preserved | PASS |

## 3. I5 boundary (observed and honored)

I5 is a **determination-only** gate over the completed I4/M2 10-year result (D14). This investigation:
did not re-run the 2,462 archives; did not re-run M2, replay, reconciliation, or memory measurement;
did not modify the qualified corpus or any qualified artifact; did not reinterpret I5 as an execution
phase. The qualified baseline (run `i4-20261008-M2`; 2,462 members; 5,689,949 rows; 12 partitions;
package 4,948 files / 21,119,807,344 bytes; manifest `e7c7e4c8…`; engine `d3269b73…`; runner
`f3ebf624…`; corpus digest `54d81507…`; R6 PASS; D11 package `8e78fcc8…`) is the **starting point**
for every finding below.

## 4. Product scope / non-goals (binding for this investigation)

Single-user, personal-use application (intent §2/§12; task §3). Non-goals preserved as hard
constraints: no authentication, RBAC, multi-user support, PostgreSQL, enterprise deployment/identity
infrastructure, tenant isolation, organization/team administration, or enterprise-scale distributed
architecture — none is recommended, implied, or assumed by this record; the single-user simplicity
principle (intent §12) is carried as the grading constraint for any future design.

## 5. Verified intent-artifact identity (intake)

Transferred into the Arena environment via the authoritative Git channel (`origin/main` commit
`e81baef…`, the task's expected transfer), fetched, materialized from the authoritative blob, and
verified byte-identical:

| Field | Value |
|---|---|
| Exact path | `docs/product/HISTORICAL_ENGINE_PRODUCT_AND_SERVING_ARCHITECTURE_INTENT.md` |
| Filename | `HISTORICAL_ENGINE_PRODUCT_AND_SERVING_ARCHITECTURE_INTENT.md` |
| Size | 18,300 bytes (595 lines) |
| SHA-256 | `7e4a14f4e6fd667d415b7351b58a266c5f0f15d494ba903fd132a15222830096` |
| Git blob | `41ad2740dd01620e547fc5a4659cafd53f28d534` (worktree `git hash-object` == tree blob) |
| Remote commit | `e81baef0…` on `origin/main` (parent `e7a9deb1…`) |
| Content verification | Complete 595-line read: 17 sections — purpose; product scope/non-goals; initial baseline; target architecture; separation of responsibilities; incremental model; version awareness; serving model; UI target (Dashboard/Data Explorer reference points); write/read data-flow separation; "what must not be assumed yet" (incl. **PostgreSQL is not a target requirement**); single-user simplicity; relationship to I5; 13 future questions; 15 non-drift rules; lifecycle; status. |
| Classification confirmed | **TARGET / INTENT ONLY** — artifact §1/§17: not implementation authority, not technology selection, no persistence/API/UI authority, does not reopen I5, does not authorize production. |

Only after this verification was the artifact used as the target-intent reference (§6–§14).

## 6. Target architecture (from the verified artifact)

Initial baseline: 2,462 archives → Historical Data Engine → **Authoritative Durable Historical
Dataset** → Query/API → UI. Future arrival: archive → discovery → identity/fingerprint/dedup →
(already processed → SKIP | new/changed → incremental process) → validation/evidence → durable
publication → query/API/UI. Critical boundaries (intent §3/§5/§8): the UI must not regenerate the
10-year corpus; the UI must not become the processing engine; the API/query layer is a **consumer**
of the durable dataset, not an owner of historical computation; the write/ingest path and the
read/serve path stay separated even in a single-user local application.

## 7. Archive discovery findings

| Finding | Evidence (path) | Classification |
|---|---|---|
| Governed per-archive inventory: 2,462 records with `root`, `relative_path`, `file_name`, `size_bytes`, `date_from_filename` (governed date), `sha256`, `detected_format`, `row_count`, `bad_rows`, `headers`, `header_signature`, `date_values`, `series_counts` | `evidence/inventory/file_inventory.json`; summary/report `INVENTORY_REPORT.md` (0 errors, 0 duplicate checksums, 0 duplicate dates, 3 schema variants, coverage 2016-09-20 → 2026-09-18) | **A. EXISTS** |
| Archive discovery from declared corpus roots; governed single-`.csv`-member extraction (CRC-checked, verbatim, never derived) | `tools/i4_runner/i4_inputs.py` (`discover_archives`, `csv_member_names`, `read_member_bytes`) | **A. EXISTS / B. REUSABLE** |
| Whole-set discovery assertion: discovered set must equal the inventory set **both directions**, no duplicate checksums/dates; every archive byte-hashes to the D01 value; opens with exactly one governed member | `tools/i4_runner/i4_preflight.py` (PF-10/PF-11/PF-12, all fail-closed gating) | **A. EXISTS / B. REUSABLE** (as the correctness core of incremental discovery) |
| Path/name contract: file naming + governed `date_from_filename` (never parsed from a name at run time, D05 §3.4/§7.2) | `i4_inputs.py` `build_source`; D05 spec | **A. EXISTS** |
| Incremental discovery mode (scan → diff against processed set → new arrivals): not present; current discovery is a full-corpus equivalence assertion | — | **C. EXTENSION REQUIRED + E. DECISION REQUIRED** (discovery mechanism = intent Q4) |

## 8. Identity / fingerprint / deduplication findings

The repository **explicitly distinguishes** these identity concepts (task §9):

| Concept | Existing contract | Evidence | Classification |
|---|---|---|---|
| Archive (apparent) identity | `file_name` / `relative_path` + governed `date_from_filename` | D01 inventory; `INPUT_MANIFEST.jsonl` per-archive record | **A. EXISTS** |
| Archive content identity | per-archive byte `sha256` (D01 inventory value **and** independently recomputed observed bytes; declared basis `D01-inventory`); per-member `sha256` raw + LF-normalized | D01 inventory; `i4_inputs.py` (`archive_sha256`, `file_facts`); `INPUT_MANIFEST.jsonl` (`archive_sha256_d01`, `archive_sha256_observed_raw_bytes`, `member_sha256_raw_bytes`, `member_sha256_lf_text`) | **A. EXISTS** |
| Duplicate detection | inventory-level: 0 duplicate checksums, 0 duplicate file dates; run-level: PF-11 cardinality/uniqueness, fail-closed | `INVENTORY_REPORT.md`; `i4_preflight.py` | **A. EXISTS** |
| Engine version | engine fingerprint over 17 declared modules (M2: `d3269b73…`) | `nse_engine.provenance.tool_fingerprint`; `i4_identity.py` | **A. EXISTS** |
| Runner/processing tool version | runner fingerprint over 6 declared modules (M2: `f3ebf624…`) | `tools/i4_runner/i4_identity.py` | **A. EXISTS** |
| Canonical contract version | `spec_version: "D05/1.0"` in the ADOPTED provenance block | D05 §8; `SourceDescriptor`/row provenance | **A. EXISTS** |
| Processing contract version | `CONTRACT_VERSION = "I4-runner/1.0"` bound in `GOVERNED_INPUTS.json` + `RUN_RECORD.json` | `i4_identity.py`; `i4_runner.py` | **A. EXISTS** |
| Evidence contract | MD-03 11-item logical envelope; MD-11 11-item retained-output contract (technology-neutral, decided) | D08 §§5/12 | **A. EXISTS (decided, technology-neutral)** |
| Run identity | `run_id` + composite run identity binding engine + runner + governed inputs + corpus archive-set digest; corpus digest `54d81507…` | `i4_identity.py` (`composite_run_identity`, `corpus_identity_digest`); D12 §3 | **A. EXISTS** |
| **Security** identity (distinct concept — the instrument, not the archive) | `SecurityIdentity` + `DatedAssociation` keyed by the adopted correlation key (D05 §3.2/§3.3); opaque `FinInstrmId`; flags never gate or de-key | `src/nse_engine/identity.py` | **A. EXISTS** (kept strictly separate from archive identity) |
| Per-archive "processed-under (content, engine, runner, contracts)" registry, durable **across runs** | Ingredients exist **per run package** (`INPUT_MANIFEST.jsonl` per-archive record + package-level `GOVERNED_INPUTS` bindings), but no cross-run registry/index exists; packages are run-scoped, new-root-only | `i4_runner.py`; `i4_output.py` (output root "new or empty") | **D. ABSENT** (as a durable index) → **C. EXTENSION REQUIRED** |
| Requalification / changed-content policy | Not established. Intent §6 (changed content "must not be silently treated as an ordinary duplicate"; exact disposition intentionally undecided) and §7 ("seen before" ≠ "permanently valid under every future contract"; policy left to a future authority decision) concur | intent artifact; D13 §5.3 (MD-12 context) | **E. DECISION REQUIRED** (deliberately deferred — not decided here) |

**§9 answer (task):** yes, the repository already distinguishes all seven concepts (archive identity,
archive content identity, engine version, canonical contract version, processing contract, evidence
contract, qualification state — the last via the R6 verdict document + D11/D14 records). Whether an
already-processed archive can be distinguished from one requiring processing **under a changed
contract/version**: within one package, implicitly (per-archive record + package-level version
bindings); across time, **not yet** (no durable cross-run registry) — and the requalification policy
itself remains an undecided authority question.

## 9. Incremental-processing findings

* **Per-archive mechanics — A. EXISTS / B. REUSABLE:** the pipeline processes archive-by-archive
  (per-archive preflight, per-member verbatim read, per-archive canonical build, per-record
  reconciliation) and partitioning is content-derived — `partition_of(record) =
  (format_family, calendar_year)` (MD-06, D08 §8) — so each archive's canonical output is
  deterministic and stable regardless of which archives are co-processed.
* **Corpus-oriented assumptions requiring the full corpus (why today's run is not incremental):**
  1. PF-10 requires the discovered set to equal the **entire** D01 inventory (both directions) — a
     run is defined as "the full governed corpus";
  2. W2 composition folds **all** member facts globally (identity correlation/dated associations
     span archives; calendar derivation and metric folds are corpus-scoped);
  3. one package, one `PACKAGE_MANIFEST.sha256`, one `RUN_RECORD.json`, one `RUN_COMPLETE.json`
     marker, one composite run identity bound to the **whole** corpus archive-set digest;
  4. the output root must be new or empty (never appended);
  5. reconciliation and replay compare the **whole package** (R6 is a total byte comparison).
* **What incremental processing would require (C. EXTENSION REQUIRED, E. DECISION REQUIRED):** an
  incremental run mode (discovered-new set instead of full-inventory equality), a durable per-archive
  processed registry keyed by content identity + version bindings (§8), a definition of run identity
  for partial runs, incremental manifest/publication semantics, and merge semantics for the serving
  dataset. Each is an authority question (intent Q4–Q7), not an implementation detail this record
  resolves.

## 10. Canonical-output findings

* **Canonical data model — A. EXISTS:** the D05 §13 ADOPTED set (field mapping, `SecurityRow`,
  `SecurityIdentity`/`DatedAssociation`, calendar from file-presence with sourced labels, overlay
  observables, non-gating validity flags, opaque FinInstrmId, CRLF/LF determinism, rupee scale +
  mandatory provenance note, registry-as-annotation), `spec_version D05/1.0` (D06 Decision A).
* **Output artifacts/contracts — A. EXISTS / B. REUSABLE:** deterministic versioned logical output
  package (MD-04): per-partition row JSONL + per-member evidence + per-partition manifest; `w2/`
  (`calendar.jsonl`, `associations.jsonl`, `identity_summary.json`, `metrics.json`,
  `unresolved.jsonl`); root documents (`PREFLIGHT.jsonl`, `RECONCILIATION.jsonl`,
  `INPUT_MANIFEST.jsonl`, `GOVERNED_INPUTS.json`, `RUN_RECORD.json`); `PACKAGE_MANIFEST.sha256`
  (per-file digests, declared hash bases); `RUN_COMPLETE.json` written last carrying the manifest's
  hash. MD-05 durability classes applied by exhaustive rule in `i4_output.py`.
* **Source-to-canonical mapping — A. EXISTS:** verbatim read (RD-5), name-keyed parsing with
  fail-closed tolerances, per-row-batch provenance block (D05 §8), per-archive `INPUT_MANIFEST`
  record, per-record `RECONCILIATION.jsonl` entries.
* **Immutability / versioning / rebuild — A. EXISTS:** outputs are content-derived and
  byte-deterministic (D05 §9; dual-hash; LF artifacts); runs write to fresh roots (no in-place
  mutation); replay (R6) proves rebuild equivalence; versions are declared per package
  (`spec_version`, `CONTRACT_VERSION`, tool fingerprints). The qualified M2 package **is** a
  durable canonical historical dataset of exactly this kind — the natural "Authoritative Durable
  Historical Dataset" of the target architecture (promotion/persistence of it = future decision, §11).

## 11. Persistence / durability findings

* **Logical contracts — A. EXISTS (decided, technology-neutral):** MD-05 durability classes
  (authoritative outputs / derived / provenance-evidence / transient); MD-06 content-derived
  partitioning; MD-07 persistence ownership (the engine owns the output contract; any future
  persistence **must preserve, not reinterpret**); MD-10 store-selection standard (7 demonstrable
  criteria: deterministic representation/retrieval; provenance preservation; integrity verification;
  replay/reproducibility; durability per MD-05; corpus-scale operation per MD-06; required downstream
  consumption per MD-03).
* **Physical persistence — D. ABSENT:** no persistence technology exists in the repository. MD-12 is
  **WITHHOLD / UNDECIDED** (D08 §16/§17; `STORAGE TECHNOLOGY = UNDECIDED`); `src/nse_engine/blocked.py`
  records "Parquet-vs-database authoritative-storage and durable output/persistence contracts are not
  decided". Durable locations today: Git (authoritative record) and the Windows run root
  (run-scoped packages; never inspected from Arena — environment boundary). No database, no store,
  no index.
* **What is missing (E. DECISION REQUIRED):** (i) the authoritative durable **serving** dataset —
  what the query layer reads (intent Q1); (ii) the persistence mechanism appropriate for a single-user
  personal application, graded against MD-10, with PostgreSQL explicitly **not** a requirement
  (intent §11; task §3). This investigation selects nothing.

## 12. Provenance / evidence findings (what future serving could expose)

All of the following already exists, is structured, and is hash-pinned (file-level exposure; a
query layer does not exist yet — §13):

| Serveable evidence | Artifact | Notes |
|---|---|---|
| Source archive per row batch | D05 §8 provenance block: `source_archive` = filename + D01 sha256, `member_name`, `format_family` | ADOPTED contract |
| Spec/tool/run identity per record | same block: `spec_version D05/1.0`, `tool_version` (name+version+sha256), `run_id`, `evidence_refs` | ADOPTED contract |
| Per-archive processing facts | `INPUT_MANIFEST.jsonl` (2,462 records: identities, digests, member sizes, header facts, `data_lines`, `rows`, `quarantined`, partition) | per-run |
| Run-level binding | `GOVERNED_INPUTS.json` / `RUN_RECORD.json` (contract version, engine/runner identity blocks, composite run identity, corpus block with `archive_set_digest`) | per-run |
| Reconciliation quality state | `RECONCILIATION.jsonl` (per-record + corpus scope; tiers; `by_result`/`by_tier` census; 0 gating divergences) | per-run |
| Unresolved-state evidence | `w2/unresolved.jsonl` (carried, never resolved) + calendar `label_status` counts in `w2/metrics.json` | per-run |
| Calendar + identities | `w2/calendar.jsonl`, `w2/associations.jsonl`, `w2/identity_summary.json`, `w2/metrics.json` | per-run |
| Preflight gate records | `PREFLIGHT.jsonl` | per-run |
| Integrity | `PACKAGE_MANIFEST.sha256` (per-file digests, declared hash bases) + `RUN_COMPLETE.json` | per-run |
| Determinism/replay qualification | R6 verdict (sha `d8e33f13…`), D11 evidence package (`8e78fcc8…`, E1–E10), monitor transcripts | durable on main |
| Qualification determination | D14 (I5 = 10-year full qualification, PASS) + D12 (I4 closure) | durable on main |

**Boundary noted (no invention):** source **row**-level offsets are **not** recorded — the D02
`row_offset`/`raw_row_hash` proposal was never adopted (D08 §4/§18, historical mismatch). Raw-record
exposure is therefore at the level of verbatim canonical field values + pinned member/archive hashes;
the raw archive/member bytes remain in Windows corpus custody (environment boundary) and are not
part of any Arena-visible dataset.

## 13. Serving / query findings

**D. ABSENT — recorded, per task instruction.** No query interface, read model, data-access
abstraction, serving module, API endpoint, local service interface, or report interface exists in the
authoritative tree. Positive evidence of absence: `tools/i4_runner/README.md` ("exposes no API/UI,
performs no network access"); `src/nse_engine/__init__.py` ("No persistence, no ingestion, no live
NSE access, no … query/API/UI/reporting surfaces"); the determinism guard tests forbid `socket`
imports in engine/runner code. (The untracked `_transfer_delivery/` staging contains a static file-
exposure page from an earlier transfer task; it is **never committed**, is a transfer convenience,
and is not a product serving layer.) Consequences (E. DECISION REQUIRED): the API/query contract
(intent Q8), the read/serve path design (intent §8), and the first release scope (intent Q13) all
remain open authority decisions.

## 14. UI / presentation findings

**D. ABSENT in the repository** — no UI files, no dashboard/explorer code, no frontend of any kind in
the 142-blob tree. The "supplied I4 application mockups" referenced by intent §9 exist **outside** the
repository (another environment/conversation); this record maps repository evidence against the
intent artifact's **in-repo summary** of those reference points (§9 of the artifact), and does not
claim to have inspected the mockups themselves.

Data-availability mapping (what the durable outputs/evidence **could** back; "data EXISTS" ≠ a
serving capability, which is ABSENT per §13):

**Dashboard reference points:** run identity/status → `RUN_RECORD.json`/`PREFLIGHT.jsonl`/
`RUN_COMPLETE.json` (EXISTS, evidence-level); archive count → D01 inventory 2,462 (EXISTS); canonical
rows → 5,689,949 via `w2/metrics.json`/reconciliation census (EXISTS); identity-record count →
`w2/identity_summary.json` (EXISTS); trading-calendar count → `w2/calendar.jsonl` +
`metrics.calendar_totals` (EXISTS); error count → reconciliation `by_result` + `quarantined` (0)
(EXISTS); rows by year → the `(format_family, year)` partition structure with per-partition manifests
and `INPUT_MANIFEST.partition` (EXISTS at partition granularity; a flat per-year rollup artifact =
minor **C. EXTENSION REQUIRED**, derivable without new processing); archives by exchange segment →
D01 per-archive `series_counts` + canonical series/market-type fields (EXISTS, derivable); data
coverage → inventory coverage 2016-09-20 → 2026-09-18 (EXISTS); archive inventory + details → D01
inventory + `INPUT_MANIFEST` (EXISTS); canonical data / identity-association / calendar-overlay /
reconciliation access → the corresponding `w2/` + root artifacts (EXISTS at file level; query access
= ABSENT serving layer); engine logs → `PREFLIGHT.jsonl` + monitor transcripts (E5 in the D11
package) (EXISTS, evidence-level).

**Data Explorer reference points:** dataset selection → family/partition (EXISTS conceptually);
date-range / instrument / segment / series-market-type / trading-status filters → the canonical row
carries these verbatim-published fields (EXISTS as data; filtering = ABSENT serving layer); query
results / saved queries / query history / charts / price views / yearly summaries / quality summaries
→ underlying data EXISTS (price fields as published; per-partition year structure; flag censuses) but
every presentation/query mechanism is ABSENT; canonical-record details / related records → row JSONL
+ `w2/associations.jsonl` (EXISTS as data); data-quality status / provenance / source archive /
reconciliation access → §12 evidence set (EXISTS); **source row → not recorded** (row offsets never
adopted — §12 boundary); **raw record access → verbatim field values + pinned hashes; raw bytes stay
in Windows custody** (environment boundary); archive access → inventory + hash facts (metadata
EXISTS; bytes out of Arena reach).

## 15. Gap matrix (every finding classified; A=EXISTS B=REUSABLE C=EXTENSION REQUIRED D=ABSENT E=DECISION REQUIRED F=OUT OF SCOPE)

| # | Area | Finding | Class |
|---|---|---|---|
| 1 | Archive inventory + discovery + preflight contracts | D01 inventory, `discover_archives`, PF-10/11/12 | A + B |
| 2 | Incremental discovery mode (new-arrival diffing) | full-corpus equivalence assertion only today | C + E (intent Q4) |
| 3 | Archive identity / content fingerprint / dedup contracts | per-archive sha256 (D01 + observed), member digests, duplicate rules | A |
| 4 | Cross-run per-archive processed registry (content + version bindings) | ingredients per-run (`INPUT_MANIFEST` + `GOVERNED_INPUTS`); no durable cross-run index | D → C |
| 5 | Requalification / version-compatibility policy | intentionally undecided (intent §7; D13 §5.3) | E |
| 6 | Changed-content disposition (conflict/reprocess/replace/quarantine) | intentionally undecided (intent §6) | E |
| 7 | Per-archive canonical processing mechanics | exists, deterministic, content-partitioned | A + B |
| 8 | Corpus-scale composition (global W2 fold, single package/manifest/marker, new-root-only, whole-package replay) | the full-corpus assumptions that block naive incremental reuse | C + E |
| 9 | Canonical model + deterministic versioned package | D05 ADOPTED; MD-04/05/06 package; R6-proven rebuild | A + B |
| 10 | Per-year flat rollup artifact | derivable from partition structure; not yet a first-class artifact | C (minor) |
| 11 | Physical persistence / serving store | MD-12 UNDECIDED; none in repo | D + E (intent Q1/Q2) |
| 12 | Serving / query / API / report layer | absent (verified) | D + E (intent Q8/Q13) |
| 13 | UI / presentation | absent from repo; data backing largely EXISTS at file level | D + E (intent Q13) |
| 14 | Row-offset-level raw-record provenance | not adopted (D02 proposal, historical mismatch) — boundary, not a gap to fill silently | E (only if a future decision wants it) |
| 15 | Serving of raw archive/member bytes to the UI | corpus in Windows custody; Arena has no filesystem reach | F (environment boundary; would require an explicit cross-environment decision) |
| 16 | Auth / RBAC / multi-user / PostgreSQL / enterprise architecture | product non-goals (intent §2/§11/§15) | F |
| 17 | Any re-run/re-measure of I4/M2/replay/I5 | qualified baseline is closed (I5 boundary, §3) | F |

## 16. Unresolved decisions (open, each requiring a future authority decision)

1. Authoritative durable **serving** dataset (what the query layer reads; promotion of the qualified
   M2 package vs a derived serving copy) — intent Q1.
2. Persistence mechanism for a single-user personal application, graded against MD-10; PostgreSQL
   not a requirement — intent Q2; D13 §5.3.
3. Canonical archive identity/fingerprint contract for incremental recognition (the D01 sha256 +
   `INPUT_MANIFEST` fields are the in-repo candidates to adopt or amend) — intent Q3.
4. Archive discovery mechanism for new arrivals — intent Q4.
5. Changed-content disposition — intent Q5/Q6.
6. Requalification / version-compatibility policy — intent Q6 (task §9; deliberately not decided here).
7. What constitutes successful incremental publication — intent Q7.
8. API/query contract (endpoints/schema) — intent Q8.
9. Which UI operations are read-only vs processing operations — intent Q9.
10. How provenance/evidence is exposed — intent Q10.
11. Incremental failure / partial-publication handling — intent Q11.
12. Backup/recovery expectations for the personal dataset — intent Q12.
13. Exact first-release UI subset (of the demonstrated Dashboard/Data Explorer) — intent Q13.

## 17. Explicit non-decisions

This record decides **nothing** and authorizes **nothing**: no persistence technology (MD-12 remains
UNDECIDED); no API framework, hosting, deployment, ingestion scheduler, or archive-watcher mechanism;
no changed-content or requalification policy; no query schema or endpoint set; no UI technology; no
serving/incremental/UI implementation; no I5 reopen or rerun; no M/N or other gate invention (intent
§15.10). The intent artifact remains TARGET/INTENT ONLY; a future governance decision must
explicitly adopt, modify, or supersede it (intent §17) before substantive post-I5 implementation.

## 18. Recommended future authority scope (recommendation only — not an authorization)

When the authority acts, the minimum scope that the repository + intent support is **one**
post-I5 "serving & incremental ingestion" gate (the D08 §16 "future M/N gate" deferral is the
existing pointer; adopting or renaming it is the authority's choice) structured in the D13 pattern:
a decision-input/authorization record answering the 13 questions of §16 **from existing engine
contracts/evidence where possible rather than reinvented** (intent §14), with the single-user
simplicity principle (intent §12) as the grading constraint and the MD-10 standard as the
persistence grading standard. Natural first candidates grounded in this investigation: adopt the D01
sha256 + `INPUT_MANIFEST` fields as the archive identity/fingerprint contract (item 3); treat the
qualified M2 package as the initial durable serving dataset (item 1); scope the first release to the
demonstrated Dashboard/Data Explorer subset whose data backing is verified in §14 (item 13). All
remain **recommendations for the decision**, not decisions.

## 19. Exclusions

No implementation of any kind (serving, incremental, UI, persistence, API); no technology
selection; no new gate or authorization; no corpus access, run, replay, or measurement; no Windows
inspection or claim; no modification of engine/runner/`i4_output.py`, corpus files, or qualified
evidence; no use of the untracked `_transfer_delivery/` staging as evidence.

## 20. Evidence references (exact paths, `origin/main@e81baef…`)

`docs/product/HISTORICAL_ENGINE_PRODUCT_AND_SERVING_ARCHITECTURE_INTENT.md` (blob `41ad2740…`,
SHA-256 `7e4a14f4…`); `docs/investigations/D14_I5_AUTHORITY_DECISION_10YEAR_FULL_QUALIFICATION.md`;
`docs/investigations/D12_I4_CLOSURE_DECISION.md` (§3 run facts, §6 C.7); `docs/investigations/D13_
POST_I4_DECISION_INPUT_INVESTIGATION.md` (§4 decided facts, §5.3 MD-12); `docs/investigations/D11_
REPLAY_QUALIFICATION_CORRECTION.md` (§1/§11); `docs/investigations/D08_I3_OUTPUT_PERSISTENCE_
CONTRACT_DECISION.md` (§§4–18: MD-02…MD-17); `docs/specs/D05_CANONICAL_MODEL_SPEC.md` (§§3/5/8/9/13);
`evidence/inventory/file_inventory.json` + `INVENTORY_REPORT.md`; `evidence/D11_REPLAY_
QUALIFICATION_20261009/`; `tools/i4_runner/` (`i4_preflight.py` PF-10/11/12, `i4_inputs.py`,
`i4_identity.py`, `i4_output.py`, `i4_runner.py`, `README.md`); `src/nse_engine/` (`identity.py`,
`provenance.py`, `contract.py`, `blocked.py`, `pipeline.py`, `w2_stream.py`, `__init__.py`);
`tests/test_determinism.py` + `tests/test_w2_determinism.py` (socket/forbidden-import guards).

## 21. Conclusion

The qualified 10-year baseline is a complete, hash-pinned, deterministic, content-partitioned
canonical dataset with a rich per-archive identity/fingerprint/provenance/evidence contract — the
write/ingest half of the target architecture exists and is reusable at the per-archive level. The
read/serve half (serving/query layer, durable serving store, UI) is **ABSENT**, and the incremental
half exists only as per-archive mechanics inside full-corpus composition; making it incremental
requires a durable per-archive processed registry and two deliberately-undecided policies
(requalification/version compatibility, changed-content disposition). Nothing in this record
authorizes any of it.

> ### **INVESTIGATION COMPLETE — ARCHITECTURE DECISION REQUIRED.**
> No serving, incremental-ingestion, UI, or persistence implementation is authorized by this
> investigation. The 13 unresolved decisions of §16 (and the recommended single-gate scope of §18)
> require a future explicit authority decision, which must first adopt, modify, or supersede the
> intent artifact (intent §17).
