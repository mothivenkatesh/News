# fintech-inshorts

Inshorts-style 60-word swipeable cards for Indian fintech operators. Aggregates from RBI, NPCI, SEBI, IRDAI primary docs + ET BFSI, Mint, Inc42, Entrackr, IndianStartupNews, Medial, MoneyLife, and others. Locally summarised by **Ollama (Gemma 4)** into a strict 60-word body, categorised across 9 buckets, and served as a static web app.

**Zero LLM cost** — runs entirely on your machine via Ollama.

## Quick start

```powershell
# 1. Make sure Ollama is running and gemma4 is pulled
ollama serve                    # in one terminal
ollama pull gemma4:e4b          # one-time, ~9.6GB

# 2. Install Python deps (Python 3.10+)
pip install -r requirements.txt

# 3. (Optional) override defaults
copy .env.example .env
# edit .env if you want a different OLLAMA_MODEL or CARDS_PER_RUN

# 4. Run the pipeline
python build_cards.py

# 5. Serve the web app
python -m http.server 8000 --directory web
# Open http://localhost:8000
```

## Architecture

```
sources.yaml
   ↓
[ rss_fetcher.py ]    [ html_scrapers.py ]
   ↓                       ↓
              ↓
       [ dedup.py ] (SQLite — URL hash + normalized-title hash)
              ↓
    [ card_generator.py ]  ──HTTP──>  Ollama (gemma4:e4b, JSON-schema constrained)
              ↓
       web/cards.json
              ↓
       web/index.html  ← Inshorts-style swipeable feed
```

## File map

| File | Purpose |
|---|---|
| `sources.yaml` | Source registry — RSS feeds + HTML scrape targets, with weights and category hints |
| `models.py` | `Story` and `Card` dataclasses; the 9 fixed categories |
| `rss_fetcher.py` | Generic RSS/Atom fetcher (feedparser) |
| `html_scrapers.py` | Per-site scrapers (NPCI, SEBI, IRDAI, **Medial**, generic blog) |
| `dedup.py` | SQLite-backed seen-URL + seen-title-hash store. The title hash catches Medial republishing IndianStartupNews |
| `card_generator.py` | Calls Ollama via HTTP `/api/chat` with JSON schema constraint → typed `Card` |
| `build_cards.py` | Orchestrator: Ollama health-check → fetch → dedup → generate → write JSON |
| `web/index.html` | Inshorts-style swipeable card UI |
| `web/app.js`, `web/styles.css` | Frontend logic + dark theme |
| `data/seen.db` | SQLite dedup store (auto-created, gitignored) |
| `output/cards-YYYY-MM-DD.json` | Daily archive of generated cards |
| `output/run-stats.json` | Last-run telemetry: per-source fetch counts, dedup totals |

## The 9 categories

| Category | What it covers |
|---|---|
| **rbi** | RBI circulars, master directions, press releases, governor speeches |
| **npci** | NPCI circulars, UPI/IMPS/NACH operational changes, statistics |
| **sebi** | SEBI circulars, broker/AMC actions, market structure |
| **irdai** | IRDAI circulars, insurance broker actions |
| **funding** | Fintech startup funding, IPO filings, M&A, ESOPs, ownership changes |
| **personnel** | CXO moves at fintechs/banks, RBI MD approvals, departures |
| **fraud** | Specific fraud patterns, scam alerts, FIU penalties, money laundering |
| **vendor** | Vendor product launches, API releases, partnerships, B2B fintech tools |
| **operator** | Operator/influencer commentary, opinion posts, podcasts, deep analyses |

## Adding a new source

Edit `sources.yaml`:

```yaml
- id: my_new_source
  name: My New Source
  type: rss            # or 'html'
  url: https://example.com/feed
  category_hint: rbi   # the LLM's default category
  weight: 7            # 1-10, ranks priority when overflowing CARDS_PER_RUN
  enabled: true
```

For HTML sources without RSS, add a scraper to `html_scrapers.py` and reference it via the `scraper:` key.

## Ollama notes

- **Default model:** `gemma4:e4b` (9.6GB). Override with `OLLAMA_MODEL` env var.
- **Speed:** ~10-30 seconds per card on consumer hardware (M1 / RTX 4060). 20 cards ≈ 5-10 minutes.
- **Quality:** Gemma 4 follows the JSON-schema constraint reliably. The 60-word body limit is a soft hint; we hard-truncate at the last word in `card_generator.py`.
- **No prompt cache** (Ollama doesn't have one yet) — but local inference is free, so it doesn't matter.
- **Want better quality?** Try `gemma4:e12b` (larger), or `qwen3:8b`, or `llama4:8b`. Just set `OLLAMA_MODEL` and `ollama pull` it.
- **Want faster?** Try `gemma4:e2b` (smaller). Quality drops but throughput doubles.

## Switching back to Claude API (optional)

If you want the editorial quality of Sonnet 4.5 / Opus 4.7 instead of local Gemma, swap the `requests.post(.../api/chat)` block in `card_generator.py` for an `anthropic.Anthropic().messages.create(...)` call with `tools=[CARD_TOOL]` + `tool_choice={"type": "tool", ...}`. The output Card structure is identical.

## Scheduling on Windows

Open Task Scheduler → Create Task →
- Program: `C:\path\to\python.exe`
- Arguments: `C:\Users\mothi\fintech-inshorts\build_cards.py`
- Trigger: Daily at 07:00 IST (and 14:00 if you want twice-daily)

Or use the `loop` skill: `/loop 6h python C:\Users\mothi\fintech-inshorts\build_cards.py`

## What's next (roadmap)

- [ ] Fix the broken-RSS cluster (LiveMint, Business Standard, FE, MoneyControl, MoneyLife — likely need browser-fingerprint scraping via Scrapling)
- [ ] WhatsApp broadcast / Telegram channel push for `breaking: true` cards
- [ ] LinkedIn operator-post ingestion (via RSS.app)
- [ ] Twitter scraping using existing `tweet-harvest` skill (50 fintech handles)
- [ ] Reddit signal layer via `reddit-scraper` skill
- [ ] Vendor wall — searchable index built from `vendor` category cards
- [ ] Job board for fintech PM/compliance/risk roles
- [ ] Daily email digest (archive surface)
- [ ] Hosted version — deploy `web/` to Vercel + scheduled GitHub Action for `build_cards.py`

## License

Personal/research use. Source content remains the property of original publishers — every card links to its source.
