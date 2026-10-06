"""Canonical row construction: mapping, verbatim retention, provenance (D05 §2.1, §3.1, §8, §10)."""

from __future__ import annotations

import unittest
from decimal import Decimal

from tests import support
from nse_engine import contract
from nse_engine.provenance import tool_fingerprint
from nse_engine.rows import strict_decimal, strict_integer


class FieldMapTests(unittest.TestCase):
    def test_map_columns_match_the_governed_headers_exactly(self):
        # Every governed source column is referenced, and no column outside the governed
        # headers is referenced. (TIMESTAMP legitimately feeds both business_date and
        # raw_biz_dt; TradDt feeds business_date and BizDt feeds raw_biz_dt.)
        for family_index, header in (
            (1, contract.LEGACY_HEADER_FIELDS),
            (2, contract.UDIFF_HEADER_FIELDS),
        ):
            columns = [
                entry[family_index] for entry in contract.CANONICAL_FIELD_MAP if entry[family_index] is not None
            ]
            self.assertEqual(set(columns), set(header))

    def test_map_keys_are_unique(self):
        keys = [entry[0] for entry in contract.CANONICAL_FIELD_MAP]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(tuple(keys), contract.CANONICAL_FIELDS)

    def test_typed_verbatim_and_derived_fields_partition_the_canonical_fields(self):
        typed = contract.DECIMAL_FIELDS + contract.INTEGER_FIELDS
        parts = typed + contract.VERBATIM_FIELDS + contract.DERIVED_FIELDS
        self.assertEqual(sorted(parts), sorted(contract.CANONICAL_FIELDS))
        self.assertEqual(len(set(parts)), len(parts))

    def test_business_date_source_columns_are_the_governed_ones(self):
        entry = [item for item in contract.CANONICAL_FIELD_MAP if item[0] == "business_date"][0]
        self.assertEqual(entry, ("business_date", "TIMESTAMP", "TradDt"))
        self.assertEqual(contract.DERIVED_FIELDS, ("business_date",))

    def test_engine_module_set_matches_the_package(self):
        import os

        package_dir = os.path.join(support.SRC_DIR, "nse_engine")
        actual = sorted(
            name[:-3] for name in os.listdir(package_dir) if name.endswith(".py")
        )
        self.assertEqual(sorted(contract.ENGINE_MODULES), actual)


class GoldenLegacyRowTests(unittest.TestCase):
    """First published legacy row (2016-09-20) reproduced field by field."""

    def setUp(self):
        self.build = support.build_sample(
            "FIX-UD-ROW-SAMPLE-01__sample_legacy_2016-09-20.csv"
        )
        self.row = self.build.rows[0]

    def test_identity_fields(self):
        self.assertEqual(self.row.format_family, "legacy13")
        self.assertEqual(self.row.security_isin, "INE144J01027")
        self.assertEqual(self.row.isin_normalized, "INE144J01027")
        self.assertEqual(self.row.isin_validity, "VALID")
        self.assertEqual(self.row.listing_symbol, "20MICRONS")
        self.assertEqual(self.row.series, "EQ")
        self.assertIsNone(self.row.security_name)  # absent in the legacy family
        expected_keys = tuple(
            key for key in contract.CANONICAL_FIELDS if key not in contract.DERIVED_FIELDS
        )
        self.assertEqual(tuple(self.row.to_dict()["source_values"]), expected_keys)

    def test_prices_as_published_with_exact_decimals(self):
        self.assertEqual(
            [self.row.value(key) for key in contract.DECIMAL_FIELDS[:6]],
            ["37.4", "39", "33.9", "37", "36.8", "36.85"],
        )
        self.assertEqual(self.row.decimal("price_open"), Decimal("37.4"))
        self.assertEqual(self.row.decimal("price_high"), Decimal("39"))
        self.assertEqual(self.row.decimal("price_prev_close"), Decimal("36.85"))

    def test_quantities_and_value(self):
        self.assertEqual(self.row.integer("traded_quantity"), 191700)
        self.assertEqual(self.row.decimal("traded_value"), Decimal("6928949.55"))
        self.assertEqual(self.row.integer("trades_count"), 820)

    def test_family_absent_fields_are_none_not_blank(self):
        for key in ("security_name", "lot_size", "remarks", "segment", "source", "instrument_type",
                    "underlying_symbol", "expiry", "actual_expiry", "strike", "option_type",
                    "underlying_price", "settlement_price", "open_interest", "open_interest_change",
                    "session_id", "rsvd1", "rsvd2", "rsvd3", "rsvd4"):
            self.assertIsNone(self.row.value(key), key)

    def test_absent_field_source_column_is_recorded(self):
        self.assertEqual(self.row.to_dict()["listing_symbol_source_column"], "SYMBOL")

    def test_raw_line_retained_verbatim_with_line_number(self):
        self.assertEqual(self.row.line_number, 2)
        self.assertEqual(self.row.physical_width, 14)
        self.assertEqual(
            self.row.raw_line,
            "20MICRONS,EQ,37.4,39,33.9,37,36.8,36.85,191700,6928949.55,20-SEP-2016,820,"
            "INE144J01027,",
        )
        self.assertEqual(self.row.value("security_isin"), self.row.raw_line.split(",")[12])

    def test_units_provenance_note_always_present(self):
        self.assertEqual(self.row.units_provenance_note, contract.UNITS_PROVENANCE_NOTE)
        self.assertIn("not by in-file metadata", self.row.units_provenance_note)


