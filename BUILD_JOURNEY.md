# Build Journey: from "research medial.app/news" to shipped MVP

> **A chronological log of what we tried, what worked, what we threw away, and what shipped. Companion to `PRD.md` (which is the static spec). This doc is the story.**

| Field | Value |
|---|---|
| Owner | Mothi Venkatesh |
| Repo | https://github.com/mothivenkatesh/News |
| Built in | One conversation session |
| Final state | v1.1 shipped, 9-card live feed, ₹0 LLM cost |
| Lines of code | ~1,500 (Python + HTML/CSS/JS) |
| Lines of docs | ~5,000 (PRD + README + this) |

---

## TL;DR

Started with: *"research the medial.app/news feature."*
Ended with: a working Inshorts-for-BFSI MVP — 21 sources, local Ollama summariser, 9 categories, swipeable web frontend, payments+lending focused, deployed to GitHub.

Three pivots in one session:
1. Discovery → "Inshorts for fintech" product spec
2. Claude API → local Ollama (₹18K/yr → ₹0)
3. v1.0 (one-source-dominates feed) → v1.1 (diversity + topic focus + engagement)

---

## Phase 0: The starting brief

> *"https://medial.app/news imagine you're medial's product manager, do deep research on startup news feature, one thing i'm sure of is all the articles are AI generated."*

Pure discovery brief. No product to build yet — just understand the space.

---

## Phase 1: Medial teardown (what we found)

| Question | Finding |
|---|---|
| Is it AI-generated? | **Yes, confirmed.** Sampled 3 articles (Razorpay IPO, OpenAI CTO resignation, Tata Digital). All ~85-95 words, zero direct quotes, zero named human sources, classic LLM summarization signature. |
| Where does the content come from? | **IndianStartupNews** (a separate company, not Medial). Every front-page article links to `indianstartupnews.com/news/...` via the "View Source" button. |
| What's the funnel? | News articles (SEO entry) → "Download the medial app" interstitial → install → community feed → Premium tier (₹89-1,499 across 3 SKUs). News is top-of-funnel for a community + jobs business. |
| Strategic risk | **Single-source dependency.** ISN can cease-and-desist tomorrow. Also: "View Source" link leaks every paid-acquired user back to the competitor's domain. |
| Funding context | $677K raised total (FirstCheque pre-seed, OG Capital pre-Series A, Shark Tank India). Reportedly in talks for $5M from OG Capital per Inc42. |

**The PMM lens:** Medial is a content arbitrage play with no editorial moat. The 90-day fix would be: diversify sources, ship a "Discuss this on Medial" CTA to convert outbound clicks into community posts, and disclose AI summarization proactively.

---

## Phase 2: Finshots comparison

User asked: *"also research finshots."*

| Dimension | Medial | Finshots |
|---|---|---|
| Content engine | AI-summarized aggregation, 50/day | Human-written, 1/day |
| Voice | None | Distinct, conversational |
| Defensibility | Low | High (7-yr brand compounding) |
| Monetization | Premium subs (₹89-1,499) | Ditto Insurance (70% of buyers come via Finshots) |
| Time to traction | Fast | Slow |

**The framework that emerged:** two opposite archetypes. Choose one, can't be both.

---

## Phase 3: User research via WhatsApp

User dropped 3 WhatsApp chat exports mid-conversation:
- FinPro Bangalore (77KB, 41 regulatory hits)
- IFF Payment & Lending (183KB, 263 reg hits, 268 lending hits)
- WTFraud Fintech Forum (183KB, 244 reg hits, 99 fraud hits)

We extracted, grepped for URLs + question patterns + topic keywords. Found:

### What gets shared (sorted by frequency)
1. **Operator commentary on LinkedIn** (not press articles!) — Sushil Kurri, Sushant Patekar, Jitendra Khorwal posts shared 5x more than ETBFSI
2. **RBI primary documents** — direct PDF links to circulars
3. **ETBFSI / BusinessLine / Government ETNow** — regulatory-trigger and personnel-change stories
4. **Vendor product docs** (yes — Cashfree fraud-risk indicator was actively shared)
5. **Job postings** (heavy across all 3 channels)
6. **Event invites** (Luma)
7. **Niche operational updates** — CKYC SFTP changes, BBPS COU pagination, DLA reporting on RBI CIMS portal — *zero outlets cover these*

### What does NOT get shared
- Inc42 / Entrackr funding roundups (operators see them as press-release-y)
- YourStory listicles
- Generic "Top 10 fintech trends 2026"
- Finshots-style consumer-finance explainers (wrong audience)

