"""Offline descriptive analysis of PPS kiosk registrations and order changes.

The primary measure is the signed change in procurement requests in each receipt
month, not delivered/installed equipment or certified accessible equipment.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from api_common import write_json


HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUTPUT = HERE / "outputs"
CORE_CODES = {"4321151401": "증명발급기", "4321151402": "무인안내시스템"}
CLASS_CODE = "43211514"


def parse_date(value: str) -> date:
    digits = "".join(c for c in value if c.isdigit())
    if len(digits) < 8:
        raise ValueError("Missing or malformed date")
    return date(int(digits[:4]), int(digits[4:6]), int(digits[6:8]))


def number(value: str) -> Decimal:
    if not value.strip():
        raise ValueError("Missing numeric value; refused to substitute zero")
    parsed = Decimal(value)
    if not parsed.is_finite():
        raise ValueError("Non-finite numeric value")
    return parsed


def plain(value: Decimal) -> str:
    return format(value.normalize(), "f")


def sums(rows: list[dict], field: str) -> str:
    return plain(sum((number(row[field]) for row in rows), Decimal(0)))


def months(start: date, end: date) -> list[str]:
    result = []
    cursor = start.replace(day=1)
    while cursor <= end:
        result.append(cursor.strftime("%Y-%m"))
        cursor = date.fromordinal(date(cursor.year, cursor.month, calendar.monthrange(cursor.year, cursor.month)[1]).toordinal() + 1)
    return result


def load(kind: str) -> tuple[list[dict], dict]:
    path = DATA / f"pps_{kind}.csv"
    manifest = json.loads((DATA / f"pps_{kind}_manifest.json").read_text())
    if not manifest.get("collection_complete"):
        raise ValueError(f"Incomplete {kind} collection")
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["csv_sha256"]:
        raise ValueError(f"{kind} input hash mismatch")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != manifest["rows"]:
        raise ValueError(f"{kind} row count mismatch")
    start, end = date.fromisoformat(manifest["start"]), date.fromisoformat(manifest["end"])
    date_field = "rgstDt" if kind == "registrations" else "dlvrReqRcptDate"
    key_fields = ("shopngCntrctNo", "shopngCntrctSno", "prdctIdntNo") if kind == "registrations" else ("dlvrReqNo", "dlvrReqChgOrd", "prdctSno")
    identities = set()
    for row in rows:
        identity = tuple(row[k] for k in key_fields)
        if not all(identity) or identity in identities:
            raise ValueError(f"Missing or duplicated {kind} record identity")
        identities.add(identity)
        if row["prdctClsfcNo"] != CLASS_CODE or row["prdctClsfcNoNm"] != "컴퓨터키오스크":
            raise ValueError("Query returned an out-of-scope product class")
        if not start <= parse_date(row[date_field]) <= end:
            raise ValueError("Record outside the requested time range")
        row["month"] = parse_date(row[date_field]).strftime("%Y-%m")
    # Every monthly delivery query must be complete, including observed zeros.
    if kind == "deliveries":
        query_groups = defaultdict(list)
        for request in manifest["requests"]:
            params = request["parameters"]
            query_groups[(params["inqryBgnDate"], params["inqryEndDate"])].append(request)
        observed_months = set()
        for (begin, finish), requests in query_groups.items():
            first, last = parse_date(begin), parse_date(finish)
            if first.day != 1 or last.day != calendar.monthrange(last.year, last.month)[1] or first.month != last.month:
                raise ValueError("Partial month in delivery queries")
            observed_months.add(first.strftime("%Y-%m"))
            if sum(r["received_count"] for r in requests) != requests[0]["total_count"]:
                raise ValueError("Incomplete delivery query pages")
            for row in rows:
                if row["month"] == first.strftime("%Y-%m"):
                    for field in ["incdecQty", "incdecAmt", "prdctQty", "prdctAmt"]:
                        number(row[field])
        if observed_months != set(months(start, end)):
            raise ValueError("Missing delivery month")
    return rows, manifest


def metrics(rows: list[dict]) -> dict:
    devices = [r for r in rows if r["prdctUnit"] == "대" and r["optnDivCdNm"] == "대표품목"]
    excluded = [r for r in rows if r not in devices]
    return {
        "change_rows": len(rows),
        "request_ids_with_changes": len({r["dlvrReqNo"] for r in rows}),
        "suppliers_with_changes": len({r["corpNm"] for r in rows}),
        "requesting_institutions": len({r["dminsttCd"] for r in rows}),
        "net_request_amount_krw": sums(rows, "incdecAmt"),
        "representative_device_change_rows": len(devices),
        "representative_device_net_quantity": sums(devices, "incdecQty"),
        "representative_device_net_amount_krw": sums(devices, "incdecAmt"),
        "other_unit_or_option_rows": len(excluded),
        "other_unit_or_option_net_amount_krw": sums(excluded, "incdecAmt"),
    }


def comparison(rows: list[dict], first_month: int, last_month: int) -> dict:
    by_year = {year: metrics([r for r in rows if r["month"][:4] == str(year) and first_month <= int(r["month"][5:]) <= last_month]) for year in (2025, 2026)}
    changes = {}
    for key in ["net_request_amount_krw", "representative_device_net_quantity", "representative_device_net_amount_krw"]:
        before, after = Decimal(by_year[2025][key]), Decimal(by_year[2026][key])
        changes[key] = {"difference": plain(after - before), "percent_change": None if before <= 0 else plain(((after - before) / before * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))}
    return {"months": [first_month, last_month], "before_2025": by_year[2025], "after_2026": by_year[2026], "changes": changes}


def exact_date_comparison(rows: list[dict]) -> dict:
    selected = [r for r in rows if "01-22" <= parse_date(r["dlvrReqRcptDate"]).strftime("%m-%d") <= "09-30"]
    result = comparison(selected, 1, 9)
    result.pop("months")
    return {"month_day_range": ["01-22", "09-30"], **result}


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        raise ValueError("Refused to write an unspecified empty table")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def registry_metrics(rows: list[dict]) -> dict:
    return {
        "contract_product_registration_rows": len(rows),
        "distinct_product_ids": len({r["prdctIdntNo"] for r in rows}),
        "distinct_supplier_names": len({r["cntrctCorpNm"] for r in rows}),
        "distinct_manufacturer_names": len({r["prdctMakrNm"] for r in rows}),
    }


def analyze() -> dict:
    registrations, reg_manifest = load("registrations")
    deliveries, delivery_manifest = load("deliveries")
    if (reg_manifest["start"], reg_manifest["end"]) != (delivery_manifest["start"], delivery_manifest["end"]):
        raise ValueError("Registration and delivery periods differ")
    period_months = months(date.fromisoformat(delivery_manifest["start"]), date.fromisoformat(delivery_manifest["end"]))
    if not set(months(date(2025, 1, 1), date(2026, 9, 30))) <= set(period_months):
        raise ValueError("Insufficient complete months for the fixed comparison")
    core_deliveries = [r for r in deliveries if r["dtilPrdctClsfcNo"] in CORE_CODES]
    core_registrations = [r for r in registrations if r["dtilPrdctClsfcNo"] in CORE_CODES]
    OUTPUT.mkdir(exist_ok=True)
    monthly = []
    for scope, scoped in [("core_kiosks", core_deliveries), ("computer_kiosk_class_all", deliveries)]:
        for month in period_months:
            monthly.append({"scope": scope, "month": month, **metrics([r for r in scoped if r["month"] == month])})
    write_csv(OUTPUT / "pps_monthly.csv", monthly)
    categories = sorted({(r["dtilPrdctClsfcNo"], r["dtilPrdctClsfcNoNm"]) for r in deliveries + registrations})
    category_monthly = []
    for code, name in categories:
        for month in period_months:
            category_monthly.append({"product_code": code, "product_name": name, "month": month, **metrics([r for r in deliveries if r["dtilPrdctClsfcNo"] == code and r["month"] == month])})
    write_csv(OUTPUT / "pps_category_monthly.csv", category_monthly)
    unit_options = []
    for scope, scoped in [("core_kiosks", core_deliveries), ("computer_kiosk_class_all", deliveries)]:
        groups = sorted({(r["prdctUnit"], r["optnDivCdNm"]) for r in scoped})
        for unit, option in groups:
            subset = [r for r in scoped if (r["prdctUnit"], r["optnDivCdNm"]) == (unit, option)]
            unit_options.append({"scope": scope, "unit": unit, "option": option, "rows": len(subset), "net_quantity_in_stated_unit": sums(subset, "incdecQty"), "net_amount_krw": sums(subset, "incdecAmt")})
    write_csv(OUTPUT / "pps_units_options.csv", unit_options)
    registry_monthly = []
    for month in period_months:
        registry_monthly.append({"month": month, **registry_metrics([r for r in core_registrations if r["month"] == month])})
    write_csv(OUTPUT / "pps_registrations_monthly.csv", registry_monthly)
    firms = []
    for name in sorted({r["cntrctCorpNm"] for r in core_registrations}):
        subset = [r for r in core_registrations if r["cntrctCorpNm"] == name]
        firms.append({"supplier_name": name, "manufacturer_names": " | ".join(sorted({r["prdctMakrNm"] for r in subset})), "enterprise_types_at_retrieval": " | ".join(sorted({r["entrprsDivNm"] for r in subset})), "first_registration_in_collected_window": min(r["rgstDt"] for r in subset), **registry_metrics(subset)})
    write_csv(OUTPUT / "pps_suppliers.csv", firms)
    summary = {
        "analysis_type": "exploratory_descriptive_not_causal",
        "input_sha256": {"pps_registrations.csv": reg_manifest["csv_sha256"], "pps_deliveries.csv": delivery_manifest["csv_sha256"]},
        "period": [delivery_manifest["start"], delivery_manifest["end"]],
        "core_product_codes": CORE_CODES,
        "excluded_from_core": {code: name for code, name in categories if code not in CORE_CODES},
        "metric_definition": "Sum signed incdecQty/incdecAmt in receipt month across all change orders. Quantity is restricted to representative items with unit 대. No delivery/installation/compliance inference.",
        "same_month_comparisons": {"feb_sep_primary": comparison(core_deliveries, 2, 9), "jan_sep_including_transition_month": comparison(core_deliveries, 1, 9), "feb_jun_before_medium_firm_phase": comparison(core_deliveries, 2, 6)},
        "same_calendar_dates_from_legal_start": exact_date_comparison(core_deliveries),
        "january_transition_detail": {str(year): {label: metrics([r for r in core_deliveries if r["month"] == f"{year}-01" and first <= parse_date(r["dlvrReqRcptDate"]).day <= last]) for label, first, last in [("days_01_21", 1, 21), ("days_22_31", 22, 31)]} for year in (2025, 2026)},
        "category_feb_sep_comparisons": {name: comparison([r for r in core_deliveries if r["dtilPrdctClsfcNo"] == code], 2, 9) for code, name in CORE_CODES.items()},
        "registrations": {
            "all_class": registry_metrics(registrations), "core": registry_metrics(core_registrations),
            "by_product_category": {name: registry_metrics([r for r in registrations if r["dtilPrdctClsfcNo"] == code]) for code, name in categories},
            "core_feb_sep_by_year": {str(year): registry_metrics([r for r in core_registrations if r["month"][:4] == str(year) and 2 <= int(r["month"][5:]) <= 9]) for year in (2025, 2026)},
            "enterprise_types": dict(Counter(r["entrprsDivNm"] or "unknown" for r in core_registrations)),
        },
        "quality": {
            "delivery_rows": len(deliveries), "core_delivery_rows": len(core_deliveries),
            "negative_amount_change_rows": sum(number(r["incdecAmt"]) < 0 for r in deliveries),
            "negative_quantity_change_rows": sum(number(r["incdecQty"]) < 0 for r in deliveries),
            "noninitial_change_rows": sum(int(r["dlvrReqChgOrd"]) != 0 for r in deliveries),
            "final_flag_counts": dict(Counter(r["fnlDlvrReqYn"] or "unknown" for r in deliveries)),
            "missing_initial_date_rows": sum(not r["IntlCntrctDlvrReqDate"] for r in deliveries),
            "initial_request_before_window_rows": sum(bool(r["IntlCntrctDlvrReqDate"]) and parse_date(r["IntlCntrctDlvrReqDate"]) < date.fromisoformat(delivery_manifest["start"]) for r in deliveries),
            "registration_calls": len(reg_manifest["requests"]), "delivery_calls": len(delivery_manifest["requests"]),
            "all_pages_complete": True, "record_id_duplicates": 0,
        },
        "limitations": [
            "A signed procurement request flow includes amendments and cancellations of earlier requests; it is not installed units or actual expenditure.",
            "Core scope is certificate dispensers and unattended information systems, not every kiosk category or the private market.",
            "Registration rows repeat product IDs across contracts. No NIA certification, first-ever model entry, or legal compliance inference is made.",
            "Current enterprise classification does not identify size on the policy date, and 중소기업 does not separate medium and small firms.",
            "Data availability and historical revisions are those of this API snapshot; even fully paged API data does not prove population completeness.",
            "January 2026 is a transition month. Adjacent disability law changes, demand composition, procurement budgets and certification rules confound attribution.",
        ],
    }
    write_json(OUTPUT / "pps_summary.json", summary)
    return summary


def self_test():
    initial = {"dlvrReqNo": "sample", "corpNm": "sample", "dminsttCd": "sample", "prdctUnit": "대", "optnDivCdNm": "대표품목", "incdecQty": "3", "incdecAmt": "300"}
    amendment = {**initial, "incdecQty": "2", "incdecAmt": "200"}
    assert metrics([initial, amendment])["representative_device_net_quantity"] == "5"
    cancellation = {**initial, "incdecQty": "-3", "incdecAmt": "-300"}
    assert metrics([initial, cancellation])["net_request_amount_krw"] == "0"
    option = {**initial, "optnDivCdNm": "별도구매", "incdecQty": "1", "incdecAmt": "10"}
    result = metrics([initial, option])
    assert result["representative_device_net_quantity"] == "3"
    assert result["net_request_amount_krw"] == "310"
    try:
        number("")
    except ValueError:
        pass
    else:
        raise AssertionError("Missing value became zero")
    print("PPS amendment/cancellation/unit/missing-value checks passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        result = analyze()
        print(json.dumps({"status": "complete", "quality": result["quality"], "primary_comparison": result["same_month_comparisons"]["feb_sep_primary"]}, ensure_ascii=False, indent=2))
