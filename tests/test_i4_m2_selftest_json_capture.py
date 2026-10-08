"""Focused regression test: the I4 M2 launch-quoting self-test must ENUMERATE the JSON array that
its argv probe returns.

Windows evidence (2026-10-08). The governed monitor
``tools/i4_m2/I4_M2_MEMORY_MONITOR.ps1`` (sha256 ``7ef9db12...``) preserved every tested argument
boundary. The packaged self-test nevertheless reported every case as FAIL because Windows PowerShell
5.1 does not enumerate a JSON array captured out of ``ConvertFrom-Json``:

    $got = @(ConvertFrom-Json $rawJson)                            # defective: ONE wrapper element
    $got = @(ConvertFrom-Json $rawJson | ForEach-Object { $_ })    # corrected: N elements

With the defective capture the count comparison ``$got.Count -ne $expect.Count`` is 1 versus N, so
C1-C10 all failed; with the corrected capture Windows reported C1-C10 PASS, including C10 with all
28 arguments intact. The monitor quoting implementation did not fail and is not implicated.

This module pins the corrected expression, extracts the self-test's OWN probe source, case vectors
and case names from the file (so it cannot drift away from them), runs the real probe as a child
process, and replays both capture semantics through a model of the self-test's comparison. The
PowerShell capture operator itself cannot be executed in this sandbox (no PowerShell on Linux), so
the enumeration semantics are modelled from the recorded Windows evidence while the expression that
produces them is pinned literally.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SELFTEST_PATH = Path(
    os.environ.get("I4_M2_SELFTEST_PATH")
    or (REPO_ROOT / "tools" / "i4_m2" / "I4_M2_TEST_LAUNCH_QUOTING.ps1")
)
SELFTEST_PRESENT = SELFTEST_PATH.is_file()
SELFTEST_TEXT = SELFTEST_PATH.read_text(encoding="utf-8") if SELFTEST_PRESENT else ""

EXPECTED_MONITOR_SHA256 = "7ef9db125c3e25135ab51c251b7cc46b38da33a329949ac2fbcd1a171dc78f00"
DEFECTIVE_CAPTURE = "$got = @(ConvertFrom-Json $rawJson)"
CORRECTED_CAPTURE = "$got = @(ConvertFrom-Json $rawJson | ForEach-Object { $_ })"

EXPECTED_CASE_NAMES = [
    "C1_inventory_path_with_spaces",
    "C2_run_root_with_spaces",
    "C3_labels_path_with_spaces",
    "C4_no_space_control",
    "C5_trailing_backslash",
    "C6_double_space",
    "C7_embedded_quotes",
    "C8_empty_value",
    "C9_unicode_path",
    "C10_full_monitor_vector",
]

EXPECTED_PROBE_SOURCE = "import json\nimport sys\n\nprint(json.dumps(sys.argv[1:], ensure_ascii=True))\n"

# The self-test composes the non-ASCII path from character codes so the source stays ASCII-only.
UNICODE_PATH = (
    "G:\\My Engines\\"
    + chr(0x00DC)
    + "n"
    + chr(0x00EF)
    + "c"
    + chr(0x00F6)
    + "d"
    + chr(0x00E9)
    + "\\"
    + chr(0x0444)
    + chr(0x0430)
    + chr(0x0439)
    + chr(0x043B)
    + ".json"
)

# PowerShell double-quoted strings do not use backslash escapes (the escape is a backtick), so a
# token is simply the text between unescaped quotes; single-quoted strings are literal.
PS_TOKEN = re.compile(r'"[^"]*"|\'[^\']*\'|\$[A-Za-z_][A-Za-z0-9_]*')
CASE_LINE = re.compile(
    r'\$cases \+= \[pscustomobject\]@\{ name = "([A-Za-z0-9_]+)"; args = (.+) \}$'
)


def ps_token_value(token):
    """Value of a PowerShell token: quoted string -> contents, variable -> the token itself."""
    if token.startswith('"') and token.endswith('"') and len(token) >= 2:
        return token[1:-1]
    if token.startswith("'") and token.endswith("'") and len(token) >= 2:
        return token[1:-1]
    return token


def extract_full_vector(text):
    """The 28-element runner argument vector, exactly as the self-test defines it."""
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip() == "$fullVector = @("]
    if len(starts) != 1:
        return []
    values = []
    for line in lines[starts[0] + 1:]:
        if line.strip() == ")":
            break
        values.extend(token[1:-1] for token in re.findall(r'"[^"]*"', line))
    return values


def extract_cases(text):
    """Ordered {name: [args]} from the self-test, with $unicodePath / $fullVector resolved."""
    full_vector = extract_full_vector(text)
    cases = []
    for line in text.splitlines():
        match = CASE_LINE.search(line)
        if not match:
            continue
        name, expr = match.group(1), match.group(2).strip()
        if expr == "$fullVector":
            args = list(full_vector)
        else:
            inner = expr[2:-1] if expr.startswith("@(") and expr.endswith(")") else expr
            args = []
            for token in PS_TOKEN.findall(inner):
                value = ps_token_value(token)
                if value == "$unicodePath":
                    value = UNICODE_PATH
                if value == "$fullVector":
                    args.extend(full_vector)
                    continue
                args.append(value)
        cases.append((name, args))
    return cases


def extract_probe_source(text):
    """The probe script the self-test writes, extracted from its $probeLines array."""
    match = re.search(r"\$probeLines = @\(\s*\n(.*?)\n\s*\)", text, re.S)
    if not match:
        return ""
    return "\n".join(re.findall(r'"([^"]*)"', match.group(1))) + "\n"


def capture_ps51_wrapper(json_text):
    """Model of the DEFECTIVE capture ``@(ConvertFrom-Json $rawJson)`` on Windows PowerShell 5.1.

    ConvertFrom-Json hands the deserialized array back as a single object, so @() wraps it in a
    one-element array whose only element is the whole array.
    """
    return [json.loads(json_text)]


def capture_corrected(json_text):
    """Model of the CORRECTED capture ``@(ConvertFrom-Json $rawJson | ForEach-Object { $_ })``."""
    return list(json.loads(json_text))


def selftest_verdict(captured, expected, exit_code=0, parse_ok=True):
    """The self-test's own comparison, transcribed: count equality then Ordinal element equality."""
    case_ok = exit_code == 0
    if not parse_ok:
        case_ok = False
    if parse_ok:
        if len(captured) != len(expected):
            case_ok = False
        if len(captured) == len(expected):
            for index in range(len(expected)):
                if str(captured[index]) != str(expected[index]):
                    case_ok = False
    return case_ok


