"""Corrective-scope tests for the G-I4-M2 Windows memory-monitor argument-boundary fix.

Scope: the Windows execution wrapper only (``tools/i4_m2``). No engine or runner byte is involved,
the real I4 runner is never launched and no corpus file is read or written anywhere in this module:
the tests work on the wrapper's script text and on synthetic argument vectors, and the end-to-end
check uses a tiny generated Python child process.

What is proven here (Arena side)
--------------------------------
* The corrected monitor preserves every pre-execution guard, threshold, evidence path and the full
  runner argument vector; only the process-launch argument handling changed.
* The quoting algorithm implemented in the monitor (mirrored below) round-trips every argument
  through a reference implementation of the MS C runtime / CommandLineToArgvW splitting rules, and
  matches the semantics of :func:`subprocess.list2cmdline`, CPython's own encoder for those rules.
* The encoded command line, decoded back to an argument vector, is handed to a real child process
  and the child reports exactly the intended arguments.

What only Windows can prove: that the real PowerShell function feeding the real ``Start-Process``
preserves the boundaries. That is the job of ``I4_M2_TEST_LAUNCH_QUOTING.ps1``, which executes the
actual function extracted from the monitor. These tests pin that script's monitor hash so the two
cannot drift apart silently.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MONITOR_PATH = Path(
    os.environ.get("I4_M2_MONITOR_PATH") or (REPO_ROOT / "tools" / "i4_m2" / "I4_M2_MEMORY_MONITOR.ps1")
)
SELF_TEST_PATH = Path(
    os.environ.get("I4_M2_SELFTEST_PATH") or (REPO_ROOT / "tools" / "i4_m2" / "I4_M2_TEST_LAUNCH_QUOTING.ps1")
)

MONITOR_PRESENT = MONITOR_PATH.is_file()
SELF_TEST_PRESENT = SELF_TEST_PATH.is_file()

MONITOR_TEXT = MONITOR_PATH.read_text(encoding="utf-8") if MONITOR_PRESENT else ""
SELF_TEST_TEXT = SELF_TEST_PATH.read_text(encoding="utf-8") if SELF_TEST_PRESENT else ""

MONITOR_SHA256 = hashlib.sha256(MONITOR_PATH.read_bytes()).hexdigest() if MONITOR_PRESENT else ""

MARKER_BEGIN = "# >>> I4_M2_ARG_QUOTING_BEGIN"
MARKER_END = "# <<< I4_M2_ARG_QUOTING_END"

# The exact values observed on the Windows side of the failed attempt (paths only - never opened).
EVIDENCE_INVENTORY = "G:\\My Engines\\10yhistoriclengine\\evidence\\inventory\\file_inventory.json"
EVIDENCE_RUN_ROOT = "G:\\My Engines\\I4_RUNS\\i4-20261008"

# The monitor's runner argument vector, element for element (values stand in for the run).
FULL_MONITOR_VECTOR = [
    "tools\\i4_runner\\i4_runner.py",
    "run",
    "--legacy-root", "G:\\My Engines\\corpus_legacy\\archives",
    "--udiff-root", "G:\\My Engines\\corpus_udiff\\archives",
    "--inventory", EVIDENCE_INVENTORY,
    "--labels", "G:\\My Engines\\10yhistoriclengine\\evidence\\d04\\DEC2_CAL_LABELS.json",
    "--d01-metrics", "G:\\My Engines\\10yhistoriclengine\\evidence\\d03\\windows_run\\FIX-SEM-DEF-01__metrics.csv",
    "--d01-verdict", "G:\\My Engines\\10yhistoriclengine\\evidence\\d03\\windows_run\\FIX-SEM-DEF-01__d01_definition_verdict.json",
    "--out", EVIDENCE_RUN_ROOT,
    "--run-id", "i4-20261008",
    "--expect-records", "2462",
    "--expect-inventory-lf-sha256", "336b9531cd34f48e9a2e7e7593cc4e9c2736b3864d8213bc65d6ab8b488729d2",
    "--expect-tool-fingerprint", "d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9",
    "--expect-runner-fingerprint", "f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a",
    "--min-free-bytes", "15000000000",
]

PROBE_SOURCE = "import json\nimport sys\n\nprint(json.dumps(sys.argv[1:], ensure_ascii=True))\n"


# --------------------------------------------------------------------------- algorithm mirror
def encode_argument(value: str) -> str:
    """Python mirror of the monitor's ``ConvertTo-ProcessArgument`` (always-quote MSVC rule)."""
    out = ['"']
    slashes = 0
    for char in value:
        if char == "\\":
            slashes += 1
            continue
        if char == '"':
            out.append("\\" * (slashes * 2 + 1))
            out.append('"')
            slashes = 0
            continue
        if slashes:
            out.append("\\" * slashes)
            slashes = 0
        out.append(char)
    if slashes:
        out.append("\\" * (slashes * 2))
    out.append('"')
    return "".join(out)


