# I4_M2_MEMORY_MONITOR.ps1 — G-I4-M2 Phase D/E: run the governed corpus execution with a
# fail-closed memory monitor.
#
# What this script does:
#   1. refuses to start unless every pre-execution condition holds (new run root, thresholds
#      declared, baseline memory readable, free disk above the declared floor);
#   2. records the baseline facts (total RAM, available RAM, free disk) BEFORE processing;
#   3. launches the governed I4 runner with the pinned fingerprints and expectations;
#   4. samples process RSS, available memory and free disk while it runs, appending JSONL;
#   5. stops the run fail-closed if the declared RSS limit or the available-memory floor is
#      crossed (no completion marker is ever written by this script);
#   6. writes a summary with exact thresholds and the measured peak.
#
# Contract: no exit / return / else / elseif / finally. Terminal stays open. Fail-closed: a
# breach or a failed pre-execution check prints the exact facts and throws.
#
# The 2.5 GB M1 acceptance criterion is NOT modified here: it is the retained-state envelope
# criterion (recorded in the summary for the record). -RssLimitMB and -AvailableFloorMB are an
# independent machine-safety threshold that MUST be declared explicitly and is recorded before
# execution begins; it must not be changed once the run has started.
#
# Recommended declaration (record the actual values on the command line):
#   -RssLimitMB      min(6144, 50% of total physical RAM in MB)
#   -AvailableFloorMB 1024
#   -MinFreeBytes    15000000000   (expected output is ~12 GB for 2,462 members)
#
# Example:
#   .\I4_M2_MEMORY_MONITOR.ps1 -RepoRoot "C:\IIPS_Data\nse-historical-data-engine" `
#     -OutRoot "G:\My Engines\I4_RUNS\i4-20261008" -RunId "i4-20261008" `
#     -RssLimitMB 6144 -AvailableFloorMB 1024 `
#     -EvidencePrefix "G:\My Engines\I4_RUNS\i4-20261008.MEMORY_MONITOR"

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$RepoRoot,
  [Parameter(Mandatory = $true)][string]$OutRoot,
  [Parameter(Mandatory = $true)][string]$RunId,
  [Parameter(Mandatory = $true)][int]$RssLimitMB,
  [Parameter(Mandatory = $true)][int]$AvailableFloorMB,
  [Parameter(Mandatory = $true)][string]$EvidencePrefix,
  [string]$PythonExe = "python",
  [string]$LegacyRoot = "C:\IIPS_Data\NSE_Legacy_Acquisition\archives",
  [string]$UdiffRoot = "C:\IIPS_Data\NSE_CM_UDiFF_10Y\archives",
  [int]$SampleSeconds = 5,
  [long]$MinFreeBytes = 15000000000
)

$ErrorActionPreference = "Continue"
$ok = $true
$problems = New-Object System.Collections.Generic.List[string]
$encoding = New-Object System.Text.UTF8Encoding($false)

$expectedToolFp = "d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9"
$expectedRunnerFp = "f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a"
$expectedInventoryLfSha = "336b9531cd34f48e9a2e7e7593cc4e9c2736b3864d8213bc65d6ab8b488729d2"
$jsonlPath = $EvidencePrefix + ".jsonl"
$baselinePath = $EvidencePrefix + ".baseline.json"
$summaryPath = $EvidencePrefix + ".summary.json"
$stdoutPath = $EvidencePrefix + ".runner.stdout.txt"
$stderrPath = $EvidencePrefix + ".runner.stderr.txt"

