#!/usr/bin/env python3
"""Validate cooking-step rules for working modes and machine parameters."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.utils.recipe_schema import Step

MODE_DESCRIPTION = "描述(Description)"
MODE_WEIGH = "称重(Weigh)"
MODE_ADAPTED = "自适应烹饪(Adapted Cooking)"


@dataclass(frozen=True)
class RuleError:
    message: str


def _has_controls(step: Step) -> bool:
    return any(
        value is not None
        for value in [
            step.temperature,
            step.speed,
            step.direction,
            step.minutes,
            step.seconds,
        ]
    )


def validate_steps(steps: List[Step]) -> List[RuleError]:
    errors: List[RuleError] = []
    for step in steps:
        if step.mode in {MODE_DESCRIPTION, MODE_WEIGH}:
            if not step.description or not step.description.strip():
                errors.append(RuleError(f"step {step.no}: description required for {step.mode}"))
            if _has_controls(step):
                errors.append(RuleError(f"step {step.no}: controls must be empty for {step.mode}"))
        elif step.mode == MODE_ADAPTED:
            if step.description and step.description.strip():
                errors.append(RuleError(f"step {step.no}: description should be empty for {step.mode}"))
            if step.minutes is None and step.seconds is None:
                errors.append(RuleError(f"step {step.no}: time required for {step.mode}"))
            if step.speed is None:
                errors.append(RuleError(f"step {step.no}: speed required for {step.mode}"))
        else:
            errors.append(RuleError(f"step {step.no}: unsupported working mode {step.mode}"))
    return errors
