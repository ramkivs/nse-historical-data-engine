# D06 — Canonical Model Adoption Decision Record

Gate: D06 — decision recording + durable publication only. This record changes **no** code, schema,
corpus data, or prior finding. Style precedent: D04 §7 (gate-outcome record).
Recorded 2026-10-06 (Arena drafting; Windows publication route per standing durability process).

## 1. Purpose and scope

D06 presents the D05 canonical-model specification (`docs/specs/D05_CANONICAL_MODEL_SPEC.md`) for the
application decision authority's adoption decision, plus the accept/decline question for the optional
DEC-1 security-master acquisition branch. D06's output is this decision record and its publication;
nothing else. Out of scope by definition: engine implementation, corpus access, DEC-1 execution, and any
resolution of D05 OPEN/DEFERRED semantics.

## 2. Authority

Decision authority: **Ramki** (application decision authority for this project, per the standing
"later gated decisions" governance model recorded in README §Status and D04 §7).
Decision rendered and transmitted verbatim in the D06 execution prompt (2026-10-06).

## 3. Decision A — D05 §13 ADOPTED set = ACCEPTED / ADOPTED

The D05 §13 "ADOPTED (governs future implementations)" list is adopted as the **governed canonical-model
contract** of this repository. The adopted set, as enumerated in D05 §13:

1. layered provenance model (D05 §2);
2. field mapping & literal `legacy13`/`udiff34` schemas (D05 §3.1);
3. `SecurityIdentity` + dated associations as *structures* (D05 §3.2–3.3);
4. calendar derived from file-presence, circular labels only where sourced (D05 §3.4);
5. overlay observables + BL/IL disjointness recorded as evidence-backed (D05 §3.5);
6. non-gating validity flags — ISIN validity informational only, never gating (D05 §5);
7. opaque `FinInstrmId` + name-keyed parsing (D05 §6–§7);
8. CRLF/LF determinism conventions (D05 §9);
9. rupee scale with mandatory provenance note (D05 §10);
10. official-circular registry as annotation-only (D05 §11).

Adoption scope note: the D05 section tags (ADOPTED/DEFERRED/OPEN-SEMANTICS/NON-ASSUMPTION) remain part of
the contract; adoption of §13-ADOPTED **does not** promote any DEFERRED or OPEN item, and does not alter
evidence-support qualifiers (corpus-proven / evidence-backed / documented / sample-supported).

## 4. Decision B — DEC-1 master-acquisition branch = DEFERRED

DEC-1 (Windows acquisition of NSE Masters snapshots + `eq_etfseclist.csv`, corpus cross-consistency,
FIX-ETF-JOIN-02 join) is **DEFERRED**. **No Windows execution and no NSE master acquisition occurs under
D06.** `evidence/d04/DEC1_SECMASTER_FEASIBILITY.json` remains the standing feasibility record (including
its three-part authority test and "master is not assumed authoritative" rule) for any future gate that
reopens this question.

## 5. Effective authoritative baseline

- Repository: `https://github.com/ramkivs/nse-historical-data-engine.git`
- Authoritative ref: `origin/main`
- Baseline commit (adoption applies to exactly this content):
  `5585ccb0ebfe9aa3f3755c8b5eebfcdf8ddbf5bc` ("Publish D05 canonical model and investigation artifacts")

## 6. F1–F17 non-assumption register — carried forward UNCHANGED

All fifteen rows of D05 §12 remain [NON-ASSUMPTION] and binding: F1 ISIN not promoted to exchange-authoritative
identity; F2 FinInstrmId↔ISIN namespace not inferable; F3 undocumented series-transition semantics; F4 UDiFF
observed groups ≠ eligibility contract; F5 SYMBOL never durable identity; F6 units "as published", no in-file
units metadata; F7 overlay/orphan observation ≠ inclusion rule (T0 open); F8 legacy-era (2016–2023) holiday
labels never invented; F9 XCONT boundary residuals UNINTERPRETED; F10 ST-parallelism & determinism dispositions
closed, not reopened; F11 IT series definition FROZEN; F12 SF code OPEN; F13 BE rights-vs-T2T row-level split
OPEN; F14 SGB-STK documentation contradiction OPEN annotation-only; F15 ETF/EQ overlap counts DEFERRED;
F16 corporate-action symbol co-location not modeled (DEFERRED); F17 security-master authority DEFERRED
(no-assumption recorded). Adoption of §13 leaves every one of these exactly as stated in D05.

## 7. D05 §14 prohibitions — carried forward UNCHANGED

No code paths shipped by D05/D06; no writes to L0 (raw archive); no silent resolution of any [OPEN-SEMANTICS]
item; no promotion of inferred semantics into governed rules without new evidence appended to the registry;
no use of fixtures as production code; no re-scan of the raw corpus to "improve" D01/D03 metrics (frozen
facts); report reality exactly where task text and evidence diverge. These bind all future implementation.

