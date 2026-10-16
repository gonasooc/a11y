"""HWP record reading, 2012-2016 table parsing, and official-count checks, no network."""

import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from broadcast_analyze import AnalysisError
from broadcast_early_analyze import members, official_check
from hwp5_table import Compound, HwpError, para_text, section_tables
from hwpx_table import Cell, Table
from kmcc_parse import ParseError, layout, operator_rows, validate


def rec(tag, level, body=b""):
    return struct.pack("<I", tag | level << 10 | len(body) << 20) + body


def text(*parts):
    """Parts are strings or raw UTF-16 code units (ints)."""
    units = []
    for part in parts:
        units += [part] if isinstance(part, int) else [ord(ch) for ch in part]
    return struct.pack(f"<{len(units)}H", *units)


def cell(row, col, row_span=1, col_span=1):
    return b"\0" * 8 + struct.pack("<4H", col, row, col_span, row_span) + b"\0" * 8


def table_record(rows, cols):
    return b"\0" * 4 + struct.pack("<HH", rows, cols) + b"\0" * 4


class HwpRecordTests(unittest.TestCase):
    def test_cells_skip_nested_lists_and_wide_controls(self):
        stream = b"".join([
            rec(66, 0), rec(67, 1, text("본문")), rec(71, 1, b" lbt"), rec(77, 2, table_record(2, 2)),
            rec(72, 2, cell(0, 0, 1, 2)), rec(66, 2), rec(67, 3, text("구분")),
            # 셀 안 각주: 목록 머리와 글자가 더 깊어서 셀로 세지 않는다.
            rec(71, 3, b"  nf"), rec(72, 4, cell(0, 0, 0, 0)), rec(66, 4), rec(67, 5, text("각주")),
            rec(72, 2, cell(1, 0)), rec(66, 2), rec(67, 3, text("가", 11, *[0] * 7, "나", 30, "다", 13)),
            rec(72, 2, cell(1, 1)), rec(66, 2), rec(67, 3, text("1")), rec(66, 2), rec(67, 3, text("2")),
            rec(66, 0), rec(67, 1, text("끝")),
        ])
        (table,) = section_tables(stream, 0)
        self.assertEqual((table.rows, table.cols), (2, 2))
        self.assertEqual([(c.row, c.col, c.row_span, c.col_span, c.text) for c in table.cells],
                         [(0, 0, 1, 2, "구분"), (1, 0, 1, 1, "가나 다"), (1, 1, 1, 1, "12")])

    def test_out_of_bounds_cell_truncated_record_and_non_ole_stop(self):
        with self.assertRaises(HwpError):
            section_tables(rec(77, 2, table_record(1, 1)) + rec(72, 2, cell(0, 1)), 0)
        with self.assertRaises(HwpError):
            section_tables(rec(67, 1, text("가"))[:-1], 0)
        with self.assertRaises(HwpError):
            Compound(b"PK\3\4" + b"\0" * 600)

    def test_lone_surrogate_becomes_replacement(self):
        self.assertEqual(para_text(text("가", 0xD800, "나")), "가�나")


HEAD_2013 = [Cell(0, 0, 3, 1, "구분"), Cell(0, 1, 3, 1, "번호"), Cell(0, 2, 3, 1, "방송사업자명"),
             Cell(0, 3, 1, 6, "장애인방송 편성실적 (%)"), Cell(1, 3, 1, 2, "자막방송"),
             Cell(1, 5, 1, 2, "화면해설방송"), Cell(1, 7, 1, 2, "수화통역방송")] + [
             Cell(2, 3 + i, 1, 1, "목표치" if i % 2 == 0 else "실적치") for i in range(6)]


def values(row, cells, span=1):
    return [Cell(row, 3 + i, span, 1, value) for i, value in enumerate(cells)]


