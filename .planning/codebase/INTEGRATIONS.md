# External Integrations

**Analysis Date:** 2026-04-09

## APIs & External Services

**eBay (Implemented):**
- eBay Finding API - Searches completed/sold listings for price research
  - SDK/Client: `httpx.AsyncClient` (async HTTP, no official SDK)
  - Endpoint: `https://svcs.ebay.com/services/search/FindingService/v1`
  - Auth env var: `EBAY_APP_ID` (also `EBAY_CERT_ID`, `EBAY_DEV_ID` in `.env.example`)
  - Implementation: `agent/scanner.py` lines 125-290
  - Rate limit handling: Returns empty `ScanResult` on HTTP 429 (`agent/scanner.py` line 178)

- eBay Browse API - Defined but not yet used
  - Endpoint constant: `EBAY_BROWSE_API` in `agent/scanner.py` line 24
  - Status: Declared as constant only, no implementation

**Amazon (Planned, not implemented):**
- Amazon Product Advertising API
  - Auth env vars: `AMAZON_ACCESS_KEY`, `AMAZON_SECRET_KEY`, `AMAZON_PARTNER_TAG`
  - No code exists yet

**Walmart (Planned, not implemented):**
- Walmart Open API
  - Auth env var: `WALMART_API_KEY`
  - No code exists yet

**Other Planned Sources (from CLAUDE.md, no env vars or code):**
- Target, Costco, BestBuy - Scraping approach planned
- AliExpress API - For China dropshipping model
- CJDropshipping API - For China dropshipping model

## Data Storage

**Databases:**
- None configured
- `db/` directory exists with `migrations/` subdirectory, both empty
- No ORM or database driver in `requirements.txt`

**File Storage:**
- Local filesystem only (translation JSON files)

**Caching:**
- In-memory only: `i18n/__init__.py` caches loaded translation dicts in `_cache: dict[str, dict]` (line 25)
- No external cache service

## Authentication & Identity

**Auth Provider:**
- None implemented
- Multi-user support planned (per CLAUDE.md) but no auth code exists

## Monitoring & Observability

**Error Tracking:**
- None

**Logs:**
- No logging framework configured
- Errors printed to stderr via `print(f"Error: {e}", file=sys.stderr)` in `calc.py` line 64
- No structured logging

## CI/CD & Deployment

**Hosting:**
- Not configured (self-hosted target per CLAUDE.md)

**CI Pipeline:**
- None (no `.github/workflows/`, no CI config files)

**Docker:**
- Not yet created (planned per CLAUDE.md architecture section)

## Environment Configuration

**Required env vars (for current features):**
- `EBAY_APP_ID` - Required for eBay scanner (validated at runtime in `agent/scanner.py` line 161)

**Defined in `.env.example` but not yet used by code:**
- `EBAY_CERT_ID`, `EBAY_DEV_ID`
- `AMAZON_ACCESS_KEY`, `AMAZON_SECRET_KEY`, `AMAZON_PARTNER_TAG`
- `WALMART_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `DISCORD_WEBHOOK_URL`

**Secrets location:**
- `.env` file (loaded by `python-dotenv`)
- `.env.example` serves as template

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None (planned: Telegram Bot API, Discord webhooks)

## Notification Channels (Planned)

**Telegram Bot:**
- `TELEGRAM_BOT_TOKEN` env var defined
- `bot/` directory scaffolded with `handlers/` and `keyboards/` subdirs (all empty)
- No bot code exists

**Discord:**
- `DISCORD_WEBHOOK_URL` env var defined
- No implementation

**Email:**
- Planned per CLAUDE.md, no env var or code

## Trend & Data Sources (Planned, per CLAUDE.md)

- Google Trends via `pytrends` - Not in requirements.txt
- Reddit API via `PRAW` - Not in requirements.txt
- Google Sheets export - Not in requirements.txt
- Shopify API - Not in requirements.txt

---

*Integration audit: 2026-04-09*
