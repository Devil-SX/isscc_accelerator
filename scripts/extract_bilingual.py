#!/usr/bin/env python3
"""Add English translations for challenges and ideas using an LLM.

For each paper, reads the Chinese challenges/ideas from papers.json and
prompts the LLM to translate them to English using original paper terminology.
Updates the text_en field on each challenge and idea.
"""

import argparse
import json
import os
import re
import sys
import time

BASE = "/home/sdu/obsidian/isscc_accelerator"
DATA_DIR = os.path.join(BASE, "data")
PAPERS_JSON = os.path.join(DATA_DIR, "papers.json")

TRANSLATION_PROMPT = """You are an expert chip design researcher fluent in both Chinese and English.

I have a paper from ISSCC with the following details:
- Title: {title}
- Paper ID: {paper_id}

Below is the paper text for terminology reference:
{paper_text_preview}

Please translate the following Chinese text items to English. Use the original paper's technical terminology where possible. Return ONLY a JSON object with the exact same structure.

Items to translate:
{items_json}

Return a JSON object with two arrays:
{{
    "challenges": [
        {{ "text_en": "<English translation of challenge>" }}
    ],
    "ideas": [
        {{ "text_en": "<English translation of idea>" }}
    ]
}}

IMPORTANT:
- Use precise technical terminology from the paper
- Keep translations concise but accurate
- Return ONLY valid JSON, no markdown or explanations
"""


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
                max_tokens=2048,
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
    text = response_text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"    JSON parse error: {e}")
        print(f"    Response preview: {text[:200]}")
        return None


def process_paper(paper, api_key, base_url, model, delay=1.0):
    """Process a single paper and return translated text."""
    pid = paper["id"]
    challenges = paper.get("challenges", [])
    ideas = paper.get("ideas", [])

    if not challenges and not ideas:
        print(f"  [{pid}] SKIP - no challenges or ideas")
        return None

    # Check if already translated
    all_translated = True
    for c in challenges:
        if not c.get("text_en"):
            all_translated = False
            break
    if all_translated:
        for idea in ideas:
            if not idea.get("text_en"):
                all_translated = False
                break
    if all_translated:
        print(f"  [{pid}] SKIP - already translated")
        return None

    # Read paper text for terminology reference
    text_path = os.path.join(DATA_DIR, pid, "text.md")
    paper_text_preview = ""
    if os.path.exists(text_path):
        with open(text_path, "r", encoding="utf-8") as f:
            paper_text_preview = f.read()[:3000]  # First 3000 chars for context

    # Build items to translate
    items = {
        "challenges": [{"text_zh": c["text"]} for c in challenges],
        "ideas": [{"text_zh": i["text"]} for i in ideas]
    }

    prompt = TRANSLATION_PROMPT.format(
        title=paper.get("title", ""),
        paper_id=pid,
        paper_text_preview=paper_text_preview,
        items_json=json.dumps(items, ensure_ascii=False, indent=2)
    )

    messages = [{"role": "user", "content": prompt}]

    print(f"  [{pid}] Calling LLM ({len(challenges)} challenges, {len(ideas)} ideas)...")
    response_text = call_llm(messages, api_key, base_url, model)
    result = parse_json_response(response_text)

    if result:
        print(f"  [{pid}] OK - translations received")
    else:
        print(f"  [{pid}] FAIL - could not parse response")

    time.sleep(delay)
    return result


def apply_translations(paper, translations):
    """Apply translations to the paper's challenges and ideas."""
    if not translations:
        return False

    changed = False
    translated_challenges = translations.get("challenges", [])
    translated_ideas = translations.get("ideas", [])

    for i, c in enumerate(paper.get("challenges", [])):
        if i < len(translated_challenges):
            text_en = translated_challenges[i].get("text_en", "")
            if text_en:
                c["text_en"] = text_en
                changed = True

    for i, idea in enumerate(paper.get("ideas", [])):
        if i < len(translated_ideas):
            text_en = translated_ideas[i].get("text_en", "")
            if text_en:
                idea["text_en"] = text_en
                changed = True

    return changed


def main():
    parser = argparse.ArgumentParser(
        description="Add English translations for challenges and ideas using LLM"
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
    skipped = 0

    for pid in target_ids:
        paper = papers_by_id[pid]
        try:
            translations = process_paper(paper, args.api_key, args.base_url, args.model, args.delay)
            if translations is None:
                skipped += 1
                continue
            if args.dry_run:
                print(f"  [{pid}] DRY RUN - would write:")
                print(json.dumps(translations, indent=2, ensure_ascii=False)[:500])
                success += 1
            else:
                if apply_translations(paper, translations):
                    success += 1
                else:
                    failed += 1
        except Exception as e:
            print(f"  [{pid}] ERROR: {e}")
            failed += 1

    if not args.dry_run:
        updated_papers = [papers_by_id[p["id"]] for p in papers]
        with open(PAPERS_JSON, "w", encoding="utf-8") as f:
            json.dump(updated_papers, f, indent=2, ensure_ascii=False)
        print(f"\nWritten to {PAPERS_JSON}")

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Processed: {success + failed + skipped}")
    print(f"  Translated: {success}")
    print(f"  Failed: {failed}")
    print(f"  Skipped: {skipped}")


if __name__ == "__main__":
    main()
