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



\*\*D01 evidence baseline complete; D02 read-only equity eligibility & identity investigation complete (investigation record only — no implementation authority).\*\*



- D02 investigation record: `docs/investigations/D02_EQUITY_ELIGIBILITY_AND_IDENTITY.md`
- D02 derived evidence artifacts: `evidence/identity/` (regenerate read-only with `python3 evidence/identity/d02_derivation.py`)



Equity eligibility governance, security-master scoping, canonical model finalization, and engine implementation remain subject to later gated decisions. D02 recommends D03 proceed as a fixtures-and-decisions gate against the Windows-side fixture requests in the D02 record (section 9).

