#!/usr/bin/env python3
"""Generate minimal SVG placeholder logos for each institution.

Creates a 64x64 circle with the institution's abbreviation/initials
in the center, using a consistent color scheme. Files are saved to
assets/logos/ in kebab-case naming.
"""

import os

BASE = "/home/sdu/obsidian/isscc_accelerator"
LOGOS_DIR = os.path.join(BASE, "assets", "logos")

# Institution name -> (filename, abbreviation, color)
INSTITUTIONS = [
    ("AMD", "amd", "AMD", "#ED1C24"),
    ("Broadcom", "broadcom", "BC", "#CC092F"),
    ("CEA-List", "cea-list", "CEA", "#003DA5"),
    ("Fudan University", "fudan-university", "FDU", "#1A237E"),
    ("HKUST", "hkust", "HKUST", "#003366"),
    ("HKUST(GZ)", "hkust-gz", "GZ", "#00509E"),
    ("IBM", "ibm", "IBM", "#0530AD"),
    ("IMECAS", "imecas", "IMEC", "#00796B"),
    ("Intel", "intel", "Intel", "#0071C5"),
    ("KAIST", "kaist", "KAIST", "#004C97"),
    ("MediaTek", "mediatek", "MTK", "#FFC107"),
    ("Northwestern University", "northwestern-university", "NU", "#4E2A84"),
    ("NTHU", "nthu", "NTHU", "#7B1FA2"),
    ("Nvidia", "nvidia", "NV", "#76B900"),
    ("Peking University", "peking-university", "PKU", "#8C1515"),
    ("Qualcomm", "qualcomm", "QC", "#3253DC"),
    ("Rebellions", "rebellions", "RB", "#FF5722"),
    ("Renesas Electronics", "renesas-electronics", "RE", "#0033A0"),
    ("Southeast University", "southeast-university", "SEU", "#1B5E20"),
    ("Tsinghua University", "tsinghua-university", "THU", "#660874"),
    ("TSMC", "tsmc", "TSMC", "#E53935"),
    ("UC Santa Barbara", "uc-santa-barbara", "UCSB", "#003660"),
    ("UNIST", "unist", "UNIST", "#1565C0"),
    ("University of Michigan", "university-of-michigan", "UM", "#00274C"),
    ("Xidian University", "xidian-university", "XDU", "#0D47A1"),
]

SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="30" fill="{color}" stroke="{color}" stroke-width="1" opacity="0.9"/>
  <text x="32" y="32" text-anchor="middle" dominant-baseline="central"
        font-family="Arial, Helvetica, sans-serif" font-weight="bold"
        font-size="{font_size}" fill="white">{abbr}</text>
</svg>"""


def get_font_size(abbr):
    """Choose font size based on abbreviation length."""
    length = len(abbr)
    if length <= 2:
        return 20
    elif length <= 3:
        return 16
    elif length <= 4:
        return 13
    else:
        return 11


def main():
    os.makedirs(LOGOS_DIR, exist_ok=True)

    for name, filename, abbr, color in INSTITUTIONS:
        font_size = get_font_size(abbr)
        svg_content = SVG_TEMPLATE.format(
            color=color,
            abbr=abbr,
            font_size=font_size
        )

        filepath = os.path.join(LOGOS_DIR, f"{filename}.svg")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"  Created: {filename}.svg ({name} -> {abbr})")

    print(f"\n{'='*60}")
    print(f"Generated {len(INSTITUTIONS)} logo placeholders in {LOGOS_DIR}")


if __name__ == "__main__":
    main()
