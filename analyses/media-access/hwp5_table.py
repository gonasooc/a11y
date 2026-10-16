"""Read table cells from HWP 5.0 (OLE compound) documents with the standard library."""

from __future__ import annotations

import struct
import sys
import zlib
from array import array
from pathlib import Path

from hwpx_table import Cell, Table


OLE_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")
FREE, END = 0xFFFFFFFF, 0xFFFFFFFE
TAG_PARA_TEXT, TAG_LIST_HEADER, TAG_TABLE = 67, 72, 77
# 문단 글자 속 컨트롤 문자. 이 코드들은 8칸(16바이트)을 차지하고, 10·13과 24 이상은 1칸이다.
WIDE_CONTROLS = {*range(1, 10), 11, 12, *range(14, 24)}
SPACES = {30: " ", 31: " ", 24: "-"}


class HwpError(ValueError):
    pass


class Compound:
    """Just enough of the OLE compound file format to read named streams."""

    def __init__(self, data: bytes):
        if data[:8] != OLE_MAGIC:
            raise HwpError("OLE 복합 문서가 아니다")
        self.data = data
        self.sector_size = 1 << struct.unpack_from("<H", data, 30)[0]
        self.mini_size = 1 << struct.unpack_from("<H", data, 32)[0]
        fat_count, dir_start, _, self.cutoff, mini_start, mini_count, difat_start, difat_count = \
            struct.unpack_from("<8I", data, 44)
        per = self.sector_size // 4
        fat_sectors = list(struct.unpack_from("<109I", data, 76))
        sector = difat_start
        for _ in range(difat_count):
            values = struct.unpack_from(f"<{per}I", self.sector(sector))
            fat_sectors += values[:-1]
            sector = values[-1]
        self.fat = []
        for number in [n for n in fat_sectors if n not in (FREE, END)][:fat_count]:
            self.fat += struct.unpack_from(f"<{per}I", self.sector(number))
        directory = self.chain(dir_start, self.fat, self.sector)
        self.entries = []
        for offset in range(0, len(directory) - 127, 128):
            entry = directory[offset:offset + 128]
            length = struct.unpack_from("<H", entry, 64)[0]
            left, right, child = struct.unpack_from("<3I", entry, 68)
            start, size = struct.unpack_from("<IQ", entry, 116)
            self.entries.append({
                "name": entry[:max(length - 2, 0)].decode("utf-16-le"), "type": entry[66],
                "left": left, "right": right, "child": child, "start": start, "size": size & 0xFFFFFFFF,
            })
        root = self.entries[0]
        self.mini_stream = self.chain(root["start"], self.fat, self.sector)[:root["size"]]
        mini_fat = self.chain(mini_start, self.fat, self.sector) if mini_count else b""
        self.mini_fat = list(struct.unpack_from(f"<{len(mini_fat) // 4}I", mini_fat))
        self.paths = self.walk(root["child"])

    def sector(self, number: int) -> bytes:
        offset = (number + 1) * self.sector_size
        if offset + self.sector_size > len(self.data):
            raise HwpError("섹터가 파일 밖에 있다")
        return self.data[offset:offset + self.sector_size]

    def mini_sector(self, number: int) -> bytes:
        return self.mini_stream[number * self.mini_size:(number + 1) * self.mini_size]

    @staticmethod
    def chain(start: int, table: list[int], read) -> bytes:
        parts, seen, number = [], set(), start
        while number not in (FREE, END):
            if number in seen or number >= len(table):
                raise HwpError("섹터 연결이 끊기거나 되돌아간다")
            seen.add(number)
            parts.append(read(number))
            number = table[number]
        return b"".join(parts)

    def walk(self, child: int) -> dict[str, dict]:
        paths, stack, seen = {}, [(child, "")], set()
        while stack:
            index, prefix = stack.pop()
            if index == FREE or index >= len(self.entries) or index in seen:
                continue
            seen.add(index)
            entry = self.entries[index]
            stack += [(entry["left"], prefix), (entry["right"], prefix)]
            paths[prefix + entry["name"]] = entry
            if entry["type"] == 1:  # 저장소(폴더)
                stack.append((entry["child"], prefix + entry["name"] + "/"))
        return paths

    def read(self, path: str) -> bytes:
        entry = self.paths.get(path)
        if entry is None:
            raise HwpError(f"{path} 스트림이 없다")
        if entry["size"] < self.cutoff:
            data = self.chain(entry["start"], self.mini_fat, self.mini_sector)
        else:
            data = self.chain(entry["start"], self.fat, self.sector)
        if len(data) < entry["size"]:
            raise HwpError(f"{path}: 스트림이 선언된 크기보다 짧다")
        return data[:entry["size"]]


