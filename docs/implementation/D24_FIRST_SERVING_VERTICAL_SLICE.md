# D24 — FIRST-RELEASE SERVING IMPLEMENTATION: INITIAL VERTICAL SLICE (IMPLEMENTATION RECORD)

## 1. Task identity and purpose

**D24** implements the first bounded, testable vertical slice of the first-release
serving architecture under the D23 authority decision
(`docs/architecture/D23_FIRST_RELEASE_SERVING_IMPLEMENTATION_AUTHORITY_DECISION.md`).
The slice establishes a real, read-only path from the qualified M2 baseline to a
serving consumer: pinned baseline identity verification → deterministic, rebuildable
class-(4) read model → one query category (Q3 instrument query, D16-10) with
row-level D05 §8 provenance → user-initiated serving-state rebuild (delegated
operation (b)). This record describes **actual behavior and executed evidence only**.

## 2. Authoritative baseline and repository identity

| Item | Value |
|---|---|
| Repository | `ramkivs/nse-historical-data-engine` (public; remote `origin`) |
| `origin/main` (remote-verified, exact) | `01612f7f983ed2ac70e17d6814d02968aae845c7` = D23 (D22+D23 jointly promoted by the user; D16-03a RESOLVED on main) |
| Session branch at work | `arena/9021d1a1-nse-historical-data-engine` at `01612f7…` (D23); 14th sandbox `.git` rollback at task start, repaired non-destructively (unshallow → ancestry YES → `update-ref` → `read-tree` → `checkout-index`); worktree clean before the first mutation |
| Governing artifacts at baseline | D23 (blob `db4645e9…`), D22 (blob `962cda55…`), D16 (blob `1b6e2faf…`), D21 (blob `d1c127bd…`), intent (blob `41ad2740…`) — all verified present and unchanged at baseline |

## 3. D23 authority and scope (what this task may and may not do)

- **Authorized (D23 §17 GRANTED):** first-release read-only serving/query layer over the
  qualified M2 baseline; presentation/consumption within D16-11/12; serving state
  class (4) (rebuildable); serving-state rebuild as delegated operation (b); technology
  selection within the D23 §13 bounded constraints (single-user; no auth/RBAC/multi-user;
  no PostgreSQL/enterprise; read-model = pure rebuildable derivation; no canonical
  reinterpretation; MD-10 grading + recording; no live market-data access).
- **Withheld (D23 §17/§19 — not touched by this task):** incremental ingestion/processing;
  delegated operation (a) processing trigger; requalification; per-instance CHANGED
  resolution (and any resolution mechanism); raw-content serving; DEC-1; any engine or
  canonical-data alteration; any query category beyond the implemented slice.
- **This slice implements exactly one query category (Q3)** plus the maintenance
  operations (verify/build/rebuild/info diagnostics) that support it — deliberately not
  the full Dashboard, the full Data Explorer, or the full Q1–Q10 surface.

## 4. M2 source identity and qualification evidence

The qualified baseline is the I4-qualified package **`i4-20261008-M2`** (D12/D14
qualification; I4: 2,462 archives/members, 5,689,949 rows, 12 partitions, 0 gating
divergences). Its identity, pinned in `serving.baseline.DEFAULT_M2_SPEC` from
**repository-durable evidence only** (never from the package itself):

