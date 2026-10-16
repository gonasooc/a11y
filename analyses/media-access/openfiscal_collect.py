"""Scan OpenFiscal sub-project budgets for disability media-access and OTT support lines."""

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
# 키 로딩·HTTPS·오류 처리는 디지털포용법 수집기와 같은 모듈을 쓴다.
sys.path.insert(1, str(HERE.parent / "digital-inclusion"))
from api_common import ApiError, load_key, request_json, write_json  # noqa: E402


KEY_NAME = "OPENFISCAL_BUDGET_API_KEY"
SERVICE = "TotalExpenditure5"
ENDPOINT = f"https://openapi.openfiscaldata.go.kr/{SERVICE}"
# 전기통신사업법 제22조의10(OTT 장애인 시청 편의, 경비 지원)은 2024-01-19 시행이라 2024년 예산부터 본다.
SCAN_YEARS = ("2024", "2025", "2026")
# 방송통신발전기금은 과학기술정보통신부 소관으로 잡힌다. 방송미디어통신위원회는 2025-10 개편 뒤 이름이다.
OFFICES = ("과학기술정보통신부", "방송통신위원회", "방송미디어통신위원회", "문화체육관광부")
SERIES_YEARS = tuple(str(year) for year in range(2018, 2027))
SERIES_SUBPROJECT = "소외계층방송접근권보장"
UNIT = "미디어 다양성 및 공공성 확보"
KEYWORDS = ("OTT", "장애", "자막", "화면해설", "수어", "수화", "접근권", "배리어", "소외계층")
TEXT_FIELDS = ("FSCL_YY", "OFFC_NM", "FSCL_NM", "ACCT_NM", "FLD_NM", "SECT_NM", "PGM_NM", "ACTV_NM",
               "SACTV_NM", "BZ_CLS_NM", "FIN_DE_EP_NM", "ANEXP_INQ_STND_CD")
# 금액은 원문 필드 이름 그대로 둔다. 단위 표기는 없고, 이름의 KCUR로 보아 천원으로 추정한다.
AMOUNT_FIELDS = ("Y_PREY_FIRST_KCUR_AMT", "Y_PREY_FNL_FRC_AMT", "Y_YY_MEDI_KCUR_AMT", "Y_YY_DFN_MEDI_KCUR_AMT")
PAGE_SIZE = 1000
DELAY_SECONDS = 1.1
MAX_CALLS = 80


class Collector:
    def __init__(self, snapshot: str, refresh: bool):
        self.key = load_key(KEY_NAME)
        self.raw_dir = HERE / "raw" / "openfiscal" / snapshot
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.refresh = refresh
        self.calls = 0
        self.last = 0.0
        self.requests = []

    def page(self, params: dict) -> tuple[int, list[dict]]:
        identity = json.dumps(params, ensure_ascii=False, sort_keys=True)
        path = self.raw_dir / f"{SERVICE}_{hashlib.sha256(identity.encode()).hexdigest()[:20]}.json"
        if path.exists() and not self.refresh:
            raw, cached = path.read_bytes(), True
        else:
            if self.calls >= MAX_CALLS:
                raise ApiError("OpenFiscal per-run request budget reached")
            time.sleep(max(0, DELAY_SECONDS - (time.monotonic() - self.last)))
            self.calls += 1
            _, raw = request_json(ENDPOINT, params, self.key)
            self.last = time.monotonic()
            parse(raw)  # 오류 응답은 저장하지 않는다.
            path.write_bytes(raw)
            cached = False
        total, rows, code = parse(raw)
        self.requests.append({"parameters": params, "response_sha256": hashlib.sha256(raw).hexdigest(),
                              "raw_path": str(path.relative_to(HERE)), "cache_reused": cached,
                              "result_code": code, "list_total_count": total, "row_count": len(rows)})
        return total, rows

    def all_rows(self, params: dict) -> list[dict]:
        rows, index = [], 1
        while True:
            total, found = self.page({**params, "Type": "json", "pIndex": str(index), "pSize": str(PAGE_SIZE)})
            rows += found
            if len(rows) >= total or not found:
                break
            index += 1
        if len(rows) != total:
            raise ApiError(f"OpenFiscal rows {len(rows)} differ from list_total_count {total}")
        keys = [tuple(row.get(field) for field in TEXT_FIELDS + AMOUNT_FIELDS) for row in rows]
        if len(keys) != len(set(keys)):
            raise ApiError("Duplicate OpenFiscal rows")
        return rows