### What they ASK ("anyone know" pattern)
Sample questions from the actual chats:
- "How do you generate 160-series numbers from TRAI for NBFC/Fintech?"
- "Anyone implemented the recent CKYC algorithm update?"
- "Anyone done DLA reporting on the RBI CIMS portal?"
- "Vendors for liveness checks — active SDK and passive?"
- "Anyone using AI/xAI-powered underwriting for credit decisioning, CAM generation, BRE setup?"

### Implication for the product
The audience is **not consuming-news**, they are **decoding-regulator + tracking-peer-moves + scouting-vendors**. Product must specialise in:
- 40% Plain-English regulator decode
- 15% License & enforcement tracking
- 15% Fraud patterns
- 10% Personnel moves
- 10% Vendor / tool intel
- 10% Operator commentary curation

---

## Phase 4: Source taxonomy (researched, mapped)

Built a tier-by-tier source matrix covering:

**Mainstream BFSI press (tier-1):** ET BFSI, Mint, Business Standard, BusinessLine, Financial Express, MoneyControl, CNBC TV18, NDTV Profit
**Pure fintech press:** Inc42, Entrackr, The Ken, The Morning Context, YourStory
**Specialty BFSI/payments:** Banking Frontiers, IBS Intelligence, Finextra, MoneyLife, Cafemutual
**Regulators (the spine):** RBI, NPCI, SEBI, IRDAI, FIU-IND, MeitY, MCA, CKYC, NeSL, IFSCA, mmdpc.in (NBFC tracker)
**Operator-creators:** LinkedIn 30-creator list, Tigerfeathers, podcast transcripts, X/Twitter 50-handle list

**Mapped each source to the 6 content buckets** + scrape mechanics (RSS available? Paywalled? Crawlable?) + WhatsApp-validation (does the audience actually share it?).

---

## Phase 5: The pivot — "Inshorts for BFSI"

User dropped mid-research:
> *"imagine you're building inshorts for BFSI/Fintech."*

This changed the output shape entirely:

| Layer | Original plan | Pivot |
|---|---|---|
| Output unit | 600-word daily explainer | Hard 60-word card |
| UX | Newsletter / blog | Vertical swipe deck |
| Source ingestion | Same | Same |
| Distribution | Email + Substack | Web app → WhatsApp/Telegram cards → email digest as archive |
| Frequency | Daily | Continuous |
| Categories | Topic mix in one piece | Tabs: 9 fixed buckets |

**What stayed:** the source mix, the editorial voice rules, the operator-focus framing.
**What changed:** output format → swipeable cards. The orchestrator + LLM module had to rebuild around a hard word count.

---

## Phase 6: v1.0 architecture decisions

### Stack chosen

| Layer | Choice | Rejected alternatives | Why |
|---|---|---|---|
| Backend | Python 3.10+ | Node, Go | User's existing scraper skills are Python (Scrapling-based) |
| RSS parser | feedparser | Manual XML, lxml | Battle-tested, handles bozo feeds gracefully |
| HTML scrapers | requests + bs4 + lxml | Scrapling | Simpler for v1; can swap to Scrapling later for bot-detected sources |
| Dedup store | SQLite | Redis, Postgres | Single-file, no daemon, lives next to code |
| LLM (initial) | Anthropic Claude Sonnet 4.5 | OpenAI, local | Best instruction-following at the time |
| LLM (final) | Ollama gemma4:e4b | Cloud APIs | User explicit pivot for ₹0 cost |
| Frontend | Vanilla HTML/CSS/JS | Next.js, React, Vue | No build step, no deps, ships as static |
| Dedup strategy | URL hash + title hash | content-hash, fuzzy match | Two-layer was enough for Medial-vs-ISN problem |

### Rejected alternatives (and why)

- **Mobile native app first** — Web is enough for MVP. Build mobile when distribution is proven.
- **User accounts + bookmarks** — Not in v1. Cards are the same for everyone.
- **Push notifications** — Not in v1. Manual share button instead.
- **Original journalism** — Out of scope. We aggregate + decode, not report.
- **Multilingual** — English only; the audience is English-fluent.
- **WhatsApp / Telegram broadcast** — Phase 2.

---

## Phase 7: Build sequence (file-by-file)

What was built, in order:

