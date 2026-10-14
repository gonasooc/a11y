"""Summarize disability-broadcast quotas by year and reconcile them with official tables."""

from __future__ import annotations

import csv
import hashlib
import json
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from pathlib import Path


HERE = Path(__file__).resolve().parent
DATA, OUT = HERE / "data", HERE / "outputs"
SERVICES = ("cc", "ad", "ksl")
# 공식 표의 '지상파(4개사)'는 지상파 일련번호 1~4다. 이름으로 한 번 더 확인한다.
CENTRAL = ("한국방송공사", "문화방송", "에스비에스", "교육방송")
OFFICIAL_GROUPS = {
    "지상파(4개사)": "central", "지역지상파(44개사)": "regional", "위성(1개사)": "위성",
    "보도PP(2개사)": "보도PP", "종편PP(4개사)": "종편PP", "SO(43개사)": "SO", "일반PP(10개사)": "PP",
}
# 장애인방송 고시 제6조⑥: 화면해설 의무 편성비율 중 같은 프로그램의 재방송은 25% 이하.
RERUN_LIMIT = Decimal(25)
TWO, ONE = Decimal("0.01"), Decimal("0.1")


class AnalysisError(ValueError):
    pass


def read_csv(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(name: str, rows: list[dict]) -> None:
    with (OUT / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def numeric(value: str) -> Decimal | None:
    return None if value in ("", "NA") else Decimal(value)


def plain(value: Decimal) -> str:
    return format(value.normalize(), "f")


def share(part: int, whole: int) -> str:
    return str((Decimal(part) * 100 / whole).quantize(ONE, ROUND_HALF_UP)) if whole else ""


def operators_of(rows: list[dict], year: int) -> list[dict]:
    return [row for row in rows if int(row["year"]) == year and row["row_kind"] == "operator"]


def compliance(rows: list[dict], years: list[int]) -> list[dict]:
    result = []
    for year in years:
        operators = operators_of(rows, year)
        variants = [row for row in rows if int(row["year"]) == year and row["row_kind"] == "variant"]
        for service in SERVICES:
            pairs = [(numeric(row[f"{service}_target"]), numeric(row[f"{service}_actual"])) for row in operators]
            compared = [(target, actual) for target, actual in pairs if target is not None and actual is not None]
            gaps = [target - actual for target, actual in compared if actual < target]
            variant_below = sum(
                1 for row in variants
                if None not in (numeric(row[f"{service}_target"]), numeric(row[f"{service}_actual"]))
                and numeric(row[f"{service}_actual"]) < numeric(row[f"{service}_target"]))
            result.append({
                "year": year, "service": service, "operators": len(operators), "compared": len(compared),
                "below_target": len(gaps), "below_share_pct": share(len(gaps), len(compared)),
                "shortfall_under_0_1pctp": sum(gap < ONE for gap in gaps),
                "shortfall_1pctp_or_more": sum(gap >= 1 for gap in gaps),
                "largest_shortfall_pctp": str(max(gaps)) if gaps else "",
                "below_target_100": sum(1 for target, actual in compared if target == 100 and actual < target),
                "variant_rows_below": variant_below,
            })
    return result


def group_summary(rows: list[dict], years: list[int]) -> list[dict]:
    result = []
    for year in years:
        operators = operators_of(rows, year)
        for group in dict.fromkeys(row["group"] for row in operators):
            members = [row for row in operators if row["group"] == group]
            record = {"year": year, "group": group or "표기 없음", "operators": len(members)}
            for service in SERVICES:
                targets = sorted({numeric(row[f"{service}_target"]) for row in members} - {None}, reverse=True)
                actuals = [numeric(row[f"{service}_actual"]) for row in members]
                actuals = [value for value in actuals if value is not None]
                record[f"{service}_targets"] = "/".join(plain(value) for value in targets)
                record[f"{service}_actual_mean"] = (
                    str((sum(actuals) / len(actuals)).quantize(TWO, ROUND_HALF_UP)) if actuals else "")
            result.append(record)
    return result


def official_members(operators: list[dict], key: str) -> list[dict]:
    terrestrial = [row for row in operators if row["group"] == "지상파"]
    if key == "central":
        members = [row for row in terrestrial if int(row["row_no"]) <= 4]
        if len(members) != 4 or any(token not in row["operator"] for token, row in zip(CENTRAL, members)):
            raise AnalysisError("지상파 일련번호 1~4가 중앙 지상파 4사가 아니다")
        return members
    if key == "regional":
        return [row for row in terrestrial if int(row["row_no"]) > 4]
    return [row for row in operators if row["group"] == key]


def official_check(rows: list[dict], official: list[dict]) -> list[dict]:
    result = []
    for record in official:
        year, service = int(record["year"]), record["service"]
        members = official_members(operators_of(rows, year), OFFICIAL_GROUPS[record["official_group"]])
        if len(members) != int(record["operators"]):
            raise AnalysisError(f"{year} {record['official_group']}: 사업자 수가 공식 표와 다르다")
        # 공식 표의 목표는 사업자군 기본값이다. 경감·유예로 개별 목표가 다른 사업자가 있어 기록만 한다.
        targets = sorted({Decimal(row[f"{service}_target"]) for row in members}, reverse=True)
        values = [Decimal(row[f"{service}_actual"]) for row in members]
        mean = sum(values) / len(values)
        expected = Decimal(record["actual"])
        truncated, rounded = mean.quantize(TWO, ROUND_DOWN), mean.quantize(TWO, ROUND_HALF_UP)
        status = "match_truncated" if truncated == expected else "match_rounded" if rounded == expected else "differ"
        result.append({
            "year": year, "official_group": record["official_group"], "service": service,
            "operators": len(members), "official_target": record["target"],
            "member_targets": "/".join(plain(value) for value in targets),
            "official_actual": record["actual"], "computed_mean": str(mean),
            "computed_truncated": str(truncated), "computed_rounded": str(rounded), "status": status,
        })
    return result


def statement_check(rows: list[dict], statements: list[dict]) -> list[dict]:
    result = []
    for record in statements:
        year, service = int(record["year"]), record["service"]
        operators = operators_of(rows, year)
        pairs = [(numeric(row[f"{service}_target"]), numeric(row[f"{service}_actual"])) for row in operators]
        if record["scope"] == "target_100":
            pairs = [(target, actual) for target, actual in pairs if target == 100]
        below = sum(1 for target, actual in pairs if None not in (target, actual) and actual < target)
        if len(operators) != int(record["operators"]):
            raise AnalysisError(f"{year}: 사업자 수가 공식 발표와 다르다")
        result.append({"year": year, "service": service, "scope": record["scope"],
                       "official_below": int(record["below_target"]), "computed_below": below,
                       "status": "match" if below == int(record["below_target"]) else "differ"})
    return result


def rerun_summary(reruns: list[dict]) -> dict:
    result = {}
    for year in sorted({int(row["year"]) for row in reruns}):
        rows = [row for row in reruns if int(row["year"]) == year]
        for row in rows:
            if row["rerun_limit_pct"] and Decimal(row["rerun_limit_pct"]) != RERUN_LIMIT:
                raise AnalysisError(f"{year} {row['operator']}: 재방송 상한이 25%가 아니다")
        shares = [Decimal(row["rerun_share_pct"]) for row in rows]
        result[str(year)] = {
            "operators": len(rows), "max_share_pct": str(max(shares)),
            "over_limit": sum(value > RERUN_LIMIT for value in shares),
            "at_least_20_pct": sum(value >= 20 for value in shares),
            "zero_rerun": sum(value == 0 for value in shares),
        }
    return result


def main() -> None:
    inputs = ["broadcast_operator_years.csv", "broadcast_ad_rerun.csv", "kmcc_group_means.csv",
              "kmcc_compliance_statements.csv", "broadcast_parse_notes.json", "kcmf_manifest.json"]
    rows = read_csv(inputs[0])
    years = sorted({int(row["year"]) for row in rows})
    OUT.mkdir(exist_ok=True)

    by_year = compliance(rows, years)
    groups = group_summary(rows, years)
    # 공식 발표와 다른 값은 오류로 멈추지 않고 양쪽 값을 남긴다(출처 간 차이는 결과로 기록).
    checked = official_check(rows, read_csv(inputs[2]))
    statements = statement_check(rows, read_csv(inputs[3]))
    checked_years = sorted({row["year"] for row in checked})

    write_csv("broadcast_compliance_by_year.csv", by_year)
    write_csv("broadcast_group_summary.csv", groups)
    write_csv("broadcast_official_check.csv", checked)
    summary = {
        "inputs": {name: hashlib.sha256((DATA / name).read_bytes()).hexdigest() for name in inputs},
        "years": years,
        "compliance": {str(row["year"]): {} for row in by_year},
        "official_group_means": {
            str(year): {
                "checked": sum(row["year"] == year for row in checked),
                **{status: sum(row["year"] == year and row["status"] == status for row in checked)
                   for status in ("match_truncated", "match_rounded", "differ")},
            } for year in checked_years
        },
        "official_statements": statements,
        "ad_rerun": rerun_summary(read_csv(inputs[1])),
        "limits": [
            "편성 비율은 방송시간 대비 비율이다. 시간대, 프로그램 종류, 자막·해설·수어의 품질은 드러나지 않는다.",
            "미달 사업자 수는 실적이 목표보다 작은 경우를 센 것이다. 공식 평가의 경감·유예·소명 결과는 반영하지 않았다.",
            "2018년 파일에는 사업자군 열이 없어 사업자군별 요약에서 '표기 없음'으로 둔다.",
            "보조 행(같은 일련번호의 다른 편성 단위·스마트수어 포함 실적)은 사업자 수와 미달 수에서 뺐다.",
        ],
    }
    for row in by_year:
        summary["compliance"][str(row["year"])][row["service"]] = {
            key: row[key] for key in ("operators", "compared", "below_target", "below_target_100",
                                      "shortfall_under_0_1pctp", "shortfall_1pctp_or_more", "largest_shortfall_pctp")}
    (OUT / "broadcast_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for year, counts in summary["official_group_means"].items():
        print(f"{year} 공식 사업자군 평균 {counts['checked']}개: 버림 일치 {counts['match_truncated']}, "
              f"반올림 일치 {counts['match_rounded']}, 다름 {counts['differ']}")
    print(f"공식 미달 사업자 수 발표 {len(statements)}건: 일치 {sum(row['status'] == 'match' for row in statements)}")


if __name__ == "__main__":
    main()
