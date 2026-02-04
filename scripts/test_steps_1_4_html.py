#!/usr/bin/env python3
"""Validate steps 1-4 with a Cookidoo HTML sample (JSON-LD only)."""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from scripts.schema_snapshot import snapshot_template
from src.transformers.list_normalizer import normalize_recipe
from src.utils.lookups_loader import load_lookups
from src.utils.recipe_schema import (
    LANGUAGE_ES,
    RECIPE_TYPE_ROBOT_COOKER,
    Ingredient,
    Recipe,
    RecipeMeta,
    Step,
    validate_recipe,
)
from src.validators.rule_validator import MODE_ADAPTED, MODE_DESCRIPTION, validate_steps


@dataclass(frozen=True)
class ParsedRecipe:
    name: str
    servings: int
    ingredients: List[str]
    instructions: List[str]


UNIT_MAP = {
    "cdita": "Cucharada",
    "cucharada": "Cucharada",
    "cucharadas": "Cucharada",
}


def extract_json_ld(html_text: str) -> dict:
    candidates = re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    for candidate in candidates:
        raw = html.unescape(candidate.strip())
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("@type") == "Recipe":
            return data
    raise ValueError("No Recipe JSON-LD found.")


def parse_servings(recipe_yield: str) -> int:
    match = re.search(r"\d+", recipe_yield or "")
    if not match:
        raise ValueError("Unable to parse servings")
    return int(match.group(0))


def parse_quantity(value: str) -> float:
    cleaned = value.strip().replace("½", "1/2")
    if "/" in cleaned:
        return float(Fraction(cleaned))
    return float(cleaned)


def parse_ingredient(raw: str, lookups: Iterable[str]) -> Ingredient:
    cleaned = html.unescape(raw).strip()
    match = re.match(r"^([\d½/.]+)\s+([^\s]+)?\s*(.+)$", cleaned)
    if not match:
        raise ValueError(f"Unable to parse ingredient: {raw}")
    qty_raw, unit_raw, name = match.groups()
    qty = parse_quantity(qty_raw)
    unit = (unit_raw or "").strip()
    unit_key = unit.lower()
    unit_candidate = UNIT_MAP.get(unit_key, unit)
    if unit_candidate and unit_candidate in lookups:
        resolved_unit = unit_candidate
        resolved_name = name
    else:
        resolved_unit = "pcs"
        resolved_name = f"{unit} {name}".strip()
    return Ingredient(no=0, qty=qty, unit=resolved_unit, name=resolved_name.strip())


def strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


SPOON_SYMBOLS = {"\ue003"}


def parse_controls(text: str) -> List[Tuple[Optional[int], Optional[int], Optional[int]]]:
    controls = []
    for segment in re.findall(r"<nobr>(.*?)</nobr>", text):
        seg = html.unescape(segment)
        minutes = None
        seconds = None
        temp = None
        speed = None
        min_match = re.search(r"(\d+)\s*min", seg)
        sec_match = re.search(r"(\d+)\s*seg", seg)
        temp_match = re.search(r"(\d+)\s*°C", seg)
        speed_match = re.search(r"vel\s*(\d+)", seg)
        has_spoon_symbol = any(symbol in seg for symbol in SPOON_SYMBOLS)
        if min_match:
            minutes = int(min_match.group(1))
        if sec_match:
            seconds = int(sec_match.group(1))
        if temp_match:
            temp = int(temp_match.group(1))
        if speed_match:
            speed = int(speed_match.group(1))
        if has_spoon_symbol:
            speed = 1
        controls.append((minutes, seconds, temp, speed))
    return controls


def parse_recipe(data: dict) -> ParsedRecipe:
    name = data.get("name", "").strip()
    servings = parse_servings(data.get("recipeYield", ""))
    ingredients = data.get("recipeIngredient", [])
    instructions = [item.get("text", "") for item in data.get("recipeInstructions", [])]
    return ParsedRecipe(name=name, servings=servings, ingredients=ingredients, instructions=instructions)


def build_steps(instructions: List[str]) -> List[Step]:
    steps: List[Step] = []
    index = 1
    for instruction in instructions:
        description = strip_tags(instruction).strip()
        steps.append(Step(no=index, mode=MODE_DESCRIPTION, description=description))
        index += 1
        for minutes, seconds, temperature, speed in parse_controls(instruction):
            steps.append(
                Step(
                    no=index,
                    mode=MODE_ADAPTED,
                    temperature=temperature,
                    speed=speed,
                    minutes=minutes,
                    seconds=seconds,
                )
            )
            index += 1
    return steps


def main() -> None:
    parser = argparse.ArgumentParser(description="Run steps 1-4 validation on HTML sample.")
    parser.add_argument(
        "--html",
        type=Path,
        default=repo_root / "samples" / "bisteces_a_la_mexicana.html",
        help="Path to HTML file containing Recipe JSON-LD",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=repo_root / "Excel template recetas.xlsx",
        help="Path to the Excel template",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=repo_root / "schema_snapshot.json",
        help="Path to output schema snapshot JSON",
    )
    args = parser.parse_args()

    if not args.snapshot.exists():
        snapshot = snapshot_template(args.template)
        args.snapshot.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    lookups = load_lookups(args.snapshot)
    html_text = args.html.read_text(encoding="utf-8")
    data = extract_json_ld(html_text)
    parsed = parse_recipe(data)

    ingredients = []
    for idx, raw in enumerate(parsed.ingredients, start=1):
        ingredient = parse_ingredient(raw, lookups.units)
        ingredients.append(Ingredient(no=idx, qty=ingredient.qty, unit=ingredient.unit, name=ingredient.name))

    steps = build_steps(parsed.instructions)
    recipe = Recipe(
        meta=RecipeMeta(
            recipe_no=1,
            language=LANGUAGE_ES,
            recipe_type=RECIPE_TYPE_ROBOT_COOKER,
            name=parsed.name,
            servings=parsed.servings,
        ),
        ingredients=ingredients,
        steps=steps,
    )

    schema_errors = validate_recipe(recipe)
    if schema_errors:
        raise SystemExit(f"Schema errors: {schema_errors}")

    normalization_errors = normalize_recipe(recipe, lookups, accessories=[])
    if normalization_errors:
        raise SystemExit(f"Normalization errors: {normalization_errors}")

    rule_errors = validate_steps(steps)
    if rule_errors:
        raise SystemExit(f"Rule errors: {rule_errors}")

    print("Steps 1-4 validation passed.")


if __name__ == "__main__":
    main()
