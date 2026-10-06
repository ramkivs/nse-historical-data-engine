# D07 — Post-D06 Gate Definition & Implementation Authorization

Gate: D07 — governance closure + explicit implementation authorization. Style precedent: D04 §7 / D06.
Recorded 2026-10-06. Publication baseline lineage: `origin/main@5d7e9425aa5fd80f7ec580c91afad727f9323b90`.

## 1. D07 identity and charter

D07 is formally chartered as: **D07 — Post-D06 Gate Definition & Authorization Decision**. It is the
governance gate immediately following D06. Prior to this record the repository did not define D07
(the D07 read-only investigation established `D07 DEFINITION INCOMPLETE (repository-silent)` via
full-tree grep at `5d7e9425`: token `D07` occurred only inside data strings, e.g. `INE583D07257`).
This record closes that gap by charter decision, not by inference.

## 2. Relationship to D06

D06 (durable; `docs/investigations/D06_CANONICAL_MODEL_ADOPTION_DECISION.md`) established the adopted
canonical-model contract and closed with: "Next stage begins only on explicit new authorization".
D07 IS that explicit new authorization, rendered by the application decision authority. D07 consumes
the D06 contract **unchanged** except where §§5–7 below state supersession precisely.

## 3. The repository-silent finding (recorded, not erased)

At `5d7e9425` no D07 definition existed. The finding stands as the reason this charter record exists;
it is a governance-process observation, not a data or model issue.

## 4. Ramki decisions (verbatim authority: application decision authority, 2026-10-06)

| # | Decision | Outcome |
|---|---|---|
| 1 | D07 charter | **ACCEPT** — gate chartered as "D07 — Post-D06 Gate Definition & Authorization Decision" |
| 2 | Engine implementation | **AUTHORIZED within D07 scope** (§§8–9 below). Per the decision text: the D06 statement `ENGINE IMPLEMENTATION IS NOT AUTHORIZED BY D06.` is **superseded for the scope established by D07** and no longer prohibits implementation within that scope |
| 3 | D7.4 pointer restatement | **ACCEPT** — governed restatement per §6; historical provenance preserved |
| 4 | D7.5 backfill | **ACCEPT** — D06 §14 placeholder filled with `5d7e9425aa5fd80f7ec580c91afad727f9323b90` |

## 5. Inherited D06 contract (unchanged)

The D05 §13 ten-item adopted set remains the governed canonical-model contract (layered provenance;
field mapping & literal schemas; SecurityIdentity + dated associations; calendar-from-file-presence with
circular labels where sourced; overlay observables with BL/IL disjointness evidence-backed; non-gating
validity flags; opaque FinInstrmId + name-key parsing; CRLF/LF determinism; rupee scale + provenance
note; circular registry as annotation). Adoption status: ADOPTED (D06 Decision A), reaffirmed here.

## 6. F1–F17 non-assumption register — unchanged

Every F1–F17 row of D05 §12 carries forward with identical force after implementation authorization.
Implementation authority **never** promotes a non-assumption into a rule: where the engine needs a
frozen/OPEN semantic, it MUST fail closed with an explicit governance dependency (D07 prompt §4 principle,
adopted here as a governed implementation rule).

## 7. D05 §14 prohibitions — remaining applicable

All §14 prohibitions survive D07 EXCEPT the single supersession stated in Decision 2:
- NO writes to L0 (raw archive) — unchanged, absolute.
- NO silent resolution of any [OPEN-SEMANTICS] item — unchanged; fail-closed handling required (§9).
- NO promotion of inferred semantics without new evidence — unchanged.
- NO use of fixtures as production code — unchanged in sense: published fixtures remain evidence; the
  engine is implemented as repository code per §8, importing D05 contracts, not fixture internals.
- NO corpus re-scan to "improve" D01/D03 metrics — unchanged; frozen facts stay frozen.
- Report reality on divergence — unchanged.
Superseded only by: implementation of the engine (code paths building canonical records from corpus
inputs under D05/D06 contract) is now authorized, NON-PRODUCTION only (§9).

## 8. DEC-1 status

**DEC-1 MASTER ACQUISITION REMAINS DEFERRED.** D07 does not authorize DEC-1 acquisition, master joins,
NSE live endpoints, production credentials, or production ingestion (§9 exclusions). Implementation must
proceed on repository-held evidence and synthetic/deterministic material; if a task becomes technically
unavoidable without an external master, STOP and flag it as a separate authorization dependency.

## 9. Nine unresolved canonical semantics — carried forward OPEN

Implementation authorization does NOT close any of: (1) T0 volume-inclusion; (2) IT definition/semantics;
(3) SF code; (4) BE rights-entitlement vs T2T row-level split; (5) SGB-STK contradiction; (6) XCONT
83/122 boundary residuals; (7) FinInstrmId namespace; (8) 3 unexplained calendar dates (2024-11-20,
2025-10-20, 2026-01-15); (9) SME surveillance-stage detail for the corpus era. Engine behavior at each:
represent the observable, carry the flag/annotation, and FAIL CLOSED (no default) where a semantic
decision would be required to proceed.

## 10. D7.4 pointer reconciliation (governed restatement)

Classification of every stale-pointer occurrence at `5d7e9425` (per D07 prompt §6 — no blind replacement):

