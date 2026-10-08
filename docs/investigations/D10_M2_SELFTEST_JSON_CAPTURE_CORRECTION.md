# D10 — G-I4-M2 launch-quoting self-test: JSON array-capture correction

**Status:** corrective revision committed in the repository and remotely verified.
**Gate:** G-I4-M2 (unchanged: corpus execution still not performed).
**Scope of this revision:** the launch-quoting self-test ONLY. No engine, no `i4_runner.py`, no
monitor, no threshold, no corpus contract, no output contract, no execution semantics.

| Item | Value |
| --- | --- |
| Repository | `ramkivs/nse-historical-data-engine` |
| Branch | `arena/9021d1a1-nse-historical-data-engine` |
| Corrective commit (self-test + regression test) | `43f233bc6b0eaf42c98294325b84b2f6eee323cc` |
| Tree of that commit | `3395226aea551cd8404479eda470c723cfb9b1f3` |
| Parent | `818c128c82f102324f28d5abbe3c058f7ef88f9e` |
| `main` | `6a60583f62905c1fbda9cc7529019e2a9ed0b097` — not modified, not merged |
| Authoritative M2 corrective monitor | `tools/i4_m2/I4_M2_MEMORY_MONITOR.ps1` = sha256 `7ef9db125c3e25135ab51c251b7cc46b38da33a329949ac2fbcd1a171dc78f00` |
| Self-test before | sha256 `b402f77fba93de1da7e9266a8d1fffd7431e74bed7efa208242460cab0a4ac19`, 10,410 B |
| Self-test after | sha256 `4986b1fbe5cb054062cadb8eee1c75b4bc46f13f7634033f6fd04601a3ae74e4`, 10,434 B |
| Engine fingerprint | `d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9` (unchanged) |
| Runner fingerprint | `f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a` (unchanged) |
| Corpus execution | **NOT PERFORMED** (nothing was executed in Arena; the 2,462-member corpus was not started) |

## 1. The defect (packaged self-test only)

`scripts/I4_M2_TEST_LAUNCH_QUOTING.ps1` read the argv probe's JSON output and captured it as:

```powershell
$got = @(ConvertFrom-Json $rawJson)
```

On Windows PowerShell 5.1, `ConvertFrom-Json` hands a deserialized JSON **array** back as a single
object, so `@(...)` wrapped it in a one-element array whose only element is the whole array. The
self-test's comparison then evaluates `$got.Count -ne $expect.Count` as `1` versus the expected
argument count, and every case reports FAIL — even though the child process received the arguments
correctly. The defect is entirely in the test's result-capture layer; it cannot affect the monitor.

## 2. Windows observed failure

Running the packaged self-test against the governed monitor on Windows produced no case verdict of
PASS; the failure came from the JSON capture above, not from the launch boundary. The monitor's own
quoting function had already preserved every tested boundary.

## 3. Temporary, non-governed corrected test (evidence)

A temporary copy of the self-test was corrected **only** at the JSON capture layer:

```powershell
$got = @(ConvertFrom-Json $rawJson | ForEach-Object { $_ })
```

Run on Windows against the governed monitor (`7ef9db12…`, sha observed on Windows), that temporary
copy reported:

```
C1_inventory_path_with_spaces -> PASS
C2_run_root_with_spaces       -> PASS
C3_labels_path_with_spaces    -> PASS
C4_no_space_control           -> PASS
C5_trailing_backslash         -> PASS
C6_double_space               -> PASS
C7_embedded_quotes            -> PASS
C8_empty_value                -> PASS
C9_unicode_path               -> PASS
C10_full_monitor_vector       -> PASS (28 arguments intact)
```

What this evidence supports, and what it does not:

* **Supported:** the monitor's quoting implementation preserves all tested argument boundaries — the
  corrective revision from the previous task is effective. The packaged self-test was defective only
  in its JSON array comparison. The temporary copy was non-governed; it was never committed.
* **Not supported / not claimed:** that the monitor quoting implementation failed. It did not fail.
* The corpus execution remained **not started** throughout; the temporary test reads no corpus file.

## 4. The narrow correction (this revision)

One hunk, one line, in `tools/i4_m2/I4_M2_TEST_LAUNCH_QUOTING.ps1`:

```diff
@@ -132,7 +132,7 @@
             if ($rawJson.Trim() -eq "[]") { $got = @() }
             if ($rawJson.Trim() -ne "[]") {
                 try {
-                    $got = @(ConvertFrom-Json $rawJson)
+                    $got = @(ConvertFrom-Json $rawJson | ForEach-Object { $_ })
                 }
                 catch {
                     $parseOk = $false
```

Preserved without change: all ten cases C1–C10 and their vectors (including the 28-element full
monitor vector and the non-ASCII path composed from `[char]` codes so the source stays ASCII-only),
the `ConvertTo-ProcessArgument` call and quoting logic, the marker-based extraction of the real
function from the monitor, the monitor SHA-256 pin `7ef9db12…`, the C1 "no fragment split at
'My Engines'" negative check, the pre-flight guards (monitor present and hash-matched, python
present, work root must not already exist), the fail-closed summary and its wording
(`I4 M2 LAUNCH QUOTING SELF-TEST = PASS` / `= FAIL`), and the `throw` on failure. The file remains
ASCII-only with LF endings.

