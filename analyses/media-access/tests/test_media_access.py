"""Parser and summary edge cases for the media-access analysis, no network."""

import sys
import tempfile
import unittest
import zipfile
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from broadcast_analyze import compliance, official_check
from hwpx_table import read_tables
from kcmf_parse import ParseError, check_minutes, group_of, number, operator_rows, validate_operators


NS = ('xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
      'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"')
HEADER = [(0, 0, 3, 2, "구분"), (0, 2, 3, 1, "방송사업자명"), (0, 3, 1, 6, "장애인방송 편성실적 (%)"),
          (1, 3, 1, 2, "폐쇄자막방송"), (1, 5, 1, 2, "화면해설방송"), (1, 7, 1, 2, "한국수어방송")] + [
          (2, 3 + i, 1, 1, "목표" if i % 2 == 0 else "실적") for i in range(6)]


def values(row, cells):
    return [(row, 3 + i, 1, 1, text) for i, text in enumerate(cells)]


def table_xml(rows, cols, cells):
    by_row = {}
    for cell in cells:
        by_row.setdefault(cell[0], []).append(cell)
    trs = []
    for row in sorted(by_row):
        tcs = "".join(
            f'<hp:tc><hp:subList><hp:p><hp:run><hp:t>{text}</hp:t></hp:run></hp:p></hp:subList>'
            f'<hp:cellAddr colAddr="{c}" rowAddr="{r}"/><hp:cellSpan colSpan="{cs}" rowSpan="{rs}"/></hp:tc>'
            for r, c, rs, cs, text in sorted(by_row[row], key=lambda item: item[1]))
        trs.append(f"<hp:tr>{tcs}</hp:tr>")
    return f'<hp:p><hp:run><hp:tbl rowCnt="{rows}" colCnt="{cols}">{"".join(trs)}</hp:tbl></hp:run></hp:p>'


def make_hwpx(directory, tables):
    path = Path(directory) / "sample.hwpx"
    body = "".join(table_xml(*table) for table in tables)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("Contents/section0.xml", f"<hs:sec {NS}>{body}</hs:sec>")
    return path


def sample_tables(so_label="SO(2)", last_number="4", last_value="7.0"):
    first = HEADER + [(3, 0, 2, 1, "지상파(2)"), (3, 1, 1, 1, "1"), (3, 2, 1, 1, "가방송")] + values(
        3, ["100.0", "100.0", "10.0", "12.5", "7.0", "9.1"]) + [
        (4, 1, 1, 1, "2"), (4, 2, 1, 1, "<hp:markpenBegin/>나방송<hp:markpenEnd/>")] + values(
        4, ["100.0", "99.99", "10.0", "10.0", "7.0", "7.0"])
    # 둘째 표는 쪽이 바뀐 연속 표다. 보조 행과 사업자군 칸이 빈 연속 행을 함께 둔다.
    second = HEADER + [(3, 0, 2, 1, so_label), (3, 1, 2, 1, "3"), (3, 2, 1, 1, "다방송")] + values(
        3, ["70.0", "71.0", "7.0", "6.5", "4.0", "4.0"]) + [
        (4, 2, 1, 1, "다방송(스마트수어 포함)")] + values(4, ["-", "-", "-", "-", "4.0", "5.2"]) + [
        (5, 0, 1, 1, ""), (5, 1, 1, 1, last_number), (5, 2, 1, 1, "라방송")] + values(
        5, ["70.0", "72.0", "7.0", "7.0", "4.0", last_value])
    return [(5, 9, first), (6, 9, second)]