1. **`models.py`** — `Story` and `Card` dataclasses, 9 fixed categories
2. **`sources.yaml`** — 21 sources with weights + category hints
3. **`rss_fetcher.py`** — generic RSS/Atom fetcher (feedparser)
4. **`html_scrapers.py`** — NPCI, SEBI, IRDAI, generic blog scrapers
5. **`dedup.py`** — SQLite seen-URL store
6. **`card_generator.py`** — initially Anthropic SDK with strict tool-use, later rewritten for Ollama
7. **`build_cards.py`** — orchestrator: health-check → fetch → dedup → LLM → write JSON
8. **`web/index.html` + `app.js` + `styles.css`** — Inshorts-style swipeable deck
9. **`test_fetch.py`** — smoke test (no LLM/API key needed)

Total: ~1,500 LOC. No build step. Ship as static.

### Source registry (21 sources)

Working on first run: **11/19** (then 13/21 after adding Medial + ISN). Broken cluster identified: financial press (LiveMint, BS, FE, MoneyControl, MoneyLife, Cafemutual) returning HTML instead of XML — bot detection. Fixable with Scrapling browser fingerprint, deferred to v1.2.

---

## Phase 8: First successful run

5/5 cards generated, ~54s/card, 100% LLM success. Top card was **RBI's PPI Master Direction draft** — model correctly:
- Caught the **May 22 feedback deadline** in the source
- Flagged it `breaking: true`
- Scored it 10/10
- Framed `why_it_matters` as *"All PPI operators must review the draft guidelines as they signal significant changes to operational compliance and risk management."*

Bottom card (Reserve Money week-end data) correctly scored 1/10 — the model didn't over-weight every RBI press release just because the source weight was 10.

---

## Phase 9: User-driven iterations

### Iteration A: Add Medial + IndianStartupNews

User: *"include this https://medial.app/news/paytm-finally-becomes-majority-indian-owned-... where the original source is https://indianstartupnews.com/news/...."*

Implementation:
- Verified ISN RSS works at `/rss` (not `/feed` — 404)
- Verified Medial has no RSS — built `scrape_medial()` for `medial.app/news` listings
- **New problem:** Medial republishes ISN. Different URLs, same content. URL-only dedup fails.
- **Solution:** Two-layer dedup. Added `title_hash()` (lowercase, strip punctuation, collapse whitespace, SHA1). A story is "new" only if BOTH `id` and `title_hash` are absent.
- Schema migration: auto-`ALTER TABLE` on startup so existing `seen.db` survives the column add.

### Iteration B: Switch to Ollama

User: *"use ollama gemma4 setup instead of paid llm models."*

Implementation:
- Removed `anthropic` from requirements.txt
- Rewrote `card_generator.py` from `client.messages.create(...)` to `requests.post(/api/chat, format=schema)`
- Used Ollama's JSON-schema constraint instead of Claude's strict tool-use — works on any 4.x model
- Ollama health check: pre-flight `GET /api/tags`, abort if unreachable or model missing
- Defensive JSON parsing (regex-extract fallback if direct parse fails)

**Cost impact:** ~₹18K/year → ₹0/year. Quality trade-off: Gemma 4 is slightly less crisp than Sonnet 4.5 on importance scoring, but the JSON schema constraint forces reliable structured output. Acceptable for MVP.

**Speed:** ~50s per card on M1/RTX-tier hardware (vs ~3s for Claude). Acceptable for daily batch.

---

## Phase 10: First "production" runs

| Run | CARDS_PER_RUN | Outcome | Issue |
|---|---|---|---|
| #1 | 5 | 5/5 cards from 1 source (RBI Press Releases) | All-RBI-treasury feed |
| #2 | 10 | 10/10 cards from 1 source (RBI Press Releases) | Same. Dedup history kept filtering everything else. |

User feedback after seeing the runs:
> *"the News stories has to drive high engagement and it should not list only one type of news, there has to be variety like medial.app/news"*

And:
> *"keep news majorly related to payments & lending"*

This drove v1.1.

---

## Phase 11: v1.1 — variety + engagement + topic focus

Three problems, three fixes (all shipped in one commit).

### Problem 1: One source dominates

**Cause:** Selection was `sorted_stories[:max_cards]` by `(weight desc, recency desc)`. RBI Press Releases at weight 10 with 10 fresh stories took every slot.

**Fix:** New `select_diverse()` function with **per-source cap** (default 2) and **per-category cap** (default 3). Two-pass:
1. Pass 1: respect both caps strictly
2. Pass 2: if under quota, fill from remaining ignoring caps

