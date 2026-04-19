#!/usr/bin/env python3
"""Batch convert MHTML exam files to Markdown documents.

Processes year folders under the current directory, extracts text and images,
filters UI noise, and outputs clean MD files.
"""

import email
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
EXTRACT_SCRIPT = "/Users/edgarlqs/.claude/skills/mhtml-reader/scripts/extract_mhtml.py"

# Year folder → output filename mapping
YEAR_MAP = {
    "2019": "2019年11月-系统架构设计师-案例真题.md",
    "2020": "2020年11月-系统架构设计师-案例真题.md",
    "2021": "2021年11月-系统架构设计师-案例真题.md",
    "2022": "2022年11月-系统架构设计师-案例真题.md",
    "2023": "2023年11月-系统架构设计师-案例真题.md",
    "202405": "2024年5月-系统架构设计师-案例真题.md",
    "202411": "2024年11月-系统架构设计师-案例真题.md",
    "202505": "2025年5月-系统架构设计师-案例真题.md",
}

# Noise patterns
NOISE_PATTERNS = [
    r"^方才coding\n首页\n教程\n软考真题\n软考训练营\n资源\nFrom Zero To Hero.*?(?=\n阅读以下|\n【说明】|\n阅读下列)",
    r"作答区.*",
    r"\n查看答案.*",
    r"\n上一题.*",
    r"\n下一题.*",
    r"\n编辑题目.*",
    r"\n答题卡.*",
    r"\n交卷.*",
    r"\n\d+-\d+\n",
    r"\n1\n2024.*",
    r"\n2025.*",
    r"\n收藏\n试卷信息.*",
    r"\n练习模式\n案例真题.*",
]

# Content start/end markers
START_MARKERS = re.compile(r"(阅读以下|阅读下列|某(软件|公司|企业|互联网|网|电|市|省|国|互|科|教))")
END_MARKERS = re.compile(r"(作答区|查看答案|上一题|下一题|编辑题目|答题卡|交卷)")


def extract_question_number(filename):
    """Extract the question group number and sub-number from filename.

    Examples: 101.mhtml → (1, 01), 201软考真题.mhtml → (2, 01), 软考真题101.mhtml → (1, 01)
    """
    m = re.search(r"(\d)(\d{2})", filename)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def clean_text(text):
    """Remove UI noise from extracted MHTML text."""
    # Find content start
    start_match = START_MARKERS.search(text)
    if start_match:
        text = text[start_match.start():]

    # Find content end
    end_match = END_MARKERS.search(text)
    if end_match:
        text = text[:end_match.start()]

    # Remove specific noise patterns
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.DOTALL)

    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


def extract_images(mhtml_path, output_dir):
    """Extract images from MHTML file. Returns list of (path, type) tuples."""
    os.makedirs(output_dir, exist_ok=True)
    saved = []

    with open(mhtml_path, "rb") as f:
        msg = email.message_from_binary_file(f)

    img_count = 0
    for part in msg.walk():
        ct = part.get_content_type()
        if ct.startswith("image/"):
            data = part.get_payload(decode=True)
            loc = part.get("Content-Location", "")
            if not data:
                continue

            # Classify image
            if "wechat_app" in loc:
                img_type = "qr"
            elif "logo" in loc:
                img_type = "logo"
            elif "rk_images" in loc or "01_papers" in loc:
                img_type = "exam"
            else:
                img_type = "unknown"

            content_hash = hashlib.md5(data).hexdigest()[:12]
            ext = ct.split("/")[-1] if "/" in ct else "png"
            filename = f"img_{img_type}_{content_hash}.{ext}"
            filepath = os.path.join(output_dir, filename)

            if not os.path.exists(filepath):
                with open(filepath, "wb") as out:
                    out.write(data)

            saved.append((filepath, img_type))
            img_count += 1

    return saved


def get_exam_title(text, group_num, sub_num):
    """Extract or generate a title for a question section."""
    lines = text.strip().split("\n")
    # Look for 【说明】section header or first meaningful sentence
    for line in lines:
        if line.startswith("【说明】"):
            return ""  # Will use generic title
        if len(line) > 10 and "阅读" not in line:
            # Take first 30 chars as summary
            summary = line[:40]
            if summary.endswith("。"):
                summary = summary[:-1]
            return summary
    return ""


