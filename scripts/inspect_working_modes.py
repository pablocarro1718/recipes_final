#!/usr/bin/env python3
"""Summarize working mode usage from an existing recipe workbook."""
from __future__ import annotations

import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

NS_MAIN = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_REL = {"rel": "http://schemas.openxmlformats.org/package/2006/relationships"}


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


def get_sheet_path(z: zipfile.ZipFile, sheet_name: str) -> str:
    workbook = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rel_map = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels.findall("rel:Relationship", NS_REL)
    }
    for sheet in workbook.findall("main:sheets/main:sheet", NS_MAIN):
        name = sheet.attrib["name"]
        if name != sheet_name:
            continue
        rid = sheet.attrib[
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        ]
        return f"xl/{rel_map[rid]}"
    raise ValueError(f"Sheet {sheet_name} not found")


def get_header_map(sheet: ET.Element, shared: List[str]) -> Dict[str, str]:
    row = sheet.find(".//main:row[@r='1']", NS_MAIN)
    if row is None:
        return {}
    headers = {}
    for cell in row.findall("main:c", NS_MAIN):
        ref = cell.attrib.get("r", "")
        col = "".join(ch for ch in ref if ch.isalpha())
        headers[col] = cell_value(cell, shared) or ""
    return headers


def inspect_working_modes(xlsx_path: Path) -> Dict[str, Dict[str, int]]:
    with zipfile.ZipFile(xlsx_path) as z:
        shared = load_shared_strings(z)
        sheet_path = get_sheet_path(z, "食谱步骤Cooking Steps")
        root = ET.fromstring(z.read(sheet_path))
        header_map = get_header_map(root, shared)
        header_to_col = {v: k for k, v in header_map.items()}
        wm_col = header_to_col.get("*步骤/工作模式\nWorking Mode")
        desc_col = header_to_col.get("步骤/文字描述\nDescription")
        temp_col = header_to_col.get("步骤/加热温度\nWorking Temperature")
        rot_dir_col = header_to_col.get("步骤/旋转方向\nRotation Direction\n（R/L)")
        rot_speed_col = header_to_col.get("步骤/旋转速度\nRotation Speed\n（0-12）")
        mins_col = header_to_col.get("步骤/分\nWorking Time/Mins")
        secs_col = header_to_col.get("步骤/秒\nWorking Time/ Seconds")

        counts = defaultdict(int)
        with_desc = defaultdict(int)
        with_controls = defaultdict(int)

        for row in root.findall("main:sheetData/main:row", NS_MAIN):
            if row.attrib.get("r") == "1":
                continue
            cells = {}
            for cell in row.findall("main:c", NS_MAIN):
                ref = cell.attrib.get("r", "")
                col = "".join(ch for ch in ref if ch.isalpha())
                cells[col] = cell_value(cell, shared)
            mode = cells.get(wm_col)
            if not mode:
                continue
            counts[mode] += 1
            if desc_col and cells.get(desc_col):
                with_desc[mode] += 1
            if any(
                cells.get(col)
                for col in [temp_col, rot_dir_col, rot_speed_col, mins_col, secs_col]
                if col
            ):
                with_controls[mode] += 1

    return {
        "counts": dict(counts),
        "with_description": dict(with_desc),
        "with_controls": dict(with_controls),
    }


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Inspect working mode usage in an existing recipes workbook."
    )
    parser.add_argument("xlsx", type=Path, help="Path to the workbook")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("working_mode_summary.json"),
        help="Output JSON path",
    )
    args = parser.parse_args()

    summary = inspect_working_modes(args.xlsx)
    args.output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
