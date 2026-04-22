"""Smoke test — runs only the fetch layer (no API key needed).

Validates that RSS feeds and HTML scrapers actually return data before you spend
LLM tokens on a real run. Prints per-source counts and a sample story from each.

Run:  python test_fetch.py
"""
from __future__ import annotations
import logging
import sys
import yaml
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S',
)

from rss_fetcher import fetch_rss
from html_scrapers import fetch_html


def main() -> int:
    cfg_path = Path(__file__).parent / 'sources.yaml'
    cfg = yaml.safe_load(cfg_path.read_text(encoding='utf-8'))
    sources = [s for s in cfg.get('sources', []) if s.get('enabled', True)]

    print(f"\n=== Smoke testing {len(sources)} sources ===\n")
    summary: list[tuple[str, int, str]] = []

    for src in sources:
        try:
            if src['type'] == 'rss':
                items = fetch_rss(src, max_items=3)
            else:
                items = fetch_html(src)
            sample = items[0].title[:70] if items else '(no items)'
            summary.append((src['id'], len(items), sample))
        except Exception as e:
            summary.append((src['id'], -1, f'ERROR: {e}'))

    print('\n=== Summary ===')
    print(f"{'source_id':<35} {'count':>6}  sample")
    print('-' * 110)
    total = 0
    failed = 0
    for sid, count, sample in summary:
        if count < 0:
            failed += 1
            print(f"{sid:<35} {'ERR':>6}  {sample[:60]}")
        else:
            total += count
            print(f"{sid:<35} {count:>6}  {sample}")
    print('-' * 110)
    working = sum(1 for _, c, _ in summary if c > 0)
    print(f"\nWorking sources: {working}/{len(sources)}  |  Total stories: {total}  |  Failed: {failed}")
    return 0 if working > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
