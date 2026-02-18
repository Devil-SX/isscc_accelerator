#!/usr/bin/env python3
"""Extract detailed metrics from paper text and figures using an LLM.

Uses an OpenAI-compatible API to extract structured chip metrics from
paper text and optionally figure images (multimodal).

Writes metrics_detailed field into papers.json.
"""

import argparse
import base64
import json
import os
import re
import sys
import time

BASE = "/home/sdu/obsidian/isscc_accelerator"
DATA_DIR = os.path.join(BASE, "data")
IMAGES_DIR = os.path.join(BASE, "images")
PAPERS_JSON = os.path.join(DATA_DIR, "papers.json")

EXTRACTION_PROMPT = """You are an expert chip design researcher. Extract detailed metrics from this ISSCC paper.

Return a JSON object with the following schema (omit fields if not found in the paper):

{
    "technology": "<process node, e.g., '28nm CMOS'>",
    "die_area": { "value": "<number>", "unit": "mm²", "note": "<core/chip/total area>" },
    "supply_voltage": {
        "values": [
            { "value": "<voltage or range>", "unit": "V", "condition": "<what domain>" }
        ]
    },
    "frequency": {
        "values": [
            { "value": "<freq or range>", "unit": "MHz", "condition": "<what clock>" }
        ]
    },
    "sram": { "value": "<number>", "unit": "KB", "note": "<breakdown if available>" },
    "power": {
        "values": [
            { "value": "<number>", "unit": "mW", "condition": "<operating condition>" }
        ]
    },
    "energy_efficiency": {
        "values": [
            { "value": "<number>", "unit": "<unit like TOPS/W, μJ/token, etc.>", "condition": "<workload>" }
        ]
    },
    "throughput": {
        "values": [
            { "value": "<number>", "unit": "<unit like TOPS, GOPS, tokens/s>", "condition": "<precision/workload>" }
        ]
    },
    "comparison": {
        "vs_sota": "<comparison statement vs state-of-the-art>",
        "speedup": "<speedup claim if any>"
    },
    "quantization": "<quantization scheme if applicable>",
    "model_benchmarks": [
        { "model": "<model name>", "metric": "<value with unit>", "detail": "<additional detail>" }
    ]
}

IMPORTANT:
- Extract ALL metrics mentioned in the paper, including from comparison tables/figures
- Use exact values from the paper, do not round or approximate
- Include units always
- If multiple operating points exist, list all of them
- For energy efficiency, include all reported metrics (TOPS/W, μJ/token, nJ/bit, etc.)
- Return ONLY valid JSON, no markdown formatting or explanations
"""


def encode_image(image_path):
    """Encode an image file as base64 for multimodal API calls."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def build_messages(paper_id, text, image_paths=None):
    """Build the message list for the LLM API call."""
    content = []

    # Text content
    content.append({
        "type": "text",
        "text": f"Paper ID: {paper_id}\n\n{EXTRACTION_PROMPT}\n\nPaper text:\n{text}"
    })

    # Add images if available
    if image_paths:
        for img_path in image_paths:
            if os.path.exists(img_path):
                b64 = encode_image(img_path)
                ext = os.path.splitext(img_path)[1].lower()
                media_type = "image/png" if ext == ".png" else "image/jpeg"
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{media_type};base64,{b64}"
                    }
                })

    return [{"role": "user", "content": content}]


def call_llm(messages, api_key, base_url, model, max_retries=3):
    """Call the OpenAI-compatible API with retry logic."""
    try:
        import openai
    except ImportError:
        print("ERROR: openai package not installed. Run: pip install openai")
        sys.exit(1)

    client = openai.OpenAI(api_key=api_key, base_url=base_url)

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1,
                max_tokens=4096,
            )
            return response.choices[0].message.content
        except Exception as e:
            wait_time = 2 ** (attempt + 1)
            print(f"    API error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"    Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise


def parse_json_response(response_text):
    """Parse JSON from LLM response, handling markdown code blocks."""
    # Strip markdown code blocks if present
    text = response_text.strip()
    if text.startswith("```"):
        # Remove first line (```json or ```)
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"    JSON parse error: {e}")
        print(f"    Response preview: {text[:200]}")
        return None


def process_paper(paper_id, api_key, base_url, model, delay=1.0):
    """Process a single paper and return extracted metrics."""
    text_path = os.path.join(DATA_DIR, paper_id, "text.md")
    if not os.path.exists(text_path):
        print(f"  [{paper_id}] SKIP - no text.md")
        return None

    with open(text_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Check for figure images (fig_6.png and fig_7.png typically have comparison tables)
    image_paths = []
    for fig_num in [6, 7]:
        fig_path = os.path.join(IMAGES_DIR, paper_id, f"fig_{fig_num}.png")
        if os.path.exists(fig_path):
            image_paths.append(fig_path)

    messages = build_messages(paper_id, text, image_paths)

    print(f"  [{paper_id}] Calling LLM ({len(image_paths)} images)...")
    response_text = call_llm(messages, api_key, base_url, model)
    metrics = parse_json_response(response_text)

    if metrics:
        field_count = len([v for v in metrics.values() if v])
        print(f"  [{paper_id}] OK - {field_count} metric fields extracted")
    else:
        print(f"  [{paper_id}] FAIL - could not parse LLM response")

    time.sleep(delay)
    return metrics


def main():
    parser = argparse.ArgumentParser(
        description="Extract detailed metrics from ISSCC papers using LLM"
    )
    parser.add_argument("--api-key", required=True, help="API key for OpenAI-compatible service")
    parser.add_argument("--base-url", default="https://api.openai.com/v1",
                        help="Base URL for API (default: OpenAI)")
    parser.add_argument("--model", default="gpt-4o",
                        help="Model name (default: gpt-4o)")
    parser.add_argument("--paper-id", help="Process only this paper ID (e.g., 31.3)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print output without writing to papers.json")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Delay between API calls in seconds (default: 1.0)")
    parser.add_argument("--max-retries", type=int, default=3,
                        help="Max retries per API call (default: 3)")
    args = parser.parse_args()

    # Load papers.json
    with open(PAPERS_JSON, "r", encoding="utf-8") as f:
        papers = json.load(f)

    papers_by_id = {p["id"]: p for p in papers}

    if args.paper_id:
        if args.paper_id not in papers_by_id:
            print(f"ERROR: Paper ID '{args.paper_id}' not found in papers.json")
            sys.exit(1)
        target_ids = [args.paper_id]
    else:
        target_ids = sorted(
            papers_by_id.keys(),
            key=lambda x: (int(x.split('.')[0]), int(x.split('.')[1]))
        )

    success = 0
    failed = 0

    for pid in target_ids:
        try:
            metrics = process_paper(pid, args.api_key, args.base_url, args.model, args.delay)
            if metrics:
                if args.dry_run:
                    print(f"  [{pid}] DRY RUN - would write:")
                    print(json.dumps(metrics, indent=2, ensure_ascii=False)[:500])
                else:
                    papers_by_id[pid]["metrics_detailed"] = metrics
                success += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  [{pid}] ERROR: {e}")
            failed += 1

    if not args.dry_run:
        # Rebuild list preserving order
        updated_papers = [papers_by_id[p["id"]] for p in papers]
        with open(PAPERS_JSON, "w", encoding="utf-8") as f:
            json.dump(updated_papers, f, indent=2, ensure_ascii=False)
        print(f"\nWritten to {PAPERS_JSON}")

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Processed: {success + failed}")
    print(f"  Success: {success}")
    print(f"  Failed: {failed}")


if __name__ == "__main__":
    main()