```python
def select_diverse(stories, max_total, per_source=2, per_category=3):
    sorted_stories = sorted(stories, key=lambda s: (-s.weight, -s.published.timestamp()))
    selected, source_counts, cat_counts = [], {}, {}
    for s in sorted_stories:
        if len(selected) >= max_total: break
        if source_counts.get(s.source_id, 0) >= per_source: continue
        if cat_counts.get(s.category_hint, 0) >= per_category: continue
        selected.append(s)
        source_counts[s.source_id] = source_counts.get(s.source_id, 0) + 1
        cat_counts[s.category_hint] = cat_counts.get(s.category_hint, 0) + 1
    # ... pass 2 fills remainder
```

**Outcome:** Test run picked 6 different sources and 4 different categories.

### Problem 2: Headlines were boring

**Cause:** SYSTEM_PROMPT had restrictions ("no clickbait", "no questions") but no positive guidance on what good looks like.

**Fix:** Rewrote SYSTEM_PROMPT with:
- **Active voice required** — "Lead with the actor (the company, person, regulator)"
- **Lede must contain the news**, not the setup
- **Cite specific numbers/names** from source
- **Banned filler list** ("interestingly", "in a major development", "notably")
- **5 weak-vs-good headline examples** to anchor the style
- **CRITICAL: never invent numbers** — only cite what's in the source

Compare:
- Before: *"RBI Floats New Draft Rules To Govern Prepaid Payment Instruments"*
- After: *"RBI drafts new PPI master direction; feedback open till May 22"*

### Problem 3: No topic focus

**Cause:** SYSTEM_PROMPT covered "fintech" generally. Insurance, gaming, e-commerce, treasury auctions all flowed through.

**Fix:** Explicit ON-TOPIC vs OFF-TOPIC lists in the prompt:

```
ON-TOPIC (score normally):
- Payments: PA-PG, UPI, IMPS, NEFT, RTGS, NACH, BBPS, AePS, cards, wallets,
  prepaid, settlement, MDR, chargebacks, tokenization, cross-border, fraud + AML
- Lending: NBFC, MFI, LSP, FLDG, AA, credit bureau, BNPL, microfinance,
  gold loan, personal/home/MSME loans, SHG/JLG, co-lending, LOS, BRE, NPA
- Regulators on the above
- Vendors that serve payments/lending

OFF-TOPIC (importance 1-2):
- Insurtech, wealthtech, AMC/MF, gaming, broking-only, generic startup news
- Macroeconomic plumbing: T-bill auctions, FX reserves, weekly stat supplements
```

Plus rebalanced source weights:
- ET BFSI 9 → 10 (BFSI-focused)
- Entrackr 8 → 9 (best India fintech leak source)
- mmdpc NBFC tracker 8 → 9 (pure lending signal)
- Finextra 4 → 2 (global, off-topic majority)
- IBS Intelligence 5 → 2 (global)
- IRDAI 8 → 5 (less aligned)
- LiveMint 7 → 5 (general business)

### Bonus 1: OG image fallback

User asked: *"are you able to pull news article cover image?"*

The architecture pulls images from RSS `media_content` / `media_thumbnail` / `enclosures`. Coverage was 7/9 cards. Added:
- New `fetch_og_image(url)` in `html_scrapers.py` — fetches the article URL and extracts `<meta property="og:image">`, falls back to `twitter:image`, then to `<article><img>`
- Hooked into `card_generator.generate_card()` as a fallback when `story.image_url is None`

### Bonus 2: Fuzzy headline dedup

The diversity selector + URL/title-hash dedup didn't catch the case where the LLM **collapses two source headlines for the same story into nearly identical card text** (e.g. PPI Master Direction from ET BFSI vs Inc42 → both ended up as *"RBI drafts new PPI master direction; feedback open till May 22"*).

**Fix:** Post-LLM `dedup_similar_headlines()` using `difflib.SequenceMatcher` (built-in, no deps):

```python
def dedup_similar_headlines(cards, threshold=0.7):
    sorted_cards = sorted(cards, key=lambda c: -c.importance)
    kept, kept_norms = [], []
    for card in sorted_cards:
        norm = _normalize_headline(card.headline)
        if any(SequenceMatcher(None, norm, prev).ratio() >= threshold for prev in kept_norms):
            continue
        kept.append(card)
        kept_norms.append(norm)
    return kept
```

Threshold 0.7 catches obvious dupes (>70% similarity) without false-positives on related-but-different stories from the same actor.

### Bonus 3: Importance threshold

