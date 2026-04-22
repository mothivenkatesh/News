# PRD: fintech-inshorts

> **Inshorts-style 60-word swipeable cards for Indian BFSI/fintech operators. Aggregates from RBI, NPCI, SEBI, IRDAI primary docs + tier-1 BFSI press + community sources, locally summarised by Ollama Gemma 4, served as a static web app.**

| Field | Value |
|---|---|
| Owner | Mothi Venkatesh |
| Status | v1.0: MVP shipped, end-to-end working |
| Last updated | 2026-04-23 |
| Repo | `C:\Users\mothi\fintech-inshorts\` |
| Stage | Internal MVP. Not yet hosted. |

---

## 1. TL;DR

Indian fintech operators (founders, PMs, compliance heads, payments engineers, risk leads) have no purpose-built news surface. They get RBI circulars as raw PDFs, fintech funding stories from Inc42 / Entrackr, and operator commentary from LinkedIn: fragmented across 7+ apps. They share links in WhatsApp groups all day. **fintech-inshorts** is a swipeable 60-word card feed across 9 fixed categories (RBI · NPCI · SEBI · IRDAI · Funding · Personnel · Fraud · Vendor · Operator), with each card hard-summarised from the source by a local LLM, sorted by importance, and surfaced for the operator commute.

The MVP is built. Backend pulls 21 sources, dedups by URL + normalized-title, generates cards via local Ollama (zero API cost), and writes a JSON consumed by an Inshorts-style web frontend.

---

## 2. Problem statement

### Today
- An RBI master direction lands as a PDF on `rbi.org.in/Scripts/NotificationUser.aspx`. No one reads the full PDF; they wait for an Inc42 article 3 days later, or a friend's LinkedIn take.
- ET BFSI, Mint, BusinessLine, Inc42, Entrackr, MoneyLife, IBS Intelligence each cover a slice: operators check none of them daily, all of them weekly.
- LinkedIn is where senior operators (Sushil Kurri, Sushant Patekar, Jitendra Khorwal) post the actual operator-grade commentary. There's no aggregation.
- WhatsApp groups (verified via three groups: FinPro Bangalore, IFF Payment & Lending, WTFraud) carry hundreds of links per month: most shared as raw URLs with no context.

### What's broken
- **No vertical specialisation.** Inshorts/Public covers consumer news. Finshots covers retail finance. No one covers fintech-operator news.
- **No regulator-decode layer.** RBI's E-mandate Framework 2026 is one PDF. There's no "what changed, who it affects" 60-word card.
- **No cross-source dedup.** Medial republishes IndianStartupNews verbatim. ETBFSI re-reports Mint. The operator sees the same story 4 times.
- **No importance ranking.** A press release on Reserve Money week-end data sits next to a draft Master Direction in every existing aggregator.

### Why now
- Local LLMs (Gemma 4) are good enough to do operator-grade editorial summarisation at zero per-token cost.
- Mobile-first card UX (Inshorts) is a solved pattern: known to retain.
- WhatsApp Business API + Telegram Bot API make distribution trivial once cards exist.

---

## 3. User research

Three WhatsApp groups were analysed (~440KB of chat across ~6 months):

| Group | Size signal | Top topic |
|---|---|---|
| FinPro Bangalore | 77KB chat, 41 regulatory hits | Product / career / vendor recommendations |
| IFF Payment & Lending | 183KB chat, 263 regulatory hits, 268 lending hits | RBI master directions, NBFC actions, lending compliance |
| WTFraud Fintech Forum | 183KB chat, 244 regulatory hits, 99 fraud hits | Fraud patterns, KYC vendors, AML |

### What gets shared (sorted by frequency)

1. **Operator commentary on LinkedIn** (Sushil Kurri, Sushant Patekar, etc.): shared more than any mainstream press
2. **RBI primary documents**: direct PDF links (rbidocs.rbi.org.in)
3. **ET BFSI / BusinessLine / Government ETNow**: regulatory-trigger and personnel-change stories
4. **Vendor product docs** (Cashfree fraud-risk indicator was actively shared)
5. **Job postings** (heavy across all 3 groups)
6. **Event invites** (Luma)
7. **Niche operational updates**: CKYC SFTP changes, BBPS COU pagination, DLA reporting on RBI CIMS portal, TRAI 160-series: zero outlets cover these

### What gets asked ("anyone know")

- "How do you generate 160-series numbers from TRAI for NBFC/Fintech?"
- "Anyone implemented the CKYC algorithm update?"
- "Anyone done DLA reporting on the RBI CIMS portal?"
- "Vendors for liveness checks: active SDK and passive?"
- "Anyone using AI/xAI-powered underwriting for credit decisioning, CAM generation, BRE setup?"

### What does NOT get shared
- Inc42 / Entrackr funding roundups (operators see them as press-release-y)
- YourStory listicles
- Generic "Top 10 fintech trends 2026"
- Finshots-style consumer-finance explainers

### Implication for the product
The audience is **not consuming-news**, they are **decoding-regulator + tracking-peer-moves + scouting-vendors**. The product must specialise in:
- Plain-English regulator decode (40% of feed)
- License & enforcement tracking (15%)
- Personnel moves (10%)
- Fraud patterns of the week (15%)
- Vendor / tool intel (10%)
- Operator commentary curation (10%)

---

## 4. Audience & personas

### Primary
**Aakash, Senior PM at a payment gateway.** Reads ETBFSI on weekends, follows 30 fintech accounts on Twitter, in 5 fintech WhatsApp groups. Gets Slack-pinged when his compliance head notices an RBI circular. Wants: 5-minute morning brief that flags "anything that changes my product roadmap this quarter."

### Secondary
- **Compliance head at an NBFC**: needs every RBI / FIU action surfaced same-day with a "who this affects" line
- **Fintech founder**: needs personnel + funding signal across the cohort
- **Risk operator**: needs fraud-pattern alerts and AML-action tracking
- **Sales lead at a B2B fintech vendor**: needs to know which fintechs are raising / hiring

### Out of scope
- Retail finance consumers (Finshots covers this)
- Investors doing diligence (PitchBook / Tracxn cover this)
- General business news readers (Mint / BS cover this)

---

## 5. Goals & non-goals

### Goals (MVP)
- G1: Aggregate from at least 10 working sources spanning regulator + press + community
- G2: Generate 60-word cards with operator-tone editorial voice
- G3: Categorise into 9 fixed buckets with consistent classification
- G4: Score importance 1-10 to drive feed ordering
- G5: Render as a swipeable Inshorts-style web feed
- G6: Run for ₹0 marginal LLM cost (local Ollama)
- G7: Catch cross-source duplicates (Medial republishing IndianStartupNews)

### Non-goals (for v1)
- NG1: Mobile native app (web is enough for MVP)
- NG2: User accounts, bookmarks, personalisation (cards are the same for everyone)
- NG3: Push notifications (manual share for now)
- NG4: Comments / reactions (this is read-only)
- NG5: Original journalism (we aggregate + decode, not report)
- NG6: Multilingual (English only; the audience is English-fluent)
- NG7: WhatsApp / Telegram broadcast (Phase 2)

---

## 6. Success metrics

### MVP / internal
- M1: At least 15 cards / day land in the feed
- M2: At least 80% of cards stay under 60-word body cap (LLM compliance)
- M3: Importance scores correlate with editorial expectation (manual sample of 50 cards, ≥ 80% agreement)
- M4: End-to-end pipeline run < 30 minutes / day on consumer hardware
- M5: Per-day LLM cost: ₹0

### Once distribution exists (Phase 2+)
- Daily active readers
- Card share-through rate (% of cards shared to WhatsApp)
- Time-to-share for `breaking: true` cards
- Subscriber retention week-over-week

---

## 7. The product

### 7.1 Card anatomy

Each card is a single full-screen unit. Render order top→bottom:

```
┌──────────────────────────────────────┐
│  [hero image: source thumbnail or   │
│   category-coloured placeholder]     │
├──────────────────────────────────────┤
│  [CATEGORY] [BREAKING?] [importance  │
│  dots ●●●●○]  [source]   [age ago]   │
├──────────────────────────────────────┤
│  Headline (≤ 12 words, declarative)  │
├──────────────────────────────────────┤
│  Body: exactly ≤ 60 words. Operator │
│  tone. No filler, no hedge soup, no  │
│  marketing voice. Cites real numbers │
│  when present in source.             │
├──────────────────────────────────────┤
│  ▍ WHY IT MATTERS: one sentence,    │
│    ≤ 20 words, framed as             │
│    "who + why care".                 │
├──────────────────────────────────────┤
│  [Read source →]    [Share]          │
└──────────────────────────────────────┘
```

### 7.2 Categories: 9 fixed buckets

| ID | Label | What it covers |
|---|---|---|
| `rbi` | RBI | Circulars, master directions, press releases, governor speeches, license cancellations |
| `npci` | NPCI | UPI/IMPS/NACH circulars, statistics, operational changes |
| `sebi` | SEBI | Circulars, broker/AMC actions, market structure |
| `irdai` | IRDAI | Insurance circulars, broker actions |
| `funding` | Funding | Fintech funding, IPO filings, M&A, ESOPs, ownership changes |
| `personnel` | Personnel | CXO moves at fintechs/banks, RBI MD approvals, departures |
| `fraud` | Fraud | Fraud patterns, scam alerts, FIU penalties, AML busts |
| `vendor` | Vendor | Vendor product launches, API releases, B2B fintech tool intel |
| `operator` | Operator | LinkedIn/Substack commentary, podcasts, deep analyses |

### 7.3 Importance scoring (1-10)

| Score | Meaning | Example |
|---|---|---|
| 10 | Major regulator action / top-10 firm license event / major fintech IPO | RBI's draft PPI Master Direction (2026-04-22) |
| 8-9 | Notable circular requiring operational change. ₹100Cr+ funding. Top-20 fintech CXO move | PhonePe crosses 10B UPI; M2P appoints group CFO |
| 6-7 | Mid-tier funding. Notable operator commentary. New product launch from major vendor | MPC minutes published |
| 4-5 | Standard funding announcement. Smaller-firm personnel move. Generic vendor PR | RBI FDI company financial data |
| 1-3 | Vague headline, marketing fluff, no operational substance | Reserve Money week-end data |

### 7.4 Breaking flag

`true` only when BOTH conditions hold:
1. Published in last 24h
2. Either regulator action requiring immediate compliance attention OR market-moving funding/M&A leak/IPO filing

Default: `false`. Drives the visual breaking-pill animation in the frontend.

### 7.5 Frontend interactions

| Interaction | Behaviour |
|---|---|
| Vertical scroll/swipe | Snap to next card (CSS scroll-snap) |
| Tap "Read source →" | Open source URL in new tab |
| Tap "Share" | Native Web Share API on mobile; clipboard fallback on desktop |
| Tap a category tab | Filter feed to that category, scroll to top |
| Tap "All" | Reset filter, show full feed sorted by importance |

---

## 8. System architecture

```
┌────────────────────────────────────────────────────────────┐
│  sources.yaml: 21 sources, weights, category hints        │
└──────────────┬─────────────────────────────────────────────┘
               ↓
       ┌───────┴─────────┐
       ↓                 ↓
