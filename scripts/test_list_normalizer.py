#!/usr/bin/env python3
"""Minimal test for list normalizer against template lookups."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.transformers.list_normalizer import normalize_recipe
from src.utils.lookups_loader import load_lookups
from src.utils.recipe_schema import (
    Ingredient,
    LANGUAGE_ES,
    RECIPE_TYPE_ROBOT_COOKER,
    Recipe,
    RecipeMeta,
    Step,
)


def main() -> None:
    snapshot_path = repo_root / "schema_snapshot.json"
    template_path = repo_root / "Excel template recetas.xlsx"

    subprocess.run(
        ["python", str(repo_root / "scripts/schema_snapshot.py"), str(template_path), "-o", str(snapshot_path)],
        check=True,
    )

    lookups = load_lookups(snapshot_path)

    recipe = Recipe(
        meta=RecipeMeta(
            recipe_no=1,
            language=LANGUAGE_ES,
            recipe_type=RECIPE_TYPE_ROBOT_COOKER,
            name="Prueba",
            servings=2,
        ),
        ingredients=[
            Ingredient(no=1, qty=100, unit=lookups.units[0], name="ingrediente"),
        ],
        steps=[
            Step(no=1, mode="描述(Description)", description="Paso."),
        ],
    )

    errors = normalize_recipe(recipe, lookups, accessories=[lookups.accessories[0]])
    assert not errors, f"Unexpected errors: {errors}"

    bad_recipe = Recipe(
        meta=recipe.meta,
        ingredients=[
            Ingredient(no=1, qty=100, unit="INVALID", name="ingrediente"),
        ],
        steps=[
            Step(no=1, mode="INVALID", description="Paso."),
        ],
    )

    bad_errors = normalize_recipe(bad_recipe, lookups, accessories=["INVALID"])
    assert bad_errors, "Expected normalization errors for invalid values"

    snapshot_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
