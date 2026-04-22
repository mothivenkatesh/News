"""SQLite-based seen-URL + seen-title tracking.

Two-layer dedup:
  1. URL hash — same URL never recarded
  2. Title hash — same normalized title (case/punct-stripped) never recarded
     This catches the Medial-republishes-IndianStartupNews case where the URL
     differs but the story is the same.
"""
from __future__ import annotations
import sqlite3
import hashlib
import re
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).parent / 'data' / 'seen.db'


def _ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS seen (
            id TEXT PRIMARY KEY,
            source_id TEXT,
            url TEXT,
            title TEXT,
            title_hash TEXT,
            first_seen_at TEXT
        )
    ''')
    # Migrate older DBs that lack title_hash
    cols = {row[1] for row in conn.execute('PRAGMA table_info(seen)').fetchall()}
    if 'title_hash' not in cols:
        conn.execute('ALTER TABLE seen ADD COLUMN title_hash TEXT')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_seen_title_hash ON seen(title_hash)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_seen_first_seen ON seen(first_seen_at)')
    conn.commit()
    return conn


def story_id(url: str, title: str) -> str:
    """Stable id for dedup: SHA1 of url (with title fallback)."""
    key = (url or title).strip().lower()
    return hashlib.sha1(key.encode('utf-8')).hexdigest()[:16]


def title_hash(title: str) -> str:
    """Normalized title hash: lowercase, strip punctuation, collapse whitespace."""
    if not title:
        return ''
    norm = re.sub(r'[^\w\s]', ' ', title.lower())
    norm = re.sub(r'\s+', ' ', norm).strip()
    return hashlib.sha1(norm.encode('utf-8')).hexdigest()[:16]


def filter_unseen(stories: list) -> list:
    """Return stories not seen by URL or by normalized title."""
    if not stories:
        return []
    conn = _ensure_db()
    unseen = []
    now = datetime.now(timezone.utc).isoformat()
    try:
        for s in stories:
            sid = story_id(s.url, s.title)
            thash = title_hash(s.title)
            row = conn.execute(
                'SELECT 1 FROM seen WHERE id = ? OR (title_hash IS NOT NULL AND title_hash = ?)',
                (sid, thash),
            ).fetchone()
            if row is None:
                unseen.append(s)
                conn.execute(
                    'INSERT INTO seen (id, source_id, url, title, title_hash, first_seen_at) '
                    'VALUES (?, ?, ?, ?, ?, ?)',
                    (sid, s.source_id, s.url, s.title, thash, now),
                )
        conn.commit()
    finally:
        conn.close()
    return unseen


def stats() -> dict:
    """Quick stats on what's been seen."""
    conn = _ensure_db()
    total = conn.execute('SELECT COUNT(*) FROM seen').fetchone()[0]
    by_source = dict(conn.execute(
        'SELECT source_id, COUNT(*) FROM seen GROUP BY source_id ORDER BY 2 DESC'
    ).fetchall())
    conn.close()
    return {'total_seen': total, 'by_source': by_source}