[ rss_fetcher.py ]   [ html_scrapers.py ]
       ↓                 ↓
       └───────┬─────────┘
               ↓
       [ dedup.py ]  ←  SQLite (data/seen.db)
       URL-hash + title-hash dedup
               ↓
   [ card_generator.py ]  ──HTTP──>  Ollama
   (gemma4:e4b, JSON schema constrained)
               ↓
       web/cards.json
               ↓
   [ web/index.html ]  ←  served by python -m http.server
   Inshorts-style swipeable feed
```

### Components

| Component | What it does | Stateful? |
|---|---|---|
| **sources.yaml** | Source registry: name, URL, type (rss / html), category hint, weight, enabled flag | No (versioned in git) |
| **rss_fetcher.py** | Generic RSS / Atom fetcher built on `feedparser` | No |
| **html_scrapers.py** | Per-site scrapers (NPCI, SEBI, IRDAI, Medial, generic blog). Built on `requests` + `beautifulsoup4` + `lxml` | No |
| **dedup.py** | SQLite seen-store. Tracks both URL hash and normalised-title hash. Auto-migrates schema | Yes (data/seen.db) |
| **card_generator.py** | Calls Ollama `/api/chat` with JSON-schema constrained format. Truncates body at 60 words | No |
| **build_cards.py** | Orchestrator. Pre-flight Ollama health check → fetch → dedup → generate → write | No |
| **web/cards.json** | Output JSON consumed by frontend | Yes (overwritten per run) |
| **web/index.html** + `app.js` + `styles.css` | Inshorts-style swipeable deck | No |

---

## 9. Functional requirements

### Backend pipeline

| ID | Requirement | Status |
|---|---|---|
| **R-001** | System reads source registry from `sources.yaml` | ✅ Done |
| **R-002** | Each source has: id, name, type, url, category_hint, weight, enabled | ✅ Done |
| **R-003** | RSS sources fetched via feedparser, max 25 items per source | ✅ Done |
| **R-004** | HTML sources scraped via per-site functions registered in `SCRAPERS` dict | ✅ Done |
| **R-005** | Failed sources log a warning and return empty list: do not crash the run | ✅ Done |
| **R-006** | Dedup by URL hash (SHA1, 16 chars) | ✅ Done |
| **R-007** | Dedup by normalised-title hash (lowercase, strip punctuation): catches Medial/ISN republishing | ✅ Done |
| **R-008** | Dedup state persists in SQLite `data/seen.db` across runs | ✅ Done |
| **R-009** | Schema migration is automatic on startup (handles `title_hash` column add) | ✅ Done |
| **R-010** | Ollama health check before LLM calls: abort if unreachable or model missing | ✅ Done |
| **R-011** | Per-card LLM call constrained by JSON schema (Ollama `format` param) | ✅ Done |
| **R-012** | Body hard-truncated at 60 words even if LLM overshoots | ✅ Done |
| **R-013** | Invalid category from LLM falls back to source `category_hint` | ✅ Done |
| **R-014** | Cards sorted by importance desc, then publish-date desc | ✅ Done |
| **R-015** | New cards merged with existing `cards.json`, capped at 200 in live feed | ✅ Done |
| **R-016** | Daily archive written to `output/cards-YYYY-MM-DD.json` | ✅ Done |
| **R-017** | Per-run telemetry written to `output/run-stats.json` | ✅ Done |

### Frontend

| ID | Requirement | Status |
|---|---|---|
| **R-101** | Vertical scroll-snap card deck | ✅ Done |
| **R-102** | Top tabs filter by category: All + 9 buckets | ✅ Done |
| **R-103** | Each card shows: image / category placeholder, category pill, breaking pill (conditional), importance dots, source name, age ago, headline, body, why-it-matters block, source CTA, share CTA | ✅ Done |
| **R-104** | Native Web Share API on mobile; clipboard fallback on desktop | ✅ Done |
| **R-105** | Image fallback to category-coloured placeholder when source provides no image | ✅ Done |
| **R-106** | Cache-busted fetch of `cards.json` on page load | ✅ Done |
| **R-107** | Empty state when no cards in selected category | ✅ Done |
| **R-108** | Dark theme, 9 distinct category colours | ✅ Done |
| **R-109** | Mobile-responsive (450px max width on desktop, full-width on mobile) | ✅ Done |

### Configuration

| ID | Requirement | Status |
|---|---|---|
| **R-201** | `OLLAMA_BASE_URL` env var (default `http://localhost:11434`) | ✅ Done |
| **R-202** | `OLLAMA_MODEL` env var (default `gemma4:e4b`) | ✅ Done |
| **R-203** | `OLLAMA_TIMEOUT`, `OLLAMA_TEMP`, `OLLAMA_NUM_CTX` env vars | ✅ Done |
| **R-204** | `CARDS_PER_RUN` env var (default 20): caps LLM calls per run | ✅ Done |
| **R-205** | `.env` auto-loaded via python-dotenv if installed | ✅ Done |

