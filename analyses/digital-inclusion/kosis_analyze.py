#!/usr/bin/env python3
"""Offline KOSIS trend/reconciliation analysis; no credentials or HTTP calls."""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date
from pathlib import Path


HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUTPUT = HERE / "outputs"
TABLE_INDICATORS = {
    "DT_12017N008": "digital_informatization_overall",
    "DT_12017N009": "digital_informatization_access",
    "DT_12017N0010": "digital_informatization_capability",
    "DT_12017N0011": "digital_informatization_utilization",
}
POPULATIONS = {"disabled", "older_adults", "low_income", "farmers_fishers", "vulnerable_weighted"}
UNIT = "index_general_population_100"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def decimal_or_none(raw):
    if raw is None or not str(raw).strip():
        return None
    try:
        result = Decimal(str(raw))
    except InvalidOperation:
        return None
    if not result.is_finite():
        return None
    if result < 0:
        raise ValueError("Negative digital-informatization index requires source review")
    return result  # 100 is a reference, not an upper bound.


def text_number(value):
    return "" if value is None else format(value.normalize(), "f")


def difference_record(rows, start_year, end_year):
    by_year = {int(r["survey_year"]): decimal_or_none(r["value"]) for r in rows}
    start, end = by_year.get(start_year), by_year.get(end_year)
    if start is None or end is None:
        return None
    interval = end_year - start_year
    if interval <= 0:
        return None
    return {
        "start_year": start_year, "end_year": end_year,
        "start_value": text_number(start), "end_value": text_number(end),
        "change_index_points": text_number(end - start), "year_intervals": interval,
        "mean_annual_index_point_change": text_number(((end - start) / interval).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)),
        "missing_numeric_years": [year for year in range(start_year, end_year + 1) if by_year.get(year) is None],
        "measurement_composition_changes_adjusted": False,
    }


def summarize_series(rows, trend_start):
    grouped = defaultdict(list)
    keys = set()
    for row in rows:
        year = int(row["survey_year"])
        key = (row["indicator"], row["population"], year)
        if key in keys:
            raise ValueError("Duplicate indicator/population/year observation")
        keys.add(key)
        if row["table_id"] not in TABLE_INDICATORS or TABLE_INDICATORS[row["table_id"]] != row["indicator"]:
            raise ValueError("Table-to-indicator mapping differs from the verified scope")
        if row["population"] not in POPULATIONS or row["unit"] != UNIT:
            raise ValueError("Population or unit differs from the verified scope")
        if decimal_or_none(row["value"]) != decimal_or_none(row["raw_value"]):
            raise ValueError("Normalized numeric value does not match the raw statistic")
        grouped[(row["indicator"], row["population"])].append(row)
    if len(grouped) != len(TABLE_INDICATORS) * len(POPULATIONS):
        raise ValueError("Expected all four indicators and five populations")
    common_years = set.intersection(*[
        {int(r["survey_year"]) for r in series
         if int(r["survey_year"]) >= trend_start and decimal_or_none(r["value"]) is not None}
        for series in grouped.values()
    ])

    coverage, trends, changes, latest = [], [], [], []
    for (indicator, population), series in sorted(grouped.items()):
        series.sort(key=lambda r: int(r["survey_year"]))
        years = [int(row["survey_year"]) for row in series]
        numeric = {int(row["survey_year"]): decimal_or_none(row["value"]) for row in series}
        metadata = {"indicator": indicator, "population": population,
                    "population_label": series[0]["population_label"], "unit": UNIT}
        coverage.append({**metadata, "first_year": min(years), "last_year": max(years),
                         "rows": len(series), "numeric_rows": sum(v is not None for v in numeric.values()),
                         "missing_years": "|".join(str(y) for y in range(min(years), max(years) + 1) if y not in numeric),
                         "nonnumeric_years": "|".join(str(y) for y, v in numeric.items() if v is None)})
        eligible = [year for year, value in numeric.items() if year >= trend_start and value is not None]
        if len(eligible) >= 2:
            result = difference_record(series, min(eligible), max(eligible))
            trends.append({**metadata, "period": "primary_descriptive_period", **result})
            if len(common_years) >= 2 and (min(eligible), max(eligible)) != (min(common_years), max(common_years)):
                trends.append({**metadata, "period": "common_numeric_period",
                               **difference_record(series, min(common_years), max(common_years))})
        recent = difference_record(series, 2021, 2025)
        if recent:
            trends.append({**metadata, "period": "api_2021_2025_overlap_period", **recent})
        for year in sorted(numeric):
            if year < trend_start + 1 or numeric[year] is None or numeric.get(year - 1) is None:
                continue
            changes.append({**metadata, "before_year": year - 1, "after_year": year,
                            "before_value": text_number(numeric[year - 1]), "after_value": text_number(numeric[year]),
                            "change_index_points": text_number(numeric[year] - numeric[year - 1])})
        if eligible:
            year = max(eligible)
            latest.append({**metadata, "survey_year": year, "value": text_number(numeric[year]),
                           "general_population_reference": 100,
                           "gap_index_points": text_number(Decimal(100) - numeric[year])})
    return coverage, trends, changes, latest, sorted(common_years)


