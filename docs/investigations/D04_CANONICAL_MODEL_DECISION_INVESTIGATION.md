# D04 — Canonical Model Decision Investigation (read-only)

Gate: D04 — investigation/decision-support only. **No implementation authority. Nothing in this record is
a schema contract, migration, or pipeline decision; all model elements remain PROPOSALS carried from D02
and constrained by D03.** Companion records: D02 (eligibility & identity investigation), D03
(§15 post-run reconciliation — the authoritative evidence base for everything below).

## 0. Scope determination (basis recorded, not invented)

The repository contains **no standalone D04 specification or handoff record** (verified by full-tree
search of `origin/main@094105b` and the arena branch: the only D04 references are D03 §10–§11/§15 and the
README status text). The authoritative D04 objective is therefore taken verbatim from what the repo
defines for the next gate:

1. README (`## Status` closing line): "**Equity eligibility governance, security-master scoping,
   canonical model finalization, and engine implementation remain subject to later gated decisions.**"
2. D03 §11/§15: "D04 must treat every §8 FROZEN row as a standing governance constraint";
   readiness = READY-for-investigation-in-Arena after the published Windows run.

⇒ D04 objective executed here: **consolidate the published D03 evidence into decision inputs for
canonical-model finalization and eligibility governance — without deciding them.** Selection basis:
unique repository definition; no competing D04 references exist (git history: `094105b` evidence commit is
the current `origin/main` tip; investigation records live only on
`arena/01a10c83-nse-historical-data-engine` — recorded in §6).

## 1. Evidence inputs (all durable, no raw-corpus access used or needed)

`evidence/d03/windows_run/*` (39 files, `094105b`), D02 `evidence/identity/*`, D01
`evidence/inventory/*`. D03 §15 is the interpretation record. Corpus: 2,462 archives, 5,689,949 rows,
2016-09-20…2026-09-18, Legacy→UDiFF boundary 2024-07-05/08.

## 2. Identity resolution — decision inputs (status: PROPOSED, evidence-supported, not adopted)

| Element | Evidence support (D03 §15) | Status / boundary |
|---|---|---|
| `security_id` durable internal key | ISIN present on 100% of rows (both formats, zero blanks); 7,633 distinct ISINs tracked; but 215,393 Legacy rows fail ISO-6166 Luhn and 205 boundary one-sided ISINs are uninterpreted | **proposed**: ISIN-derived resolution remains viable as candidate *only with* informational validity flag; final resolution strategy (incl. whether a surrogate is needed alongside ISIN) is a D05-stage decision under user authority |
| `isin_validity_flag` | INVALID_CHECKDIGIT ≈5.4% of Legacy rows; INVALID_LEN=1; corpus-proven real ISINs fail Luhn | **evidence-backed constraint**: flag must never gate row acceptance or identity |
| `FinInstrmId` (UDiFF) | never equals ISIN (1,700,650/1,700,650 differ); short-numeric format; no blank | attribute (proposed); its namespace semantics (exchange security id?) documentation-gated — **must not be assumed** |
| symbol / series as dated attributes | 845 multi-symbol ISINs; 2,431 multi-series; EQ↔BE round-trips; transitions dated in fixtures | supports time-varying (symbol, series) association tables; **identity must not key on either** |
| legacy-era segment scoping | UDiFF Sgmt=CM, Src=NSE singletons; Legacy none | corpus-consistent segment claim; formal eligibility rules still blocked on Q1-ETF item (§3) |

## 3. Equity eligibility governance — unresolved with exact blockers (no rule may be adopted yet)

- `SERIES==EQ` admits ETFs and (per legend) rolling variants — row-level reconfirmed (1,188,443 EQ rows /
  3,078 ISINs, ETF-hint tickers inside).
- `FinInstrmTp==STK` is useless as an equity filter here (**all** rows STK, incl. debt/MF).
- ETF/rights disambiguation inside EQ/BE requires either (a) the security master — **GATED** by user
  authorization (D03 FIX-SECMASTER-01 scoping) — or (b) an in-corpus membership list the user supplies.
- BE dual use (T2T state vs Rights Entitlement) has no in-corpus discriminator proven; EQ↔BE round-trips
  support "state-change" rows; RE-symbol heuristics remain evidence-only.
⇒ Eligibility governance is **DEFERRED pending one user decision** (master authorization vs corpus-only
rule set). D04 explicitly does not pick.

## 4. Standing constraints carried forward (from D03, unchanged in force)

1. Q7 units "as published"; any unit-dependent analytic must state assumptions.
2. Q8 overlay volume inclusion: neither add nor drop as *security-level* aggregate without documentation;
   overlay rows are same-ISIN state/window rows in 3,356/3,692 observed cases; 336 orphans (mostly IT).
3. CAL: weekday-file model only; no holiday labels without official circulars (fetching them is an
   authorized-documentation decision, not Arena work).
4. CIRC: no retroactive legend; era-bracket semantics only.
5. Q3: series transition ≠ proven same-or-new security semantically.
6. Header/timestamp variance (2017-07-10, 2020-07-13) must be tolerated, not "fixed".
7. Determinism contracts (frozen-time, manifest, CRLF-vs-LF packaging note) apply to all future tooling.
8. Fixtures/selftests are evidence artifacts — never production code imports.

## 5. What D04 did NOT do (boundary record)

No schema adoption, no parser implementation, no storage design, no pipeline, no security-master
acquisition, no new corpus scan, no re-run of fixtures (not required: verification of published evidence
passed 37/37 from git content). No unresolved semantic question was silently resolved; every FROZEN
D03 row stayed frozen.

## 6. Durable-artifact state

D03 evidence: durable on `origin/main@094105b`. D02/D03/D04 records + tooling: committed on
`arena/01a10c83-nse-historical-data-engine`; Arena session push capability is reported per session
(closed sessions cannot push) — if the branch push is not observable on the remote, the operator replays
this branch from the transfer package as done for D03 (procedure proven).

## 7. Gate outcome

D04 investigation outcome = **decision-ready inputs complete; three explicit user decisions unblock
progress**:
- **DEC-1**: authorize (or decline) security-master acquisition for eligibility disambiguation;
- **DEC-2**: calendar/circular documentation retrieval — authorized fetch vs deferred vs out-of-scope;
- **DEC-3**: whether D05 (specification of canonical schema + parser + governance rules) may open,
  under the standing constraint list §4.
Next gate after this record: **user decisions DEC-1..3**, then D05 as a *specification* gate (still not
implementation). No automatic commencement.
