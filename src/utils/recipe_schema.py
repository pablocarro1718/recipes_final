#!/usr/bin/env python3
"""Define and validate the internal recipe schema for the pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

LANGUAGE_ES = "ES"
RECIPE_TYPE_ROBOT_COOKER = "汤机(Robot Cooker)"


@dataclass(frozen=True)
class RecipeMeta:
    recipe_no: int
    language: str
    recipe_type: str
    name: str
    servings: int


@dataclass(frozen=True)
class Ingredient:
    no: int
    qty: float
    unit: str
    name: str


@dataclass(frozen=True)
class Step:
    no: int
    mode: str
    description: Optional[str] = None
    temperature: Optional[int] = None
    speed: Optional[int] = None
    direction: Optional[str] = None
    minutes: Optional[int] = None
    seconds: Optional[int] = None


@dataclass(frozen=True)
class Recipe:
    meta: RecipeMeta
    ingredients: List[Ingredient]
    steps: List[Step]


def validate_recipe(recipe: Recipe) -> List[str]:
    errors: List[str] = []

    if recipe.meta.language != LANGUAGE_ES:
        errors.append(f"language must be {LANGUAGE_ES}")
    if recipe.meta.recipe_type != RECIPE_TYPE_ROBOT_COOKER:
        errors.append(f"recipe_type must be {RECIPE_TYPE_ROBOT_COOKER}")
    if recipe.meta.recipe_no <= 0:
        errors.append("recipe_no must be positive")
    if recipe.meta.servings <= 0:
        errors.append("servings must be positive")
    if not recipe.meta.name.strip():
        errors.append("name must be non-empty")

    if not recipe.ingredients:
        errors.append("ingredients cannot be empty")
    if not recipe.steps:
        errors.append("steps cannot be empty")

    return errors
