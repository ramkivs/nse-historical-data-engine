# Post-I5 Serving / Incremental / Product Architecture — Authority Decision (D16)

**Recorded:** 2026-10-09 (Arena side, recording an explicit authority decision).
**Decision authority:** Ramki (application decision authority), via the explicit D16 directive that
commissioned this task ("establish the explicit architecture decisions required before any
Serving/API, incremental-ingestion, persistence, or UI implementation may begin").
**Governing decision inputs (both durable on `origin/main@d60eb3d4…`, verified byte-identical):**
1. `docs/product/HISTORICAL_ENGINE_PRODUCT_AND_SERVING_ARCHITECTURE_INTENT.md`
   (blob `41ad2740…`, SHA-256 `7e4a14f4…`, 595 lines — TARGET/INTENT ONLY)
2. `docs/investigations/POST_I5_SERVING_INCREMENTAL_PRODUCT_ARCHITECTURE_INVESTIGATION.md`
   (blob `79157b82…` — the D15 investigation; disposition: INVESTIGATION COMPLETE — ARCHITECTURE
   DECISION REQUIRED)

**This record makes architecture decisions only. It authorizes no implementation of any kind.**

---

## 1. Purpose

Establish, with explicit authority, the architecture decisions the D15 investigation identified as
required before any serving/API, incremental-ingestion, persistence, or UI implementation may begin:
13 decisions (D16-01…D16-13), each receiving exactly one disposition, plus the approved
responsibility-boundary model, the approved incremental model, the changed-content/requalification
disposition, the serving dataset boundary, the first-release query/product scope, and the
implementation-authority disposition.

## 2. Authority and scope

* Authority: the explicit D16 directive (header). Precedent pattern: D06 (adoption decisions), D08
  (MD dispositions with explicit authority boundaries), D14 (I5 determination).
* Scope: architecture of post-I5 serving, incremental ingestion, persistence boundary, and UI for a
  **single-user, personal-use application** (intent §2/§12 — mandatory unless a future explicit scope
  decision supersedes it).
* This record: does not implement anything; does not select implementation libraries/frameworks; does
  not introduce authentication, RBAC, multi-user support, PostgreSQL, or any enterprise architecture;
  does not rerun I4/I5; does not modify the qualified historical dataset or existing engine behavior;
  changes exactly one repository path (this file). No source/test/tool file is touched.

## 3. Evidence baseline (read-only, verified)

| Check | Observed | Verdict |
|---|---|---|
| Repository / origin | `ramkivs/nse-historical-data-engine` / `https://github.com/ramkivs/nse-historical-data-engine.git` | PASS |
| Authoritative ref | `origin/main` = `d60eb3d4f51f58347200066d4d41bcd6d78848e0` (D15 publication; parent `e81baef0…`); tree `1703e577…`, 144 blobs | PASS |
| Intent artifact | worktree == authoritative blob `41ad2740…`; SHA-256 `7e4a14f4…`; complete 595-line content verified at D15 intake | PASS |
| D15 investigation | worktree == authoritative blob `79157b82…`; disposition + 17-row gap matrix present | PASS |
| I5 state | I5 = 10-year full qualification — PASS, CLOSED / DURABLE / REMOTELY VERIFIED (D14) | PASS |
| Working tree | clean; only untracked `_transfer_delivery/` (staging, never committed) preserved | PASS |
| Mutation set | exactly 1 path: this file (new; `docs/architecture/` is a new directory) | bounded |

D15's evidence (which cites D08 §§4–18, D05, D11/D12/D14, the D01 inventory, the `tools/i4_runner/`
contracts, and `src/nse_engine/` identity/provenance machinery) was consulted as recorded; no
completed qualification work was repeated.

## 4. Product-intent disposition

The intent artifact is hereby **explicitly ADOPTED as the governing target intent**, unmodified
(satisfying intent §17: "A future governance decision should explicitly adopt, modify, or supersede
this intent before substantive post-I5 implementation begins"). Adoption carries its self-declared
limits unchanged: it remains TARGET/INTENT ONLY — not implementation, persistence, API, UI, or
production authority. Its non-drift rules (§15) bind all future work unless an explicit future
decision changes them (rule 14).

## 5. D15 findings adopted

Adopted as the factual basis for the decisions below: D15 §7 (discovery/identity contracts EXIST and
are reusable), §8 (all seven identity/version concepts distinguished; cross-run registry ABSENT;
requalification + changed-content deliberately undecided), §9 (per-archive mechanics reusable;
corpus-scale composition enumerated), §10 (canonical model + deterministic package EXISTS), §11
(logical persistence contracts decided/technology-neutral; physical persistence ABSENT, MD-12
UNDECIDED), §12 (provenance/evidence inventory; row-offset limitation; raw bytes in Windows custody),
§13 (serving/query ABSENT), §14 (UI ABSENT; data-availability mapping for the demonstrated
Dashboard/Data Explorer), §15 gap matrix (17 classified rows), §16 (13 unresolved decisions), §18
(recommended single-gate scope).

## 6. Decision methodology

Each of the 13 decisions (D16-01…D16-13) received exactly one disposition from: **ADOPT / MODIFY /
DEFER / REJECT (OUT OF SCOPE) / EVIDENCE REQUIRED**, recorded with: (1) Decision ID, (2) Question,
(3) Evidence, (4) Existing intent, (5) Decision, (6) Rationale, (7) Consequences, (8)
Implementation boundary, (9) Whether additional authority is required. A decision was made only
where the repository evidence (D15 + cited contracts) supports it; where the evidence is genuinely
insufficient, the disposition is EVIDENCE REQUIRED or DEFER with the gap named — **no gap was
filled with a general engineering assumption, and no conventional/technically-convenient default was
promoted**.

---

## 7. Decisions D16-01 … D16-13

### D16-01 — Incremental archive discovery

1. **ID:** D16-01. 2. **Question:** Are future archive arrivals detected, and under what contract?
3. **Evidence:** D01 governed per-archive inventory (`root`, `relative_path`, `file_name`,
   `size_bytes`, `date_from_filename`, `sha256`, `detected_format`, `row_count`, `headers`,
   `header_signature`, `series_counts`); `i4_inputs.py` `discover_archives` / `csv_member_names` /
   `read_member_bytes` (CRC-checked, verbatim, single governed member); `i4_preflight.py`
   PF-10/11/12 (both-directions set equality, no duplicate checksums/dates, per-archive byte-hash
   against D01 values; all fail-closed gating) (D15 §7).
4. **Existing intent:** §4/§6 discovery stage; non-drift #4 (identity/content fingerprinting for
   duplicate recognition).