class GoldenUdiffRowTests(unittest.TestCase):
    """First published UDiFF row (2024-07-08) reproduced field by field."""

    def setUp(self):
        self.build = support.build_sample("FIX-UD-ROW-SAMPLE-01__sample_udiff_2024-07-08.csv")
        self.row = self.build.rows[0]

    def test_identity_and_descriptive_fields(self):
        self.assertEqual(self.row.format_family, "udiff34")
        self.assertEqual(self.row.security_isin, "INE488B01017")
        self.assertEqual(self.row.listing_symbol, "20092")  # opaque FinInstrmId, verbatim
        self.assertEqual(self.row.value("series"), "EQ")
        self.assertEqual(self.row.security_name, "TASTY BITE EATABLES LTD")
        self.assertEqual(self.row.value("underlying_symbol"), "TASTYBITE")
        self.assertEqual(self.row.value("segment"), "CM")
        self.assertEqual(self.row.value("source"), "NSE")
        self.assertEqual(self.row.value("instrument_type"), "STK")
        self.assertEqual(self.row.value("session_id"), "F1")
        self.assertEqual(self.row.value("lot_size"), "1")
        self.assertEqual(self.row.value("remarks"), "")
        self.assertEqual(self.row.value("rsvd4"), "")
        self.assertEqual(self.row.to_dict()["listing_symbol_source_column"], "FinInstrmId")

    def test_numeric_fields_from_udiff_columns(self):
        self.assertEqual(self.row.decimal("price_open"), Decimal("10400.10"))
        self.assertEqual(self.row.decimal("price_close"), Decimal("10273.20"))
        self.assertEqual(self.row.value("settlement_price"), "10272.10")  # stored verbatim
        self.assertEqual(self.row.integer("traded_quantity"), 2793)
        self.assertEqual(self.row.decimal("traded_value"), Decimal("28877900.75"))
        self.assertEqual(self.row.integer("trades_count"), 1046)
        self.assertEqual(self.row.value("open_interest"), "")
        self.assertEqual(self.row.value("expiry"), "")

    def test_fininstrm_id_is_opaque_and_never_interpretted_as_isin(self):
        self.assertNotEqual(self.row.listing_symbol, self.row.security_isin)
        self.assertIn("D07-OPEN-7", self.row.governance_dependencies)
        self.assertNotIn(self.row.listing_symbol, self.row.security_isin)

    def test_governance_dependency_annotation_present(self):
        self.assertEqual(self.row.governance_dependencies, ("D07-OPEN-7",))


