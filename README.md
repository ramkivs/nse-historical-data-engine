\# NSE Historical Data Engine



10-year NSE historical market-data engine for Legacy Bhavcopy and CM-UDiFF archives, with governed normalization, security identity, equity analytics, and historical query capabilities.



\## Environment Boundary



This project operates across three separate environments.



\### Windows



Windows is the raw-data custody and full-dataset execution environment.



It has access to the local NSE historical archives:



\- `C:\\IIPS\_Data\\NSE\_Legacy\_Acquisition\\archives`

\- `C:\\IIPS\_Data\\NSE\_CM\_UDiFF\_10Y\\archives`



Windows is responsible for:



\- Raw archive custody

\- Full-dataset inventory and profiling

\- Full-dataset processing when required

\- Generation of evidence artifacts and controlled data extracts



\### GitHub



GitHub is the authoritative durable project record.



It contains:



\- Evidence artifacts

\- Specifications

\- Architecture and design decisions

\- Source-code

\- Tests

\- Development documentation

\- Controlled fixtures and extracts



The raw NSE archive files are not stored in this repository.



\### Arena



Arena is the investigation and development environment.



Arena does not have direct access to the Windows filesystem or the raw NSE archives.



Arena receives data and evidence through the Git repository and other explicitly controlled artifacts.



Arena is responsible for:



\- Read-only investigation

\- Architecture and specification development

\- Engine development

\- Automated testing

\- Documentation

\- Durable publication through Git



\### Raw NSE Archives



The raw NSE archives remain outside Git.



They are treated as source data and must not be modified by the engine development workflow.



\## Current Evidence Baseline



The initial archive inventory established:



\- Total files: 2,462

\- Legacy files: 1,919

\- UDiFF files: 543

\- Inventory errors: 0

\- Duplicate dates: 0

\- Duplicate checksums: 0

\- Schema variants: 3

\- Coverage: 2016-09-20 through 2026-09-18



The inventory was generated read-only.



\## Development Principle



The project follows a controlled evidence-to-development workflow:



Windows raw archives

→ evidence / controlled extracts

→ GitHub authoritative repository

→ Arena investigation and development

→ GitHub durable publication



No environment should assume direct filesystem access to another environment.



\## Status



Current stage:



\*\*D01 evidence baseline complete; D02 identity/eligibility investigation complete; D03 COMPLETE — Windows corpus execution published (evidence/d03/windows_run @ origin/main 094105b, 39 files, determinism PASS, post-run reconciliation in D03 record §15); D04 canonical-model decision investigation record committed; DEC-1/DEC-2 documented (D04B record + evidence/d04/); D05 CANONICAL MODEL SPECIFICATION authored (docs/specs/D05_CANONICAL_MODEL_SPEC.md); D06 DECISION RECORDED — D05 §13 ADOPTED set ADOPTED as governed canonical-model contract, DEC-1 master acquisition DEFERRED, ENGINE IMPLEMENTATION NOT AUTHORIZED (docs/investigations/D06_CANONICAL_MODEL_ADOPTION_DECISION.md); D07 CHARTER + IMPLEMENTATION AUTHORIZATION RECORDED — engine implementation AUTHORIZED within D07 scope (non-production), DEC-1 remains DEFERRED, D7.4 pointer restatement + D7.5 backfill applied (docs/investigations/D07_GATE_DEFINITION_AND_IMPLEMENTATION_AUTHORIZATION.md) — implementation proceeds only after D07 record is durable and remote-verified.\*\*



- D02 investigation record: `docs/investigations/D02_EQUITY_ELIGIBILITY_AND_IDENTITY.md`
- D02 derived evidence artifacts: `evidence/identity/` (regenerate read-only with `python3 evidence/identity/d02_derivation.py`)
- D03 investigation record: `docs/investigations/D03_BOUNDED_FIXTURE_INVESTIGATION.md`
- D03 fixture tool (read-only, deterministic, selftested): `tools/d03_fixture_scan/` — Windows runbook in D03 record §12
- D03 Arena-side partial evidence: `evidence/d03/` (regenerate read-only with `python3 evidence/d03/d03_arena_evidence.py`)
- D03 Windows run evidence (durable on main): `evidence/d03/windows_run/` (RUN_INFO + MANIFEST; verify: `python tools/d03_fixture_scan/d03_fixtures.py verify --out evidence/d03/windows_run` — see D03 §15 CRLF packaging note)
- D04 investigation record (decision inputs only; no schema adopted): `docs/investigations/D04_CANONICAL_MODEL_DECISION_INVESTIGATION.md`
- D04B DEC-1/DEC-2 investigation record (official documentation + security-master scoping): `docs/investigations/D04B_DEC12_DOCUMENTATION_AND_MASTER_INVESTIGATION.md`; machine-readable evidence `evidence/d04/` (deterministic: `python3 evidence/d04/d04_arena_synthesis.py`)
- D05 canonical model specification (specification-only; ADOPTED/DEFERRED/OPEN/NON-ASSUMPTION tagged): `docs/specs/D05_CANONICAL_MODEL_SPEC.md`
- D06 canonical-model adoption decision record (D06 = ACCEPTED/ADOPTED; DEC-1 = DEFERRED; engine gate closed): `docs/investigations/D06_CANONICAL_MODEL_ADOPTION_DECISION.md`
- D07 gate charter + implementation authorization record (D07 decisions 1-4; pointer restatement D7.4; D06 §14 backfill D7.5; scope boundary §13; first work item W1 §14): `docs/investigations/D07_GATE_DEFINITION_AND_IMPLEMENTATION_AUTHORIZATION.md`



Canonical model finalized via D06 (§13-ADOPTED; F1–F17 and all OPEN/DEFERRED items carried forward unchanged). Equity eligibility governance and security-master scoping remain DEFERRED (D06 Decision B); engine implementation was authorized at gate D07 within its explicit scope (non-production; fail-closed on OPEN semantics) — see `docs/investigations/D07_GATE_DEFINITION_AND_IMPLEMENTATION_AUTHORIZATION.md`. D02 recommends D03 proceed as a fixtures-and-decisions gate against the Windows-side fixture requests in the D02 record (section 9).

