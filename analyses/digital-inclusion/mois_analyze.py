#!/usr/bin/env python3
"""Analyze a validated MOIS current-record snapshot without network access or keys."""

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


HERE = Path(__file__).resolve().parent
KEYS = ("OPN_ATMY_GRP_CD", "MNG_NO")
FEATURES = {
    "FRBLND_KPD": ("시각장애인용 키패드", "제공", "미제공"),
    "FRBLND_VOICE_GD": ("시각장애인용 음성안내", "제공", "미제공"),
    "FRDEAF_SCRN_GD": ("청각장애인용 화면안내", "제공", "미제공"),
    "BRL_LBL_ATCMNT": ("점자라벨 부착", "부착", "미부착"),
    "EPHN_SCKT": ("이어폰 소켓", "제공", "미제공"),
    "TCTL_ELCTNC_MONITOR": ("촉각(전자)모니터", "제공", "미제공"),
    "SCRN_EXPSN_FWK": ("화면 확대 기능", "제공", "미제공"),
    "WHCHR_USER_MNPLT": ("휠체어 사용자 조작", "가능", "불가능"),
}
FREQUENCY_FIELDS = (
    "CTPV_CD", "ROAD_SGG_CD", "USE_YN_NM", "DAT_UPDT_SE",
    "LAST_MDFCN_PNT", "DAT_UPDT_PNT", *FEATURES,
)
REQUIRED_FIELDS = (*KEYS, *FREQUENCY_FIELDS)


class AnalysisError(ValueError):
    """Input is incomplete or no longer agrees with its collection manifest."""


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentage(numerator, denominator):
    return round(numerator / denominator * 100, 6) if denominator else None


def normalize_feature(field, raw):
    """Only field-specific exact enums count; substrings such as 미제공 are unsafe."""
    _, yes, no = FEATURES[field]
    value = str(raw or "").strip()
    return "yes" if value == yes else "no" if value == no else "unknown"


def normalize_use(raw):
    value = str(raw or "").strip()
    return "yes" if value == "사용" else "no" if value == "미사용" else "unknown"


def local_path(relative):
    path = (HERE / relative).resolve()
    if not path.is_relative_to(HERE):
        raise AnalysisError("Manifest path is outside the analysis directory")
    return path


