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

CURRENT_ESSAY_SAMPLE_PATHS = (
    "02-论文专题/0001-软件架构风格/04-软件架构风格论文范文-改写版.md",
    "02-论文专题/0002-多元异构数据集成/04-多元异构数据集成论文范文-2026H2.md",
    "02-论文专题/0003-测试/03-系统性能测试论文范文-2026H2.md",
    "02-论文专题/0004-微服务/03-微服务论文范文-改写版.md",
    "02-论文专题/0005-云原生/03-云原生论文范文-2026H2.md",
    "02-论文专题/0006-ABSD 基于软件架构设计/03-ABSD 论文范文-改写版.md",
    "02-论文专题/0007-系统安全架构设计/03-系统安全架构设计论文范文-改写版.md",
    "02-论文专题/0008-软件维护/03-软件维护论文范文-2026H2.md",
    "02-论文专题/0009-SOA/03-SOA论文范文-2026H2.md",
    "02-论文专题/0010-大数据架构/03-大数据架构论文范文-改写版.md",
    "02-论文专题/0011-性能优化/03-高并发系统设计论文范文-2026H2.md",
)

CURRENT_KNOWLEDGE_FILES = {
    "01-知识点/README.md": {
        "type": "navigation",
        "status": "reviewed",
        "applicable_exam": "2026-H2",
    },
    "01-知识点/03-Redis 专题-2026H2.md": {
        "type": "knowledge-guide",
        "status": "reviewed",
        "applicable_exam": "2026-H2",
        "scenario_data": "not_applicable",
        "last_verified_at": "required",
        "source_level_contains": "official",
    },
    "01-知识点/03-Redis 专题-核验说明.md": {
        "type": "verification-note",
        "status": "reviewed",
        "applicable_exam": "2026-H2",
    },
    "03-案例专题/01-架构风格与模式.md": {
        "type": "knowledge-guide",
        "status": "reviewed",
        "applicable_exam": "2026-H2",
        "scenario_data": "not_applicable",
        "last_verified_at": "required",
        "source_level_contains": "official",
    },
}

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
    """Parse the small YAML subset used by current docs, including simple lists."""
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
            continue

        if stripped and not line[0].isspace():
            list_key = None

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


def load_metadata(errors: list[str], rel_text: str) -> dict[str, str] | None:
    full = ROOT / rel_text
    if not full.is_file():
        error(errors, rel_text, "file does not exist")
        return None
    try:
        metadata = parse_frontmatter(full.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        error(errors, rel_text, f"cannot read UTF-8 text: {exc}")
        return None
    if metadata is None:
        error(errors, rel_text, "missing or malformed YAML frontmatter")
    return metadata


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
        if relative not in manifest_paths:
            error(errors, rel_text, "yearly verification note missing from current manifest")

        metadata = load_metadata(errors, rel_text)
        if metadata is None:
            continue
        if metadata.get("type") != "verification-note":
            error(errors, rel_text, "type must be verification-note")
        if metadata.get("record_type") != "personal_practice":
            error(errors, rel_text, "record_type must be personal_practice")
        if not metadata.get("question_completeness"):
            error(errors, rel_text, "missing question_completeness")


def validate_current_essay_samples(errors: list[str], manifest_paths: set[Path]) -> None:
    seen_topics: set[str] = set()
    for rel_text in CURRENT_ESSAY_SAMPLE_PATHS:
        relative = Path(rel_text)
        topic = relative.parts[1] if len(relative.parts) > 2 else rel_text
        topic_prefix = topic[:4]

        if topic_prefix in seen_topics:
            error(errors, rel_text, f"multiple current essay samples configured for topic {topic_prefix}")
        seen_topics.add(topic_prefix)

        if relative not in manifest_paths:
            error(errors, rel_text, "current essay sample missing from current manifest")

        metadata = load_metadata(errors, rel_text)
        if metadata is None:
            continue
        if metadata.get("type") != "essay-sample":
            error(errors, rel_text, "type must be essay-sample")
        if metadata.get("status") in {"deprecated", "archived"}:
            error(errors, rel_text, "current essay sample cannot be deprecated or archived")
        if metadata.get("applicable_exam") != "2026-H2":
            error(errors, rel_text, "current essay sample must declare applicable_exam: 2026-H2")
        if metadata.get("scenario_data") != "simulated":
            error(errors, rel_text, "current essay sample must declare scenario_data: simulated")

    expected_topics = {f"{number:04d}" for number in range(1, 12)}
    if seen_topics != expected_topics:
        missing = sorted(expected_topics - seen_topics)
        extra = sorted(seen_topics - expected_topics)
        if missing:
            error(errors, "02-论文专题", f"missing current essay sample configuration for: {', '.join(missing)}")
        if extra:
            error(errors, "02-论文专题", f"unexpected current essay sample topics: {', '.join(extra)}")


def validate_current_knowledge(errors: list[str], manifest_paths: set[Path]) -> None:
    for rel_text, rules in CURRENT_KNOWLEDGE_FILES.items():
        relative = Path(rel_text)
        if relative not in manifest_paths:
            error(errors, rel_text, "current knowledge file missing from current manifest")

        metadata = load_metadata(errors, rel_text)
        if metadata is None:
            continue

        for key in ("type", "status", "applicable_exam", "scenario_data"):
            expected = rules.get(key)
            if expected is not None and metadata.get(key) != expected:
                error(errors, rel_text, f"{key} must be {expected!r}")

        if rules.get("last_verified_at") == "required" and not metadata.get("last_verified_at"):
            error(errors, rel_text, "missing last_verified_at")

        required_source = rules.get("source_level_contains")
        if required_source:
            source_items = {
                item.strip() for item in metadata.get("source_level", "").split(",") if item.strip()
            }
            if required_source not in source_items:
                error(errors, rel_text, f"source_level must include {required_source!r}")


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
                if rel.startswith(("01-知识点/", "02-论文专题/", "03-案例专题/")):
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
    validate_current_essay_samples(errors, manifest_paths)
    validate_current_knowledge(errors, manifest_paths)

    for item in errors:
        print(item)
    print(f"Checked {len(paths)} current documents; {len(errors)} error(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())