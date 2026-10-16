"""Turn the 2012-2016 KMCC HWP tables into one CSV row per broadcaster-year."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from hwp5_table import read_tables
from hwpx_table import Table
from kcmf_parse import VALUE_FIELDS, ParseError, number, write_csv


HERE = Path(__file__).resolve().parent
SERVICES = (("자막", "cc"), ("화면해설", "ad"), ("수화", "ksl"), ("수어", "ksl"))
# 2013·2014년 표는 '보도'·'종편'으로 적는다. 2015년부터는 2017년 이후 재단 자료처럼 'PP'를 붙인다.
GROUPS = {"지상파": "지상파", "위성": "위성", "보도": "보도PP", "보도PP": "보도PP",
          "종편": "종편PP", "종편PP": "종편PP", "SO": "SO", "PP": "PP"}
# 2012년 표에는 사업자군 칸이 없다. 보도자료 본문의 '지상파방송사(50개사)'로 대조한다.
UNLABELED = {2012: ("지상파", 50)}
# 2012년 붙임: "각 방송사가 '12년도 달성가능 목표를 제시하여 방통위가 승인".
# 2015·2016년 보도자료: "방송사업자별 장애인방송 편성비율 목표치를 ’12년부터 ’16년까지 단계적으로 높여왔으며".
TARGET_BASIS = {2012: "broadcaster_proposed", 2013: "phased_by_operator", 2014: "phased_by_operator",
                2015: "phased_by_operator", 2016: "phased_by_operator"}
FIELDS = ["year", "unit_order", "row_no", "row_kind", "group", "group_label", "operator", *VALUE_FIELDS,
          "target_basis", "file_seq", "source_table", "source_row"]


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def group_of(label: str) -> tuple[str, int | None]:
    match = re.fullmatch(r"(.+?)\((\d+)\)", label)
    name, count = (match.group(1), int(match.group(2))) if match else (label, None)
    if name not in GROUPS:
        raise ParseError(f"알 수 없는 사업자군: {label!r}")
    return GROUPS[name], count


def layout(table: Table) -> dict | None:
    """Find the name, number, group and target/actual columns, or None for a table without them."""
    top = [cell for cell in table.cells if cell.row == 0]
    division = [cell for cell in top if compact(cell.text) == "구분"]
    names = [cell for cell in top if "사업자" in cell.text and "명" in cell.text]
    if len(division) != 1 or len(names) != 1:
        return None
    start = division[0].row + division[0].row_span
    head = [cell for cell in table.cells if cell.row < start]
    services = [(cell.col, cell.col + cell.col_span, key) for cell in head for word, key in SERVICES if word in cell.text]
    fields = {}
    for cell in head:
        word = re.sub(r"\(.*\)", "", compact(cell.text))  # '목표(A)'·'목표치' → 목표
        if word not in ("목표", "목표치", "실적", "실적치"):
            continue
        keys = {key for left, right, key in services if left <= cell.col < right}
        field = f"{keys.pop()}_{'target' if word.startswith('목표') else 'actual'}" if len(keys) == 1 else None
        if field is None or field in fields:
            raise ParseError(f"표 {table.index}: 목표·실적 열의 서비스가 모호하다")
        fields[field] = cell.col
    if not fields:
        return None
    if sorted(fields) != sorted(VALUE_FIELDS):
        raise ParseError(f"표 {table.index}: 목표·실적 열이 6개가 아니다")
    numbers = [cell for cell in top if compact(cell.text) == "번호"]
    if numbers:  # 2013·2014년: 구분 | 번호 | 방송사업자명
        group_col, number_col = division[0].col, numbers[0].col
    elif division[0].col_span == 2:  # 2015·2016년: 구분(사업자군·번호) | 방송사업자명
        group_col, number_col = division[0].col, division[0].col + 1
    else:  # 2012년: 구분(번호) | 사업자명
        group_col, number_col = None, division[0].col
    return {"start": start, "name_col": names[0].col, "number_col": number_col, "group_col": group_col, "fields": fields}


def operator_rows(year: int, file_seq: int, table: Table, shape: dict) -> tuple[list[dict], dict[str, int]]:
    rows, labels, previous = [], {}, None
    for r in range(shape["start"], table.rows):
        name = table.start(r, shape["name_col"])
        if name is None or not name.text:
            continue
        number_cell = table.covering(r, shape["number_col"])
        if number_cell is None or not number_cell.text.isdigit():
            raise ParseError(f"{year} {name.text}: 일련번호 칸이 없다")
        if shape["group_col"] is None:
            group, count = UNLABELED[year]
            label = ""
        else:
            group_cell = table.covering(r, shape["group_col"])
            if group_cell is None or not group_cell.text:
                raise ParseError(f"{year} {name.text}: 사업자군 칸이 비어 있다")
            label = compact(group_cell.text)
            group, count = group_of(label)
        if count is not None and labels.setdefault(group, count) != count:
            raise ParseError(f"{year} {group}: 사업자 수 표기가 둘이다")
        # 앞 사업자 행과 같은 번호 칸을 쓰면 보조 행이다. 2013년 SO 표는 번호 칸과 사업자명 칸의
        # 병합이 한 줄 어긋나 있어, 번호 칸이 시작하는 행으로는 판정하지 않는다.
        kind = "variant" if (number_cell.row, number_cell.col) == previous else "operator"
        previous = (number_cell.row, number_cell.col)
        row = {
            "year": year, "unit_order": 0, "row_no": number_cell.text, "row_kind": kind, "group": group,
            "group_label": label, "operator": name.text, "target_basis": TARGET_BASIS[year],
            "file_seq": file_seq, "source_table": table.index, "source_row": r,
        }
        for field, col in shape["fields"].items():
            cell = table.start(r, col)
            row[field] = number(cell.text if cell else "", what=f"{year} {name.text} {field}")
        rows.append(row)
    return rows, labels


def validate(year: int, rows: list[dict], labels: dict[str, int]) -> None:
    operators = [row for row in rows if row["row_kind"] == "operator"]
    if not operators:
        raise ParseError(f"{year}: 사업자 행이 없다")
    # 2013년은 필수지정·고시의무 표가 따로 있고 표마다 1번부터 센다.
    for table in sorted({row["source_table"] for row in operators}):
        numbers = [row["row_no"] for row in operators if row["source_table"] == table]
        if numbers != [str(i) for i in range(1, len(numbers) + 1)]:
            raise ParseError(f"{year} 표 {table}: 일련번호가 1부터 빠짐없이 이어지지 않는다")
    keys = [(row["source_table"], row["row_kind"], row["row_no"], row["operator"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise ParseError(f"{year}: 같은 사업자 행이 중복됐다")
    counted = {}
    for row in operators:
        counted[row["group"]] = counted.get(row["group"], 0) + 1
    if counted != labels:
        raise ParseError(f"{year}: 사업자군별 행 수 {counted}가 표기된 수 {labels}와 다르다")
    for row in operators:
        if any(row[field] in ("", "NA") for field in VALUE_FIELDS):
            raise ParseError(f"{year} {row['operator']}: 비어 있는 목표·실적이 있다")


def main() -> None:
    manifest = json.loads((HERE / "data" / "kmcc_manifest.json").read_text(encoding="utf-8"))
    rows, notes = [], []
    for entry in manifest["files"]:
        if entry["role"] == "body":
            continue
        path = HERE / entry["raw_path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ParseError(f"{path.name}: 수집 명세의 SHA256과 다르다")
        year, found, labels, used = entry["year"], [], {}, []
        for table in read_tables(path):
            shape = layout(table)
            if shape is None:
                continue
            table_rows, table_labels = operator_rows(year, entry["file_seq"], table, shape)
            for group, count in table_labels.items():
                if labels.setdefault(group, count) != count:
                    raise ParseError(f"{year} {group}: 표마다 사업자 수가 다르다")
            found += table_rows
            used.append(table.index)
        validate(year, found, labels)
        for order, row in enumerate(found, start=1):
            row["unit_order"] = order
        rows += found
        notes.append({
            "year": year, "file_seq": entry["file_seq"], "sha256": entry["sha256"], "tables": used,
            "operator_rows": sum(row["row_kind"] == "operator" for row in found),
            "variant_rows": [row["operator"] for row in found if row["row_kind"] == "variant"],
            "group_counts_in_source": labels, "target_basis": TARGET_BASIS[year],
        })
    data = HERE / "data"
    write_csv(data / "broadcast_operator_years_2012_2016.csv", FIELDS, rows)
    (data / "broadcast_parse_notes_2012_2016.json").write_text(
        json.dumps({"source_manifest": "data/kmcc_manifest.json", "years": notes}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(f"사업자 행 {len(rows)}개: " + ", ".join(f"{note['year']} {note['operator_rows']}" for note in notes))


if __name__ == "__main__":
    main()