### Operational

| ID | Requirement | Status |
|---|---|---|
| **R-301** | `test_fetch.py` smoke test: runs only fetch layer, no LLM, no API key needed | ✅ Done |
| **R-302** | Logging at INFO level by default with timestamps + module names | ✅ Done |
| **R-303** | Per-source fetch counts logged for every run | ✅ Done |
| **R-304** | LLM-time elapsed logged per card | ✅ Done |
| **R-305** | `data/seen.db` and `output/*.json` are gitignored | ✅ Done |

---

## 10. Engineering implementation: file-by-file

### `models.py` (65 lines)
Two dataclasses:
- `Story`: raw fetched item: `source_id`, `source_name`, `url`, `title`, `summary`, `published`, `category_hint`, `weight`, `image_url`, `raw_content`
- `Card`: finalised LLM output: `id`, `headline`, `body`, `category`, `source_name`, `source_url`, `published_at`, `fetched_at`, `importance`, `image_url`, `breaking`, `why_it_matters`

Plus `CATEGORIES` list and `CATEGORY_LABELS` map.

### `rss_fetcher.py` (114 lines)
Single function: `fetch_rss(source: dict, max_items=25) -> list[Story]`.
- Uses `feedparser.parse()` with a custom User-Agent
- Best-effort date parse from `published / updated / pubDate / created`
- Image extraction from `media_content`, `media_thumbnail`, `enclosures`, `links`
- Summary extraction with HTML stripping (regex-based for speed)
- Defensive: returns `[]` on any parse failure, logs the bozo exception

