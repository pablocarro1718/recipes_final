#!/usr/bin/env python3
"""Write recipes into the provider Excel template using standard library only."""
from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from xml.etree import ElementTree as ET

from src.utils.recipe_schema import Recipe, Step

NS_MAIN = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_REL = {"rel": "http://schemas.openxmlformats.org/package/2006/relationships"}


@dataclass(frozen=True)
class WorkbookSheet:
    name: str
    path: str


RECIPE_LIST_HEADERS = {
    "*食谱序号\nRecipe NO": "recipe_no",
    "语言\nLanguage": "language",
    "*食谱类型\nRecipe Type": "recipe_type",
    "*食谱名称\nRecipe Name": "name",
    "*食谱分类（单选）\nRecipe Category(Multiple Choice)": "category",
    "*份量\nServings": "servings",
    "*准备时间/小时\nPrepare Time/Hour": "prep_hours",
    "*准备时间/分\nPrepare Time/Minutes": "prep_minutes",
    "*烹饪时间/小时\nCooking Time/Hour": "cook_hours",
    "*烹饪时间/分\nCooking Time/Minutes": "cook_minutes",
    "*休息时间/小时\nRest Time/Hour": "rest_hours",
    "*休息时间/分\nRest Time/Minutes": "rest_minutes",
    "*难易度\nDifficulty Level": "difficulty",
    "*配件序号（可多选）\nAccessory No/ID（Choose multiply ）": "accessory_no",
    "所用配件名称\nUsed Accessories": "accessory_name",
    "食谱制作总步骤（做法介绍）\nOverview For Cooking Steps": "overview",
}

INGREDIENT_HEADERS = {
    "*食谱序号\nRecipe NO": "recipe_no",
    "语言\nLanguage": "language",
    "*食谱类型\nRecipe Type": "recipe_type",
    "*食谱名称\nRecipe Name": "name",
    "*食材序号\nIngredients No": "ingredient_no",
    "*食材/数量\nIngredients/qty": "qty",
    "*食材/单位\nIngredients/Unit": "unit",
    "*食材/名称\nIngredient/Name": "ingredient_name",
}

STEP_HEADERS = {
    "*食谱序号\nRecipe NO": "recipe_no",
    "语言\nLanguage": "language",
    "*食谱类型\nRecipe Type": "recipe_type",
    "*食谱名称\nRecipe Name": "name",
    "*步骤序号\nCooking Step NO": "step_no",
    "*步骤/工作模式\nWorking Mode": "mode",
    "步骤/文字描述\nDescription": "description",
    "步骤/加热温度\nWorking Temperature": "temperature",
    "步骤/旋转方向\nRotation Direction\n（R/L)": "direction",
    "步骤/旋转速度\nRotation Speed\n（0-12）": "speed",
    "步骤/分\nWorking Time/Mins": "minutes",
    "步骤/秒\nWorking Time/ Seconds": "seconds",
}

DEFAULT_CATEGORY = "Platillos Mexicanos"
DEFAULT_PREP_HOURS = 0
DEFAULT_PREP_MINUTES = 0
DEFAULT_COOK_HOURS = 0
DEFAULT_COOK_MINUTES = 0
DEFAULT_REST_HOURS = 0
DEFAULT_REST_MINUTES = 0
DEFAULT_DIFFICULTY = "fácil"
DEFAULT_ACCESSORY_NO = 5
DEFAULT_ACCESSORY_NAME = "Cuchilla"


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


