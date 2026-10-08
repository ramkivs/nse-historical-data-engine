# G-I4-M2 monitor — Windows process-launch argument-boundary correction

**Scope:** corrective revision of the Windows execution wrapper ONLY. No engine byte, no
`i4_runner.py` byte, no memory threshold, no guard and no output/persistence contract changed. No
corpus execution occurred in Arena. The failed Windows attempt is preserved and was not touched.

| Item | Value |
| --- | --- |
| Repository | `ramkivs/nse-historical-data-engine` |
| Base revision for this correction | `8ade8372e150e541a52206baa377a02249a308f4` (tree `8e1557de…`) |
| Corrected file | `tools/i4_m2/I4_M2_MEMORY_MONITOR.ps1` |
| Monitor SHA-256 before | `d572e30e33c0cea16d160d4473e7adc87b964e2f86b2c1a437130f0f6204b23c` (14,208 B) |
| Monitor SHA-256 after | `7ef9db125c3e25135ab51c251b7cc46b38da33a329949ac2fbcd1a171dc78f00` |
| Windows proof script | `tools/i4_m2/I4_M2_TEST_LAUNCH_QUOTING.ps1` |
| Resulting commit / tree / package hashes | recorded in the package's `EVIDENCE_I4_M2_MONITOR_FIX.json` and `I4_M2_PACKAGE_BUILD_INFO.json` |

## 1. The defect

The monitor launched the runner with an ARRAY argument list:

```powershell
$proc = Start-Process -FilePath $PythonExe -ArgumentList $argList -WorkingDirectory $RepoRoot -PassThru `
  -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
```

`Start-Process -ArgumentList` with an array joins the elements with single spaces and performs **no
quoting**, so the child command line contained `... --legacy-root G:\My Engines\... ...` and the
space inside `My Engines` split those values into fragments. On Windows this produced:

* runner exit code `2`, stdout empty;
* stderr: `i4_runner: error: unrecognized arguments: Engines\10yhistoriclengine\evidence\inventory\file_inventory.json
  Engines\10yhistoriclengine\evidence\d04\DEC2_CAL_LABELS.json Engines\10yhistoriclengine\evidence\d03\windows_run\FIX-SEM-DEF-01__metrics.csv
  Engines\10yhistoriclengine\evidence\d03\windows_run\FIX-SEM-DEF-01__d01_definition_verdict.json Engines\I4_RUNS\i4-20261008`;
* output root `G:\My Engines\I4_RUNS\i4-20261008` never created; no member processed; no threshold
  breached. The monitor's pre-execution checks all passed — the failure was purely at the launch
  boundary.

Evidence (preserved, read-only): `M2_MEMORY_MONITOR_i4-20261008.baseline.json`,
`M2_MEMORY_MONITOR_i4-20261008.summary.json`, `M2_MEMORY_MONITOR_i4-20261008.runner.stderr.txt`.

## 2. The correction

Each element of the existing argument list is now encoded with the documented Windows command-line
quoting rule (MS C runtime / `CommandLineToArgvW`): wrap the value in double quotes, double any
backslash run standing before a quote, and double trailing backslashes so they cannot escape the
closing quote. The encoded elements are joined into ONE command-line string, which is what
`CreateProcess` actually consumes:

```powershell
$quotedArgs = @()
foreach ($item in $argList) { $quotedArgs += (ConvertTo-ProcessArgument -Value ([string]$item)) }
$startArgs = $quotedArgs -join " "
Write-Host ("runner command: " + $PythonExe + " " + $startArgs)
$proc = Start-Process -FilePath $PythonExe -ArgumentList $startArgs -WorkingDirectory $RepoRoot -PassThru `
  -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
```

`ConvertTo-ProcessArgument` is defined in the monitor between the marker comments
`# >>> I4_M2_ARG_QUOTING_BEGIN` / `# <<< I4_M2_ARG_QUOTING_END`, so the Windows self-test can
extract and execute the real function from the real file. Trailing backslashes are handled (a naive
`'"' + $value + '"'` would lose them), and embedded quotes are escaped.

Why not `ProcessStartInfo.ArgumentList`? That property (which handles quoting itself) exists only in
PowerShell 7 / .NET (Core); these wrappers target Windows PowerShell 5.1, where it does not exist.
The explicit quoted string is the portable, correct form for 5.1.