### `html_scrapers.py` (250 lines)
Per-site scrapers, each returning `list[Story]`:
- `scrape_npci`: NPCI circulars page; finds anchors pointing to `.pdf`
- `scrape_sebi`: SEBI listings; table-row based (date in cell 0)
- `scrape_irdai`: IRDAI document detail page; broad anchor matching
- `scrape_medial`: Medial news listing; `a[href*="/news/"]` matching, with title-suffix cleanup to strip "Source · 2d ago"
- `scrape_generic_blog`: fallback for any blog using `<article>` / `<div class*="post|article|entry">`

Dispatch via `SCRAPERS` dict + `fetch_html(source)`.

### `dedup.py` (90 lines)
- SQLite at `data/seen.db`, schema: `(id, source_id, url, title, title_hash, first_seen_at)`
- `story_id(url, title)`: SHA1 of url, 16 chars
- `title_hash(title)`: SHA1 of normalised title (lowercase, punct-stripped, whitespace-collapsed), 16 chars
- `filter_unseen(stories)`: filters and atomically marks new stories as seen
- `stats()`: returns total + per-source counts
- Auto-migrates pre-title_hash schemas via `ALTER TABLE ADD COLUMN`

### `card_generator.py` (220 lines)
- Calls Ollama `POST /api/chat` with `format: CARD_SCHEMA` (JSON schema constraint)
- `SYSTEM_PROMPT` (~1500 chars): role, audience, hard rules, 9 categories, importance rubric, breaking criteria, why-it-matters guidance
- `CARD_SCHEMA`: enforces `headline` / `body` / `category` (enum) / `importance` (1-10 int) / `why_it_matters` / `breaking` (bool)
- `ollama_health()`: pre-flight check, returns `(bool, str)` for `build_cards.py` to act on
- `generate_card(story)`: single-card path with defensive JSON parsing fallback (regex extract from fenced block if direct parse fails)
- `generate_cards(stories, max_cards=30)`: sort by `(weight desc, recency desc)`, generate up to `max_cards`, return sorted by importance

