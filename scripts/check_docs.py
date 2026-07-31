#!/usr/bin/env python3
"""Validate the repository's current documentation set.

The checker intentionally uses only the Python standard library. It validates the
files listed in 00-项目管理/docs-current-manifest.txt rather than failing on all
historical material at once.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "00-项目管理" / "docs-current-manifest.txt"

FRONTMATTER_EXEMPT = {
    "README.md",
    "2026下半年系统架构设计师备考计划.md",
    "00-项目管理/README.md",
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

BAD_SCORE_SENTENCES = (
    "5 道大题，每大题 25 分，总分 75 分",
    "5道大题，每大题25分，总分75分",
)

OLD_CURRENT_MARKERS = (
    "适用考试：系统架构设计师（2026 年 5 月）",
    "适用考试：系统架构设计师（2026年5月）",
)

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SCORE_RE = re.compile(
    r"(?P<score>\d+(?:\.\d+)?)\s*/\s*(?P<maximum>\d+(?:\.\d+)?)"
    r"[^\n%]{0,80}?(?P<rate>\d+(?:\.\d+)?)\s*%"
)


@dataclass(frozen=True)
class Finding:
    level: str
    path: str
    message: str


def read_manifest() -> list[Path]:
    if not MANIFEST.is_file():
        raise FileNotFoundError(f"manifest not found: {MANIFEST}")

    paths: list[Path] = []
    for raw in MANIFEST.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        paths.append(Path(line))
    return paths


def parse_frontmatter(text: str) -> dict[str, str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None

    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        if not line or line[0].isspace() or line.lstrip().startswith("-"):
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            metadata[match.group(1)] = match.group(2).strip().strip('"\'')
    return metadata


def iter_markdown_links(text: str) -> list[str]:
    links: list[str] = []
    in_fence = False
    fence_marker = ""

    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            continue
        if in_fence:
            continue
        links.extend(match.group(1).strip() for match in LINK_RE.finditer(line))
    return links


def clean_link_target(target: str) -> str | None:
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()

    # Remove an optional Markdown title: path "title".
    target = re.sub(r"\s+[\"'][^\"']*[\"']\s*$", "", target).strip()
    if not target or target.startswith("#"):
        return None

    parsed = urlsplit(target)
    if parsed.scheme.lower() in EXTERNAL_SCHEMES or parsed.netloc:
        return None

    path = unquote(parsed.path)
    return path or None


def resolve_link(source: Path, target: str) -> Path:
    if target.startswith("/"):
        return ROOT / target.lstrip("/")
    return source.parent / target


def validate_score_math(rel_path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in SCORE_RE.finditer(line):
            score = float(match.group("score"))
            maximum = float(match.group("maximum"))
            rate = float(match.group("rate"))
            if maximum <= 0:
                findings.append(
                    Finding("ERROR", rel_path.as_posix(), f"line {line_no}: maximum score must be > 0")
                )
                continue
            expected = round(score / maximum * 100, 1)
            if abs(expected - rate) > 0.11:
                findings.append(
                    Finding(
                        "ERROR",
                        rel_path.as_posix(),
                        f"line {line_no}: {score:g}/{maximum:g} should be {expected:.1f}%, not {rate:g}%",
                    )
                )
    return findings


def validate_topic_structure(findings: list[Finding]) -> None:
    essay_root = ROOT / "02-论文专题"
    for number in range(1, 12):
        prefix = f"{number:04d}-"
        matches = sorted(path for path in essay_root.iterdir() if path.is_dir() and path.name.startswith(prefix))
        if len(matches) != 1:
            findings.append(
                Finding(
                    "ERROR",
                    "02-论文专题",
                    f"expected exactly one topic directory with prefix {prefix}, found {len(matches)}",
                )
            )
            continue

        topic = matches[0]
        memory_cards = list(topic.glob("00-大纲记忆卡.md"))
        frameworks = list(topic.glob("02-*.md"))
        if not memory_cards:
            findings.append(Finding("ERROR", topic.relative_to(ROOT).as_posix(), "missing 00-大纲记忆卡.md"))
        if not frameworks:
            findings.append(Finding("ERROR", topic.relative_to(ROOT).as_posix(), "missing current 02- writing framework"))


def main() -> int:
    findings: list[Finding] = []
    ids: dict[str, str] = {}

    try:
        manifest_paths = read_manifest()
    except (OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if len(manifest_paths) != len(set(manifest_paths)):
        findings.append(Finding("ERROR", MANIFEST.relative_to(ROOT).as_posix(), "duplicate path in manifest"))

    for rel_path in manifest_paths:
        full_path = ROOT / rel_path
        rel = rel_path.as_posix()
        if not full_path.exists():
            findings.append(Finding("ERROR", rel, "manifest entry does not exist"))
            continue
        if not full_path.is_file():
            findings.append(Finding("ERROR", rel, "manifest entry is not a file"))
            continue

        try:
            text = full_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            findings.append(Finding("ERROR", rel, f"cannot read UTF-8 text: {exc}"))
            continue

        metadata = parse_frontmatter(text)
        if rel not in FRONTMATTER_EXEMPT:
            if metadata is None:
                findings.append(Finding("ERROR", rel, "missing or malformed YAML frontmatter"))
            else:
                for key in ("id", "type", "status", "updated_at"):
                    if not metadata.get(key):
                        findings.append(Finding("ERROR", rel, f"frontmatter missing {key}"))

        if metadata:
            doc_id = metadata.get("id")
            if doc_id:
                previous = ids.get(doc_id)
                if previous:
                    findings.append(Finding("ERROR", rel, f"duplicate id {doc_id!r}; already used by {previous}"))
                else:
                    ids[doc_id] = rel

            doc_type = metadata.get("type")
            if doc_type in {"essay-sample", "memory-card"} and metadata.get("scenario_data") != "simulated":
                findings.append(
                    Finding("ERROR", rel, f"{doc_type} must declare scenario_data: simulated")
                )
            if metadata.get("status") not in {"deprecated", "archived"}:
                exam = metadata.get("applicable_exam")
                if rel.startswith(("02-论文专题/", "03-案例专题/")) and not exam:
                    findings.append(Finding("ERROR", rel, "current topic document missing applicable_exam"))

        for bad in BAD_SCORE_SENTENCES:
            if bad in text:
                findings.append(Finding("ERROR", rel, f"contains invalid case score sentence: {bad}"))

        if not rel.startswith("00-项目管理/"):
            for marker in OLD_CURRENT_MARKERS:
                if marker in text:
                    findings.append(Finding("ERROR", rel, f"contains stale current-exam marker: {marker}"))

        findings.extend(validate_score_math(rel_path, text))

        for raw_target in iter_markdown_links(text):
            target = clean_link_target(raw_target)
            if target is None:
                continue
            resolved = resolve_link(full_path, target)
            if not resolved.exists():
                findings.append(
                    Finding(
                        "ERROR",
                        rel,
                        f"broken relative link {raw_target!r} -> {resolved.relative_to(ROOT) if resolved.is_relative_to(ROOT) else resolved}",
                    )
                )

    validate_topic_structure(findings)

    errors = [finding for finding in findings if finding.level == "ERROR"]
    warnings = [finding for finding in findings if finding.level == "WARNING"]

    for finding in findings:
        print(f"{finding.level}: {finding.path}: {finding.message}")

    print(
        f"Checked {len(manifest_paths)} current documents; "
        f"{len(errors)} error(s), {len(warnings)} warning(s)."
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