class BlankAndZeroDisciplineTests(unittest.TestCase):
    def test_blank_stays_blank_and_zero_is_meaningful(self):
        build = support.parse_synthetic(
            support.legacy_member(
                [
                    support.legacy_row(OPEN="0", HIGH="0", LOW="0", CLOSE="0", LAST="0", TOTTRDQTY="0", TOTTRDVAL="0", TOTALTRADES="0"),
                    support.legacy_row(ISIN="INE002A01018", OPEN="", HIGH="", TOTTRDQTY="", TOTTRDVAL="", TOTALTRADES=""),
                ]
            ),
            expected_source_date="2016-09-20",
        )
        zeros, blanks = build.rows
        self.assertEqual(zeros.decimal("price_open"), Decimal("0"))
        self.assertEqual(zeros.integer("traded_quantity"), 0)
        self.assertEqual(zeros.decimal("traded_value"), Decimal("0"))
        self.assertEqual(blanks.value("price_open"), "")
        self.assertIsNone(blanks.decimal("price_open"))
        self.assertIsNone(blanks.integer("traded_quantity"))
        self.assertIsNone(blanks.decimal("traded_value"))

    def test_unparseable_numeric_is_quarantined_not_coerced(self):
        build = support.parse_synthetic(
            support.legacy_member([support.legacy_row(TOTTRDVAL='"1,234.50"')]),
            expected_source_date="2016-09-20",
        )
        self.assertEqual(len(build.rows), 0)
        record = build.quarantined[0]
        self.assertEqual(record.reason_code, "numeric_field_unparseable")
        self.assertIn("TOTTRDVAL", record.reason_detail)
        self.assertIn("coercion is not permitted", record.reason_detail)

    def test_unparseable_integer_is_quarantined(self):
        build = support.parse_synthetic(
            support.udiff_member([support.udiff_row(TtlTradgVol="2793.0")]),
            expected_source_date="2024-07-08",
        )
        self.assertEqual(len(build.rows), 0)
        self.assertEqual(build.quarantined[0].reason_code, "numeric_field_unparseable")

    def test_strict_numeric_helpers_reject_non_literals(self):
        self.assertIsNone(strict_decimal("1e5"))
        self.assertIsNone(strict_decimal(" 37.4"))
        self.assertIsNone(strict_integer("820.0"))
        self.assertIsNone(strict_integer("+820"))
        self.assertEqual(strict_decimal("-0.5"), Decimal("-0.5"))
        self.assertEqual(strict_integer("-3"), -3)

    def test_quoted_numeric_is_kept_as_published_text(self):
        # The CSV layer removes the quotes; the published value is retained exactly.
        build = support.parse_synthetic(
            support.legacy_member([support.legacy_row(SYMBOL='"20MICRONS"')]),
            expected_source_date="2016-09-20",
        )
        self.assertEqual(build.rows[0].listing_symbol, "20MICRONS")


class ProvenanceTests(unittest.TestCase):
    def test_provenance_block_carries_every_d05_section_8_field(self):
        build = support.build_sample(
            "FIX-UD-ROW-SAMPLE-01__sample_udiff_2025-10-30.csv", run_id="w1-test-run"
        )
        row = build.rows[0]
        provenance = row.to_dict()["provenance"]
        self.assertEqual(
            sorted(provenance),
            [
                "archive_sha256",
                "archive_sha256_basis",
                "evidence_refs",
                "format_family",
                "member_name",
                "member_sha256_lf_text",
                "member_sha256_raw_bytes",
                "run_id",
                "source_archive",
                "spec_version",
                "tool_name",
                "tool_sha256",
                "tool_version",
            ],
        )
        self.assertEqual(provenance["spec_version"], contract.SPEC_VERSION)
        self.assertEqual(provenance["tool_version"], contract.TOOL_VERSION)
        self.assertEqual(provenance["tool_sha256"], tool_fingerprint())
        self.assertEqual(provenance["run_id"], "w1-test-run")
        self.assertEqual(provenance["member_name"], "FIX-UD-ROW-SAMPLE-01__sample_udiff_2025-10-30.csv")
        self.assertEqual(provenance["format_family"], "udiff34")
        self.assertEqual(provenance["archive_sha256"], None)
        self.assertIn("not-supplied", provenance["archive_sha256_basis"])
        self.assertEqual(provenance["evidence_refs"], ["FIX-UD-ROW-SAMPLE-01"])

    def test_member_hashes_match_the_dual_hash_convention(self):
        from nse_engine.provenance import dual_hash

        name = "FIX-UD-ROW-SAMPLE-01__sample_legacy_2024-07-05.csv"
        raw_sha, lf_sha = dual_hash(support.fixture_bytes(name))
        build = support.build_sample(name)
        provenance = build.rows[0].provenance
        self.assertEqual(provenance.member_sha256_raw_bytes, raw_sha)
        self.assertEqual(provenance.member_sha256_lf_text, lf_sha)

    def test_archive_hash_is_reported_when_supplied(self):
        source = support.synthetic_source(expected_source_date="2016-09-20")
        from nse_engine import SourceDescriptor, build_canonical

        described = SourceDescriptor(
            source_archive="cm20SEP2016bhav.csv.zip",
            member_name="cm20SEP2016bhav.csv",
            archive_sha256="0" * 64,
            archive_sha256_basis="D01-inventory",
            expected_source_date="2016-09-20",
            evidence_refs=("FIX-LEG-CENSUS-01",),
        )
        build = build_canonical(support.legacy_member([support.legacy_row()]), described)
        provenance = build.rows[0].provenance
        self.assertEqual(provenance.archive_sha256, "0" * 64)
        self.assertEqual(provenance.archive_sha256_basis, "D01-inventory")
        self.assertEqual(source.archive_sha256, None)


if __name__ == "__main__":
    unittest.main()
