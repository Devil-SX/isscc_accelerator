#!/usr/bin/env python3
"""Extract individual figures from ISSCC 2026 session PDFs.

Each paper has ~7 figures arranged in a 2-column grid across 2 figure pages.
This script extracts each figure as a separate image file:
  images/{paper_id}/fig_{n}.png  (n = 1,2,3,...)

Images are sorted by position (top-to-bottom, left-to-right) to match
the standard ISSCC figure numbering convention.
"""

import fitz
import os
import re

BASE = "/home/sdu/obsidian/isscc_accelerator"
PDF_DIR = os.path.join(BASE, "pdfs")
IMG_DIR = os.path.join(BASE, "images")

# Minimum image dimensions to filter out tiny decorative images
MIN_WIDTH = 200
MIN_HEIGHT = 200


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


def extract_figures_from_pages(doc, pages, out_dir):
    """Extract individual figures from figure pages, sorted by position."""
    all_figures = []

    for page_num in pages:
        page = doc[page_num]
        images = page.get_images(full=True)

        for img_info in images:
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
            except Exception:
                continue

            w = base_image["width"]
            h = base_image["height"]

            # Skip tiny images (logos, icons, etc.)
            if w < MIN_WIDTH or h < MIN_HEIGHT:
                continue

            # Get position on page
            rects = page.get_image_rects(xref)
            if not rects:
                continue

            rect = rects[0]
            all_figures.append({
                "xref": xref,
                "image_data": base_image["image"],
                "ext": base_image["ext"],
                "width": w,
                "height": h,
                "page": page_num,
                "y": rect.y0,
                "x": rect.x0,
            })

    # Sort by page, then row (y), then column (x)
    # Use a threshold for "same row" grouping (within 30 points)
    ROW_THRESHOLD = 30
    all_figures.sort(key=lambda f: (f["page"], f["y"], f["x"]))

    # Group into rows and sort within each row
    if all_figures:
        rows = []
        current_row = [all_figures[0]]
        current_page = all_figures[0]["page"]
        current_y = all_figures[0]["y"]

        for fig in all_figures[1:]:
            if fig["page"] == current_page and abs(fig["y"] - current_y) < ROW_THRESHOLD:
                current_row.append(fig)
            else:
                rows.append(current_row)
                current_row = [fig]
                current_page = fig["page"]
                current_y = fig["y"]
        rows.append(current_row)

        # Sort each row by x position (left to right)
        sorted_figures = []
        for row in rows:
            row.sort(key=lambda f: f["x"])
            sorted_figures.extend(row)

        all_figures = sorted_figures

    # Save figures
    os.makedirs(out_dir, exist_ok=True)
    saved = 0
    for idx, fig in enumerate(all_figures, 1):
        ext = fig["ext"]
        if ext == "jpeg":
            ext = "jpg"
        out_path = os.path.join(out_dir, f"fig_{idx}.{ext}")
        with open(out_path, "wb") as f:
            f.write(fig["image_data"])
        saved += 1

    return saved


def main():
    total_figures = 0

    for pdf_name in sorted(os.listdir(PDF_DIR)):
        if not pdf_name.endswith('.pdf'):
            continue
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        doc = fitz.open(pdf_path)
        print(f"Processing {pdf_name}...")

        paper_pages = find_paper_pages(doc)

        for pid in sorted(paper_pages.keys(),
                          key=lambda x: (int(x.split('.')[0]), int(x.split('.')[1]))):
            pages = sorted(paper_pages[pid])

            # Figure pages are pages with embedded images (typically pages 2,3 of each paper)
            fig_pages = []
            for pn in pages:
                if len(doc[pn].get_images(full=True)) > 0:
                    fig_pages.append(pn)

            if not fig_pages:
                print(f"  Paper {pid}: no figure pages found")
                continue

            out_dir = os.path.join(IMG_DIR, pid)
            count = extract_figures_from_pages(doc, fig_pages, out_dir)
            total_figures += count
            print(f"  Paper {pid}: {count} figures extracted -> {out_dir}")

        doc.close()

    print(f"\nDone! Extracted {total_figures} individual figures total.")


if __name__ == "__main__":
    main()