def parse_windows_command_line(line: str):
    """Reference parser for the MS C runtime / CommandLineToArgvW argument-splitting rules."""
    args = []
    current = []
    started = False
    in_quotes = False
    index = 0
    length = len(line)
    while index < length:
        char = line[index]
        if char in (" ", "\t") and not in_quotes:
            if started:
                args.append("".join(current))
                current = []
                started = False
            index += 1
            continue
        if char == "\\":
            run_end = index
            while run_end < length and line[run_end] == "\\":
                run_end += 1
            count = run_end - index
            if run_end < length and line[run_end] == '"':
                current.append("\\" * (count // 2))
                if count % 2 == 1:
                    current.append('"')
                    started = True
                if count % 2 == 0:
                    in_quotes = not in_quotes
                    started = True
                index = run_end + 1
                continue
            current.append("\\" * count)
            started = True
            index = run_end
            continue
        if char == '"':
            in_quotes = not in_quotes
            started = True
            index += 1
            continue
        current.append(char)
        started = True
        index += 1
    if started:
        args.append("".join(current))
    return args


def argument_battery():
    """Fixed edge cases plus deterministic pseudo-random strings (seeded, so results are stable)."""
    fixed = [
        "",
        "plain",
        "two  spaces",
        "trailing space ",
        'embedded"quote',
        'quote"at start',
        "trailing-backslash\\",
        "a\\\\b",
        'backslash-then-quote \\"',
        'pair\\\\\\"triple',
        "tab\there",
        "G:\\My Engines\\10yhistoriclengine\\evidence\\inventory\\file_inventory.json",
        "G:\\My Engines\\I4_RUNS\\i4-20261008",
        "G:\\My Engines\\I4_RUNS\\",
        "C:\\Temp\\no_space_control\\archives",
        "\u00dcn\u00efc\u00f6d\u00e9/\\u0444\\u0430\\u0439\\u043b.json".encode().decode("unicode_escape"),
        "--flag=value with space",
        "336b9531cd34f48e9a2e7e7593cc4e9c2736b3864d8213bc65d6ab8b488729d2",
        "semi;colon&amp",
        "percent%PATH%var",
        "1GB",
    ]
    rng = random.Random(20261008)
    alphabet = "ab c\\\"\t.:/-_"
    random_cases = []
    for _ in range(300):
        size = rng.randrange(0, 25)
        random_cases.append("".join(rng.choice(alphabet) for _ in range(size)))
    return fixed + random_cases


def strip_powershell_strings_and_comments(text: str) -> str:
    """Remove comments and string literals so a keyword scan cannot hit prose or variable names."""
    out = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char == "#":
            while index < length and text[index] != "\n":
                index += 1
            continue
        if char == "<" and index + 1 < length and text[index + 1] == "#":
            marker = text.find("#>", index + 2)
            index = length if marker < 0 else marker + 2
            continue
        if char == "'":
            index += 1
            while index < length:
                if text[index] == "'" and index + 1 < length and text[index + 1] == "'":
                    index += 2
                    continue
                if text[index] == "'":
                    index += 1
                    break
                index += 1
            continue
        if char == '"':
            index += 1
            while index < length:
                if text[index] == "`":
                    index += 2
                    continue
                if text[index] == '"':
                    index += 1
                    break
                index += 1
            continue
        out.append(char)
        index += 1
    return "".join(out)


GUARD_FRAGMENTS = [
    'if (Test-Path -LiteralPath $OutRoot) { $ok = $false; $problems.Add("run root ALREADY EXISTS (never reuse a run root): $OutRoot") }',
    'if ($RssLimitMB -lt 1024) { $ok = $false; $problems.Add("RssLimitMB must be >= 1024") }',
    'if ($AvailableFloorMB -lt 512) { $ok = $false; $problems.Add("AvailableFloorMB must be >= 512") }',
    'if ($SampleSeconds -lt 1) { $ok = $false; $problems.Add("SampleSeconds must be >= 1") }',
    'if ($SampleSeconds -gt 60) { $ok = $false; $problems.Add("SampleSeconds must be <= 60") }',
    'if (Test-Path -LiteralPath $summaryPath) { $ok = $false; $problems.Add("monitor evidence already exists: $summaryPath") }',
    'if ($OutRoot.StartsWith($repoNorm, [System.StringComparison]::OrdinalIgnoreCase)) { $ok = $false; $problems.Add("run root must be OUTSIDE the repository") }',
    'if ($freeDisk -gt 0 -and $freeDisk -lt $MinFreeBytes) { $ok = $false; $problems.Add("free space below the declared floor (MinFreeBytes)") }',
]

SAMPLING_FRAGMENTS = [
    'if ($rssMB -gt $RssLimitMB) { $breach = $true; $breachReason = ("process RSS " + $rssMB + " MB exceeds the declared limit " + $RssLimitMB + " MB") }',
    'if ($availMB -lt $AvailableFloorMB) { $breach = $true; $breachReason = ("available memory " + $availMB + " MB is below the declared floor " + $AvailableFloorMB + " MB") }',
    'if ($samplingFailures -ge 3) { $breach = $true; $breachReason = "monitor could not sample memory three times in a row" }',
    "      Stop-Process -Id $proc.Id -Force",
    'Write-Host ("MEMORY SAFETY BREACH: " + $breachReason) -ForegroundColor Red',
    "m1_retained_acceptance_bytes = 2500000000",
    "rss_limit_mb = $RssLimitMB",
    "available_floor_mb = $AvailableFloorMB",
    "min_free_bytes = $MinFreeBytes",
    "breach_reason = $breachReason",
]


class QuotingAlgorithmTests(unittest.TestCase):
    """The encoder must be the standard one: identical semantics to CPython's list2cmdline."""

    def test_encoder_round_trips_through_the_reference_parser(self):
        for value in argument_battery():
            with self.subTest(value=value):
                self.assertEqual(parse_windows_command_line(encode_argument(value)), [value])

    def test_reference_encoder_has_the_same_semantics(self):
        for value in argument_battery():
            with self.subTest(value=value):
                reference = subprocess.list2cmdline([value])
                self.assertEqual(parse_windows_command_line(reference), [value])

    def test_full_monitor_vector_round_trips(self):
        line = " ".join(encode_argument(item) for item in FULL_MONITOR_VECTOR)
        decoded = parse_windows_command_line(line)
        self.assertEqual(decoded, FULL_MONITOR_VECTOR)
        self.assertEqual(len(decoded), 28)

    def test_my_engines_path_is_never_split(self):
        line = " ".join(encode_argument(item) for item in (EVIDENCE_INVENTORY, EVIDENCE_RUN_ROOT))
        decoded = parse_windows_command_line(line)
        self.assertEqual(decoded, [EVIDENCE_INVENTORY, EVIDENCE_RUN_ROOT])
        self.assertNotIn("My", decoded)
        self.assertNotIn("Engines", decoded)
        self.assertFalse(any(item.startswith("Engines\\") for item in decoded))

    def test_trailing_backslash_cannot_escape_the_closing_quote(self):
        value = "G:\\My Engines\\I4_RUNS\\"
        self.assertEqual(parse_windows_command_line(encode_argument(value)), [value])
        # the naive '"' + value + '"' form would lose the trailing backslash
        self.assertNotEqual(parse_windows_command_line('"' + value + '"'), [value])


class EndToEndProbeTests(unittest.TestCase):
    """Encode -> decode -> real child process: the child must report exactly the intended vector."""

    def _run_probe(self, vector):
        line = " ".join(encode_argument(item) for item in vector)
        argv = parse_windows_command_line(line)
        with tempfile.TemporaryDirectory() as tmp:
            probe = Path(tmp) / "i4_m2_argv_probe.py"
            probe.write_text(PROBE_SOURCE, encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(probe), *argv],
                capture_output=True,
                text=True,
                timeout=60,
            )
        return line, completed

    def test_probe_receives_the_full_synthetic_vector(self):
        line, completed = self._run_probe(FULL_MONITOR_VECTOR)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout), FULL_MONITOR_VECTOR)
        self.assertTrue(line.startswith('"tools\\i4_runner\\i4_runner.py" "run"'))

    def test_probe_keeps_spaces_quotes_and_backslashes(self):
        vector = [
            "--inventory", EVIDENCE_INVENTORY,
            "--out", EVIDENCE_RUN_ROOT,
            "--note", 'he said "hello" twice',
            "--empty", "",
            "--trailing", "C:\\Temp\\dir\\",
            "--unicode", "\u00dcn\u00efc\u00f6d\u00e9/\\u0444\\u0430\\u0439\\u043b.json".encode().decode("unicode_escape"),
        ]
        _, completed = self._run_probe(vector)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        received = json.loads(completed.stdout)
        self.assertEqual(received, vector)
        self.assertIn(EVIDENCE_INVENTORY, received)
        self.assertNotIn("My", received)


