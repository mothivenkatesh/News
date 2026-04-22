"""Generic RSS / Atom feed fetcher using feedparser."""
from __future__ import annotations
import feedparser
from datetime import datetime, timezone
from dateutil import parser as date_parser
import logging
from models import Story

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 "
    "fintech-inshorts/0.1 (+https://mothi.work)"
)


def _parse_date(entry) -> datetime:
    """Best-effort date parse from a feed entry."""
    for attr in ('published', 'updated', 'pubDate', 'created'):
        val = None
        try:
            val = getattr(entry, attr, None)
        except Exception:
            pass
        if not val and hasattr(entry, 'get'):
            val = entry.get(attr)
        if val:
            try:
                dt = date_parser.parse(val)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                continue
    return datetime.now(timezone.utc)


def _extract_image(entry) -> str | None:
    """Pull a hero image URL from common feed locations."""
    try:
        if hasattr(entry, 'media_content') and entry.media_content:
            return entry.media_content[0].get('url')
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            return entry.media_thumbnail[0].get('url')
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enc in entry.enclosures:
                if enc.get('type', '').startswith('image'):
                    return enc.get('href')
        if hasattr(entry, 'links'):
            for link in entry.links:
                if link.get('type', '').startswith('image'):
                    return link.get('href')
    except Exception:
        pass
    return None


def _extract_summary(entry) -> str:
    """Get the cleanest summary text we can."""
    for attr in ('summary', 'description', 'subtitle'):
        try:
            val = getattr(entry, attr, '') or (entry.get(attr) if hasattr(entry, 'get') else '')
            if val:
                # Strip basic HTML
                import re as _re
                clean = _re.sub(r'<[^>]+>', ' ', str(val))
                clean = _re.sub(r'\s+', ' ', clean).strip()
                if clean:
                    return clean[:2000]
        except Exception:
            continue
    return ''


def fetch_rss(source: dict, max_items: int = 25) -> list[Story]:
    """Fetch and normalize an RSS feed into Story objects.

    Returns empty list on failure (logs warning, doesn't raise).
    """
    url = source['url']
    try:
        feed = feedparser.parse(url, agent=USER_AGENT)
        if feed.bozo and not feed.entries:
            logger.warning(f"[{source['id']}] feed parse failed: {feed.bozo_exception}")
            return []

        stories: list[Story] = []
        for entry in feed.entries[:max_items]:
            try:
                title = (getattr(entry, 'title', '') or '').strip()
                link = (getattr(entry, 'link', '') or '').strip()
                if not title or not link:
                    continue
                stories.append(Story(
                    source_id=source['id'],
                    source_name=source['name'],
                    url=link,
                    title=title,
                    summary=_extract_summary(entry),
                    published=_parse_date(entry),
                    category_hint=source.get('category_hint', 'funding'),
                    weight=source.get('weight', 5),
                    image_url=_extract_image(entry),
                ))
            except Exception as e:
                logger.warning(f"[{source['id']}] entry parse failed: {e}")
                continue

        logger.info(f"[{source['id']}] fetched {len(stories)} items")
        return stories
    except Exception as e:
        logger.error(f"[{source['id']}] fatal fetch error: {e}")
        return []
