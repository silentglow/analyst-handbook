#!/usr/bin/env python3
"""Extract and inventory the original data_learn DOCX course corpus.

The generated manifest is internal build evidence. It is deliberately not linked
from the learner-facing website.
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
}
W = "{%s}" % NS["w"]


def natural_key(path: Path):
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", path.name)]


def source_number(name: str) -> int | None:
    match = re.match(r"(\d+)_", name)
    return int(match.group(1)) if match else None


def classify(name: str) -> tuple[str, str]:
    number = source_number(name)
    if number is None:
        return "未分类", "待人工确认"
    ranges = [
        (1, 11, "数据分析认知", "system-foundation"),
        (12, 37, "Excel", "excel-reference-and-workshops"),
        (38, 48, "Tableau 与可视化", "visualization-workshops"),
        (49, 70, "SQL", "sql-business-and-interview"),
        (71, 85, "Python", "python-analysis-projects"),
        (86, 156, "机器学习算法", "machine-learning-zero-to-one"),
        (157, 179, "业务分析模型", "business-analysis-methods"),
        (180, 214, "A/B 测试", "ab-testing-deep-course"),
        (215, 231, "游戏氪金案例", "game-monetization-workshop"),
        (232, 245, "异常订单检测案例", "anomaly-detection-workshop"),
        (246, 287, "广告投放案例", "advertising-workshop"),
        (288, 305, "用户流失案例", "ml-pipeline-reference"),
        (306, 318, "数据分析报告", "analysis-report-course"),
    ]
    for start, end, category, track in ranges:
        if start <= number <= end:
            return category, track
    return "未分类", "待人工确认"


TRACK_DESTINATIONS = {
    "system-foundation": ["content/guide.html", "content/ch02.html", "content/ch03.html"],
    "excel-reference-and-workshops": [],
    "visualization-workshops": [],
    "sql-business-and-interview": [],
    "python-analysis-projects": [],
    "machine-learning-zero-to-one": ["topics-src/ml-zero-to-one.html", "topics-src/kmeans.html", "content/ml01.html", "content/ml02.html", "content/ml03.html", "content/ml04.html"],
    "business-analysis-methods": ["topics-src/business-analysis-methods.html", "topics-src/incident-analysis.html", "content/ch03.html", "content/ch04.html", "content/ch07.html", "content/ch08.html", "content/ch09.html", "content/ch10.html", "content/ch11.html"],
    "ab-testing-deep-course": ["content/ch05.html", "content/ch22.html", "topics-src/ab-test-flow.html"],
    "game-monetization-workshop": ["topics-src/game-monetization.html"],
    "anomaly-detection-workshop": ["topics-src/anomaly-orders.html", "story-src/story-26-model-score-trap.html"],
    "advertising-workshop": ["topics-src/advertising-channel-quality.html", "story-src/story-21-advertising-roi.html", "story-src/story-22-multi-touch-attribution.html", "story-src/story-23-organic-vs-paid-traffic.html"],
    "ml-pipeline-reference": ["topics-src/ml-pipeline-patterns.html"],
    "analysis-report-course": ["topics-src/analysis-report.html", "content/ch15.html"],
    "待人工确认": [],
}

INTEGRATED_TRACKS = {
    "system-foundation",
    "machine-learning-zero-to-one",
    "business-analysis-methods",
    "ab-testing-deep-course",
    "game-monetization-workshop",
    "anomaly-detection-workshop",
    "advertising-workshop",
    "ml-pipeline-reference",
    "analysis-report-course",
}

EXCLUDED_TRACKS = {
    "excel-reference-and-workshops",
    "visualization-workshops",
    "sql-business-and-interview",
    "python-analysis-projects",
}

TRACK_DECISIONS = {
    "system-foundation": ("integrated", "数据思维、岗位价值与工作流程已并入系统课程主线，不拆成零散概念页。"),
    "excel-reference-and-workshops": ("excluded_by_user", "用户明确要求 Excel 资料不进入当前学习 Web。"),
    "visualization-workshops": ("excluded_by_user", "用户明确要求 Tableau 资料不进入当前学习 Web。"),
    "sql-business-and-interview": ("excluded_by_user", "用户明确要求 SQL 资料不进入当前学习 Web。"),
    "python-analysis-projects": ("excluded_by_user", "用户明确要求 Python 资料不进入当前学习 Web。"),
    "machine-learning-zero-to-one": ("integrated", "算法原理、参数、评估、调优、失败边界与业务决策已整合为机器学习从 0 到 1 主课及专项页。"),
    "business-analysis-methods": ("integrated", "对比、拆解、漏斗、公式、矩阵、路径、留存、同期群、画像、RFM 与 AARRR 已重组为方法选择主课；Python 实操步骤不进入页面。"),
    "ab-testing-deep-course": ("integrated", "原理、A/A、多变量、错误类型、样本量、实验架构、污染诊断和面试问答已整合为完整专题。"),
    "game-monetization-workshop": ("integrated", "行业机制、经营指标、新手体验、平衡性、偏态、特征工程与两阶段模型已整合为业务工作坊。"),
    "anomaly-detection-workshop": ("integrated", "电商模式、异常定义、数据质量、特征工程、不均衡评估、GBDT、软投票与人机处置已整合。"),
    "advertising-workshop": ("integrated", "营销机制、指标体系、渠道量质、行为、素材、预算、KMeans 分群与增量决策已整合；数据库与 Python 操作已按要求剔除。"),
    "ml-pipeline-reference": ("integrated", "已移除用户流失主线，保留数据质量、编码、ColumnTransformer、分箱、Pipeline、调优和模型解释等通用技术。"),
    "analysis-report-course": ("integrated", "日报、专题与综合报告的类型、结构、标题、目录、正文、结论建议、附录和 0 到 1 流程已整合。"),
    "待人工确认": ("not_migrated", "需要人工确认内容与去向。"),
}


def style_names(zf: zipfile.ZipFile) -> dict[str, str]:
    try:
        root = ET.fromstring(zf.read("word/styles.xml"))
    except KeyError:
        return {}
    result = {}
    for style in root.findall("w:style", NS):
        sid = style.get(W + "styleId", "")
        name = style.find("w:name", NS)
        if sid and name is not None:
            result[sid] = name.get(W + "val", sid)
    return result


def node_text(node: ET.Element) -> str:
    parts = []
    for child in node.iter():
        if child.tag == W + "t" and child.text:
            parts.append(child.text)
        elif child.tag == W + "tab":
            parts.append("\t")
        elif child.tag in {W + "br", W + "cr"}:
            parts.append("\n")
    return "".join(parts).strip()


def extract_docx(path: Path) -> dict:
    with zipfile.ZipFile(path) as zf:
        styles = style_names(zf)
        root = ET.fromstring(zf.read("word/document.xml"))
        body = root.find("w:body", NS)
        paragraphs, headings, tables = [], [], []
        if body is not None:
            for node in list(body):
                if node.tag == W + "p":
                    text = node_text(node)
                    if not text:
                        continue
                    pstyle = node.find("w:pPr/w:pStyle", NS)
                    sid = pstyle.get(W + "val", "") if pstyle is not None else ""
                    style = styles.get(sid, sid)
                    record = {"text": text, "style": style or "Normal"}
                    paragraphs.append(record)
                    if re.search(r"heading|标题|title", style, re.I):
                        headings.append(text)
                elif node.tag == W + "tbl":
                    rows = []
                    for tr in node.findall("w:tr", NS):
                        cells = [node_text(tc) for tc in tr.findall("w:tc", NS)]
                        if any(cells):
                            rows.append(cells)
                    if rows:
                        tables.append(rows)
        media = sorted(n for n in zf.namelist() if n.startswith("word/media/") and not n.endswith("/"))
        full_text = "\n".join(p["text"] for p in paragraphs)
        if not headings:
            headings = [p["text"] for p in paragraphs if len(p["text"]) <= 42][:12]
        return {
            "paragraphs": paragraphs,
            "headings": headings[:40],
            "tables": tables,
            "media": media,
            "text": full_text,
        }


def clean_title(filename: str) -> str:
    title = re.sub(r"\.docx$", "", filename, flags=re.I)
    title = re.sub(r"^\d+_", "", title)
    title = re.sub(r"_原文$", "", title)
    return title


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--artifact-dir", type=Path, default=Path(".artifacts/doc-audit"))
    parser.add_argument("--manifest", type=Path, default=Path("data/content-source-manifest.json"))
    args = parser.parse_args()

    docs = sorted((p for p in args.source.rglob("*.docx") if ".venv" not in p.parts), key=natural_key)
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir = args.artifact_dir / "extracted"
    extracted_dir.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)

    entries, category_counts, status_counts = [], Counter(), Counter()
    total_words = total_media = total_tables = 0
    errors = []
    for index, path in enumerate(docs, 1):
        category, track = classify(path.name)
        status, reason = TRACK_DECISIONS[track]
        try:
            data = extract_docx(path)
        except Exception as exc:  # retain audit evidence instead of aborting the corpus
            errors.append({"source": path.name, "error": str(exc)})
            data = {"paragraphs": [], "headings": [], "tables": [], "media": [], "text": ""}
        text_name = f"{source_number(path.name) or index:03d}.txt"
        (extracted_dir / text_name).write_text(data["text"], encoding="utf-8")
        char_count = len(re.sub(r"\s+", "", data["text"]))
        word_count = len(re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", data["text"]))
        entry = {
            "id": source_number(path.name),
            "source": path.name,
            "title": clean_title(path.name),
            "category": category,
            "track": track,
            "extraction": {
                "text_file": str((extracted_dir / text_name).as_posix()),
                "paragraph_count": len(data["paragraphs"]),
                "table_count": len(data["tables"]),
                "image_count": len(data["media"]),
                "character_count": char_count,
                "token_estimate": word_count,
                "headings": data["headings"],
            },
            "migration": {
                "status": status,
                "destinations": TRACK_DESTINATIONS[track],
                "decision": reason,
                "verified_complete": track in EXCLUDED_TRACKS or track in INTEGRATED_TRACKS,
            },
        }
        entries.append(entry)
        category_counts[category] += 1
        status_counts[status] += 1
        total_words += char_count
        total_media += len(data["media"])
        total_tables += len(data["tables"])

    manifest = {
        "schema_version": 1,
        "source_collection": "data_learn external authoring corpus",
        "learner_visible": False,
        "audit_note": "Internal provenance map. A destination is a planned or partial landing point, not proof of complete migration.",
        "summary": {
            "docx_count": len(entries),
            "character_count": total_words,
            "table_count": total_tables,
            "embedded_image_count": total_media,
            "category_counts": dict(category_counts),
            "migration_status_counts": dict(status_counts),
            "verified_complete_count": sum(bool(e["migration"]["verified_complete"]) for e in entries),
            "in_scope_document_count": sum(e["track"] not in EXCLUDED_TRACKS for e in entries),
            "excluded_document_count": sum(e["track"] in EXCLUDED_TRACKS for e in entries),
            "extraction_error_count": len(errors),
        },
        "documents": entries,
        "errors": errors,
    }
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.artifact_dir / "summary.json").write_text(json.dumps(manifest["summary"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
