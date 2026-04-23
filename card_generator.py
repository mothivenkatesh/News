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
import re
import json
import logging
import requests
from datetime import datetime, timezone
from difflib import SequenceMatcher
from models import Story, Card, CATEGORIES
from dedup import story_id
from html_scrapers import fetch_og_image

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))  # 5 min per call
OLLAMA_TEMP = float(os.getenv("OLLAMA_TEMP", "0.3"))  # lower = more consistent editorial voice
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
# Diversity caps — prevent one source/category from dominating the feed
MAX_PER_SOURCE = int(os.getenv("MAX_PER_SOURCE", "2"))
MAX_PER_CATEGORY = int(os.getenv("MAX_PER_CATEGORY", "3"))
# Fuzzy headline dedup threshold — post-LLM. 0=off, 1.0=exact match only. 0.7 catches
# the "RBI's draft PPI norms..." vs "RBI Floats New Draft Rules..." case where the LLM
# normalises both source headlines to nearly identical card headlines.
HEADLINE_DEDUP_THRESHOLD = float(os.getenv("HEADLINE_DEDUP_THRESHOLD", "0.7"))


SYSTEM_PROMPT = """You are the editorial brain behind a fintech news-card product for Indian PAYMENTS and LENDING operators (founders, PMs, compliance heads, payments engineers, risk teams, lending ops). Your job: turn one raw news item into a single 60-word swipeable card that an operator wants to read on their commute.

## Your audience
Indian payments + lending operators. Fluent in: RBI, NPCI, UPI, KYC, NBFC, BBPS, AA, FLDG, CKYC, PA-PG, IRDAI, SEBI, MFI, LSP, BRE, LOS, SHG, JLG, FIU, AML, PMLA, IFSC. Do NOT explain acronyms.

## TOPIC FOCUS (CRITICAL)
This product covers PAYMENTS and LENDING in India. Score on-topic stories normally. Score OFF-TOPIC stories at importance 1-2 (so they get filtered out).

ON-TOPIC (score normally):
- Payments: PA-PG, payment gateways, UPI, IMPS, NEFT, RTGS, NACH, BBPS, AePS, cards (issuing/acquiring/networks), wallets, prepaid (PPI), settlement, MDR, chargebacks, tokenization, cross-border, remittance, switches, payment fraud and AML
- Lending: NBFC, MFI, LSP, FLDG, AA (account aggregator), credit bureau, BNPL, microfinance, gold loan, personal/home/MSME loans, SHG/JLG, co-lending, loan origination (LOS), underwriting, BRE, collections, NPA
- Regulators on the above: RBI master directions on PA-PG / NBFC / lending; NPCI circulars; SEBI on broker-NBFC overlap; FIU on payment-fraud penalties
- Vendors that serve payments/lending: KYC, liveness, BRE, CKYC, document extraction, fraud-detection, collection-tech, switch-as-a-service

OFF-TOPIC (importance 1-2):
- Insurtech, wealthtech, AMC/MF, broking-only stories, gaming
- Generic startup news (e-commerce, SaaS, EVs, climate-tech)
- Macroeconomic plumbing: T-bill auctions, FX reserves, monetary policy minutes, weekly statistical supplements, money market operations
- M&A in non-fintech sectors

## Hard rules
1. Body: 60 words max. Hard cap.
2. Headline: 12 words max. ACTIVE VOICE. Lead with the actor (the company, person, regulator). Include a specific number or named entity from the source if present.
3. Lede (first sentence of body): contains the news itself, not setup. NEVER open with "The RBI published a report on..." or "X has announced...". Open with what was decided / changed / launched / shipped.
4. No filler. Banned: "interestingly", "in a major development", "it is worth noting", "notably", "this comes amid".
5. Operator-newsroom tone. Direct, factual, slightly punchy. No marketing voice, no hype.
6. One verb per claim. "Razorpay plans IPO" beats "Razorpay reportedly aims to potentially file".
7. Cite specific numbers, names, dates that appear in the source. They make cards swipe-worthy.
8. CRITICAL: NEVER invent numbers, names, or facts. Only cite what appears in the source. If a number isn't in the source, leave it out.

## Headline examples (study)
WEAK:  "RBI Releases Weekly Statistical Supplement Data on Reserves and Deposits"
GOOD:  "RBI weekly stats: forex reserves and bank deposit data published" (importance 1, off-topic)

WEAK:  "Kiwi co-founder Mohit Bedi steps down"
GOOD:  "Kiwi co-founder Mohit Bedi exits credit-card-on-UPI startup"

WEAK:  "RBI Floats New Draft Rules To Govern Prepaid Payment Instruments"
GOOD:  "RBI drafts new PPI master direction; feedback open till May 22"

WEAK:  "Tata Digital cuts 250 jobs to improve efficiencies"
GOOD:  "Tata Digital lays off 250, shrinks workforce to ~1,000"

WEAK:  "Razorpay plans confidential IPO filing"
GOOD:  "Razorpay files confidential DRHP, eyes $700M raise at $5B valuation"

## Categories: pick exactly ONE
- rbi: RBI circulars, master directions, press releases, governor speeches, license cancellations
- npci: NPCI circulars, UPI/IMPS/NACH operational changes, statistics
- sebi: SEBI circulars, broker/AMC actions, market structure
- irdai: IRDAI circulars, insurance broker actions
- funding: Fintech startup funding, IPO filings, M&A, ESOPs, valuations, ownership changes
- personnel: CXO moves at fintechs/banks/NBFCs, RBI MD approvals, departures, board changes
- fraud: Specific fraud patterns, scam alerts, FIU penalties, money-laundering busts
- vendor: Vendor product launches, API releases, B2B fintech tools
- operator: LinkedIn/Substack commentary, opinion posts, podcasts, deep analyses

The 'category_hint' from the source is just a hint. Override if the actual story fits another category better.

## Importance scoring (1-10)
- 10: Major payments/lending regulator action (PA-PG framework, new NBFC master direction). License event for top-10 payments/lending firm. Major payments/lending fintech IPO.
- 8-9: Notable payments/lending circular requiring operational change. 100Cr+ funding in payments/lending. CXO move at top-20 payments/lending firm.
- 6-7: Mid-tier payments/lending funding. Notable operator commentary. Major payments/lending vendor product launch. RBI-approved bank MD.
- 4-5: Standard payments/lending funding announcement. Smaller-firm personnel move in payments/lending. Generic payments/lending vendor PR.
- 1-3: OFF-TOPIC (insurtech/wealthtech/gaming/general business). Routine money-market ops (auctions, weekly data, T-bill results). Vague headlines. Marketing fluff.

## Breaking flag
True ONLY if BOTH:
(a) Published in last 24h, AND
(b) Payments/lending regulator action requiring immediate compliance attention, OR market-moving payments/lending funding/M&A leak/IPO filing
Default: false.

## why_it_matters
ONE sentence, 20 words max. Frame as "who this affects + why they should care". Be honest: if it doesn't affect payments/lending operators, say so plainly.

## Output
Return ONLY a single JSON object. No prose, no markdown fence, no explanation. Keys: headline, body, category, importance, why_it_matters, breaking."""


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

        # Image: prefer the one captured by the fetcher, otherwise fall back to OG image
        image_url = story.image_url
        if not image_url:
            image_url = fetch_og_image(story.url)

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
            image_url=image_url,
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


