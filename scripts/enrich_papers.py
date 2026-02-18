#!/usr/bin/env python3
"""
Enrich papers.json with analytical_tags, affiliation_info, abstract,
text_en stubs for challenges/ideas, metrics_detailed stub, and figure_paragraphs stub.
"""

import json
import re
import os

BASE_DIR = "/home/sdu/obsidian/isscc_accelerator"
PAPERS_JSON = os.path.join(BASE_DIR, "data", "papers.json")

# --- Analytical Tags ---
ANALYTICAL_TAGS = {
    "2.1": ["混合精度", "3D堆叠/HBM", "业界"],
    "2.2": ["芯粒/Chiplet", "可重构", "LLM/NLP", "业界"],
    "2.3": ["稀疏化", "可重构", "视觉/CV", "学界"],
    "2.4": ["视觉/CV", "学界"],
    "2.5": ["学界"],
    "2.6": ["混合精度", "稀疏化", "LLM/NLP", "片外访存优化", "业界"],
    "2.7": ["量化", "混合精度", "生成式AI", "片外访存优化", "学界"],
    "2.8": ["生成式AI", "可重构", "业界"],
    "2.9": ["可重构", "视觉/CV", "学界"],
    "2.10": ["可重构", "视觉/CV", "学界"],
    "10.1": ["芯粒/Chiplet", "业界"],
    "10.2": ["业界"],
    "10.3": ["业界"],
    "10.4": ["业界"],
    "10.5": ["学界"],
    "10.6": ["3D堆叠/HBM", "业界"],
    "10.7": ["CIM", "学界"],
    "10.8": ["学界"],
    "10.9": ["学界"],
    "10.10": ["CIM", "学界"],
    "18.1": ["芯粒/Chiplet", "学界"],
    "18.2": ["CIM", "LLM/NLP", "学界"],
    "18.3": ["CIM", "稀疏化", "LLM/NLP", "学界"],
    "18.4": ["CIM", "学界"],
    "18.5": ["量化", "生成式AI", "学界"],
    "30.1": ["CIM", "混合精度", "学界"],
    "30.2": ["CIM", "业界"],
    "30.3": ["CIM", "LLM/NLP", "学界"],
    "30.4": ["CIM", "位串行", "学界"],
    "30.5": ["CIM", "混合精度", "学界"],
    "30.6": ["CIM", "学界"],
    "30.7": ["3D堆叠/HBM", "片外访存优化", "LLM/NLP", "学界"],
    "30.8": ["CIM", "视觉/CV", "学界"],
    "30.9": ["CIM", "业界"],
    "31.1": ["CIM", "3D堆叠/HBM", "量化", "LLM/NLP", "学界"],
    "31.2": ["量化", "蒸馏/剪枝", "混合精度", "LLM/NLP", "学界"],
    "31.3": ["量化", "LUT计算", "位串行", "LLM/NLP", "学界"],
    "31.4": ["LUT计算", "稀疏化", "生成式AI", "学界"],
    "31.5": ["片外访存优化", "LLM/NLP", "学界"],
    "31.6": ["稀疏化", "LLM/NLP", "视觉/CV", "学界"],
    "31.7": ["LUT计算", "LLM/NLP", "学界"],
    "31.8": ["稀疏化", "LLM/NLP", "学界"],
    "31.9": ["视觉/CV", "业界"],
}

