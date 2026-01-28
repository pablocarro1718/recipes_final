#!/usr/bin/env python3
"""Load lookup lists from a schema snapshot JSON produced by schema_snapshot.py."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class LookupTables:
    units: List[str]
    accessories: List[str]
    working_modes: List[str]
    categories: List[str]
    labels: List[str]


def _strip_empty(values: Iterable[Optional[str]]) -> List[str]:
    return [value.strip() for value in values if value and value.strip()]


def _extract_column(rows: List[Dict[str, Optional[str]]], header: str) -> List[str]:
    return _strip_empty(row.get(header) for row in rows)


def _unique_sorted(values: Iterable[str]) -> List[str]:
    return sorted(set(values))


def load_snapshot(snapshot_path: Path) -> Dict[str, List[Dict[str, Optional[str]]]]:
    data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    sheets = data.get("sheets", {})
    return {
        name: sheet.get("rows", []) for name, sheet in sheets.items() if isinstance(sheet, dict)
    }


def load_lookups(snapshot_path: Path) -> LookupTables:
    sheets = load_snapshot(snapshot_path)

    units = _extract_column(
        sheets.get("食材单位列表Unit For Ingredients", []), "*单位名称\nUnit Name"
    )
    accessories = _extract_column(
        sheets.get("配件列表Accessories List", []), "*配件名称\nAccessory Name"
    )
    working_modes = _extract_column(
        sheets.get("自动程序Working Mode List", []), "模式名称\nName of Working mode"
    )
    categories = _extract_column(
        sheets.get("分类列表Category List", []), "*分类名称\nCategory Name"
    )
    labels = _extract_column(
        sheets.get("标签列表Label List", []), "*标签名称\nLabel Name"
    )

    return LookupTables(
        units=_unique_sorted(units),
        accessories=_unique_sorted(accessories),
        working_modes=_unique_sorted(working_modes),
        categories=_unique_sorted(categories),
        labels=_unique_sorted(labels),
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Load lookup tables from snapshot JSON.")
    parser.add_argument("snapshot", type=Path, help="Path to schema_snapshot.json")
    args = parser.parse_args()

    lookups = load_lookups(args.snapshot)
    print("Units:", len(lookups.units))
    print("Accessories:", len(lookups.accessories))
    print("Working modes:", len(lookups.working_modes))
    print("Categories:", len(lookups.categories))
    print("Labels:", len(lookups.labels))


if __name__ == "__main__":
    main()
