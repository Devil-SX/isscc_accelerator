#!/usr/bin/env python3
"""Extract page images from ISSCC 2026 session PDFs.

For each paper (identified by X.Y pattern in the PDF), renders pages at 300 DPI
and saves them as images/{paper_id}/page_{n}.png.
"""

import fitz
import os
import re

BASE = "/home/sdu/obsidian/isscc_accelerator"
PDF_DIR = os.path.join(BASE, "pdfs")
IMG_DIR = os.path.join(BASE, "images")

DPI = 300
ZOOM = DPI / 72  # fitz default is 72 DPI


def find_paper_pages(doc):
    """Map paper IDs to their page indices."""
    paper_pages = {}
    for i in range(doc.page_count):
        text = doc[i].get_text()[:500]
        # Match "SESSION X / ... / X.Y"
        m = re.search(r'SESSION\s+\d+\s*/[^/]+/\s*(\d+\.\d+)', text)
        if m:
            pid = m.group(1)
            if pid not in paper_pages:
                paper_pages[pid] = []
            paper_pages[pid].append(i)
        # Also detect figure pages via "Figure X.Y.Z"
        figs = re.findall(r'Figure\s+(\d+\.\d+)\.\d+', text)
        for fig_id in figs:
            if fig_id not in paper_pages:
                paper_pages[fig_id] = []
            if i not in paper_pages[fig_id]:
                paper_pages[fig_id].append(i)
    return paper_pages


def extract_images():
    total_images = 0
    for pdf_name in sorted(os.listdir(PDF_DIR)):
        if not pdf_name.endswith('.pdf'):
            continue
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        doc = fitz.open(pdf_path)
        print(f"Processing {pdf_name} ({doc.page_count} pages)...")

        paper_pages = find_paper_pages(doc)

        for pid in sorted(paper_pages.keys(), key=lambda x: (int(x.split('.')[0]), int(x.split('.')[1]))):
            pages = sorted(paper_pages[pid])
            out_dir = os.path.join(IMG_DIR, pid)
            os.makedirs(out_dir, exist_ok=True)

            for idx, page_num in enumerate(pages, 1):
                page = doc[page_num]
                mat = fitz.Matrix(ZOOM, ZOOM)
                pix = page.get_pixmap(matrix=mat)
                out_path = os.path.join(out_dir, f"page_{idx}.png")
                pix.save(out_path)
                total_images += 1

            print(f"  Paper {pid}: {len(pages)} pages -> {out_dir}")

        doc.close()

    print(f"\nDone! Extracted {total_images} page images total.")


if __name__ == "__main__":
    extract_images()