@unittest.skipUnless(SELFTEST_PRESENT, "self-test not present in this checkout")
class JsonCaptureContractTests(unittest.TestCase):
    """The correction itself: one capture site, enumerated, still pinned to the governed monitor."""

    def test_corrected_capture_expression_is_present_exactly_once(self):
        self.assertEqual(SELFTEST_TEXT.count(CORRECTED_CAPTURE), 1)

    def test_defective_capture_expression_is_gone(self):
        self.assertNotIn(DEFECTIVE_CAPTURE, SELFTEST_TEXT)

    def test_there_is_exactly_one_capture_site(self):
        self.assertEqual(SELFTEST_TEXT.count("ConvertFrom-Json"), 1)
        self.assertEqual(SELFTEST_TEXT.count("$got = @(ConvertFrom-Json"), 1)

    def test_the_capture_feeds_the_self_test_comparison_unchanged(self):
        self.assertIn("if ($got.Count -ne $expect.Count) { $caseOk = $false }", SELFTEST_TEXT)
        self.assertIn(
            "if (-not [string]::Equals([string]$got[$k], [string]$expect[$k], "
            "[System.StringComparison]::Ordinal)) { $caseOk = $false }",
            SELFTEST_TEXT,
        )
        self.assertIn("$expect = @($case.args)", SELFTEST_TEXT)

    def test_self_test_still_pins_the_governed_monitor(self):
        match = re.search(r'\$ExpectMonitorSha256 = "([0-9a-f]{64})"', SELFTEST_TEXT)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), EXPECTED_MONITOR_SHA256)

    def test_fail_closed_summary_and_output_wording_are_unchanged(self):
        self.assertIn('Write-Host "I4 M2 LAUNCH QUOTING SELF-TEST = PASS"', SELFTEST_TEXT)
        self.assertIn('Write-Host "I4 M2 LAUNCH QUOTING SELF-TEST = FAIL"', SELFTEST_TEXT)
        self.assertIn("PROBLEM: ", SELFTEST_TEXT)
        self.assertIn(
            "throw \"I4_M2_TEST_LAUNCH_QUOTING: FAILED (see PROBLEM lines above)\"", SELFTEST_TEXT
        )
        self.assertIn("work root already exists; remove it or pass -WorkRoot", SELFTEST_TEXT)
        self.assertIn("monitor sha256 mismatch; expected ", SELFTEST_TEXT)

    def test_case_set_matches_the_windows_evidence(self):
        names = [name for name, _ in extract_cases(SELFTEST_TEXT)]
        self.assertEqual(names, EXPECTED_CASE_NAMES)

    def test_unicode_case_is_still_composed_from_character_codes(self):
        codes = ["0x00DC", "0x00EF", "0x00F6", "0x00E9", "0x0444", "0x0430", "0x0439", "0x043B"]
        for code in codes:
            with self.subTest(code=code):
                self.assertIn("[char]" + code, SELFTEST_TEXT)
        cases = dict(extract_cases(SELFTEST_TEXT))
        self.assertEqual(cases["C9_unicode_path"], ["--path", UNICODE_PATH])
        self.assertNotIn("\u00dc", SELFTEST_TEXT)


