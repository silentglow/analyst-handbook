#!/usr/bin/env python3
"""Report how much of the DOCX corpus has a verified Web destination."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


def html_text_size(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return len(re.sub(r"\s+", "", text))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path, nargs="?", default=Path("data/content-source-manifest.json"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path(".artifacts/doc-audit/coverage.json"))
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in manifest["documents"]:
        grouped[item["category"]].append(item)

    excluded_status = "excluded_by_user"
    in_scope_documents = [
        item for item in manifest["documents"]
        if item["migration"]["status"] != excluded_status
    ]
    excluded_documents = [
        item for item in manifest["documents"]
        if item["migration"]["status"] == excluded_status
    ]

    rows = []
    for category, docs in grouped.items():
        destinations = []
        for doc in docs:
            for dest in doc["migration"]["destinations"]:
                if dest not in destinations:
                    destinations.append(dest)
        existing = [dest for dest in destinations if not dest.startswith("planned:") and (args.root / dest).exists()]
        planned = [dest.removeprefix("planned:") for dest in destinations if dest.startswith("planned:")]
        excluded = all(doc["migration"]["status"] == excluded_status for doc in docs)
        rows.append({
            "category": category,
            "source_documents": len(docs),
            "source_characters": sum(doc["extraction"]["character_count"] for doc in docs),
            "source_images": sum(doc["extraction"]["image_count"] for doc in docs),
            "existing_destinations": existing,
            "existing_destination_characters_upper_bound": sum(html_text_size(args.root / dest) for dest in existing),
            "planned_destinations": planned,
            "verified_complete_documents": sum(bool(doc["migration"]["verified_complete"]) for doc in docs),
            "status": "excluded_by_user" if excluded else ("verified" if all(doc["migration"]["verified_complete"] for doc in docs) else "incomplete"),
        })

    result = {
        "rule": "A file is complete only after its concepts and screenshot-contained knowledge have been editorially reviewed in its Web destination.",
        "summary": {
            "source_documents": len(manifest["documents"]),
            "in_scope_documents": len(in_scope_documents),
            "excluded_documents": len(excluded_documents),
            "verified_complete_documents": sum(bool(d["migration"]["verified_complete"]) for d in in_scope_documents),
            "incomplete_documents": sum(not d["migration"]["verified_complete"] for d in in_scope_documents),
        },
        "categories": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["summary"]["incomplete_documents"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
