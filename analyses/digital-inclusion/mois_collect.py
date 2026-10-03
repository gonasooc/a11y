#!/usr/bin/env python3
"""Fetch and validate all pages of the MOIS current-device snapshot."""

import argparse
import csv
import hashlib
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

from api_common import ApiError, load_key, request_json, write_json


HERE = Path(__file__).resolve().parent
ENDPOINT = "https://apis.data.go.kr/1741000/kiosk_info/installation_info"
PAGE_SIZE = 100
FIELDS = [
    "OPN_ATMY_GRP_CD", "MNG_NO", "CTPV_CD", "ROAD_SGG_CD", "USE_YN_NM",
    "DAT_UPDT_SE", "LAST_MDFCN_PNT", "DAT_UPDT_PNT", "FRBLND_KPD",
    "FRBLND_VOICE_GD", "FRDEAF_SCRN_GD", "BRL_LBL_ATCMNT", "EPHN_SCKT",
    "TCTL_ELCTNC_MONITOR", "SCRN_EXPSN_FWK", "WHCHR_USER_MNPLT",
]


def unpack(payload):
    response = payload.get("response", {})
    header = response.get("header", {})
    code = str(header.get("resultCode", "missing"))
    if code not in {"0", "00", "0000"}:
        raise ApiError("MOIS application response was not successful")
    body = response.get("body", {})
    items = body.get("items", {}) or {}
    rows = items.get("item", []) if isinstance(items, dict) else items
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list):
        raise ApiError("MOIS item schema changed")
    return int(body["totalCount"]), int(body["pageNo"]), rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", default=datetime.now(timezone(timedelta(hours=9))).date().isoformat())
    args = parser.parse_args()
    # This is a local collection date, never passed as a historic-state API filter.
    datetime.strptime(args.snapshot, "%Y-%m-%d")
    raw_dir = HERE / "raw" / "mois" / args.snapshot
    raw_dir.mkdir(parents=True, exist_ok=True)
    key = load_key("MOIS_KIOSK_INFO_SERVICE_KEY")
    start = datetime.now(timezone.utc).isoformat()

    def fetch_page(page, use_cache=True):
        path = raw_dir / f"page-{page:04d}.json"
        if use_cache and path.exists():
            raw = path.read_bytes()
            payload = json.loads(raw)
        else:
            for attempt in range(3):
                try:
                    payload, raw = request_json(ENDPOINT, {
                        "pageNo": page, "numOfRows": PAGE_SIZE, "returnType": "JSON",
                    }, key, timeout=60)
                    unpack(payload)
                    break
                except ApiError as exc:
                    if attempt == 2 or ("Network failure" not in str(exc) and not str(exc).startswith("HTTP 5")):
                        raise
                    time.sleep(1 + attempt)
            if use_cache:
                path.write_bytes(raw)
        total, returned_page, rows = unpack(payload)
        if returned_page != page:
            raise ApiError("MOIS returned an unexpected page number")
        return {"page": page, "total": total, "rows": rows,
                "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                "raw_path": str(path.relative_to(HERE))}

    first = fetch_page(1)
    total = first["total"]
    if total <= 0:
        raise ApiError("Unexpected empty MOIS dataset; not a valid analysis snapshot")
    page_count = math.ceil(total / PAGE_SIZE)
    if page_count > 1000:
        raise ApiError("Unexpected dataset expansion; review before continuing")
    pages = {1: first}
    print(f"MOIS authentication succeeded; API total {total}, {page_count} pages.", flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fetch_page, page): page for page in range(2, page_count + 1)}
        for future in as_completed(futures):
            result = future.result()
            pages[result["page"]] = result
            if len(pages) % 10 == 0 or len(pages) == page_count:
                print(f"Collected {len(pages)}/{page_count} pages.", flush=True)

    rows = []
    for number in range(1, page_count + 1):
        page = pages[number]
        expected = min(PAGE_SIZE, total - (number - 1) * PAGE_SIZE)
        if page["total"] != total or len(page["rows"]) != expected:
            raise ApiError("MOIS page totals or sizes changed during collection")
        rows.extend(page["rows"])
    keys = [(str(row.get("OPN_ATMY_GRP_CD", "")), str(row.get("MNG_NO", ""))) for row in rows]
    if any(not a or not b for a, b in keys):
        raise ApiError("MOIS device keys are missing; review raw records")
    initial_unique = len(set(keys))
    partitions = []
    if initial_unique != len(keys):
        # Unstable ordering at page boundaries can omit records as well as repeat
        # them. Deduplication alone would hide those omissions. Query disjoint
        # authorities (and time ranges where needed), each in a single page.
        print(f"Detected {len(keys) - initial_unique} repeated boundary rows; rebuilding with authority partitions.", flush=True)
        authorities = sorted({row["OPN_ATMY_GRP_CD"] for row in rows})

        def partition(authority, lower="", upper="", depth=0):
            if depth > 20:
                raise ApiError("Cannot split MOIS authority into complete single-page ranges")
            params = {"pageNo": 1, "numOfRows": PAGE_SIZE, "returnType": "JSON",
                      "cond[OPN_ATMY_GRP_CD::EQ]": authority}
            if lower:
                params["cond[DAT_UPDT_PNT::GTE]"] = lower
            if upper:
                params["cond[DAT_UPDT_PNT::LT]"] = upper
            filename = f"authority-{authority}-{lower or 'start'}-{upper or 'end'}.json"
            path = raw_dir / filename
            if path.exists():
                raw = path.read_bytes()
                payload = json.loads(raw)
            else:
                for attempt in range(3):
                    try:
                        payload, raw = request_json(ENDPOINT, params, key, timeout=60)
                        unpack(payload)
                        break
                    except ApiError as exc:
                        if attempt == 2 or ("Network failure" not in str(exc) and not str(exc).startswith("HTTP 5")):
                            raise
                        time.sleep(1 + attempt)
                path.write_bytes(raw)
            count, returned_page, items = unpack(payload)
            if returned_page != 1 or any(row.get("OPN_ATMY_GRP_CD") != authority for row in items):
                raise ApiError("MOIS authority filter did not match returned records")
            metadata = {"request_parameters": params, "total": count, "received_rows": len(items),
                        "raw_path": str(path.relative_to(HERE)), "sha256": hashlib.sha256(raw).hexdigest(),
                        "saved_at_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()}
            if count <= PAGE_SIZE:
                if len(items) != count:
                    raise ApiError("Incomplete MOIS single-page partition")
                for row in items:
                    stamp = datetime.fromisoformat(row["DAT_UPDT_PNT"]).strftime("%Y%m%d%H%M%S")
                    if (lower and stamp < lower) or (upper and stamp >= upper):
                        raise ApiError("MOIS timestamp filter was not respected")
                return count, items, [metadata]
            stamps = sorted({datetime.fromisoformat(row["DAT_UPDT_PNT"]).strftime("%Y%m%d%H%M%S") for row in items})
            pivot = stamps[len(stamps) // 2]
            if (lower and pivot <= lower) or (upper and pivot >= upper):
                raise ApiError("MOIS timestamp bucket cannot be split further")
            left_count, left, left_meta = partition(authority, lower, pivot, depth + 1)
            right_count, right, right_meta = partition(authority, pivot, upper, depth + 1)
            if left_count + right_count != count:
                raise ApiError("MOIS disjoint time ranges do not reconcile with authority total")
            metadata["split_parent_only"] = True
            return count, left + right, [metadata] + left_meta + right_meta

        rows = []
        partition_total = 0
        completed = 0
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(partition, authority) for authority in authorities]
            for future in as_completed(futures):
                count, items, metadata = future.result()
                partition_total += count
                rows.extend(items)
                partitions.extend(metadata)
                completed += 1
                if completed % 30 == 0 or completed == len(authorities):
                    print(f"Verified {completed}/{len(authorities)} authority partitions.", flush=True)
        keys = [(row["OPN_ATMY_GRP_CD"], row["MNG_NO"]) for row in rows]
        if partition_total != total or len(rows) != total or len(set(keys)) != total:
            raise ApiError("MOIS partition totals and unique keys do not reconcile with global total")
        rows.sort(key=lambda row: (row["OPN_ATMY_GRP_CD"], row["MNG_NO"]))
    check = fetch_page(1, use_cache=False)
    if check["total"] != total:
        raise ApiError("MOIS global total changed; snapshot needs review")
    if not partitions and check["rows"] != first["rows"]:
        raise ApiError("MOIS first-page sentinel changed; snapshot needs review")

    target = HERE / "data" / f"mois_devices_{args.snapshot}.csv"
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows({name: row.get(name, "") for name in FIELDS} for row in rows)
    manifest = {
        "source_id": "15154774", "source_url": "https://www.data.go.kr/data/15154774/openapi.do",
        "endpoint": ENDPOINT, "snapshot_date_kst": args.snapshot,
        "collection_started_at_utc": start, "collection_finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "authentication": "succeeded", "environment_variable": "MOIS_KIOSK_INFO_SERVICE_KEY",
        "key_handling": "URL-encoded input is decoded once in memory; key omitted from artifacts",
        "request_parameters": {"numOfRows": PAGE_SIZE, "returnType": "JSON"},
        "reported_total": total, "received_rows": len(rows), "unique_device_keys": len(set(keys)),
        "key_columns": ["OPN_ATMY_GRP_CD", "MNG_NO"], "page_count": page_count,
        "all_page_counts_consistent": True, "first_page_sentinel_unchanged": check["rows"] == first["rows"],
        "global_total_rechecked": check["total"],
        "collection_strategy": "single-page disjoint authority/time partitions" if partitions else "pagination",
        "initial_paginated_unique_keys": initial_unique, "initial_repeated_rows": total - initial_unique,
        "partition_counts_and_unique_keys_reconciled": bool(partitions), "partitions": partitions,
        "transactionally_consistent_snapshot_guaranteed": False,
        "dataset_path": str(target.relative_to(HERE)),
        "dataset_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "pages": [{k: v for k, v in pages[n].items() if k != "rows"} for n in sorted(pages)],
        "limitations": ["API current rows, not a census of every physically installed device",
                        "Modification/update dates are not installation or feature-adoption dates",
                        "Server-side ordering and transactional consistency are not guaranteed"],
    }
    saved = [datetime.fromtimestamp((HERE / item["raw_path"]).stat().st_mtime, timezone.utc)
             for item in manifest["pages"] + partitions]
    manifest["earliest_raw_saved_at_utc"] = min(saved).isoformat()
    manifest["latest_raw_saved_at_utc"] = max(saved).isoformat()
    write_json(HERE / "data" / f"mois_manifest_{args.snapshot}.json", manifest)
    print(f"Validated {len(rows)} unique devices; saved normalized CSV and provenance manifest.")


if __name__ == "__main__":
    try:
        main()
    except (ApiError, ValueError, KeyError) as exc:
        print(f"Collection stopped: {exc}", file=sys.stderr)
        sys.exit(1)
