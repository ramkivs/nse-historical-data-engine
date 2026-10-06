"""Non-gating validity flags (D05 §5), ISIN handling (D05 §5/§6.1) and the W1-DIV-1 record."""

from __future__ import annotations

import unittest

from tests import support
from nse_engine import contract
from nse_engine.rows import iso6166_check_digit, isin_validity, normalize_isin


class FlagVocabularyTests(unittest.TestCase):
    def test_flag_set_is_exactly_the_governed_seven(self):
        self.assertEqual(
            tuple(name for name, _sev, _ref in contract.VALIDITY_FLAGS),
            (
                "isin_invalid_checkdigit",
                "isin_invalid_length",
                "row_fieldcount_mismatch",
                "date_source_conflict",
                "bizdt_ne_traddt",
                "orphan_no_base_row",
                "overlay_qty_gt_base",
            ),
        )

    def test_no_flag_is_gating(self):
        self.assertEqual(contract.GATING_FLAG_NAMES, ())

    def test_severities_match_d05_section_5_verbatim(self):
        self.assertEqual(contract.FLAG_SEVERITY["isin_invalid_checkdigit"], "informational")
        self.assertEqual(contract.FLAG_SEVERITY["isin_invalid_length"], "informational")
        self.assertEqual(
            contract.FLAG_SEVERITY["row_fieldcount_mismatch"], "quarantine row-level, keep raw"
        )
        self.assertEqual(
            contract.FLAG_SEVERITY["date_source_conflict"], "informational, keep both"
        )
        self.assertEqual(contract.FLAG_SEVERITY["bizdt_ne_traddt"], "informational")
        self.assertEqual(contract.FLAG_SEVERITY["orphan_no_base_row"], "informational")
        self.assertEqual(
            contract.FLAG_SEVERITY["overlay_qty_gt_base"], "informational (additivity evidence)"
        )

    def test_every_flag_reference_points_at_a_governed_section(self):
        for name, severity, reference in contract.VALIDITY_FLAGS:
            self.assertTrue(severity)
            self.assertIn("D05", reference)
            self.assertTrue(contract.FLAG_REFERENCE[name])


class IsinHandlingTests(unittest.TestCase):
    def test_normalization_is_uppercase_and_strip_only(self):
        self.assertEqual(normalize_isin(" ine144j01027 "), "INE144J01027")
        self.assertEqual(normalize_isin("INE144J01027"), "INE144J01027")

    def test_iso6166_reference_vectors(self):
        # US0378331005 (Apple Inc.) is a published, valid ISIN example.
        self.assertEqual(iso6166_check_digit("US037833100"), 5)
        self.assertEqual(iso6166_check_digit("INE144J0102"), 7)
        self.assertEqual(isin_validity("INE144J01027"), "VALID")

    def test_invalid_length_flag_is_emitted_and_row_retained(self):
        build = support.parse_synthetic(
            support.legacy_member([support.legacy_row(ISIN="INE144J0102")]),
            expected_source_date="2016-09-20",
        )
        self.assertEqual(len(build.rows), 1)
        row = build.rows[0]
        self.assertEqual(row.isin_validity, "INVALID_LEN")
        self.assertEqual(row.flag_names(), (contract.FLAG_ISIN_INVALID_LENGTH,))
        self.assertEqual(row.value("security_isin"), "INE144J0102")  # stored verbatim

    def test_invalid_checkdigit_flag_is_emitted_and_row_retained(self):
        build = support.parse_synthetic(
            support.legacy_member([support.legacy_row(ISIN="INE144J01020")]),
            expected_source_date="2016-09-20",
        )
        row = build.rows[0]
        self.assertEqual(row.isin_validity, "INVALID_CHECKDIGIT")
        self.assertEqual(row.flag_names(), (contract.FLAG_ISIN_INVALID_CHECKDIGIT,))
        self.assertIn("informational", row.flags[0].severity)
        self.assertIn("never implies non-security", row.flags[0].detail)

    def test_blank_isin_stays_blank_without_a_flag(self):
        build = support.parse_synthetic(
            support.legacy_member([support.legacy_row(ISIN="")]),
            expected_source_date="2016-09-20",
        )
        row = build.rows[0]
        self.assertEqual(row.isin_validity, "BLANK")
        self.assertEqual(row.flag_names(), ())
        self.assertEqual(row.isin_normalized, "")

    def test_prefix_and_charset_categories_are_observations_not_flags(self):
        for value, expected in (("US0378331005", "INVALID_PREFIX"), ("IN00000000AB", "INVALID_CHARSET")):
            with self.subTest(isin=value):
                build = support.parse_synthetic(
                    support.legacy_member([support.legacy_row(ISIN=value)]),
                    expected_source_date="2016-09-20",
                )
                self.assertEqual(build.rows[0].isin_validity, expected)
                self.assertEqual(build.rows[0].flag_names(), ())

    def test_isin_validity_never_gates_row_retention(self):
        rows = [
            support.legacy_row(ISIN="INE144J01020"),  # invalid check digit
            support.legacy_row(ISIN="INE144J0102"),  # invalid length
            support.legacy_row(ISIN=""),  # blank
            support.legacy_row(ISIN="INE002A01018"),  # valid
        ]
        build = support.parse_synthetic(
            support.legacy_member(rows), expected_source_date="2016-09-20"
        )
        self.assertEqual(len(build.rows), 4)
        self.assertEqual(len(build.quarantined), 0)


