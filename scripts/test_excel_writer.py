#!/usr/bin/env python3
"""Smoke test for Excel writer using the provider template."""
from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Dict, Optional
from xml.etree import ElementTree as ET

import sys

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.generators.excel_writer import write_recipes_to_template
from src.utils.recipe_schema import Ingredient, Recipe, RecipeMeta, Step
from src.validators.rule_validator import MODE_ADAPTED, MODE_DESCRIPTION

NS_MAIN = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_REL = {"rel": "http://schemas.openxmlformats.org/package/2006/relationships"}


def get_sheet_paths(z: zipfile.ZipFile) -> Dict[str, str]:
    workbook = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rel_map = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels.findall("rel:Relationship", NS_REL)
    }
    return {
        sheet.attrib["name"]: f"xl/{rel_map[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]}"
        for sheet in workbook.findall("main:sheets/main:sheet", NS_MAIN)
    }


def load_shared_strings(z: zipfile.ZipFile) -> Dict[int, str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return {}
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    strings = {}
    for idx, si in enumerate(root.findall("main:si", NS_MAIN)):
        text = "".join(t.text or "" for t in si.findall(".//main:t", NS_MAIN))
        strings[idx] = text
    return strings


def cell_value(cell: ET.Element, shared: Dict[int, str]) -> Optional[str]:
    if cell.attrib.get("t") == "s":
        value = cell.find("main:v", NS_MAIN)
        if value is None or value.text is None:
            return None
        try:
            return shared[int(value.text)]
        except (ValueError, KeyError):
            return None
    inline = cell.find("main:is/main:t", NS_MAIN)
    if inline is not None and inline.text is not None:
        return inline.text
    value = cell.find("main:v", NS_MAIN)
    return value.text if value is not None else None


def header_map(sheet: ET.Element, shared: Dict[int, str]) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    row = sheet.find("main:sheetData/main:row[@r='1']", NS_MAIN)
    if row is None:
        return headers
    for cell in row.findall("main:c", NS_MAIN):
        ref = cell.attrib.get("r", "")
        col = "".join(ch for ch in ref if ch.isalpha())
        value = cell_value(cell, shared)
        if value:
            headers[value] = col
    return headers


def read_cell(
    sheet: ET.Element, shared: Dict[int, str], header: str, row_num: int
) -> Optional[str]:
    headers = header_map(sheet, shared)
    col = headers.get(header)
    if not col:
        return None
    cell = sheet.find(
        f"main:sheetData/main:row[@r='{row_num}']/main:c[@r='{col}{row_num}']",
        NS_MAIN,
    )
    if cell is None:
        return None
    return cell_value(cell, shared)


def main() -> None:
    template = repo_root / "Excel template recetas.xlsx"
    output = repo_root / "tmp_excel_writer_output.xlsx"

    recipe = Recipe(
        meta=RecipeMeta(
            recipe_no=1,
            language="ES",
            recipe_type="汤机(Robot Cooker)",
            name="Receta de prueba",
            servings=2,
        ),
        ingredients=[
            Ingredient(no=1, qty=200, unit="g", name="cebolla"),
            Ingredient(no=2, qty=1, unit="pcs", name="chile serrano"),
        ],
        steps=[
            Step(no=1, mode=MODE_DESCRIPTION, description="Pique la cebolla."),
            Step(no=2, mode=MODE_ADAPTED, temperature=120, speed=2, minutes=5, seconds=0),
        ],
    )

    write_recipes_to_template([recipe], template, output)

    with zipfile.ZipFile(output) as z:
        shared = load_shared_strings(z)
        sheets = get_sheet_paths(z)
        recipe_sheet = ET.fromstring(z.read(sheets["食谱列表Recipe List"]))
        ingredient_sheet = ET.fromstring(z.read(sheets["食材Ingredients List"]))
        steps_sheet = ET.fromstring(z.read(sheets["食谱步骤Cooking Steps"]))

        assert (
            read_cell(recipe_sheet, shared, "*食谱名称\nRecipe Name", 2) == "Receta de prueba"
        ), "Recipe name missing"
        assert (
            read_cell(ingredient_sheet, shared, "*食材/单位\nIngredients/Unit", 2) == "g"
        )
        assert (
            read_cell(steps_sheet, shared, "*步骤/工作模式\nWorking Mode", 3)
            == MODE_ADAPTED
        )

    output.unlink()
    print("Excel writer smoke test passed.")


if __name__ == "__main__":
    main()
