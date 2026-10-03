"""Edge cases for relative indices and source reconciliation, no network."""

import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kosis_analyze import decimal_or_none, difference_record, reconcile


class KosisAnalysisTests(unittest.TestCase):
    def test_statistical_symbol_is_not_zero_and_index_can_exceed_100(self):
        self.assertIsNone(decimal_or_none("-"))
        self.assertEqual(decimal_or_none("0.0"), Decimal(0))
        self.assertEqual(decimal_or_none("101.2"), Decimal("101.2"))

    def test_annual_average_uses_year_intervals_and_keeps_missing_years(self):
        result = difference_record([
            {"survey_year": "2016", "value": "70"},
            {"survey_year": "2018", "value": "74"},
        ], 2016, 2018)
        self.assertEqual(result["mean_annual_index_point_change"], "2")
        self.assertEqual(result["year_intervals"], 2)
        self.assertEqual(result["missing_numeric_years"], [2017])

    def test_missing_endpoint_does_not_create_a_change(self):
        rows = [{"survey_year": "2016", "value": ""}, {"survey_year": "2025", "value": "84.1"}]
        self.assertIsNone(difference_record(rows, 2016, 2025))

    def test_source_reconciliation_ignores_decimal_display_precision(self):
        base = {"indicator": "digital_informatization_overall", "population": "disabled",
                "survey_year": "2025", "unit": "index_general_population_100",
                "value": "84.10", "source_url": "https://example.org/report", "source_locator": "table 2"}
        api = {**base, "value": "84.1", "raw_value": "84.1", "table_id": "DT_12017N008", "last_modified": "2026-03-26"}
        self.assertEqual(reconcile([api], [base])[0]["status"], "match")
        self.assertEqual(reconcile([{**api, "value": "84.2", "raw_value": "84.2"}], [base])[0]["status"], "numeric_difference")
        self.assertEqual(reconcile([], [base])[0]["status"], "api_observation_absent")
        missing = reconcile([api], [{**base, "value": "-"}])[0]
        self.assertEqual(missing["status"], "report_value_nonnumeric")
        self.assertEqual(missing["api_minus_report_index_points"], "")

    def test_unit_difference_is_not_numerically_compared(self):
        base = {"indicator": "digital_informatization_overall", "population": "disabled",
                "survey_year": "2025", "unit": "index_general_population_100", "value": "84.1",
                "source_url": "https://example.org/report", "source_locator": "table 2"}
        api = {**base, "unit": "absolute_score", "raw_value": "84.1", "table_id": "DT_12017N008", "last_modified": "2026-03-26"}
        result = reconcile([api], [base])[0]
        self.assertEqual(result["status"], "unit_mismatch")
        self.assertEqual(result["api_minus_report_index_points"], "")


if __name__ == "__main__":
    unittest.main()
