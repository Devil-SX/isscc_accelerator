#!/usr/bin/env python3
"""Extract individual figures from ISSCC 2026 session PDFs.

Dual-path extraction:
  Path A (bitmap): Use page.get_images() - works for 40/43 papers
  Path B (vector fallback): Render page at high DPI and crop by caption positions
                            (for 10.3, 10.6, 10.10 which use PDF vector graphics)

Output: images/{paper_id}/fig_{n}.png (unified PNG format)
"""

import fitz
import json
import os
import re

BASE = "/home/sdu/obsidian/isscc_accelerator"
PDF_DIR = os.path.join(BASE, "pdfs")
IMG_DIR = os.path.join(BASE, "images")

MIN_WIDTH = 200
MIN_HEIGHT = 200
VECTOR_DPI = 300
VECTOR_ZOOM = VECTOR_DPI / 72
PAGE_MID_X = 306


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


def count_expected_figures(doc, pages, paper_id):
    """Count expected figures from captions."""
    fig_nums = set()
    for page_num in pages:
        text = doc[page_num].get_text()
        for m in re.finditer(rf'Figure\s+{re.escape(paper_id)}\.(\d+)', text):
            fig_nums.add(int(m.group(1)))
    return len(fig_nums)


def extract_bitmap_figures(doc, fig_pages, out_dir):
    """Path A: Extract bitmap figures sorted by position. Same logic as original extract_figures.py."""
    all_figures = []

    for page_num in fig_pages:
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
            if w < MIN_WIDTH or h < MIN_HEIGHT:
                continue

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

    # Sort by page, then row (y with threshold), then column (x)
    ROW_THRESHOLD = 30
    all_figures.sort(key=lambda f: (f["page"], f["y"], f["x"]))

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

        sorted_figures = []
        for row in rows:
            row.sort(key=lambda f: f["x"])
            sorted_figures.extend(row)
        all_figures = sorted_figures

    # Save as PNG
    os.makedirs(out_dir, exist_ok=True)
    saved = 0
    for idx, fig in enumerate(all_figures, 1):
        out_path = os.path.join(out_dir, f"fig_{idx}.png")
        ext = fig["ext"]
        if ext != "png":
            try:
                pix = fitz.Pixmap(fig["image_data"])
                if pix.alpha:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                pix.save(out_path)
            except Exception:
                with open(out_path.replace(".png", f".{ext}"), "wb") as f:
                    f.write(fig["image_data"])
        else:
            with open(out_path, "wb") as f:
                f.write(fig["image_data"])
        saved += 1
    return saved


def find_caption_positions(page, paper_id):
    """Find Figure X.Y.Z caption positions on a page."""
    captions = []
    blocks = page.get_text("dict")["blocks"]
    pattern = re.compile(rf'Figure\s+{re.escape(paper_id)}\.(\d+)')

    for block in blocks:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            line_text = "".join(span["text"] for span in line["spans"])
            m = pattern.search(line_text)
            if m:
                fig_num = int(m.group(1))
                bbox = line["bbox"]
                captions.append({
                    "fig_num": fig_num,
                    "x0": bbox[0],
                    "y0": bbox[1],
                    "x1": bbox[2],
                    "y1": bbox[3],
                    "text": line_text,
                })
    return captions