@unittest.skipUnless(SELFTEST_PRESENT, "self-test not present in this checkout")
class ProbeArrayCaptureRegressionTests(unittest.TestCase):
    """End to end: the real probe -> JSON array -> both capture semantics -> the self-test verdict."""

    @classmethod
    def setUpClass(cls):
        cls.probe_source = extract_probe_source(SELFTEST_TEXT)
        cls.cases = extract_cases(SELFTEST_TEXT)
        cls.full_vector = extract_full_vector(SELFTEST_TEXT)
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.probe_path = Path(cls.tempdir.name) / "i4_m2_argv_probe.py"
        cls.probe_path.write_text(cls.probe_source, encoding="utf-8", newline="")
        cls.probe_json = {}
        for name, args in cls.cases:
            completed = subprocess.run(
                [sys.executable, str(cls.probe_path)] + list(args),
                cwd=cls.tempdir.name,
                capture_output=True,
                check=False,
            )
            cls.probe_json[name] = (completed.returncode, completed.stdout.decode("utf-8"),
                                    completed.stderr.decode("utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tempdir.cleanup()

    def test_probe_source_is_the_one_the_self_test_writes(self):
        self.assertEqual(self.probe_source, EXPECTED_PROBE_SOURCE)

    def test_full_vector_has_the_28_runner_arguments(self):
        self.assertEqual(len(self.full_vector), 28)
        self.assertEqual(self.full_vector[0], "tools\\i4_runner\\i4_runner.py")
        self.assertEqual(self.full_vector[1], "run")

    def test_probe_returns_the_json_array_of_its_own_argv(self):
        for name, args in self.cases:
            with self.subTest(case=name):
                exit_code, stdout, stderr = self.probe_json[name]
                self.assertEqual(exit_code, 0, stderr)
                parsed = json.loads(stdout)
                self.assertIsInstance(parsed, list)
                self.assertEqual(parsed, list(args))
                for element in parsed:
                    self.assertIsInstance(element, str)

    def test_corrected_capture_reproduces_the_windows_pass(self):
        for name, args in self.cases:
            with self.subTest(case=name):
                _, stdout, _ = self.probe_json[name]
                captured = capture_corrected(stdout)
                self.assertEqual(len(captured), len(args))
                self.assertTrue(selftest_verdict(captured, args))

    def test_corrected_capture_keeps_all_28_vector_arguments_intact(self):
        _, stdout, _ = self.probe_json["C10_full_monitor_vector"]
        captured = capture_corrected(stdout)
        self.assertEqual(len(captured), 28)
        self.assertEqual(captured, self.full_vector)
        for index, value in enumerate(self.full_vector):
            with self.subTest(index=index):
                self.assertEqual(captured[index], value)

    def test_defective_capture_reproduces_the_windows_all_fail(self):
        for name, args in self.cases:
            with self.subTest(case=name):
                _, stdout, _ = self.probe_json[name]
                captured = capture_ps51_wrapper(stdout)
                self.assertEqual(len(captured), 1, "the wrapper holds the whole array as one element")
                self.assertNotEqual(len(captured), len(args))
                self.assertFalse(selftest_verdict(captured, args),
                                 "the defective capture must fail the comparison for " + name)

    def test_c1_negative_check_still_reports_no_split_at_my_engines(self):
        _, stdout, _ = self.probe_json["C1_inventory_path_with_spaces"]
        captured = capture_corrected(stdout)
        fragments = ("My", "Engines\\10yhistoriclengine\\evidence\\inventory\\file_inventory.json")
        for element in captured:
            with self.subTest(element=element[:40]):
                self.assertNotIn(element, fragments)
        self.assertIn("G:\\My Engines\\10yhistoriclengine\\evidence\\inventory\\file_inventory.json",
                      captured)


if __name__ == "__main__":
    unittest.main()