def load_shared_strings(z: zipfile.ZipFile) -> List[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    strings = []
    for si in root.findall("main:si", NS_MAIN):
        text = "".join(t.text or "" for t in si.findall(".//main:t", NS_MAIN))
        strings.append(text)
    return strings


def header_map(sheet: ET.Element, shared: List[str]) -> Dict[str, str]:
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


def cell_value(cell: ET.Element, shared: List[str]) -> Optional[str]:
    if cell.attrib.get("t") == "s":
        value = cell.find("main:v", NS_MAIN)
        if value is None or value.text is None:
            return None
        try:
            return shared[int(value.text)]
        except (ValueError, IndexError):
            return None
    inline = cell.find("main:is/main:t", NS_MAIN)
    if inline is not None and inline.text is not None:
        return inline.text
    value = cell.find("main:v", NS_MAIN)
    if value is None:
        return None
    return value.text


def clear_data_rows(sheet: ET.Element) -> None:
    sheet_data = sheet.find("main:sheetData", NS_MAIN)
    if sheet_data is None:
        return
    for row in list(sheet_data.findall("main:row", NS_MAIN)):
        if row.attrib.get("r") != "1":
            sheet_data.remove(row)


def make_cell(col: str, row_num: int, value: object) -> ET.Element:
    cell = ET.Element(f"{{{NS_MAIN['main']}}}c", r=f"{col}{row_num}")
    if value is None:
        return cell
    if isinstance(value, (int, float)):
        v = ET.SubElement(cell, f"{{{NS_MAIN['main']}}}v")
        v.text = str(value)
        return cell
    cell.set("t", "inlineStr")
    is_el = ET.SubElement(cell, f"{{{NS_MAIN['main']}}}is")
    t_el = ET.SubElement(is_el, f"{{{NS_MAIN['main']}}}t")
    t_el.text = str(value)
    return cell


def append_rows(
    sheet: ET.Element,
    header_to_col: Dict[str, str],
    rows: List[Dict[str, object]],
    headers: Dict[str, str],
) -> None:
    sheet_data = sheet.find("main:sheetData", NS_MAIN)
    if sheet_data is None:
        sheet_data = ET.SubElement(sheet, f"{{{NS_MAIN['main']}}}sheetData")
    start_row = 2
    for offset, row_data in enumerate(rows):
        row_num = start_row + offset
        row = ET.Element(f"{{{NS_MAIN['main']}}}row", r=str(row_num))
        for header, key in headers.items():
            col = header_to_col.get(header)
            if not col:
                continue
            value = row_data.get(key)
            if value is None:
                continue
            row.append(make_cell(col, row_num, value))
        sheet_data.append(row)


def recipe_list_rows(recipes: List[Recipe]) -> List[Dict[str, object]]:
    rows = []
    for recipe in recipes:
        rows.append(
            {
                "recipe_no": recipe.meta.recipe_no,
                "language": recipe.meta.language,
                "recipe_type": recipe.meta.recipe_type,
                "name": recipe.meta.name,
                "category": DEFAULT_CATEGORY,
                "servings": recipe.meta.servings,
                "prep_hours": DEFAULT_PREP_HOURS,
                "prep_minutes": DEFAULT_PREP_MINUTES,
                "cook_hours": DEFAULT_COOK_HOURS,
                "cook_minutes": DEFAULT_COOK_MINUTES,
                "rest_hours": DEFAULT_REST_HOURS,
                "rest_minutes": DEFAULT_REST_MINUTES,
                "difficulty": DEFAULT_DIFFICULTY,
                "accessory_no": DEFAULT_ACCESSORY_NO,
                "accessory_name": DEFAULT_ACCESSORY_NAME,
                "overview": build_overview(recipe.steps),
            }
        )
    return rows


def build_overview(steps: List[Step]) -> str:
    sentences: List[str] = [f"Ponemos en el vaso el accesorio \"{DEFAULT_ACCESSORY_NAME}\"."]
    for step in steps:
        if step.description and step.description.strip():
            sentences.append(step.description.strip())
            continue
        if step.temperature is None and step.speed is None and step.minutes is None and step.seconds is None:
            continue
        parts: List[str] = []
        if step.minutes is not None:
            parts.append(f"{step.minutes} minutos")
        if step.seconds is not None and step.seconds != 0:
            parts.append(f"{step.seconds} segundos")
        time_text = " ".join(parts)
        temp_text = f"{step.temperature}°C" if step.temperature is not None else None
        speed_text = f"velocidad {step.speed}" if step.speed is not None else None
        details = ", ".join(item for item in [time_text, temp_text, speed_text] if item)
        if details:
            sentences.append(f"Cocinamos {details}.")
    return " ".join(sentences)


def ingredient_rows(recipes: List[Recipe]) -> List[Dict[str, object]]:
    rows = []
    for recipe in recipes:
        for ingredient in recipe.ingredients:
            rows.append(
                {
                    "recipe_no": recipe.meta.recipe_no,
                    "language": recipe.meta.language,
                    "recipe_type": recipe.meta.recipe_type,
                    "name": recipe.meta.name,
                    "ingredient_no": ingredient.no,
                    "qty": ingredient.qty,
                    "unit": ingredient.unit,
                    "ingredient_name": ingredient.name,
                }
            )
    return rows


def step_rows(recipes: List[Recipe]) -> List[Dict[str, object]]:
    rows = []
    for recipe in recipes:
        for step in recipe.steps:
            rows.append(step_row(recipe, step))
    return rows


def step_row(recipe: Recipe, step: Step) -> Dict[str, object]:
    return {
        "recipe_no": recipe.meta.recipe_no,
        "language": recipe.meta.language,
        "recipe_type": recipe.meta.recipe_type,
        "name": recipe.meta.name,
        "step_no": step.no,
        "mode": step.mode,
        "description": step.description,
        "temperature": step.temperature,
        "direction": step.direction,
        "speed": step.speed,
        "minutes": step.minutes,
        "seconds": step.seconds,
    }


def write_recipes_to_template(
    recipes: List[Recipe], template_path: Path, output_path: Path
) -> None:
    with zipfile.ZipFile(template_path) as z:
        shared = load_shared_strings(z)
        sheets = get_sheet_paths(z)
        sheet_map = {sheet.name: sheet.path for sheet in sheets}

        replacements: Dict[str, bytes] = {}

        for name, headers, rows in [
            ("食谱列表Recipe List", RECIPE_LIST_HEADERS, recipe_list_rows(recipes)),
            ("食材Ingredients List", INGREDIENT_HEADERS, ingredient_rows(recipes)),
            ("食谱步骤Cooking Steps", STEP_HEADERS, step_rows(recipes)),
        ]:
            path = sheet_map.get(name)
            if not path:
                raise ValueError(f"Missing sheet {name} in template")
            root = ET.fromstring(z.read(path))
            headers_to_col = header_map(root, shared)
            clear_data_rows(root)
            append_rows(root, headers_to_col, rows, headers)
            replacements[path] = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        with zipfile.ZipFile(output_path, "w") as out:
            for item in z.infolist():
                if item.filename in replacements:
                    out.writestr(item, replacements[item.filename])
                else:
                    out.writestr(item, z.read(item.filename))
