#!/usr/bin/env python3
"""Export each ISSCC 2026 paper's text content to Markdown files.

Outputs one .md file per paper to data/markdown/{paper_id}.md.
"""

import fitz
import os
import re

BASE = "/home/sdu/obsidian/isscc_accelerator"
PDF_DIR = os.path.join(BASE, "pdfs")
MD_DIR = os.path.join(BASE, "data", "markdown")


def find_paper_pages(doc):
    """Map paper IDs to their page indices."""
    paper_pages = {}
    for i in range(doc.page_count):
        text = doc[i].get_text()[:500]
        m = re.search(r'SESSION\s+\d+\s*/[^/]+/\s*(\d+\.\d+)', text)
        if m:
            pid = m.group(1)
            if pid not in paper_pages:
                paper_pages[pid] = []
            paper_pages[pid].append(i)
        figs = re.findall(r'Figure\s+(\d+\.\d+)\.\d+', text)
        for fig_id in figs:
            if fig_id not in paper_pages:
                paper_pages[fig_id] = []
            if i not in paper_pages[fig_id]:
                paper_pages[fig_id].append(i)
    return paper_pages


def export_markdown():
    os.makedirs(MD_DIR, exist_ok=True)
    total = 0

    for pdf_name in sorted(os.listdir(PDF_DIR)):
        if not pdf_name.endswith('.pdf'):
            continue
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        doc = fitz.open(pdf_path)
        print(f"Processing {pdf_name}...")

        paper_pages = find_paper_pages(doc)

        for pid in sorted(paper_pages.keys(), key=lambda x: (int(x.split('.')[0]), int(x.split('.')[1]))):
            pages = sorted(paper_pages[pid])
            md_lines = [f"# Paper {pid}\n\n"]

            for page_num in pages:
                page = doc[page_num]
                text = page.get_text()
                md_lines.append(text)
                md_lines.append("\n\n---\n\n")

            md_path = os.path.join(MD_DIR, f"{pid}.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("".join(md_lines))

            total += 1
            print(f"  Paper {pid} -> {md_path}")

        doc.close()

    print(f"\nDone! Exported {total} markdown files.")


if __name__ == "__main__":
    export_markdown()
