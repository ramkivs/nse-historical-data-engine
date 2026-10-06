"""Header handling, authorized tolerance and fail-closed width validation (D05 §7, D07 §13-A)."""

from __future__ import annotations

import unittest

from tests import support
from nse_engine import contract
from nse_engine.errors import (
    BomNotToleratedError,
    CarriageReturnNotFollowedByLineFeedError,
    EmptyMemberError,
    HeaderUnrecognizedError,
    MemberDecodeError,
)
from nse_engine.parsing import detect_header


class HeaderDetectionTests(unittest.TestCase):
    def test_legacy_thirteen_field_header(self):
        spec = detect_header(contract.LEGACY_HEADER_FIELDS)
        self.assertEqual(spec.family, contract.FAMILY_LEGACY)
        self.assertEqual(spec.physical_width, 13)
        self.assertIsNone(spec.tolerance_applied)
        self.assertEqual(spec.row_physical_widths, (13,))

    def test_legacy_fourteen_field_trailing_empty_tolerated(self):
        spec = detect_header(contract.LEGACY_HEADER_FIELDS + ("",))
        self.assertEqual(spec.family, contract.FAMILY_LEGACY)
        self.assertEqual(spec.physical_width, 14)
        self.assertEqual(spec.tolerance_applied, "legacy13_trailing_empty_field")
        self.assertEqual(spec.row_physical_widths, (14,))

    def test_udiff_header(self):
        spec = detect_header(contract.UDIFF_HEADER_FIELDS)
        self.assertEqual(spec.family, contract.FAMILY_UDIFF)
        self.assertEqual(spec.physical_width, 34)
        self.assertIsNone(spec.tolerance_applied)

    def test_legacy_fourteen_field_header_with_non_empty_fourteenth_is_rejected(self):
        with self.assertRaises(HeaderUnrecognizedError):
            detect_header(contract.LEGACY_HEADER_FIELDS + ("EXTRA",))

    def test_udiff_header_with_trailing_empty_field_is_rejected(self):
        # The trailing-empty tolerance is a legacy-only serialization variation (D05 §7.1);
        # UDiFF width is strictly 34 (D07 §13-A "fail-closed width != 34").
        with self.assertRaises(HeaderUnrecognizedError):
            detect_header(contract.UDIFF_HEADER_FIELDS + ("",))

    def test_udiff_header_with_thirtythree_fields_is_rejected(self):
        with self.assertRaises(HeaderUnrecognizedError):
            detect_header(contract.UDIFF_HEADER_FIELDS[:33])

    def test_header_with_whitespace_padded_name_is_rejected(self):
        padded = tuple((" " + name) for name in contract.LEGACY_HEADER_FIELDS)
        with self.assertRaises(HeaderUnrecognizedError):
            detect_header(padded)

    def test_position_swap_is_rejected(self):
        swapped = (contract.LEGACY_HEADER_FIELDS[1],) + (contract.LEGACY_HEADER_FIELDS[0],) + contract.LEGACY_HEADER_FIELDS[2:]
        with self.assertRaises(HeaderUnrecognizedError):
            detect_header(swapped)

    def test_mapping_is_by_name_not_position(self):
        # A member whose header columns are permuted but named must fail closed rather than
        # being position-mapped into wrong canonical fields.
        reordered = tuple(reversed(contract.LEGACY_HEADER_FIELDS))
        with self.assertRaises(HeaderUnrecognizedError):
            detect_header(reordered)