def process_year_folder(year_folder, output_md):
    """Process a single year folder and generate MD file."""
    folder_path = BASE_DIR / year_folder
    if not folder_path.exists():
        print(f"  SKIP: {year_folder} not found")
        return False

    mhtml_files = sorted(folder_path.glob("*.mhtml"))
    if not mhtml_files:
        print(f"  SKIP: no MHTML files in {year_folder}")
        return False

    print(f"  Processing {year_folder} ({len(mhtml_files)} files)...")

    # Extract text from all files
    file_data = {}  # (group, sub) → text
    image_dir = BASE_DIR / f"{year_folder}_images"
    all_images = {}  # (group, sub) → list of (path, type)

    # Run extract_mhtml.py on the folder
    result = subprocess.run(
        [sys.executable, EXTRACT_SCRIPT, str(folder_path), "--json"],
        capture_output=True, text=True, cwd=str(BASE_DIR)
    )
    if result.returncode != 0:
        print(f"  WARN: extract_mhtml.py stderr: {result.stderr[:200]}")

    try:
        json_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  ERROR: failed to parse JSON output for {year_folder}")
        return False

    for entry in json_data:
        filepath = entry.get("file", "")
        sections = entry.get("sections", [])
        if not sections:
            continue

        fname = os.path.basename(filepath)
        group, sub = extract_question_number(fname)
        if group is None:
            continue

        text = clean_text(sections[0])
        file_data[(group, sub)] = text

        # Extract images
        imgs = extract_images(filepath, str(image_dir))
        all_images[(group, sub)] = imgs

    # Group files by question group
    groups = {}
    for (group, sub), text in file_data.items():
        if group not in groups:
            groups[group] = []
        groups[group].append((sub, text))

    # Sort
    for g in groups:
        groups[g].sort(key=lambda x: x[0])

    # Build MD
    md_parts = []
    # Determine date from year_folder
    date_str = ""
    if year_folder.endswith("05"):
        date_str = year_folder[:4] + "年5月"
    elif year_folder.endswith("11"):
        date_str = year_folder[:4] + "年11月"
    else:
        date_str = year_folder + "年11月"

    md_parts.append(f"# {date_str} 系统架构设计师 案例分析真题")
    md_parts.append("")
    md_parts.append(f"> 来源：方才coding 软考真题")

    # Check for incomplete set
    if year_folder == "2023" and len(groups) < 5:
        md_parts.append(f"> **注意**：本年份真题文件不完整，缺少部分题目。")

    md_parts.append("")
    md_parts.append("---")

    question_num = 1
    group_title_map = {
        1: "软件架构设计与评估",
        2: "系统建模与分析",
        3: "数据库与系统设计",
        4: "Web应用架构",
        5: "嵌入式与实时系统",
    }

    for group_num in sorted(groups.keys()):
        title = group_title_map.get(group_num, "")
        md_parts.append("")
        md_parts.append(f"## 第{group_num}大题：{title}" if title else f"## 第{group_num}大题")
        md_parts.append("")

        for sub_num, text in groups[group_num]:
            md_parts.append(f"### 试题{question_num}")
            md_parts.append("")
            md_parts.append(text)
            md_parts.append("")

            # Add exam images for this sub-question
            imgs = all_images.get((group_num, sub_num), [])
            for img_path, img_type in imgs:
                if img_type == "exam":
                    img_name = os.path.basename(img_path)
                    md_parts.append(f"![考题图](./{year_folder}_images/{img_name})")
                    md_parts.append("")

            md_parts.append("---")
            question_num += 1

    # Appendix (deduplicated)
    md_parts.append("")
    md_parts.append("## 附录：提取的图片")
    md_parts.append("")

    seen_images = set()
    exam_images_found = False
    for (group_num, sub_num), imgs in sorted(all_images.items()):
        for img_path, img_type in imgs:
            img_name = os.path.basename(img_path)
            if img_name in seen_images:
                continue
            seen_images.add(img_name)
            if img_type == "qr":
                md_parts.append(f"- `{img_name}`：微信小程序二维码，已省略")
            elif img_type == "logo":
                md_parts.append(f"- `{img_name}`：站点 Logo，已省略")
            elif img_type == "exam":
                md_parts.append(f"- `{img_name}`：第{group_num}大题第{sub_num}小题架构图/表格图")
                exam_images_found = True

    if not exam_images_found:
        md_parts.append("（所有提取的图片均为二维码或 Logo，已省略。考题架构图如存在，已用 mermaid 或表格在正文中替代。）")

    md_content = "\n".join(md_parts) + "\n"

    # Write MD file
    output_path = BASE_DIR / year_folder / output_md
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"  Wrote: {output_path}")
    return True


def main():
    for year_folder, output_md in YEAR_MAP.items():
        success = process_year_folder(year_folder, output_md)
        if success:
            print(f"  OK: {output_md}")
        else:
            print(f"  FAILED: {output_md}")
        print()

    # Summary
    total = len(YEAR_MAP)
    print(f"\nDone. Processed {total} year folders.")


if __name__ == "__main__":
    main()