### `build_cards.py` (140 lines)
Orchestrator:
1. Ollama health check (abort if down)
2. Load `sources.yaml`
3. Fetch all enabled sources
4. Dedup against `seen.db`
5. Run `generate_cards()` capped at `CARDS_PER_RUN`
6. Merge with existing `cards.json`, cap at 200
7. Write `web/cards.json`, `output/cards-YYYY-MM-DD.json`, `output/run-stats.json`

### `web/index.html` (37 lines), `web/app.js` (142 lines), `web/styles.css` (279 lines)
- Vanilla JS, no framework, no build step
- Dark theme with 9 category colours (rbi=blue, npci=cyan, sebi=purple, irdai=pink, funding=green, personnel=orange, fraud=red, vendor=slate, operator=amber)
- CSS scroll-snap for swipe behaviour
- Native Web Share API + clipboard fallback
- Mobile-first (max-width 480px on desktop, edge-to-edge on mobile)

### `test_fetch.py` (62 lines)
Smoke test: runs only the fetch layer, no LLM call, no API key needed. Reports per-source counts + first sample title. Use this to validate new sources before spending LLM time.

---

## 11. Source registry

| ID | Name | Type | Working? | Issue if not |
|---|---|---|---|---|
| `rbi_notifications` | RBI Notifications | RSS | ✅ |: |
| `rbi_press_releases` | RBI Press Releases | RSS | ✅ |: |
| `rbi_speeches` | RBI Speeches | RSS | ✅ |: |
| `inc42` | Inc42 | RSS | ✅ |: |
| `entrackr` | Entrackr | RSS | ✅ |: |
| `indianstartupnews` | Indian Startup News | RSS | ✅ |: |
| `medial` | Medial | HTML scrape | ✅ |: |
| `etbfsi` | ET BFSI | RSS | ✅ |: |
| `livemint_companies` | LiveMint Companies | RSS | ✅ | (returning global feed; URL needs swap to `/banking`) |
| `business_standard_finance` | Business Standard Finance | RSS | ❌ | Returns HTML: needs Scrapling browser fingerprint |
| `businessline_money_banking` | The Hindu BusinessLine: Money & Banking | RSS | ✅ |: |
| `financial_express_industry` | Financial Express Industry | RSS | ❌ | Returns HTML |
| `moneycontrol_business` | MoneyControl Business | RSS | ❌ | Returns HTML |
| `moneylife` | MoneyLife | RSS | ❌ | Returns HTML |
| `cafemutual` | Cafemutual | RSS | ❌ | Returns HTML |
| `ibs_intelligence` | IBS Intelligence | RSS | ⚠️ | Returns 1 item: RSS feed appears truncated |
| `finextra` | Finextra | RSS | ✅ |: |
| `npci_circulars_upi` | NPCI UPI Circulars | HTML scrape | ❌ | 30s timeout: bump to 90s and retry |
| `sebi_circulars` | SEBI Circulars | HTML scrape | ⚠️ | DNS resolution failed in test env: likely works on production machine |
| `irdai_circulars` | IRDAI Circulars | HTML scrape | ✅ | (returns generic anchors: needs site-specific selector tightening) |
| `mmdpc_nbfc_tracker` | mmdpc NBFC Tracker | HTML scrape | ❌ | Cloudflare 525: needs Scrapling stealth fetch |