def validate_source(snapshot):
    dataset = HERE / "data" / f"mois_devices_{snapshot}.csv"
    manifest_path = HERE / "data" / f"mois_manifest_{snapshot}.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_id") != "15154774" or manifest.get("snapshot_date_kst") != snapshot:
        raise AnalysisError("Source or snapshot date does not match the request")
    if local_path(manifest["dataset_path"]) != dataset:
        raise AnalysisError("Manifest references a different dataset")
    if sha256(dataset) != manifest.get("dataset_sha256"):
        raise AnalysisError("Dataset checksum does not match the collection manifest")
    with dataset.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not set(REQUIRED_FIELDS).issubset(reader.fieldnames or []):
            raise AnalysisError("Required data fields are missing")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise AnalysisError("Malformed CSV row")
    total = manifest["reported_total"]
    size = manifest["request_parameters"]["numOfRows"]
    if not isinstance(total, int) or total <= 0 or not isinstance(size, int) or size <= 0:
        raise AnalysisError("Invalid total or page size")
    if total != len(rows) or manifest.get("received_rows") != len(rows):
        raise AnalysisError("Partial collection: API total and CSV row count differ")
    expected_pages = math.ceil(total / size)
    pages = manifest["pages"]
    if manifest.get("page_count") != expected_pages or [p["page"] for p in pages] != list(range(1, expected_pages + 1)):
        raise AnalysisError("Partial or duplicated page sequence")
    if not manifest.get("all_page_counts_consistent"):
        raise AnalysisError("Collection consistency checks did not pass")
    if any(p["total"] != total for p in pages):
        raise AnalysisError("Page totals do not match")
    keys = {tuple(row[field] for field in KEYS) for row in rows}
    if manifest.get("unique_device_keys") != len(keys):
        raise AnalysisError("Unique record key count does not match manifest")
    if len(keys) != total or any(not all(part.strip() for part in key) for key in keys):
        raise AnalysisError("Unique nonempty keys do not cover the API total; deduplication cannot repair missing records")

    partitions = manifest.get("partitions", [])
    if partitions:
        if not manifest.get("partition_counts_and_unique_keys_reconciled") or manifest.get("global_total_rechecked") != total:
            raise AnalysisError("Partition collection did not reconcile with the rechecked global total")
        grouped = defaultdict(list)
        for item in partitions:
            params = item["request_parameters"]
            if params.get("pageNo") != 1 or params.get("numOfRows") != size:
                raise AnalysisError("Partition is not a single-page query")
            authority = str(params.get("cond[OPN_ATMY_GRP_CD::EQ]", ""))
            if not authority:
                raise AnalysisError("Partition authority is missing")
            grouped[authority].append(item)
        root_total, leaves = 0, []
        for authority, items in grouped.items():
            roots = [item for item in items if not item["request_parameters"].get("cond[DAT_UPDT_PNT::GTE]")
                     and not item["request_parameters"].get("cond[DAT_UPDT_PNT::LT]")]
            if len(roots) != 1:
                raise AnalysisError("Authority partition must have one unrestricted root")
            root_total += roots[0]["total"]
            authority_leaves = sorted((item for item in items if not item.get("split_parent_only")),
                                      key=lambda item: item["request_parameters"].get("cond[DAT_UPDT_PNT::GTE]", ""))
            previous_upper = ""
            for index, item in enumerate(authority_leaves):
                params = item["request_parameters"]
                lower, upper = params.get("cond[DAT_UPDT_PNT::GTE]", ""), params.get("cond[DAT_UPDT_PNT::LT]", "")
                if lower != previous_upper or (upper and lower and upper <= lower):
                    raise AnalysisError("Partition time ranges have a gap or overlap")
                if not upper and index != len(authority_leaves) - 1:
                    raise AnalysisError("Unbounded partition occurs before the last range")
                if item["total"] != item["received_rows"] or not 0 <= item["total"] <= size:
                    raise AnalysisError("Leaf partition is incomplete or exceeds one page")
                previous_upper = upper
            if not authority_leaves or previous_upper or sum(item["total"] for item in authority_leaves) != roots[0]["total"]:
                raise AnalysisError("Leaf ranges do not fully reconcile with the authority root")
            leaves.extend(authority_leaves)
        if root_total != total or sum(item["total"] for item in leaves) != total:
            raise AnalysisError("Authority roots and leaf counts do not cover the API total")
        if {key[0] for key in keys} != set(grouped):
            raise AnalysisError("CSV authority groups differ from the partition groups")
        evidence = partitions
    else:
        if not manifest.get("first_page_sentinel_unchanged"):
            raise AnalysisError("Paginated source changed during collection")
        evidence = pages

    raw_verified, raw_missing = 0, 0
    leaf_records = []
    for page in evidence:
        path = local_path(page["raw_path"])
        if not path.exists():
            raw_missing += 1
            continue
        if sha256(path) != page["sha256"] or ("bytes" in page and path.stat().st_size != page["bytes"]):
            raise AnalysisError("Raw page checksum or size mismatch")
        payload = json.loads(path.read_bytes())
        response = payload.get("response", {})
        if str(response.get("header", {}).get("resultCode", "")) not in {"0", "00", "0000"}:
            raise AnalysisError("Cached raw page is not a successful API response")
        body = response["body"]
        actual = body.get("items", {}) or {}
        actual = actual.get("item", []) if isinstance(actual, dict) else actual
        actual = [actual] if isinstance(actual, dict) else actual
        start = 0 if partitions else (page["page"] - 1) * size
        expected = page["received_rows"] if partitions else min(size, total - start)
        expected_page = 1 if partitions else page["page"]
        if int(body["totalCount"]) != page["total"] or int(body["pageNo"]) != expected_page or len(actual) != expected:
            raise AnalysisError("Raw page count, total or number mismatch")
        normalized = [{field: "" if row.get(field) is None else str(row.get(field, ""))
                       for field in REQUIRED_FIELDS} for row in actual]
        if partitions:
            params = page["request_parameters"]
            authority = str(params["cond[OPN_ATMY_GRP_CD::EQ]"])
            lower, upper = params.get("cond[DAT_UPDT_PNT::GTE]", ""), params.get("cond[DAT_UPDT_PNT::LT]", "")
            for row in normalized:
                if row["OPN_ATMY_GRP_CD"] != authority:
                    raise AnalysisError("Partition source row does not satisfy its declared filters")
                if lower or upper:
                    timestamp = datetime.fromisoformat(row["DAT_UPDT_PNT"]).strftime("%Y%m%d%H%M%S")
                    if (lower and timestamp < lower) or (upper and timestamp >= upper):
                        raise AnalysisError("Partition timestamp does not satisfy its declared filters")
            if not page.get("split_parent_only"):
                leaf_records.extend(normalized)
        else:
            csv_slice = [{field: row[field] for field in REQUIRED_FIELDS}
                         for row in rows[start:start + expected]]
            if normalized != csv_slice:
                raise AnalysisError("CSV content differs from its source page")
        raw_verified += 1
    if partitions and not raw_missing:
        by_key = lambda row: tuple(row[field] for field in KEYS)
        csv_records = [{field: row[field] for field in REQUIRED_FIELDS} for row in rows]
        if sorted(leaf_records, key=by_key) != sorted(csv_records, key=by_key):
            raise AnalysisError("Partition leaf records differ from the CSV dataset")
    integrity = {
        "collection_scope": "complete_partition_union" if partitions else "all_pages",
        "dataset_sha256_verified": True,
        "initial_page_sequence_verified": True, "initial_expected_pages": expected_pages,
        "manifest_reports_consistent_page_counts": True,
        "manifest_reports_unchanged_first_page": manifest.get("first_page_sentinel_unchanged"),
        "initial_paginated_unique_keys": manifest.get("initial_paginated_unique_keys", total),
        "initial_repeated_rows": manifest.get("initial_repeated_rows", 0),
        "initial_pagination_used_as_final_dataset": not bool(partitions),
        "authority_partition_groups": len(grouped) if partitions else None,
        "partition_queries_including_split_parents": len(partitions),
        "leaf_partition_queries": len(leaves) if partitions else None,
        "partition_ranges_and_counts_verified": bool(partitions),
        "global_total_rechecked": manifest.get("global_total_rechecked"),
        "expected_raw_evidence_files": len(evidence),
        "raw_pages_locally_verified": raw_verified, "raw_pages_not_present": raw_missing,
        "all_raw_pages_locally_verified": raw_verified == len(evidence),
        "transactionally_consistent_snapshot_guaranteed": False,
    }
    return rows, manifest, manifest_path, integrity


