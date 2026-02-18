# ISSCC 2026 Accelerator Survey

Interactive survey website for 43 accelerator/processor papers from ISSCC 2026 (Sessions 2, 10, 18, 30, 31).

**Live site**: https://devil-sx.github.io/isscc_accelerator/site/index.html

## Features

- **Overview table** with sorting and filtering by session, process node, application, and keyword search
- **Detail pages** for each paper with:
  - Title annotation (说文解字) — color-coded breakdown of technical terms
  - Challenge-Idea cards — 3-4 paired problem/solution pairs per paper
  - Figure captions listing
  - Chip metrics — structured display of technology, area, power, efficiency, etc.
- **Responsive layout** for mobile and desktop

## Project Structure

```
site/                  # SPA website (HTML/CSS/JS)
  index.html
  css/style.css
  js/app.js, overview.js, detail.js
data/                  # Structured data
  papers.json          # Main dataset (43 papers with metadata)
  {paper_id}/          # Per-paper directory
    figures.json       # Figure captions
    metrics.json       # Chip metrics
scripts/               # Data processing scripts
tests/                 # Playwright E2E tests
```

## Note on Copyrighted Content

This public repository contains only **derived metadata** (titles, challenges, ideas, metrics, figure captions). Paper full text and figure images are excluded due to IEEE copyright. To use the full version locally:

1. Place source PDFs in `pdfs/`
2. Run `python3 scripts/extract_all_figures.py` to extract figures to `images/`
3. Run `python3 scripts/restructure_data.py` to generate `text.md` files
4. Run `python3 scripts/update_papers_json.py` to rebuild `papers.json` with image paths

The site auto-detects available content and gracefully handles missing images/text.

## Local Development

```bash
python3 -m http.server 8765
# Open http://localhost:8765/site/index.html
```

## Data Processing Scripts

```bash
# Extract figures from PDFs (requires PyMuPDF)
python3 scripts/extract_all_figures.py

# Restructure data directories and extract captions
python3 scripts/restructure_data.py

# Extract chip metrics from paper text
python3 scripts/extract_metrics.py

# Merge all data into papers.json
python3 scripts/update_papers_json.py
```
