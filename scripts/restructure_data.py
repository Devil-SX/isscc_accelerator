#!/usr/bin/env python3
"""Restructure data directory and extract figure captions.

Creates per-paper directories:
  data/{paper_id}/
    text.md       - paper text (migrated from data/markdown/{id}.md)
    figures.json  - figure captions with image paths

Also cleans captions of ISSCC headers/footers.
"""

import json
import os
import re
import shutil
import glob

BASE = "/home/sdu/obsidian/isscc_accelerator"
DATA_DIR = os.path.join(BASE, "data")
MD_DIR = os.path.join(DATA_DIR, "markdown")
IMG_DIR = os.path.join(BASE, "images")


def clean_caption(text):
    """Remove ISSCC headers, footers, copyright, and page artifacts from caption text."""
    # Remove copyright lines
    text = re.sub(r'979-8-\d+-\d+-\d+/\d+/\$[\d.]+ .*?IEEE', '', text)
    text = re.sub(r'\u00a9\s*\d{4}\s*IEEE.*', '', text)
    # Remove ISSCC session headers
    text = re.sub(r'ISSCC\s+\d{4}\s*/\s*SESSION\s+\d+\s*/[^/]+/\s*\d+\.\d+', '', text)
    text = re.sub(r'ISSCC\s+\d{4}\s*/\s*\w+\s+\d+,\s*\d{4}\s*/\s*[\d:]+\s*[AP]M', '', text)
    # Remove DIGEST OF TECHNICAL PAPERS
    text = re.sub(r'DIGEST\s+OF\s+TECHNICAL\s+PAPERS\s*\u2022?', '', text)
    # Remove page numbers (standalone digits)
    text = re.sub(r'^\s*\d{1,3}\s*\u2022?\s*', '', text)
    text = re.sub(r'\s*\u2022\s*\d{4}\s+IEEE.*', '', text)
    # Remove "20XX IEEE International Solid-State Circuits Conference"
    text = re.sub(r'\d{4}\s+IEEE\s+International\s+Solid-State\s+Circuits\s+Conference', '', text)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_captions_from_text(text, paper_id):
    """Extract Figure X.Y.Z: captions from markdown text.

    Returns list of {figure_id, figure_num, caption}.
    """
    # Match "Figure X.Y.Z: caption text" - caption continues until next Figure or --- or end
    pattern = rf'Figure\s+({re.escape(paper_id)}\.(\d+)):\s*(.+?)(?=\nFigure\s+\d+\.\d+\.\d+|\n---|\Z)'
    matches = re.findall(pattern, text, re.DOTALL)

    captions = []
    seen_nums = set()

    for figure_id, fig_num_str, caption_text in matches:
        fig_num = int(fig_num_str)
        if fig_num in seen_nums:
            continue  # Skip duplicates (some captions appear twice)
        seen_nums.add(fig_num)

        caption = clean_caption(caption_text)
        if not caption:
            continue

        # Truncate overly long captions - ISSCC captions are typically < 200 chars.
        # If caption is too long, it likely captured body text after the actual caption.
        # Find the first sentence ending (period followed by space or end) within
        # a reasonable length, then truncate there.
        if len(caption) > 200:
            # Try to find a good cut point: end of first 1-2 sentences
            cut = -1
            for m in re.finditer(r'\.\s', caption):
                if m.start() >= 40:  # At least 40 chars for a valid caption
                    cut = m.start() + 1
                    if cut >= 80:  # If we have at least 80 chars, that's enough
                        break
            if cut > 0:
                caption = caption[:cut].strip()

        captions.append({
            "figure_id": figure_id,
            "figure_num": fig_num,
            "caption": caption
        })

    # Sort by figure number
    captions.sort(key=lambda c: c["figure_num"])
    return captions


def find_figure_image(paper_id, fig_num):
    """Find the image file path for a figure."""
    fig_dir = os.path.join(IMG_DIR, paper_id)

    # Check for extracted individual figures
    for ext in ["png", "jpg", "jpeg"]:
        path = os.path.join(fig_dir, f"fig_{fig_num}.{ext}")
        if os.path.exists(path):
            return f"images/{paper_id}/fig_{fig_num}.{ext}"

    return None


def restructure_paper(paper_id):
    """Create data/{paper_id}/ directory with text.md and figures.json."""
    paper_dir = os.path.join(DATA_DIR, paper_id)
    os.makedirs(paper_dir, exist_ok=True)

    # Migrate markdown
    src_md = os.path.join(MD_DIR, f"{paper_id}.md")
    dst_md = os.path.join(paper_dir, "text.md")

    if os.path.exists(src_md):
        shutil.copy2(src_md, dst_md)

    # Read text for caption extraction
    text = ""
    if os.path.exists(dst_md):
        with open(dst_md, "r", encoding="utf-8") as f:
            text = f.read()

    # Extract captions
    captions = extract_captions_from_text(text, paper_id)

    # Build figures.json with image paths
    figures = []
    for cap in captions:
        img_path = find_figure_image(paper_id, cap["figure_num"])
        figures.append({
            "figure_id": cap["figure_id"],
            "figure_num": cap["figure_num"],
            "caption": cap["caption"],
            "image_path": img_path
        })

    # Write figures.json
    figures_path = os.path.join(paper_dir, "figures.json")
    with open(figures_path, "w", encoding="utf-8") as f:
        json.dump(figures, f, indent=2, ensure_ascii=False)

    return len(figures)


def main():
    # Load papers.json to get all paper IDs
    papers_path = os.path.join(DATA_DIR, "papers.json")
    with open(papers_path, "r", encoding="utf-8") as f:
        papers = json.load(f)

    total_captions = 0
    paper_ids = [p["id"] for p in papers]

    for pid in sorted(paper_ids,
                      key=lambda x: (int(x.split('.')[0]), int(x.split('.')[1]))):
        count = restructure_paper(pid)
        total_captions += count
        print(f"  Paper {pid}: {count} figure captions")

    print(f"\n{'='*60}")
    print(f"Total: {total_captions} captions from {len(paper_ids)} papers")
    print(f"Data directories created in {DATA_DIR}/")

    # Verify
    missing = []
    for pid in paper_ids:
        figures_path = os.path.join(DATA_DIR, pid, "figures.json")
        if os.path.exists(figures_path):
            with open(figures_path) as f:
                figs = json.load(f)
            missing_imgs = [fig for fig in figs if not fig["image_path"]]
            if missing_imgs:
                missing.append((pid, len(missing_imgs)))

    if missing:
        print(f"\nPapers with missing figure images:")
        for pid, count in missing:
            print(f"  {pid}: {count} figures without images")


if __name__ == "__main__":
    main()