def select_records(rows):
    """Keep unique, nonconflicting keys; quarantine an unverified D update code."""
    keyed = defaultdict(list)
    missing_keys = []
    for row in rows:
        key = tuple(row[field].strip() for field in KEYS)
        (keyed[key] if all(key) else missing_keys).append(row)
    unique, duplicate_rows, conflicting_keys, conflicting_rows = [], 0, 0, 0
    for group in keyed.values():
        if all(row == group[0] for row in group):
            unique.append(group[0])
            duplicate_rows += len(group) - 1
        else:
            conflicting_keys += 1
            conflicting_rows += len(group)
    d_code = [r for r in unique if r["DAT_UPDT_SE"].strip() == "D"]
    eligible = [r for r in unique if r["DAT_UPDT_SE"].strip() != "D"]
    used = [r for r in eligible if normalize_use(r["USE_YN_NM"]) == "yes"]
    unused = [r for r in eligible if normalize_use(r["USE_YN_NM"]) == "no"]
    use_unknown = [r for r in eligible if normalize_use(r["USE_YN_NM"]) == "unknown"]
    flow = {
        "received_rows": len(rows), "missing_key_rows_excluded": len(missing_keys),
        "distinct_nonempty_keys": len(keyed), "exact_duplicate_rows_removed": duplicate_rows,
        "conflicting_duplicate_keys_excluded": conflicting_keys,
        "conflicting_duplicate_rows_excluded": conflicting_rows,
        "unique_nonconflicting_records": len(unique),
        "update_code_D_quarantined": len(d_code),
        "remaining_unique_records": len(eligible), "explicitly_in_use_records": len(used),
        "explicitly_not_in_use_records": len(unused), "unknown_use_records": len(use_unknown),
    }
    assert len(unique) + duplicate_rows + conflicting_rows + len(missing_keys) == len(rows)
    assert len(used) + len(unused) + len(use_unknown) + len(d_code) == len(unique)
    return used, eligible, flow


