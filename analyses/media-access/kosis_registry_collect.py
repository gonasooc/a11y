"""Collect KOSIS registered-disability counts by age for hearing and visual disability."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
# 키 로딩·HTTPS·오류 처리는 디지털포용법 수집기와 같은 모듈을 쓴다. 인증 코드를 두 벌 두지 않는다.
sys.path.insert(1, str(HERE.parent / "digital-inclusion"))
from api_common import ApiError, load_key, request_json, write_json  # noqa: E402


KEY_NAME = "KOSIS_DISABILITY_API_KEY"
ORG = "117"
AGE_TABLE, TYPE_TABLE = "DT_11761_N003", "DT_11761_N001"
META_URL = "https://kosis.kr/openapi/statisticsData.do"
DATA_URL = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
ITEM_ID, ITEM_NAME, UNIT = "00", "등록장애인수", "명"
# 유형 코드는 표마다 다르다. N001은 청각을 '청각ㆍ언어'(CHU45)의 하위 코드 CHU041에 둔다.
TYPES = {
    AGE_TABLE: {"CHUT0": ("all", "합계"), "CHU03": ("visual", "시각"), "CHU04": ("hearing", "청각")},
    TYPE_TABLE: {"CHUT0": ("all", "합계"), "CHU03": ("visual", "시각"), "CHU041": ("hearing", "청각")},
}
AGE_TOTAL, AGE_UNKNOWN = "000", "500"
OVER_100 = ("450", "460", "470", "480", "490")
# 연령은 5세 구간 상위 코드만 받는다. 각 세 코드는 구간의 하위 항목이다.
AGES = {
    "000": "합계", "020": "0-4세", "050": "5-9세", "070": "10-14세", "100": "15-19세",
    "120": "20-24세", "130": "25-29세", "150": "30-34세", "160": "35-39세", "180": "40-44세",
    "190": "45-49세", "210": "50-54세", "230": "55-59세", "260": "60-64세", "280": "65-69세",
    "310": "70-74세", "330": "75-79세", "360": "80-84세", "380": "85-89세", "410": "90-94세",
    "430": "95-99세", "450": "100-104세", "460": "105-109세", "470": "110-114세",
    "480": "115-119세", "490": "120-124세", "500": "해당없음",
}
SEX_TOTAL = {AGE_TABLE: ("1611713103150006A4428", "계"), TYPE_TABLE: ("TT", "계")}
DELAY_SECONDS = 3.1
MAX_CALLS = 20


def rows_of(payload, *, allow_no_data=False) -> list[dict]:
    if isinstance(payload, dict) and "err" in payload:
        code = str(payload["err"])
        code = code if re.fullmatch(r"[A-Z0-9_-]{1,32}", code) else "unrecognized"
        if allow_no_data and code == "30":
            return []
        raise ApiError(f"KOSIS error code: {code}")
    if not isinstance(payload, list) or any(not isinstance(row, dict) for row in payload):
        raise ApiError("Unexpected KOSIS response structure")
    return payload


def count(raw: str) -> str:
    """Keep integer counts as text; symbols become '' and are never replaced with zero."""
    if re.fullmatch(r"\d+", raw):
        return raw
    if re.search(r"\d", raw):
        raise ApiError("Non-integer KOSIS count")
    return ""


class Collector:
    def __init__(self, snapshot: str, refresh: bool):
        self.key = load_key(KEY_NAME)
        self.snapshot = snapshot
        self.refresh = refresh
        self.raw_dir = HERE / "raw" / "kosis" / snapshot
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.calls = 0
        self.last = 0.0
        self.requests = []

    def fetch(self, endpoint: str, params: dict, *, allow_no_data=False) -> list[dict]:
        identity = json.dumps([endpoint, params], ensure_ascii=False, sort_keys=True)
        digest = hashlib.sha256(identity.encode()).hexdigest()[:20]
        path = self.raw_dir / f"{params['tblId']}_{params.get('type', 'data')}_{digest}.json"
        if path.exists() and not self.refresh:
            raw = path.read_bytes()
            payload = json.loads(raw)
            fetched = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
            cached = True
        else:
            if self.calls >= MAX_CALLS:
                raise ApiError("KOSIS per-run request budget reached")
            time.sleep(max(0, DELAY_SECONDS - (time.monotonic() - self.last)))
            self.calls += 1
            payload, raw = request_json(endpoint, params, self.key)
            self.last = time.monotonic()
            # 인증·매개변수 오류 응답은 저장하지 않는다. 고친 요청이 오류 캐시를 다시 읽지 않게 한다.
            rows_of(payload, allow_no_data=allow_no_data)
            if path.exists() and path.read_bytes() != raw:
                previous = path.read_bytes()
                path.with_name(f"{path.stem}_{hashlib.sha256(previous).hexdigest()[:12]}.json").write_bytes(previous)
            path.write_bytes(raw)
            fetched = datetime.now(timezone.utc).isoformat()
            cached = False
        rows = rows_of(payload, allow_no_data=allow_no_data)
        self.requests.append({
            "endpoint": endpoint, "parameters": params, "fetched_at_utc": fetched,
            "response_sha256": hashlib.sha256(raw).hexdigest(), "raw_path": str(path.relative_to(HERE)),
            "cache_reused": cached, "row_count": len(rows),
        })
        return rows

    def metadata(self, table: str) -> dict:
        output = {}
        for kind in ("TBL", "PRD", "ITM", "CMMT"):
            params = {"method": "getMeta", "type": kind, "orgId": ORG, "tblId": table, "format": "json", "jsonVD": "Y"}
            if kind == "PRD":
                params["detail"] = "Y"
            output[kind] = self.fetch(META_URL, params, allow_no_data=kind == "CMMT")
        return output


def table_definition(metadata: dict) -> dict:
    if {row.get("PRD_SE") for row in metadata["PRD"] if "PRD_SE" in row} != {"년"}:
        raise ApiError("Unexpected KOSIS frequency; annual collection stopped")
    years = sorted(row["PRD_DE"] for row in metadata["PRD"] if "PRD_DE" in row)
    if not years or any(not re.fullmatch(r"\d{4}", year) for year in years):
        raise ApiError("Unexpected KOSIS annual periods")
    if [int(year) for year in years] != list(range(int(years[0]), int(years[-1]) + 1)):
        raise ApiError("KOSIS annual periods are not contiguous")
    items = [row for row in metadata["ITM"] if row.get("OBJ_ID") == "ITEM"]
    if [(row.get("ITM_ID"), row.get("ITM_NM"), row.get("UNIT_NM")) for row in items] != [(ITEM_ID, ITEM_NAME, UNIT)]:
        raise ApiError("KOSIS item metadata changed; review required")
    ages = {row["ITM_ID"]: row["ITM_NM"] for row in metadata["ITM"] if row.get("OBJ_ID") == "YRE" and not row.get("UP_ITM_ID")}
    types = {row["ITM_ID"]: row["ITM_NM"] for row in metadata["ITM"] if row.get("OBJ_ID") == "CHU"}
    sexes = {row["ITM_ID"]: row["ITM_NM"] for row in metadata["ITM"] if row.get("OBJ_ID") == "SBB"}
    if ages != AGES:
        raise ApiError("KOSIS age bands changed; review required")
    if any(types.get(code) != label for code, (_, label) in TYPES[AGE_TABLE].items()):
        raise ApiError("KOSIS disability type codes changed; review required")
    if sexes.get(SEX_TOTAL[AGE_TABLE][0]) != SEX_TOTAL[AGE_TABLE][1]:
        raise ApiError("KOSIS sex total code changed; review required")
    return {"table_name": metadata["TBL"][0]["TBL_NM"], "years": years, "comments": metadata["CMMT"]}


def output_row(table: str, row: dict, type_code: str, age: str = "") -> dict:
    return {
        "table_id": table, "year": row["PRD_DE"], "type": TYPES[table][type_code][0],
        "type_code": type_code, "age_code": age, "age_label": AGES[age] if age else "",
        "raw_value": str(row.get("DT", "")), "value": count(str(row.get("DT", ""))),
        "unit_source": row.get("UNIT_NM", ""), "last_modified": row.get("LST_CHN_DE", ""),
        "source_url": f"https://kosis.kr/statHtml/statHtml.do?orgId={ORG}&tblId={table}",
    }


def age_rows(rows: list[dict], years: list[str]) -> tuple[list[dict], dict]:
    seen = {}
    for row in rows:
        if (row.get("ORG_ID"), row.get("TBL_ID"), row.get("ITM_ID")) != (ORG, AGE_TABLE, ITEM_ID) or row.get("PRD_SE") not in {"Y", "A"}:
            raise ApiError("Unexpected KOSIS table, item, or frequency")
        if row.get("PRD_DE") not in years or row.get("C1") not in AGES or row.get("C2") not in TYPES[AGE_TABLE] or row.get("C3") != SEX_TOTAL[AGE_TABLE][0]:
            raise ApiError("Unexpected KOSIS observation")
        if row.get("C1_NM") != AGES[row["C1"]] or row.get("C2_NM") != TYPES[AGE_TABLE][row["C2"]][1] or row.get("UNIT_NM") != UNIT:
            raise ApiError("KOSIS code/label/unit mismatch")
        key = (row["PRD_DE"], row["C2"], row["C1"])
        if key in seen:
            raise ApiError("Duplicate KOSIS observation")
        seen[key] = output_row(AGE_TABLE, row, row["C2"], row["C1"])
    unallocated = {}
    for year in years:
        for code, (name, _) in TYPES[AGE_TABLE].items():
            total = seen.get((year, code, AGE_TOTAL))
            if total is None or total["value"] == "":
                raise ApiError(f"{year} {code}: KOSIS age total missing")
            parts = {age: cell for (y, c, age), cell in seen.items() if y == year and c == code and age != AGE_TOTAL}
            gap = int(total["value"]) - sum(int(cell["value"]) for cell in parts.values() if cell["value"])
            # 빠진 구간이 있어도 구간 합이 합계와 같으면 그 구간은 0이다.
            # 2007~2014년은 100세 이상 구간과 '해당없음'을 공표하지 않아 합계보다 작다. 이때만 차이를 따로 남긴다.
            if gap < 0 or (gap and set(parts) & {*OVER_100, AGE_UNKNOWN}):
                raise ApiError(f"{year} {code}: KOSIS age bands do not add up to the total")
            if gap:
                unallocated.setdefault(year, {})[name] = gap
    return [seen[key] for key in sorted(seen)], unallocated


def type_rows(rows: list[dict], years: list[str]) -> list[dict]:
    seen = {}
    for row in rows:
        if (row.get("ORG_ID"), row.get("TBL_ID"), row.get("ITM_ID")) != (ORG, TYPE_TABLE, ITEM_ID) or row.get("PRD_SE") not in {"Y", "A"}:
            raise ApiError("Unexpected KOSIS table, item, or frequency")
        if row.get("PRD_DE") not in years or row.get("C1") not in TYPES[TYPE_TABLE] or (row.get("C2"), row.get("C2_NM")) != SEX_TOTAL[TYPE_TABLE]:
            raise ApiError("Unexpected KOSIS observation")
        if row.get("C1_NM") != TYPES[TYPE_TABLE][row["C1"]][1] or row.get("UNIT_NM") != UNIT:
            raise ApiError("KOSIS code/label/unit mismatch")
        key = (row["PRD_DE"], row["C1"])
        if key in seen:
            raise ApiError("Duplicate KOSIS observation")
        seen[key] = output_row(TYPE_TABLE, row, row["C1"])
    # 대조용 표다. 빠진 셀은 만들지 않고 분석에서 '대조 불가'로 남긴다.
    return [seen[key] for key in sorted(seen)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=date.fromisoformat, default=date.today())
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    snapshot = args.snapshot.isoformat()
    collector = Collector(snapshot, args.refresh)
    definition = table_definition(collector.metadata(AGE_TABLE))
    years = definition["years"]
    common = {"method": "getList", "orgId": ORG, "format": "json", "jsonVD": "Y", "itmId": ITEM_ID,
              "prdSe": "Y", "startPrdDe": years[0], "endPrdDe": years[-1]}
    ages, unallocated = age_rows(collector.fetch(DATA_URL, {
        **common, "tblId": AGE_TABLE, "objL1": "+".join(AGES), "objL2": "+".join(TYPES[AGE_TABLE]),
        "objL3": SEX_TOTAL[AGE_TABLE][0]}), years)
    totals = type_rows(collector.fetch(DATA_URL, {
        **common, "tblId": TYPE_TABLE, "objL1": "+".join(TYPES[TYPE_TABLE]), "objL2": SEX_TOTAL[TYPE_TABLE][0]}), years)
    rows = ages + totals
    data = HERE / "data"
    csv_path = data / f"kosis_registry_{snapshot}.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    write_json(data / f"kosis_registry_manifest_{snapshot}.json", {
        "source": "보건복지부 「장애인현황」 KOSIS orgId=117",
        "snapshot": snapshot, "key_variable": KEY_NAME, "authentication": "successful",
        "csv_path": str(csv_path.relative_to(HERE)), "csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "rows": len(rows),
        "tables": {
            AGE_TABLE: {
                "table_name": definition["table_name"], "years": [years[0], years[-1]],
                "age_codes": AGES, "type_codes": {code: label for code, (_, label) in TYPES[AGE_TABLE].items()},
                "sex_code": SEX_TOTAL[AGE_TABLE][0], "comments": definition["comments"],
                "observed_cells": len(ages), "requested_cells": len(years) * len(AGES) * len(TYPES[AGE_TABLE]),
                "symbol_cells": sum(row["value"] == "" for row in ages),
                "unallocated_by_year": unallocated,
            },
            TYPE_TABLE: {
                "role": "연령 표의 유형별 합계를 대조하는 표", "sex_code": SEX_TOTAL[TYPE_TABLE][0],
                "type_codes": {code: label for code, (_, label) in TYPES[TYPE_TABLE].items()},
                "observed_cells": len(totals), "requested_cells": len(years) * len(TYPES[TYPE_TABLE]),
            },
        },
        "completeness_rule": "연령 표는 해마다 유형별 합계가 있고 5세 구간과 '해당없음'의 합이 합계와 같아야 한다. 100세 이상 구간과 '해당없음'이 모두 없는 해만 합계보다 작을 수 있고, 그 차이는 unallocated_by_year에 남긴다. 응답에 없는 구간은 만들지 않는다.",
        "requests": collector.requests, "credentials_excluded": True,
        "reference_documents": [
            "https://kosis.kr/openapi/devGuide/devGuide_0201List.do",
            "https://kosis.kr/openapi/devGuide/devGuide_060103List.do",
        ],
    })
    print(json.dumps({"status": "complete", "years": [years[0], years[-1]], "age_cells": len(ages),
                      "type_cells": len(totals), "live_calls": collector.calls}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except ApiError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None
    except Exception as exc:
        print(f"KOSIS collection failed ({type(exc).__name__}); request URL omitted", file=sys.stderr)
        raise SystemExit(1) from None