# >>> I4_M2_ARG_QUOTING_BEGIN
# Defect fixed in this revision: 'Start-Process -ArgumentList <array>' joins the elements with
# spaces and does NOT preserve argument boundaries, so any value containing a space was split and
# the runner received fragments (observed on Windows: exit code 2, "unrecognized arguments").
# Every element of the argument list is now encoded with the documented Windows command-line
# quoting rule (MS C runtime / CommandLineToArgvW): wrap the value in double quotes, double any
# backslash run that stands before a quote, and double trailing backslashes so they cannot escape
# the closing quote.
function ConvertTo-ProcessArgument {
    param([string]$Value)
    $text = [string]$Value
    $builder = New-Object System.Text.StringBuilder
    [void]$builder.Append('"')
    $slashes = 0
    foreach ($char in $text.ToCharArray()) {
        if ($char -eq '\') {
            $slashes = $slashes + 1
            continue
        }
        if ($char -eq '"') {
            [void]$builder.Append('\' * (($slashes * 2) + 1))
            [void]$builder.Append('"')
            $slashes = 0
            continue
        }
        if ($slashes -gt 0) {
            [void]$builder.Append('\' * $slashes)
            $slashes = 0
        }
        [void]$builder.Append($char)
    }
    if ($slashes -gt 0) {
        [void]$builder.Append('\' * ($slashes * 2))
    }
    [void]$builder.Append('"')
    $builder.ToString()
}
# <<< I4_M2_ARG_QUOTING_END

Write-Host "== Phase D: pre-execution checks ==" -ForegroundColor Cyan
if (-not (Test-Path -LiteralPath $RepoRoot)) { $ok = $false; $problems.Add("repo root missing: $RepoRoot") }
if (-not (Get-Command $PythonExe -ErrorAction SilentlyContinue)) { $ok = $false; $problems.Add("python not found: $PythonExe") }
if (-not (Test-Path -LiteralPath $LegacyRoot)) { $ok = $false; $problems.Add("legacy root missing: $LegacyRoot") }
if (-not (Test-Path -LiteralPath $UdiffRoot)) { $ok = $false; $problems.Add("UDiFF root missing: $UdiffRoot") }
$outParent = Split-Path -Parent $OutRoot
if (-not (Test-Path -LiteralPath $outParent)) { $ok = $false; $problems.Add("run parent missing: $outParent") }
if (Test-Path -LiteralPath $OutRoot) { $ok = $false; $problems.Add("run root ALREADY EXISTS (never reuse a run root): $OutRoot") }
if ($RunId -eq "") { $ok = $false; $problems.Add("run id must not be empty") }
if ($RunId -match "[\\/]") { $ok = $false; $problems.Add("run id must not contain path separators") }
if ($RssLimitMB -lt 1024) { $ok = $false; $problems.Add("RssLimitMB must be >= 1024") }
if ($AvailableFloorMB -lt 512) { $ok = $false; $problems.Add("AvailableFloorMB must be >= 512") }
if ($SampleSeconds -lt 1) { $ok = $false; $problems.Add("SampleSeconds must be >= 1") }
if ($SampleSeconds -gt 60) { $ok = $false; $problems.Add("SampleSeconds must be <= 60") }
if (Test-Path -LiteralPath $summaryPath) { $ok = $false; $problems.Add("monitor evidence already exists: $summaryPath") }
$evidenceDir = Split-Path -Parent $EvidencePrefix
if ($evidenceDir -eq "") { $evidenceDir = "." }
if (-not (Test-Path -LiteralPath $evidenceDir)) { $ok = $false; $problems.Add("monitor evidence directory missing: $evidenceDir") }

$repoNorm = $RepoRoot.TrimEnd("\")
if ($OutRoot.StartsWith($repoNorm, [System.StringComparison]::OrdinalIgnoreCase)) { $ok = $false; $problems.Add("run root must be OUTSIDE the repository") }
if ($OutRoot.StartsWith($LegacyRoot.TrimEnd("\"), [System.StringComparison]::OrdinalIgnoreCase)) { $ok = $false; $problems.Add("run root must be OUTSIDE the legacy corpus root") }
if ($OutRoot.StartsWith($UdiffRoot.TrimEnd("\"), [System.StringComparison]::OrdinalIgnoreCase)) { $ok = $false; $problems.Add("run root must be OUTSIDE the UDiFF corpus root") }
if ($EvidencePrefix.StartsWith($OutRoot.TrimEnd("\"), [System.StringComparison]::OrdinalIgnoreCase)) { $ok = $false; $problems.Add("monitor evidence must live OUTSIDE the run root") }

$osInfo = $null
try { $osInfo = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop } catch { $osInfo = $null }
if ($null -eq $osInfo) { $ok = $false; $problems.Add("could not read baseline memory (Win32_OperatingSystem)") }
$totalRamMB = 0
$availRamMB = 0
if ($null -ne $osInfo) {
  $totalRamMB = [math]::Round($osInfo.TotalVisibleMemorySize / 1024, 1)
  $availRamMB = [math]::Round($osInfo.FreePhysicalMemory / 1024, 1)
}
$freeDisk = 0
try { $freeDisk = (New-Object System.IO.DriveInfo((Split-Path -Qualifier $OutRoot))).AvailableFreeSpace } catch { $freeDisk = 0 }
if ($freeDisk -le 0) { $ok = $false; $problems.Add("could not read free space for the run root drive") }
if ($freeDisk -gt 0 -and $freeDisk -lt $MinFreeBytes) { $ok = $false; $problems.Add("free space below the declared floor (MinFreeBytes)") }

$inventoryPath = Join-Path $RepoRoot "evidence\inventory\file_inventory.json"
$labelsPath = Join-Path $RepoRoot "evidence\d04\DEC2_CAL_LABELS.json"
$metricsPath = Join-Path $RepoRoot "evidence\d03\windows_run\FIX-SEM-DEF-01__metrics.csv"
$verdictPath = Join-Path $RepoRoot "evidence\d03\windows_run\FIX-SEM-DEF-01__d01_definition_verdict.json"
foreach ($required in @($inventoryPath, $labelsPath, $metricsPath, $verdictPath)) {
  if (-not (Test-Path -LiteralPath $required)) { $ok = $false; $problems.Add("governed input missing: $required") }
}

Write-Host "== Phase D: baseline facts ==" -ForegroundColor Cyan
$baseline = [ordered]@{
  recorded_at = (Get-Date).ToString("o")
  run_id = $RunId
  out_root = $OutRoot
  repo_root = $RepoRoot
  total_ram_mb = $totalRamMB
  available_ram_mb = $availRamMB
  free_disk_bytes = $freeDisk
  rss_limit_mb = $RssLimitMB
  available_floor_mb = $AvailableFloorMB
  min_free_bytes = $MinFreeBytes
  sample_seconds = $SampleSeconds
  m1_retained_acceptance_bytes = 2500000000
  m1_retained_acceptance_note = "unchanged M1 criterion: accumulator + runner retained envelope"
  expected_tool_fingerprint = $expectedToolFp
  expected_runner_fingerprint = $expectedRunnerFp
  expected_records = 2462
  expected_inventory_lf_sha256 = $expectedInventoryLfSha
}
[System.IO.File]::WriteAllText($baselinePath, (($baseline | ConvertTo-Json -Depth 5) + "`n"), $encoding)
Write-Host ("baseline written: " + $baselinePath)
Write-Host ("total RAM: " + $totalRamMB + " MB | available: " + $availRamMB + " MB | free disk: " + [math]::Round($freeDisk / 1GB, 2) + " GB")
Write-Host ("declared thresholds: RSS limit " + $RssLimitMB + " MB | available floor " + $AvailableFloorMB + " MB | min free bytes " + $MinFreeBytes)

Write-Host "== Phase E: launch the governed run ==" -ForegroundColor Cyan
if (-not $ok) {
  foreach ($problem in $problems) { Write-Host ("PROBLEM: " + $problem) -ForegroundColor Red }
  Write-Host "I4 M2 EXECUTION RESULT = FAIL (pre-execution checks failed; nothing was launched)" -ForegroundColor Red
  throw "I4_M2_MEMORY_MONITOR: pre-execution checks failed"
}
if ($ok) {
  $argList = @(
    "tools\i4_runner\i4_runner.py",
    "run",
    "--legacy-root", $LegacyRoot,
    "--udiff-root", $UdiffRoot,
    "--inventory", $inventoryPath,
    "--labels", $labelsPath,
    "--d01-metrics", $metricsPath,
    "--d01-verdict", $verdictPath,
    "--out", $OutRoot,
    "--run-id", $RunId,
    "--expect-records", "2462",
    "--expect-inventory-lf-sha256", $expectedInventoryLfSha,
    "--expect-tool-fingerprint", $expectedToolFp,
    "--expect-runner-fingerprint", $expectedRunnerFp,
    "--min-free-bytes", "$MinFreeBytes"
  )
  $quotedArgs = @()
  foreach ($item in $argList) { $quotedArgs += (ConvertTo-ProcessArgument -Value ([string]$item)) }
  $startArgs = $quotedArgs -join " "
  Write-Host ("runner command: " + $PythonExe + " " + $startArgs)
  $proc = Start-Process -FilePath $PythonExe -ArgumentList $startArgs -WorkingDirectory $RepoRoot -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
  Write-Host ("runner pid: " + $proc.Id)
  $breach = $false
  $breachReason = ""
  $sampleCount = 0
  $peakRssMB = 0
  $minAvailMB = [double]::MaxValue
  $minFreeDisk = $freeDisk
  $samplingFailures = 0
  $firstSample = $true

  while (-not $proc.HasExited) {
    $proc.Refresh()
    $rssMB = [math]::Round($proc.WorkingSet64 / 1MB, 1)
    $osSample = $null
    try { $osSample = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop } catch { $osSample = $null }
    $availMB = $null
    if ($null -ne $osSample) {
      $availMB = [math]::Round($osSample.FreePhysicalMemory / 1024, 1)
      $samplingFailures = 0
    }
    if ($null -eq $osSample) { $samplingFailures = $samplingFailures + 1 }
    $diskFree = 0
    try { $diskFree = (New-Object System.IO.DriveInfo((Split-Path -Qualifier $OutRoot))).AvailableFreeSpace } catch { $diskFree = 0 }

    $sampleCount = $sampleCount + 1
    if ($rssMB -gt $peakRssMB) { $peakRssMB = $rssMB }
    if ($null -ne $availMB) {
      if ($availMB -lt $minAvailMB) { $minAvailMB = $availMB }
    }
    if ($diskFree -gt 0) {
      if ($diskFree -lt $minFreeDisk) { $minFreeDisk = $diskFree }
    }
    $line = ([pscustomobject]@{
      at = (Get-Date).ToString("o")
      sample = $sampleCount
      runner_pid = $proc.Id
      rss_mb = $rssMB
      available_mb = $availMB
      free_disk_bytes = $diskFree
      sampling_failures = $samplingFailures
    } | ConvertTo-Json -Compress)
    [System.IO.File]::AppendAllText($jsonlPath, ($line + "`n"), $encoding)
    if ($firstSample) {
      Write-Host ("first sample: RSS " + $rssMB + " MB | available " + $availMB + " MB | free disk " + [math]::Round($diskFree / 1GB, 2) + " GB")
      $firstSample = $false
    }

    if ($rssMB -gt $RssLimitMB) { $breach = $true; $breachReason = ("process RSS " + $rssMB + " MB exceeds the declared limit " + $RssLimitMB + " MB") }
    if ($null -ne $availMB) {
      if ($availMB -lt $AvailableFloorMB) { $breach = $true; $breachReason = ("available memory " + $availMB + " MB is below the declared floor " + $AvailableFloorMB + " MB") }
    }
    if ($samplingFailures -ge 3) { $breach = $true; $breachReason = "monitor could not sample memory three times in a row" }
    if ($breach) {
      Write-Host ("MEMORY SAFETY BREACH: " + $breachReason) -ForegroundColor Red
      Stop-Process -Id $proc.Id -Force
      Start-Sleep -Seconds 2
    }
    if (-not $breach) { Start-Sleep -Seconds $SampleSeconds }
  }

  $proc.Refresh()
  $exitCode = $null
  $minAvailValue = $minAvailMB
  if ($minAvailMB -eq [double]::MaxValue) { $minAvailValue = $null }
  if ($proc.HasExited) { $exitCode = $proc.ExitCode }
  $completionMarker = Join-Path $OutRoot "RUN_COMPLETE.json"
  $summary = [ordered]@{
    recorded_at = (Get-Date).ToString("o")
    run_id = $RunId
    out_root = $OutRoot
    rss_limit_mb = $RssLimitMB
    available_floor_mb = $AvailableFloorMB
    min_free_bytes = $MinFreeBytes
    sample_seconds = $SampleSeconds
    samples = $sampleCount
    peak_rss_mb = $peakRssMB
    min_available_mb = $minAvailValue
    min_free_disk_bytes = $minFreeDisk
    baseline_total_ram_mb = $totalRamMB
    baseline_available_ram_mb = $availRamMB
    breach = $breach
    breach_reason = $breachReason
    runner_exit_code = $exitCode
    completion_marker_present = (Test-Path -LiteralPath $completionMarker)
    m1_retained_acceptance_bytes = 2500000000
    m1_retained_acceptance_note = "unchanged M1 criterion: accumulator + runner retained envelope"
  }
  [System.IO.File]::WriteAllText($summaryPath, (($summary | ConvertTo-Json -Depth 5) + "`n"), $encoding)
  Write-Host "== Phase E summary ==" -ForegroundColor Cyan
  Write-Host ("samples: " + $sampleCount + " | peak process RSS: " + $peakRssMB + " MB | min available: " + $summary.min_available_mb + " MB")
  Write-Host ("thresholds (declared before execution, not modified): RSS limit " + $RssLimitMB + " MB | available floor " + $AvailableFloorMB + " MB")
  Write-Host ("runner exit code: " + $exitCode + " | completion marker present: " + $summary.completion_marker_present)
  Write-Host ("monitor evidence: " + $summaryPath)
  if ($breach) {
    Write-Host "I4 M2 EXECUTION RESULT = FAIL (memory safety threshold crossed)" -ForegroundColor Red
    Write-Host "The run root is a FAILED run: preserve it untouched, never reuse it, and never verify it as complete."
    throw ("I4_M2_MEMORY_MONITOR: memory safety breach - " + $breachReason)
  }
  if ($exitCode -ne 0) {
    Write-Host "I4 M2 EXECUTION RESULT = FAIL (runner exit code $exitCode)" -ForegroundColor Red
    Write-Host "The run root is a FAILED run: preserve it untouched, never reuse it. See RUN_FAILED.json in the run root."
    throw "I4_M2_MEMORY_MONITOR: runner exited non-zero"
  }
  Write-Host "I4 M2 EXECUTION RESULT = PASS (runner completed; package verification is Phase F)" -ForegroundColor Green
}
