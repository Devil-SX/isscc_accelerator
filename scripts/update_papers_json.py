#!/usr/bin/env python3
"""Merge all extracted data into papers.json.

Reads from:
  - data/{paper_id}/figures.json
  - data/{paper_id}/metrics.json

Updates papers.json with:
  - page_images: renamed from images (full page screenshots)
  - figures: array of {num, caption, path}
  - metrics: structured chip metrics object
  - data_path: path to paper data directory
  - markdown_path: updated to new location
"""

import json
import os

BASE = "/home/sdu/obsidian/isscc_accelerator"
DATA_DIR = os.path.join(BASE, "data")
PAPERS_PATH = os.path.join(DATA_DIR, "papers.json")


def main():
    with open(PAPERS_PATH, "r", encoding="utf-8") as f:
        papers = json.load(f)

    updated = 0
    for paper in papers:
        pid = paper["id"]
        paper_dir = os.path.join(DATA_DIR, pid)

        # Rename images -> page_images (preserve original page screenshots)
        if "images" in paper and "page_images" not in paper:
            paper["page_images"] = paper["images"]

        # Load figures.json
        figures_path = os.path.join(paper_dir, "figures.json")
        if os.path.exists(figures_path):
            with open(figures_path, "r", encoding="utf-8") as f:
                figs = json.load(f)
            paper["figures"] = [
                {
                    "num": fig["figure_num"],
                    "caption": fig["caption"],
                    "path": fig["image_path"]
                }
                for fig in figs
                if fig.get("image_path")  # Only include figures with images
            ]
        else:
            paper["figures"] = []

        # Load metrics.json
        metrics_path = os.path.join(paper_dir, "metrics.json")
        if os.path.exists(metrics_path):
            with open(metrics_path, "r", encoding="utf-8") as f:
                metrics = json.load(f)
            paper["metrics"] = metrics

            # Update top-level fields from metrics if they have better data
            if metrics.get("technology") and not paper.get("process_node"):
                paper["process_node"] = metrics["technology"]
            if metrics.get("supply_voltage"):
                paper["supply_voltage"] = metrics["supply_voltage"]
            if metrics.get("frequency_mhz"):
                paper["frequency_mhz"] = metrics["frequency_mhz"]

        # Update paths
        paper["data_path"] = f"data/{pid}/"
        paper["markdown_path"] = f"data/{pid}/text.md"

        updated += 1

    # Write updated papers.json
    with open(PAPERS_PATH, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)

    print(f"Updated {updated} papers in {PAPERS_PATH}")

    # Stats
    with_figures = sum(1 for p in papers if p.get("figures") and len(p["figures"]) > 0)
    with_metrics = sum(1 for p in papers if p.get("metrics"))
    total_figs = sum(len(p.get("figures", [])) for p in papers)

    print(f"\nStats:")
    print(f"  Papers with figures: {with_figures}/{len(papers)}")
    print(f"  Papers with metrics: {with_metrics}/{len(papers)}")
    print(f"  Total figure entries: {total_figs}")


if __name__ == "__main__":
    main()
