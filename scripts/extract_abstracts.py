#!/usr/bin/env python3
"""Extract abstracts from data/{id}/text.md files and update papers.json.

The ISSCC abstract format: Each text.md has a line containing only "Abstract"
near the end. The abstract text is the paragraph just before this label.
"""

import json
import os
import re

BASE = "/home/sdu/obsidian/isscc_accelerator"
DATA_DIR = os.path.join(BASE, "data")
PAPERS_JSON = os.path.join(DATA_DIR, "papers.json")


def extract_abstract(text_path):
    """Extract abstract from a text.md file.

    Strategy:
    1. Find the "Abstract" label line (regex ^\\s*Abstract\\s*$)
    2. Walk backwards from that line, skip blank lines
    3. Collect text lines until hitting a blank line or start of author/title block
    4. Join and return the paragraph
    """
    if not os.path.exists(text_path):
        return None

    with open(text_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find the "Abstract" label line
    abstract_idx = None
    for i, line in enumerate(lines):
        if re.match(r'^\s*Abstract\s*$', line):
            abstract_idx = i
            break

    if abstract_idx is None:
        return None

    # Walk backwards from the Abstract line, skip blank lines first
    idx = abstract_idx - 1
    while idx >= 0 and lines[idx].strip() == '':
        idx -= 1

    if idx < 0:
        return None

    # Collect paragraph lines going backwards until blank line
    paragraph_lines = []
    while idx >= 0:
        line = lines[idx].strip()
        if line == '':
            break
        paragraph_lines.append(line)
        idx -= 1

    if not paragraph_lines:
        return None

    # Reverse to get correct order and join
    paragraph_lines.reverse()
    abstract = ' '.join(paragraph_lines)

    # Clean up: normalize whitespace
    abstract = re.sub(r'\s+', ' ', abstract).strip()

    return abstract


def main():
    # Load papers.json
    with open(PAPERS_JSON, "r", encoding="utf-8") as f:
        papers = json.load(f)

    success = 0
    failed = 0
    skipped = 0

    for paper in papers:
        pid = paper["id"]
        text_path = os.path.join(DATA_DIR, pid, "text.md")

        if not os.path.exists(text_path):
            print(f"  [{pid}] SKIP - no text.md found")
            skipped += 1
            continue

        abstract = extract_abstract(text_path)

        if abstract:
            paper["abstract"] = abstract
            # Show first 80 chars
            preview = abstract[:80] + "..." if len(abstract) > 80 else abstract
            print(f"  [{pid}] OK - {len(abstract)} chars: {preview}")
            success += 1
        else:
            print(f"  [{pid}] FAIL - could not extract abstract")
            failed += 1

    # Write back papers.json
    with open(PAPERS_JSON, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total papers: {len(papers)}")
    print(f"  Abstracts extracted: {success}")
    print(f"  Failed: {failed}")
    print(f"  Skipped (no text.md): {skipped}")


if __name__ == "__main__":
    main()
