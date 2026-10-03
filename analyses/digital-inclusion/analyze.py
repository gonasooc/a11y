#!/usr/bin/env python3
"""Recompute descriptive outputs offline using only Python's standard library.

No raw registry rows or policy effects are inferred from aggregate observations.
Run: python3 analyses/digital-inclusion/analyze.py
"""

import csv
import hashlib
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUTPUT = HERE / "outputs"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rounded(value, places="0.1"):
    return float(Decimal(str(value)).quantize(Decimal(places), rounding=ROUND_HALF_UP))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def registry_summary(rows, metadata):
    groups = defaultdict(dict)
    for row in rows:
        dimension, label = row["dimension"], row["label"]
        require(label not in groups[dimension], f"Duplicate registry cell: {dimension}/{label}")
        require(row["unit"] == "models", "Registry unit must be models, not installed devices")
        require(row["evidence_status"] == metadata["evidence_status"], "Registry provenance mismatch")
        value = int(row["count"])
        require(value >= 0, "Negative registry count")
        groups[dimension][label] = value

    require(set(groups) == {"registration_number_year", "company_type", "product_class"},
            "Unexpected registry dimensions")
    total = metadata["total_models"]
    years = groups["registration_number_year"]
    require(set(years) == {"2023", "2024", "2025", "2026"}, "Registry years changed; review analysis")
    require(sum(years.values()) == total, "Year totals do not reconcile with the documented snapshot")
    require(sum(groups["company_type"].values()) == total, "Company types do not reconcile")
    remainder = total - sum(groups["product_class"].values())
    require(remainder >= 0, "Product classes exceed snapshot total")
    groups["product_class"]["remaining_classes"] = remainder

    composition = []
    for dimension, cells in groups.items():
        for label, count in cells.items():
            composition.append({
                "dimension": dimension, "label": label, "count": count,
                "denominator_models": total,
                "share_percent": rounded(Decimal(count) * 100 / total),
                "evidence_status": metadata["evidence_status"],
            })

    comparisons = []
    for earlier, later in [("2024", "2025"), ("2025", "2026")]:
        base, value = years[earlier], years[later]
        comparisons.append({
            "earlier_registration_number_year": earlier,
            "later_registration_number_year": later,
            "earlier_count": base, "later_count": value,
            "arithmetic_count_difference": value - base,
            "arithmetic_percent_difference": rounded(Decimal(value - base) * 100 / base),
            "is_policy_effect": False,
            "is_same_period_growth_rate": False,
        })
    return composition, comparisons


def baseline_summary(rows, policy_year):
    by_series = defaultdict(list)
    seen = set()
    for row in rows:
        year = int(row["survey_year"])
        require(year < policy_year, f"A post-policy observation entered the baseline: {year}")
        require(row["source_url"].startswith("https://"), "Baseline row lacks its original source")
        require(bool(row["source_locator"]), "Baseline source location is empty")
        require(bool(row["verification_status"]), "Baseline verification status is empty")
        key = (row["indicator"], row["population"], year)
        require(key not in seen, f"Duplicate baseline cell: {key}")
        seen.add(key)
        value = Decimal(row["value"])
        require(value.is_finite() and value >= 0, "Baseline value is invalid")
        by_series[(row["indicator"], row["population"], row["unit"])].append((year, value, row))

    changes = []
    period_changes = []
    latest_gaps = []
    for (indicator, population, unit), observations in sorted(by_series.items()):
        observations.sort(key=lambda item: item[0])
        for previous, current in zip(observations, observations[1:]):
            before_year, before, before_row = previous
            after_year, after, after_row = current
            if after_year - before_year != 1:
                continue  # Never silently treat a multi-year gap as a one-year change.
            changes.append({
                "indicator": indicator, "population": population,
                "before_survey_year": before_year, "after_survey_year": after_year,
                "before_value": str(before), "after_value": str(after),
                "difference": str(after - before), "input_unit": unit,
                "policy_period": "both_pre_policy",
                "before_verification": before_row["verification_status"],
                "after_verification": after_row["verification_status"],
            })
        by_year = {year: value for year, value, _ in observations}
        if 2021 in by_year and 2025 in by_year:
            period_changes.append({
                "indicator": indicator, "population": population,
                "before_survey_year": 2021, "after_survey_year": 2025,
                "before_value": str(by_year[2021]), "after_value": str(by_year[2025]),
                "difference": str(by_year[2025] - by_year[2021]),
                "input_unit": unit, "policy_period": "both_pre_policy",
            })
        if indicator.startswith("digital_informatization_") and 2025 in by_year:
            latest_gaps.append({
                "survey_year": 2025, "indicator": indicator, "population": population,
                "general_population_reference": 100,
                "gap_index_points": str(100 - by_year[2025]),
            })
    return changes, period_changes, latest_gaps


def main():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    metadata = json.loads((DATA / "archived_registry_metadata.json").read_text(encoding="utf-8"))
    require(not plan["preregistered"], "This analysis has prior exposure; it cannot claim preregistration")
    require(not metadata["upstream_refetched"], "New raw evidence requires a reviewed analysis plan")
    registry = read_csv(DATA / "archived_registry_counts.csv")
    baseline = read_csv(DATA / "baseline_indicators.csv")
    require(bool(baseline), "No baseline observations")
    composition, comparisons = registry_summary(registry, metadata)
    changes, period_changes, latest_gaps = baseline_summary(baseline, int(plan["treatment_date"][:4]))
    require(bool(changes), "No adjacent-year baseline comparisons")

    # Keep the initial baseline independent of subsequently collected API data.
    inputs = [DATA / name for name in (
        "archived_registry_counts.csv", "archived_registry_metadata.json",
        "baseline_indicators.csv", "source_manifest_baseline.json",
    )] + [HERE / "plan.json"]
    hashes = {str(path.relative_to(HERE)): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    result = {
        "analysis_id": plan["id"], "analysis_date": plan["analysis_date"],
        "status": plan["status"], "causal_verdict": plan["inference_now"],
        "registry_evidence_status": metadata["evidence_status"],
        "registry_observed_on": metadata["source_observed_on"],
        "registry_refetched": metadata["upstream_refetched"],
        "total_models_in_documented_snapshot": metadata["total_models"],
        "registry_comparisons": comparisons,
        "baseline_rows": len(baseline), "pre_policy_changes": changes,
        "baseline_2021_to_2025": period_changes,
        "baseline_2025_general_population_gaps": latest_gaps,
        "warnings": [metadata["coverage_warning"], metadata["unit_warning"],
                     "차이는 기술통계이며 인과효과 추정치가 아니다.",
                     "일반국민=100인 상대지수의 차이는 지수 포인트이다. 백분율 지표의 차이는 퍼센트포인트이다.",
                     "서로 다른 조사 표본과 측정 기준의 차이를 보정하지 않았다. 신뢰구간과 유의성은 추정하지 않는다."],
        "input_sha256": hashes,
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "registry_composition.csv", composition, list(composition[0]))
    write_csv(OUTPUT / "baseline_changes.csv", changes, list(changes[0]))
    (OUTPUT / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Validated {len(registry)} registry aggregates and {len(baseline)} baseline observations.")
    print(f"Wrote 3 outputs to {OUTPUT}; causal verdict: {plan['inference_now']}.")


if __name__ == "__main__":
    main()
