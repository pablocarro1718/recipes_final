#!/usr/bin/env python3
"""Orchestrate recipe validation and export to the provider template."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from src.generators.excel_writer import write_recipes_to_template
from src.transformers.list_normalizer import normalize_recipe
from src.utils.lookups_loader import load_lookups
from src.utils.recipe_schema import Ingredient, Recipe, RecipeMeta, Step, validate_recipe
from src.validators.rule_validator import validate_steps


def load_recipes_from_json(path: Path) -> List[Recipe]:
    data = json.loads(path.read_text(encoding="utf-8"))
    recipes = []
    for item in data.get("recipes", []):
        meta = RecipeMeta(**item["meta"])
        ingredients = [Ingredient(**ing) for ing in item.get("ingredients", [])]
        steps = [Step(**step) for step in item.get("steps", [])]
        recipes.append(Recipe(meta=meta, ingredients=ingredients, steps=steps))
    return recipes


def run_pipeline(
    recipes: List[Recipe], snapshot_path: Path, template_path: Path, output_path: Path
) -> None:
    lookups = load_lookups(snapshot_path)

    for recipe in recipes:
        schema_errors = validate_recipe(recipe)
        if schema_errors:
            raise ValueError(f"Schema errors: {schema_errors}")

        normalization_errors = normalize_recipe(recipe, lookups, accessories=[])
        if normalization_errors:
            raise ValueError(f"Normalization errors: {normalization_errors}")

        rule_errors = validate_steps(recipe.steps)
        if rule_errors:
            raise ValueError(f"Rule errors: {rule_errors}")

    write_recipes_to_template(recipes, template_path, output_path)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run recipe pipeline.")
    parser.add_argument("--input", type=Path, required=True, help="Path to recipes JSON")
    parser.add_argument(
        "--snapshot",
        type=Path,
        required=True,
        help="Path to schema snapshot JSON from schema_snapshot.py",
    )
    parser.add_argument(
        "--template", type=Path, required=True, help="Path to provider Excel template"
    )
    parser.add_argument("--output", type=Path, required=True, help="Path to output XLSX")
    args = parser.parse_args()

    recipes = load_recipes_from_json(args.input)
    run_pipeline(recipes, args.snapshot, args.template, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
