#!/usr/bin/env python3
"""Extract paragraphs containing figure references from text.md files.

For each paper, finds references to figures (e.g., "Figure 31.3.1", "Fig. 2.1.3")
and extracts the paragraph containing each reference. Updates the figure_paragraphs
array in papers.json.
"""

import json
import os
import re

BASE = "/home/sdu/obsidian/isscc_accelerator"
DATA_DIR = os.path.join(BASE, "data")
PAPERS_JSON = os.path.join(DATA_DIR, "papers.json")

# Pattern to match figure references like "Figure 31.3.1", "Fig. 2.1.3", "Figure 2.1.1"
# The last number after the second dot is the figure number within the paper
FIGURE_REF_PATTERN = re.compile(
    r'(?:Figure|Fig\.?)\s+(\d+\.\d+\.\d+)',
    re.IGNORECASE
)


def extract_figure_number(paper_id, ref_str):
    """Extract the figure number from a reference string.

    For paper 31.3, "Figure 31.3.2" -> figure_num = 2
    For paper 2.1, "Figure 2.1.5" -> figure_num = 5
    """
    parts = ref_str.split('.')
    if len(parts) == 3:
        # The figure number is the last part
        try:
            return int(parts[2])
        except ValueError:
            return None
    return None


def split_into_paragraphs(text):
    """Split text into paragraphs (separated by blank lines)."""
    # Split on one or more blank lines
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if p.strip()]


def extract_figure_paragraphs(paper_id, text):
    """Extract paragraphs that reference figures for this paper.

    Returns a list of {figure_num, paragraph} dicts.
    """
    paragraphs = split_into_paragraphs(text)
    figure_paragraphs = {}  # figure_num -> paragraph text

    # Build the expected prefix pattern for this paper (e.g., "31.3" or "2.1")
    for para in paragraphs:
        # Find all figure references in this paragraph
        matches = FIGURE_REF_PATTERN.findall(para)
        for ref_str in matches:
            fig_num = extract_figure_number(paper_id, ref_str)
            if fig_num is not None and fig_num not in figure_paragraphs:
                # Clean paragraph: normalize whitespace
                clean_para = re.sub(r'\s+', ' ', para).strip()
                figure_paragraphs[fig_num] = clean_para

    # Convert to sorted list
    result = []
    for fig_num in sorted(figure_paragraphs.keys()):
        result.append({
            "figure_num": fig_num,
            "paragraph": figure_paragraphs[fig_num]
        })

    return result


def main():
    # Load papers.json
    with open(PAPERS_JSON, "r", encoding="utf-8") as f:
        papers = json.load(f)

    total_figures = 0
    papers_with_figs = 0
    papers_without = 0

    for paper in papers:
        pid = paper["id"]
        text_path = os.path.join(DATA_DIR, pid, "text.md")

        if not os.path.exists(text_path):
            print(f"  [{pid}] SKIP - no text.md")
            papers_without += 1
            continue

        with open(text_path, "r", encoding="utf-8") as f:
            text = f.read()

        fig_paras = extract_figure_paragraphs(pid, text)

        if fig_paras:
            paper["figure_paragraphs"] = fig_paras
            fig_nums = [fp["figure_num"] for fp in fig_paras]
            total_figures += len(fig_paras)
            papers_with_figs += 1
            print(f"  [{pid}] OK - {len(fig_paras)} figures: {fig_nums}")
        else:
            paper["figure_paragraphs"] = []
            papers_without += 1
            print(f"  [{pid}] No figure references found")

    # Write back papers.json
    with open(PAPERS_JSON, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total papers: {len(papers)}")
    print(f"  Papers with figure paragraphs: {papers_with_figs}")
    print(f"  Papers without: {papers_without}")
    print(f"  Total figure paragraphs extracted: {total_figures}")


if __name__ == "__main__":
    main()
