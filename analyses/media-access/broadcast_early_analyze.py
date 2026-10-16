"""Summarize the 2012-2016 disability-broadcast results and reconcile them with the official press releases."""

from __future__ import annotations

import hashlib
import json

from broadcast_analyze import DATA, OUT, SERVICES, AnalysisError, compliance, group_summary, numeric, operators_of, read_csv, write_csv


INPUTS = ["broadcast_operator_years_2012_2016.csv", "kmcc_early_statements.csv",
          "broadcast_parse_notes_2012_2016.json", "kmcc_manifest.json"]
# 공식 표의 중앙지상파는 지상파 일련번호 1~4다. 연도마다 이름 표기가 달라 두 가지 표기로 확인한다.
CENTRAL = (("한국방송공사", "KBS"), ("문화방송", "MBC"), ("SBS",), ("교육방송", "EBS"))


def members(operators: list[dict], group: str) -> list[dict]:
    terrestrial = [row for row in operators if row["group"] == "지상파"]
    if group == "all":
        return operators
    if group == "central":
        central = [row for row in terrestrial if int(row["row_no"]) <= 4]
        if len(central) != 4 or any(not any(token in row["operator"] for token in tokens)
                                    for tokens, row in zip(CENTRAL, central)):
            raise AnalysisError("지상파 일련번호 1~4가 중앙 지상파 4사가 아니다")
        return central
    if group == "regional":
        return [row for row in terrestrial if int(row["row_no"]) > 4]
    if group == "news_general_pp":
        return [row for row in operators if row["group"] in ("보도PP", "종편PP")]
    return [row for row in operators if row["group"] == group]


def below(row: dict, service: str) -> bool:
    services = SERVICES if service == "any" else (service,)
    pairs = [(numeric(row[f"{key}_target"]), numeric(row[f"{key}_actual"])) for key in services]
    return any(actual < target for target, actual in pairs if None not in (target, actual))


def official_check(rows: list[dict], statements: list[dict]) -> list[dict]:
    result = []
    for record in statements:
        year, service = int(record["year"]), record["service"]
        group = members(operators_of(rows, year), record["group"])
        computed = sum(below(row, service) for row in group)
        status = "match" if (len(group), computed) == (int(record["operators"]), int(record["below_target"])) else "differ"
        result.append({"year": year, "group": record["group"], "service": service,
                       "official_operators": int(record["operators"]), "computed_operators": len(group),
                       "official_below": int(record["below_target"]), "computed_below": computed, "status": status})
    return result


def any_below(rows: list[dict], years: list[int]) -> dict:
    result = {}
    for year in years:
        operators = operators_of(rows, year)
        variants = [row for row in rows if int(row["year"]) == year and row["row_kind"] == "variant"]
        result[str(year)] = {"operators": len(operators), "below_any": sum(below(row, "any") for row in operators),
                             "variant_rows_below_any": sum(below(row, "any") for row in variants)}
    return result


def main() -> None:
    rows = read_csv(INPUTS[0])
    years = sorted({int(row["year"]) for row in rows})
    bases = {row["year"]: row["target_basis"] for row in rows}
    OUT.mkdir(exist_ok=True)
    checked = official_check(rows, read_csv(INPUTS[1]))
    write_csv("broadcast_early_compliance_by_year.csv", compliance(rows, years))
    write_csv("broadcast_early_group_summary.csv", group_summary(rows, years))
    write_csv("broadcast_early_official_check.csv", checked)
    summary = {
        "inputs": {name: hashlib.sha256((DATA / name).read_bytes()).hexdigest() for name in INPUTS},
        "years": years, "target_basis": bases,
        "below_any_service": any_below(rows, years),
        "official_check": {status: sum(row["status"] == status for row in checked) for status in ("match", "differ")},
        "official_differ": [row for row in checked if row["status"] == "differ"],
        "limits": [
            "2012~2016년 목표는 방송사업자별로 해마다 단계적으로 높인 값이다(2012년은 방송사가 제시하고 방송통신위원회가 승인). "
            "2017년 이후의 사업자군별 의무 비율과 기준이 달라 미달 수를 2017년 이후와 한 줄로 잇지 않는다.",
            "편성 비율의 산정 기준(인정 방송시간 등)이 2017년 이후와 같은지 확인하지 못했다. 실적 평균도 2017년 이후와 바로 잇지 않는다.",
            "미달은 실적이 목표보다 작은 경우를 센 것이다. 공식 평가의 소명·경감 결과는 반영하지 않았다.",
            "보조 행(같은 번호 아래 두 번째 편성 단위, 해마다 MBC경남 한 줄)은 사업자 수와 미달 수에서 뺐다.",
        ],
    }
    (OUT / "broadcast_early_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for year, counts in summary["below_any_service"].items():
        print(f"{year}: 사업자 {counts['operators']}곳 중 한 가지 이상 미달 {counts['below_any']}곳")
    print(f"공식 집계 대조 {len(checked)}건: 일치 {summary['official_check']['match']}, 다름 {summary['official_check']['differ']}")


if __name__ == "__main__":
    main()