def _normalize_headline(h: str) -> str:
    """For similarity matching: lowercase, strip punctuation, collapse whitespace."""
    if not h:
        return ''
    h = re.sub(r'[^\w\s]', ' ', h.lower())
    h = re.sub(r'\s+', ' ', h).strip()
    return h


def dedup_similar_headlines(cards: list[Card], threshold: float = HEADLINE_DEDUP_THRESHOLD) -> list[Card]:
    """Drop cards whose headline is too similar to a higher-importance card already kept.

    The LLM often collapses two source headlines for the same story into nearly identical
    text (e.g. "RBI drafts new PPI master direction" coming from both ET BFSI and Inc42).
    URL + source-title-hash dedup misses these because the source headlines differ; this
    layer catches them on the LLM-generated card headline.
    """
    if not cards or threshold <= 0:
        return cards
    # Sort by importance desc, then recency desc: highest-importance survives ties
    sorted_cards = sorted(
        cards,
        key=lambda c: (-c.importance, -datetime.fromisoformat(c.published_at).timestamp()),
    )
    kept: list[Card] = []
    kept_norms: list[str] = []
    for card in sorted_cards:
        norm = _normalize_headline(card.headline)
        is_dup = False
        for prev_norm in kept_norms:
            ratio = SequenceMatcher(None, norm, prev_norm).ratio()
            if ratio >= threshold:
                logger.info(
                    f"fuzzy-dedup: dropped '{card.headline[:60]}' "
                    f"(similarity {ratio:.2f} >= {threshold:.2f} to a kept card)"
                )
                is_dup = True
                break
        if not is_dup:
            kept.append(card)
            kept_norms.append(norm)
    return kept


