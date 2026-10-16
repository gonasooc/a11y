"""OpenFiscal response parsing and keyword matching, no key or network."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openfiscal_collect import AMOUNT_FIELDS, SERVICE, TEXT_FIELDS, ApiError, matched, parse


def row(**changes):
    base = {field: "x" for field in TEXT_FIELDS}
    base.update({field: 0 for field in AMOUNT_FIELDS})
    base.update(changes)
    return base


def wrapped(payload):
    """The service returns a JSON string that holds the JSON document."""
    return json.dumps(json.dumps(payload, ensure_ascii=False)).encode()


def ok(rows, total=None):
    return {SERVICE: [{"head": [{"list_total_count": len(rows) if total is None else total},
                                {"RESULT": {"CODE": "INFO-000", "MESSAGE": "정상 처리되었습니다."}}]},
                      {"row": rows}]}


class ParseTests(unittest.TestCase):
    def test_wrapped_and_plain_json_both_parse(self):
        rows = [row(SACTV_NM="소외계층방송접근권보장")]
        self.assertEqual(parse(wrapped(ok(rows))), (1, rows, "INFO-000"))
        self.assertEqual(parse(json.dumps(ok(rows)).encode())[0], 1)

    def test_no_data_is_empty_and_errors_stop(self):
        self.assertEqual(parse(wrapped({"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}})),
                         (0, [], "INFO-200"))
        for payload in ({"RESULT": {"CODE": "ERROR-290", "MESSAGE": "인증키가 유효하지 않습니다."}}, {"other": []}):
            with self.subTest(payload=payload), self.assertRaises(ApiError):
                parse(wrapped(payload))

    def test_missing_fields_stop(self):
        broken = row()
        del broken["Y_YY_DFN_MEDI_KCUR_AMT"]
        with self.assertRaises(ApiError):
            parse(wrapped(ok([broken])))

    def test_keywords_look_at_unit_and_subproject_names(self):
        self.assertEqual(matched(row(ACTV_NM="방송콘텐츠 경쟁력 강화", SACTV_NM="OTT산업경쟁력강화")), ["OTT"])
        self.assertEqual(matched(row(ACTV_NM="미디어 다양성 및 공공성 확보", SACTV_NM="소외계층방송접근권보장")),
                         ["접근권", "소외계층"])
        self.assertEqual(matched(row(ACTV_NM=None, SACTV_NM="방송시장 경쟁상황 평가", PGM_NM="장애인")), [])


if __name__ == "__main__":
    unittest.main()
