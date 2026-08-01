#!/usr/bin/env python3
"""Validate the six current case topic guides and their authoritative index."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = ROOT / "03-案例专题"

GUIDES = (
    "01-架构风格与模式.md",
    "02-数据库与大数据分布式-2026H2.md",
    "03-Web架构与云原生-2026H2.md",
    "04-软件工程与可靠性-2026H2.md",
    "05-辅助领域-2026H2.md",
    "06-知识图谱-2026H2.md",
)

INDEX = CASE_ROOT / "00-专题当前指南索引.md"
OVERVIEW = CASE_ROOT / "README.md"

HISTORICAL_DEFAULT_PATTERNS = (
    "[数据库、分布式数据与大数据](./02-数据库与大数据分布式.md)",
    "[Web、微服务与云原生](./03-Web架构与云原生.md)",
    "[软件工程与可靠性](./04-软件工程与可靠性.md)",
    "[辅助领域](./05-辅助领域.md)",
    "[知识图谱](./06-知识图谱.md)",
)


def parse_frontmatter(text: str) -> dict[str, str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        return None

    metadata: dict[str, str] = {}
    list_key: str | None = None
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            key = match.group(1)
            value = match.group(2).strip().strip("\"'")
            metadata[key] = value
            list_key = key if value == "" else None
            continue
        stripped = line.strip()
        if list_key and stripped.startswith("-"):
            item = stripped[1:].strip().strip("\"'")
            if item:
                previous = metadata.get(list_key, "")
                metadata[list_key] = f"{previous},{item}".strip(",")
    return metadata


def main() -> int:
    errors: list[str] = []

    for name in GUIDES:
        path = CASE_ROOT / name
        relative = path.relative_to(ROOT).as_posix()
        if not path.is_file():
            errors.append(f"ERROR: {relative}: missing current case guide")
            continue

        text = path.read_text(encoding="utf-8")
        metadata = parse_frontmatter(text)
        if metadata is None:
            errors.append(f"ERROR: {relative}: missing YAML frontmatter")
            continue

        expected = {
            "type": "knowledge-guide",
            "status": "reviewed",
            "applicable_exam": "2026-H2",
            "scenario_data": "not_applicable",
        }
        for key, value in expected.items():
            if metadata.get(key) != value:
                errors.append(f"ERROR: {relative}: {key} must be {value!r}")

        if not metadata.get("last_verified_at"):
            errors.append(f"ERROR: {relative}: missing last_verified_at")

        sources = {
            item.strip()
            for item in metadata.get("source_level", "").split(",")
            if item.strip()
        }
        if "official" not in sources:
            errors.append(f"ERROR: {relative}: source_level must include 'official'")

    if not INDEX.is_file():
        errors.append("ERROR: 03-案例专题/00-专题当前指南索引.md: missing authoritative index")
    else:
        index_text = INDEX.read_text(encoding="utf-8")
        for name in GUIDES:
            if f"./{name}" not in index_text:
                errors.append(f"ERROR: index does not link current guide {name}")

    if not OVERVIEW.is_file():
        errors.append("ERROR: 03-案例专题/README.md: missing overview")
    else:
        overview_text = OVERVIEW.read_text(encoding="utf-8")
        for name in GUIDES:
            if f"./{name}" not in overview_text:
                errors.append(f"ERROR: case overview does not link current guide {name}")
        for pattern in HISTORICAL_DEFAULT_PATTERNS:
            if pattern in overview_text:
                errors.append(f"ERROR: case overview still promotes historical guide: {pattern}")

    for item in errors:
        print(item)
    print(f"Checked {len(GUIDES)} current case guides; {len(errors)} error(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())