`MIN_IMPORTANCE` env var (default bumped from 3 to 4). Cards below the threshold drop UNLESS the feed would fall under `MIN_FEED_SIZE` (default 5), in which case top-N by importance is kept regardless. Prevents both noise-pollution AND empty-feed days.

---

## Phase 12: Final run results

| Stage | Count |
|---|---|
| Sources fetched | 13 working (out of 21 configured) |
| Stories pulled | 210 |
| New after dedup | 196 |
| Selected by `select_diverse()` | 10 (from 6 sources, 4 categories) |
| LLM cards generated | 10/10 |
| Fuzzy dedup removed | 0 (no near-dupes this run) |
| Met `MIN_IMPORTANCE=4` | 3 (light news day for payments+lending) |
| `MIN_FEED_SIZE=5` floor topped up | +2 |
| **Final feed** | **5 cards** (3 on-topic + 2 off-topic kept by floor) |
| With cover images | 4/5 (80%) |
| Total run time | 8 min 30 sec |
| **Cost** | **₹0** |

**Top card:**
> 🔴 BREAKING · ●●●●● · NPCI · *Indian Startup News · 2h ago*
>
> **NPCI data: PhonePe crosses 10B monthly UPI transactions; Google Pay remains second**
>
> PhonePe processed 10.50 billion UPI transactions in March 2026, becoming the first app to cross the 10B mark. NPCI data shows UPI hit a record 22.64 billion transactions for the month. Google Pay remained second with 7.53 billion transactions, capturing 33.3% of the total volume.
>
> ▍ WHY IT MATTERS — Payments operators must monitor UPI volume trends and market share shifts to optimize their payment strategies.

Real numbers, named entities, operator-perspective framing, swipe-worthy.

---

## Phase 13: Documentation + GitHub

- **PRD.md** — 20 sections, 31 traceable requirement IDs, file-by-file engineering walkthrough, source registry table with status badges, failure-mode recovery table
- **README.md** — quickstart with Ollama setup notes
- **BUILD_JOURNEY.md** — this document
- **GitHub repo** — https://github.com/mothivenkatesh/News (public, main branch)

Two commits:
1. `965f718` — Initial release: fintech-inshorts MVP (17 files)
2. `f9b54a7` — v1.1: feed diversity, payments+lending focus, fuzzy dedup, OG images (5 files, +285/-56)

---

## Decision log (everything we considered and why we chose what we chose)

| Decision | What we picked | Considered | Why |
|---|---|---|---|
| Brand archetype | Operator-newsroom (between Medial aggregator and Finshots single-piece) | Pure aggregator OR pure single-piece | Audience research showed operators want decoded primary docs + curated peer commentary, neither of which the two extremes serve well |
| Editorial voice | Operator-newsroom (direct, factual, slightly punchy) | Conversational (Finshots), deadpan (Reuters) | Audience is professional + time-constrained |
| Output format | 60-word swipeable cards | Long-form daily, newsletter, Twitter threads | User pivot to "Inshorts for BFSI" mid-conversation |
| LLM provider | Ollama gemma4:e4b (local) | Claude Sonnet 4.5 (initially used + working) | User pivot for ₹0 cost; quality trade-off accepted |
| Output structure enforcement | JSON schema constraint (Ollama `format` param) | Tool-use, prompt-only, retry on parse fail | Reliable on Gemma 4, no extra round-trips |
| Dedup | URL-hash + title-hash (two-layer) | URL-only, content-hash | Two-layer catches Medial-vs-ISN; content-hash overkill for MVP |
| Diversity enforcement | Pre-LLM source + category caps | Post-LLM rebalancing | Pre-LLM saves token spend; simpler logic |
| Frontend stack | Vanilla HTML/CSS/JS | Next.js, React, Vue | No build step, no deps, ships as static, ~280 LOC total |
| Dedup library for fuzzy headlines | `difflib.SequenceMatcher` (stdlib) | Levenshtein, FuzzyWuzzy, sentence-transformers | Stdlib = no deps; perfectly adequate for short strings |
| Image fallback | OG meta → Twitter card → first `<article><img>` | Per-source scraping recipes | OG is set on ~99% of news pages for social sharing — universal fallback |
| Off-topic handling | LLM scores 1-2 + post-LLM filter | Pre-LLM keyword blocklist | LLM understands context; keyword blocklist is brittle |

---

## What we tried that didn't make it (and why)