def geography(row):
    code = row["ROAD_SGG_CD"].strip()
    # Prefixes are labels derived from the observed installation code, not a code-name lookup.
    if re.fullmatch(r"[0-9]{5}", code) and code != "00000":
        return code, code[:2]
    return "unknown", "unknown"


def feature_summaries(used, snapshot):
    groups = defaultdict(list)
    groups[("national", "all")] = list(used)
    for row in used:
        district, province = geography(row)
        groups[("installation_province_prefix", province)].append(row)
        groups[("installation_sgg_code", district)].append(row)
    summaries = []
    for (level, code), group in sorted(groups.items()):
        for field, (label, _, _) in FEATURES.items():
            counts = Counter(normalize_feature(field, row[field]) for row in group)
            yes, no, unknown, n = counts["yes"], counts["no"], counts["unknown"], len(group)
            summaries.append({
                "snapshot_date": snapshot, "geography_level": level, "geography_code": code,
                "feature": field, "feature_label": label, "in_use_records_n": n,
                "yes": yes, "no": no, "unknown": unknown,
                "yes_pct_all": percentage(yes, n), "unknown_pct_all": percentage(unknown, n),
                "known_n": yes + no, "yes_pct_known": percentage(yes, yes + no),
            })
    return summaries


def build_region_labels(snapshot, rows, manifest, manifest_path, target):
    """Extract address first-token frequencies without publishing detailed addresses."""
    evidence = manifest.get("partitions") or manifest["pages"]
    first_tokens, authority_codes = defaultdict(Counter), defaultdict(Counter)
    observed_keys = set()
    for item in evidence:
        if item.get("split_parent_only"):
            continue
        path = local_path(item["raw_path"])
        if not path.exists() or sha256(path) != item["sha256"]:
            raise AnalysisError("Complete verified raw sources are needed to refresh region labels")
        payload = json.loads(path.read_bytes())
        records = payload["response"]["body"].get("items", {}) or {}
        records = records.get("item", []) if isinstance(records, dict) else records
        records = [records] if isinstance(records, dict) else records
        for row in records:
            key = tuple(str(row.get(field, "")) for field in KEYS)
            if key in observed_keys:
                raise AnalysisError("Repeated raw keys cannot be used for region-label frequencies")
            observed_keys.add(key)
            prefix = geography({"ROAD_SGG_CD": str(row.get("ROAD_SGG_CD") or "")})[1]
            words = str(row.get("INSTL_PLC_ADDR") or "").split()
            first_tokens[prefix][words[0] if words else "(missing)"] += 1
            authority_codes[prefix][str(row.get("CTPV_CD") or "")] += 1
    if observed_keys != {tuple(row[field] for field in KEYS) for row in rows}:
        raise AnalysisError("Region-label raw records do not match the source dataset")
    regions = []
    for code, counts in sorted(first_tokens.items()):
        named = {token: count for token, count in counts.items() if token != "(missing)"}
        label = min(named, key=lambda token: (-named[token], token)) if named else "표시명 미상"
        regions.append({
            "geography_code": code, "display_label": label, "records_n": sum(counts.values()),
            "address_first_token_frequencies": dict(sorted(counts.items())),
            "ctpv_code_frequencies": dict(sorted(authority_codes[code].items())),
        })
    metadata = {
        "snapshot_date_kst": snapshot, "source_id": manifest["source_id"],
        "source_url": manifest["source_url"], "source_manifest": str(manifest_path.relative_to(HERE)),
        "source_manifest_sha256": sha256(manifest_path),
        "source_dataset_sha256": manifest["dataset_sha256"], "source_records_n": len(rows),
        "frequency_scope": "all_received_unique_records_including_not_in_use",
        "source_address_field": "INSTL_PLC_ADDR",
        "retained_address_component": "First whitespace-delimited token only; no detailed address or contact details retained",
        "code_basis": "First two digits of ROAD_SGG_CD; original prefix remains the grouping key",
        "display_label_method": "Most frequent nonmissing address first token within each prefix; lexical tie break. Other observed tokens are retained in frequencies.",
        "official_code_table_verified": False,
        "interpretation": "원자료 주소 첫 토큰을 관측해 붙인 표시명이다. 법정 표준코드표나 전체 행정구역 코드 검증 결과가 아니며, 다른 첫 토큰을 가진 행의 행정구역을 개별 재판정하지 않는다.",
        "regions": regions,
    }
    temp = target.with_suffix(".json.tmp")
    temp.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(target)