class HwpxTableTests(unittest.TestCase):
    def test_markpen_text_and_merged_cells_are_read(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = read_tables(make_hwpx(directory, sample_tables()))
        self.assertEqual(first.start(4, 2).text, "나방송")
        self.assertEqual(first.covering(4, 0).text, "지상파(2)")
        self.assertEqual(second.covering(4, 1).text, "3")


class ParseTests(unittest.TestCase):
    def parse(self, **changes):
        with tempfile.TemporaryDirectory() as directory:
            tables = read_tables(make_hwpx(directory, sample_tables(**changes)))
        rows, labels = operator_rows(2025, tables)
        validate_operators(2025, rows, labels)
        return rows, labels

    def test_number_keeps_digits_and_marks_not_applicable(self):
        self.assertEqual(number("12.50%", what="t"), "12.50")
        self.assertEqual(number("-", what="t"), "NA")
        self.assertEqual(number("", what="t"), "")
        self.assertEqual(number("95,300", what="t", upper=None), "95300")
        with self.assertRaises(ParseError):
            number("100.5", what="t")
        with self.assertRaises(ParseError):
            number("약 10", what="t")

    def test_group_labels_are_normalized(self):
        self.assertEqual(group_of("지상파  (48)"), ("지상파", 48))
        self.assertEqual(group_of("pp (16)"), ("PP", 16))
        with self.assertRaises(ParseError):
            group_of("IPTV(3)")

    def test_continuation_table_variant_row_and_counts(self):
        rows, labels = self.parse()
        self.assertEqual(labels, {"지상파": 2, "SO": 2})
        self.assertEqual([row["row_kind"] for row in rows], ["operator"] * 3 + ["variant", "operator"])
        self.assertEqual(rows[-1]["group"], "SO")
        self.assertEqual(rows[3]["cc_target"], "NA")
        self.assertEqual(rows[1]["operator"], "나방송")

    def test_count_mismatch_gap_and_missing_value_stop(self):
        for changes in ({"so_label": "SO(3)"}, {"last_number": "5"}, {"last_value": ""}):
            with self.subTest(changes=changes), self.assertRaises(ParseError):
                self.parse(**changes)

    def test_rerun_minutes_must_add_up(self):
        row = {"year": 2025, "operator": "가", "required_minutes": "100", "first_run_minutes": "80",
               "rerun_minutes": "20", "rerun_share_pct": "20.00"}
        check_minutes(row)
        check_minutes({**row, "first_run_minutes": "100", "rerun_minutes": "NA", "rerun_share_pct": "0.00"})
        with self.assertRaises(ParseError):
            check_minutes({**row, "rerun_minutes": "25"})
        with self.assertRaises(ParseError):
            check_minutes({**row, "rerun_share_pct": "25.00"})


class SummaryTests(unittest.TestCase):
    def rows(self):
        base = {"year": "2025", "row_kind": "operator", "group": "PP", "cc_target": "70.0",
                "ad_target": "5.0", "ad_actual": "5.0", "ksl_target": "3.0", "ksl_actual": "3.0"}
        return [
            {**base, "row_no": "1", "operator": "가", "cc_actual": "69.95"},
            {**base, "row_no": "2", "operator": "나", "cc_actual": "60.0"},
            {**base, "row_no": "3", "operator": "다", "cc_actual": "70.0"},
            {**base, "row_no": "3", "operator": "다(보조)", "row_kind": "variant", "cc_actual": "50.0"},
        ]

    def test_below_target_is_strict_and_variants_are_separate(self):
        cc = [row for row in compliance(self.rows(), [2025]) if row["service"] == "cc"][0]
        self.assertEqual((cc["operators"], cc["below_target"]), (3, 2))
        self.assertEqual((cc["shortfall_under_0_1pctp"], cc["shortfall_1pctp_or_more"]), (1, 1))
        self.assertEqual(cc["largest_shortfall_pctp"], "10.0")
        self.assertEqual(cc["variant_rows_below"], 1)

    def test_official_mean_matches_after_truncation(self):
        official = [{"year": "2025", "official_group": "일반PP(10개사)", "operators": "3", "service": "cc",
                     "target": "70.00", "actual": "66.65"}]
        result = official_check(self.rows(), official)[0]
        self.assertEqual(result["computed_rounded"], "66.65")
        self.assertEqual(result["status"], "match_truncated")
        self.assertEqual(Decimal(result["computed_mean"]).quantize(Decimal("0.001")), Decimal("66.650"))


if __name__ == "__main__":
    unittest.main()
