#!/usr/bin/env python3
"""Batch translate challenges/ideas to English using original paper text as context."""

import json
import os
import sys
import time
import anthropic

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
PAPERS_JSON = os.path.join(DATA_DIR, 'papers.json')

client = anthropic.Anthropic(
    base_url=os.environ.get('ANTHROPIC_BASE_URL'),
    api_key=os.environ.get('ANTHROPIC_AUTH_TOKEN')
)

def read_text_md(paper_id):
    path = os.path.join(DATA_DIR, paper_id, 'text.md')
    if os.path.exists(path):
        with open(path, 'r') as f:
            return f.read()
    return ''

def translate_paper(paper, text_md):
    """Translate challenges and ideas for one paper."""
    challenges = paper.get('challenges', [])
    ideas = paper.get('ideas', [])

    if not challenges and not ideas:
        return challenges, ideas

    # Build prompt
    challenge_lines = []
    for i, c in enumerate(challenges):
        challenge_lines.append(f"C{i+1}: {c['text']}")

    idea_lines = []
    for i, idea in enumerate(ideas):
        idea_lines.append(f"I{i+1}: {idea['text']}")

    prompt = f"""You are translating Chinese technical summaries into English for an ISSCC paper survey.

Below is the original English paper text, followed by Chinese challenge/idea summaries.
Translate each Chinese summary into concise English (1 sentence each), using the EXACT technical terms and data from the original paper. Do NOT paraphrase — match the paper's terminology precisely.

## Original Paper Text
{text_md[:8000]}

## Chinese Summaries to Translate

### Challenges
{chr(10).join(challenge_lines)}

### Ideas
{chr(10).join(idea_lines)}

## Output Format
Return ONLY a JSON object with this exact format (no markdown fences):
{{"challenges": ["english for C1", "english for C2", ...], "ideas": ["english for I1", "english for I2", ...]}}"""

    try:
        resp = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=2000,
            messages=[{'role': 'user', 'content': prompt}]
        )
        text = resp.content[0].text.strip()
        # Strip markdown fences if present
        if text.startswith('```'):
            text = text.split('\n', 1)[1]
            if text.endswith('```'):
                text = text[:-3]
            elif '```' in text:
                text = text[:text.rfind('```')]
        result = json.loads(text.strip())
        return result.get('challenges', []), result.get('ideas', [])
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return None, None

def main():
    with open(PAPERS_JSON) as f:
        papers = json.load(f)

    total = len(papers)
    for idx, paper in enumerate(papers):
        pid = paper['id']
        challenges = paper.get('challenges', [])
        ideas = paper.get('ideas', [])

        # Skip if already translated
        has_en = any(c.get('text_en') for c in challenges) or any(i.get('text_en') for i in ideas)
        if has_en:
            print(f"[{idx+1}/{total}] {pid}: already translated, skipping")
            continue

        if not challenges and not ideas:
            print(f"[{idx+1}/{total}] {pid}: no challenges/ideas, skipping")
            continue

        print(f"[{idx+1}/{total}] {pid}: translating {len(challenges)}C + {len(ideas)}I ...")

        text_md = read_text_md(pid)
        en_challenges, en_ideas = translate_paper(paper, text_md)

        if en_challenges is not None:
            for i, c in enumerate(challenges):
                if i < len(en_challenges):
                    c['text_en'] = en_challenges[i]
            for i, idea in enumerate(ideas):
                if i < len(en_ideas):
                    idea['text_en'] = en_ideas[i]
            print(f"  OK: {len(en_challenges)}C + {len(en_ideas)}I translated")
        else:
            print(f"  FAILED")

        # Rate limit
        time.sleep(0.5)

    # Save
    with open(PAPERS_JSON, 'w') as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)

    # Summary
    filled = 0
    empty = 0
    for p in papers:
        for c in p.get('challenges', []):
            if c.get('text_en'): filled += 1
            else: empty += 1
        for i in p.get('ideas', []):
            if i.get('text_en'): filled += 1
            else: empty += 1
    print(f"\nDone: {filled} translated, {empty} remaining empty")

if __name__ == '__main__':
    main()
