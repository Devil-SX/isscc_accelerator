#!/usr/bin/env python3
"""Download real logos or create high-quality SVG logos for all institutions."""

import urllib.request
import os
import json
import time

LOGO_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logos')

# Known Wikimedia Commons direct URLs (verified filenames)
WIKIMEDIA_URLS = {
    'hkust': 'https://upload.wikimedia.org/wikipedia/en/3/31/HKUST_Logo.svg',
    'unist': 'https://upload.wikimedia.org/wikipedia/en/e/e9/UNIST_seal.svg',
    'nthu': 'https://upload.wikimedia.org/wikipedia/en/a/a1/National_Tsing_Hua_University_logo.svg',
    'southeast-university': 'https://upload.wikimedia.org/wikipedia/en/3/3a/Southeast_University_logo.svg',
    'xidian-university': 'https://upload.wikimedia.org/wikipedia/en/4/4a/Xidian_University_logo.svg',
    'uc-santa-barbara': 'https://upload.wikimedia.org/wikipedia/en/a/a3/UC_Santa_Barbara_Seal.svg',
    'university-of-michigan': 'https://upload.wikimedia.org/wikipedia/commons/9/93/Seal_of_the_University_of_Michigan.svg',
    'cea-list': 'https://upload.wikimedia.org/wikipedia/commons/3/37/CEA_logo.svg',
    'imecas': None,  # No Wikimedia logo available
    'rebellions': None,  # Startup, no Wikimedia logo
    'hkust-gz': None,  # Too new, no Wikimedia logo
}