# --- Affiliation Info ---
AFFILIATION_INFO = {
    "AMD": {"name": "AMD", "name_zh": "AMD", "type": "industry", "country": "United States", "country_code": "US", "logo": "assets/logos/amd.png"},
    "Rebellions": {"name": "Rebellions", "name_zh": "Rebellions", "type": "industry", "country": "South Korea", "country_code": "KR", "logo": "assets/logos/rebellions.png"},
    "UNIST": {"name": "UNIST", "name_zh": "蔚山科学技术大学", "type": "academia", "country": "South Korea", "country_code": "KR", "logo": "assets/logos/unist.png"},
    "KAIST": {"name": "KAIST", "name_zh": "韩国科学技术院", "type": "academia", "country": "South Korea", "country_code": "KR", "logo": "assets/logos/kaist.png"},
    "University of Michigan": {"name": "University of Michigan", "name_zh": "密歇根大学", "type": "academia", "country": "United States", "country_code": "US", "logo": "assets/logos/university-of-michigan.png"},
    "IBM": {"name": "IBM", "name_zh": "IBM", "type": "industry", "country": "United States", "country_code": "US", "logo": "assets/logos/ibm.png"},
    "NTHU": {"name": "NTHU", "name_zh": "国立清华大学", "type": "academia", "country": "Taiwan", "country_code": "TW", "logo": "assets/logos/nthu.png"},
    "MediaTek": {"name": "MediaTek", "name_zh": "联发科", "type": "industry", "country": "Taiwan", "country_code": "TW", "logo": "assets/logos/mediatek.png"},
    "Tsinghua": {"name": "Tsinghua University", "name_zh": "清华大学", "type": "academia", "country": "China", "country_code": "CN", "logo": "assets/logos/tsinghua-university.png"},
    "Tsinghua University": {"name": "Tsinghua University", "name_zh": "清华大学", "type": "academia", "country": "China", "country_code": "CN", "logo": "assets/logos/tsinghua-university.png"},
    "Renesas Electronics": {"name": "Renesas Electronics", "name_zh": "瑞萨电子", "type": "industry", "country": "Japan", "country_code": "JP", "logo": "assets/logos/renesas-electronics.png"},
    "Qualcomm": {"name": "Qualcomm", "name_zh": "高通", "type": "industry", "country": "United States", "country_code": "US", "logo": "assets/logos/qualcomm.png"},
    "Broadcom": {"name": "Broadcom", "name_zh": "博通", "type": "industry", "country": "United States", "country_code": "US", "logo": "assets/logos/broadcom.png"},
    "Northwestern University": {"name": "Northwestern University", "name_zh": "西北大学", "type": "academia", "country": "United States", "country_code": "US", "logo": "assets/logos/northwestern-university.png"},
    "Intel": {"name": "Intel", "name_zh": "英特尔", "type": "industry", "country": "United States", "country_code": "US", "logo": "assets/logos/intel.png"},
    "Peking University": {"name": "Peking University", "name_zh": "北京大学", "type": "academia", "country": "China", "country_code": "CN", "logo": "assets/logos/peking-university.png"},
    "UC Santa Barbara": {"name": "UC Santa Barbara", "name_zh": "加州大学圣巴巴拉分校", "type": "academia", "country": "United States", "country_code": "US", "logo": "assets/logos/uc-santa-barbara.png"},
    "CEA-List": {"name": "CEA-List", "name_zh": "法国原子能委员会", "type": "research_inst", "country": "France", "country_code": "FR", "logo": "assets/logos/cea-list.png"},
    "HKUST(GZ)": {"name": "HKUST(GZ)", "name_zh": "香港科技大学(广州)", "type": "academia", "country": "China", "country_code": "CN", "logo": "assets/logos/hkust-gz.png"},
    "HKUST": {"name": "HKUST", "name_zh": "香港科技大学", "type": "academia", "country": "Hong Kong", "country_code": "HK", "logo": "assets/logos/hkust.png"},
    "Southeast University": {"name": "Southeast University", "name_zh": "东南大学", "type": "academia", "country": "China", "country_code": "CN", "logo": "assets/logos/southeast-university.png"},
    "TSMC": {"name": "TSMC", "name_zh": "台积电", "type": "industry", "country": "Taiwan", "country_code": "TW", "logo": "assets/logos/tsmc.png"},
    "Xidian University": {"name": "Xidian University", "name_zh": "西安电子科技大学", "type": "academia", "country": "China", "country_code": "CN", "logo": "assets/logos/xidian-university.png"},
    "IMECAS": {"name": "IMECAS", "name_zh": "中科院微电子所", "type": "research_inst", "country": "China", "country_code": "CN", "logo": "assets/logos/imecas.png"},
    "Fudan University": {"name": "Fudan University", "name_zh": "复旦大学", "type": "academia", "country": "China", "country_code": "CN", "logo": "assets/logos/fudan-university.png"},
    "Nvidia": {"name": "Nvidia", "name_zh": "英伟达", "type": "industry", "country": "United States", "country_code": "US", "logo": "assets/logos/nvidia.png"},
}


def is_affiliation_line(line):
    """Check if a line looks like an affiliation/institution line.

    Affiliation lines typically start with numbered institution markers like:
    '1AMD, Austin, TX' or '1KAIST, Daejeon, Korea' or '4Xi'an UniIC...'
    They may also contain patterns like 'University', country names, state abbreviations.
    """
    stripped = line.strip()
    # Matches lines starting with a digit followed by institution name, city, state/country
    # e.g. "1AMD, Austin, TX, 2AMD, Fort Collins, CO..."
    # e.g. "1KAIST, Daejeon, Korea, 2Massachusetts Institute..."
    # e.g. "4Xi'an UniIC Semiconductors, Xi'an, China"
    if re.match(r'^\d+[A-Z]', stripped):
        return True
    return False


