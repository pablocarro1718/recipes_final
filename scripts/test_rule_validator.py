#!/usr/bin/env python3
"""Minimal test for rule-based step validation."""
from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.utils.recipe_schema import Step
from src.validators.rule_validator import (
    MODE_ADAPTED,
    MODE_DESCRIPTION,
    MODE_WEIGH,
    validate_steps,
)


def main() -> None:
    valid_steps = [
        Step(no=1, mode=MODE_DESCRIPTION, description="Agrega cebolla."),
        Step(no=2, mode=MODE_WEIGH, description="Pesa el agua."),
        Step(no=3, mode=MODE_ADAPTED, temperature=120, speed=2, minutes=5, seconds=0),
    ]
    errors = validate_steps(valid_steps)
    assert not errors, f"Unexpected errors: {errors}"

    invalid_steps = [
        Step(no=1, mode=MODE_DESCRIPTION, description="", temperature=100),
        Step(no=2, mode=MODE_ADAPTED, description="No debería", speed=None, minutes=None),
        Step(no=3, mode="INVALID", description="Paso"),
    ]
    invalid_errors = validate_steps(invalid_steps)
    assert invalid_errors, "Expected rule validation errors"


if __name__ == "__main__":
    main()