def load_region_labels(snapshot, rows, manifest, manifest_path):
    path = HERE / "data" / f"mois_region_labels_{snapshot}.json"
    if not path.exists():
        raise AnalysisError("Region-label metadata is missing; use --refresh-region-labels with verified raw files")
    metadata = json.loads(path.read_text(encoding="utf-8"))
    if metadata.get("snapshot_date_kst") != snapshot or metadata.get("source_dataset_sha256") != manifest["dataset_sha256"]:
        raise AnalysisError("Region labels refer to a different dataset")
    if metadata.get("source_manifest_sha256") != sha256(manifest_path):
        raise AnalysisError("Region-label source manifest changed; rerun with --refresh-region-labels")
    counts = Counter(geography(row)[1] for row in rows)
    labels = {item["geography_code"]: item for item in metadata["regions"]}
    if len(labels) != len(metadata["regions"]) or set(labels) != set(counts):
        raise AnalysisError("Region-label prefixes are duplicated or do not cover the dataset")
    if metadata.get("source_records_n") != len(rows) or metadata.get("official_code_table_verified") is not False:
        raise AnalysisError("Region-label scope is inconsistent")
    for code, item in labels.items():
        frequencies = item["address_first_token_frequencies"]
        if item["records_n"] != counts[code] or sum(frequencies.values()) != counts[code]:
            raise AnalysisError("Region-label frequencies do not reconcile with source rows")
        named = {token: count for token, count in frequencies.items() if token != "(missing)"}
        expected_label = min(named, key=lambda token: (-named[token], token)) if named else "표시명 미상"
        if item["display_label"] != expected_label:
            raise AnalysisError("Region display label does not follow its documented selection rule")
    provenance = {"path": str(path.relative_to(HERE)), "sha256": sha256(path),
                  "source_manifest_sha256": metadata["source_manifest_sha256"],
                  "display_label_method": metadata["display_label_method"],
                  "official_code_table_verified": False}
    return labels, provenance


def region_comparison(features, labels, snapshot):
    selected = defaultdict(dict)
    for item in features:
        if item["geography_level"] == "installation_province_prefix":
            selected[item["geography_code"]][item["feature"]] = item
    result = []
    for code, fields in sorted(selected.items()):
        wheelchair, tactile = fields["WHCHR_USER_MNPLT"], fields["TCTL_ELCTNC_MONITOR"]
        if wheelchair["in_use_records_n"] != tactile["in_use_records_n"]:
            raise AnalysisError("Regional feature denominators differ")
        row = {"snapshot_date": snapshot, "geography_code": code,
               "display_label": labels[code]["display_label"],
               "in_use_records_n": wheelchair["in_use_records_n"]}
        for name, item in [("wheelchair", wheelchair), ("tactile", tactile)]:
            for key in ("yes", "no", "unknown", "yes_pct_all", "unknown_pct_all", "known_n", "yes_pct_known"):
                row[f"{name}_{key}"] = item[key]
        result.append(row)
    return result