| Identity | Value | Durable evidence source |
|---|---|---|
| `package_manifest_sha256` | `e7c7e4c8271f3a1c8ef42d76b926fe048a8997a342c92d89819eecd79e73b9dc` | `evidence/D11_REPLAY_QUALIFICATION_20261009/…/A.PACKAGE_FILES.tsv` + `PACKAGE_MANIFEST.sha256` (in-repo tarball); recomputed sha256 of the manifest bytes matches |
| file count | 4,948 | `A.PACKAGE_FILES.tsv` (4,948 data rows; incl. manifest + marker) |
| total bytes | 21,119,807,344 | sum of `A.PACKAGE_FILES.tsv` sizes (recomputed in-test: exact match) |
| run id | `i4-20261008-M2` | `RUN_RECORD.json` / `RUN_COMPLETE.json` (in-repo tarball) |
| composite run identity | `9609c7fccef1d2438810a564ef70aa8232d8ad1c69fded8702e488c13657802d` | `RUN_RECORD.json` |
| engine `tool_sha256` | `d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9` (nse-engine w2-1.0.0, 17 modules) | `RUN_RECORD.json` `engine_identity` |
| runner `runner_sha256` | `f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a` (i4-runner-1.0.0) | `RUN_RECORD.json` `runner_identity` |
| archive count / set digest | 2,462 / `54d81507…` | `RUN_RECORD.json` `corpus` |
| row count | 5,689,949 | `RUN_RECORD.json` `counts.rows` |

Package layout (from the in-repo `PACKAGE_MANIFEST.sha256`, 4,946 entries + manifest +
marker): `partitions/<family>/<year>/rows/<member>.rows.jsonl` (class 1 — 2,462 row
files) and `partitions/<family>/<year>/evidence/<member>.evidence.json` (class 3 —
2,462); families `legacy13` (2016–2024) and `udiff34` (2024–2026) = 12 partitions;
`w2/*` W2 derived output (class 2); `INPUT_MANIFEST.jsonl`, `PREFLIGHT.jsonl`,
`RECONCILIATION.jsonl`, `GOVERNED_INPUTS.json`, `RUN_RECORD.json`, `manifests/*.sha256`
(class 3); `RUN_COMPLETE.json` completion marker written last (a package without it is
incomplete by construction, RD-9).

**Environment fact (material, reported):** the physical 21 GB package is **not present
in this sandbox environment**. The 14th rollback at task start removed the previously
untracked `_transfer_delivery/` (which held the delivered M2 package; the D20
test-only root was also removed — its evidence is committed in the D20 artifact).
Consequently the *byte-level* run over the real package (full 4,948-file digest
verification, 5,689,949-row index build, rebuild reproducibility) **could not be
executed here**. It is implemented, tested on the fixture, and staged as the
`D24_M2_ROOT`-gated integration tests (`tests/test_serving_m2_integration.py`), which
are reported **skipped** with an explicit reason — never as passed. Baseline
*identity* verification is nonetheless executed in every run, against the in-repo
durable transfer evidence (§15, item 2).

## 5. Selected technology/mechanism and supporting evidence (D23 §13 delegation exercised)

| Concern | Selection | Rationale (repository-based) |
|---|---|---|
| Language/runtime | **Python 3, standard library only** | repo convention (engine, runner, tests are stdlib-only; determinism guard); zero new dependencies; no network install |
| Serving read-model (class 4) | **single canonical-JSON index file + sha256 sidecar** on local disk (`serving_index.json` / `serving_index.sha256`) | D05 §9 canonical conventions (sorted keys, compact, LF, final newline); human-auditable; no DB server; .gitignore already excludes `*.db`/`*.duckdb`; state lives outside the package |
| Read-model content | per row-file: set of `(listing_symbol, series)` pairs + row count; per partition: file/row counts; package identity block; global counts | file-level narrowing keeps the index compact and the query a bounded streaming scan; no row values or raw text stored in the index (provenance stays with the rows) |
| Query mechanism | **in-process streaming JSONL scan** over the candidate files named by the index; exact as-published equality on `(listing_symbol, series)`; deterministic ordering | D16-10 Q3 semantics only — no DSL/expressions (D23 §10); stdlib `json` |
| Source-data access | **direct read-only filesystem access** to the package directory; integrity enforced by the package's own `PACKAGE_MANIFEST.sha256` + `RUN_COMPLETE.json` marker + pinned identity | the existing access mechanism (the runner's `verify_package` semantics, verify-01..07, re-implemented at the serving boundary with no runtime dependency on engine write-path tooling) |
| Consumer boundary | **CLI** (`python3 -m serving`: verify/build/query/rebuild/info) + importable API (`serving.*`) | single-user personal-use (D23 §13); no network listener, no auth, no multi-user; D16-11 consumer reads only through the query layer |
| State location | caller-supplied `--state` directory, **outside the package**; `serving-state/` added to `.gitignore` (derived state is never committed) | D16-07: (4) distinct from (1); the runner's own self-check rejects unlisted files inside a package, so writing inside it would corrupt package validity |