**Exactly what changed, byte-level:** two regions — the inserted `ConvertTo-ProcessArgument`
function (39 lines, with its marker comments) and the launch block (2 lines replaced by 5). A
reverse-surgery check removed the inserted block and restored the two original lines and reproduced
the pre-correction file **byte-for-byte**, which proves no other byte moved. Everything else is
unchanged, including: every pre-execution guard, the declared/threshold semantics
(`-RssLimitMB`, `-AvailableFloorMB`, `-MinFreeBytes`, the 2.5 GB retained-envelope acceptance value),
the RSS / available-memory / free-disk sampling loops, the fail-closed breach kill, the
stdout/stderr redirection, the working directory, the process monitoring, the completion/failure
handling, and the full runner argument vector (all 28 elements, verbatim).

## 3. Verification performed in Arena (no corpus, no Windows execution)

| Check | Result |
| --- | --- |
| Reverse surgery: removing the two changed regions reproduces the previous file byte-for-byte | PASS |
| PowerShell syntax validation (tree-sitter-powershell grammar parse; the only raw error nodes are the grammar's unsupported `1GB`/`1MB` numeric-multiplier literals, identical in the pre-correction file) | 0 errors after that documented substitution; corrected file adds none |
| Quoting algorithm round-trip against a reference implementation of the MS C runtime splitting rules, on the exact evidence paths plus 320 edge/random cases | PASS |
| Same cases through `subprocess.list2cmdline` (CPython's implementation of those rules) — encoder semantics identical | PASS |
| End-to-end: encode → decode → real child process; child reports exactly the intended 28-element vector; no fragment split at `My Engines` | PASS |
| New test module (`tests/test_i4_m2_monitor_launch.py`) — guards, thresholds, vector and algorithm | 19 tests OK |
| Full test suite | see the package evidence JSON (count recorded there) |
| compileall | clean |
| Engine / runner fingerprints unchanged | `d3269b73…` / `f3ebf624…` |
| Corpus execution in Arena | **none** (no corpus path is opened by any test; the vector uses stand-in paths) |

What only Windows can prove: that the real PowerShell function feeding the real `Start-Process`
preserves boundaries. That is exactly what the self-test does (below), and the Python test pins the
self-test's monitor hash so the two cannot drift apart silently.

## 4. Apply and test on Windows

1. Take the corrected package (v2). It carries `scripts\I4_M2_MEMORY_MONITOR.ps1` (corrected),
   `scripts\I4_M2_TEST_LAUNCH_QUOTING.ps1`, `tools\I4_M2_MEMORY_MONITOR.ps1` and the evidence JSON.
   Verify the tarball's SHA-256 against its sidecar first.
2. Run the self-test **before** any further execution attempt:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\I4_M2_TEST_LAUNCH_QUOTING.ps1
```

   It must print `I4 M2 LAUNCH QUOTING SELF-TEST = PASS`. It checks the monitor SHA-256 against the
   published pin, extracts the real function, drives 10 synthetic cases through `Start-Process`
   (including both `G:\My Engines\...` paths from the failure, a trailing-backslash path, embedded
   quotes, an empty value, a non-ASCII path and the full 28-element vector), and reads back what the
   child actually received. Any other printed result is a fail-closed stop — report it, do not edit.

3. Re-run the monitor. Two things change **only** in how you invoke it:

   * the run id stays **`i4-20261008`** — a validation failure is not a reason to mint a second run
     id, and the output root `G:\My Engines\I4_RUNS\i4-20261008` was never created, so it is still
     fresh;
   * pass a **new `-EvidencePrefix`** (for example `..._i4-20261008_R2`). The monitor refuses to
     reuse an existing evidence prefix, and the failed attempt's evidence
     (`M2_MEMORY_MONITOR_i4-20261008.*`) must stay exactly as it is. Nothing else about the
     invocation changes.

## 5. Standing statements

* The 2,462-member corpus was **NOT executed in Arena**; no member was processed during this
  correction.
* The failed attempt (`G:\My Engines\I4_RUNS\i4-20261008` and its sibling monitor-evidence files) is
  preserved evidence: not touched, not repaired, not appended to, not reused as an output root.
* `main` remains `6a60583f…`; this correction is not merged into it. No production authorisation.
* A successful rerun would still not authorise production, and storage technology remains
  undecided.
