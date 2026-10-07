# D08 — I3 Output / Persistence Contract Decision Record

Gate: D08 — I3 contract closure + durable publication. Style precedent: D06 §14 / D07.
Recorded 2026-10-06. Decision authority: Ramki (explicit I3 authorization, 2026-10-06).
Publication baseline: `arena/9021d1a1-nse-historical-data-engine @ b86d25c182bf82e4e2a4c3a4775cff134df3bd66`.

## 1. Purpose and scope

D08 records the authorized I3 Output / Persistence Contract decisions (consolidated set MD-02 … MD-17,
DOC-01), applies the one authorized documentation correction (DOC-01), and publishes this record to the
designated authoritative ref for remote verification.

In scope by definition: the decisions below, the documentation correction, this record, and its
publication. Explicitly out of scope for this gate: persistence implementation, storage-technology
selection, I4 execution, API/serving implementation, UI/presentation implementation, and the deferred or
out-of-scope items recorded in §16.

This record changes **no** engine code, **no** canonical-model semantics, **no** corpus data and **no**
prior finding. It resolves no OPEN semantic and reopens no frozen item.

## 2. Authority — Ramki authorization provenance

Ramki (application decision authority) issued an explicit I3 authorization on 2026-10-06 against the I3
decision set, whose working documents are:

| Document | Location | Status |
|---|---|---|
| I3 output/persistence contract investigation (evidence base; 50-item register; 14 findings) | `/home/user/I3_OUTPUT_PERSISTENCE_CONTRACT_INVESTIGATION.md` | temporary; not committed |
| I3 decision matrix (consolidation; MD-01…MD-17 + DOC-01) | `/home/user/I3_DECISION_MATRIX.md` | temporary; not committed |
| I3 Ramki authorization sheet (per-decision questions, recommendations, blank decision fields) | `/home/user/I3_RAMKI_AUTHORIZATION_SHEET.md` | temporary; not committed |