| Attempt | Outcome | Lesson |
|---|---|---|
| `https://www.financialexpress.com/feed/` | Returns HTML, not XML | Bot detection on default UA; defer to Scrapling for v1.2 |
| `https://www.livemint.com/rss/companies` | Returns global Wall Street feed, not India | Wrong feed URL; needs `/rss/banking` or similar |
| Most financial press RSS | Same — bot-detected, served HTML | Cluster fix via Scrapling browser fingerprint |
| `npci.org.in/what-we-do/upi/circular` HTTP scrape | 30s timeout consistently | NPCI is slow; needs longer timeout + retry |
| `mmdpc.in/category/rbi-cancels-nbfcs/` | Cloudflare 525 | Needs Scrapling stealth fetch |
| Per-source-only diversity (without per-category cap) | Worked but allowed all funding | Both caps needed for true variety |
| MIN_IMPORTANCE=3 default | Allowed too many off-topic IRDAI/gaming through | Bumped to 4; MIN_FEED_SIZE=5 floor handles slow days |

---

## What's queued for v1.2

1. **Fix the broken-RSS cluster** (LiveMint correct URL, BS, FE, MoneyControl, MoneyLife) via Scrapling browser fingerprint — adds ~50-100 candidate stories per run
2. **NPCI scraper retry/timeout fix** — bump from 30s to 90s, retry once
3. **mmdpc.in via Scrapling stealth fetch** — high-signal NBFC license tracker
4. **Tweet-harvest integration** — existing skill for 50 fintech operator handles → operator commentary cards
5. **Reddit signal layer** — r/IndianStreetBets, r/IndiaInvestments via existing reddit-scraper skill
6. **WhatsApp / Telegram broadcast** — push `breaking: true` cards to a channel
7. **Story-level fuzzy dedup** — catches duplicates BEFORE the LLM call, saves token spend (already free, but saves time on Ollama)
8. **Vendor wall** — searchable directory built from `vendor` category cards
9. **Job board** — fintech PM/compliance/risk roles, weekly curated
10. **Hosted version** — deploy `web/` to Vercel + GitHub Action for `build_cards.py`

---

## What this project demonstrates (for portfolio purposes)

For a PMM looking at remote GTM AI / PMM roles, this single repo demonstrates:

| Skill | Evidence |
|---|---|
| User research → product spec | WhatsApp chat analysis (3 communities, 7 archetypes, 12+ recurring questions) → mapped to 6 content buckets |
| Competitive teardown with strategic POV | Medial PMM analysis with concrete 90-day fix recommendations |
| Source taxonomy + scrapeability mapping | 21-source registry with weight/category/scrape-mechanism per row, 5-tier categorization |
| Architectural decisions with rejected alternatives | Decision log table above |
| Build + ship cadence | Two commits, v1.0 → v1.1 in same session, real measured throughput |
| LLM integration | Both Anthropic SDK (with prompt caching + tool-use) AND Ollama (with JSON schema) implementations |
| Cost engineering | ₹18K/yr (paid LLM) → ₹0/yr (local Ollama), documented trade-offs |
| Editorial voice design | System prompt rewrite with active-voice rules, weak-vs-good examples, ON/OFF-topic enumeration |
| Honest product behavior | MIN_IMPORTANCE filter that drops cards the LLM scored low; off-topic stories get `why_it_matters: "primarily affects insurers, not core payments/lending"` instead of fake operator framing |
| Documentation | PRD with 31 requirement IDs + this build journey + README quickstart |

---

## Appendix: timeline

| Phase | What happened |
|---|---|
| 1 | Medial.app/news teardown |
| 2 | Finshots comparison + two-archetype framework |
| 3 | WhatsApp chat analysis (3 communities, ~440KB) |
| 4 | Source taxonomy mapping (21 sources, 5 tiers) |
| 5 | "Inshorts for BFSI" pivot from user |
| 6 | v1.0 build: Python pipeline + Claude → Ollama swap + frontend |
| 7 | First successful run (5 cards, PPI Master Direction at top) |
| 8 | Add Medial + IndianStartupNews + title-hash dedup |
| 9 | Push v1.0 to GitHub (commit 965f718) |
| 10 | PRD authored (20 sections, 31 requirement IDs) |
| 11 | Run #2: still all-RBI feed, user flagged variety problem |
| 12 | v1.1 build: select_diverse + engagement prompt + topic focus + OG images + fuzzy dedup |
| 13 | Final run: 6 sources, 4 categories, 4/5 with images, PhonePe 10B as top card |
| 14 | Push v1.1 to GitHub (commit f9b54a7) |
| 15 | This document |

---

**End of build journey.**
