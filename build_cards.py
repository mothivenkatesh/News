"""Orchestrator — fetches all configured sources, dedups, generates cards, writes JSON.

Run:  python build_cards.py
Output: web/cards.json (consumed by the web frontend)
        output/cards-YYYY-MM-DD.json (daily archive)
        output/run-stats.json (last run telemetry)
"""
from __future__ import annotations
import os
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
import yaml

# Load .env if python-dotenv is installed (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from rss_fetcher import fetch_rss
from html_scrapers import fetch_html
from dedup import filter_unseen, stats as dedup_stats
from card_generator import generate_cards, ollama_health
from models import Story

ROOT = Path(__file__).parent
SOURCES_FILE = ROOT / 'sources.yaml'
WEB_OUT = ROOT / 'web' / 'cards.json'
ARCHIVE_DIR = ROOT / 'output'
STATS_FILE = ARCHIVE_DIR / 'run-stats.json'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger('orchestrator')


def load_sources() -> list[dict]:
    with open(SOURCES_FILE, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    return [s for s in cfg.get('sources', []) if s.get('enabled', True)]


def fetch_all(sources: list[dict]) -> tuple[list[Story], dict]:
    """Fetch every enabled source. Returns (stories, per-source-counts)."""
    all_stories: list[Story] = []
    counts: dict[str, int] = {}
    for src in sources:
        try:
            if src['type'] == 'rss':
                items = fetch_rss(src)
            elif src['type'] == 'html':
                items = fetch_html(src)
            else:
                logger.warning(f"Unknown source type: {src['type']}")
                items = []
            counts[src['id']] = len(items)
            all_stories.extend(items)
        except Exception as e:
            logger.error(f"[{src['id']}] crashed: {e}")
            counts[src['id']] = 0
    return all_stories, counts


def main() -> int:
    started_at = datetime.now(timezone.utc)
    logger.info(f"=== fintech-inshorts run @ {started_at.isoformat()} ===")

    # 0. Ollama precheck — fail fast if it's down or model isn't pulled
    ok, msg = ollama_health()
    logger.info(f"Ollama: {msg}")
    if not ok:
        logger.error("Aborting — fix the Ollama setup above and rerun.")
        return 1

    sources = load_sources()
    logger.info(f"Loaded {len(sources)} enabled sources")

    # 1. Fetch
    stories, fetch_counts = fetch_all(sources)
    logger.info(f"Fetched {len(stories)} total stories")
    for src_id, n in sorted(fetch_counts.items(), key=lambda x: -x[1]):
        logger.info(f"  {src_id:<35} {n:>4}")

    # 2. Dedup (URL + normalized-title)
    new_stories = filter_unseen(stories)
    logger.info(f"After dedup: {len(new_stories)} new ({len(stories) - len(new_stories)} already seen)")

    if not new_stories:
        logger.info("No new stories — keeping existing cards.json untouched.")
        return 0

    # 3. LLM card generation via Ollama (diversity-aware selection inside)
    max_cards = int(os.getenv('CARDS_PER_RUN', '20'))
    min_importance = int(os.getenv('MIN_IMPORTANCE', '4'))  # drop cards below this — bumped to 4 to filter off-topic insurtech/gaming/macro noise
    min_feed_size = int(os.getenv('MIN_FEED_SIZE', '5'))    # but keep at least this many
    logger.info(f"Generating cards (max {max_cards}) via Ollama...")
    raw_cards = generate_cards(new_stories, max_cards=max_cards)
    logger.info(f"Generated {len(raw_cards)} raw cards")

    # 3b. Filter by importance, with a floor to avoid an empty feed on slow days
    high_signal = [c for c in raw_cards if c.importance >= min_importance]
    if len(high_signal) >= min_feed_size:
        new_cards = high_signal
        dropped = len(raw_cards) - len(new_cards)
        if dropped:
            logger.info(f"Dropped {dropped} low-importance cards (importance < {min_importance})")
    else:
        # Not enough high-signal — keep top N by importance to ensure feed isn't empty
        raw_cards.sort(key=lambda c: -c.importance)
        new_cards = raw_cards[:max(min_feed_size, len(high_signal))]
        logger.info(
            f"Only {len(high_signal)} cards met threshold; "
            f"keeping top {len(new_cards)} by importance to maintain min_feed_size"
        )

    # 4. Merge with existing cards.json (keep older cards visible until they age out)
    existing: list[dict] = []
    if WEB_OUT.exists():
        try:
            existing = json.loads(WEB_OUT.read_text(encoding='utf-8')).get('cards', [])
        except Exception:
            existing = []

    new_card_dicts = [c.to_dict() for c in new_cards]
    new_ids = {nc['id'] for nc in new_card_dicts}
    merged = new_card_dicts + [c for c in existing if c.get('id') not in new_ids]
    merged = merged[:200]  # keep last 200 cards in the live feed

    # 5. Write outputs
    WEB_OUT.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'count': len(merged),
        'cards': merged,
    }
    WEB_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    logger.info(f"Wrote {len(merged)} cards to {WEB_OUT}")

    archive_path = ARCHIVE_DIR / f"cards-{started_at.strftime('%Y-%m-%d')}.json"
    archive_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')

    stats = {
        'started_at': started_at.isoformat(),
        'finished_at': datetime.now(timezone.utc).isoformat(),
        'sources_total': len(sources),
        'stories_fetched': len(stories),
        'stories_new': len(new_stories),
        'cards_generated': len(new_cards),
        'cards_in_feed': len(merged),
        'fetch_counts': fetch_counts,
        'dedup': dedup_stats(),
    }
    STATS_FILE.write_text(json.dumps(stats, indent=2), encoding='utf-8')
    elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
    logger.info(f"Done in {elapsed:.1f}s ({elapsed/max(1,len(new_cards)):.1f}s per card)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
