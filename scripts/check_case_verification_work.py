#!/usr/bin/env python3
"""Validate historical case verification ledgers, notes and remediation plans."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "03-案例专题" / "000-历年真题"

NOTES = tuple(f"{year}-核验说明.md" for year in (
    "2019年11月",
    "2020年11月",
    "2021年11月",
    "2022年11月",
    "2023年11月",
    "2024年5月",
    "2024年11月",
    "2025年5月",
    "2025年11月",
))

REQUIRED = (
    "00-核验工作入口.md",
    "README.md",
    "评分模板.md",
    "案例成绩与资料核验总账.md",
    "答案来源与选答记录总账.md",
    "2025年5月-图片题面文本化计划.md",
    "2023年11月-第3大题补录计划.md",
    *NOTES,
)


def parse_frontmatter(text: str) -> dict[str, str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        return None

    metadata: dict[str, str] = {}
    list_key: str | None = None
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            key = match.group(1)
            value = match.group(2).strip().strip("\"'")
            metadata[key] = value
            list_key = key if not value else None
            continue
        stripped = line.strip()
        if list_key and stripped.startswith("-"):
            item = stripped[1:].strip().strip("\"'")
            if item:
                metadata[list_key] = f"{metadata.get(list_key, '')},{item}".strip(",")
    return metadata


def main() -> int:
    errors: list[str] = []

    for name in REQUIRED:
        path = BASE / name
        relative = path.relative_to(ROOT).as_posix()
        if not path.is_file():
            errors.append(f"ERROR: {relative}: missing required verification file")
            continue

        metadata = parse_frontmatter(path.read_text(encoding="utf-8"))
        if metadata is None:
            errors.append(f"ERROR: {relative}: missing YAML frontmatter")
            continue

        for key in ("id", "type", "status", "applicable_exam", "updated_at"):
            if not metadata.get(key):
                errors.append(f"ERROR: {relative}: missing {key}")

    for name in NOTES:
        path = BASE / name
        if not path.is_file():
            continue
        metadata = parse_frontmatter(path.read_text(encoding="utf-8")) or {}
        relative = path.relative_to(ROOT).as_posix()
        if metadata.get("type") != "verification-note":
            errors.append(f"ERROR: {relative}: type must be verification-note")
        if metadata.get("record_type") != "personal_practice":
            errors.append(f"ERROR: {relative}: record_type must be personal_practice")
        if not metadata.get("question_completeness"):
            errors.append(f"ERROR: {relative}: missing question_completeness")

    plans = (
        BASE / "2025年5月-图片题面文本化计划.md",
        BASE / "2023年11月-第3大题补录计划.md",
    )
    for path in plans:
        if not path.is_file():
            continue
        metadata = parse_frontmatter(path.read_text(encoding="utf-8")) or {}
        relative = path.relative_to(ROOT).as_posix()
        if metadata.get("type") != "remediation-plan":
            errors.append(f"ERROR: {relative}: type must be remediation-plan")
        if metadata.get("status") in {"verified", "complete", "completed"}:
            errors.append(f"ERROR: {relative}: unresolved plan cannot be marked complete")

    provenance = BASE / "答案来源与选答记录总账.md"
    if provenance.is_file():
        text = provenance.read_text(encoding="utf-8")
        for session in ("2019 下", "2020 下", "2021 下", "2022 下", "2023 下", "2024 上", "2024 下", "2025 上", "2025 下"):
            if session not in text:
                errors.append(f"ERROR: provenance ledger missing session {session}")
        if "selected_questions" not in text:
            errors.append("ERROR: provenance ledger missing selected_questions field guidance")

    entry = BASE / "00-核验工作入口.md"
    if entry.is_file():
        entry_text = entry.read_text(encoding="utf-8")
        for name in ("案例成绩与资料核验总账.md", "答案来源与选答记录总账.md", "2025年5月-图片题面文本化计划.md", "2023年11月-第3大题补录计划.md"):
            if f"./{name}" not in entry_text:
                errors.append(f"ERROR: verification entry does not link {name}")

    for item in errors:
        print(item)
    print(f"Checked {len(REQUIRED)} historical verification files; {len(errors)} error(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())