class EvidenceDivergenceW1Div1Tests(unittest.TestCase):
    """W1-DIV-1: the governed flag cannot reproduce the D03-era census formula.

    D05 §5 defines the flag as "ISIN fails mod-10 check digit"; the published census figure
    (215,393 legacy rows) was produced by the D03 evidence tool, whose routine summed over
    ISIN characters 2..11 instead of the ISO 6166 body (characters 1..11) — it drops the
    leading country-code character and shifts the Luhn doubling parity. W1 implements the
    governed definition and records the divergence instead of reproducing the artifact.
    """

    @staticmethod
    def d03_era_formula(isin: str) -> bool:
        """The D03 evidence tool's check (body = isin[1:11]) — recorded, never used by W1."""
        body = isin[1:11]
        digits = []
        for char in body.upper():
            if char.isdigit():
                digits.append(char)
            elif "A" <= char <= "Z":
                digits.append(str(ord(char) - 55))
            else:
                return False
        total = 0
        double = True
        for char in reversed("".join(digits)):
            value = int(char)
            if double:
                value *= 2
                if value > 9:
                    value -= 9
            total += value
            double = not double
        return (10 - total % 10) % 10 == int(isin[11])

    def test_divergence_is_recorded_in_the_contract(self):
        record = [item for item in contract.KNOWN_EVIDENCE_DIVERGENCES if item["id"] == "W1-DIV-1"]
        self.assertEqual(len(record), 1)
        self.assertIn("215,393", record[0]["governed_text"])
        self.assertIn("v[1:11]", record[0]["finding"])

    def test_known_valid_external_isin_check_digit_diverges_between_the_two_formulas(self):
        # ISO 6166 over the full 11-character body gives the published check digit 5;
        # the D03-era body (characters 2..11) gives 1 and therefore misclassifies the ISIN.
        self.assertEqual(iso6166_check_digit("US037833100"), 5)
        self.assertEqual(iso6166_check_digit("S037833100"), 1)
        self.assertFalse(self.d03_era_formula("US0378331005"))
        # the category vocabulary is Indian-ISIN scoped, so a US ISIN is INVALID_PREFIX,
        # which is an observation and carries no governed flag
        self.assertEqual(isin_validity("US0378331005"), "INVALID_PREFIX")

    def test_all_published_sample_rows_are_iso6166_valid(self):
        total = 0
        for name in support.PUBLISHED_SAMPLES:
            build = support.build_sample(name)
            for row in build.rows:
                total += 1
                self.assertEqual(
                    row.isin_validity,
                    "VALID",
                    "%s line %d ISIN %s" % (name, row.line_number, row.security_isin),
                )
        self.assertEqual(total, 3554)  # 1,588 legacy + 1,966 udiff published sample rows

    def test_w1_diverges_from_the_d03_era_formula_on_the_published_samples(self):
        w1_invalid = d03_invalid = total = 0
        for name in support.PUBLISHED_SAMPLES:
            build = support.build_sample(name)
            for row in build.rows:
                total += 1
                if row.isin_validity == "INVALID_CHECKDIGIT":
                    w1_invalid += 1
                if not self.d03_era_formula(row.security_isin):
                    d03_invalid += 1
        self.assertEqual(w1_invalid, 0)
        self.assertEqual(d03_invalid, 713)
        self.assertEqual(total, 3554)


if __name__ == "__main__":
    unittest.main()
