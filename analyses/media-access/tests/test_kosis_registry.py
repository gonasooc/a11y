"""KOSIS registry checks and yearly summary edge cases, no key or network."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kosis_registry_collect import AGE_TABLE, AGES, SEX_TOTAL, TYPE_TABLE, TYPES, ApiError, age_rows, count, type_rows
from registry_analyze import by_year, context_check


def age_cell(year, age, code, value):
    return {"ORG_ID": "117", "TBL_ID": AGE_TABLE, "ITM_ID": "00", "PRD_SE": "A", "PRD_DE": year,
            "C1": age, "C1_NM": AGES[age], "C2": code, "C2_NM": TYPES[AGE_TABLE][code][1],
            "C3": SEX_TOTAL[AGE_TABLE][0], "UNIT_NM": "명", "DT": value, "LST_CHN_DE": "2026-04-10"}


def age_year(year, bands, total=None):
    """Same bands for all three types; total defaults to the band sum."""
    total = sum(int(value) for value in bands.values() if value.isdigit()) if total is None else total
    return [age_cell(year, age, code, value) for code in TYPES[AGE_TABLE]
            for age, value in {"000": str(total), **bands}.items()]


def type_cell(year, code, value):
    return {"ORG_ID": "117", "TBL_ID": TYPE_TABLE, "ITM_ID": "00", "PRD_SE": "A", "PRD_DE": year,
            "C1": code, "C1_NM": TYPES[TYPE_TABLE][code][1], "C2": "TT", "C2_NM": "계",
            "UNIT_NM": "명", "DT": value, "LST_CHN_DE": "2026-04-10"}


class CollectTests(unittest.TestCase):
    def test_count_keeps_integers_and_symbols(self):
        self.assertEqual(count("449269"), "449269")
        self.assertEqual(count("-"), "")
        with self.assertRaises(ApiError):
            count("12.5")

    def test_absent_band_is_allowed_when_bands_add_up(self):
        rows, unallocated = age_rows(age_year("2025", {"020": "10", "280": "6"}), ["2025"])
        self.assertEqual((len(rows), unallocated), (9, {}))

    def test_gap_is_recorded_only_without_100_plus_and_unknown(self):
        _, unallocated = age_rows(age_year("2014", {"020": "10", "280": "5"}, total=17), ["2014"])
        self.assertEqual(unallocated, {"2014": {"all": 2, "visual": 2, "hearing": 2}})
        for bands in ({"020": "10", "450": "1"}, {"020": "10", "500": "1"}):
            with self.subTest(bands=bands), self.assertRaises(ApiError):
                age_rows(age_year("2016", bands, total=20), ["2016"])

    def test_bands_over_total_missing_total_and_duplicates_stop(self):
        cases = [
            age_year("2025", {"020": "10", "280": "6"}, total=15),
            age_year("2025", {"020": "10"}, total="-"),
            age_year("2025", {"020": "10"}) + [age_cell("2025", "020", "CHU03", "10")],
            [{**row, "C2_NM": "청각"} if row["C2"] == "CHU03" else row for row in age_year("2025", {"020": "1"})],
            age_year("2025", {"020": "1"}) + [age_cell("2024", "000", "CHU03", "1")],
        ]
        for rows in cases:
            with self.assertRaises(ApiError):
                age_rows(rows, ["2025"])

    def test_type_table_keeps_missing_cells_and_checks_sex(self):
        rows = type_rows([type_cell("2025", "CHUT0", "100"), type_cell("2025", "CHU041", "20")], ["2025"])
        self.assertEqual([(row["type"], row["value"]) for row in rows], [("hearing", "20"), ("all", "100")])
        with self.assertRaises(ApiError):
            type_rows([{**type_cell("2025", "CHUT0", "100"), "C2": "1"}], ["2025"])


def saved(year, kind, age, value, table=AGE_TABLE):
    return {"table_id": table, "year": year, "type": kind, "age_code": age, "value": value}


class SummaryTests(unittest.TestCase):
    def rows(self):
        rows = []
        for kind, cells in (("all", {"000": "21", "020": "8", "280": "10", "500": "3"}),
                            ("hearing", {"000": "11", "020": "3", "280": "5"}),
                            ("visual", {"000": "10", "020": "5", "280": "5"})):
            rows += [saved("2014", kind, age, value) for age, value in cells.items()]
        return rows + [saved("2014", "all", "", "21", TYPE_TABLE), saved("2014", "hearing", "", "12", TYPE_TABLE)]

    def test_unknown_age_is_not_older_and_gap_gives_upper_share(self):
        series = {row["type"]: row for row in by_year(self.rows())}
        self.assertEqual((series["all"]["age65_plus"], series["all"]["age65_plus_share_pct"]), (10, "47.6"))
        self.assertEqual((series["all"]["age_under65"], series["all"]["age_unknown"], series["all"]["unallocated"]), (8, 3, 0))
        self.assertEqual((series["hearing"]["age_under65"], series["hearing"]["age_unknown"]), (3, 0))
        hearing = series["hearing"]
        self.assertEqual((hearing["unallocated"], hearing["age65_plus_share_pct"], hearing["age65_plus_share_upper_pct"]),
                         (3, "45.5", "72.7"))
        self.assertEqual(hearing["share_of_all_pct"], "52.4")
        self.assertEqual([series[kind]["n001_status"] for kind in ("all", "hearing", "visual")],
                         ["match", "differ", "unavailable"])

    def test_document_values_are_compared_not_enforced(self):
        facts = [{"survey_year": "2014", "indicator": "registered_by_type", "population": "hearing", "value": "11"},
                 {"survey_year": "2014", "indicator": "registered_65plus_share", "population": "visual", "value": "49.9"},
                 {"survey_year": "2014", "indicator": "ad_rerun_limit", "population": "visual", "value": "25"}]
        checked = context_check(by_year(self.rows()), facts)
        self.assertEqual([row["status"] for row in checked], ["match", "differ"])


if __name__ == "__main__":
    unittest.main()