Authorization outcome, as recorded here (each decision's exact scope in §§4–15):

| Decision | Authorized disposition |
|---|---|
| MD-02 Provenance completion | **ACCEPT WITH AMENDMENT** (§4) |
| MD-03 Evidence envelope | **ACCEPT WITH AMENDMENT** (§5) |
| MD-04 Output package / version / vocabulary | **ACCEPT** (§6) |
| MD-05 Durability classes | **ACCEPT** (§7) |
| MD-06 Partition rule | **ACCEPT** (§8) |
| MD-07 Persistence ownership | **ACCEPT** (§9) |
| MD-10 Store-selection standard | **ACCEPT** — `STORAGE TECHNOLOGY = UNDECIDED` (§10) |
| DOC-01 D05 §12 reference correction | **ACCEPT** (narrow correction; applied) (§11) |
| MD-11 I4 retained output | **ACCEPT** (§12) |
| MD-13 I4 execution authorization | **ACCEPT** — authorized, **not executed** (§13) |
| MD-14 Publication authority | **ACCEPT** — exercised by this record (§14) |
| MD-15 I3 closure ratification | **ACCEPT** — conditional on remote verification (§15) |

**Authority separation (binding).** The following are distinct and none may be inferred from another:
I3 architectural contract approval; I3 decision-record publication; I3 closure ratification; I4 execution
authorization; persistence technology authorization; persistence implementation; API/serving
authorization; UI/presentation authorization. See §17.

## 3. Baseline and evidence sources

**Baseline verified before mutation (2026-10-06, read-only):**

| Check | Observed | Verdict |
|---|---|---|
| Repository root | `/home/user/nse-historical-data-engine` | PASS |
| Branch | `arena/9021d1a1-nse-historical-data-engine` (designated session/authoritative ref for this publication) | PASS |
| Local HEAD | `b86d25c182bf82e4e2a4c3a4775cff134df3bd66` (W2/I2) — equal to the required baseline | PASS |
| Worktree | clean; no staged files; no untracked files | PASS |
| `origin` | `https://github.com/ramkivs/nse-historical-data-engine.git` | PASS |
| Remote session branch | `b86d25c182bf82e4e2a4c3a4775cff134df3bd66` (pre-publication) | PASS |
| Remote `main` | `89ce965c7961088950faf08b83a31f961e6fc214` (unchanged; not touched by this publication) | PASS |

**Evidence sources relied on:** D05 canonical model specification; D06 adoption record; D07 gate charter
and implementation authorization; D02 §8 (D02-era provenance proposal, explicitly non-binding);
D03 §15 closure (evidence packaging + CRLF/LF hash-basis lesson); `evidence/inventory/` and
`evidence/d03/windows_run/`; W1/W2 implementation reports and their determinism artifacts; repository
custody boundary (README; `.gitignore`); roadmap V2 downstream gap register (`V2-INV-2/3/4`, `G-01…G-20`).
Full citation detail remains in the temporary I3 investigation report named in §2.

## 4. MD-02 — Provenance completion: ACCEPT WITH AMENDMENT

**DECISION.** The existing D05/W1 provenance representation is authoritative for the current engine
contract.

1. The D02-era proposed fields `row_offset` and `raw_row_hash` were **not adopted** by D05 and **must not
   be retrofitted into W1** merely to reconcile the historical proposal.
2. The D02/W1 provenance discrepancy **remains explicitly recorded as a historical contract mismatch**
   (D02 §8 is a proposal that declares itself "no schema"; D05 §8 adopted a different record set). It is
   not silently resolved, and it is not erased.
3. **I4 traceability claims are therefore limited to the content-level traceability supported by the
   adopted D05/W1 contract**, unless a later explicit contract decision changes this. Content-level
   traceability today comprises: `source_archive`/`member_name` identity, member dual hashes
   (`member_sha256_raw_bytes`, `member_sha256_lf_text`), `archive_sha256` (+ its declared basis field,
   currently `not-supplied` until a corpus-side run binds it), `source_line_number`, `raw_line`,
   `tool_name`/`tool_version`/`tool_sha256`, `spec_version`, and `run_id`.
4. **This decision does NOT authorize modification of W1** (or W2). No engine file changes under MD-02.

**Effect:** the provenance contract is closed by decision at content-level; byte-offset reversibility is
explicitly not part of the current contract; the historical proposal stays visible for a future contract
decision should one ever be taken.

## 5. MD-03 — Evidence envelope: ACCEPT WITH AMENDMENT

**DECISION.** The durable evidence envelope must support, as applicable, the following **logical** evidence
requirements (no physical storage technology is selected or implied):

1. input identity;
2. input hashes;
3. output identity;
4. output hashes;
5. tool identity / version;
6. tool hash;
7. run identity;
8. declared hash basis (hash fields must state their own basis in-band — the `archive_sha256_basis`
   precedent, and the D03 §15 CRLF↔LF lesson);
9. manifests (input manifest naming consumed members + hashes; payload manifest over emitted artifacts);
10. validation / reconciliation evidence;
11. deterministic replay evidence.

The envelope is a contract over *what must exist and be resolvable*, not over *where or how it is stored*.

## 6. MD-04 — Output package / version / vocabulary: ACCEPT

**DECISION.** The engine shall have a **deterministic, versioned logical output package**.

1. Existing governed semantics remain authoritative; nothing in D05/D06 is re-described or replaced.
2. The existing **format-family vocabulary differences** (evidence-layer `LEGACY`/`UDIFF` per D01/D02/D03
   vs canonical-model `legacy13`/`udiff34` per D05/W1, with the implemented mapping) must be **explicitly
   represented / documented rather than silently conflated**.
3. **No new semantic vocabulary may be invented merely for implementation convenience.**

## 7. MD-05 — Durability classes: ACCEPT

**DECISION.** Establish **logical durability classes** distinguishing:

1. authoritative engine outputs;
2. derived outputs;
3. provenance / evidence;
4. execution / transient artifacts.

The classification is logical. **No physical storage technology is selected by this decision**, and no
retention location, period or replication is fixed by it.

## 8. MD-06 — Partition rule: ACCEPT

**DECISION.** Establish the **logical partitioning** required to support:

1. deterministic output;
2. deterministic replay;
3. integrity verification;
4. provenance;
5. corpus-scale processing;
6. future serving.

The partition contract must remain **technology-neutral**. Partitions must be content-derived (deterministic
from governed inputs), never size- or time-of-execution-derived.

## 9. MD-07 — Persistence ownership: ACCEPT

**DECISION.** Establish the persistence boundary / ownership at the **logical architecture level**.

1. The engine owns the contract for the outputs it produces.
2. A future persistence implementation **must preserve** the governed output, provenance, evidence,
   determinism and durability contracts — it may not reinterpret, re-derive, mutate or extend them.
3. **This decision does NOT authorize selection or implementation of a specific persistence technology.**

## 10. MD-10 — Store-selection standard: ACCEPT; storage technology status

**DECISION.** Any future storage-technology selection must **demonstrably satisfy** the approved logical
contract, including:

1. deterministic representation / retrieval;
2. provenance preservation;
3. integrity verification;
4. replay / reproducibility;
5. durability (per MD-05 classes);
6. corpus-scale operation (per MD-06 partitioning);
7. required downstream consumption (per MD-03 envelope).

**No concrete storage technology is selected by MD-10**, and none is selected by this record.

> **STORAGE TECHNOLOGY = UNDECIDED.**

MD-12 (storage technology + implementation) is **WITHHOLD / NOT AUTHORIZED** (§16). Nothing in this
record names, ranks, prefers or implies any technology; the names appearing in the repository's
fail-closed stub remain descriptions of an undecided choice, not candidates.

## 11. DOC-01 — D05 documentation correction: ACCEPT (applied)

**DECISION.** Authorize **only** the narrow reference correction for D05 §12 rows F4 and F15, which cited
a nonexistent "§6.5" (D05 §6 contains five numbered rules; the referenced content — "no eligibility
predicate is part of the canonical model" — is rule 5).

Applied correction (reference text only; **no substantive D05 semantics changed**; no unrelated
documentation cleanup):

| Row | Before | After |
|---|---|---|
| D05 §12 F4 | `§6.5 — no eligibility predicate` | `§6 rule 5 — no eligibility predicate` |
| D05 §12 F15 | `§6.5 — DEFERRED` | `§6 rule 5 — DEFERRED` |

This correction was applied in place in `docs/specs/D05_CANONICAL_MODEL_SPEC.md` as an explicitly
authorized, narrowly scoped amendment — **not** a silent alteration: it is recorded here with before/after
text and in the publication commit message. The D05 diff for this publication contains exactly these two
lines and nothing else. The F1–F17 register, its items and their governed status are unchanged.

## 12. MD-11 — I4 retained output: ACCEPT

**DECISION.** The future I4 corpus-scale run must retain sufficient deterministic run output and evidence
to reproduce, audit, and independently verify the run. At minimum the retained evidence must support:

1. input identity;
2. input hashes;
3. output identity;
4. output hashes;
5. tool identity / version / hash;
6. run identity;
7. deterministic replay evidence;
8. validation / reconciliation results;
9. unresolved-state evidence (governance-dependency annotations, calendar `label_status`, non-promotion
   notes, boundary residuals — carried, never resolved);
10. manifest information (per §5.9, including declared hash bases);
11. the approved **content-level traceability boundary** (§4.3).

**No persistence technology is implied.** This requirement is logical and satisfiable run-scoped.

## 13. MD-13 — I4 execution authorization: ACCEPT (not executed in this gate)

**DECISION.** Authorize the **non-production** 10-year historical corpus replay / full historical run
under the approved I3 contract.

1. The run must use the governed corpus (Windows-custody L0 archives; read-only) and must preserve the
   approved I4 retained-output / evidence requirements (MD-11).
2. The traceability claim is explicitly:
   **CONTENT-LEVEL TRACEABILITY UNDER THE ADOPTED D05/W1 CONTRACT** (§4.3).
3. The run **must NOT claim** implementation of the unadopted D02 `row_offset` / `raw_row_hash` proposal.

**This authorization does NOT authorize:** production ingestion; live NSE access; provider integration;
credentials; persistence-technology implementation; API; UI; serving; product deployment.

**Status:** I4 is **AUTHORIZED / READY TO EXECUTE — NOT EXECUTED** by this gate. No corpus access, no
archive scan and no run occurred here. Execution is a separate, subsequently scheduled action that must
follow MD-11 and this section's boundary.

## 14. MD-14 — Publication authority: ACCEPT (exercised)

**DECISION.** Authorize publication of the approved I3 decision record to the designated authoritative
repository/ref. Exercised as follows.

**Pre-mutation gate (all PASS; see §3):** repository identity verified; authoritative remote verified;
current baseline verified (`b86d25c…`); worktree inspected; unrelated work preserved (none present);
mutation set identified and limited to the intended I3 publication artifacts:

| # | Path | Change |
|---|---|---|
| 1 | `docs/investigations/D08_I3_OUTPUT_PERSISTENCE_CONTRACT_DECISION.md` | **new** (this record) |
| 2 | `docs/specs/D05_CANONICAL_MODEL_SPEC.md` | 2 reference corrections (DOC-01 only) |
| 3 | `README.md` | status block: D08/I3 record entry + record bullet |

No W1/W2 implementation file (`src/nse_engine/**`, `tests/**`), no evidence file, no tool file, and no
other document is modified. The publication is committed **only** to the designated branch
`arena/9021d1a1-nse-historical-data-engine`; `main` is not advanced.

**Post-mutation verification protocol (mandatory):** after commit — push to the designated branch; fetch;
verify the remote ref returns the exact commit SHA; verify the committed tree and content
(`git ls-remote`, remote-tracking ref resolution, tree comparison, and `git cat-file`/`git show` of this
path at the remote ref); verify only the three authorized paths changed; verify W1/W2 implementation
bytes unchanged; verify no storage technology was introduced; verify no I4 execution occurred.

**Durability claim:** this record is durable **only after** that remote verification passes. The record
itself does not claim durability; the verified commit SHA and verification result are reported in the
publication report for this gate (session report). If verification fails: `I3 = NOT DURABLE`, no closure
claimed.

## 15. MD-15 — I3 closure ratification: ACCEPT (conditional)

**DECISION.** After MD-02 … MD-07 and MD-10 have been recorded (§§4–10) **and** this decision record has
been durably published and remotely verified (§14), ratify:

> **I3 = CLOSED / DURABLE / REMOTELY VERIFIED**

**I3 is not ratified before remote verification succeeds.** If remote verification fails, I3 remains
**NOT CLOSED**, and the failure is recorded rather than worked around.

## 16. Non-authorized dispositions (MD-08, MD-09, MD-12, MD-16, MD-17)

| Item | Disposition | Effect |
|---|---|---|
| MD-08 — Serving ownership / runtime | **DEFERRED BY SEQUENCING** | no serving layer ownership defined; runtime environment still undefined; decision belongs to the future M/N gate |
| MD-09 — Consumer result contract | **DEFERRED BY SEQUENCING** | no consumer result shape/ordering/state/traceability exposure frozen; governed consumer obligations (units/provenance note, non-gating flags, no `FinInstrmId` identity, no overlay aggregation, unknown states displayed, no retroactive annotations) remain binding meanwhile |
| MD-12 — Storage technology + implementation | **WITHHOLD / NOT AUTHORIZED** | **STORAGE TECHNOLOGY = UNDECIDED**; no selection, no implementation, no ingestion, no deployment |
| MD-16 — DEC-1 | **DEFERRED / UNCHANGED** | eligibility predicate, ETF/master-snapshot association, delisting markers, corporate-action co-location all remain deferred; nothing in this record may be used as a back door to resolve them |
| MD-17 — UI design, API style, transport, hosting, exports, technology naming | **OUT OF SCOPE** | remain with their future gates |

No implementation authority is granted for any item in this section.

## 17. Authority boundaries (no inference)

| # | Authority | Granted by this record? |
|---|---|---|
| 1 | I3 architectural contract approval (MD-02…MD-07, MD-10) | **YES** — decisions recorded in §§4–10 |
| 2 | I3 decision-record publication (MD-14) | **YES** — exercised in §14 (to the designated branch only) |
| 3 | I3 closure ratification (MD-15) | **YES, conditional** — only after remote verification passes |
| 4 | I4 execution authorization (MD-13) | **YES** — but **I4 is NOT executed** by this gate |
| 5 | Persistence technology selection (MD-12) | **NO** — withheld; `STORAGE TECHNOLOGY = UNDECIDED` |
| 6 | Persistence implementation | **NO** |
| 7 | API / serving authorization (MD-08, MD-09) | **NO** — deferred by sequencing |
| 8 | UI / presentation authorization (MD-17) | **NO** — out of scope |
| 9 | Production ingestion / deployment / live NSE / credentials | **NO** — excluded by D07 §13-D and restated in §13 |

Architectural approval granted in this record does **not** authorize implementation; publication does not
authorize execution; I4 authorization does not authorize persistence; and none of them authorizes a
storage technology.

## 18. Carried-forward unresolved items (unchanged)

Nothing below was resolved, reinterpreted, weakened or normalized by this record; all remain as governed:

- **DEC-1** — deferred (eligibility predicate, ETF register join, master snapshots, delisting markers,
  corporate-action co-location).
- **W1-DIV-1** — D03-era ISIN check-digit census divergence vs the governed ISO-6166 routine; preserved,
  not reproduced, not altered; ISIN validity remains informational and non-gating.
- **Three unexplained calendar dates** (2024-11-20, 2025-10-20, 2026-01-15) and legacy-era
  `not-retrieved` labels — `official_holiday_label = null` with `label_status`
  `unexplained-by-obtained-circulars`; never filled in.
- **T0 / IT / SF / BE (rights vs T2T) / SGB-STK / `FinInstrmId` namespace / SME stage** — frozen; carried
  as governance-dependency annotations; fail-closed stubs intact.
- **XCONT continuity semantics** — mechanics resolved; policy and 83/122 residuals UNINTERPRETED; no
  durable artifact may assert continuity as fact.
- **D02 `row_offset` / `raw_row_hash`** — historical contract mismatch, explicitly recorded (§4), not
  adopted.

## 19. Final disposition

**D08 = RECORDED.** Authorized decisions MD-02, MD-03, MD-04, MD-05, MD-06, MD-07, MD-10, MD-11, MD-13,
MD-14 and MD-15 are recorded within the exact scopes stated; DOC-01 is applied as a narrow reference
correction; MD-08/MD-09 are deferred by sequencing; MD-12 is withheld; MD-16 is unchanged deferred;
MD-17 remains out of scope.

**Storage technology = UNDECIDED.** **I4 = AUTHORIZED / READY — NOT EXECUTED.** Content-level
traceability limitation in force (§4.3). W1/W2 implementation unchanged. Production not authorized.

**Durability:** publication to the designated branch `arena/9021d1a1-nse-historical-data-engine`, with
remote verification per §14. I3 closure (MD-15) is claimed only after that verification passes; the
verifying commit SHA is reported in the publication report for this gate.