## 8. D05 OPEN items — carried forward UNCHANGED (still OPEN)

1. T0 volume-inclusion semantics (237/237 lt consistent with both models; no official totals statement);
2. IT series definition/semantics (FROZEN, no authoritative text retrieved);
3. SF code (no official definition found; D04B/`DEC2_CIRC_MEANINGS.json`);
4. BE rights-entitlement vs T2T row-level split (heuristic evidence-only);
5. SGB-STK documentation contradiction (D02-era; OPEN);
6. XCONT `only_legacy_isins` 83 / `only_udiff_isins` 122 boundary residuals (UNINTERPRETED);
7. `FinInstrmId` namespace semantics (FROZEN opaque attribute);
8. three unexplained calendar gaps: 2024-11-20, 2025-10-20, 2026-01-15 (`DEC2_CAL_LABELS.json`);
9. SME surveillance-stage detail for the corpus era of ST↔SM (D04B §1).

## 9. D05 DEFERRED items — carried forward UNCHANGED (still DEFERRED)

1. eligibility predicate & ETF join (blocker: DEC-1 acquisition + consistency + acceptance — now additionally
   deferred by Decision B);
2. master-snapshot dated associations (same blocker);
3. legacy-era (2016–2023) calendar labels (needs 2016–2023 circular retrieval; explicitly "permitted to stay
   unresolved");
4. corpus-side implementation itself (pipeline authority NOT granted — separate later gate);
5. corporate-action symbol co-location semantics (not modeled).

## 10. Explicit no-execution statement

DEC-1 is DEFERRED (Decision B). Accordingly, under D06: no Windows environment was tasked, no NSE
download/acquisition was attempted or performed, no master file was joined, and no eligibility rule was
activated. The DEC-1 blockers recorded in `DEC1_SECMASTER_FEASIBILITY.json.acquisition_status` stand
unchanged.

## 11. Engine implementation status

**ENGINE IMPLEMENTATION IS NOT AUTHORIZED BY D06.**
Adoption of the canonical-model contract is a specification-governance act. Building the historical-data
engine (parser/normalizer pipeline execution over the corpus, schema creation in any environment, ingestion)
remains a **separate later authorization gate**. Nothing in this record grants it.

## 12. Evidence references supporting D06

- `docs/specs/D05_CANONICAL_MODEL_SPEC.md` @ 5585ccb (adopted contract text; §12–§15)
- `docs/investigations/D04_CANONICAL_MODEL_DECISION_INVESTIGATION.md` §7 (gate-outcome precedent; DEC-1..3 framing)
- `docs/investigations/D04B_DEC12_DOCUMENTATION_AND_MASTER_INVESTIGATION.md` §§1–4 (DEC-1/DEC-2 outcomes; recovery verification)
- `docs/investigations/D03_BOUNDED_FIXTURE_INVESTIGATION.md` §§15–16 and `evidence/d03/windows_run/` (frozen corpus evidence base, 39 files, determinism PASS)
- `evidence/d04/DEC2_CAL_LABELS.json`, `DEC2_Q7_UNIT_SCALE.json`, `DEC2_Q8_OVERLAY_AGG.json`, `DEC2_CIRC_MEANINGS.json` (upgraded evidence supports)
- `evidence/d04/DEC1_SECMASTER_FEASIBILITY.json` (DEFERRED-branch standing record)
- `docs/investigations/D02_EQUITY_ELIGIBILITY_AND_IDENTITY.md` + `evidence/identity/`, `evidence/inventory/` (D01/D02 baseline facts)
- D06 readiness investigation (this session's predecessor turn; full-tree D06 grep: single definition site at D05 §15) — findings reproduced in §§1–11 above

## 13. Final D06 disposition

**D06 = ACCEPTED / ADOPTED; DEC-1 = DEFERRED.**
Effective against `origin/main@5585ccb0ebfe9aa3f3755c8b5eebfcdf8ddbf5bc`. Engine implementation gate remains
closed and unstarted. Next stage begins only on explicit new authorization (no automatic commencement —
standing governance rule from D04 §7).

## 14. Publication record (fill by Windows operator)

- Applied from Arena transfer package (see package `TRANSFER_MANIFEST.json`), verified pre-image:
  `README.md` on main must equal the recorded preimage hash before update; `D06_*.md` is a NEW path.
- Commit: `<WINDOWS: record commit sha after step G>`
- Pushed to `origin/main` (or merge route), then MANDATORY remote verification:
  `git ls-remote origin refs/heads/main`; `git cat-file -e origin/main:docs/investigations/D06_CANONICAL_MODEL_ADOPTION_DECISION.md`.
- D06 is durable **only after** that remote verification passes; this file alone does not claim it.
