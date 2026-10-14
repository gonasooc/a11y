"""Turn the KCMF HWPX tables into one CSV row per broadcaster-year, plus AD rerun rows."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from hwpx_table import Table, read_tables


HERE = Path(__file__).resolve().parent
SERVICES = (("폐쇄자막", "cc"), ("화면해설", "ad"), ("한국수어", "ksl"), ("수화", "ksl"))
GROUPS = {"지상파", "위성", "보도PP", "종편PP", "SO", "PP"}
VALUE_FIELDS = ["cc_target", "cc_actual", "ad_target", "ad_actual", "ksl_target", "ksl_actual"]
OPERATOR_FIELDS = ["year", "unit_order", "row_no", "row_kind", "group", "group_label", "operator",
                   *VALUE_FIELDS, "source_table", "source_row"]
RERUN_FIELDS = ["year", "operator", "rerun_limit_pct", "rerun_share_pct", "required_minutes",
                "first_run_minutes", "rerun_minutes", "source_table", "source_row"]
# 재방송 표의 머리글 문구와 열 이름. 2023·2024는 비율, 2025는 분 단위 시간과 비율을 싣는다.
RERUN_HEADERS = (("목표*", "rerun_limit_pct"), ("실적**", "rerun_share_pct"),
                 ("목표편성", "required_minutes"), ("본방송", "first_run_minutes"),
                 ("재방송(C)", "rerun_minutes"), ("편성비율", "rerun_share_pct"))
HUNDRED = Decimal(100)


class ParseError(ValueError):
    pass


def number(text: str, *, what: str, upper: Decimal | None = HUNDRED) -> str:
    """Return '' for an empty cell, 'NA' for '-', otherwise the validated source digits."""
    raw = text.replace("%", "").replace(",", "").strip()
    if raw == "":
        return ""
    if raw == "-":
        return "NA"
    try:
        value = Decimal(raw)
    except InvalidOperation:
        raise ParseError(f"{what}: 숫자가 아니다: {text!r}") from None
    if value < 0 or (upper is not None and value > upper):
        raise ParseError(f"{what}: 범위를 벗어났다: {text!r}")
    return raw


def group_of(label: str) -> tuple[str, int | None]:
    compact = re.sub(r"\s+", "", label)
    match = re.fullmatch(r"(.+?)\((\d+)\)", compact)
    name, count = (match.group(1), int(match.group(2))) if match else (compact, None)
    name = name.upper() if name.lower() in ("pp", "so") else name
    if name not in GROUPS:
        raise ParseError(f"알 수 없는 사업자군: {label!r}")
    return name, count


def is_main(table: Table) -> bool:
    texts = [cell.text for cell in table.cells if cell.row <= 2]
    return any("폐쇄자막" in t for t in texts) and "목표" in texts and "실적" in texts


def is_rerun(table: Table) -> bool:
    return any("재방송" in cell.text for cell in table.cells if cell.row <= 1)


def main_columns(table: Table) -> tuple[int, bool, int, dict[str, int]]:
    name = [c for c in table.cells if c.row == 0 and "방송사업자" in c.text]
    first = [c for c in table.cells if c.row == 0 and c.text == "구분"]
    if len(name) != 1 or len(first) != 1:
        raise ParseError(f"표 {table.index}: 머리글(구분·방송사업자)을 찾지 못했다")
    has_group = first[0].col_span == 2
    services = [(c.col, c.col + c.col_span, key) for c in table.cells if c.row == 1
                for word, key in SERVICES if word in c.text]
    columns = {}
    for cell in table.cells:
        if cell.row == 2 and cell.text in ("목표", "실적"):
            keys = [key for start, end, key in services if start <= cell.col < end]
            field = f"{keys[0]}_{'target' if cell.text == '목표' else 'actual'}" if len(keys) == 1 else None
            if field is None or field in columns:
                raise ParseError(f"표 {table.index}: 목표·실적 열의 서비스가 모호하다")
            columns[field] = cell.col
    if sorted(columns) != sorted(VALUE_FIELDS):
        raise ParseError(f"표 {table.index}: 목표·실적 열이 6개가 아니다")
    return name[0].col, has_group, 1 if has_group else 0, columns


def operator_rows(year: int, tables: list[Table]) -> tuple[list[dict], dict[str, int]]:
    rows, labels, group, group_label = [], {}, "", ""
    for table in filter(is_main, tables):
        name_col, has_group, number_col, columns = main_columns(table)
        for r in range(3, table.rows):
            name = table.start(r, name_col)
            if name is None or not name.text:
                continue
            number_cell = table.covering(r, number_col)
            if number_cell is None:
                raise ParseError(f"{year} {name.text}: 일련번호 칸이 없다")
            if has_group:
                group_cell = table.covering(r, 0)
                if group_cell is not None and group_cell.text:
                    group_label = re.sub(r"\s+", "", group_cell.text)
                    group, count = group_of(group_cell.text)
                    if count is not None and labels.setdefault(group, count) != count:
                        raise ParseError(f"{year} {group}: 표마다 사업자 수가 다르다")
                elif not group:
                    raise ParseError(f"{year} {name.text}: 사업자군 없이 표가 시작한다")
            kind = "operator" if number_cell.row == r else "variant"
            row = {
                "year": year, "unit_order": len(rows) + 1, "row_no": number_cell.text,
                "row_kind": kind, "group": group, "group_label": group_label, "operator": name.text,
                "source_table": table.index, "source_row": r,
            }
            for field, col in columns.items():
                cell = table.start(r, col)
                row[field] = number(cell.text if cell else "", what=f"{year} {name.text} {field}")
            rows.append(row)
    return rows, labels


def validate_operators(year: int, rows: list[dict], labels: dict[str, int]) -> None:
    operators = [row for row in rows if row["row_kind"] == "operator"]
    if not operators:
        raise ParseError(f"{year}: 사업자 행이 없다")
    if [row["row_no"] for row in operators] != [str(i) for i in range(1, len(operators) + 1)]:
        raise ParseError(f"{year}: 일련번호가 1부터 빠짐없이 이어지지 않는다")
    keys = [(row["row_kind"], row["row_no"], row["operator"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise ParseError(f"{year}: 같은 사업자 행이 중복됐다")
    if labels:
        counted = {}
        for row in operators:
            counted[row["group"]] = counted.get(row["group"], 0) + 1
        if counted != labels:
            raise ParseError(f"{year}: 사업자군별 행 수 {counted}가 표기된 수 {labels}와 다르다")
    for row in operators:
        if any(row[field] == "" for field in VALUE_FIELDS):
            raise ParseError(f"{year} {row['operator']}: 비어 있는 목표·실적이 있다")


def rerun_rows(year: int, tables: list[Table]) -> list[dict]:
    rows = []
    for table in filter(is_rerun, tables):
        if is_main(table):
            continue
        header = [c for c in table.cells if c.row <= 2 and (
            any(word in c.text for word, _ in RERUN_HEADERS) or "방송사" in c.text)]
        names = [c for c in header if "방송사" in c.text]
        columns = {}
        for cell in header:
            for word, field in RERUN_HEADERS:
                if word in cell.text:
                    if field in columns:
                        raise ParseError(f"{year} 재방송 표: {field} 열이 둘이다")
                    columns[field] = cell.col
        if len(names) != 1 or "rerun_share_pct" not in columns:
            raise ParseError(f"{year} 재방송 표: 머리글을 해석하지 못했다")
        start = max(cell.row + cell.row_span for cell in header)
        for r in range(start, table.rows):
            name = table.start(r, names[0].col)
            if name is None or not name.text:
                continue
            row = {field: "" for field in RERUN_FIELDS}
            row.update(year=year, operator=name.text, source_table=table.index, source_row=r)
            for field, col in columns.items():
                cell = table.start(r, col)
                upper = HUNDRED if field.endswith("_pct") else None
                row[field] = number(cell.text if cell else "", what=f"{year} {name.text} {field}", upper=upper)
            check_minutes(row)
            rows.append(row)
    return rows


def check_minutes(row: dict) -> None:
    """2025년 표는 A=B+C와 C/A 비율을 함께 싣는다. 전사 오류를 막으려고 서로 대조한다."""
    if not row["required_minutes"]:
        return
    total, first = Decimal(row["required_minutes"]), Decimal(row["first_run_minutes"])
    rerun = Decimal(0) if row["rerun_minutes"] == "NA" else Decimal(row["rerun_minutes"])
    if total != first + rerun:
        raise ParseError(f"{row['year']} {row['operator']}: 본방송+재방송이 의무편성 시간과 다르다")
    share = (rerun * HUNDRED / total).quantize(Decimal("0.01"))
    if abs(share - Decimal(row["rerun_share_pct"])) > Decimal("0.01"):
        raise ParseError(f"{row['year']} {row['operator']}: 재방송 비율이 시간과 맞지 않는다")


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    manifest = json.loads((HERE / "data" / "kcmf_manifest.json").read_text(encoding="utf-8"))
    operators, reruns, notes = [], [], []
    for entry in manifest["files"]:
        path = HERE / entry["raw_path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ParseError(f"{path.name}: 수집 명세의 SHA256과 다르다")
        tables = read_tables(path)
        rows, labels = operator_rows(entry["year"], tables)
        validate_operators(entry["year"], rows, labels)
        extra = rerun_rows(entry["year"], tables)
        operators += rows
        reruns += extra
        notes.append({
            "year": entry["year"], "sha256": entry["sha256"],
            "operator_rows": sum(row["row_kind"] == "operator" for row in rows),
            "variant_rows": sum(row["row_kind"] == "variant" for row in rows),
            "group_counts_in_source": labels or None, "rerun_rows": len(extra),
        })
    data = HERE / "data"
    write_csv(data / "broadcast_operator_years.csv", OPERATOR_FIELDS, operators)
    write_csv(data / "broadcast_ad_rerun.csv", RERUN_FIELDS, reruns)
    (data / "broadcast_parse_notes.json").write_text(
        json.dumps({"source_manifest": "data/kcmf_manifest.json", "years": notes}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(f"사업자 행 {len(operators)}개, 재방송 행 {len(reruns)}개")


if __name__ == "__main__":
    main()