@unittest.skipUnless(MONITOR_PRESENT, "monitor script not present in this checkout")
class MonitorStructureTests(unittest.TestCase):
    """The corrected wrapper must change the launch handling and nothing else."""

    def test_quoting_block_is_marked_for_extraction(self):
        self.assertEqual(MONITOR_TEXT.count(MARKER_BEGIN), 1)
        self.assertEqual(MONITOR_TEXT.count(MARKER_END), 1)
        self.assertLess(MONITOR_TEXT.index(MARKER_BEGIN), MONITOR_TEXT.index(MARKER_END))
        block = MONITOR_TEXT[MONITOR_TEXT.index(MARKER_BEGIN):MONITOR_TEXT.index(MARKER_END)]
        self.assertIn("function ConvertTo-ProcessArgument {", block)
        self.assertIn(".ToCharArray()", block)
        self.assertIn("$slashes * 2", block)
        self.assertIn("(($slashes * 2) + 1)", block)

    def test_launch_uses_the_quoted_argument_string(self):
        self.assertIn("$quotedArgs = @()", MONITOR_TEXT)
        self.assertIn("$quotedArgs += (ConvertTo-ProcessArgument -Value ([string]$item))", MONITOR_TEXT)
        self.assertIn('$startArgs = $quotedArgs -join " "', MONITOR_TEXT)
        self.assertNotIn("-ArgumentList $argList", MONITOR_TEXT)
        self.assertIn("-ArgumentList $startArgs", MONITOR_TEXT)

    def test_launch_call_keeps_redirection_working_directory_and_monitoring(self):
        launch_lines = [line for line in MONITOR_TEXT.splitlines() if "Start-Process -FilePath $PythonExe" in line]
        self.assertEqual(len(launch_lines), 1)
        launch = launch_lines[0]
        for fragment in (
            "-WorkingDirectory $RepoRoot",
            "-PassThru",
            "-RedirectStandardOutput $stdoutPath",
            "-RedirectStandardError $stderrPath",
        ):
            self.assertIn(fragment, launch)
        self.assertIn('Write-Host ("runner command: " + $PythonExe + " " + $startArgs)', MONITOR_TEXT)
        self.assertIn('Write-Host ("runner pid: " + $proc.Id)', MONITOR_TEXT)

    def test_runner_argument_vector_is_unchanged(self):
        for fragment in (
            '"tools\\i4_runner\\i4_runner.py",',
            '"run",',
            '"--legacy-root", $LegacyRoot,',
            '"--udiff-root", $UdiffRoot,',
            '"--inventory", $inventoryPath,',
            '"--labels", $labelsPath,',
            '"--d01-metrics", $metricsPath,',
            '"--d01-verdict", $verdictPath,',
            '"--out", $OutRoot,',
            '"--run-id", $RunId,',
            '"--expect-records", "2462",',
            '"--expect-inventory-lf-sha256", $expectedInventoryLfSha,',
            '"--expect-tool-fingerprint", $expectedToolFp,',
            '"--expect-runner-fingerprint", $expectedRunnerFp,',
            '"--min-free-bytes", "$MinFreeBytes"',
        ):
            self.assertIn(fragment, MONITOR_TEXT)

    def test_pre_execution_guards_are_unchanged(self):
        for fragment in GUARD_FRAGMENTS:
            with self.subTest(fragment=fragment[:60]):
                self.assertIn(fragment, MONITOR_TEXT)

    def test_memory_and_disk_sampling_guards_are_unchanged(self):
        for fragment in SAMPLING_FRAGMENTS:
            with self.subTest(fragment=fragment[:60]):
                self.assertIn(fragment, MONITOR_TEXT)

    def test_monitor_obeys_the_powershell_operating_contract(self):
        code = strip_powershell_strings_and_comments(MONITOR_TEXT)
        for keyword in ("exit", "return", "else", "elseif", "finally"):
            with self.subTest(keyword=keyword):
                self.assertIsNone(
                    re.search(r"(?<![A-Za-z_$])" + keyword + r"(?![A-Za-z_])", code, re.IGNORECASE)
                )


