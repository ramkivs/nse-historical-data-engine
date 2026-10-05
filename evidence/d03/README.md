# D03 evidence — Arena-side partials and tool verification

Scope: D03 is an evidence-generation and semantic-investigation gate. The
corpus-dependent fixtures (FIX-SEM-DEF-01, FIX-UD-CENSUS-01, FIX-UD-ROW-SAMPLE-01,
FIX-LEG-CENSUS-01, FIX-XCONT-01, FIX-SYMBOL-HIST-01, FIX-SERIES-EVENTS-01,
FIX-OVERLAY-SEM-01, FIX-ANOM-01) execute on the Windows host against the raw
archives; their outputs will be committed here under `windows_run/` when the run
happens. This directory currently holds only what could be derived from evidence
already committed in this repository, plus tool-verification records.

| file | what it is | status |
|---|---|---|
| `d03_arena_evidence.py` | deterministic derivation (read-only on D01/D02 committed evidence; no clock, no corpus access) | reproduction: `python3 evidence/d03/d03_arena_evidence.py` |
| `FIX-UD-CENSUS-01_arena_header_verification.json` | header-width census over all 2,462 stored D01 header signatures (UDiFF 34 × 543 verified; Legacy 13-field variant = exactly 2 files) | COMPLETE (Arena-side component) |
| `FIX-CAL-01_arena_partial.json` | day-of-week structure of corpus + 147 missing weekday dates; holiday labels NOT assigned | PARTIAL (labels UNRESOLVED — needs official circulars) |
| `FIX-CIRC-01_arena_partial.json` | first/last sighting per series (era brackets for future circular dating) | PARTIAL (code meanings UNRESOLVED — needs circular archive) |
| `FIX-SECMASTER-01_scoping.json` | security-master acquisition scoping — NOT executed, authorization-gated | GATED |
| `D03_TOOL_SELFTTEST_output.txt` | full selftest run (`tools/d03_fixture_scan/d03_selftest.py`): 65/65 checks, synthetic data only | PASSED |

NOT corpus evidence: `D03_TOOL_SELFTTEST_output.txt` verifies tool behaviour on
hand-built synthetic archives; none of its numbers describe the real corpus.
