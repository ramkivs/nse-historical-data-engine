#requires -Version 5.1
<#
  I4_M2_TEST_LAUNCH_QUOTING - prove that the monitor's argument quoting preserves argument
  boundaries across the Windows process-launch boundary.

  Why this exists: the M2 monitor originally passed an ARRAY to 'Start-Process -ArgumentList',
  which joins the elements with spaces and splits any value that contains a space. On Windows the
  runner therefore exited with code 2 and "unrecognized arguments", receiving fragments such as
  'Engines\10yhistoriclengine\evidence\inventory\file_inventory.json'. This self-test loads the
  REAL quoting function from the corrected monitor (between its marker comments), verifies the
  monitor SHA-256 pin, and launches a synthetic argument-capture child once per case through
  Start-Process with the quoted command line. Every value must arrive intact.

  Usage
    powershell -ExecutionPolicy Bypass -File I4_M2_TEST_LAUNCH_QUOTING.ps1
    powershell -ExecutionPolicy Bypass -File I4_M2_TEST_LAUNCH_QUOTING.ps1 -WorkRoot D:\tmp\quotetest

  The work folder must NOT already exist (fail-closed: no stale results are reused). No corpus
  file is read, the I4 runner is never launched, and nothing outside the work folder is written.
  This source file is ASCII-only by design, so Windows PowerShell 5.1 reads it identically on any
  code page; the non-ASCII test path is composed from character codes at run time.
#>

[CmdletBinding()]
param(
    [string]$MonitorPath = "",
    [string]$PythonExe = "python",
    [string]$WorkRoot = "",
    [string]$ExpectMonitorSha256 = "7ef9db125c3e25135ab51c251b7cc46b38da33a329949ac2fbcd1a171dc78f00"
)

$ErrorActionPreference = "Continue"
$problems = New-Object System.Collections.Generic.List[string]

if ($MonitorPath -eq "") { $MonitorPath = Join-Path (Split-Path -Parent $PSCommandPath) "I4_M2_MEMORY_MONITOR.ps1" }
if ($WorkRoot -eq "") { $WorkRoot = Join-Path $env:TEMP "i4_m2_quoting_test" }

Write-Host "monitor        : $MonitorPath"
Write-Host "python         : $PythonExe"
Write-Host "work root      : $WorkRoot"
Write-Host "expected sha256: $ExpectMonitorSha256"

if (-not (Test-Path -LiteralPath $MonitorPath)) { $problems.Add("monitor not found: $MonitorPath") }
if (-not (Get-Command $PythonExe -ErrorAction SilentlyContinue)) { $problems.Add("python not found: $PythonExe") }
if (Test-Path -LiteralPath $WorkRoot) { $problems.Add("work root already exists; remove it or pass -WorkRoot: $WorkRoot") }

$monitorOk = $false
if (Test-Path -LiteralPath $MonitorPath) {
    $monitorSha = (Get-FileHash -LiteralPath $MonitorPath -Algorithm SHA256).Hash.ToLower()
    Write-Host ("monitor sha256 : " + $monitorSha)
    if ($monitorSha -eq $ExpectMonitorSha256) { $monitorOk = $true }
    if ($monitorSha -ne $ExpectMonitorSha256) { $problems.Add("monitor sha256 mismatch; expected " + $ExpectMonitorSha256) }
}

$functionLoaded = $false
if ($monitorOk) {
    $monitorText = Get-Content -LiteralPath $MonitorPath -Raw
    $markerBegin = "# >>> I4_M2_ARG_QUOTING_BEGIN"
    $markerEnd = "# <<< I4_M2_ARG_QUOTING_END"
    $atBegin = $monitorText.IndexOf($markerBegin)
    $atEnd = $monitorText.IndexOf($markerEnd)
    if ($atBegin -lt 0 -or $atEnd -le $atBegin) {
        $problems.Add("quoting marker comments not found in the monitor")
    }
    if ($atBegin -ge 0 -and $atEnd -gt $atBegin) {
        $functionText = $monitorText.Substring($atBegin, $atEnd - $atBegin)
        Invoke-Expression $functionText
        $loaded = Get-Command ConvertTo-ProcessArgument -ErrorAction SilentlyContinue
        if ($null -ne $loaded) { $functionLoaded = $true }
        if ($null -eq $loaded) { $problems.Add("the extracted block did not define ConvertTo-ProcessArgument") }
    }
}