5. **Decision:** **ADOPT** — incremental discovery is a **read-only re-scan of the declared corpus
   roots** (the same LEGACY + UDiFF roots as the D01 baseline) producing per-archive records in the
   **D01 inventory record shape**, which are then classified per D16-03 against (a) the D01 baseline
   inventory and (b) the processed-archive registry (D16-02). The discovery contract inherits the
   PF-10/11/12 fail-closed discipline: an archive that fails CRC, contains more than one governed
   member, or whose bytes cannot be hashed is a **finding** — never a silent skip. Discovery never
   writes to or mutates the corpus. The scan *mechanism/scheduler* (watcher vs manual trigger) is an
   implementation detail of a future implementation decision — the *contract* is decided here.
6. **Rationale:** Reuses the only existing, proven discovery/identity mechanism (D15: EXISTS/REUSABLE)
   instead of inventing one; fail-closed is a house invariant (D05/D07).
7. **Consequences:** A discovery pass yields a classified archive set; D16-03/05 consume it.
8. **Implementation boundary:** Decision only — no discovery code, watcher, or scheduler.
9. **Additional authority required:** No for the contract; implementation = future (D16-13).

### D16-02 — Durable cross-run processed-archive registry

1. **ID:** D16-02. 2. **Question:** Is a durable registry required to establish whether an archive
   has already been processed, and under which relevant contract/version?
3. **Evidence:** D15 §8 — per-run ingredients exist (`INPUT_MANIFEST.jsonl` per-archive records:
   identities, digests, partition, rows, quarantined; `GOVERNED_INPUTS.json` bindings:
   `contract_version I4-runner/1.0`, engine `d3269b73…`/runner `f3ebf624…` fingerprints,
   `spec_version D05/1.0`, corpus digest `54d81507…`) but no cross-run registry exists; packages are
   run-scoped, new-root-only; D15 gap #4 (ABSENT → EXTENSION REQUIRED).
4. **Existing intent:** §6 ("The system should recognize an archive that has already been
   successfully processed"); §7 (version awareness: "seen before" ≠ "permanently valid").
5. **Decision:** **ADOPT** — a **durable processed-archive registry is required** as an
   architectural component, defined by its **content contract** (storage technology deliberately not
   selected — see §14). Each entry records: archive identity (root, relative_path, file_name,
   date_from_filename); content identity (archive byte sha256); processing result (partition, rows,
   quarantined); **version bindings** (engine fingerprint, runner fingerprint, canonical contract
   `spec_version`, processing contract version); run provenance (run_id, package manifest digest);
   and status (processed / pending / flagged). The registry is the **single authoritative statement**
   of "processed under X". It is updated **only** by a successful validated incremental publication
   (D16-05) — never out-of-band.
6. **Rationale:** Without it, intent non-drift rules #2/#3 (no unnecessary reprocessing; process
   genuinely new archives incrementally) are unimplementable; D15 gap #4 requires exactly this.
7. **Consequences:** The registry becomes durable product state under the persistence boundary
   (D16-07 class 3); any ingestion implementation must read and update it.
8. **Implementation boundary:** Contract only — no storage technology, no format, no code.
9. **Additional authority required:** No (architecture); a physical-store selection, if ever made,
   is an MD-12 decision (UNDECIDED, §14).

### D16-03 — New / unchanged / changed archive classification

1. **ID:** D16-03. 2. **Question:** Authoritative classification semantics for a discovered archive.
3. **Evidence:** Two distinct identity axes both exist and are hash-pinned (D15 §8): apparent
   identity (file_name + governed date_from_filename) and content identity (archive byte sha256;
   member raw/LF digests). Baseline uniqueness is proven (0 duplicate checksums, 0 duplicate dates);
   PF-11 treats duplicate checksums as a gating anomaly.