class MemberWidthTests(unittest.TestCase):
    def test_legacy_trailing_empty_variant_parses(self):
        build = support.parse_synthetic(
            support.legacy_member([support.legacy_row()]), expected_source_date="2016-09-20"
        )
        self.assertEqual(len(build.rows), 1)
        self.assertEqual(build.rows[0].physical_width, 14)
        self.assertEqual(build.rows[0].value("series"), "EQ")
        self.assertEqual(build.rows[0].value("security_isin"), "INE144J01027")

    def test_legacy_thirteen_field_variant_parses(self):
        build = support.parse_synthetic(
            support.legacy_member([support.legacy_row()], trailing_empty_header=False),
            expected_source_date="2016-09-20",
        )
        self.assertEqual(len(build.rows), 1)
        self.assertEqual(build.rows[0].physical_width, 13)

    def test_legacy_row_width_mismatch_is_quarantined_not_coerced(self):
        # A 13-field row inside a 14-field member is a width mismatch: fail closed.
        data = support.legacy_member([support.legacy_row()], trailing_empty_header=True)
        text = data.decode("utf-8").replace("INE144J01027,\n", "INE144J01027\n", 1)
        build = support.parse_synthetic(text.encode("utf-8"), expected_source_date="2016-09-20")
        self.assertEqual(len(build.rows), 0)
        self.assertEqual(len(build.quarantined), 1)
        record = build.quarantined[0]
        self.assertEqual(record.reason_code, "row_fieldcount_mismatch")
        self.assertIn(contract.FLAG_ROW_FIELDCOUNT_MISMATCH, record.flag_names)
        self.assertEqual(record.physical_width, 13)

    def test_legacy_fourteenth_field_non_empty_is_quarantined(self):
        row = support.legacy_row() + ("LEAK",)
        build = support.parse_synthetic(
            support.legacy_member([row], trailing_empty_header=True),
            expected_source_date="2016-09-20",
        )
        self.assertEqual(len(build.rows), 0)
        self.assertEqual(build.quarantined[0].reason_code, "row_fieldcount_mismatch")
        self.assertIn("not empty", build.quarantined[0].reason_detail)

    def test_legacy_too_wide_row_is_quarantined(self):
        row = support.legacy_row() + ("", "EXTRA")
        build = support.parse_synthetic(
            support.legacy_member([row]), expected_source_date="2016-09-20"
        )
        self.assertEqual(len(build.rows), 0)
        self.assertEqual(build.quarantined[0].reason_code, "row_fieldcount_mismatch")

    def test_udiff_thirtythree_field_row_is_quarantined(self):
        build = support.parse_synthetic(
            support.udiff_member([support.udiff_row()[:-1]]), expected_source_date="2024-07-08"
        )
        self.assertEqual(len(build.rows), 0)
        self.assertEqual(build.quarantined[0].reason_code, "row_fieldcount_mismatch")
        self.assertEqual(build.quarantined[0].physical_width, 33)

    def test_udiff_thirtyfive_field_row_is_quarantined(self):
        build = support.parse_synthetic(
            support.udiff_member([support.udiff_row() + ("X",)]), expected_source_date="2024-07-08"
        )
        self.assertEqual(len(build.rows), 0)
        self.assertEqual(build.quarantined[0].reason_code, "row_fieldcount_mismatch")

    def test_quarantine_retains_raw_line_and_line_number(self):
        row = support.legacy_row()[:-1]
        build = support.parse_synthetic(
            support.legacy_member([support.legacy_row(), row, support.legacy_row(ISIN="INE002A01018")]),
            expected_source_date="2016-09-20",
        )
        self.assertEqual(len(build.rows), 2)
        self.assertEqual(len(build.quarantined), 1)
        record = build.quarantined[0]
        self.assertEqual(record.line_number, 3)
        self.assertTrue(record.raw_line.startswith("20MICRONS,EQ,37.4"))
        # quarantined raw lines remain available as evidence, and rows keep their identity
        self.assertEqual([r.line_number for r in build.rows], [2, 4])

    def test_empty_interior_line_is_quarantined_not_dropped(self):
        member = support.legacy_member([support.legacy_row()])
        text = member.decode("utf-8").replace("\n", "\n\n", 1)
        build = support.parse_synthetic(text.encode("utf-8"), expected_source_date="2016-09-20")
        self.assertEqual(len(build.rows), 1)
        self.assertEqual([q.reason_code for q in build.quarantined], ["empty_interior_line"])

    def test_malformed_csv_line_is_quarantined(self):
        # Characters after a closing quote violate RFC-4180: the csv layer raises, so the
        # line is quarantined with its raw text rather than best-effort mapped.
        member = support.legacy_member([support.legacy_row()])
        broken = member.decode("utf-8").replace('20MICRONS', '"20MICRONS"X', 1)
        build = support.parse_synthetic(broken.encode("utf-8"), expected_source_date="2016-09-20")
        self.assertEqual(len(build.rows), 0)
        self.assertEqual(build.quarantined[0].reason_code, "csv_syntax_error")
        self.assertTrue(build.quarantined[0].raw_line.startswith('"20MICRONS"X'))