def reconcile(rows, baseline):
    indexed = {(row["indicator"], row["population"], int(row["survey_year"])): row for row in rows}
    result = []
    for report in baseline:
        if report["indicator"] not in TABLE_INDICATORS.values():
            continue
        api = indexed.get((report["indicator"], report["population"], int(report["survey_year"])))
        report_value = decimal_or_none(report["value"])
        api_value = decimal_or_none(api["value"]) if api else None
        if api is None:
            status = "api_observation_absent"
        elif api["unit"] != report["unit"]:
            status = "unit_mismatch"
        elif api_value is None:
            status = "api_value_nonnumeric"
        elif report_value is None:
            status = "report_value_nonnumeric"
        else:
            status = "match" if api_value == report_value else "numeric_difference"
        result.append({
            "indicator": report["indicator"], "population": report["population"],
            "survey_year": report["survey_year"], "report_value": report["value"],
            "api_raw_value": api["raw_value"] if api else "", "api_value": text_number(api_value),
            "api_minus_report_index_points": text_number(api_value - report_value) if status in {"match", "numeric_difference"} else "",
            "status": status, "report_source_url": report["source_url"],
            "report_source_locator": report["source_locator"],
            "api_source_url": api["source_url"] if api else "",
            "api_table_id": api["table_id"] if api else "",
            "api_last_modified": api["last_modified"] if api else "",
        })
    return result


def write_csv(path, records):
    if not records:
        raise ValueError("Refused to write an empty analysis table")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows({key: "|".join(map(str, value)) if isinstance(value, list) else value for key, value in row.items()} for row in records)


