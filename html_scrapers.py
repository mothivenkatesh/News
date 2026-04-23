"""HTML scrapers for sources without RSS feeds.

Each scraper takes a source config dict and returns list[Story].
Add new ones to the SCRAPERS dict at the bottom.
"""
from __future__ import annotations
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from dateutil import parser as date_parser
import logging
import re
from urllib.parse import urljoin
from models import Story

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 "
        "fintech-inshorts/0.1"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _safe_get(url: str, timeout: int = 30) -> str | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        return r.text
    except Exception as e:
        logger.error(f"GET failed for {url}: {e}")
        return None


def fetch_og_image(url: str, timeout: int = 6) -> str | None:
    """Fetch the article page and extract <meta property="og:image">.
    Falls back to twitter:image and to the first <img> in <article>. Returns None on failure.
    """
    if not url or not url.startswith(('http://', 'https://')):
        return None
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'lxml')

        # 1. Open Graph image (most reliable)
        meta = soup.find('meta', property='og:image') or soup.find('meta', attrs={'property': 'og:image'})
        if meta and meta.get('content'):
            return meta['content'].strip()

        # 2. Twitter card image
        meta = soup.find('meta', attrs={'name': 'twitter:image'}) or soup.find('meta', attrs={'name': 'twitter:image:src'})
        if meta and meta.get('content'):
            return meta['content'].strip()

        # 3. First image in <article> tag
        article = soup.find('article')
        if article:
            img = article.find('img', src=True)
            if img:
                src = img['src']
                if not src.startswith('http'):
                    src = urljoin(url, src)
                return src
        return None
    except Exception as e:
        logger.debug(f"OG image fetch failed for {url}: {e}")
        return None


def _make_story(source: dict, title: str, link: str, published: datetime, summary: str = "") -> Story:
    return Story(
        source_id=source['id'],
        source_name=source['name'],
        url=link,
        title=title.strip(),
        summary=summary.strip()[:2000],
        published=published,
        category_hint=source.get('category_hint', 'funding'),
        weight=source.get('weight', 5),
    )


def _parse_date_safe(text: str) -> datetime:
    try:
        dt = date_parser.parse(text, dayfirst=True, fuzzy=True)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)


def scrape_npci(source: dict) -> list[Story]:
    """NPCI circulars page — anchors pointing to PDFs."""
    html = _safe_get(source['url'])
    if not html:
        return []
    soup = BeautifulSoup(html, 'lxml')
    stories: list[Story] = []
    seen = set()

    for link in soup.find_all('a', href=True):
        href = link['href']
        if '.pdf' not in href.lower():
            continue
        title = link.get_text(strip=True)
        if not title or len(title) < 10:
            continue
        full_url = urljoin(source['url'], href)
        if full_url in seen:
            continue
        seen.add(full_url)
        parent_text = link.parent.get_text(' ', strip=True) if link.parent else ''
        date_match = re.search(r'(\d{1,2}[\s/-][A-Za-z]+[\s/-]\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}-\d{1,2}-\d{4})', parent_text)
        pub_date = _parse_date_safe(date_match.group(1)) if date_match else datetime.now(timezone.utc)
        stories.append(_make_story(source, title, full_url, pub_date))
        if len(stories) >= 20:
            break

    logger.info(f"[{source['id']}] scraped {len(stories)} items")
    return stories


def scrape_sebi(source: dict) -> list[Story]:
    """SEBI circulars listing page — table-based."""
    html = _safe_get(source['url'])
    if not html:
        return []
    soup = BeautifulSoup(html, 'lxml')
    stories: list[Story] = []
    seen = set()

    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) < 2:
            continue
        link_tag = row.find('a', href=True)
        if not link_tag:
            continue
        title = link_tag.get_text(strip=True)
        if not title or len(title) < 10:
            continue
        href = urljoin(source['url'], link_tag['href'])
        if href in seen:
            continue
        seen.add(href)
        date_text = cells[0].get_text(strip=True)
        pub_date = _parse_date_safe(date_text)
        stories.append(_make_story(source, title, href, pub_date))
        if len(stories) >= 20:
            break

    logger.info(f"[{source['id']}] scraped {len(stories)} items")
    return stories