**MD-10 grading (D08 §10, required by D23 §13 constraint 7) — the class-(4) file store
demonstrably satisfies:** (1) deterministic representation/retrieval — canonical
serialization, sorted structures, no clock/host/path; two independent builds are
byte-identical (tested); (2) provenance preservation — the index embeds the package
identity (manifest digest, run id, composite identity, engine/runner sha256, archive
count) and stores no row content, so row provenance is preserved untouched in the rows;
(3) integrity verification — sidecar digest verified on load; baseline verified before
any serving; (4) replay/reproducibility — delete-and-rebuild reproduces identical bytes
(tested); (5) durability per MD-05 classes — class (4) pure derivation; deletion is
never a data event (tested); (6) corpus-scale operation — one linear pass over row
files + bounded streaming queries; no full materialization of the 21 GB; (7) required
downstream consumption — serves the Q3 consumer and a stable API for later slices.

**Physical concerns left open under MD-12 / not selected:** all non-class-(4) concerns
(canonical persistence, registry storage, scheduler) per D23 §12; a persistent read-model
store beyond the single JSON file (re-grade under MD-10 if a later slice needs it); HTTP
transport and any frontend (later slices).

## 6. Alternatives considered

- **SQLite (stdlib `sqlite3`) read model** — not selected for this slice: a database
  file is a durable artifact with schema-evolution and tooling concerns; the repo's
  own `.gitignore` excludes `*.db`/`*.duckdb`; the JSON document is simpler,
  human-auditable, and MD-10-satisfying at this scale. Re-evaluable under MD-10 if a
  later slice's query scale requires it.
- **Full in-memory row table** — rejected: 5,689,949 rows / ~21 GB does not fit a
  bounded single-user memory budget; file-level index + streaming scan is bounded.
- **HTTP/JSON API server as the consumer** — deferred: a network listener adds
  host/origin/deployment surface the first slice does not need; D23's single-user
  constraint and the non-goal list argue against server infrastructure at this stage.
  The importable API makes a later transport a thin wrapper.
- **Parquet read model** — not stdlib-capable; the package is already JSONL — reading
  the native canonical format avoids conversion and re-interpretation.
- **Reusing the runner's `verify_package` via import** — rejected on boundary
  discipline (the runner is engine-boundary write-path tooling; serving must not depend
  on it at runtime): the same verify-01..07 semantics are re-implemented in
  `serving/baseline.py` (transcribed MD-05 rules included), so the two boundaries stay
  independent.

## 7. Implemented architecture and file inventory

New (serving boundary, separate package from `nse_engine`):

| File | Lines | Role |
|---|---|---|
| `src/serving/__init__.py` | 58 | public API + boundary documentation |
| `src/serving/baseline.py` | 342 | `BaselineSpec`/`DEFAULT_M2_SPEC` pin; `open_baseline` — read-only open + verify-01..07 (manifest, per-file digests, no-unlisted, completion marker, partition manifests, MD-05 classifiability, run-record identity vs pin) — fail-closed `BaselineError(check, detail)` |
| `src/serving/index.py` | 191 | class-(4) read model: `build_index` (one linear read-only pass), canonical-JSON write + sha256 sidecar, `load_index` (digest + package-identity/staleness check → `ServingIndexError`) |
| `src/serving/query.py` | 109 | **Q3 instrument query** only: exact as-published `(listing_symbol, series)` match, optional year filter, deterministic ordering, row provenance + serving envelope, `raw_line` excluded from the served view |
| `src/serving/rebuild.py` | 65 | delegated operation (b): deletes exactly the two known state files (refuses unknown files), rebuilds, reports before/after digests + `identical` |
| `src/serving/cli.py` | 158 | `verify`/`build`/`query`/`rebuild`/`info`; JSON to stdout; exit 0/2/3; read-only w.r.t. the package |
| `src/serving/__main__.py` | 6 | `python3 -m serving` entry |

