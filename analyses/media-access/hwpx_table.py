"""Read table cells from HWPX (OWPML) documents with the standard library."""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
SECTION = re.compile(r"Contents/section(\d+)\.xml")


@dataclass(frozen=True)
class Cell:
    row: int
    col: int
    row_span: int
    col_span: int
    text: str


@dataclass(frozen=True)
class Table:
    index: int
    rows: int
    cols: int
    cells: tuple[Cell, ...]

    def start(self, row: int, col: int) -> Cell | None:
        """Return the cell whose top-left corner is (row, col)."""
        for cell in self.cells:
            if cell.row == row and cell.col == col:
                return cell
        return None

    def covering(self, row: int, col: int) -> Cell | None:
        """Return the cell that covers (row, col), including merged cells."""
        for cell in self.cells:
            if (cell.row <= row < cell.row + cell.row_span
                    and cell.col <= col < cell.col + cell.col_span):
                return cell
        return None


def cell_text(tc: ET.Element) -> str:
    # 형광펜(markpen) 같은 하위 요소 뒤의 글자도 읽으려고 itertext를 쓴다.
    return "".join("".join(t.itertext()) for t in tc.iter(HP + "t")).strip()


def read_tables(path: Path) -> list[Table]:
    with zipfile.ZipFile(path) as archive:
        sections = sorted(
            (name for name in archive.namelist() if SECTION.fullmatch(name)),
            key=lambda name: int(SECTION.fullmatch(name).group(1)),
        )
        if not sections:
            raise ValueError(f"{path.name}: HWPX 본문(section)이 없다")
        tables = []
        for name in sections:
            root = ET.fromstring(archive.read(name))
            for tbl in root.iter(HP + "tbl"):
                cells = []
                for tr in tbl.findall(HP + "tr"):
                    for tc in tr.findall(HP + "tc"):
                        addr, span = tc.find(HP + "cellAddr"), tc.find(HP + "cellSpan")
                        if addr is None or span is None:
                            raise ValueError(f"{path.name}: 셀 주소나 병합 정보가 없다")
                        cells.append(Cell(
                            int(addr.get("rowAddr")), int(addr.get("colAddr")),
                            int(span.get("rowSpan")), int(span.get("colSpan")), cell_text(tc),
                        ))
                tables.append(Table(len(tables), int(tbl.get("rowCnt")), int(tbl.get("colCnt")), tuple(cells)))
    return tables
