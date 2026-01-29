#!/usr/bin/env python3
"""Minimal smoke test for lookup loader against the current template."""
from __future__ import annotations

import subprocess
from pathlib import Path

import sys

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.utils.lookups_loader import load_lookups


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    snapshot_path = repo_root / "schema_snapshot.json"
    template_path = repo_root / "Excel template recetas.xlsx"

    subprocess.run(
        ["python", str(repo_root / "scripts/schema_snapshot.py"), str(template_path), "-o", str(snapshot_path)],
        check=True,
    )

    lookups = load_lookups(snapshot_path)
    assert lookups.units, "Expected units to be populated"
    assert lookups.accessories, "Expected accessories to be populated"
    assert lookups.working_modes, "Expected working modes to be populated"

    snapshot_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