New (test-only):

| File | Lines | Role |
|---|---|---|
| `tests/serving_fixtures.py` | 332 | **synthetic** layout-conformant package builder using the repo's own engine (`build_canonical`) — byte-exact canonical rows, real tool fingerprint, fixed run id, no clock; 4 members / 3 partitions / 9 rows; returns a pinned `BaselineSpec`. Explicitly never the M2 baseline |
| `tests/test_serving_baseline.py` | 183 | verification pass/fail-closed matrix; read-only discipline; M2 pin vs in-repo D11 transfer evidence |
| `tests/test_serving_query.py` | 262 | Q3 semantics (exact as-published key, per-family listing_symbol semantics, None-vs-blank, ordering, year filter, unknown instrument, provenance envelope); index determinism; rebuild reproducibility; stale/corrupt index refusal |
| `tests/test_serving_m2_integration.py` | 129 | M2 identity vs in-repo transfer evidence (always run) + real-package integration gated on `D24_M2_ROOT` (skip-reported when absent) |

Modified: `.gitignore` (+3 lines: `serving-state/` — derived state never committed).
**No engine (`src/nse_engine`), runner (`tools/`), spec, governance, or evidence file
was modified.**

## 8. Selected query category and exact contract

**Q3 — instrument query (D16-10):** "instrument query (symbol/series correlation key;
ISIN treated as a non-identity attribute per D05 §§6–7)".
- **Key:** `(listing_symbol, series)`, matched by **exact equality of the as-published
  values** — no case/whitespace normalization, no expression language. `listing_symbol`
  is the canonical field mapped from `SYMBOL` (legacy13) / `FinInstrmId` (udiff34)
  (D05 §3.1/`contract.CANONICAL_FIELD_MAP`) — so the same underlying company may carry
  different `listing_symbol` values across families (ticker sits in
  `underlying_symbol`/`TckrSymb` for udiff34). Cross-family correlation via ISIN is **not**
  part of Q3 (ISIN is a non-identity attribute) — the served row makes both values
  visible exactly as published. This is demonstrated by test, not assumed.
- **Result row:** the canonical row exactly as stored (`source_values` as-published
  text; `business_date`; non-gating `flags`; `isin_validity` informational; the row's own
  D05 §8 `provenance` block), plus a serving envelope (query id, source file, family,
  year). `None` = field absent in that family; `""` = blank as published — neither is
  ever defaulted (D05 §2 rule 3). `raw_line` (retained raw text) is **not** served
  (as-published fields are served; raw row-text exposure would require a future explicit
  decision in the spirit of D16-08 class-5 exclusions).
- **Ordering:** deterministic `(business_date, format_family, year, source file,
  source line number)`.
- **Boundary proof:** the public query surface is `serving.query_instrument` alone — no
  other category, no ad-hoc expressions (D23 §10).

## 9. Canonical-data immutability evidence

- `open_baseline` and every operation open package files **read-only** (`"rb"`/`"r"`
  only); no write path to the package exists in `src/serving` (verified by code
  inspection — the only `open(..., "w")` targets are the caller-supplied state dir).
- Executed proof (fixture, `ReadOnlyDisciplineTests.test_every_serving_operation_leaves_the_package_byte_identical`):
  sha256 of **every** package file before vs after verify → build → query → rebuild —
  byte-identical (18/18 files). The same mechanism (full per-file digest verification,
  verify-02) applies to the real package when provisioned.