class MemberLevelFailureTests(unittest.TestCase):
    def test_bom_is_not_tolerated(self):
        data = b"\xef\xbb\xbf" + support.legacy_member([support.legacy_row()])
        with self.assertRaises(BomNotToleratedError):
            support.parse_synthetic(data, expected_source_date="2016-09-20")

    def test_non_utf8_bytes_fail_loudly(self):
        data = support.legacy_member([support.legacy_row()]).replace(b"20MICRONS", b"20MICR\xd8NS")
        with self.assertRaises(MemberDecodeError):
            support.parse_synthetic(data, expected_source_date="2016-09-20")

    def test_bare_carriage_return_fails_closed(self):
        data = support.legacy_member([support.legacy_row()]).replace(b"37.4", b"37\r.4", 1)
        with self.assertRaises(CarriageReturnNotFollowedByLineFeedError):
            support.parse_synthetic(data, expected_source_date="2016-09-20")

    def test_empty_member_raises(self):
        with self.assertRaises(EmptyMemberError):
            support.parse_synthetic(b"", expected_source_date="2016-09-20")

    def test_unrecognized_header_raises_rather_than_best_effort(self):
        with self.assertRaises(HeaderUnrecognizedError):
            support.parse_synthetic(
                support.legacy_member([support.legacy_row()], header=["SYM", "SER", "O"]),
                expected_source_date="2016-09-20",
            )


class LineEndingTests(unittest.TestCase):
    def test_crlf_and_lf_members_are_content_identical(self):
        rows = [support.legacy_row(), support.legacy_row(ISIN="INE002A01018")]
        lf = support.legacy_member(rows, line_ending="\n")
        crlf = support.legacy_member(rows, line_ending="\r\n")
        lf_build = support.parse_synthetic(lf, expected_source_date="2016-09-20")
        crlf_build = support.parse_synthetic(crlf, expected_source_date="2016-09-20")

        def without_raw_member_hash(build):
            rows = []
            for row in build.rows:
                data = row.to_dict()
                data["provenance"]["member_sha256_raw_bytes"] = "<raw-bytes-hash>"
                rows.append(data)
            return rows

        self.assertEqual(without_raw_member_hash(lf_build), without_raw_member_hash(crlf_build))
        self.assertEqual(len(lf_build.rows), 2)
        self.assertEqual(len(crlf_build.rows), 2)
        # hashes differ for raw bytes, are identical for the LF-normalized text (D05 §9.2/§9.3)
        self.assertNotEqual(
            lf_build.parse.report.member_sha256_raw_bytes,
            crlf_build.parse.report.member_sha256_raw_bytes,
        )
        self.assertEqual(
            lf_build.parse.report.member_sha256_lf_text,
            crlf_build.parse.report.member_sha256_lf_text,
        )
        self.assertEqual(crlf_build.parse.report.crlf_line_endings, 3)
        self.assertEqual(lf_build.parse.report.crlf_line_endings, 0)
        # raw lines are retained LF-normalized, so CR is never smuggled into field values
        for row in crlf_build.rows:
            self.assertNotIn("\r", row.raw_line)


class QuoteHandlingTests(unittest.TestCase):
    def test_quoted_field_with_embedded_comma_is_one_record(self):
        row = support.udiff_row(FinInstrmNm='"ACME, INDUSTRIES LTD"')
        build = support.parse_synthetic(
            support.udiff_member([row]), expected_source_date="2024-07-08"
        )
        self.assertEqual(len(build.rows), 1)
        self.assertEqual(build.rows[0].value("security_name"), "ACME, INDUSTRIES LTD")
        self.assertEqual(build.rows[0].physical_width, 34)


if __name__ == "__main__":
    unittest.main()
