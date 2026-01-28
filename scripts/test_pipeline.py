#!/usr/bin/env python3
"""Smoke test for the end-to-end pipeline orchestration."""
from __future__ import annotations

import json
from pathlib import Path

import sys

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from scripts.schema_snapshot import snapshot_template
from src.pipeline.run_pipeline import run_pipeline
from src.utils.recipe_schema import Ingredient, Recipe, RecipeMeta, Step
from src.validators.rule_validator import MODE_ADAPTED, MODE_DESCRIPTION


def main() -> None:
    template = repo_root / "Excel template recetas.xlsx"
    snapshot_path = repo_root / "tmp_schema_snapshot.json"
    output_path = repo_root / "tmp_pipeline_output.xlsx"
    input_path = repo_root / "tmp_pipeline_input.json"

    snapshot = snapshot_template(template)
    snapshot_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    recipe = Recipe(
        meta=RecipeMeta(
            recipe_no=1,
            language="ES",
            recipe_type="汤机(Robot Cooker)",
            name="Receta pipeline",
            servings=2,
        ),
        ingredients=[
            Ingredient(no=1, qty=200, unit="g", name="cebolla"),
        ],
        steps=[
            Step(no=1, mode=MODE_DESCRIPTION, description="Pique la cebolla."),
            Step(no=2, mode=MODE_ADAPTED, temperature=120, speed=2, minutes=5, seconds=0),
        ],
    )

    payload = {
        "recipes": [
            {
                "meta": recipe.meta.__dict__,
                "ingredients": [ing.__dict__ for ing in recipe.ingredients],
                "steps": [step.__dict__ for step in recipe.steps],
            }
        ]
    }
    input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    run_pipeline([recipe], snapshot_path, template, output_path)

    assert output_path.exists(), "Pipeline did not write output file"

    output_path.unlink()
    input_path.unlink()
    snapshot_path.unlink()
    print("Pipeline smoke test passed.")


if __name__ == "__main__":
    main()
