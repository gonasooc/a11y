"""Summarize registered hearing and visual disability by year from a saved KOSIS snapshot."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path


HERE = Path(__file__).resolve().parent
DATA, OUT = HERE / "data", HERE / "outputs"
AGE_TABLE, TYPE_TABLE = "DT_11761_N003", "DT_11761_N001"
AGE_TOTAL, AGE_UNKNOWN = "000", "500"
# 65-69세부터 120-124세까지. '해당없음'(500)은 65세 이상에도 미만에도 넣지 않는다.
OLDER = ("280", "310", "330", "360", "380", "410", "430", "450", "460", "470", "480", "490")
YOUNGER = ("020", "050", "070", "100", "120", "130", "150", "160", "180", "190", "210", "230", "260")
CONTEXT_FACTS = "context_facts_2026-10-13.csv"
ONE = Decimal("0.1")


class AnalysisError(ValueError):
    pass


def share(part: int, whole: int) -> str:
    return str((Decimal(part) * 100 / whole).quantize(ONE, ROUND_HALF_UP)) if whole else ""


def by_year(rows: list[dict]) -> list[dict]:
    ages, totals = {}, {}
    for row in rows:
        if row["table_id"] == AGE_TABLE:
            ages.setdefault((row["year"], row["type"]), {})[row["age_code"]] = row["value"]
        elif row["table_id"] == TYPE_TABLE:
            totals[(row["year"], row["type"])] = row["value"]
        else:
            raise AnalysisError(f"모르는 표: {row['table_id']}")
    result = []
    for year, kind in sorted(ages, key=lambda key: (key[0], ("all", "hearing", "visual").index(key[1]))):
        cells = ages[(year, kind)]
        registered = int(cells[AGE_TOTAL])
        older = sum(int(cells[code]) for code in OLDER if cells.get(code))
        younger = sum(int(cells[code]) for code in YOUNGER if cells.get(code))
        unknown = int(cells.get(AGE_UNKNOWN) or 0)
        unallocated = registered - sum(int(value) for code, value in cells.items() if code != AGE_TOTAL and value)
        if unallocated < 0:
            raise AnalysisError(f"{year} {kind}: 연령 구간 합이 합계보다 크다")
        if set(cells) - {AGE_TOTAL, AGE_UNKNOWN, *OLDER, *YOUNGER} or older + younger + unknown + unallocated != registered:
            raise AnalysisError(f"{year} {kind}: 연령 구간을 65세 기준으로 나누지 못했다")
        all_registered = int(ages[(year, "all")][AGE_TOTAL])
        other = totals.get((year, kind), "")
        result.append({
            "year": year, "type": kind, "registered": registered, "age65_plus": older,
            "age65_plus_share_pct": share(older, registered), "age_under65": younger, "age_unknown": unknown,
            "unallocated": unallocated,
            # 공표되지 않은 차이를 모두 65세 이상으로 볼 때의 비율. 차이가 없으면 위 비율과 같다.
            "age65_plus_share_upper_pct": share(older + unallocated, registered),
            "share_of_all_pct": "" if kind == "all" else share(registered, all_registered),
            "n001_registered": other,
            "n001_status": "unavailable" if other == "" else "match" if int(other) == registered else "differ",
        })
    return result


def context_check(series: list[dict], facts: list[dict]) -> list[dict]:
    computed = {(row["year"], row["type"]): row for row in series}
    columns = {"registered_by_type": "registered", "registered_65plus_share": "age65_plus_share_pct"}
    result = []
    for fact in facts:
        row = computed.get((fact["survey_year"], fact["population"]))
        if fact["indicator"] not in columns or row is None:
            continue
        value = str(row[columns[fact["indicator"]]])
        result.append({"year": fact["survey_year"], "indicator": fact["indicator"], "population": fact["population"],
                       "document": fact["value"], "computed": value,
                       "status": "match" if Decimal(value) == Decimal(fact["value"]) else "differ"})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, help="수집일(YYYY-MM-DD). 조사연도가 아니다")
    args = parser.parse_args()
    names = [f"kosis_registry_{args.snapshot}.csv", f"kosis_registry_manifest_{args.snapshot}.json", CONTEXT_FACTS]
    manifest = json.loads((DATA / names[1]).read_text(encoding="utf-8"))
    if hashlib.sha256((DATA / names[0]).read_bytes()).hexdigest() != manifest["csv_sha256"]:
        raise AnalysisError("수집 CSV가 명세의 SHA256과 다르다")
    with (DATA / names[0]).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with (DATA / names[2]).open(encoding="utf-8", newline="") as handle:
        facts = list(csv.DictReader(handle))
    series = by_year(rows)
    # 수집 명세에 남긴 미공표 차이와 다시 계산한 차이가 같아야 한다.
    recorded = manifest["tables"][AGE_TABLE]["unallocated_by_year"]
    if {(row["year"], row["type"]): row["unallocated"] for row in series if row["unallocated"]} != {
            (year, kind): gap for year, gaps in recorded.items() for kind, gap in gaps.items()}:
        raise AnalysisError("미공표 연령 차이가 수집 명세와 다르다")

    OUT.mkdir(exist_ok=True)
    with (OUT / "registry_by_year.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(series[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(series)
    checked = context_check(series, facts)
    years = sorted({row["year"] for row in series})
    summary = {
        "inputs": {name: hashlib.sha256((DATA / name).read_bytes()).hexdigest() for name in names},
        "snapshot": args.snapshot, "years": [years[0], years[-1]],
        "series": {},
        "checks": {
            "n001": {status: sum(row["n001_status"] == status for row in series) for status in ("match", "differ", "unavailable")},
            "n001_differ": [{key: row[key] for key in ("year", "type", "registered", "n001_registered")}
                            for row in series if row["n001_status"] == "differ"],
            "unallocated_years": sorted({row["year"] for row in series if row["unallocated"]}),
            "upper_share_differs": [{key: row[key] for key in ("year", "type", "age65_plus_share_pct", "age65_plus_share_upper_pct")}
                                    for row in series if row["age65_plus_share_pct"] != row["age65_plus_share_upper_pct"]],
            "context_facts": checked,
        },
        "limits": [
            "연도 말 등록 인원이다. 등록하지 않은 난청·저시력 인구는 빠진다.",
            "2007~2014년은 100세 이상 구간과 '해당없음'이 공표되지 않아 연령 구간 합이 합계보다 작다. 65세 이상은 공표된 구간만 더했고, 차이를 모두 65세 이상으로 볼 때의 비율을 upper 열에 따로 둔다.",
            "등록 인원의 변화에는 장애 발생뿐 아니라 판정 기준·등록 유인의 변화가 함께 들어 있다. 이 자료로 원인을 나누지 않는다.",
            "65세 이상 비율의 상승에는 인구 전체의 고령화가 함께 들어 있다.",
        ],
    }
    for kind in ("all", "hearing", "visual"):
        rows_of_kind = [row for row in series if row["type"] == kind]
        peak = max(rows_of_kind, key=lambda row: row["registered"])
        summary["series"][kind] = {"first": rows_of_kind[0], "last": rows_of_kind[-1],
                                   "peak": {"year": peak["year"], "registered": peak["registered"]}}
    (OUT / "registry_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for kind in ("hearing", "visual"):
        first, last = summary["series"][kind]["first"], summary["series"][kind]["last"]
        print(f"{kind}: {first['year']} {first['registered']:,}명(65세 이상 {first['age65_plus_share_pct']}%) → "
              f"{last['year']} {last['registered']:,}명(65세 이상 {last['age65_plus_share_pct']}%)")
    counts = summary["checks"]["n001"]
    print(f"N001 대조 {len(series)}칸: 일치 {counts['match']}, 다름 {counts['differ']}, 대조 불가 {counts['unavailable']}")
    print(f"문서 값 대조 {len(checked)}건: 일치 {sum(row['status'] == 'match' for row in checked)}")


if __name__ == "__main__":
    main()
