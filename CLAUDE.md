# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Vanilla JS SPA for browsing 43 ISSCC 2026 accelerator papers (Sessions 2, 10, 18, 30, 31). No build tools, no frameworks — pure HTML/CSS/JS. Data lives in `data/papers.json`.

**Live site**: https://devil-sx.github.io/isscc_accelerator/site/index.html

## Commands

```bash
# Local development server
python3 -m http.server 8765
# Public: http://localhost:8765/site/index.html
# Private: http://localhost:8765/site/index.html?private=1

# Run E2E tests (Playwright, sync API)
python3 tests/e2e.py

# Data extraction pipeline (requires PDFs in pdfs/ and PyMuPDF)
python3 scripts/extract_all_figures.py     # PDF → images/{id}/fig_*.png
python3 scripts/export_markdown.py         # PDF → data/markdown/{id}.md
python3 scripts/restructure_data.py        # Organize into data/{id}/ dirs
python3 scripts/extract_abstracts.py       # text.md → abstract field
python3 scripts/extract_metrics.py         # Regex-based metric extraction
python3 scripts/extract_metrics_llm.py     # LLM-assisted detailed metrics
python3 scripts/extract_bilingual.py       # LLM translate challenges/ideas
python3 scripts/enrich_papers.py           # Add analytical_tags, affiliation_info
python3 scripts/update_papers_json.py      # Merge everything into papers.json
```

## Architecture

### Frontend (site/)

Three JS files loaded in order by `index.html`. Each is an IIFE that registers render functions on `window`:

- **app.js** — Global state (`window.APP`), hash router (`#overview` / `#paper/{id}`), lightbox, private mode detection. Routes call `window.renderOverview()` or `window.renderDetail()`.
- **overview.js** — Registers `window.renderOverview()`. Builds session tabs, filter panel (process/application/innovationType/analyticalTags/search), comparison table (CSS Grid, 9 columns, sortable), and statistics bar (SVG donut charts for academia/industry and country distribution).
- **detail.js** — Registers `window.renderDetail()`. Builds a sidebar (all 43 papers grouped by session) + detail content: abstract, title annotation (说文解字), meta cards (simple or detailed with multi-value conditions), challenge↔idea 3-column layout, innovations, tags. In private mode, builds a 3-mode reader (paired figure+paragraph / fulltext / gallery) instead of the basic image gallery.

All rendering is imperative HTML string concatenation — no virtual DOM.

### Data Flow

```
papers.json ──fetch──→ window.APP.papers
                          ↓
            ┌─────────────┴─────────────┐
     renderOverview()            renderDetail(id)
     (filter/sort/table)         (sections + reader)
```

### Public / Private Mode

Controlled by URL parameter `?private=1` (no code changes needed):

| Mode | URL | What's different |
|------|-----|-----------------|
| Public | `site/index.html` | Figures, metadata, abstract — no full text |
| Private | `site/index.html?private=1` | Full text reader with paired/fulltext/gallery modes |

- GitHub Pages always serves public (no parameter)
- Detection: `app.js` → `detectPrivateMode()` reads `URLSearchParams`
- `detail.js` checks `window.APP.privateMode` to pick reader vs basic gallery

### ISSCC Figure Characteristics

ISSCC papers use a distinctive 2-page layout where each paper has 7 figures:
- Fig 1: Problem overview / motivation
- Fig 2: Overall architecture
- Fig 3-5: Key technique details
- Fig 6: Measurement results / comparison table
- Fig 7: Chip micrograph / summary

All figures are landscape-oriented and information-dense (architecture block diagrams,
comparison tables with many columns, circuit schematics). The reader paired mode uses
a top-figure/bottom-text layout to give figures maximum display width.

### Image Strategy

Two directories: `images/` (full-res, gitignored) and `images_web/` (compressed, gitignored). `app.js` → `detectImageDir()` probes `images_web/` with a HEAD request; falls back to `images/`. `detail.js` → `resolveImagePath()` swaps prefixes at render time.

## Data Schema (papers.json)

Each of the 43 paper objects:

| Field Group | Fields | Notes |
|------------|--------|-------|
| Identity | `id`, `session`, `data_path`, `markdown_path` | id format: `"31.3"` |
| Titles | `title`, `title_zh` | English + Chinese |
| Affiliation | `affiliation`, `authors`, `affiliation_info` | info has: name, name_zh, type (academia/industry/research_inst), country, country_code, logo |
| Abstract | `abstract` | English, extracted from text.md |
| Title Annotation | `title_annotation.segments[]` | Each: text, meaning, color, type |
| Challenges | `challenges[]` | text (zh), text_en, related_idea_idx |
| Ideas | `ideas[]` | text (zh), text_en, type, color |
| Innovations | `innovations[]` | tag, type |
| Tags | `tags`, `analytical_tags` | Original keywords + curated facets |
| Metrics (basic) | `process_node`, `die_area_mm2`, `power_mw`, `energy_efficiency`, `supply_voltage`, `frequency_mhz`, `target_model`, `application` | Top-level convenience fields |
| Metrics (structured) | `metrics` | Same fields in an object + `source_figure`, `sram_kb`, `throughput` |
| Metrics (detailed) | `metrics_detailed` | Multi-value with conditions: `{power: {values: [{value, unit, condition}]}}` |
| Figures | `figures[]` | num, caption, path |
| Reader data | `figure_paragraphs[]` | figure_path, figure_label, paragraph |
| Page images | `page_images[]` | Full page screenshot paths |

## Conventions

- **ES5 only** in all frontend JS: no arrow functions, no `let`/`const`, no template literals, no destructuring
- CSS custom properties in `:root` of `style.css` — dark academic theme
- Innovation type colors: `hw-arch=#e74c3c` (red), `hw-circuit=#e67e22` (orange), `sw=#2ecc71` (green), `codesign=#9b59b6` (purple), `system=#3498db` (blue)
- Logos in `assets/logos/{kebab-case}.{svg|png}` — 26 institutions
- Bilingual pattern: Chinese primary field (`text`), English secondary (`text_en`)
- Copyrighted content (PDFs, full text, images) is gitignored — public repo has metadata only