**Summary: 13/21 working, ~210 raw stories per run.** The broken cluster is bot-detection on the financial press tier: fixable in one pass by swapping `requests` for Scrapling on those specific sources.

---

## 12. LLM design

### Why local Ollama / Gemma 4 (and not Claude / OpenAI)
- **Cost:** ₹0 marginal cost. 20 cards/day × 365 days = ₹0 vs ~₹3,650/year on Sonnet 4.5.
- **Privacy:** No source content leaves your machine.
- **Latency:** ~54s per card on consumer hardware: acceptable for daily batch, not for real-time.
- **Quality:** Gemma 4 follows JSON schema constraints reliably. Trade-off: slightly more verbose than Sonnet, occasionally less crisp on importance scoring. Acceptable for MVP.

### Why JSON schema (and not tool-use / function-calling)
- Ollama supports JSON-schema-constrained generation via the `format` param (since Ollama 0.5)
- Simpler than tool-use, no extra round-trips
- Schema acts as a hard validation contract: bad outputs fail at parse time, not at render time

### Prompt design philosophy
- System prompt is large and stable: defines audience, rules, categories, scoring rubric, breaking criteria. ~1500 chars.
- User prompt per call is small: just source metadata + headline + content. ~400 chars.
- No few-shot examples (Gemma 4 follows the schema reliably without them; saves tokens)
- `temperature=0.3` for editorial consistency (not creative writing)

### Schema (CARD_SCHEMA)
```json
{
  "type": "object",
  "properties": {
    "headline": {"type": "string"},
    "body": {"type": "string"},
    "category": {"type": "string", "enum": [...9 categories...]},
    "importance": {"type": "integer", "minimum": 1, "maximum": 10},
    "why_it_matters": {"type": "string"},
    "breaking": {"type": "boolean"}
  },
  "required": ["headline", "body", "category", "importance", "why_it_matters", "breaking"]
}
```

### Hard truncation
Body is hard-capped at 60 words via `_truncate_words()` even if Gemma overshoots. The system prompt sets the soft limit; the truncate enforces the hard limit.

### Switching to Claude (optional, documented)
If editorial quality matters more than cost, swap the `requests.post(.../api/chat)` block in `card_generator.py` for `anthropic.Anthropic().messages.create(...)` with `tools=[CARD_TOOL]` + `tool_choice={"type": "tool", ...}`. Output `Card` shape is identical so the orchestrator and frontend don't change.

---

## 13. Dedup strategy

### The problem
Medial republishes IndianStartupNews verbatim. Different URLs (`medial.app/news/...` vs `indianstartupnews.com/news/...`), same content. URL-only dedup fails.

### The solution
Two-layer hash check:
1. **`story_id(url, title)`**: SHA1 of url, 16 chars. Catches the same URL fetched twice.
2. **`title_hash(title)`**: SHA1 of normalised title (lowercase, strip punctuation, collapse whitespace), 16 chars. Catches same content at different URLs.

A story is "new" only if BOTH `id` and `title_hash` are absent from `seen.db`.

### What gets through
- Same story syndicated under a slightly different headline (e.g., ETBFSI rewriting Mint): different `title_hash`, both processed. We accept this: the LLM will produce two cards but with different framings.
- Updates to a previously-seen story (e.g., RBI revising a circular): same URL, gets blocked. **Trade-off accepted for MVP**: could add a `version` column later if it becomes a problem.

### What's logged
Per run, the orchestrator logs `After dedup: N new (M already seen)` so you can see how aggressive dedup is being.

---

## 14. Run characteristics (measured)

From the most recent run (2026-04-22, 5-card test):

| Metric | Value |
|---|---|
| Sources configured | 21 |
| Sources returning data | 13 |
| Total stories fetched | 210 |
| New stories after dedup | 207 |
| Dupes caught | 3 (Medial republishing ISN) |
| LLM cards generated | 5/5 (100% success) |
| Avg time per card | ~54s |
| Total run time | 4 min 30 sec |
| Cost | ₹0 |
| Disk per run | ~25KB (cards.json + archive) |

Extrapolated:
- 20 cards/day → ~18 minutes
- 50 cards/day → ~45 minutes (use a smaller model like `gemma4:e2b` or upgrade hardware)
- 100 cards/day → switch to Ollama batching, run on GPU box

---

## 15. Operational concerns

### Scheduling
**Windows Task Scheduler**: recommended for daily runs:
- Program: `C:\path\to\python.exe`
- Arguments: `C:\Users\mothi\fintech-inshorts\build_cards.py`
- Trigger: Daily at 07:00 IST
- Working directory: `C:\Users\mothi\fintech-inshorts`