def parse(raw: bytes) -> tuple[int, list[dict], str]:
    """The body is a JSON string that itself holds JSON. INFO-200 means no matching data."""
    payload = json.loads(raw.decode("utf-8-sig"))
    if isinstance(payload, str):
        payload = json.loads(payload)
    if isinstance(payload, dict) and "RESULT" in payload:
        code = str(payload["RESULT"].get("CODE", ""))
        if code == "INFO-200":
            return 0, [], code
        raise ApiError(f"OpenFiscal result code: {code if re.fullmatch(r'[A-Z]+-[0-9]+', code) else 'unrecognized'}")
    body = payload.get(SERVICE) if isinstance(payload, dict) else None
    if not isinstance(body, list) or not body or "head" not in body[0]:
        raise ApiError("Unexpected OpenFiscal response structure")
    head = body[0]["head"]
    total = head[0]["list_total_count"]
    code = head[1]["RESULT"]["CODE"]
    if code != "INFO-000":
        raise ApiError(f"OpenFiscal result code: {code}")
    rows = body[1]["row"] if len(body) > 1 else []
    if any(set(TEXT_FIELDS + AMOUNT_FIELDS) - set(row) for row in rows):
        raise ApiError("OpenFiscal row fields changed; review required")
    return int(total), rows, code


def matched(row: dict) -> list[str]:
    names = f"{row.get('ACTV_NM') or ''} {row.get('SACTV_NM') or ''}"
    return [word for word in KEYWORDS if word in names]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=date.fromisoformat, default=date.today())
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    snapshot = args.snapshot.isoformat()
    collector = Collector(snapshot, args.refresh)
    kept, scans = {}, []

    def keep(row: dict, reason: str) -> None:
        key = tuple(row.get(field) for field in TEXT_FIELDS + AMOUNT_FIELDS)
        record = kept.setdefault(key, {**{field: "" if row.get(field) is None else str(row[field])
                                          for field in TEXT_FIELDS + AMOUNT_FIELDS}, "included_by": []})
        if reason not in record["included_by"]:
            record["included_by"].append(reason)

    common = {"ANEXP_INQ_STND_CD": "1"}
    for year in SCAN_YEARS:
        for office in OFFICES:
            rows = collector.all_rows({**common, "FSCL_YY": year, "BDG_FND_DIV_CD": "0", "OFFC_NM": office})
            hits = [row for row in rows if matched(row)]
            for row in hits:
                keep(row, "keyword:" + "+".join(matched(row)))
            for row in rows:
                if row.get("ACTV_NM") == UNIT:
                    keep(row, "unit")
            scans.append({"year": year, "office": office, "rows_scanned": len(rows), "keyword_rows": len(hits)})
            print(f"{year} {office}: {len(rows)}행, 키워드 {len(hits)}행", flush=True)
    for year in SERIES_YEARS:
        for row in collector.all_rows({**common, "FSCL_YY": year, "BDG_FND_DIV_CD": "5", "SACTV_NM": SERIES_SUBPROJECT}):
            keep(row, "series")
    records = sorted(kept.values(), key=lambda row: (row["FSCL_YY"], row["OFFC_NM"], row["PGM_NM"], row["ACTV_NM"], row["SACTV_NM"]))
    for record in records:
        record["included_by"] = ";".join(record["included_by"])
    csv_path = HERE / "data" / f"openfiscal_access_lines_{snapshot}.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    write_json(HERE / "data" / f"openfiscal_manifest_{snapshot}.json", {
        "source": "열린재정(openfiscaldata.go.kr) Open API TotalExpenditure5, 총지출 기준 세부사업 예산",
        "snapshot": snapshot, "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "key_variable": KEY_NAME, "credentials_excluded": True,
        "csv_path": str(csv_path.relative_to(HERE)), "csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "rows": len(records), "keywords": KEYWORDS, "unit": UNIT, "series_subproject": SERIES_SUBPROJECT,
        "scans": scans, "requests": collector.requests,
        "amount_note": "금액 필드는 원문 이름 그대로 둔다. 단위 표기가 없고 이름의 KCUR로 보아 천원으로 추정한다.",
        "access_note": ("API 호스트(openapi.openfiscaldata.go.kr)에는 robots.txt가 없다. 누리집(www) robots.txt는 일반 로봇에 "
                        "전체 경로를 막아 약관 페이지를 자동으로 받지 않았다. 열린재정 Open API 약관 원문은 직접 확인하지 못했고, "
                        "사용자가 인증키를 발급받으며 동의했다(2026-10-17). 원응답은 raw/에 두고 Git에서 제외한다."),
    })
    print(json.dumps({"status": "complete", "rows": len(records), "live_calls": collector.calls}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except ApiError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None
    except Exception as exc:
        print(f"OpenFiscal collection failed ({type(exc).__name__}); request URL omitted", file=sys.stderr)
        raise SystemExit(1) from None