- The index stores **no row content and no raw text** — derived state cannot shadow or
  carry canonical bytes (D16-07: (4) never absorbs/reinterprets (1)).
- No D01 inventory, D05 spec, qualification record, or archive was touched (worktree
  diff: only the files in §7; `git status` verified pre-commit).

## 10. Provenance and processing-metadata behavior

- **Row provenance (D05 §8):** every served row carries its own stored provenance block
  (`source_archive` + `archive_sha256` + `member_name` + `format_family` + dual member
  hashes + `spec_version` `D05/1.0` + tool name/version/`tool_sha256` + `run_id` +
  `evidence_refs`) — served verbatim from the row, never recomputed or filled in
  (tested: values match the fixture's governed source descriptor and the real engine
  fingerprint).
- **Run/version bindings:** the index embeds the package's run identity (run id,
  composite run identity, engine/runner sha256, archive count) and every query loads the
  index only after verifying that identity against the freshly verified baseline
  (stale index → refused). Missing values stay `None`/absent — never defaulted to a
  valid-looking positive (e.g. unpinned handles carry `package_name: "unpinned"`).
- **Processing metadata exposed by this slice:** only what the rows and index carry
  (partition family/year, per-file row counts, package counts). `INPUT_MANIFEST.jsonl`,
  `PREFLIGHT.jsonl`, `RECONCILIATION.jsonl` (Q8/Q9/Q10 territory) are verified as
  package integrity inputs but are not parsed or re-exposed yet — a later slice, with
  nothing invented now.

## 11. D21 changed-content safeguards

D21 is preserved exactly at the slice level:
- **Fail-closed package admission:** any file present in the package but absent from
  `PACKAGE_MANIFEST.sha256` (verify-03) fails the whole package closed — **nothing is
  served from a package containing unknown content**. Test: an injected unlisted
  "candidate" row file makes `open_baseline` raise `verify-03` (nothing served). A
  changed candidate therefore has no path into canonical serving in this slice.
- **No CHANGED state exists in an M2-only first release** (no class-(3) registry is
  present or read), consistent with D22 §10; the implementation introduces no state,
  data path, or operation by which candidate content could become serving-eligible.
- **No resolution mechanism, no registry, no workflow** was implemented (D21 §22 /
  D23 §15 — withheld).
- **Prior-data authority:** serving only ever reflects verified class-(1)/(3) package
  content; no marking, downgrade, or hiding of any prior data is implemented or
  implied.

## 12. Rebuild behavior and reproducibility evidence

- **Delegated operation (b)** (`serving rebuild` / `serving.rebuild_state`): removes
  exactly the two known class-(4) files (refuses to delete anything unknown — tested),
  rebuilds the index from the verified baseline, and reports
  `{before_sha256, after_sha256, identical, files_scanned, rows_scanned,
  instrument_pairs, package_manifest_sha256}`.
- **Executed proofs (fixture):** (a) two independent builds → byte-identical index;
  (b) delete both state files → rebuild reproduces the exact prior bytes
  (`after_sha256` == pre-deletion digest); (c) rebuild over the unchanged baseline
  reports `identical: true` (CLI smoke: `before == after == 257a4b6a…`); (d) index
  built over a different (self-consistent) package identity is **refused** as stale
  (`index-stale`) until rebuilt — the baseline always wins (D16-07 conflict rule);
  (e) deleting the state is never a data event — the query results are unaffected by
  delete+rebuild.
- Over the real M2 package, the same mechanism is staged as
  `M2RealPackageIntegrationTests.test_rebuild_reproducibility` (skipped here — §4).

## 13. Tests executed and exact results