4. **Existing intent:** §6 (duplicates recognized "using the applicable identity/content contract";
   "If an archive with the same apparent identity has different content, it must **not** be silently
   treated as an ordinary duplicate"); non-drift #5.
5. **Decision:** **ADOPT** the following semantics (content identity governs; the filename/date never
   alone establishes "already processed"):
   * **UNCHANGED** — apparent identity matches a registry entry **and** content sha256 matches the
     entry's recorded content sha256 **and** the entry's version bindings remain applicable under
     D16-04 → SKIP processing.
   * **NEW** — content sha256 matches no registry entry (whether or not the apparent identity is
     new) → incremental processing.
   * **CHANGED** — apparent identity matches a registry entry but content sha256 differs → **never**
     classified unchanged; **never** silently reprocessed over the prior result; the prior result
     stays intact; the archive is held as a **flagged finding** pending the changed-content
     disposition (D16-03a below).
   * **Anomalous** — structural failure (CRC, multi-member, unhashable) or second occurrence of
     identical content under a different path → finding (fail-closed), not a skippable class.
   * **D16-03a (sub-decision) — CHANGED CONTENT DISPOSITION: EVIDENCE REQUIRED.** The exact
     disposition (explicit conflict flag / quarantine / versioned replacement / reprocessing) is
     decided by a future authority decision when and only when a changed archive actually presents;
     no repository evidence exists to choose among outcomes now, and the intent (§6) deliberately
     leaves it open. Until D16-03a, CHANGED archives are quarantined from automatic processing by
     default (the fail-closed reading of the intent).
6. **Rationale:** This is precisely what the intent mandates and what the existing contracts support
   (both identity axes already exist and are hash-pinned); it resolves the *classification* while
   refusing to invent the *resolution* of changed content.
7. **Consequences:** D16-05 consumes NEW (process) / UNCHANGED (skip) / CHANGED (held, flagged) /
   Anomalous (finding); the CHANGED hold is the default until D16-03a.
8. **Implementation boundary:** Semantics only — no classifier code.
9. **Additional authority required:** **Yes** — D16-03a (changed-content disposition) is a future
   authority decision (intent Q5).

### D16-04 — Requalification policy

1. **ID:** D16-04. 2. **Question:** When do previously processed archives/data require
   requalification?
3. **Evidence:** All version bindings exist and are per-archive resolvable from D16-02 entries
   (engine/runner fingerprints; `spec_version D05/1.0`; processing contract `I4-runner/1.0`); R6
   proved byte-exact rebuild equivalence **for identical pinned bytes + versions**; no contract/tool
   version change has occurred since the M2 baseline.
4. **Existing intent:** §7 ("must not silently assume that 'seen before' always means 'permanently
   valid under every future contract'; The exact requalification/versioning policy is intentionally
   left for a future authority decision").
5. **Decision:** **ADOPT the applicability condition; DEFER the migration mechanism.**
   * **Binding principle (decided):** "processed" is always a statement about
     **(content identity × version bindings)**. An entry is *applicable* only while the current
     engine fingerprint, runner fingerprint, canonical `spec_version`, and processing contract
     version **equal** the entry's bindings. Any mismatch marks the entry **stale** — its results
     may not serve under the new contract until the archive is reprocessed (and re-validated) under
     the new bindings. Staleness is a **deterministic census derived from the registry**, not an
     execution: deciding staleness costs no processing.
   * **Deferred:** the migration *mechanism* (batch requalification run vs per-archive lazy
     requalification vs versioned dataset coexistence) — **DEFER** until the first actual
     contract/tool version change occurs, when there will be evidence (stale census, scope, cost) to
     decide against. Until then the sole applicable version set is the M2 baseline's
     (`d3269b73…` / `f3ebf624…` / `D05/1.0` / `I4-runner/1.0`).
   * **No requalification is performed, ordered, or implied by this record** (task boundary; I5
     boundary).
6. **Rationale:** The *condition* for requalification follows directly from contracts the repository
   already fixed (version bindings exist exactly for this purpose); the *mechanism* has no evidence
   to be decided against yet (no version change has happened) — deciding it now would be invention.
7. **Consequences:** The registry carries bindings; a future version change yields a stale census;
   the I5-qualified baseline remains the reference version set.
8. **Implementation boundary:** Policy statement only — no runs, no census tooling.
9. **Additional authority required:** **Yes** — the migration mechanism, when the first version
   change occurs (intent Q6).

### D16-05 — Incremental corpus composition

1. **ID:** D16-05. 2. **Question:** How do newly processed archive results join the canonical
   historical dataset without regenerating unaffected archives?
3. **Evidence:** Per-archive output is deterministic and content-partitioned:
   `partition_of = (format_family, calendar_year)` (MD-06, content-derived), per-partition manifests,
   per-member evidence (D15 §9/§10). Corpus-scoped derived state exists: W2 identity correlation /
   dated associations, calendar derivation, metric folds — computed over **all** member facts
   (D15 §9: the enumerated corpus-scale composition).
4. **Existing intent:** §6 flow (incremental process → validation/evidence → durable publication →
   "Dataset/index update" → UI sees available data).
5. **Decision:** **ADOPT** the following composition semantics:
   * **Per-archive contributions are committed to their own partition** — an archive's canonical
     rows + member evidence are a pure function of that archive's bytes + contract versions
     (determinism, D05 §9), so unaffected archives are **never re-read or re-parsed**.
   * **Corpus-scoped derived state (identity/associations, calendar, metrics) is re-derived, not
     re-processed:** after any approved incremental publication, derived state is recomputed as a
     pure function of **all processed archives' canonical rows + contract versions**. This is the
     minimum necessary work and is explicitly *not* "regeneration of unaffected archives" (their raw
     bytes are untouched; their canonical rows are consumed).
   * **Invariants:** (i) derived state is always deterministically reproducible from
     (processed canonical rows × contract versions) — byte-identical re-derivation (D05 §9
     discipline); (ii) derived state is always verifiable (same reconciliation discipline as the
     baseline, scaled to the run); (iii) the registry (D16-02) is updated in the same publication.
   * **Boundary with the qualified baseline:** an incremental publication is **never** a
     re-qualification of the I5 baseline. The M2 package + D11/D14 records remain the sole
     qualification of the 10-year baseline; incremental publications carry their own run identity,
     package manifest, and evidence under the same MD-11-style discipline (D14 boundary preserved;
     I5 not reopened).
6. **Rationale:** Follows directly from the repository's actual computation structure (per-archive
   deterministic contributions vs global folds, D15 §9) — no merge algorithm is invented; the record
   states only the invariants an implementation must satisfy.
7. **Consequences:** "Incremental" is now precisely defined: classify → process NEW only →
   re-derive derived state → validate → publish (partition contributions + derived state +
   manifests + run identity) → update registry.
8. **Implementation boundary:** Semantics/invariants only — no code, no rollups.
9. **Additional authority required:** No (architecture); implementation = future (D16-13).

### D16-06 — Partition / per-year update semantics

1. **ID:** D16-06. 2. **Question:** Can the existing partition model be extended incrementally, and
   which invariants must remain true?
3. **Evidence:** `partition_of(record) = (format_family, calendar_year of date_from_filename)` —
   content-derived per MD-06 ("content-derived (deterministic from governed inputs), never size- or
   time-of-execution-derived"); 12 baseline partitions; per-partition manifests; D15 gap #10
   (per-year rollup derivable, minor EXTENSION).
4. **Existing intent:** not specific (partitioning is engine-internal in the intent's flow).
5. **Decision:** **ADOPT** — the partition model extends incrementally **unchanged**. Partitions are
   stable content buckets; a new archive joins its key's partition (an existing partition for known
   families/years; a **new** partition only if a new (family, year) key arises — e.g., a 2027 file —
   and a **new format family** requires an explicit review before acceptance, since parser support
   would be a contract change). Invariants that must remain true: (1) keys stay content-derived
   (MD-06) — never execution-time- or size-derived; (2) an archive contributes to exactly one
   partition; (3) partition manifests stay complete and verifiable with declared hash bases;
   (4) partition membership is deterministic across runs under the same contracts; (5) the 12
   qualified baseline partitions remain **byte-identical, immutable qualified artifacts** —
   incremental publications add/update partition state only through approved publications, never by
   in-place mutation of the M2 package. A per-year rollup (D15 gap #10) is a **derived view over the
   partition structure** (serving state, D16-07 class 4), not a new partitioning.
6. **Rationale:** The content-derived key design already guarantees incremental stability; the
   decision merely fixes the invariants rather than re-opening the partition contract.
7. **Consequences:** First-release per-year views and any incremental partition growth have a fixed
   semantic basis.
8. **Implementation boundary:** Invariants only — no rollup implementation.
9. **Additional authority required:** No.

### D16-07 — Durable persistence boundary

1. **ID:** D16-07. 2. **Question:** Architectural ownership boundary for durable state.
3. **Evidence:** MD-05 durability classes; MD-07 ("The engine owns the contract for the outputs it
   produces. A future persistence implementation **must preserve** the governed output, provenance,
   evidence, determinism and durability contracts — it may not reinterpret, re-derive, mutate or
   extend them"); MD-10 standard; MD-12 WITHHOLD/UNDECIDED; `blocked.py` ("Parquet-vs-database
   authoritative-storage … not decided"); D15 §11.
4. **Existing intent:** §8 (serving is a consumer of the durable dataset), §10 (write/read path
   separation, preserved even single-user).
5. **Decision:** **ADOPT** — durable state is exactly **four named classes with fixed owners**:
   * **(1) Qualified baseline package** — the M2 run package + D11 evidence + D12/D14 records.
     Owner: the qualification record (I4/I5). **Immutable**; no component may mutate, re-derive, or
     re-qualify it.
   * **(2) Incremental publications** — each approved incremental run's package (partition
     contributions, re-derived state, manifests, run identity, evidence). Owner: the historical
     processing engine, under MD-11-style discipline.
   * **(3) Processed-archive registry** (D16-02). Owner: the ingestion boundary. The single
     authoritative "processed under" statement.
   * **(4) Serving/derived state** — indexes, rollups, query accelerants, saved-query stores. Owner:
     the serving boundary. **Always a pure derivation of (1)+(2)+registry; rebuildable at any time
     from them with no loss — deleting (4) is never a data event.**
   * **Conflict rule:** if (4) ever disagrees with (1)/(2)/(3), (1)/(2)/(3) win and (4) is rebuilt.
   * **Technology: NONE selected — TECHNOLOGY = UNDECIDED** (MD-12 stands). If physical persistence is
     ever chosen, it is graded against MD-10's 7 criteria under the single-user simplicity constraint
     (intent §12). The qualified M2 package (1) and any future serving persistence (4) remain
     **distinct** — serving persistence never absorbs, shadows, or reinterprets the qualified
     baseline (task-required distinction, preserved).
6. **Rationale:** Preserves the decided logical contracts (MD-05/07/10) verbatim, makes "what is
   authoritative" unambiguous across all four state classes, and selects no technology.
7. **Consequences:** Every implementation must respect (1)'s immutability, (3)'s single-writer rule,
   and (4)'s rebuildability.
8. **Implementation boundary:** Boundary/ownership only — no store, no format, no code.
9. **Additional authority required:** No (boundary); any physical store selection is a future MD-12
   decision.

### D16-08 — Serving dataset (what the serving/API layer may expose)

1. **ID:** D16-08. 2. **Question:** What authoritative data may the future serving/API layer expose?
3. **Evidence:** D15 §12 (the full provenance/evidence inventory, all structured and hash-pinned);
   D05 consumer obligations that remain binding meanwhile (D08 §16 MD-09: units/provenance note
   mandatory, non-gating flags, no `FinInstrmId` identity, no overlay aggregation, unknown states
   displayed, no retroactive annotations); environment boundary (raw archive/member bytes in
   Windows custody; Arena has no filesystem reach — D15 §12/§15#15); row offsets never adopted
   (D08 §4/§18).
4. **Existing intent:** §5 (serving exposes the durable canonical dataset, provenance, quality);
   §14 Q10.
5. **Decision:** **ADOPT** the five-class exposure boundary:
   * **Canonical historical data — MAY be exposed:** partition canonical rows (verbatim-published
     fields + non-gating flags), identity/association data, calendar (with `label_status`; the three
     unexplained dates displayed as unexplained — never filled in), metrics — subject to the D05
     consumer obligations.
   * **Provenance/evidence — MAY be exposed:** per-record provenance blocks (D05 §8),
     `INPUT_MANIFEST` per-archive records, reconciliation records, unresolved-state records,
     preflight records, run identity/fingerprints, package manifests/hashes, qualification records
     (D11/D12/D14), registry entries.
   * **Processing metadata — MAY be exposed:** partition definitions, registry status + version
     bindings, per-archive processing facts, incremental run records.
   * **Operational metadata — MAY be exposed (minimal single-user form):** run status, what was
     processed when under which run, error/finding records. No multi-user operational concepts
     (non-goal).
   * **Raw archive content — NOT exposed by default:** raw bytes remain in Windows corpus custody
     (environment boundary). Serving exposes verbatim field values (already canonical), pinned
     hashes, and archive metadata. Exposing raw bytes/row text would require a future explicit
     decision **plus** a cross-environment mechanism — currently OUT OF SCOPE (D15 #15).
   * **Source-row granularity:** "source row" exposure is at member/archive granularity + verbatim
     field values (row offsets were never adopted) — a limitation of record, not a gap to fill
     silently.
6. **Rationale:** Mirrors the repository's actual artifact structure (D15 §12); the D05 obligations
   are already-decided binding constraints; the raw-content exclusion follows from the environment
   boundary, not a technical preference.
7. **Consequences:** The serving design space is bounded before any API design begins.
8. **Implementation boundary:** Exposure classes only — no API schema, endpoints, or technology.
9. **Additional authority required:** Only if raw-content serving is ever desired (future decision).

### D16-09 — Serving/query boundary (responsibility boundary)

1. **ID:** D16-09. 2. **Question:** Responsibility boundary across historical engine → durable data
   → serving/query layer → UI.
3. **Evidence:** intent §4/§5/§8/§10; D15 §13 (serving ABSENT — the boundary is unconstrained
   today); MD-07; D14 non-authorizations.
4. **Existing intent:** §8 ("The API/query layer should be a **consumer** of the durable dataset,
   not the owner of historical computation. Queries should not cause a full historical
   reprocessing run."); §5 critical boundary (UI ≠ processing engine; "Process New Archives" is a
   UI-exposed operation whose execution belongs to the ingestion side).
5. **Decision:** **ADOPT**:
   * **Historical processing engine (write path):** owns discovery, classification, processing,
     validation, evidence generation, derived-state re-derivation, registry updates, publication.
   * **Durable data:** the boundary of record — classes (1)–(4) of D16-07.
   * **Serving/query layer:** read-only consumer of (1)+(2)+(3); owns query execution, result
     shaping, and derived serving state (4). It **never invokes or schedules** historical
     processing; it **never treats (4) as a source of truth**.
   * **User-initiated processing operations** (e.g., "Process New Archives", serving-state rebuild)
     are explicit delegated invocations of their owning boundary — a UI may surface them, but
     execution, validation, and publication are the owning boundary's responsibility; they are
     never query side effects.
   * **UI:** consumer of serving only (D16-11).
   * **Invariants:** a query never mutates durable data; a processing run never reads (4) as an
     input; a query failure can never corrupt (1)–(3); a processing failure leaves (4) at its last
     approved publication state.
6. **Rationale:** Exactly the intent's stated separation, now fixed as an authority decision with
   invariants that make the boundaries testable.
7. **Consequences:** Failure domains are disjoint; the three-layer implementation (processing /
   serving / UI) + durable record is the only permitted shape.
8. **Implementation boundary:** Boundary + invariants only — no endpoints, no code.
9. **Additional authority required:** No.

### D16-10 — Query contract (first-release semantic categories)

1. **ID:** D16-10. 2. **Question:** The semantic categories of queries the first release must
   support (semantics only — no endpoints, frameworks, or schema).
3. **Evidence:** D15 §14 data-availability mapping (verified data backing for each demonstrated
   reference point); D05 field vocabulary (as-published symbol/series/market-type/segment fields,
   prices as published, non-gating flags, calendar `label_status`, `SecurityIdentity`/
   `DatedAssociation`); D08 §16 MD-09 binding obligations.
4. **Existing intent:** §9 Data Explorer direction (dataset selection; date range; instrument;
   segment; series/market type; trading status; exchange segment; filters; quick filters; results;
   saved queries; query history; record details; source evidence; related records; quality status;
   provenance; source archive; reconciliation; charts; yearly summaries; quality summaries).
5. **Decision:** **ADOPT** the first-release semantic query categories (each mapped to verified
   existing data; no new computation invented):
   * **Q1** dataset/partition selection (family × year) and yearly summaries (D16-06 derived view).
   * **Q2** date-range query over canonical rows.
   * **Q3** instrument query (symbol/series correlation key; ISIN treated as a non-identity
     attribute per D05 §§6–7).
   * **Q4** segment / market-type / series / trading-status filtering (as-published field values).
   * **Q5** identity/association query ("related records" = the instrument's dated-association
     intervals; no overlay aggregation — D05).
   * **Q6** calendar query (trading days from file-presence; sourced holiday labels; the three
     unexplained dates shown as `unexplained-by-obtained-circulars`; legacy era `not-retrieved`).
   * **Q7** record detail with full provenance (D05 §8 block + `INPUT_MANIFEST` archive facts + the
     archive's reconciliation records).
   * **Q8** data-quality views (flag censuses, unresolved-state records, quarantined counts,
     reconciliation by-result/by-tier).
   * **Q9** archive inventory query (D01 facts + registry status/version bindings per archive).
   * **Q10** qualification/evidence views (run identity, fingerprints, manifests, R6/D11/D12/D14
     records).
   * **Saved queries and query history** are first-release product features, persisted as serving
     state (4) (single-user; mechanism = implementation detail).
   * **Explicitly not in the first release:** eligibility/master queries (DEC-1 DEFERRED);
     computed analytics beyond as-published values + derived state (no re-derivation of
     non-adopted semantics); raw-byte serving (D16-08).
6. **Rationale:** Every category is data-backed by verified existing artifacts (D15 §14) — the
   contract is bounded by what exists, and the D05/D08 obligations constrain its semantics.
7. **Consequences:** The future API/query design has a fixed semantic scope; endpoint names,
   frameworks, and schemas remain undecided (TECHNOLOGY = UNDECIDED, §14).
8. **Implementation boundary:** Semantic categories only — no endpoint names, no framework, no
   schema.
9. **Additional authority required:** No.

### D16-11 — UI/product boundary

1. **ID:** D16-11. 2. **Question:** What belongs to the UI/product layer vs serving/query vs
   historical processing.
3. **Evidence:** intent §5 (critical boundary), §9 (Dashboard/Data Explorer direction), §12
   (simplicity); D15 §14 (UI ABSENT; data backing mapped).
4. **Existing intent:** "The UI must not become the historical processing engine… UI reads through
   the serving/query layer"; non-drift #12 (preserve the demonstrated I4 UI model as the target
   reference).
5. **Decision:** **ADOPT**:
   * **UI owns:** presentation, navigation, query construction (Q1–Q10), result display,
     status/evidence display, report presentation, user interaction, saved-query management.
   * **UI must not own:** parsing, classification, processing, validation, evidence generation,
     publication, registry mutation, derived-state re-derivation, or direct access to durable data
     (always via serving).
   * **UI may expose, as explicit user-initiated delegated operations:** (a) archive
     discovery/processing trigger (executed by the ingestion boundary; the UI shows progress/status
     from processing metadata only); (b) serving-state rebuild trigger (executed by the serving
     boundary; a maintenance operation). Everything else is read-only through serving.
   * **Target presentation:** the demonstrated I4 application (non-drift #12); first-release scope
     = D16-12.
6. **Rationale:** Fixes the intent's critical boundary as an authority decision with an explicit
   whitelist of the only two delegated operations.
7. **Consequences:** The UI can never become a second processing engine by drift.
8. **Implementation boundary:** Ownership boundary only — no UI technology, no screens, no code.
9. **Additional authority required:** No.

### D16-12 — First-release product scope

1. **ID:** D16-12. 2. **Question:** The minimum useful single-user product scope for the first
   release.
3. **Evidence:** D15 §14 (data backing verified for each Dashboard tile and Explorer capability);
   the I5-qualified baseline (D14) as the data source; intent §14 Q13 ("Which exact subset of the
   demonstrated UI becomes the first serving release?").
4. **Existing intent:** §9 (Dashboard + Data Explorer direction), §16 lifecycle (serving and
   ingestion as parallel post-authority tracks).
5. **Decision:** **ADOPT** — first release = **read-only serving + presentation over the qualified
   M2 baseline** (plus any approved incremental publication present at that time):
   * **Dashboard:** the demonstrated reference tiles whose data backing D15 verified (run
     identity/status, archive count, canonical rows, identity records, calendars, errors, rows by
     year, archives by exchange segment, data coverage, archive inventory + details, reconciliation
     summary) — all from durable data classes (1)–(3).
   * **Data Explorer:** query categories Q1–Q10 with record detail + provenance, quality views,
     yearly summaries, and as-published price/field display (charts over as-published values).
   * **Saved queries + query history** (serving state 4).
   * **Explicitly excluded from the first release:** the incremental-processing operation
     (discovery/processing triggers), raw-content serving, DEC-1/eligibility features, and every
     non-goal in §13 of this record.
   * **Rationale:** the minimum useful scope is "the demonstrated application's read experience over
     qualified data"; incremental ingestion, though architecturally decided (D16-01–06), is not
     needed for the first release's usefulness and carries the highest implementation risk (registry
     + publication + re-derivation) — its implementation therefore follows as a **second**
     implementation gate (the intent's §16 lifecycle shows the two tracks as parallel, not
     sequential dependencies).
6. **Rationale:** Simplicity principle (intent §12): the smallest scope that delivers the
   demonstrated product; risk-ordered sequencing without deferring the architecture.
7. **Consequences:** A future implementation-authority decision can scope the first release
   precisely (read-only serving + first-release UI) with D16-08/09/10/11/12 as its contract.
8. **Implementation boundary:** Scope statement only — no screens, no endpoints, no code.
9. **Additional authority required:** **Yes** — implementation authorization for the first release
   is a future authority decision (D16-13 withholds all implementation).

### D16-13 — Implementation-authority boundary (the controlling decision)

1. **ID:** D16-13. 2. **Question:** What is now authorized for implementation; what remains
   deferred; what requires a later authority decision; may serving/API, incremental-ingestion,
   persistence, or UI implementation begin?
3. **Evidence:** D14 §9 (exhaustive non-authorizations; the house rule that an architecture/
   decision record authorizes nothing executable); D15 §21 (INVESTIGATION COMPLETE — ARCHITECTURE
   DECISION REQUIRED; "No serving, incremental-ingestion, UI, or persistence implementation is
   authorized"); intent §17 (a future governance decision must adopt the intent **before
   substantive post-I5 implementation** — adoption is now done in §4; the implementation
   authorization itself remains open by intent design); the D06→D07 precedent (adoption ≠
   implementation authorization); the D16 directive itself ("Do NOT grant implementation authority
   merely because the architecture has been decided").
4. **Existing intent:** §11 (what must not be assumed yet); §14 (questions to be resolved "when the
   post-I5 serving/consumption phase is formally authorized").
5. **Decision:** **ADOPT** the following, stated exhaustively:
   * **ARCHITECTURE DECISION:** ESTABLISHED by this record (D16-01…D16-12), including adoption of
     the intent artifact as governing target intent (§4).
   * **IMPLEMENTATION AUTHORITY = NOT GRANTED.** On the strength of this record alone: **serving/API
     implementation may NOT begin; incremental-ingestion implementation may NOT begin; persistence
     implementation may NOT begin; UI implementation may NOT begin.** No implementation library or
     framework is selected or implied.
   * **What this record authorizes:** nothing executable. It authorizes only: (a) the future
     authority to grant implementation against the decided architecture; (b) read-only
     investigation; (c) documentation of future decisions.
   * **What remains deferred:** all implementation (first release per D16-12; incremental ingestion
     per D16-01–06); D16-03a changed-content disposition (EVIDENCE REQUIRED); the requalification
     migration mechanism (first version change); MD-12 physical store selection (if/when needed);
     raw-content serving (if ever); any scope change to single-user.
   * **What requires a later authority decision (enumerated):** (1) first-release
     implementation authorization (read-only serving + first-release UI, contract = D16-08/09/10/
     11/12); (2) incremental-ingestion implementation authorization (contract = D16-01–06 +
     D16-02); (3) D16-03a; (4) requalification migration mechanism; (5) MD-12; (6) raw-content
     serving. Each follows the house pattern: decision input → explicit authorization → scoped
     implementation → evidence → remote verification.
   * **No authority expansion:** D14's non-authorizations (no serving/API/UI/persistence/production/
     semantic/execution authority from I5) stand unchanged; this record adds an architecture and
     removes nothing.
6. **Rationale:** The task mandates the ARCHITECTURE-DECISION / IMPLEMENTATION-AUTHORIZATION
   distinction; the repository's own pattern (D06 adopted the model; D07 separately authorized
   implementation) is the precedent; granting implementation here would be exactly the "authority
   expansion" the directive forbids.
7. **Consequences:** The repository now holds a fully decided post-I5 architecture with an explicit,
   verifiable non-implementation status; the next gate (if any) is an **implementation-
   authorization** gate, not an architecture gate.
8. **Implementation boundary:** This decision *is* the boundary: zero implementation.
9. **Additional authority required:** Yes — for every item enumerated in (5).

---

## 8. Approved architecture boundaries

```
Archive discovery (read-only re-scan; D01 record shape; PF fail-closed)      [owner: ingestion]
        ↓
Archive identity / content fingerprint (apparent + sha256; D16-03 classes)   [owner: ingestion]
        ↓
Historical processing engine (process NEW only; deterministic per-archive)   [owner: engine]
        ↓
Qualified canonical historical dataset:
   (1) qualified M2 baseline — IMMUTABLE          (owner: qualification record)
   (2) incremental publications                   (owner: engine, MD-11-style)
   (3) processed-archive registry (single writer) (owner: ingestion boundary)
        ↓
Durable persistence boundary — TECHNOLOGY = UNDECIDED (MD-10 standard; MD-12 stands)
        ↓
Serving / query boundary (read-only consumer; Q1–Q10; derived state (4) rebuildable)
   (4) serving/derived state — pure derivation of (1)+(2)+(3), never a source of truth
        ↓
Single-user product / UI (presentation only; two delegated operations; reads via serving)
```

For each boundary: **owner** as labeled; **responsibility / authoritative state / may change / may
NOT change** are fixed by D16-01–D16-11: ingestion may change (2) and (3) only through approved
publications and never (1); serving may change (4) only by re-derivation and never (1)–(3); the UI
may change nothing durable; the engine never reads (4); queries never mutate (1)–(3).

## 9. Approved incremental model (conceptual flow — not implemented)

new archive discovered (read-only scan) → identity/content classification
(UNCHANGED: skip | NEW: process | CHANGED: held + flagged per D16-03 | Anomalous: finding) →
process only NEW archives (per-archive, deterministic, into their content partition) → re-derive
corpus-scoped derived state from all processed canonical rows (D16-05 invariants) → validate
(reconciliation discipline; package manifest; run identity; version bindings recorded) → publish
durable state (partition contributions + derived state + manifests + registry update, one approved
publication) → make approved result visible to serving (serving reads (1)+(2)+(3); may rebuild (4))
→ UI consumes serving (read-only). CHANGED content is **never** silently treated as unchanged or
reprocessed — it stays held until D16-03a (fail-closed default: quarantine).

## 10. Changed-content / requalification disposition

* **CHANGED CONTENT (D16-03a): EVIDENCE REQUIRED / quarantined by default.** No policy invented; the
  intent's four candidate outcomes (conflict / reprocessing / replacement-versioning / quarantine)
  remain open for the future decision when a changed archive actually presents; until then the
  fail-closed hold applies.
* **REQUALIFICATION (D16-04):** applicability condition ADOPTED (processed = content × version
  bindings; mismatch ⇒ stale; staleness is a registry census, not an execution); migration
  mechanism DEFERRED to the first actual version change; no requalification performed or implied.

## 11. Serving dataset boundary

The five-class exposure boundary of D16-08: canonical historical data / provenance+evidence /
processing metadata / minimal operational metadata — MAY be exposed; raw archive content — NOT
exposed by default (Windows custody; future decision + cross-environment mechanism required).
D05 consumer obligations bind all exposure. Source-row granularity = member/archive + verbatim
fields (row offsets never adopted).

## 12. Query / product scope

Q1–Q10 semantic categories (D16-10) + saved queries/query history; first release = read-only
serving + presentation over the qualified baseline (D16-12); explicitly excluded: eligibility/
master (DEC-1), computed analytics beyond as-published + derived state, raw-byte serving, all §13
non-goals.

## 13. Explicit non-goals (binding)

No authentication; no RBAC; no multi-user support; no PostgreSQL; no enterprise deployment /
identity infrastructure; no tenant isolation; no organization/team administration; no
enterprise-scale distributed architecture; no implementation libraries/frameworks selected or
implied; no rerun of I4 or I5; no modification of the qualified dataset or existing engine
behavior; no authority expansion beyond this record's stated decisions.

## 14. Technology decisions / undecided items

**TECHNOLOGY = UNDECIDED** — for every physical concern: persistence store (MD-12 stands; MD-10 is
the grading standard if selection ever occurs), API framework, UI technology, hosting/deployment
model, ingestion scheduler/archive-watcher mechanism, registry storage format, query engine. No
technology named, ranked, preferred, or implied anywhere in this record (task technology-neutrality
requirement honored; no concrete-technology decision was unavoidable).

## 15. Implementation-authority disposition

> ### **ARCHITECTURE DECISION = ESTABLISHED. IMPLEMENTATION AUTHORITY = NOT GRANTED.**

Serving/API implementation: may NOT begin. Incremental-ingestion implementation: may NOT begin.
Persistence implementation: may NOT begin. UI implementation: may NOT begin. The enumerated later
authority decisions (§7 D16-13(5)) are required before any of them.

## 16. Deferred decisions

Requalification migration mechanism (first version change); registry physical format (until an
implementation decision); any new (family, year) partition key or new format family (explicit
review); incremental-ingestion implementation scope; serving implementation scope; first-release UI
implementation scope.

## 17. Evidence-required decisions

**D16-03a changed-content disposition** (quarantine-by-default until decided); requalification
migration mechanism (evidence = first stale census); raw-content serving (if ever desired).

## 18. Consequences

1. Post-I5 architecture is fully decided; future implementation debates are bounded to
   implementation choices inside decided contracts, not to re-litigating architecture.
2. The single-user simplicity principle is a governing constraint on every implementation
   decision (no enterprise drift by convention).
3. The qualified baseline's immutability and the baseline/serving persistence distinction are
   authority-fixed.
4. Changed-content and requalification-migration questions are formally held with fail-closed
   defaults — no silent policy can creep in.
5. The next gate, if the authority proceeds, is an **implementation-authorization** gate
   (first release per D16-12 and/or incremental ingestion per D16-01–06), each with its own
   explicit authorization, evidence, and verification pattern.

## 19. Artifact / evidence inventory

**This record:** `docs/architecture/POST_I5_SERVING_INCREMENTAL_PRODUCT_ARCHITECTURE_AUTHORITY_
DECISION.md` (the only mutation). **Governing inputs (verified byte-identical at `origin/main@
d60eb3d4…`):** intent artifact (blob `41ad2740…`, SHA-256 `7e4a14f4…`); D15 investigation (blob
`79157b82…`). **Cited evidence base (as recorded in D15/D14):** D05 spec; D06; D07 §§8–13; D08
§§4–18 (MD-02…MD-17); D11 (§1/§11/§12); D12 (§3/§6/§9–11); D14 (§§5–9); D01 inventory +
`INVENTORY_REPORT.md`; `tools/i4_runner/` (`i4_preflight.py` PF-10/11/12, `i4_inputs.py`,
`i4_identity.py`, `i4_output.py`, `i4_runner.py`); `src/nse_engine/` (`identity.py`, `contract.py`,
`blocked.py`, `pipeline.py`, `w2_stream.py`); `evidence/D11_REPLAY_QUALIFICATION_20261009/`;
`evidence/inventory/`.

## 20. Final authority statement

By the explicit D16 authority decision recorded here: the post-I5 serving / incremental-ingestion /
product architecture is **ESTABLISHED** as decided in D16-01…D16-13; the product & serving
architecture intent artifact is **ADOPTED** unmodified as governing target intent; the qualified M2
baseline, the registry contract, the incremental model, the serving dataset boundary, the query/
product scope, and all responsibility boundaries are fixed; all physical technologies remain
**UNDECIDED**; and

> ### **IMPLEMENTATION AUTHORITY = NOT GRANTED.**
> No serving/API, incremental-ingestion, persistence, or UI implementation is authorized by this
> record. Implementation may begin only under a later explicit authority decision for a stated
> scope (§7 D16-13(5)), following the house pattern of decision input → explicit authorization →
> scoped implementation → evidence → remote verification.