def extract_abstract(paper_id):
    """Extract abstract from data/{id}/text.md.

    The abstract is the paragraph(s) just before the line containing only "Abstract"
    near the end of the file. Pattern:
      - Author names line
      - Affiliation line(s)
      - (optional blank line)
      - Abstract text paragraph (one or more lines)
      - "Abstract" label line

    Some papers have the affiliation line directly adjacent to abstract text
    (no blank line). We detect and remove affiliation lines.
    """
    text_path = os.path.join(BASE_DIR, "data", paper_id, "text.md")
    if not os.path.exists(text_path):
        return ""

    with open(text_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find the line matching "Abstract" (possibly with whitespace)
    abstract_line_idx = None
    for i, line in enumerate(lines):
        if re.match(r'^\s*Abstract\s*$', line):
            abstract_line_idx = i

    if abstract_line_idx is None:
        return ""

    # Go backwards from abstract_line_idx, skip blank lines
    idx = abstract_line_idx - 1
    while idx >= 0 and lines[idx].strip() == "":
        idx -= 1

    # Collect text lines going backwards until we hit an empty line
    abstract_lines = []
    while idx >= 0:
        stripped = lines[idx].strip()
        if stripped == "":
            break
        abstract_lines.append(stripped)
        idx -= 1

    # Reverse to get correct order
    abstract_lines.reverse()

    # Remove leading affiliation lines (lines starting with digit+uppercase)
    while abstract_lines and is_affiliation_line(abstract_lines[0]):
        abstract_lines.pop(0)

    # Join into a single paragraph
    abstract_text = " ".join(abstract_lines)

    # Clean up any double spaces
    abstract_text = re.sub(r'\s+', ' ', abstract_text).strip()

    return abstract_text


def main():
    # Load existing papers.json
    with open(PAPERS_JSON, "r", encoding="utf-8") as f:
        papers = json.load(f)

    print(f"Loaded {len(papers)} papers from papers.json")

    abstracts_extracted = 0
    affiliation_matched = 0
    tags_added = 0

    for paper in papers:
        pid = paper["id"]

        # 1. Add analytical_tags
        if pid in ANALYTICAL_TAGS:
            paper["analytical_tags"] = ANALYTICAL_TAGS[pid]
            tags_added += 1
        else:
            paper["analytical_tags"] = []
            print(f"  WARNING: No analytical tags for paper {pid}")

        # 2. Add affiliation_info
        affiliation = paper.get("affiliation", "")
        if affiliation in AFFILIATION_INFO:
            paper["affiliation_info"] = AFFILIATION_INFO[affiliation]
            affiliation_matched += 1
        else:
            paper["affiliation_info"] = {
                "name": affiliation,
                "name_zh": affiliation,
                "type": "unknown",
                "country": "Unknown",
                "country_code": "",
                "logo": ""
            }
            print(f"  WARNING: No affiliation info for '{affiliation}' (paper {pid})")

        # 3. Extract abstract from text.md
        abstract = extract_abstract(pid)
        paper["abstract"] = abstract
        if abstract:
            abstracts_extracted += 1
        else:
            print(f"  WARNING: No abstract extracted for paper {pid}")

        # 4. Add text_en stubs to challenges and ideas
        for challenge in paper.get("challenges", []):
            if "text_en" not in challenge:
                challenge["text_en"] = ""

        for idea in paper.get("ideas", []):
            if "text_en" not in idea:
                idea["text_en"] = ""

        # 5. Add metrics_detailed stub
        if "metrics_detailed" not in paper:
            paper["metrics_detailed"] = {}

        # 6. Add figure_paragraphs stub
        if "figure_paragraphs" not in paper:
            paper["figure_paragraphs"] = []

    # Write enriched papers.json
    with open(PAPERS_JSON, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)

    print(f"\n=== Enrichment Summary ===")
    print(f"Total papers: {len(papers)}")
    print(f"Analytical tags added: {tags_added}")
    print(f"Affiliations matched: {affiliation_matched}")
    print(f"Abstracts extracted: {abstracts_extracted}")
    print(f"Papers enriched and written to {PAPERS_JSON}")


if __name__ == "__main__":
    main()