**One adjacent repair in the same test file** (identified in the previous task and fixed here):
`tests/test_i4_m2_monitor_launch.py`'s full-vector coverage loop iterated the vector without
asserting anything (a no-op). It now asserts that each vector value appears in the self-test source.
No assertion was weakened or removed.

## 5. Proof that monitor / engine / runner behaviour is unchanged

| Check | Result |
| --- | --- |
| Monitor bytes | `tools/i4_m2/I4_M2_MEMORY_MONITOR.ps1` = `7ef9db12…`, byte-identical to the packaged copy; not touched by this revision |
| All 131 paths of the parent commit compared to the worktree | **exactly 2** differ — the self-test (the fix) and the launch-quoting test (the tightened assertion). 0 missing. No engine module (`src/nse_engine/*`), no runner module (`tools/i4_runner/*`), no doc, no manifest differs |
| Engine fingerprint | `d3269b73…` — unchanged |
| Runner fingerprint | `f3ebf624…` — unchanged |
| Runner module count / engine module count | 6 / 17 — unchanged |
| Static grammar validation (tree-sitter-powershell) | self-test parses with `has_error=False` before and after the substitution used for the grammar's unsupported `1GB`/`1MB` numeric literals; the corrected line introduces no error |

## 6. Focused regression test (added)

`tests/test_i4_m2_selftest_json_capture.py` — 15 tests, all OK. It does not merely re-check text: it
**extracts the self-test's own probe source, case vectors and case names from the file** (so the test
cannot silently drift from the script), writes the extracted probe, runs it as a real child process
for each of the ten cases, and replays both capture semantics through a model of the self-test's
comparison:

* the corrected expression appears exactly once, the defective form is gone, and there is exactly one
  capture site;
* the capture still feeds the unchanged count/element comparison, and the monitor pin and the
  fail-closed wording are intact;
* the probe returns a JSON **array** of its own argv for every case, with the elements exactly equal
  to the intended vector (including all 28 of C10);
* the corrected capture reproduces the Windows PASS for all ten cases;
* the defective capture reproduces the Windows all-FAIL (captured count 1 against expected N).

Limit, stated honestly: the PowerShell `@()`/pipeline enumeration semantics cannot be executed in
this sandbox (no PowerShell on Linux), so those semantics are modelled from the recorded Windows
evidence while the expression that produces them is pinned literally in the self-test. Only Windows
can execute the corrected self-test end-to-end; the package below carries it for that purpose.

## 7. Tests, counts, static checks

| Run | Result |
| --- | --- |
| Focused regression module (new) | 15 tests OK |
| Launch-quoting module (existing, tightened) | 19 tests OK |
| Both focused modules together | 34 tests OK |
| Complete repository suite | **432 tests OK** (previous 417 + 15 new) |
| `python3 -m compileall -q src tools tests` | exit 0 |
| Pattern checks on every AI-generated file | ASCII-only, LF-only, no `exit` / `return` / `else` / `elseif` / `finally` |

## 8. Delivery

The corrected self-test is delivered two ways:

1. **In Git** (durable, remote-verified): `tools/i4_m2/I4_M2_TEST_LAUNCH_QUOTING.ps1` at commit
   `43f233bc…`, with the regression test at `tests/test_i4_m2_selftest_json_capture.py`.
2. **In the transfer package** `I4_M2_WINDOWS_PACKAGE_v3.tar.gz` (`_transfer_delivery/m2_fix/`), whose
   `scripts\I4_M2_TEST_LAUNCH_QUOTING.ps1` is the corrected `4986b1fb…`. Package v2 is superseded for
   this file only; its monitor was already correct. Artifact hashes are recorded in
   `I4_M2_PACKAGE_BUILD_INFO_v3.json`.

On Windows, run the self-test before any execution attempt; it must print
`I4 M2 LAUNCH QUOTING SELF-TEST = PASS`. The re-run parameters are unchanged from the previous task:
same run id `i4-20261008`, new `-EvidencePrefix`, output root `G:\My Engines\I4_RUNS\i4-20261008`
(never created, still must not exist).

## 9. Prohibitions restated

No engine change · no `i4_runner.py` change · no monitor change · no threshold, corpus-contract,
output-contract or execution-semantics change · no corpus execution (2,462 members NOT executed) · no
production · no live NSE/provider access · no credentials · `main` untouched (`6a60583f…`) and no
merge into it · the failed attempt `G:\My Engines\I4_RUNS\i4-20261008` and its evidence remain
untouched and are never reused · storage technology remains undecided.

**Status: SELF-TEST CORRECTION = CLOSED / DURABLE / REMOTELY VERIFIED.**
**CORPUS EXECUTION = NOT PERFORMED.**