Or use the user's `loop` skill: `/loop 6h python C:\Users\mothi\fintech-inshorts\build_cards.py`

### Failure modes & recovery

| Failure | Symptom | Recovery |
|---|---|---|
| Ollama not running | Health check fails immediately, exit code 1 | `ollama serve` in another terminal |
| Model not pulled | Health check warns with `ollama pull <model>` instruction | Run the suggested `pull` command |
| Source URL changed | That source returns 0, others continue | Update URL in `sources.yaml` |
| Source returns HTML instead of XML | "feed parse failed" warning, that source returns 0 | Swap to Scrapling fetcher or find correct URL |
| `seen.db` corrupted | SQLite errors | Delete `data/seen.db`, will rebuild (loses dedup history) |
| `cards.json` corrupted | Frontend shows empty state | Delete `web/cards.json`, rerun pipeline |
| Disk full | Write fails | Standard ops |

### Monitoring
- `output/run-stats.json` updated every run with: `started_at`, `finished_at`, per-source fetch counts, dedup totals
- Logs go to stdout: pipe to a file in scheduled task (`>> logs/build.log 2>&1`)

### Manual intervention
- **Re-run for missed source:** Set `enabled: true` for a previously-disabled source in `sources.yaml`, rerun
- **Force regenerate a card:** Delete its row from `seen.db`, rerun
- **Wipe history:** `rm data/seen.db`: pipeline will repopulate from sources

---

## 16. Cost model

| Component | Cost | Notes |
|---|---|---|
| Ollama runtime | ₹0 | Local inference, electricity only |
| Source bandwidth | ₹0 | Public RSS / public web pages |
| Disk | <100MB total | seen.db + 90 days of archives |
| Hosting | ₹0 (current) | Local-only. Vercel free tier when hosted (Phase 2) |
| Domain | ₹800/year | Optional, when going public |
| **Total annual** | **~₹0–₹800** | | 

Compare to a paid-LLM equivalent: 20 cards/day × 365 days × Sonnet 4.5 (~₹2.50/card uncached) = ~₹18,000/year.

---

## 17. Roadmap

### Phase 1: MVP (DONE ✅)
- 21 sources configured
- Local Ollama integration
- Dedup + frontend + scheduling docs

### Phase 2: Source repair + distribution (next 2 weeks)
- [ ] Fix the broken-RSS cluster (LiveMint, BS, FE, MoneyControl, MoneyLife) via Scrapling browser fingerprint
- [ ] Fix NPCI / mmdpc via Scrapling
- [ ] Wire in WhatsApp broadcast for `breaking: true` cards (WhatsApp Business API or Twilio)
- [ ] Add Telegram channel push (zero infra: Bot API is free)

### Phase 3: Community + operator signal (next 4 weeks)
- [ ] LinkedIn operator-post ingestion via RSS.app (50 creator profiles)
- [ ] Twitter scraping using existing `tweet-harvest` skill (50 fintech handles)
- [ ] Reddit signal layer (r/IndianStreetBets, r/IndiaInvestments, r/personalfinanceindia) via existing `reddit-scraper` skill
- [ ] Operator commentary curation: automatic surface of LinkedIn posts that get >100 reactions in 24h

### Phase 4: Defensible moats (next 8 weeks)
- [ ] Vendor wall: searchable directory of 40 most-asked vendor categories built from `vendor` cards
- [ ] Job board for fintech PM/compliance/risk roles
- [ ] Daily email digest as archive surface
- [ ] License & enforcement tracker: dedicated page showing RBI license actions over time

### Phase 5: Hosted + scale (next 12 weeks)
- [ ] Deploy frontend to Vercel
- [ ] GitHub Action for `build_cards.py` (runs Ollama in a container or switches to API model in cloud)
- [ ] Real custom domain (decide name: `pgwala`, `notabank`, `paybeat`, `fineprint.fyi`)
- [ ] Disclosure page: "Auto-summarised by AI · Source links always present"
- [ ] First-party AI reporter: monitor MCA filings, RoC updates, ESOP grants on filings, SEBI DRHPs → write original briefs from primary data (not aggregation)

---

## 18. Known issues / tech debt

| Issue | Severity | Plan |
|---|---|---|
| 8/21 sources broken | High | Phase 2: Scrapling rewrite |
| LLM throughput ~1 card/min on consumer CPU | Medium | Acceptable for daily batch; upgrade to GPU when hosted |
| No retry on transient Ollama failures | Low | Add exponential backoff in `generate_card()` |
| Dedup loses RBI-circular-revisions | Low | Add `version` column if it surfaces as an issue |
| No alerting if a daily run fails | Medium | Phase 2: webhook on non-zero exit, or use scheduled task error-action |
| Frontend has no service-worker / offline support | Low | Defer to Phase 5 |
| `IRDAI_circulars` returns generic anchors | Medium | Tighten selector when source becomes important |
| No SEBI connectivity in test env | Low | Likely env-specific, retest on production machine |
| Card image URLs from sources sometimes 404 | Low | Frontend already has fallback |
| No A/B testing of prompts | N/A | Phase 4: add eval harness for prompt iterations |

