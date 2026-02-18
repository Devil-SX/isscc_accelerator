#!/usr/bin/env python3
"""Extract chip metrics from paper text and existing papers.json data.

Reads from:
  - data/{paper_id}/text.md (paper body text)
  - data/papers.json (existing metadata)

Writes to:
  - data/{paper_id}/metrics.json
"""

import json
import os
import re

BASE = "/home/sdu/obsidian/isscc_accelerator"
DATA_DIR = os.path.join(BASE, "data")


def extract_from_text(text):
    """Extract chip metrics from paper body text using regex patterns."""
    metrics = {}

    # Technology / Process node
    tech_patterns = [
        r'(\d+\s*nm)\s+CMOS',
        r'fabricated\s+in\s+(\d+\s*nm)',
        r'(\d+\s*nm)\s+(?:UTBB-)?FDSOI',
        r'(\d+\s*nm)\s+FinFET',
        r'(\d+\s*nm)\s+process',
        r'(\d+\s*nm)\s+technology',
        r'TSMC\s+(\d+\s*nm)',
    ]
    for pat in tech_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            metrics["technology"] = m.group(1).replace(' ', '') + " CMOS"
            break

    # Die area
    area_patterns = [
        r'die\s+area\s+(?:of\s+)?(\d+\.?\d*)\s*mm\s*[²2]',
        r'(\d+\.?\d*)\s*mm\s*[²2]\s+die\s+area',
        r'(\d+\.?\d*)\s*mm\s*[²2]\s+(?:core|chip|total)\s+area',
        r'core\s+area\s+(?:of\s+)?(\d+\.?\d*)\s*mm\s*[²2]',
        r'chip\s+area\s+(?:of\s+|is\s+)?(\d+\.?\d*)\s*mm\s*[²2]',
        r'occupies\s+(\d+\.?\d*)\s*mm\s*[²2]',
        r'(\d+\.?\d*)\s*[×x]\s*(\d+\.?\d*)\s*mm\s*[²2]?\s*(?:die|chip|core)',
    ]
    for pat in area_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            if m.lastindex == 2:
                # WxH format
                metrics["die_area_mm2"] = str(round(float(m.group(1)) * float(m.group(2)), 2))
            else:
                metrics["die_area_mm2"] = m.group(1)
            break

    # Supply voltage
    volt_patterns = [
        r'(\d+\.?\d*)\s*V\s+supply',
        r'supply\s+(?:voltage\s+)?(?:of\s+)?(\d+\.?\d*)\s*V',
        r'VDD\s*=\s*(\d+\.?\d*)\s*V',
        r'(\d+\.?\d*)\s*V\s+VDD',
        r'operating\s+at\s+(\d+\.?\d*)\s*V',
    ]
    for pat in volt_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            v = float(m.group(1))
            if 0.3 <= v <= 5.0:  # Reasonable supply voltage range
                metrics["supply_voltage"] = f"{v}V"
            break

    # SRAM size
    sram_patterns = [
        r'(\d+\.?\d*)\s*[KkMm]B\s+(?:of\s+)?(?:on-chip\s+)?SRAM',
        r'SRAM\s+(?:of\s+)?(\d+\.?\d*)\s*[KkMm]B',
        r'(\d+\.?\d*)\s*[KkMm]B\s+(?:on-chip\s+)?memory',
    ]
    for pat in sram_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            metrics["sram_kb"] = m.group(0).strip()
            break

    # Frequency
    freq_patterns = [
        r'(\d+\.?\d*)\s*[GM]Hz\s+clock',
        r'clock\s+(?:frequency\s+)?(?:of\s+)?(\d+\.?\d*)\s*[GM]Hz',
        r'operates?\s+at\s+(?:up\s+to\s+)?(\d+\.?\d*)\s*[GM]Hz',
        r'(\d+\.?\d*)\s*[GM]Hz\s+(?:operating|operation)',
        r'running\s+at\s+(\d+\.?\d*)\s*[GM]Hz',
        r'frequency\s+(?:of\s+)?(\d+\.?\d*)\s*[GM]Hz',
    ]
    for pat in freq_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            freq_str = m.group(0).strip()
            freq_m = re.search(r'(\d+\.?\d*)\s*([GM]Hz)', freq_str, re.IGNORECASE)
            if freq_m:
                val = float(freq_m.group(1))
                unit = freq_m.group(2)
                if unit.upper() == 'GHZ':
                    metrics["frequency_mhz"] = str(int(val * 1000))
                else:
                    metrics["frequency_mhz"] = str(int(val))
            break

    # Power
    power_patterns = [
        r'(?:dissipating|consumes?|power\s+(?:consumption\s+)?(?:of\s+)?)\s*(\d+\.?\d*)\s*([mu]?W)',
        r'(\d+\.?\d*)\s*([mu]?W)\s+(?:power|total)',
        r'(?:total|peak|average)\s+power\s+(?:of\s+)?(\d+\.?\d*)\s*([mu]?W)',
    ]
    for pat in power_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            unit = m.group(2)
            if unit == 'uW':
                val_mw = val / 1000
            elif unit == 'W':
                val_mw = val * 1000
            else:
                val_mw = val
            metrics["power_mw"] = str(round(val_mw, 2))
            break

    # Energy efficiency
    eff_patterns = [
        r'(\d+\.?\d*)\s*TOPS/W',
        r'(\d+\.?\d*)\s*GOPS/W',
        r'(\d+\.?\d*)\s*[pn]J/b(?:it)?',
        r'energy\s+efﬁciency\s+(?:of\s+)?(\d+\.?\d*\s*\S+)',
        r'(\d+\.?\d*)\s*TFLOPS/W',
    ]
    for pat in eff_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            metrics["energy_efficiency"] = m.group(0).strip()
            break

    # Throughput
    tp_patterns = [
        r'(\d+\.?\d*)\s*TOPS(?:\s|,|\.)',
        r'(\d+\.?\d*)\s*GOPS(?:\s|,|\.)',
        r'throughput\s+(?:of\s+)?(\d+\.?\d*\s*\S+)',
        r'(\d+\.?\d*)\s*TFLOPS(?:\s|,|\.)',
        r'(\d+\.?\d*)\s*[GM]b/s',
    ]
    for pat in tp_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            metrics["throughput"] = m.group(0).strip()
            break

    return metrics


