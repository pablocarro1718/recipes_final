#!/usr/bin/env python3
"""Extracts headers and reference lists from the recipe Excel templates.

This uses only the Python standard library to avoid external dependencies.
"""
from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from xml.etree import ElementTree as ET

NS_MAIN = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_REL = {"rel": "http://schemas.openxmlformats.org/package/2006/relationships"}


@dataclass
class WorkbookSheet:
    name: str
    path: str


def load_shared_strings(z: zipfile.ZipFile) -> List[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    strings = []
    for si in root.findall("main:si", NS_MAIN):
        text = "".join(t.text or "" for t in si.findall(".//main:t", NS_MAIN))
        strings.append(text)
    return strings


def cell_value(cell: ET.Element, shared: List[str]) -> Optional[str]:
    value = cell.find("main:v", NS_MAIN)
    if value is None:
        return None
    raw = value.text or ""
    if cell.attrib.get("t") == "s":
        try:
            return shared[int(raw)]
        except (ValueError, IndexError):
            return None
    return raw


def get_sheet_paths(z: zipfile.ZipFile) -> List[WorkbookSheet]:
    workbook = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rel_map = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels.findall("rel:Relationship", NS_REL)
    }
    sheets = []
    for sheet in workbook.findall("main:sheets/main:sheet", NS_MAIN):
        name = sheet.attrib["name"]
        rid = sheet.attrib[
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        ]
        sheets.append(WorkbookSheet(name=name, path=f"xl/{rel_map[rid]}"))
    return sheets


def get_row(sheet: ET.Element, shared: List[str], row_num: int) -> Dict[str, Optional[str]]:
    row = sheet.find(f".//main:row[@r='{row_num}']", NS_MAIN)
    if row is None:
        return {}
    values = {}
    for cell in row.findall("main:c", NS_MAIN):
        ref = cell.attrib.get("r", "")
        col = "".join(ch for ch in ref if ch.isalpha())
        values[col] = cell_value(cell, shared)
    return values


def col_sorted(values: Dict[str, Optional[str]]) -> List[Optional[str]]:
    def col_index(col: str) -> int:
        index = 0
        for ch in col:
            index = index * 26 + (ord(ch) - 64)
        return index

    return [values.get(col) for col in sorted(values, key=col_index)]


def iter_rows(sheet: ET.Element) -> Iterable[ET.Element]:
    yield from sheet.findall("main:sheetData/main:row", NS_MAIN)


def is_empty_row(row: ET.Element, shared: List[str]) -> bool:
    for cell in row.findall("main:c", NS_MAIN):
        if cell_value(cell, shared):
            return False
    return True


def read_list_sheet(
    sheet: ET.Element, shared: List[str], header_map: Dict[str, str]
) -> List[Dict[str, Optional[str]]]:
    rows = []
    for row in iter_rows(sheet):
        if row.attrib.get("r") == "1":
            continue
        if is_empty_row(row, shared):
            continue
        entry = {}
        for cell in row.findall("main:c", NS_MAIN):
            ref = cell.attrib.get("r", "")
            col = "".join(ch for ch in ref if ch.isalpha())
            header = header_map.get(col)
            if header:
                entry[header] = cell_value(cell, shared)
        if entry:
            rows.append(entry)
    return rows


def snapshot_template(xlsx_path: Path) -> dict:
    with zipfile.ZipFile(xlsx_path) as z:
        shared = load_shared_strings(z)
        sheets = get_sheet_paths(z)
        output = {
            "template": xlsx_path.name,
            "sheets": {},
        }

        for sheet in sheets:
            root = ET.fromstring(z.read(sheet.path))
            header_row = get_row(root, shared, 1)
            headers = col_sorted(header_row)
            output["sheets"][sheet.name] = {
                "headers": headers,
            }

            if sheet.name in {
                "分类列表Category List",
                "标签列表Label List",
                "配件列表Accessories List",
                "食材单位列表Unit For Ingredients",
                "自动程序Working Mode List",
            }:
                output["sheets"][sheet.name]["rows"] = read_list_sheet(
                    root, shared, header_row
                )
        return output


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Snapshot recipe Excel template schema.")
    parser.add_argument("xlsx", type=Path, help="Path to the Excel template")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("schema_snapshot.json"),
        help="Output JSON path",
    )
    args = parser.parse_args()

    snapshot = snapshot_template(args.xlsx)
    args.output.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
