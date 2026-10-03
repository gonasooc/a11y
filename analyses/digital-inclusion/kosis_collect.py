"""Collect four KOSIS digital-divide tables using a local, never-logged key."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from api_common import ApiError, load_key, request_json, write_json


HERE = Path(__file__).resolve().parent
TABLES = ("DT_12017N008", "DT_12017N009", "DT_12017N0010", "DT_12017N0011")
INDICATORS = dict(zip(TABLES, [
    "digital_informatization_overall", "digital_informatization_access",
    "digital_informatization_capability", "digital_informatization_utilization",
]))
POPULATIONS = {
    "취약계층 평균": "vulnerable_weighted", "장애인": "disabled",
    "고령층": "older_adults", "저소득층": "low_income", "농어민": "farmers_fishers",
}
META_URL = "https://kosis.kr/openapi/statisticsData.do"
DATA_URL = "https://kosis.kr/openapi/Param/statisticsParameterData.do"


def checked_rows(payload, *, allow_no_data=False):
    if isinstance(payload, dict) and "err" in payload:
        code = str(payload["err"])
        code = code if re.fullmatch(r"[A-Z0-9_-]{1,32}", code) else "unrecognized"
        if allow_no_data and code == "30":
            return []
        raise ApiError(f"KOSIS error code: {code}")
    if not isinstance(payload, list) or any(not isinstance(row, dict) for row in payload):
        raise ApiError("Unexpected KOSIS response structure")
    return payload


class Collector:
    def __init__(self, snapshot: date, refresh: bool):
        self.key = load_key("KOSIS_DIGITAL_DIVIDE_API_KEY")
        self.snapshot = snapshot.isoformat()
        self.refresh = refresh
        self.raw_dir = HERE / "raw" / "kosis" / self.snapshot
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.calls = 0
        self.last_request = 0.0
        self.requests = []

    def fetch(self, endpoint: str, params: dict, *, allow_no_data=False):
        identity = json.dumps([endpoint, params], ensure_ascii=False, sort_keys=True)
        digest = hashlib.sha256(identity.encode()).hexdigest()[:20]
        label = params.get("type", "data")
        path = self.raw_dir / f"{params['tblId']}_{label}_{digest}.json"
        if path.exists() and not self.refresh:
            raw = path.read_bytes()
            payload = json.loads(raw)
            retrieved = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
            cached = True
        else:
            # Small, sequential requests; do not race the official rate limit.
            time.sleep(max(0, 3.1 - (time.monotonic() - self.last_request)))
            if self.calls >= 100:
                raise ApiError("KOSIS per-run request budget reached")
            self.calls += 1
            self.last_request = time.monotonic()
            payload, raw = request_json(endpoint, params, self.key)
            # Failed authentication/parameter responses must not become a cache
            # that keeps rejecting a later corrected request.
            checked_rows(payload, allow_no_data=allow_no_data)
            if path.exists() and path.read_bytes() != raw:
                previous = path.read_bytes()
                path.with_name(f"{path.stem}_{hashlib.sha256(previous).hexdigest()[:12]}.json").write_bytes(previous)
            path.write_bytes(raw)
            retrieved = datetime.now(timezone.utc).isoformat()
            cached = False
        rows = checked_rows(payload, allow_no_data=allow_no_data)
        self.requests.append({
            "endpoint": endpoint, "parameters": params, "fetched_at_utc": retrieved,
            "response_sha256": hashlib.sha256(raw).hexdigest(), "raw_path": str(path.relative_to(HERE)),
            "cache_reused": cached, "row_count": len(rows),
            "response_status": "no_data_30" if isinstance(payload, dict) else "success",
        })
        return rows

    def metadata(self, table: str):
        output = {}
        for kind in ("TBL", "PRD", "ITM", "CMMT"):
            params = {"method": "getMeta", "type": kind, "orgId": "127", "tblId": table, "format": "json", "jsonVD": "Y"}
            if kind == "PRD":
                params["detail"] = "Y"
            output[kind] = self.fetch(META_URL, params, allow_no_data=kind == "CMMT")
        return output


def table_definition(table: str, metadata: dict) -> dict:
    if {row.get("PRD_SE") for row in metadata["PRD"] if "PRD_SE" in row} != {"년"}:
        raise ApiError("Unexpected KOSIS frequency; annual collection stopped")
    periods = sorted(row["PRD_DE"] for row in metadata["PRD"] if "PRD_DE" in row)
    if not periods or any(not re.fullmatch(r"\d{4}", period) for period in periods):
        raise ApiError("Unexpected KOSIS annual periods")
    items = [row for row in metadata["ITM"] if row.get("OBJ_ID") == "ITEM"]
    classifications = [row for row in metadata["ITM"] if row.get("OBJ_ID") != "ITEM"]
    if len(items) != 1 or {row.get("OBJ_ID_SN") for row in classifications} != {"1"}:
        raise ApiError("Unexpected KOSIS dimensions; manual schema review needed")
    if len({row["OBJ_ID"] for row in classifications}) != 1:
        raise ApiError("Multiple KOSIS classification dimensions")
    if {row["ITM_NM"] for row in classifications} != set(POPULATIONS):
        raise ApiError("KOSIS population metadata changed; review required")
    return {
        "table_id": table, "table_name": metadata["TBL"][0]["TBL_NM"],
        "periods": periods, "item_id": items[0]["ITM_ID"], "item_name": items[0]["ITM_NM"],
        "unit_source": items[0].get("UNIT_NM", ""),
        "classification_dimension": classifications[0]["OBJ_ID"],
        "classifications": {row["ITM_ID"]: row["ITM_NM"] for row in classifications},
    }


def normalize(table: str, rows: list[dict], definition: dict):
    expected = {(period, definition["item_id"], classification) for period in definition["periods"] for classification in definition["classifications"]}
    observed = set()
    output = []
    for row in rows:
        if row.get("ORG_ID") != "127" or row.get("TBL_ID") != table or row.get("PRD_SE") not in {"Y", "A"}:
            raise ApiError("Unexpected KOSIS table, organization, or frequency")
        identity = (row["PRD_DE"], row["ITM_ID"], row["C1"])
        if identity not in expected or identity in observed:
            raise ApiError("Unexpected or duplicate KOSIS observation")
        if any(row.get(f"C{index}") for index in range(2, 9)):
            raise ApiError("Unexpected additional KOSIS dimensions")
        if row.get("C1_NM") != definition["classifications"][row["C1"]]:
            raise ApiError("KOSIS classification code/label mismatch")
        if row.get("UNIT_NM") != definition["unit_source"]:
            raise ApiError("KOSIS unit metadata/observation mismatch")
        observed.add(identity)
        raw_value = "" if row.get("DT") is None else str(row["DT"])
        try:
            number = Decimal(raw_value)
        except InvalidOperation:
            value = ""
        else:
            if not number.is_finite() or number < 0:
                raise ApiError("Invalid KOSIS relative index")
            value = raw_value
        output.append({
            "survey_year": row["PRD_DE"], "indicator": INDICATORS[table],
            "population": POPULATIONS[row["C1_NM"]], "population_label": row["C1_NM"],
            "table_id": table, "item_id": row["ITM_ID"],
            "frequency_source": row["PRD_SE"],
            "classification_id": row["C1"], "classification_dimension": definition["classification_dimension"],
            "raw_value": raw_value, "value": value, "unit_source": row.get("UNIT_NM", ""),
            "unit": "index_general_population_100", "last_modified": row.get("LST_CHN_DE", ""),
            "source_url": f"https://kosis.kr/statHtml/statHtml.do?orgId=127&tblId={table}",
        })
    if observed != expected:
        raise ApiError("KOSIS full-period Cartesian coverage incomplete; no fabricated cells")
    return output


def self_test():
    definition = {
        "periods": ["2025"], "item_id": "1", "unit_source": "%",
        "classification_dimension": "population", "classifications": {"disabled": "장애인"},
    }
    row = {
        "ORG_ID": "127", "TBL_ID": TABLES[0], "PRD_SE": "A", "PRD_DE": "2025",
        "ITM_ID": "1", "C1": "disabled", "C1_NM": "장애인", "UNIT_NM": "%", "DT": "-",
    }
    output = normalize(TABLES[0], [row], definition)[0]
    assert output["raw_value"] == "-" and output["value"] == ""
    assert normalize(TABLES[0], [{**row, "DT": "0"}], definition)[0]["value"] == "0"
    for malformed in ([row, row], [], [{**row, "DT": "-1"}], [{**row, "PRD_SE": "Q"}]):
        try:
            normalize(TABLES[0], malformed, definition)
        except ApiError:
            pass
        else:
            raise AssertionError("Invalid observation accepted")
    print("KOSIS symbol/zero/duplicate/missing/negative/frequency checks passed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=date.fromisoformat, default=date.today())
    parser.add_argument("--table", choices=TABLES, action="append")
    parser.add_argument("--metadata-only", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    collector = Collector(args.snapshot, args.refresh)
    tables = args.table or TABLES
    if len(tables) != len(set(tables)):
        parser.error("Duplicate --table selection")
    metadata = {}
    all_rows = []
    definitions = {}
    for table in tables:
        metadata[table] = collector.metadata(table)
        definitions[table] = table_definition(table, metadata[table])
        write_json(HERE / "data" / f"kosis_metadata_{collector.snapshot}.json", {"snapshot": collector.snapshot, "tables": metadata, "requests": collector.requests, "metadata_collection_complete": len(metadata) == len(TABLES)})
        print(json.dumps({"table": table, "metadata_rows": {key: len(value) for key, value in metadata[table].items()}}, ensure_ascii=False), flush=True)
        if not args.metadata_only:
            definition = definitions[table]
            params = {
                "method": "getList", "orgId": "127", "tblId": table,
                "format": "json", "jsonVD": "Y", "objL1": "ALL",
                "itmId": definition["item_id"], "prdSe": "Y",
                "startPrdDe": definition["periods"][0], "endPrdDe": definition["periods"][-1],
                "smblChk": "Y",
            }
            rows = collector.fetch(DATA_URL, params)
            normalized = normalize(table, rows, definition)
            all_rows.extend(normalized)
            definitions[table]["expected_cells"] = len(definition["periods"]) * len(definition["classifications"])
            definitions[table]["observed_cells"] = len(normalized)
            definitions[table]["missing_or_symbol_cells"] = sum(row["value"] == "" for row in normalized)
            print(json.dumps({"table": table, "periods": [definition["periods"][0], definition["periods"][-1]], "observations": len(normalized)}, ensure_ascii=False), flush=True)
    # Keep metadata provenance distinct from the statistical value requests.
    write_json(HERE / "data" / f"kosis_metadata_{collector.snapshot}.json", {"snapshot": collector.snapshot, "tables": metadata, "requests": [r for r in collector.requests if r["parameters"]["method"] == "getMeta"], "metadata_collection_complete": len(metadata) == len(TABLES)})
    if args.metadata_only:
        print(json.dumps({"status": "authenticated_metadata", "tables": len(metadata), "live_calls": collector.calls}))
        return
    all_rows.sort(key=lambda row: (row["indicator"], row["population"], row["survey_year"]))
    csv_path = HERE / "data" / f"kosis_digital_divide_{collector.snapshot}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)
    write_json(HERE / "data" / f"kosis_manifest_{collector.snapshot}.json", {
        "source": "KOSIS 디지털정보격차실태조사 orgId=127",
        "snapshot": collector.snapshot, "authentication": "successful",
        "csv_path": str(csv_path.relative_to(HERE)),
        "csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "rows": len(all_rows), "collection_complete": len(metadata) == len(TABLES),
        "tables": definitions, "requests": collector.requests,
        "completeness_rule": "Every period × item × classification cell declared in metadata is present exactly once; symbols are preserved and not replaced with zero.",
        "numeric_cells": sum(row["value"] != "" for row in all_rows),
        "symbol_or_missing_cells": sum(row["value"] == "" for row in all_rows),
        "credentials_excluded": True, "reference_documents": [
            "https://kosis.kr/openapi/devGuide/devGuide_0201List.do",
            "https://kosis.kr/openapi/devGuide/devGuide_060103List.do",
            "https://kosis.kr/openapi/devGuide/devGuide_060104List.do",
            "https://kosis.kr/openapi/devGuide/devGuide_060105List.do",
        ],
    })
    print(json.dumps({"status": "complete", "tables": len(metadata), "rows": len(all_rows), "live_calls": collector.calls}))


if __name__ == "__main__":
    try:
        main()
    except ApiError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None
    except Exception as exc:
        print(f"KOSIS collection failed ({type(exc).__name__}); request URL omitted", file=sys.stderr)
        raise SystemExit(1) from None