class ParseTests(unittest.TestCase):
    def test_misaligned_number_merge_is_not_a_variant(self):
        # 2013년 SO 표처럼 둘째 사업자명이 두 줄, 셋째 번호 칸이 그 아래 줄에서 시작한다.
        cells = HEAD_2013 + [Cell(3, 0, 4, 1, "SO(3)"), Cell(3, 1, 1, 1, "1"), Cell(3, 2, 1, 1, "가")] + values(
            3, ["30.0", "29.3", "3.0", "3.7", "1.0", "2.0"]) + [
            Cell(4, 1, 1, 1, "2"), Cell(4, 2, 2, 1, "나")] + values(4, ["30.0", "16.7", "3.0", "13.5", "1.0", "3.2"], 2) + [
            Cell(5, 1, 2, 1, "3"), Cell(6, 2, 1, 1, "다")] + values(6, ["30.0", "16.4", "3.0", "13.5", "1.0", "6.0"])
        table = Table(3, 7, 9, tuple(cells))
        rows, labels = operator_rows(2013, 39231, table, layout(table))
        validate(2013, rows, labels)
        self.assertEqual([(row["row_no"], row["row_kind"], row["operator"]) for row in rows],
                         [("1", "operator", "가"), ("2", "operator", "나"), ("3", "operator", "다")])
        self.assertEqual(labels, {"SO": 3})

    def test_shared_number_cell_marks_variant_and_short_labels_map(self):
        cells = HEAD_2013 + [Cell(3, 0, 2, 1, "보도(1)"), Cell(3, 1, 2, 1, "1"), Cell(3, 2, 1, 1, "가(창원)")] + values(
            3, ["30.0", "30.0", "3.0", "3.0", "1.0", "1.0"]) + [Cell(4, 2, 1, 1, "가(진주)")] + values(
            4, ["30.0", "20.0", "3.0", "3.0", "1.0", "1.0"])
        table = Table(2, 5, 9, tuple(cells))
        rows, labels = operator_rows(2013, 39231, table, layout(table))
        self.assertEqual([row["row_kind"] for row in rows], ["operator", "variant"])
        self.assertEqual((rows[0]["group"], labels), ("보도PP", {"보도PP": 1}))

    def test_2012_layout_skips_achievement_rate_and_uses_press_count(self):
        head = [Cell(0, 0, 2, 1, "구분"), Cell(0, 1, 2, 1, "사업자명[지역(총)국]")] + [
            Cell(0, 2 + 3 * i, 1, 3, f"{name}(%)") for i, name in enumerate(("자막방송", "화면해설방송", "수화통역방송"))] + [
            Cell(1, 2 + i, 1, 1, ("목표(A)", "실적(B)", "달성률(B/A)")[i % 3]) for i in range(9)]
        data = [Cell(2, 0, 1, 1, "1"), Cell(2, 1, 1, 1, "가방송")] + [
            Cell(2, 2 + i, 1, 1, value) for i, value in enumerate(
                ["100.0", "100.0", "100.0", "10.0", "11.2", "112.0", "5.0", "6.7", "134.0"])]
        table = Table(2, 3, 11, tuple(head + data))
        shape = layout(table)
        self.assertEqual(shape["fields"], {"cc_target": 2, "cc_actual": 3, "ad_target": 5, "ad_actual": 6,
                                           "ksl_target": 8, "ksl_actual": 9})
        rows, labels = operator_rows(2012, 37195, table, shape)
        self.assertEqual((rows[0]["group"], rows[0]["ksl_actual"], labels), ("지상파", "6.7", {"지상파": 50}))
        with self.assertRaises(ParseError):  # 표에는 1개사뿐이라 보도자료의 50개사와 다르다.
            validate(2012, rows, labels)

    def test_summary_table_without_targets_is_skipped(self):
        table = Table(0, 2, 3, (Cell(0, 0, 1, 1, "구  분"), Cell(0, 1, 1, 2, "편성목표 달성 사업자명"),
                                Cell(1, 1, 1, 1, "자막"), Cell(1, 2, 1, 1, "계")))
        self.assertIsNone(layout(table))


def operator(row_no, name, group="지상파", cc=("100.0", "100.0"), ad=("10.0", "10.0"), ksl=("5.0", "5.0")):
    return {"year": "2016", "row_kind": "operator", "row_no": str(row_no), "operator": name, "group": group,
            "cc_target": cc[0], "cc_actual": cc[1], "ad_target": ad[0], "ad_actual": ad[1],
            "ksl_target": ksl[0], "ksl_actual": ksl[1]}


class OfficialCheckTests(unittest.TestCase):
    def rows(self):
        central = [operator(i + 1, name) for i, name in enumerate(("KBS", "㈜문화방송", "㈜SBS", "한국교육방송공사"))]
        return central + [operator(5, "원주문화방송㈜", ad=("10.0", "9.9")), operator(1, "㈜채널에이", "종편PP", cc=("100.0", "99.0"))]

    def test_groups_and_any_service_counts(self):
        statements = [
            {"year": "2016", "group": "all", "service": "any", "operators": "6", "below_target": "2"},
            {"year": "2016", "group": "regional", "service": "ad", "operators": "1", "below_target": "1"},
            {"year": "2016", "group": "news_general_pp", "service": "any", "operators": "1", "below_target": "0"},
        ]
        self.assertEqual([row["status"] for row in official_check(self.rows(), statements)], ["match", "match", "differ"])

    def test_central_must_be_the_four_networks(self):
        rows = self.rows()
        rows[1]["operator"] = "가방송"
        with self.assertRaises(AnalysisError):
            members(rows, "central")


if __name__ == "__main__":
    unittest.main()
