"""LLM card generator using Ollama (local, free).

Defaults to gemma4:e4b but override via OLLAMA_MODEL env var.
Uses Ollama's structured output (format=json-schema, supported in Ollama >=0.5)
for typed Card output — same shape we used to get from Claude's strict tool-use.

Why this design:
- No API costs. Runs entirely on your machine.
- No prompt cache (Ollama doesn't have one), but no per-token cost either.
- JSON schema constraint forces Gemma to emit a parseable object — Gemma 4 follows
  schema constraints reliably, so we don't need a retry loop for malformed JSON.
"""
from __future__ import annotations
import os
import json
import logging
import requests
from datetime import datetime, timezone
from models import Story, Card, CATEGORIES
from dedup import story_id

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))  # 5 min per call
OLLAMA_TEMP = float(os.getenv("OLLAMA_TEMP", "0.3"))  # lower = more consistent editorial voice
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "8192"))


SYSTEM_PROMPT = """You are the editorial brain behind a fintech news-card product for Indian fintech operators (founders, PMs, compliance heads, payments engineers, risk teams). Your job: turn one raw news item into a single 60-word card.

## Your audience
Indian fintech operators. They are already fluent in: RBI, NPCI, UPI, KYC, NBFC, BBPS, AA, FLDG, CKYC, PA-PG, IRDAI, SEBI, MFI, LSP, BRE, LOS, SHG, JLG, FIU, AML, PMLA, IFSC. Do NOT explain these acronyms. Do NOT define what UPI is. Skip consumer-finance basics.

## Hard rules
1. Body: maximum 60 words. Hard cap.
2. Headline: maximum 12 words. Declarative. No clickbait. No questions. No "here's why" / "here's what".
3. No filler ("interestingly", "in a major development", "it is worth noting").
4. No marketing voice. Operator-newsroom tone — direct, factual, slightly dry.
5. If the input is vague, low-substance, or pure PR fluff, score importance 1-3.
6. Avoid hedge soup. Pick one verb. "Razorpay plans IPO" not "Razorpay reportedly aims to potentially file".
7. If the source is a regulator PDF, lead with WHAT changed and FOR WHOM. Not "RBI released a circular today on..."

## Categories — pick exactly ONE
- rbi: RBI circulars, master directions, press releases, governor speeches, license cancellations
- npci: NPCI circulars, UPI/IMPS/NACH operational changes, statistics, NPCI personnel actions
- sebi: SEBI circulars, broker/AMC actions, market structure changes
- irdai: IRDAI circulars, insurance broker actions, IRDAI personnel
- funding: Fintech startup funding, IPO filings, M&A, ESOPs, valuations, ownership changes
- personnel: CXO moves at fintechs/banks/NBFCs, RBI MD approvals, departures, board changes (NOT regulator policy)
- fraud: Specific fraud patterns, scam alerts, FIU penalties, money-laundering busts, mule networks
- vendor: Vendor product launches, API releases, partnerships, B2B fintech tool intel (KYC, BRE, liveness, CKYC providers, document extraction, etc.)
- operator: Operator/influencer commentary, opinion posts, podcasts, deep analyses (LinkedIn, Substack)

The 'category_hint' from the source is just a hint. Override if the actual story fits another category better.

## Importance scoring (1-10)
- 10: Major regulator action that changes how operators work (PA-PG framework, new master direction). License grant/revocation to a top-10 firm. Major fintech IPO filing.
- 8-9: Notable circular requiring operational change. 100Cr+ funding round. CXO move at a top-20 fintech.
- 6-7: Mid-tier fintech funding. Noteworthy operator commentary. New product launch from a major vendor. RBI-approved bank MD appointment.
- 4-5: Standard funding announcement. Personnel move at smaller firm. Generic vendor PR.
- 1-3: Vague headline, marketing fluff, listicle, no operational substance.

## Breaking flag
True ONLY if BOTH conditions hold:
(a) Published in last 24h, AND
(b) Either a regulator action requiring immediate compliance attention, OR a market-moving funding/M&A leak/IPO filing
Default: false.

## why_it_matters
ONE sentence (maximum 20 words). Frame: "Who this affects + why they should care."

## Output
Return ONLY a single JSON object matching the required schema. No prose, no markdown fence, no explanation. The JSON must have these exact keys: headline, body, category, importance, why_it_matters, breaking."""


CARD_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "body": {"type": "string"},
        "category": {"type": "string", "enum": CATEGORIES},
        "importance": {"type": "integer", "minimum": 1, "maximum": 10},
        "why_it_matters": {"type": "string"},
        "breaking": {"type": "boolean"},
    },
    "required": ["headline", "body", "category", "importance", "why_it_matters", "breaking"],
}


