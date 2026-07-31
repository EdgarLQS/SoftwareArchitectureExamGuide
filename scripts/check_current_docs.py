#!/usr/bin/env python3
"""Check links, metadata, IDs and score math for current documentation."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "00-项目管理" / "docs-current-manifest.txt"

FRONTMATTER_EXEMPT = {
    "README.md",
    "2026下半年系统架构设计师备考计划.md",
    "00-项目管理/README.md",
}

CASE_VERIFICATION_PATHS = (
    "03-案例专题/000-历年真题/2019年11月-核验说明.md",
    "03-案例专题/000-历年真题/2020年11月-核验说明.md",
    "03-案例专题/000-历年真题/2021年11月-核验说明.md",
    "03-案例专题/000-历年真题/2022年11月-核验说明.md",
    "03-案例专题/000-历年真题/2023年11月-核验说明.md",
    "03-案例专题/000-历年真题/2024年5月-核验说明.md",
    "03-案例专题/000-历年真题/2024年11月-核验说明.md",
    "03-案例专题/000-历年真题/2025年5月-核验说明.md",
    "03-案例专题/000-历年真题/2025年11月-核验说明.md",
)

EXTERNAL_SCHEMES = {
    "http",
    "https",
    "mailto",
    "tel",
    "data",
    "javascript",
    "plugin",
    "sandbox",
}

INVALID_CASE_SCORE_TEXT = {
    "5 道大题，每大题 25 分，总分 75 分",
    "5道大题，每大题25分，总分75分",
}

STALE_EXAM_MARKERS = {
    "适用考试：系统架构设计师（2026 年 5 月）",
    "适用考试：系统架构设计师（2026年5月）",
}

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SCORE_RE = re.compile(
    r"(?P<score>\d+(?:\.\d+)?)\s*/\s*(?P<maximum>\d+(?:\.\d+)?)"
    r"[^\n%]{0,80}?(?P<rate>\d+(?:\.\d+)?)\s*%"
)


def error(errors: list[str], path: str, message: str) -> None:
    errors.append(f"ERROR: {path}: {message}")


def read_manifest() -> list[Path]:
    paths: list[Path] = []
    for raw in MANIFEST.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            paths.append(Path(line))
    return paths


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
    for line in lines[1:end]:
        if not line or line[0].isspace() or line.lstrip().startswith("-"):
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            value = match.group(2).strip().strip("\"'")
            metadata[match.group(1)] = value
    return metadata


def markdown_links(text: str) -> list[str]:
    result: list[str] = []
    in_fence = False
    fence = ""

    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence = marker
            elif marker == fence:
                in_fence = False
                fence = ""
            continue
        if not in_fence:
            result.extend(match.group(1).strip() for match in LINK_RE.finditer(line))
    return result


def local_target(raw: str) -> str | None:
    value = raw.strip()
    if value.startswith("<") and value.endswith(">"):
        value = value[1:-1].strip()

    value = re.sub(r"\s+[\"'][^\"']*[\"']\s*$", "", value).strip()
    if not value or value.startswith("#"):
        return None

    parsed = urlsplit(value)
    if parsed.scheme.lower() in EXTERNAL_SCHEMES or parsed.netloc:
        return None
    return unquote(parsed.path) or None


def validate_topic_directories(errors: list[str]) -> None:
    essay_root = ROOT / "02-论文专题"
    for number in range(1, 12):
        prefix = f"{number:04d}-"
        directories = [
            path for path in essay_root.iterdir()
            if path.is_dir() and path.name.startswith(prefix)
        ]
        if len(directories) != 1:
            error(errors, "02-论文专题", f"expected one directory with prefix {prefix}, found {len(directories)}")
            continue
        topic = directories[0]
        if not (topic / "00-大纲记忆卡.md").is_file():
            error(errors, topic.relative_to(ROOT).as_posix(), "missing 00-大纲记忆卡.md")
        if not list(topic.glob("02-*.md")):
            error(errors, topic.relative_to(ROOT).as_posix(), "missing current 02- writing framework")


def validate_case_verification_notes(errors: list[str], manifest_paths: set[Path]) -> None:
    for rel_text in CASE_VERIFICATION_PATHS:
        relative = Path(rel_text)
        full = ROOT / relative
        if relative not in manifest_paths:
            error(errors, rel_text, "yearly verification note missing from current manifest")
        if not full.is_file():
            error(errors, rel_text, "missing yearly verification note")
            continue

        try:
            metadata = parse_frontmatter(full.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            error(errors, rel_text, f"cannot read verification note: {exc}")
            continue

        if metadata is None:
            error(errors, rel_text, "missing or malformed YAML frontmatter")
            continue
        if metadata.get("type") != "verification-note":
            error(errors, rel_text, "type must be verification-note")
        if metadata.get("record_type") != "personal_practice":
            error(errors, rel_text, "record_type must be personal_practice")
        if not metadata.get("question_completeness"):
            error(errors, rel_text, "missing question_completeness")


def main() -> int:
    if not MANIFEST.is_file():
        print(f"ERROR: missing manifest: {MANIFEST}", file=sys.stderr)
        return 2

    errors: list[str] = []
    ids: dict[str, str] = {}
    paths = read_manifest()
    manifest_paths = set(paths)

    if len(paths) != len(manifest_paths):
        error(errors, MANIFEST.relative_to(ROOT).as_posix(), "duplicate path in manifest")

    for relative in paths:
        full = ROOT / relative
        rel = relative.as_posix()
        if not full.is_file():
            error(errors, rel, "manifest file does not exist")
            continue

        try:
            text = full.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            error(errors, rel, f"cannot read UTF-8 text: {exc}")
            continue

        metadata = parse_frontmatter(text)
        if rel not in FRONTMATTER_EXEMPT:
            if metadata is None:
                error(errors, rel, "missing or malformed YAML frontmatter")
            else:
                for key in ("id", "type", "status", "updated_at"):
                    if not metadata.get(key):
                        error(errors, rel, f"frontmatter missing {key}")

        if metadata:
            doc_id = metadata.get("id")
            if doc_id:
                previous = ids.get(doc_id)
                if previous:
                    error(errors, rel, f"duplicate id {doc_id!r}; already used by {previous}")
                else:
                    ids[doc_id] = rel

            doc_type = metadata.get("type")
            if doc_type in {"essay-sample", "memory-card"}:
                if metadata.get("scenario_data") != "simulated":
                    error(errors, rel, f"{doc_type} must declare scenario_data: simulated")

            if metadata.get("status") not in {"deprecated", "archived"}:
                if rel.startswith(("02-论文专题/", "03-案例专题/")):
                    if not metadata.get("applicable_exam"):
                        error(errors, rel, "current topic file missing applicable_exam")

        for bad_text in INVALID_CASE_SCORE_TEXT:
            if bad_text in text:
                error(errors, rel, f"invalid case scoring text: {bad_text}")

        if not rel.startswith("00-项目管理/"):
            for marker in STALE_EXAM_MARKERS:
                if marker in text:
                    error(errors, rel, f"stale current-exam marker: {marker}")

        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in SCORE_RE.finditer(line):
                score = float(match.group("score"))
                maximum = float(match.group("maximum"))
                rate = float(match.group("rate"))
                if maximum <= 0:
                    error(errors, rel, f"line {line_number}: maximum score must be greater than zero")
                    continue
                expected = round(score / maximum * 100, 1)
                if abs(expected - rate) > 0.11:
                    error(
                        errors,
                        rel,
                        f"line {line_number}: {score:g}/{maximum:g} should be {expected:.1f}%, not {rate:g}%",
                    )

        for raw_link in markdown_links(text):
            target = local_target(raw_link)
            if target is None:
                continue
            resolved = ROOT / target.lstrip("/") if target.startswith("/") else full.parent / target
            if not resolved.exists():
                try:
                    display = resolved.relative_to(ROOT).as_posix()
                except ValueError:
                    display = str(resolved)
                error(errors, rel, f"broken relative link {raw_link!r} -> {display}")

    validate_topic_directories(errors)
    validate_case_verification_notes(errors, manifest_paths)

    for item in errors:
        print(item)
    print(f"Checked {len(paths)} current documents; {len(errors)} error(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())