def raw_frequencies(rows, used, snapshot):
    result = []
    for scope, records in [("all_received", rows), ("explicitly_in_use", used)]:
        for field in FREQUENCY_FIELDS:
            for raw, count in sorted(Counter(row[field] for row in records).items()):
                normalized = normalize_feature(field, raw) if field in FEATURES else (
                    normalize_use(raw) if field == "USE_YN_NM" else "not_applicable")
                result.append({"snapshot_date": snapshot, "scope": scope, "field": field,
                               "raw_value": raw, "normalized_value": normalized,
                               "count": count, "scope_n": len(records),
                               "pct": percentage(count, len(records))})
    return result


def date_quality(records, field, snapshot):
    valid, invalid, missing = [], 0, 0
    for row in records:
        raw = row[field].strip()
        if not raw:
            missing += 1
            continue
        try:
            # API timestamps do not expose a time zone. Compare calendar dates only.
            parsed = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
            valid.append(parsed)
        except ValueError:
            invalid += 1
    date = datetime.strptime(snapshot, "%Y-%m-%d").date()
    return {
        "records_n": len(records), "valid_n": len(valid), "missing_n": missing,
        "invalid_n": invalid, "unknown_pct": percentage(missing + invalid, len(records)),
        "earliest": min(valid).isoformat(sep=" ") if valid else None,
        "latest": max(valid).isoformat(sep=" ") if valid else None,
        "older_than_365_days_n": sum((date - value.date()).days > 365 for value in valid),
        "future_calendar_date_n": sum(value.date() > date for value in valid),
        "not_installation_or_feature_adoption_date": True,
    }