def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return ' '.join(words[:max_words])


def _build_user_prompt(story: Story) -> str:
    age_hours = max(
        0,
        (datetime.now(timezone.utc) - story.published).total_seconds() / 3600,
    )
    return f"""SOURCE: {story.source_name}
URL: {story.url}
PUBLISHED: {story.published.strftime('%Y-%m-%d %H:%M UTC')} (~{age_hours:.0f}h ago)
CATEGORY HINT: {story.category_hint}
HEADLINE: {story.title}

CONTENT:
{(story.summary or '').strip()[:1800]}

Return the JSON card."""


def ollama_health() -> tuple[bool, str]:
    """Check Ollama is reachable and the configured model is pulled."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m.get('name', '') for m in r.json().get('models', [])]
        if OLLAMA_MODEL in models or any(m.startswith(OLLAMA_MODEL.split(':')[0]) for m in models):
            return True, f"OK — {len(models)} models installed, target '{OLLAMA_MODEL}' available"
        return False, (
            f"Ollama is up but model '{OLLAMA_MODEL}' is not pulled. "
            f"Run: ollama pull {OLLAMA_MODEL}\n"
            f"Available: {', '.join(models) or '(none)'}"
        )
    except requests.exceptions.ConnectionError:
        return False, f"Cannot reach Ollama at {OLLAMA_BASE_URL}. Start it with: ollama serve"
    except Exception as e:
        return False, f"Ollama health check failed: {e}"


def generate_card(story: Story) -> Card | None:
    """Convert one Story to one Card via Ollama. Returns None on failure (logs)."""
    user_prompt = _build_user_prompt(story)
    try:
        r = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "format": CARD_SCHEMA,  # Ollama enforces this JSON schema on the response
                "stream": False,
                "options": {
                    "temperature": OLLAMA_TEMP,
                    "num_ctx": OLLAMA_NUM_CTX,
                },
            },
            timeout=OLLAMA_TIMEOUT,
        )
        r.raise_for_status()
        payload = r.json()
        content = payload.get("message", {}).get("content", "").strip()
        if not content:
            logger.warning(f"Empty response for '{story.title[:60]}'")
            return None

        # The format=schema constraint guarantees content is a JSON string
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Defensive fallback: try to extract JSON from a fenced block
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if not match:
                logger.warning(f"Non-JSON response for '{story.title[:60]}': {content[:200]}")
                return None
            data = json.loads(match.group(0))

        # Validate required keys present
        for key in ("headline", "body", "category", "importance", "why_it_matters", "breaking"):
            if key not in data:
                logger.warning(f"Missing key '{key}' for '{story.title[:60]}'")
                return None
        if data["category"] not in CATEGORIES:
            logger.warning(f"Invalid category '{data['category']}' for '{story.title[:60]}', defaulting to hint")
            data["category"] = story.category_hint if story.category_hint in CATEGORIES else 'funding'

        body = _truncate_words(str(data["body"]), 60)
        return Card(
            id=story_id(story.url, story.title),
            headline=str(data["headline"]).strip(),
            body=body.strip(),
            category=data["category"],
            source_name=story.source_name,
            source_url=story.url,
            published_at=story.published.isoformat(),
            fetched_at=datetime.now(timezone.utc).isoformat(),
            importance=int(data["importance"]),
            image_url=story.image_url,
            breaking=bool(data["breaking"]),
            why_it_matters=str(data["why_it_matters"]).strip(),
        )
    except requests.exceptions.Timeout:
        logger.error(f"Ollama timeout (>{OLLAMA_TIMEOUT}s) for '{story.title[:60]}'")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Lost connection to Ollama at {OLLAMA_BASE_URL}")
        raise
    except Exception as e:
        logger.error(f"Card generation failed for '{story.title[:60]}': {e}")
        return None


def generate_cards(stories: list[Story], max_cards: int = 30) -> list[Card]:
    """Generate cards for stories. Returns list sorted by importance desc."""
    if not stories:
        return []
    sorted_stories = sorted(
        stories,
        key=lambda s: (-s.weight, -s.published.timestamp()),
    )[:max_cards]

    cards: list[Card] = []
    for i, story in enumerate(sorted_stories, 1):
        card = generate_card(story)
        if card:
            cards.append(card)
        status = "OK  " if card else "FAIL"
        logger.info(f"[{i:>2}/{len(sorted_stories)}] {status} | {story.source_name[:25]:<25} | {story.title[:60]}")

    cards.sort(key=lambda c: (-c.importance, -datetime.fromisoformat(c.published_at).timestamp()))
    return cards
