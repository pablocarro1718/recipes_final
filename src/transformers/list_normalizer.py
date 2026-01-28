#!/usr/bin/env python3
"""Normalize recipe fields against lookup tables."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from src.utils.lookups_loader import LookupTables
from src.utils.recipe_schema import Ingredient, Recipe, Step

ALLOWED_MODES = {
    "描述(Description)",
    "称重(Weigh)",
    "自适应烹饪(Adapted Cooking)",
}


@dataclass(frozen=True)
class NormalizationError:
    message: str


def _validate_membership(value: str, allowed: Iterable[str], field: str) -> List[NormalizationError]:
    if value not in allowed:
        return [NormalizationError(f"{field} value '{value}' is not in lookup list")]
    return []


def normalize_ingredients(
    ingredients: List[Ingredient], lookups: LookupTables
) -> List[NormalizationError]:
    errors: List[NormalizationError] = []
    for ingredient in ingredients:
        errors.extend(_validate_membership(ingredient.unit, lookups.units, "unit"))
    return errors


def normalize_steps(steps: List[Step], lookups: LookupTables) -> List[NormalizationError]:
    errors: List[NormalizationError] = []
    allowed_modes = set(lookups.working_modes) & ALLOWED_MODES
    for step in steps:
        errors.extend(_validate_membership(step.mode, allowed_modes, "working_mode"))
    return errors


def normalize_accessories(accessories: List[str], lookups: LookupTables) -> List[NormalizationError]:
    errors: List[NormalizationError] = []
    for accessory in accessories:
        errors.extend(_validate_membership(accessory, lookups.accessories, "accessory"))
    return errors


def normalize_recipe(recipe: Recipe, lookups: LookupTables, accessories: List[str]) -> List[NormalizationError]:
    errors: List[NormalizationError] = []
    errors.extend(normalize_ingredients(recipe.ingredients, lookups))
    errors.extend(normalize_steps(recipe.steps, lookups))
    errors.extend(normalize_accessories(accessories, lookups))
    return errors