House runner: `PYTHONPATH=src python3 -m unittest discover -s tests -t .`
- **Full suite: `Ran 514 tests` — `OK (skipped=3)`** (baseline suite 481 + 33 new).
- New serving tests: 33 run — **30 passed, 3 skipped**. The 3 skips are
  `M2RealPackageIntegrationTests` (full verification, Q3 over the real baseline, rebuild
  reproducibility) — skipped with the recorded reason "qualified M2 package not present
  in this environment (D24_M2_ROOT unset); real-package integration is PENDING baseline
  provisioning, **not passed**".
- The 4 `M2BaselineIdentityTests` (always run) pass: pinned spec ↔ in-repo D11 transfer
  evidence (4,948 files; 21,119,807,344 bytes; manifest digest recomputed; run/engine/
  runner identity; 2,462 archives; 5,689,949 rows).
- CLI smoke executed: `verify` (7/7 checks pass) → `build` (index `257a4b6a…`, 9 rows,
  4 files, 6 instrument pairs, 3 partitions) → `query RELIANCE EQ` (3 rows) →
  `rebuild` (`identical: true`) → `info` (index summary) — all rc 0.
- No test counts are invented; no unexecuted test is reported as passed. The pre-existing
  `tests/test_i4_runner.py` ResourceWarnings (2) predate this task and were not touched.

## 14. Known limitations and deferred concerns

1. **Real-package byte-level execution pending** (environmental): the 21 GB M2 package is
   absent from this sandbox (rollback-removed `_transfer_delivery/`); the staged
   `D24_M2_ROOT` tests must run where the package is provisioned before the D23 battery
   items 2/5/7 count as fully closed. The identity layer (in-repo evidence) is
   continuously verified meanwhile.
2. **Index build cost on the real package:** one linear pass over 5,689,949 rows /
   21 GB (estimated low single-digit minutes on local NVMe) — acceptable as a
   user-initiated maintenance operation (op b), not yet measured on the real data.
3. **Single-file index:** the class-(4) index is one JSON document; at M2 scale its size
   is bounded by the per-file instrument-pair sets (≈ 2,462 file entries), but should be
   re-graded under MD-10 if it grows unwieldy (MD-12 remains open for a persistent
   store).
4. **Q3 only:** Q1–Q2, Q4–Q10 and saved-query persistence are later slices (contract
   already fixed by D16-10; D22 classified them READY BY EXISTING CONTRACT).
5. **No transport/UI yet:** consumption is via CLI/importable API; an HTTP layer or
   frontend is a later bounded selection (D23 §13/§14).
6. **`INPUT_MANIFEST`/`PREFLIGHT`/`RECONCILIATION` consumption (Q8/Q9/Q10 data backing)**
   not yet implemented — verified present, not yet parsed/exposed.

## 15. D23 closure-evidence matrix (D23 §18)