def write_csv(path, records):
    if not records:
        raise AnalysisError("Refusing to write a headerless empty table")
    temp = path.with_suffix(".csv.tmp")
    with temp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    temp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, help="Local collection date, YYYY-MM-DD")
    parser.add_argument("--refresh-region-labels", action="store_true",
                        help="Rebuild first-address-token display labels from verified local raw files")
    args = parser.parse_args()
    datetime.strptime(args.snapshot, "%Y-%m-%d")
    rows, manifest, manifest_path, integrity = validate_source(args.snapshot)
    if args.refresh_region_labels:
        build_region_labels(args.snapshot, rows, manifest, manifest_path,
                            HERE / "data" / f"mois_region_labels_{args.snapshot}.json")
    labels, label_provenance = load_region_labels(args.snapshot, rows, manifest, manifest_path)
    used, eligible, flow = select_records(rows)
    features = feature_summaries(used, args.snapshot)
    frequencies = raw_frequencies(rows, used, args.snapshot)
    regions = region_comparison(features, labels, args.snapshot)
    district_counts = Counter(geography(row)[0] for row in used)
    province_counts = Counter(geography(row)[1] for row in used)
    summary = {
        "snapshot_date_kst": args.snapshot,
        "analysis": "MOIS current snapshot: feature-specific descriptive statistics",
        "unit": "API records keyed by OPN_ATMY_GRP_CD and MNG_NO; not all physical devices",
        "source_url": manifest["source_url"], "endpoint": manifest["endpoint"],
        "collection_started_at_utc": manifest["collection_started_at_utc"],
        "collection_finished_at_utc": manifest["collection_finished_at_utc"],
        "source_dataset": manifest["dataset_path"], "source_dataset_sha256": manifest["dataset_sha256"],
        "source_manifest": str(manifest_path.relative_to(HERE)),
        "source_manifest_sha256": sha256(manifest_path), "integrity": integrity,
        "region_label_metadata": label_provenance,
        "record_flow": flow,
        "denominator_policy": "After unique-key validation and D-code quarantine, only USE_YN_NM=사용 records enter feature rates. Missing/unrecognized feature values stay in N and are also reported as unknown.",
        "enum_mapping": {field: {yes: "yes", no: "no", "all_other_values": "unknown"}
                         for field, (_, yes, no) in FEATURES.items()},
        "update_code_policy": "D is quarantined separately without asserting a verified deletion meaning. No other update code is interpreted as an installation event. All original codes are retained in frequency output.",
        "national_features": [item for item in features if item["geography_level"] == "national"],
        "data_quality": {
            "unknown_use_pct_remaining": percentage(flow["unknown_use_records"], len(eligible)),
            "unrecognized_update_code_n": sum(row["DAT_UPDT_SE"].strip() not in {"I", "U", "D"} for row in rows),
            "in_use_missing_or_malformed_installation_code_n": district_counts["unknown"],
            "in_use_missing_or_malformed_installation_code_pct": percentage(district_counts["unknown"], len(used)),
            "installation_code_membership_verification": "not_performed; syntactic validity does not establish a current official region code",
            "observed_installation_sgg_codes_n": len(set(district_counts) - {"unknown"}),
            "observed_installation_province_prefixes_n": len(set(province_counts) - {"unknown"}),
            "date_fields_all_received": {field: date_quality(rows, field, args.snapshot)
                                         for field in ("LAST_MDFCN_PNT", "DAT_UPDT_PNT")},
            "date_fields_in_use": {field: date_quality(used, field, args.snapshot)
                                   for field in ("LAST_MDFCN_PNT", "DAT_UPDT_PNT")},
        },
        "geographic_definition": {
            "installation_sgg_code": "ROAD_SGG_CD; syntactically valid five-digit nonzero codes; official code membership/name not validated",
            "installation_province_prefix": "First two digits of ROAD_SGG_CD; display labels use the most frequent observed address first token, not an official code-name table",
            "CTPV_CD": "Preserved only as raw frequencies; not used to infer installation geography",
        },
        "limitations": [
            "The denominator covers API records, not a census of every physically installed device or every kiosk category.",
            "Feature availability is an administrative data value, not an on-site usability test or a legal-compliance judgment.",
            "The eight fields are not combined into a legal-compliance or accessibility score.",
            "A current snapshot contains no same-device before/after history. Modification/update timestamps are not installation or feature-adoption dates.",
            "Regional rates use currently recorded installation codes, unadjusted for device model, agency, age or sample composition. Counts accompany each rate.",
            "Region display names are derived from observed address first tokens; the complete legal administrative code table has not been validated.",
            "Complete partition counts and an unchanged global total do not establish transactional consistency across all server queries.",
            "If raw pages are absent from a later checkout, the CSV hash and collection manifest can be checked but raw-page validation cannot be repeated until originals are restored.",
        ],
    }
    outputs = HERE / "outputs"
    outputs.mkdir(exist_ok=True)
    tables = {
        f"mois_features_{args.snapshot}.csv": features,
        f"mois_region_comparison_{args.snapshot}.csv": regions,
        f"mois_raw_value_frequencies_{args.snapshot}.csv": frequencies,
        f"mois_record_flow_{args.snapshot}.csv": [
            {"snapshot_date": args.snapshot, "stage": key, "records_or_keys_n": value}
            for key, value in flow.items()],
    }
    for filename, table in tables.items():
        write_csv(outputs / filename, table)
    summary["output_tables"] = [{"path": f"outputs/{name}", "rows": len(table),
                                 "sha256": sha256(outputs / name)} for name, table in tables.items()]
    target = outputs / f"mois_summary_{args.snapshot}.json"
    temp = target.with_suffix(".json.tmp")
    temp.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(target)
    print(f"MOIS snapshot {args.snapshot}: {len(rows)} rows; {len(used)} explicitly in-use records.")
    print(f"Validated {integrity['raw_pages_locally_verified']}/{integrity['expected_raw_evidence_files']} raw evidence files locally.")
    for feature in summary["national_features"]:
        print(f"{feature['feature']}: yes={feature['yes']}, no={feature['no']}, "
              f"unknown={feature['unknown']}, yes/all={feature['yes_pct_all']}%")


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, AssertionError) as exc:
        print(f"Analysis stopped: {exc}", file=sys.stderr)
        sys.exit(1)