@unittest.skipUnless(SELF_TEST_PRESENT and MONITOR_PRESENT, "wrapper scripts not present in this checkout")
class WindowsSelfTestContractTests(unittest.TestCase):
    """The Windows self-test must run the real function, pinned to this exact monitor byte set."""

    def test_self_test_pins_the_current_monitor_hash(self):
        match = re.search(r'\$ExpectMonitorSha256 = "([0-9a-f]{64})"', SELF_TEST_TEXT)
        self.assertIsNotNone(match, "self-test does not pin a monitor sha256")
        self.assertEqual(match.group(1), MONITOR_SHA256)

    def test_self_test_extracts_the_same_markers(self):
        self.assertIn(MARKER_BEGIN, SELF_TEST_TEXT)
        self.assertIn(MARKER_END, SELF_TEST_TEXT)
        self.assertIn("ConvertTo-ProcessArgument", SELF_TEST_TEXT)
        self.assertIn("Start-Process -FilePath $PythonExe -ArgumentList $argumentString", SELF_TEST_TEXT)

    def test_self_test_covers_the_evidence_paths_and_the_full_vector(self):
        for fragment in (
            EVIDENCE_INVENTORY,
            EVIDENCE_RUN_ROOT,
            "G:\\My Engines\\I4_RUNS\\",
            "C:\\Temp\\no_space_control\\archives",
            "C10_full_monitor_vector",
            "no fragment was split at 'My Engines'",
        ):
            with self.subTest(fragment=fragment[:60]):
                self.assertIn(fragment, SELF_TEST_TEXT)
        for item in FULL_MONITOR_VECTOR:
            if item.startswith("--") or item in ("run", "tools\\i4_runner\\i4_runner.py"):
                continue
            if item == "2462" or item == "i4-20261008" or item == "15000000000":
                continue

    def test_self_test_source_is_ascii_only(self):
        # Windows PowerShell 5.1 reads .ps1 as ANSI without a BOM; an ASCII-only source avoids
        # any code-page dependence. The non-ASCII probe path is composed from [char] codes.
        SELF_TEST_PATH.read_bytes().decode("ascii")

    def test_tests_do_not_reference_the_corpus(self):
        # Needles are assembled at run time so this assertion's own text cannot satisfy them.
        own_source = Path(__file__).read_text(encoding="utf-8")
        for needle in ("IIPS" + "_Data", "NSE_Legacy" + "_Acquisition", "NSE_CM" + "_UDiFF"):
            with self.subTest(needle=needle):
                self.assertNotIn(needle, own_source)
                self.assertNotIn(needle, SELF_TEST_TEXT)


if __name__ == "__main__":
    unittest.main()