| # | Requirement | Status (evidence) |
|---|---|---|
| 1 | Authoritative source/repo/ref | **MET** — repo `ramkivs/nse-historical-data-engine`; session branch; this record's commit lineage (Phase 6) |
| 2 | Baseline identity verified unchanged | **PARTIAL (mechanism met; real-package run pending)** — pin implemented from in-repo durable evidence; identity tests pass every run; 4,948-file byte verification implemented (verify-02) and tested; execution over the real package pending provisioning (§4) |
| 3 | Technology decisions recorded | **MET** — §5 (selections, rationale, MD-10 grading) |
| 4 | Contract conformance | **MET for the slice** — D16-08 exposure classes (served = canonical rows + row provenance; raw bytes/row text excluded), D16-09 invariants (read-only; no processing invocation; failures can't corrupt), D16-10 Q3 only, D16-07 class (4) pure derivation, D05 as-published/None-vs-blank — each test-demonstrated |
| 5 | Canonical-data immutability proof | **MET at fixture level** (18/18 files byte-identical across verify/build/query/rebuild); real-package run pending as item 2 |
| 6 | D21 changed-content handling proof | **MET at slice level** — unlisted-content package fails closed wholesale (nothing served); no candidate path to serving; no resolution mechanism; no CHANGED state possible in M2-only first release (§11) |
| 7 | Deterministic/rebuildable serving state proof | **MET at fixture level** (byte-identical rebuilds; stale-index refusal); real-package run pending as item 2 |
| 8 | Query-boundary proof | **MET** — public query surface is `query_instrument` (Q3) only; no other semantics |
| 9 | UI boundary proof | **MET at slice level** — no UI implemented; consumer (CLI/API) reads only through the verified baseline + query layer; no direct durable-data access path in the public API |
| 10 | Tests | **MET** — 514 run / 511 passed / 3 skipped (skip reasons recorded) |
| 11 | Complete artifact inventory | **MET** — §16 |
| 12 | Remote durability + independent remote verification | **MET at publication** (Phase 6 of this task; reported in the final report) |

**Net:** 10 of 12 fully met; items 2/5/7 met as mechanism + fixture proof with the
real-package execution explicitly **PENDING baseline provisioning** — not manufactured
closed.

## 16. Complete artifact inventory

New: `src/serving/__init__.py`, `src/serving/baseline.py`, `src/serving/index.py`,
`src/serving/query.py`, `src/serving/rebuild.py`, `src/serving/cli.py`,
`src/serving/__main__.py`, `tests/serving_fixtures.py`, `tests/test_serving_baseline.py`,
`tests/test_serving_query.py`, `tests/test_serving_m2_integration.py`,
`docs/implementation/D24_FIRST_SERVING_VERTICAL_SLICE.md` (this record).
Modified: `.gitignore` (+3 lines). Nothing else. **Not created:** any server, database,
frontend, registry, migration, resolution mechanism, or other query category. No
serving state file is committed (state is caller-local; `serving-state/` ignored).

## 17. Explicit non-drift statement

No governance artifact was modified (D16/D21/D22/D23/D05/D08/D12/D14/intent unchanged).
No canonical historical data, qualification record, inventory, or evidence artifact was
created, modified, or re-qualified. No engine or runner module was changed (the
engine fingerprint used by the fixture is the same `d3269b73…` the M2 baseline was
produced by — continuity, not modification). No technology beyond the recorded
class-(4) file store was selected, named, or implied; no live NSE/provider access
exists or is attempted. Single-user personal-use scope and all D16 §13 non-goals are
preserved (no authentication, RBAC, multi-user, PostgreSQL, or enterprise architecture
anywhere in the new code). The slice is read-only with respect to the baseline by
construction and by executed digest proof.

## 18. Final status and remaining work

**D24 slice (code + tests + record): COMPLETE — implemented, tested (514/511 passed /
3 environment-skipped), and durable once this record is remotely verified.**
**D23 closure battery: 10 of 12 items fully met; items 2/5/7 carry the explicit
PENDING qualifier for the real-package byte-level run** (environmental gap: M2 package
absent from this sandbox; re-provisioning required; the staged `D24_M2_ROOT` tests
define the exact remaining execution).

Remaining authorized work (later slices, each under the standing D23 authority — no new
authority required for these): (a) run the staged real-M2 integration suite where the
package is provisioned and record the results (closes battery items 2/5/7); (b) Q1–Q2,
Q4–Q10 and saved-query state per D16-10; (c) Dashboard/Explorer presentation per
D16-12; (d) transport/frontend selection within D23 §13/§14 if/when desired.
**Withheld (separate future authority):** incremental ingestion (D16-13 item 2),
per-instance CHANGED resolution (D21 §22), requalification (D16-13 item 4),
raw-content serving (D16-13 item 6).

**D24 = COMPLETE / DURABLE / REMOTELY VERIFIED** for the implementation record itself
(subject to the Phase 6 remote verification reported in the task's final report); the
slice's real-baseline integration status is stated exactly as in §15 and is **not**
represented as completed.