def select_diverse(
    stories: list[Story],
    max_total: int,
    per_source: int = MAX_PER_SOURCE,
    per_category: int = MAX_PER_CATEGORY,
) -> list[Story]:
    """Pick up to max_total stories with both source and category-hint diversity caps.

    Pass 1: respect both caps strictly (no source > per_source, no category > per_category).
    Pass 2: if under quota, fill from remaining stories ignoring caps.

    Within each pass, selection order is by (weight desc, recency desc).
    """
    if not stories:
        return []
    sorted_stories = sorted(
        stories,
        key=lambda s: (-s.weight, -s.published.timestamp()),
    )
    selected: list[Story] = []
    selected_urls: set[str] = set()
    source_counts: dict[str, int] = {}
    cat_counts: dict[str, int] = {}

    # Pass 1: diversity-respecting
    for s in sorted_stories:
        if len(selected) >= max_total:
            break
        if source_counts.get(s.source_id, 0) >= per_source:
            continue
        if cat_counts.get(s.category_hint, 0) >= per_category:
            continue
        selected.append(s)
        selected_urls.add(s.url)
        source_counts[s.source_id] = source_counts.get(s.source_id, 0) + 1
        cat_counts[s.category_hint] = cat_counts.get(s.category_hint, 0) + 1

    # Pass 2: fill remainder if we hit caps before max_total
    if len(selected) < max_total:
        for s in sorted_stories:
            if len(selected) >= max_total:
                break
            if s.url in selected_urls:
                continue
            selected.append(s)
            selected_urls.add(s.url)

    return selected


def generate_cards(stories: list[Story], max_cards: int = 30) -> list[Card]:
    """Generate cards for stories with diversity-aware selection.

    Returns list sorted by importance desc.
    """
    if not stories:
        return []
    selected_stories = select_diverse(stories, max_total=max_cards)
    logger.info(
        f"select_diverse picked {len(selected_stories)} stories "
        f"(per_source={MAX_PER_SOURCE}, per_category={MAX_PER_CATEGORY})"
    )
    # Log the source/category mix being sent to LLM
    src_mix: dict[str, int] = {}
    cat_mix: dict[str, int] = {}
    for s in selected_stories:
        src_mix[s.source_name] = src_mix.get(s.source_name, 0) + 1
        cat_mix[s.category_hint] = cat_mix.get(s.category_hint, 0) + 1
    logger.info(f"  by source: {dict(sorted(src_mix.items(), key=lambda x: -x[1]))}")
    logger.info(f"  by category-hint: {dict(sorted(cat_mix.items(), key=lambda x: -x[1]))}")

    cards: list[Card] = []
    for i, story in enumerate(selected_stories, 1):
        card = generate_card(story)
        if card:
            cards.append(card)
        status = "OK  " if card else "FAIL"
        logger.info(f"[{i:>2}/{len(selected_stories)}] {status} | {story.source_name[:25]:<25} | {story.title[:60]}")

    # Post-LLM: fuzzy dedup on generated headlines (catches LLM-collapsed duplicates)
    before = len(cards)
    cards = dedup_similar_headlines(cards)
    after = len(cards)
    if before != after:
        logger.info(f"fuzzy-dedup: {before} -> {after} cards ({before - after} duplicate(s) removed)")

    cards.sort(key=lambda c: (-c.importance, -datetime.fromisoformat(c.published_at).timestamp()))
    return cards