def extract_vector_figures(doc, fig_pages, out_dir, paper_id):
    """Path B: Render pages and crop figures by caption positions."""
    all_captions = []

    for page_num in fig_pages:
        page = doc[page_num]
        caps = find_caption_positions(page, paper_id)
        for cap in caps:
            cap["page_num"] = page_num
            cap["page_height"] = page.rect.height
            cap["page_width"] = page.rect.width
            cap_center_x = (cap["x0"] + cap["x1"]) / 2
            cap["column"] = 0 if cap_center_x < PAGE_MID_X else 1
        all_captions.extend(caps)

    if not all_captions:
        return 0

    all_captions.sort(key=lambda c: c["fig_num"])

    # Group by (page, column) for boundary computation
    page_col_caps = {}
    for cap in all_captions:
        key = (cap["page_num"], cap["column"])
        if key not in page_col_caps:
            page_col_caps[key] = []
        page_col_caps[key].append(cap)

    for key in page_col_caps:
        page_col_caps[key].sort(key=lambda c: c["y0"])

    os.makedirs(out_dir, exist_ok=True)
    mat = fitz.Matrix(VECTOR_ZOOM, VECTOR_ZOOM)
    saved = 0
    MARGIN = 18
    COL_GAP = 8

    for cap in all_captions:
        page_num = cap["page_num"]
        page = doc[page_num]
        col = cap["column"]

        # Column boundaries
        if cap["x1"] - cap["x0"] > PAGE_MID_X:
            col_x0, col_x1 = MARGIN, page.rect.width - MARGIN
        elif col == 0:
            col_x0, col_x1 = MARGIN, PAGE_MID_X - COL_GAP / 2
        else:
            col_x0, col_x1 = PAGE_MID_X + COL_GAP / 2, page.rect.width - MARGIN

        # Find top boundary
        key = (page_num, col)
        caps_in_group = page_col_caps.get(key, [])
        idx_in_group = next(
            (i for i, c in enumerate(caps_in_group) if c["fig_num"] == cap["fig_num"]),
            -1
        )

        if idx_in_group > 0:
            top_y = caps_in_group[idx_in_group - 1]["y1"] + 2
        else:
            top_y = MARGIN + 20

        bottom_y = cap["y1"] + 2

        if bottom_y - top_y < 40:
            continue

        clip = fitz.Rect(col_x0, top_y, col_x1, bottom_y)
        pix = page.get_pixmap(matrix=mat, clip=clip)

        out_path = os.path.join(out_dir, f"fig_{cap['fig_num']}.png")
        pix.save(out_path)
        saved += 1

    return saved


def clean_figures(out_dir):
    """Remove old fig_* files."""
    if not os.path.exists(out_dir):
        return
    for fname in os.listdir(out_dir):
        if fname.startswith("fig_"):
            os.remove(os.path.join(out_dir, fname))


def main():
    total_figures = 0
    paper_stats = []

    for pdf_name in sorted(os.listdir(PDF_DIR)):
        if not pdf_name.endswith('.pdf'):
            continue
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        doc = fitz.open(pdf_path)
        print(f"Processing {pdf_name} ({doc.page_count} pages)...")

        paper_pages = find_paper_pages(doc)

        for pid in sorted(paper_pages.keys(),
                          key=lambda x: (int(x.split('.')[0]), int(x.split('.')[1]))):
            pages = sorted(paper_pages[pid])

            # Figure pages = pages with embedded images (original logic)
            fig_pages = [pn for pn in pages if len(doc[pn].get_images(full=True)) > 0]
            expected = count_expected_figures(doc, pages, pid)

            out_dir = os.path.join(IMG_DIR, pid)
            clean_figures(out_dir)

            # Path A: bitmap extraction
            count = extract_bitmap_figures(doc, fig_pages, out_dir)

            # Path B: vector fallback when bitmap gets less than half expected
            if count <= expected // 2 and expected >= 5:
                print(f"    Using vector fallback for {pid} (bitmap: {count}/{expected})")
                clean_figures(out_dir)
                # Use all pages with figure captions for vector extraction
                caption_pages = [pn for pn in pages
                                 if re.search(rf'Figure\s+{re.escape(pid)}\.\d+', doc[pn].get_text())]
                count = extract_vector_figures(doc, caption_pages, out_dir, pid)

            total_figures += count
            status = "OK" if count >= expected - 1 else ("LOW" if count < expected - 2 else "OK")
            paper_stats.append({"id": pid, "extracted": count, "expected": expected, "status": status})
            print(f"  Paper {pid}: {count}/{expected} figures [{status}] -> {out_dir}")

        doc.close()

    # Summary
    print(f"\n{'='*60}")
    print(f"Total: {total_figures} figures from {len(paper_stats)} papers")
    low = [s for s in paper_stats if s["status"] == "LOW"]
    if low:
        print(f"\nPapers with < 6 figures:")
        for s in low:
            print(f"  {s['id']}: {s['extracted']}/{s['expected']}")
    print(f"{'='*60}")

    # Save stats
    stats_path = os.path.join(BASE, "data", "figure_stats.json")
    with open(stats_path, "w") as f:
        json.dump(paper_stats, f, indent=2)
    print(f"Stats saved to {stats_path}")


if __name__ == "__main__":
    main()