| Occurrence | Type | Action | Rationale |
|---|---|---|---|
| README L189 `windows_run @ origin/main 094105b` | historical evidence pointer | KEPT | records the actual publication event of D03 evidence |
| D02 L10 `Baseline: origin/main @ 410135d (D01)` | baseline-at-time declaration | KEPT | historically accurate for D02's issuance |
| D03 L4 `durable on origin/main@094105b` | durability claim (lineage-level) | NOTE ADDED | content still durable; lineage restated by D07 note block (D03 §17) |
| D03 L198, L252; D04B L54; D04 L11/L22; D06 L113 | provenance narratives / negative-search records | KEPT | historical accuracy required; no current-authority claim |
| D06 L54 (§5 "Effective authoritative baseline: 5585ccb…") | current-authoritative baseline declaration | RESTATED (amendment line appended, original preserved) | `5585ccb` unreachable in current lineage after squash republication; misleading as a current claim |
| D06 L125 (§13 "Effective against origin/main@5585ccb…") | current-authoritative effectivity | RESTATED (amendment line) | same |
| D06 §14 placeholder `<WINDOWS: record commit sha after step G>` | publication bookkeeping | BACKFILLED (D7.5) | decision 4 |

Governance explanation (recorded once, referenced everywhere): the Windows publication of D06 produced
the CURRENT authoritative `main` lineage as a **root/squash commit** (`5d7e9425`, commit count 1); the
earlier linear history (`410135d → 094105b → 5585ccb`) is no longer reachable from `main`, but full
content identity was verified byte-exact across all 79 tracked files at D07 Phase 1 (zero `DIFFERS`).
Therefore historical pointers stay true to their events; only "effective/authoritative-baseline NOW"
phrasing is amended, by dated amendment note, never by rewriting history.

## 11. D7.5 backfill

D06 §14 now records the Windows publication commit `5d7e9425aa5fd80f7ec580c91afad727f9323b90`, with the
verification basis stated precisely (see D06 §14 amended text).

## 12. Explicit implementation authorization

Engine implementation is AUTHORIZED within this record's scope: repository code, deterministic
parse→canonicalize pipeline per D05 §3 field tables, flags, calendar, overlay observables, tests on
published fixtures + synthetic inputs. This sentence is the authorization event; nothing before it in
the durable record authorized code.

## 13. Exact implementation scope (boundary assessment, D07 prompt §8 A–H)

**A. Implementable now (evidence-complete):** legacy13 + udiff34 parsers (name-keyed, §7 tolerances incl.
trailing-empty header field and DD-Mon-YY|YYYY timestamps; fail-closed width ≠ 34); canonical `SecurityRow`
builder with full provenance block (D05 §8); validity flags (all §5 flags, non-gating); calendar derivation
(file-presence primary + sourced labels); `OverlayObservation` linking incl. `qty_rel`/orphan flags; dated
`DatedAssociation(corpus-observed)` construction; D01 distinct-nonblank metric re-computation; determinism
harness honoring D05 §9 (LF artifacts, dual-hash, run-metadata exclusion); test suites over
`evidence/d03/windows_run/` published fixtures + synthetic rows.
**B. Blocked by OPEN semantics (fail-closed in code):** any T0 aggregate rule; BE rights-vs-T2T row
classification; IT/SF interpretation; XCONT boundary continuity POLICY (match storage only); SME-stage
annotation completeness; the 3 CAL dates (flag only).
**C. Blocked by DEC-1 (DEFERRED):** eligibility predicate; ETF-exclusion join; master-snapshot dated
associations; delisting markers; corporate-action co-location.
**D. Explicitly out of scope:** production deployment/ingestion; live NSE access; credentials; persistence
to any production store; corpus mutation; provider integrations (incl. any Dhan path — zero references in
this repository).
**E. Tests/fixtures:** unit + golden tests derived ONLY from published fixture evidence and synthetic
corpus-shaped inputs; fixture tools stay evidence-only (no import); property tests for header/timestamp
tolerance and flag non-gating.
**F. Determinism:** byte-identical reruns except declared run-metadata; hash-pinned inputs; D05 §9 rules
normative.
**G. Provenance:** every output record carries D05 §8 provenance; unresolved-semantic outputs carry the
governance-dependency ID from §9 list.
**H. Acceptance criteria (gate-I1):** parser acceptance on all 39 published windows_run artifacts +
synthetic edge-cases; zero semantic defaults; flag semantics exactly D05 §5; golden metric reproduction
(D01 definitions); determinism double-run PASS; no new dependencies on raw archives in tests beyond
repository-held evidence.

## 14. First implementation work item (after this record is durable)

**W1 — Reference parser + canonical row builder (both families), repository path `src/nse_engine/`**
(implementation begins only when this D07 record is verified on `origin/main`).
Prereqs: this record durable (§15); evidence bundle `evidence/d03/windows_run/` present (it is).
Scope: §13-A items for parse/row-build/flags/provenance + their tests; fail-closed stubs naming each
§13-B/C dependency. Acceptance: gate-I1 subset applied to W1; non-production boundary observed (§9-D).

## 15. Next gate after D07

**GATE-I1 — Engine Implementation, Increment 1 (W1 acceptance review).** Type: implementation +
validation review under existing D07 authority (no new authorization needed for §13-A work; new
authorization IS required for anything in §13-B/C/D). Ramki decision needed before: W1 durable
publication route, any DEC-1 reopening, any semantic closure.

## 16. Final D07 disposition

**D07 = CLOSED / DURABLE ONLY AFTER remote verification of this record; as of drafting: recorded,
validated, pending publication** (Arena transport to GitHub is closed — see D07 final report).
No automatic commencement into W1 until this record is remote-verified (D07 prompt §14).