# High-quality SVG fallbacks for institutions without downloadable logos
SVG_LOGOS = {
    'hkust': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <circle cx="100" cy="100" r="95" fill="#003366" stroke="#C4972A" stroke-width="4"/>
  <circle cx="100" cy="100" r="75" fill="none" stroke="#C4972A" stroke-width="2"/>
  <text x="100" y="80" text-anchor="middle" fill="#C4972A" font-family="serif" font-size="22" font-weight="bold">HKUST</text>
  <text x="100" y="108" text-anchor="middle" fill="white" font-family="serif" font-size="11">Hong Kong University of</text>
  <text x="100" y="124" text-anchor="middle" fill="white" font-family="serif" font-size="11">Science and Technology</text>
  <text x="100" y="150" text-anchor="middle" fill="#C4972A" font-family="serif" font-size="12">Est. 1991</text>
</svg>''',
    'hkust-gz': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <circle cx="100" cy="100" r="95" fill="#003366" stroke="#C4972A" stroke-width="4"/>
  <circle cx="100" cy="100" r="75" fill="none" stroke="#C4972A" stroke-width="2"/>
  <text x="100" y="75" text-anchor="middle" fill="#C4972A" font-family="serif" font-size="20" font-weight="bold">HKUST</text>
  <text x="100" y="100" text-anchor="middle" fill="#C4972A" font-family="serif" font-size="16" font-weight="bold">(GZ)</text>
  <text x="100" y="125" text-anchor="middle" fill="white" font-family="serif" font-size="10">Guangzhou Campus</text>
  <text x="100" y="150" text-anchor="middle" fill="#C4972A" font-family="serif" font-size="12">Est. 2022</text>
</svg>''',
    'unist': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <circle cx="100" cy="100" r="95" fill="#1B3C73" stroke="#4A90D9" stroke-width="4"/>
  <circle cx="100" cy="100" r="75" fill="none" stroke="#4A90D9" stroke-width="2"/>
  <text x="100" y="90" text-anchor="middle" fill="white" font-family="sans-serif" font-size="36" font-weight="bold">UNIST</text>
  <text x="100" y="115" text-anchor="middle" fill="#4A90D9" font-family="sans-serif" font-size="10">Ulsan National Institute of</text>
  <text x="100" y="130" text-anchor="middle" fill="#4A90D9" font-family="sans-serif" font-size="10">Science and Technology</text>
</svg>''',
    'nthu': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <circle cx="100" cy="100" r="95" fill="#7B1FA2" stroke="#CE93D8" stroke-width="4"/>
  <circle cx="100" cy="100" r="75" fill="none" stroke="#CE93D8" stroke-width="2"/>
  <text x="100" y="80" text-anchor="middle" fill="white" font-family="serif" font-size="28" font-weight="bold">NTHU</text>
  <text x="100" y="108" text-anchor="middle" fill="#CE93D8" font-family="serif" font-size="10">National Tsing Hua</text>
  <text x="100" y="123" text-anchor="middle" fill="#CE93D8" font-family="serif" font-size="10">University</text>
  <text x="100" y="150" text-anchor="middle" fill="white" font-family="serif" font-size="13">清華大學</text>
</svg>''',
    'southeast-university': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <circle cx="100" cy="100" r="95" fill="#8B0000" stroke="#FFD700" stroke-width="4"/>
  <circle cx="100" cy="100" r="75" fill="none" stroke="#FFD700" stroke-width="2"/>
  <text x="100" y="75" text-anchor="middle" fill="#FFD700" font-family="serif" font-size="14" font-weight="bold">SOUTHEAST</text>
  <text x="100" y="95" text-anchor="middle" fill="#FFD700" font-family="serif" font-size="14" font-weight="bold">UNIVERSITY</text>
  <text x="100" y="125" text-anchor="middle" fill="white" font-family="serif" font-size="18">东南大学</text>
  <text x="100" y="155" text-anchor="middle" fill="#FFD700" font-family="serif" font-size="12">Est. 1902</text>
</svg>''',
    'xidian-university': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <circle cx="100" cy="100" r="95" fill="#003399" stroke="#FFD700" stroke-width="4"/>
  <circle cx="100" cy="100" r="75" fill="none" stroke="#FFD700" stroke-width="2"/>
  <text x="100" y="75" text-anchor="middle" fill="#FFD700" font-family="serif" font-size="16" font-weight="bold">XIDIAN</text>
  <text x="100" y="95" text-anchor="middle" fill="#FFD700" font-family="serif" font-size="14" font-weight="bold">UNIVERSITY</text>
  <text x="100" y="125" text-anchor="middle" fill="white" font-family="serif" font-size="18">西安电子科技大学</text>
  <text x="100" y="155" text-anchor="middle" fill="#FFD700" font-family="serif" font-size="12">Est. 1931</text>
</svg>''',
    'uc-santa-barbara': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <circle cx="100" cy="100" r="95" fill="#003660" stroke="#FEBC11" stroke-width="4"/>
  <circle cx="100" cy="100" r="75" fill="none" stroke="#FEBC11" stroke-width="2"/>
  <text x="100" y="70" text-anchor="middle" fill="#FEBC11" font-family="serif" font-size="32" font-weight="bold">UC</text>
  <text x="100" y="100" text-anchor="middle" fill="white" font-family="serif" font-size="14" font-weight="bold">SANTA</text>
  <text x="100" y="120" text-anchor="middle" fill="white" font-family="serif" font-size="14" font-weight="bold">BARBARA</text>
  <text x="100" y="150" text-anchor="middle" fill="#FEBC11" font-family="serif" font-size="11">Est. 1891</text>
</svg>''',
    'university-of-michigan': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="10" fill="#00274C"/>
  <text x="100" y="120" text-anchor="middle" fill="#FFCB05" font-family="serif" font-size="120" font-weight="bold">M</text>
  <text x="100" y="175" text-anchor="middle" fill="white" font-family="serif" font-size="13">MICHIGAN</text>
</svg>''',
    'cea-list': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
  <rect width="200" height="80" rx="4" fill="white"/>
  <rect x="0" y="0" width="6" height="80" fill="#E30613"/>
  <text x="20" y="42" fill="#1D1D1B" font-family="sans-serif" font-size="36" font-weight="bold">CEA</text>
  <text x="125" y="42" fill="#E30613" font-family="sans-serif" font-size="36" font-weight="bold">LIST</text>
  <text x="20" y="65" fill="#666" font-family="sans-serif" font-size="10">Commissariat à l'énergie atomique</text>
</svg>''',
    'imecas': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <circle cx="100" cy="100" r="95" fill="#1A237E" stroke="#42A5F5" stroke-width="4"/>
  <circle cx="100" cy="100" r="75" fill="none" stroke="#42A5F5" stroke-width="2"/>
  <text x="100" y="80" text-anchor="middle" fill="white" font-family="sans-serif" font-size="24" font-weight="bold">IMECAS</text>
  <text x="100" y="108" text-anchor="middle" fill="#42A5F5" font-family="sans-serif" font-size="9">Institute of Microelectronics</text>
  <text x="100" y="123" text-anchor="middle" fill="#42A5F5" font-family="sans-serif" font-size="9">Chinese Academy of Sciences</text>
  <text x="100" y="148" text-anchor="middle" fill="white" font-family="sans-serif" font-size="13">中科院微电子所</text>
</svg>''',
    'rebellions': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect width="200" height="200" rx="20" fill="#0A0A0A"/>
  <text x="100" y="90" text-anchor="middle" fill="#00E5FF" font-family="sans-serif" font-size="60" font-weight="bold">R</text>
  <text x="100" y="130" text-anchor="middle" fill="white" font-family="sans-serif" font-size="18" font-weight="bold" letter-spacing="4">REBELLIONS</text>
  <text x="100" y="155" text-anchor="middle" fill="#666" font-family="sans-serif" font-size="10">AI Semiconductor</text>
</svg>''',
}


def download_logo(name, url, dest_path):
    """Try to download a logo from URL."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            if len(data) > 400:  # Real file, not error page
                with open(dest_path, 'wb') as f:
                    f.write(data)
                print(f"  DOWNLOADED: {name} ({len(data)} bytes) -> {dest_path}")
                return True
            else:
                print(f"  TOO SMALL: {name} ({len(data)} bytes)")
                return False
    except Exception as e:
        print(f"  FAILED: {name} - {e}")
        return False


def create_svg(name, svg_content, dest_path):
    """Create SVG logo."""
    with open(dest_path, 'w') as f:
        f.write(svg_content)
    print(f"  CREATED SVG: {name} ({len(svg_content)} bytes) -> {dest_path}")


def main():
    os.makedirs(LOGO_DIR, exist_ok=True)

    # Check which logos are still placeholders
    placeholders = []
    for name in WIKIMEDIA_URLS:
        path = os.path.join(LOGO_DIR, f'{name}.svg')
        if os.path.exists(path):
            size = os.path.getsize(path)
            if size < 500:
                placeholders.append(name)
        else:
            placeholders.append(name)

    print(f"Found {len(placeholders)} placeholder logos to replace: {placeholders}")

    for name in placeholders:
        dest = os.path.join(LOGO_DIR, f'{name}.svg')
        print(f"\nProcessing: {name}")

        # Try Wikimedia download first
        url = WIKIMEDIA_URLS.get(name)
        if url:
            success = download_logo(name, url, dest)
            if success:
                continue

        # Fallback: create SVG
        if name in SVG_LOGOS:
            create_svg(name, SVG_LOGOS[name], dest)
        else:
            print(f"  WARNING: No SVG template for {name}")

    # Verify all logos
    print("\n=== Final status ===")
    for f in sorted(os.listdir(LOGO_DIR)):
        path = os.path.join(LOGO_DIR, f)
        size = os.path.getsize(path)
        status = "OK" if size > 500 else "PLACEHOLDER"
        print(f"  {status}: {f} ({size} bytes)")


if __name__ == '__main__':
    main()
