#!/usr/bin/env python3
"""Generate/validate papers.json for ISSCC 2026 survey.

This script validates the existing papers.json or can be used as a reference
for the data schema. The actual papers.json was generated with full metadata
from manual reading of all 43 papers.
"""

import json
import os

BASE = "/home/sdu/obsidian/isscc_accelerator"
JSON_PATH = os.path.join(BASE, "data", "papers.json")

def validate():
    with open(JSON_PATH) as f:
        papers = json.load(f)

    print(f"Total papers: {len(papers)}")

    sessions = {}
    for p in papers:
        s = p["session"]
        sessions[s] = sessions.get(s, 0) + 1

    for s in sorted(sessions):
        print(f"  Session {s}: {sessions[s]} papers")

    # Validate schema
    required_fields = [
        "id", "session", "title", "title_zh", "title_annotation",
        "challenges", "ideas", "affiliation", "process_node",
        "energy_efficiency", "application", "innovations", "tags",
        "images", "markdown_path"
    ]

    errors = 0
    for p in papers:
        for field in required_fields:
            if field not in p:
                print(f"  ERROR: Paper {p.get('id','?')} missing field: {field}")
                errors += 1

        # Check images exist
        for img in p.get("images", []):
            img_path = os.path.join(BASE, img)
            if not os.path.exists(img_path):
                print(f"  WARNING: Paper {p['id']} image not found: {img}")

        # Check markdown exists
        md_path = os.path.join(BASE, p.get("markdown_path", ""))
        if not os.path.exists(md_path):
            print(f"  WARNING: Paper {p['id']} markdown not found: {p.get('markdown_path')}")

    if errors == 0:
        print("\nAll papers valid!")
    else:
        print(f"\n{errors} errors found!")

if __name__ == "__main__":
    validate()
