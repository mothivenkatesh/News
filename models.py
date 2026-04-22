"""Data models for fintech-inshorts pipeline."""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional


@dataclass
class Story:
    """Raw story fetched from a source, before LLM card generation."""
    source_id: str
    source_name: str
    url: str
    title: str
    summary: str
    published: datetime
    category_hint: str
    weight: int
    image_url: Optional[str] = None
    raw_content: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d['published'] = self.published.isoformat() if self.published else None
        return d


@dataclass
class Card:
    """Final Inshorts-style card ready for the frontend.
    body is HARD-CAPPED at 60 words by the LLM card generator.
    """
    id: str
    headline: str
    body: str
    category: str  # rbi | npci | sebi | irdai | funding | personnel | fraud | vendor | operator
    source_name: str
    source_url: str
    published_at: str
    fetched_at: str
    importance: int  # 1-10
    image_url: Optional[str] = None
    breaking: bool = False
    why_it_matters: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


CATEGORIES = [
    'rbi', 'npci', 'sebi', 'irdai',
    'funding', 'personnel', 'fraud', 'vendor', 'operator',
]

CATEGORY_LABELS = {
    'rbi': 'RBI',
    'npci': 'NPCI',
    'sebi': 'SEBI',
    'irdai': 'IRDAI',
    'funding': 'Funding',
    'personnel': 'Personnel',
    'fraud': 'Fraud',
    'vendor': 'Vendor',
    'operator': 'Operator Take',
}