---

## 19. Open questions

| Question | Owner | Decision needed by |
|---|---|---|
| Brand name (currently "fintech-inshorts" working title) | Mothi | Before public launch |
| Domain: `.in` vs `.fyi` vs `.app` | Mothi | Phase 5 |
| Disclosure copy: how prominent should "AI-summarised" be? | Mothi | Before public launch |
| Cashfree affiliation disclosure: header? footer? | Mothi | Before public launch |
| Do we need a paid tier? (Premium digest, vendor profiles) | Mothi | Phase 4 |
| WhatsApp distribution: Business API (paid) vs Telegram first (free)? | Mothi | Phase 2 |
| Should the LLM cite which sentences came from source vs added context? | Mothi | If trust becomes an issue |

---

## 20. Appendix

### A.1 Sample card output (real, from 2026-04-22 run)

```json
{
  "id": "05af0eb0406d7524",
  "headline": "RBI releases draft Master Direction on Prepaid Payment Instruments (PPIs)",
  "body": "The RBI released a draft Master Direction on Prepaid Payment Instruments (PPIs) following a comprehensive review of existing guidelines. Regulated entities and stakeholders can submit feedback on the draft direction until May 22, 2026, via the 'Connect 2 Regulate' section.",
  "category": "rbi",
  "source_name": "RBI Press Releases",
  "source_url": "http://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=62602",
  "published_at": "2026-04-22T17:40:00+00:00",
  "fetched_at": "2026-04-22T21:14:22.655176+00:00",
  "importance": 10,
  "image_url": null,
  "breaking": true,
  "why_it_matters": "All PPI operators must review the draft guidelines as they signal significant changes to operational compliance and risk management."
}
```

### A.2 Project layout

```
fintech-inshorts/
├── PRD.md                  ← this document
├── README.md               ← quickstart for users
├── requirements.txt
├── .env.example
├── .gitignore
├── sources.yaml            ← source registry (21 sources)
├── models.py               ← Story + Card dataclasses
├── rss_fetcher.py          ← generic RSS / Atom
├── html_scrapers.py        ← per-site HTML scrapers
├── dedup.py                ← URL + title-hash dedup
├── card_generator.py       ← Ollama integration
├── build_cards.py          ← orchestrator
├── test_fetch.py           ← smoke test (no LLM needed)
├── data/
│   └── seen.db             ← SQLite dedup store (gitignored)
├── output/
│   ├── cards-YYYY-MM-DD.json   ← daily archive (gitignored)
│   └── run-stats.json          ← last-run telemetry
└── web/
    ├── index.html
    ├── app.js
    ├── styles.css
    └── cards.json          ← live feed (gitignored)
```

### A.3 How to extend

**Add a new RSS source:**
```yaml
- id: my_source
  name: My Source
  type: rss
  url: https://example.com/feed
  category_hint: rbi
  weight: 7
  enabled: true
```

**Add a new HTML scrape source:**
1. Add the entry above with `type: html` and `scraper: my_scraper`
2. Write `scrape_my_scraper(source) -> list[Story]` in `html_scrapers.py`
3. Register it in the `SCRAPERS` dict at the bottom

**Tune the editorial voice:**
Edit `SYSTEM_PROMPT` in `card_generator.py`. Change rules, add new rules, swap the importance rubric. Restart `build_cards.py`: no rebuild needed.

**Swap the LLM model:**
Set `OLLAMA_MODEL` env var to any pulled Ollama model (`gemma4:e12b`, `qwen3:8b`, `llama4:8b`). Schema constraint works on any model that supports the `format` param.

### A.4 Key references

- WhatsApp group analysis (in-conversation): FinPro Bangalore, IFF Payment & Lending, WTFraud Fintech Forum
- Architectural inspiration: Inshorts (mobile UX), Finshots (editorial voice), Bloomberg Terminal (operator focus)
- LLM provider: [Ollama](https://ollama.com), [Gemma 4](https://ollama.com/library/gemma3) (Google)
- Frontend: vanilla HTML/CSS/JS, no framework
- Backend: Python 3.10+, `feedparser`, `requests`, `beautifulsoup4`, `PyYAML`, SQLite

---

**End of PRD.**