def load_inputs(snapshot):
    csv_path = DATA / f"kosis_digital_divide_{snapshot}.csv"
    manifest_path = DATA / f"kosis_manifest_{snapshot}.json"
    metadata_path = DATA / f"kosis_metadata_{snapshot}.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    rows = read_csv(csv_path)
    if manifest.get("collection_complete") is not True or metadata.get("metadata_collection_complete") is not True:
        raise ValueError("KOSIS metadata/data collection is incomplete")
    if metadata.get("snapshot") != snapshot or manifest.get("snapshot") != snapshot:
        raise ValueError("KOSIS metadata snapshot differs from the requested date")
    if manifest.get("csv_path") != str(csv_path.relative_to(HERE)):
        raise ValueError("KOSIS manifest references a different dataset")
    if manifest.get("csv_sha256") != digest(csv_path) or manifest.get("rows") != len(rows):
        raise ValueError("KOSIS CSV differs from the collection manifest")
    if set(metadata["tables"]) != set(TABLE_INDICATORS):
        raise ValueError("KOSIS table coverage differs from the analysis plan")
    expected = set()
    for table, parts in metadata["tables"].items():
        periods = {str(r["PRD_DE"]) for r in parts["PRD"] if "PRD_DE" in r}
        if not periods or any(len(year) != 4 or not year.isdigit() for year in periods):
            raise ValueError("KOSIS metadata periods are not annual years")
        items = {str(r["ITM_ID"]) for r in parts["ITM"] if r.get("OBJ_ID") == "ITEM"}
        groups = {str(r["ITM_ID"]) for r in parts["ITM"] if r.get("OBJ_ID") != "ITEM"}
        if len(items) != 1 or len(groups) != 5:
            raise ValueError("KOSIS metadata dimensions changed; review the analysis scope")
        expected.update((table, item, group, year) for item in items for group in groups for year in periods)
    actual = [(r["table_id"], r["item_id"], r["classification_id"], r["survey_year"]) for r in rows]
    if len(set(actual)) != len(actual) or set(actual) != expected:
        raise ValueError("KOSIS observations do not cover the metadata product exactly")

    checked, missing, raw_paths = 0, 0, set()
    indexed_rows = dict(zip(actual, rows))
    original_data_cells = set()
    for request in metadata.get("requests", []) + manifest.get("requests", []):
        relative = request["raw_path"]
        if relative in raw_paths:
            continue
        raw_paths.add(relative)
        path = (HERE / relative).resolve()
        if not path.is_relative_to(HERE):
            raise ValueError("Source manifest path is outside the analysis directory")
        if not path.exists():
            missing += 1
            continue
        if digest(path) != request["response_sha256"]:
            raise ValueError("KOSIS raw response checksum differs from source manifest")
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if request.get("response_status") == "no_data_30":
            if (request["parameters"].get("method") != "getMeta"
                    or request["parameters"].get("type") != "CMMT"
                    or not isinstance(payload, dict) or str(payload.get("err")) != "30"
                    or request["row_count"] != 0):
                raise ValueError("Unexpected no-data response outside optional table comments")
            payload = []
        if not isinstance(payload, list) or len(payload) != request["row_count"]:
            raise ValueError("KOSIS raw response is an error or has an unexpected row count")
        if request["parameters"].get("method") == "getMeta":
            table, kind = request["parameters"]["tblId"], request["parameters"]["type"]
            if kind in metadata["tables"][table] and payload != metadata["tables"][table][kind]:
                raise ValueError("KOSIS normalized metadata differs from the original response")
        elif request["parameters"].get("method") == "getList":
            for original in payload:
                key = (original["TBL_ID"], original["ITM_ID"], original["C1"], original["PRD_DE"])
                if key not in indexed_rows or key in original_data_cells:
                    raise ValueError("KOSIS raw statistic identity is unexpected or repeated")
                normalized = indexed_rows[key]
                raw_value = "" if original.get("DT") is None else str(original["DT"])
                if (normalized["raw_value"] != raw_value
                        or normalized["unit_source"] != original.get("UNIT_NM", "")
                        or normalized["population_label"] != original.get("C1_NM", "")
                        or normalized["last_modified"] != original.get("LST_CHN_DE", "")):
                    raise ValueError("KOSIS CSV content differs from its original statistic")
                if original.get("ORG_ID") != "127" or original.get("PRD_SE") not in {"A", "Y"}:
                    raise ValueError("Unexpected original KOSIS organization or annual frequency")
                if "frequency_source" in normalized and normalized["frequency_source"] != original["PRD_SE"]:
                    raise ValueError("KOSIS frequency source was not preserved")
                original_data_cells.add(key)
        checked += 1
    if missing == 0 and original_data_cells != expected:
        raise ValueError("Local KOSIS data responses do not cover every normalized observation")
    integrity = {"metadata_product_cells": len(expected), "unique_data_cells": len(actual),
                 "metadata_product_matches_csv": True, "csv_sha256_verified": True,
                 "raw_responses_locally_verified": checked, "raw_responses_not_present": missing,
                 "raw_data_cells_locally_verified": len(original_data_cells),
                 "all_raw_responses_locally_verified": bool(raw_paths) and missing == 0}
    return rows, manifest, metadata, [csv_path, manifest_path, metadata_path], integrity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True)
    args = parser.parse_args()
    date.fromisoformat(args.snapshot)
    plan_path = HERE / "kosis_analysis_plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    rows, manifest, metadata, inputs, integrity = load_inputs(args.snapshot)
    coverage, trends, changes, latest, common_years = summarize_series(rows, plan["primary_trend_start_year"])
    baseline_path = DATA / "baseline_indicators.csv"
    comparison = reconcile(rows, read_csv(baseline_path))
    counts = Counter(row["status"] for row in comparison)
    OUTPUT.mkdir(exist_ok=True)
    tables = {
        f"kosis_coverage_{args.snapshot}.csv": coverage,
        f"kosis_trends_{args.snapshot}.csv": trends,
        f"kosis_annual_changes_{args.snapshot}.csv": changes,
        f"kosis_latest_gaps_{args.snapshot}.csv": latest,
        f"kosis_report_comparison_{args.snapshot}.csv": comparison,
    }
    for filename, records in tables.items():
        write_csv(OUTPUT / filename, records)
    policy_year = int(plan["policy_date"][:4])
    summary = {
        "snapshot_date": args.snapshot, "analysis_type": plan["status"],
        "causal_verdict": plan["causal_verdict"], "rows": len(rows),
        "integrity": integrity,
        "earliest_survey_year": min(int(row["survey_year"]) for row in rows),
        "latest_survey_year": max(int(row["survey_year"]) for row in rows),
        "latest_numeric_survey_year": max((int(row["survey_year"]) for row in rows if decimal_or_none(row["value"]) is not None), default=None),
        "policy_year_or_later_rows": sum(int(row["survey_year"]) >= policy_year for row in rows),
        "numeric_policy_year_or_later_rows": sum(int(row["survey_year"]) >= policy_year and decimal_or_none(row["value"]) is not None for row in rows),
        "primary_trend_start_year": plan["primary_trend_start_year"],
        "common_numeric_years_since_trend_start": common_years,
        "excluded_earlier_year_rows": sum(int(row["survey_year"]) < plan["primary_trend_start_year"] for row in rows),
        "report_reconciliation": {"report_cells": len(comparison), "status_counts": dict(counts), "baseline_overwritten": False},
        "coverage": coverage, "trends": trends, "latest_gaps": latest,
        "input_sha256": {str(p.relative_to(HERE)): digest(p) for p in inputs + [baseline_path, plan_path]},
        "limitations": plan["rules"] + ["2016년 이후의 모든 조사설계가 동일하다고 검증한 것은 아니다."],
        "output_tables": [{"path": f"outputs/{filename}", "rows": len(records), "sha256": digest(OUTPUT / filename)} for filename, records in tables.items()],
    }
    (OUTPUT / f"kosis_summary_{args.snapshot}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"KOSIS: {len(rows)} observations; report comparison: {dict(counts)}; causal effect not identified.")


if __name__ == "__main__":
    main()