def merge_with_existing(paper, text_metrics):
    """Merge text-extracted metrics with existing papers.json data."""
    merged = {}

    # Start with text-extracted metrics
    merged.update(text_metrics)

    # Override/supplement with papers.json data (which was manually curated)
    if paper.get("process_node"):
        merged["technology"] = paper["process_node"]
    if paper.get("die_area_mm2"):
        val = paper["die_area_mm2"]
        # Only use if it looks numeric
        try:
            float(val)
            merged["die_area_mm2"] = val
        except (ValueError, TypeError):
            if "die_area_mm2" not in merged:
                merged["die_area_mm2"] = val

    if paper.get("power_mw"):
        merged["power_mw"] = paper["power_mw"]
    if paper.get("energy_efficiency"):
        merged["energy_efficiency"] = paper["energy_efficiency"]
    if paper.get("target_model"):
        merged["target_model"] = paper["target_model"]

    return merged


def main():
    # Load papers.json
    papers_path = os.path.join(DATA_DIR, "papers.json")
    with open(papers_path, "r", encoding="utf-8") as f:
        papers = json.load(f)

    papers_by_id = {p["id"]: p for p in papers}

    total = 0
    for pid in sorted(papers_by_id.keys(),
                      key=lambda x: (int(x.split('.')[0]), int(x.split('.')[1]))):
        paper = papers_by_id[pid]
        paper_dir = os.path.join(DATA_DIR, pid)

        # Read text.md
        text_path = os.path.join(paper_dir, "text.md")
        text = ""
        if os.path.exists(text_path):
            with open(text_path, "r", encoding="utf-8") as f:
                text = f.read()

        # Extract metrics from text
        text_metrics = extract_from_text(text)

        # Merge with existing data
        metrics = merge_with_existing(paper, text_metrics)

        # Determine source figure (usually fig 7 or last figure)
        figures_path = os.path.join(paper_dir, "figures.json")
        if os.path.exists(figures_path):
            with open(figures_path) as f:
                figures = json.load(f)
            if figures:
                last_fig = max(figures, key=lambda f: f["figure_num"])
                metrics["source_figure"] = f"fig_{last_fig['figure_num']}"

        # Write metrics.json
        os.makedirs(paper_dir, exist_ok=True)
        metrics_path = os.path.join(paper_dir, "metrics.json")
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)

        field_count = len([v for v in metrics.values() if v])
        total += 1
        print(f"  Paper {pid}: {field_count} metrics extracted")

    print(f"\n{'='*60}")
    print(f"Processed {total} papers")

    # Summary of coverage
    all_fields = ["technology", "die_area_mm2", "supply_voltage", "sram_kb",
                   "frequency_mhz", "power_mw", "energy_efficiency", "throughput"]
    coverage = {f: 0 for f in all_fields}

    for pid in papers_by_id:
        mp = os.path.join(DATA_DIR, pid, "metrics.json")
        if os.path.exists(mp):
            with open(mp) as f:
                m = json.load(f)
            for field in all_fields:
                if m.get(field):
                    coverage[field] += 1

    print(f"\nMetrics coverage ({total} papers):")
    for field, count in coverage.items():
        pct = count / total * 100 if total > 0 else 0
        print(f"  {field:20s}: {count:3d}/{total} ({pct:.0f}%)")


if __name__ == "__main__":
    main()
