"""Collect narrowly selected PPS kiosk records; credentials never enter the CLI.

Examples (run from the repository root):
  python3 analyses/digital-inclusion/pps_collect.py --probe
  python3 analyses/digital-inclusion/pps_collect.py --kind registrations \
      --term 무인민원발급기 --start 2024-01-01 --end 2026-09-30

Sources: data.go.kr/15129471 and its official reference document version 1.3.
Raw response caches are gitignored. CSV files deliberately omit personal contact
details and company registration numbers; this analysis identifies public firms
by names, with that limitation recorded in its output.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from api_common import ApiError, load_key, request_json, write_json


HERE = Path(__file__).resolve().parent
BASE = "https://apis.data.go.kr/1230000/at/ShoppingMallPrdctInfoService/"
OPERATIONS = {
    "registrations": "getShoppingMallPrdctInfoList",
    "deliveries": "getDlvrReqDtlInfoList",
}
REG_FIELDS = [
    "rgstDt", "shopngCntrctNo", "shopngCntrctSno", "prdctIdntNo",
    "cntrctCorpNm", "prdctMakrNm", "entrprsDivNm", "cntrctMthdNm",
    "prdctClsfcNo", "prdctClsfcNoNm", "dtilPrdctClsfcNo",
    "dtilPrdctClsfcNoNm", "prdctSpecNm", "cntrctPrceAmt", "prdctUnit",
    "cntrctDate", "cntrctBgnDate", "cntrctEndDate", "prodctCertList",
]
DEL_FIELDS = [
    "dlvrReqNo", "dlvrReqChgOrd", "dlvrReqRcptDate", "prdctSno",
    "cntrctNo", "cntrctChgOrd", "prdctIdntNo", "prdctIdntNoNm",
    "corpNm", "corpEntrprsDivNmNm", "prdctClsfcNo", "prdctClsfcNoNm",
    "dtilPrdctClsfcNo", "dtilPrdctClsfcNoNm", "prdctQty", "prdctAmt",
    "prdctUnit", "prdctUprc", "dlvrReqQty", "dlvrReqAmt", "incdecQty",
    "incdecAmt", "fnlDlvrReqYn", "optnDivCdNm", "dminsttCd",
    "dminsttNm", "dminsttRgnNm", "IntlCntrctDlvrReqDate",
]


def unpack(payload: dict) -> tuple[dict, list[dict]]:
    response = payload.get("response", {})
    header = response.get("header", {})
    code = str(header.get("resultCode", ""))
    if code not in {"00", "0"}:
        safe_code = code if re.fullmatch(r"[A-Z0-9_-]{1,48}", code) else "missing_or_unrecognized"
        raise ApiError(f"PPS resultCode={safe_code}")
    body = response.get("body", {})
    items = body.get("items", [])
    if isinstance(items, dict):
        items = items.get("item", [])
    if not items:
        items = []
    elif isinstance(items, dict):
        items = [items]
    if not isinstance(items, list) or any(not isinstance(x, dict) for x in items):
        raise ValueError("Unexpected PPS item structure")
    return body, items


def periods(start: date, end: date, monthly: bool):
    cursor = start
    while cursor <= end:
        finish = date(cursor.year, cursor.month, calendar.monthrange(cursor.year, cursor.month)[1]) if monthly else date(cursor.year, 12, 31)
        finish = min(end, finish)
        yield cursor, finish
        cursor = date.fromordinal(finish.toordinal() + 1)


class Collector:
    def __init__(self, max_calls: int, refresh: bool):
        self.key = load_key("PPS_SHOPPING_MALL_SERVICE_KEY")
        self.max_calls = max_calls
        self.refresh = refresh
        self.calls = 0
        self.requests: list[dict] = []
        self.raw_dir = HERE / "raw" / "pps" / date.today().isoformat()
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self, operation: str, params: dict) -> tuple[dict, list[dict]]:
        identity = json.dumps([operation, params], ensure_ascii=False, sort_keys=True)
        digest = hashlib.sha256(identity.encode()).hexdigest()[:20]
        raw_path = self.raw_dir / f"{operation}_{digest}.json"
        if raw_path.exists() and not self.refresh:
            raw = raw_path.read_bytes()
            payload = json.loads(raw)
            fetched_at = datetime.fromtimestamp(raw_path.stat().st_mtime, timezone.utc).isoformat()
            cached = True
        else:
            if self.calls >= self.max_calls:
                raise ValueError("PPS request budget reached; no partial dataset written")
            self.calls += 1
            payload, raw = request_json(BASE + operation, params, self.key)
            # A credential-bearing response must never be persisted.
            if self.key.encode() in raw:
                raise ValueError("Credential unexpectedly present in response")
            if raw_path.exists() and raw_path.read_bytes() != raw:
                previous = raw_path.read_bytes()
                archive = raw_path.with_name(f"{raw_path.stem}_{hashlib.sha256(previous).hexdigest()[:12]}.json")
                archive.write_bytes(previous)
            raw_path.write_bytes(raw)
            fetched_at = datetime.now(timezone.utc).isoformat()
            cached = False
        body, items = unpack(payload)
        self.requests.append({
            "endpoint": BASE + operation, "parameters": params,
            "response_sha256": hashlib.sha256(raw).hexdigest(),
            "raw_path": str(raw_path.relative_to(HERE)),
            "fetched_at_utc": fetched_at, "cache_reused": cached,
            "result_code": "00", "total_count": int(body["totalCount"]),
            "received_count": len(items),
        })
        return body, items

    def complete(self, operation: str, params: dict) -> list[dict]:
        records = []
        page = 1
        expected = None
        fingerprints = set()
        while True:
            body, items = self.fetch(operation, {**params, "pageNo": page, "numOfRows": 100})
            count = int(body["totalCount"])
            if expected is None:
                expected = count
            elif count != expected:
                raise ValueError("PPS totalCount changed while paging; rerun the query")
            for row in items:
                fingerprint = json.dumps(row, ensure_ascii=False, sort_keys=True)
                if fingerprint in fingerprints:
                    raise ValueError("Duplicate PPS record across pages")
                fingerprints.add(fingerprint)
                records.append(row)
            if len(records) == expected:
                break
            if not items or len(records) > expected:
                raise ValueError("PPS pagination incomplete or excessive")
            page += 1
        return records


def as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def write_csv(path: Path, records: list[dict], fields: list[str]):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows({field: as_text(row.get(field)) for field in fields} for row in records)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--kind", choices=OPERATIONS, default="registrations")
    parser.add_argument("--term", action="append")
    parser.add_argument("--field", choices=["dtilPrdctClsfcNoNm", "prdctClsfcNoNm", "prdctIdntNoNm"], default="dtilPrdctClsfcNoNm")
    parser.add_argument("--start", type=date.fromisoformat, default=date(2024, 1, 1))
    parser.add_argument("--end", type=date.fromisoformat, default=date(2026, 9, 30))
    parser.add_argument("--max-calls", type=int, default=150)
    parser.add_argument("--monthly", action="store_true", help="Use shorter registration queries to reduce server load")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    if args.start > args.end or args.end >= date.today():
        parser.error("Use a past, ordered date interval")
    collector = Collector(args.max_calls, args.refresh)
    data_dir = HERE / "data"
    data_dir.mkdir(exist_ok=True)
    if args.probe:
        probes = []
        for field, term in [
            ("dtilPrdctClsfcNoNm", "키오스크"),
            ("dtilPrdctClsfcNoNm", "무인민원발급기"),
            ("dtilPrdctClsfcNoNm", "무인안내시스템"),
            ("dtilPrdctClsfcNoNm", "무인발권기"),
            ("dtilPrdctClsfcNoNm", "무인주문기"),
            ("prdctClsfcNoNm", "컴퓨터키오스크"),
        ]:
            params = {"type": "json", "inqryDiv": 1, "inqryBgnDate": args.end.replace(day=1).strftime("%Y%m%d"), "inqryEndDate": args.end.strftime("%Y%m%d"), "regtCncelYn": "Y", field: term, "pageNo": 1, "numOfRows": 5}
            body, items = collector.fetch(OPERATIONS["registrations"], params)
            probes.append({"field": field, "term": term, "total_count": int(body["totalCount"]), "sample": [{k: item.get(k) for k in ["dtilPrdctClsfcNo", "dtilPrdctClsfcNoNm", "prdctClsfcNoNm", "prdctSpecNm", "entrprsDivNm", "rgstDt"]} for item in items]})
            write_json(data_dir / "pps_probe.json", {"exploratory": True, "probe_complete": False, "probes": probes, "requests": collector.requests})
        write_json(data_dir / "pps_probe.json", {"exploratory": True, "probe_complete": True, "probes": probes, "requests": collector.requests})
        print(json.dumps({"status": "authenticated", "live_calls": collector.calls, "probes": [{k: p[k] for k in ["field", "term", "total_count"]} for p in probes]}, ensure_ascii=False))
        return 0
    if not args.term:
        parser.error("Supply at least one --term; broad unfiltered collection is disabled")
    records = []
    unique = set()
    overlaps = 0
    for term in args.term:
        for start, end in periods(args.start, args.end, args.kind == "deliveries" or args.monthly):
            params = {"type": "json", "inqryDiv": 1, "inqryBgnDate": start.strftime("%Y%m%d"), "inqryEndDate": end.strftime("%Y%m%d"), args.field: term}
            if args.kind == "registrations":
                params["regtCncelYn"] = "Y"
            rows = collector.complete(OPERATIONS[args.kind], params)
            for row in rows:
                fingerprint = json.dumps(row, ensure_ascii=False, sort_keys=True)
                if fingerprint in unique:
                    overlaps += 1
                    continue
                unique.add(fingerprint)
                records.append(row)
            print(json.dumps({"period": [start.isoformat(), end.isoformat()], "term": term, "rows": len(rows)}, ensure_ascii=False), flush=True)
    fields = REG_FIELDS if args.kind == "registrations" else DEL_FIELDS
    records.sort(key=lambda row: tuple(as_text(row.get(k)) for k in fields))
    csv_path = data_dir / f"pps_{args.kind}.csv"
    write_csv(csv_path, records, fields)
    write_json(data_dir / f"pps_{args.kind}_manifest.json", {
        "source_url": "https://www.data.go.kr/data/15129471/openapi.do",
        "reference_document_url": "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003701083&fileDetailSn=1",
        "reference_version": "1.3", "exploratory": True,
        "collection_complete": True, "start": args.start.isoformat(), "end": args.end.isoformat(),
        "operation": OPERATIONS[args.kind], "query_field": args.field,
        "terms": args.term, "rows": len(records), "identical_query_overlap_rows": overlaps,
        "csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "credentials_excluded": True, "unselected_fields_omitted": True,
        "requests": collector.requests,
    })
    print(json.dumps({"status": "complete", "kind": args.kind, "rows": len(records), "live_calls": collector.calls}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ApiError as exc:
        # api_common deliberately limits these messages to safe diagnostics.
        print(f"PPS collection failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
    except Exception as exc:
        # Do not interpolate network exceptions: some include authenticated URLs.
        print(f"PPS collection failed ({type(exc).__name__}); no credential printed", file=sys.stderr)
        raise SystemExit(1) from None