def records(data: bytes):
    offset = 0
    while offset < len(data):
        if offset + 4 > len(data):
            raise HwpError("레코드 머리가 잘렸다")
        header = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        tag, level, size = header & 0x3FF, (header >> 10) & 0x3FF, header >> 20
        if size == 0xFFF:
            size = struct.unpack_from("<I", data, offset)[0]
            offset += 4
        if offset + size > len(data):
            raise HwpError("레코드 본문이 잘렸다")
        yield tag, level, data[offset:offset + size]
        offset += size


def para_text(body: bytes) -> str:
    units = array("H")
    units.frombytes(body[:len(body) // 2 * 2])
    if sys.byteorder == "big":
        units.byteswap()
    out, index = [], 0
    while index < len(units):
        code = units[index]
        if code in WIDE_CONTROLS:
            index += 8
            continue
        if code < 32:
            if code in SPACES:
                out.append(ord(SPACES[code]))
            index += 1
            continue
        out.append(code)
        index += 1
    # 사용자 정의 문자(짝 없는 서로게이트)는 대체 문자로 바꾼다.
    return array("H", out).tobytes().decode("utf-16-le" if sys.byteorder == "little" else "utf-16-be", errors="replace")


def section_tables(data: bytes, first_index: int) -> list[Table]:
    done, stack = [], []

    def close(table: dict) -> None:
        cells = []
        for cell in table["cells"]:
            if cell["row"] + cell["row_span"] > table["rows"] or cell["col"] + cell["col_span"] > table["cols"]:
                raise HwpError("셀 주소가 표 크기를 벗어난다")
            cells.append(Cell(cell["row"], cell["col"], cell["row_span"], cell["col_span"], "".join(cell["texts"]).strip()))
        done.append((table["order"], cells, table["rows"], table["cols"]))

    order = 0
    for tag, level, body in records(data):
        # 표 레코드보다 얕은 레코드가 나오면 그 표는 끝났다.
        while stack and level < stack[-1]["level"]:
            close(stack.pop())
        if tag == TAG_TABLE:
            rows, cols = struct.unpack_from("<HH", body, 4)
            stack.append({"level": level, "rows": rows, "cols": cols, "cells": [], "cell": None, "order": order})
            order += 1
        elif tag == TAG_LIST_HEADER and stack and level == stack[-1]["level"]:
            # 셀은 표 레코드와 같은 깊이에 있다. 각주·글상자의 목록 머리는 더 깊어서 셀로 세지 않는다.
            col, row, col_span, row_span = struct.unpack_from("<4H", body, 8)
            cell = {"row": row, "col": col, "row_span": row_span, "col_span": col_span, "texts": []}
            stack[-1]["cells"].append(cell)
            stack[-1]["cell"] = cell
        elif tag == TAG_PARA_TEXT and stack and stack[-1]["cell"] is not None and level == stack[-1]["level"] + 1:
            stack[-1]["cell"]["texts"].append(para_text(body))
    while stack:
        close(stack.pop())
    # 바깥 표가 안쪽 표보다 먼저 시작하므로 시작 순서로 번호를 매긴다.
    return [Table(first_index + i, rows, cols, tuple(cells))
            for i, (_, cells, rows, cols) in enumerate(sorted(done, key=lambda item: item[0]))]


def read_tables(path: Path) -> list[Table]:
    compound = Compound(Path(path).read_bytes())
    header = compound.read("FileHeader")
    if not header.startswith(b"HWP Document File"):
        raise HwpError(f"{Path(path).name}: HWP 5.0 문서가 아니다")
    flags = struct.unpack_from("<I", header, 36)[0]
    if flags & 0b110:
        raise HwpError(f"{Path(path).name}: 암호화 또는 배포용 문서라 읽지 않는다")
    sections = sorted((name for name in compound.paths if name.startswith("BodyText/Section")),
                      key=lambda name: int(name.rsplit("Section", 1)[1]))
    if not sections:
        raise HwpError(f"{Path(path).name}: 본문(BodyText) 구역이 없다")
    tables = []
    for name in sections:
        raw = compound.read(name)
        data = zlib.decompress(raw, -15) if flags & 1 else raw
        tables += section_tables(data, len(tables))
    return tables
