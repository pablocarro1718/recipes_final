#!/usr/bin/env python3
"""Minimal validation test for the internal recipe schema."""
from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.utils.recipe_schema import (
    Ingredient,
    LANGUAGE_ES,
    RECIPE_TYPE_ROBOT_COOKER,
    Recipe,
    RecipeMeta,
    Step,
    validate_recipe,
)


def main() -> None:
    recipe = Recipe(
        meta=RecipeMeta(
            recipe_no=1,
            language=LANGUAGE_ES,
            recipe_type=RECIPE_TYPE_ROBOT_COOKER,
            name="Tinga de pollo",
            servings=4,
        ),
        ingredients=[
            Ingredient(no=1, qty=300, unit="g", name="pechuga de pollo"),
        ],
        steps=[
            Step(no=1, mode="描述(Description)", description="Agrega el pollo."),
        ],
    )

    errors = validate_recipe(recipe)
    assert not errors, f"Unexpected errors: {errors}"

    bad_recipe = Recipe(
        meta=RecipeMeta(
            recipe_no=0,
            language="EN",
            recipe_type="",
            name=" ",
            servings=0,
        ),
        ingredients=[],
        steps=[],
    )

    bad_errors = validate_recipe(bad_recipe)
    assert bad_errors, "Expected validation errors for invalid recipe"


if __name__ == "__main__":
    main()
