# D04B — DEC-1 / DEC-2 Investigation Record (official-documentation & security-master scoping)

Status: COMPLETE (investigation/evidence acquisition only). Produced 2026-10-06 (Arena side).
Downstream product: `docs/specs/D05_CANONICAL_MODEL_SPEC.md`.
Machine-readable evidence: `evidence/d04/DEC2_CAL_LABELS.json`, `DEC2_Q7_UNIT_SCALE.json`,
`DEC2_Q8_OVERLAY_AGG.json`, `DEC2_CIRC_MEANINGS.json`, `DEC1_SECMASTER_FEASIBILITY.json`,
`DEC12_CIRCULAR_REGISTRY.json` (deterministic: `python3 evidence/d04/d04_arena_synthesis.py`,
re-verified byte-identical on rerun this session).

Scope guard (per authorization): no implementation, no corpus mutation, no schema mutation; official
documentation was NOT silently converted into implementation rules — every spec-level use below is
tagged with its evidence basis; existing corpus evidence was not reinterpreted (documentation is
recorded ALONGSIDE it).

## 1. Official-document retrieval outcomes (DEC-2)

| Question | Outcome | Basis |
|---|---|---|
| Q3 series semantics | **UPGRADED**: EQ↔BE and SM↔ST round-trips (5,738/5,653 and 869/1,368 measured in D03) correspond to the officially documented surveillance movement "securities … shifted from Rolling Settlement (EQ/SM) to Trade-for-Trade (BE/ST)" (ESM/GSM frameworks; NSE/SURV/74008 consolidated circular incl. stage tables; NSE EMERGE page for SM/ST/SO). Residual transitions without a matching documented action remain **UNRESOLVED** — documentation explains the mechanism class, not every row. | registry `NSE/SURV/74008`, `NSE-EMERGE-PAGE`, `NSE-ESM-2026` |
| Q8 overlays | **UPGRADED for BL/IL**: recomputation from the PUBLISHED per-overlay evidence (3,692 rows) shows overlay qty > same-day normal-row qty for the same ISIN in 1,037/2,803 BL and 23/204 IL rows — inclusion in the normal row is arithmetically impossible for those rows; combined with official definitions (BL = block-deal window trades, market type N, NSE/CMTR/7864; IL = separate inter-institutional market segment, discontinued 2018-07-01 per NSE/CMTR/37880) and the official "number of trades = normal market only" field definition, the spec may state: **BL/IL overlay rows are disjoint-market additions** (evidence-backed). **BO**: buyback event rows (lt only). **T0**: 237/237 lt — consistent with both models; **stays OPEN**. | `DEC2_Q8_OVERLAY_AGG.json` + registry |
| CAL labels | For the UDiFF-era years with retrieved circulars: **29/32** missing weekdays match official notified holidays (2024-H2, 2025, 2026 incl. the F&O-published weekday set of the common 2026 notification); unexplained: 2024-11-20, 2025-10-20, 2026-01-15. **Both-direction divergences documented**: 2024-11-01 holiday w/o file vs **2025-10-21 holiday-per-circular WITH a normal-scale file (3,039 rows)** — special Muhurat session (NSE/FAOP/70320). Governance rule for D05: file-presence is the trading signal; circulars are labels. Legacy-era years (2016–2023, ~120 dates) remain unlabeled — deferred, not decision-relevant under the D03 stopping rule. | `DEC2_CAL_LABELS.json` |
| CIRC codes | IL/BL/ST/SO now documented (above). BE mainboard T2T usage documented; Rights-Entitlement dual use (2024 legend) retained as observed. **SF**: still no official definition found this session → OPEN. HA–HE: untouched (no corpus impact). IT: separate-market rows without normal counterparts (333 incl. 4 UDiFF orphans) — still **FROZEN** (no authoritative definition retrieved). | `DEC2_CIRC_MEANINGS.json` |
| Q7 units | **RESOLVED at rupee scale for the value fields** by test on published row samples: 1,589 testable rows across 4 fixture dates/both eras — zero lakh-scaled rows; value ≡ qty×close (within 2%) or explained VWAP≠close gaps; official field definitions corroborate ("rupee value", VWAP = field9/field8, trades exclude auction market). Files still embed no units metadata → provenance note remains mandatory in the spec. | `DEC2_Q7_UNIT_SCALE.json` |

## 2. Security-master feasibility (DEC-1)

- **Authority NOT assumed.** The official historical-dissemination document describes the NSE **Masters**
  database: monthly point-in-time snapshots (end of preceding month) with ISIN, Symbol, Series, Name,
  Deleted — historically the exchange's own security master, and an official statement that symbol+series
  was treated as the unique security key in that model.
- **Decisive small file**: `eq_etfseclist.csv` — official complete ETF register incl. ISIN numbers
  (schema verified incl. a real row `NIFTYBEES, 162, ISIN…`). ISIN-membership in this register would
  convert the "EQ minus ETFs" ambiguity into a join.
- **Acquisition blocked from this environment**: fetches returned HTTP 500 / TLS failures for the CSV and
  binary `.gz` paths; sandbox has no direct network egress for NSE downloads. The corpus-era acquisition
  path (Windows) remains the only verified route; it is **optional and not started**.
- **Feasibility answer**: a downloaded official master (Masters snapshots + ETF register) CAN establish
  historical identity/eligibility metadata (listing dates, series-at-month, ETF membership, delisting
  markers) at monthly granularity, with limitations: point-in-time-only (no intra-month events), possible
  non-availability for some legacy months until probed, and authority requiring the three checks recorded
  in `DEC1_SECMASTER_FEASIBILITY.json` (provenance capture, corpus cross-consistency, explicit user
  acceptance). Until then eligibility stays **DEFERRED**, not defaulted.

## 3. What D05 must carry forward unchanged

All D03 §8/§15 frozen dispositions remain frozen (FinInstrmId namespace, IT, eligibility contract,
legacy CAL labels, orphan interpretation, XCONT residuals, ISIN non-promotion, units provenance note);
the upgrades above change *evidence support level*, not corpus facts. Nothing here grants pipeline
implementation authority.

## 4. Post-reset repo recovery verification (same session)

Sandbox reset destroyed local commits again; tree state was intact on disk and re-committed
(`757df1b`, `e1a7a5b`), then merged with published `origin/main@094105b` (`-X ours`). Verification:
all 39 `windows_run` files are payload-identical to the published remote copies after CRLF→LF
normalization (39/39); the fixture `verify` tool's 10 raw-byte hash flags on JSON artifacts are the
known closed CRLF packaging variance (D03 §15), not content drift. No windows_run content changed.