def scrape_irdai(source: dict) -> list[Story]:
    """IRDAI document detail page (best-effort generic anchor pull)."""
    html = _safe_get(source['url'])
    if not html:
        return []
    soup = BeautifulSoup(html, 'lxml')
    stories: list[Story] = []
    seen = set()

    for link in soup.find_all('a', href=True):
        href = link['href']
        title = link.get_text(strip=True)
        if not title or len(title) < 15:
            continue
        if not any(kw in href.lower() for kw in ['document', 'circular', 'pdf', '.aspx', 'order']):
            continue
        full_url = urljoin(source['url'], href)
        if full_url in seen:
            continue
        seen.add(full_url)
        stories.append(_make_story(source, title, full_url, datetime.now(timezone.utc)))
        if len(stories) >= 15:
            break

    logger.info(f"[{source['id']}] scraped {len(stories)} items")
    return stories


def scrape_generic_blog(source: dict) -> list[Story]:
    """Generic blog scraper — looks for article/post elements."""
    html = _safe_get(source['url'])
    if not html:
        return []
    soup = BeautifulSoup(html, 'lxml')
    stories: list[Story] = []
    seen = set()

    candidates = soup.find_all(['article', 'div'], class_=re.compile(r'post|article|entry', re.I))[:30]
    for c in candidates:
        link_tag = c.find('a', href=True)
        if not link_tag:
            continue
        heading = c.find(['h1', 'h2', 'h3'])
        title = (heading.get_text(strip=True) if heading else '') or link_tag.get_text(strip=True)
        if not title or len(title) < 10:
            continue
        full_url = urljoin(source['url'], link_tag['href'])
        if full_url in seen:
            continue
        seen.add(full_url)
        time_tag = c.find('time')
        if time_tag:
            pub_date = _parse_date_safe(time_tag.get('datetime', '') or time_tag.get_text(strip=True))
        else:
            pub_date = datetime.now(timezone.utc)
        summary_tag = c.find('p')
        summary = summary_tag.get_text(strip=True) if summary_tag else ''
        stories.append(_make_story(source, title, full_url, pub_date, summary))
        if len(stories) >= 15:
            break

    logger.info(f"[{source['id']}] scraped {len(stories)} items")
    return stories


def scrape_medial(source: dict) -> list[Story]:
    """Medial news listing — anchor tags pointing to /news/[slug]-[hash]."""
    html = _safe_get(source['url'])
    if not html:
        return []
    soup = BeautifulSoup(html, 'lxml')
    stories: list[Story] = []
    seen = set()

    for link in soup.find_all('a', href=True):
        href = link['href']
        if '/news/' not in href:
            continue
        # Skip the listing page itself and source/category subpages
        path = href.rstrip('/').rsplit('/', 1)[-1]
        if path == 'news' or '/source/' in href or '/category/' in href:
            continue
        full_url = urljoin(source['url'], href)
        if full_url in seen:
            continue
        seen.add(full_url)

        # Title: prefer headline element, fallback to anchor text
        title = ''
        for tag in ('h1', 'h2', 'h3', 'h4'):
            h = link.find(tag)
            if h:
                title = h.get_text(strip=True)
                break
        if not title:
            title = link.get_text(' ', strip=True)
        # Strip Medial's "Source · 2d ago" suffix that gets concatenated into anchor text
        title = re.sub(r'\s+(IndianStartupNews|Medial)\s+\d+[dhm]\s+ago.*$', '', title)
        title = re.sub(r'\s+\d+[dhm]\s+ago.*$', '', title)
        title = title.strip()

        if not title or len(title) < 15:
            continue

        img = link.find('img')
        image_url = img.get('src') if img and img.get('src') else None
        if image_url and not image_url.startswith('http'):
            image_url = urljoin(source['url'], image_url)

        story = _make_story(source, title, full_url, datetime.now(timezone.utc))
        story.image_url = image_url
        stories.append(story)
        if len(stories) >= 25:
            break

    logger.info(f"[{source['id']}] scraped {len(stories)} items")
    return stories


SCRAPERS = {
    'npci': scrape_npci,
    'sebi': scrape_sebi,
    'irdai': scrape_irdai,
    'medial': scrape_medial,
    'generic_blog': scrape_generic_blog,
}


def fetch_html(source: dict) -> list[Story]:
    """Dispatch to the right scraper based on source['scraper']."""
    scraper_name = source.get('scraper', 'generic_blog')
    scraper = SCRAPERS.get(scraper_name, scrape_generic_blog)
    return scraper(source)