if ($problems.Count -eq 0) {
    New-Item -ItemType Directory -Path $WorkRoot -Force | Out-Null
    $probePath = Join-Path $WorkRoot "i4_m2_argv_probe.py"
    $probeLines = @(
        "import json",
        "import sys",
        "",
        "print(json.dumps(sys.argv[1:], ensure_ascii=True))"
    )
    [System.IO.File]::WriteAllText($probePath, (($probeLines -join "`n") + "`n"), (New-Object System.Text.UTF8Encoding($false)))

    $unicodePath = "G:\My Engines\" + [string][char]0x00DC + "n" + [string][char]0x00EF + "c" + [string][char]0x00F6 + "d" + [string][char]0x00E9 + "\" + [string][char]0x0444 + [string][char]0x0430 + [string][char]0x0439 + [string][char]0x043B + ".json"

    $fullVector = @(
        "tools\i4_runner\i4_runner.py",
        "run",
        "--legacy-root", "G:\My Engines\corpus_legacy\archives",
        "--udiff-root", "G:\My Engines\corpus_udiff\archives",
        "--inventory", "G:\My Engines\10yhistoriclengine\evidence\inventory\file_inventory.json",
        "--labels", "G:\My Engines\10yhistoriclengine\evidence\d04\DEC2_CAL_LABELS.json",
        "--d01-metrics", "G:\My Engines\10yhistoriclengine\evidence\d03\windows_run\FIX-SEM-DEF-01__metrics.csv",
        "--d01-verdict", "G:\My Engines\10yhistoriclengine\evidence\d03\windows_run\FIX-SEM-DEF-01__d01_definition_verdict.json",
        "--out", "G:\My Engines\I4_RUNS\i4-20261008",
        "--run-id", "i4-20261008",
        "--expect-records", "2462",
        "--expect-inventory-lf-sha256", "336b9531cd34f48e9a2e7e7593cc4e9c2736b3864d8213bc65d6ab8b488729d2",
        "--expect-tool-fingerprint", "d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9",
        "--expect-runner-fingerprint", "f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a",
        "--min-free-bytes", "15000000000"
    )

    $cases = @()
    $cases += [pscustomobject]@{ name = "C1_inventory_path_with_spaces"; args = @("--inventory", "G:\My Engines\10yhistoriclengine\evidence\inventory\file_inventory.json") }
    $cases += [pscustomobject]@{ name = "C2_run_root_with_spaces"; args = @("--out", "G:\My Engines\I4_RUNS\i4-20261008") }
    $cases += [pscustomobject]@{ name = "C3_labels_path_with_spaces"; args = @("--labels", "G:\My Engines\10yhistoriclengine\evidence\d04\DEC2_CAL_LABELS.json") }
    $cases += [pscustomobject]@{ name = "C4_no_space_control"; args = @("--legacy-root", "C:\Temp\no_space_control\archives") }
    $cases += [pscustomobject]@{ name = "C5_trailing_backslash"; args = @("--root", "G:\My Engines\I4_RUNS\") }
    $cases += [pscustomobject]@{ name = "C6_double_space"; args = @("--path", "G:\My  Engines\double  space\file.json") }
    $cases += [pscustomobject]@{ name = "C7_embedded_quotes"; args = @("--note", 'he said "hello" twice') }
    $cases += [pscustomobject]@{ name = "C8_empty_value"; args = @("--empty", "") }
    $cases += [pscustomobject]@{ name = "C9_unicode_path"; args = @("--path", $unicodePath) }
    $cases += [pscustomobject]@{ name = "C10_full_monitor_vector"; args = $fullVector }

    Write-Host "== running argument-boundary cases =="
    foreach ($case in $cases) {
        $items = @($probePath) + @($case.args)
        $quoted = @()
        foreach ($item in $items) { $quoted += (ConvertTo-ProcessArgument -Value ([string]$item)) }
        $argumentString = $quoted -join " "
        $stdoutPath = Join-Path $WorkRoot ("case_" + $case.name + ".stdout.txt")
        $stderrPath = Join-Path $WorkRoot ("case_" + $case.name + ".stderr.txt")
        $proc = Start-Process -FilePath $PythonExe -ArgumentList $argumentString -WorkingDirectory $WorkRoot -PassThru -Wait -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
        $exitCode = $proc.ExitCode
        $rawJson = Get-Content -LiteralPath $stdoutPath -Raw
        $got = @()
        $parseOk = $true
        if ($null -eq $rawJson) { $parseOk = $false }
        if ($null -ne $rawJson) {
            if ($rawJson.Trim() -eq "[]") { $got = @() }
            if ($rawJson.Trim() -ne "[]") {
                try {
                    $got = @(ConvertFrom-Json $rawJson)
                }
                catch {
                    $parseOk = $false
                }
            }
        }
        $expect = @($case.args)
        $caseOk = $exitCode -eq 0
        if (-not $parseOk) { $caseOk = $false }
        if ($parseOk) {
            if ($got.Count -ne $expect.Count) { $caseOk = $false }
            if ($got.Count -eq $expect.Count) {
                for ($k = 0; $k -lt $expect.Count; $k++) {
                    if (-not [string]::Equals([string]$got[$k], [string]$expect[$k], [System.StringComparison]::Ordinal)) { $caseOk = $false }
                }
            }
        }
        if ($caseOk) {
            Write-Host ("  " + $case.name + " -> PASS  (" + $expect.Count + " arguments intact)")
        }
        if (-not $caseOk) {
            Write-Host ("  " + $case.name + " -> FAIL") -ForegroundColor Red
            Write-Host ("     command line : " + $argumentString)
            Write-Host ("     exit code    : " + $exitCode)
            Write-Host ("     expected     : " + ($expect -join " | "))
            Write-Host ("     received     : " + ($got -join " | "))
            $stderrText = Get-Content -LiteralPath $stderrPath -Raw
            if ($stderrText) { Write-Host ("     stderr       : " + $stderrText.Trim()) }
            $problems.Add($case.name + ": arguments did not survive the process-launch boundary intact")
        }
        if ($case.name -eq "C1_inventory_path_with_spaces") {
            $splitAtSpace = $false
            foreach ($element in $got) {
                if ([string]::Equals([string]$element, "My", [System.StringComparison]::Ordinal)) { $splitAtSpace = $true }
                if ([string]::Equals([string]$element, "Engines\10yhistoriclengine\evidence\inventory\file_inventory.json", [System.StringComparison]::Ordinal)) { $splitAtSpace = $true }
            }
            if ($splitAtSpace) { $problems.Add("C1: the path was split at the space in 'My Engines'") }
            if (-not $splitAtSpace) { Write-Host "  C1 negative check: no fragment was split at 'My Engines' -> PASS" }
        }
    }
}

Write-Host "== I4 M2 launch quoting self-test summary =="
if ($problems.Count -gt 0) {
    foreach ($problem in $problems) { Write-Host ("PROBLEM: " + $problem) -ForegroundColor Red }
    Write-Host "I4 M2 LAUNCH QUOTING SELF-TEST = FAIL" -ForegroundColor Red
    throw "I4_M2_TEST_LAUNCH_QUOTING: FAILED (see PROBLEM lines above)"
}
Write-Host "I4 M2 LAUNCH QUOTING SELF-TEST = PASS" -ForegroundColor Green
Write-Host "The monitor now preserves every argument; a fresh monitored run may proceed (new -EvidencePrefix)."
