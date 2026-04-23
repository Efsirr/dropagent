<div align="center">

# DropAgent

AI-powered dropshipping assistant for eBay resellers. Scans marketplaces, calculates margins, delivers daily digests via Telegram, and surfaces trend signals — all from a single self-hosted Docker stack.

**English** · [Русский](./README.ru.md) · [中文](./README.zh.md) · [Azərbaycan](./README.az.md)

<br/>

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram_Bot-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![eBay](https://img.shields.io/badge/eBay_API-E53238?style=for-the-badge&logo=ebay&logoColor=white)
![Amazon](https://img.shields.io/badge/Amazon_PA--API-FF9900?style=for-the-badge&logo=amazon&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-384_passing-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)

</div>

<br/>

## What it does

| Feature | Details |
|---|---|
| **Daily Digest** | Scans Amazon, Walmart, AliExpress, CJ → compares eBay sold prices → ranks by net profit |
| **Margin Calculator** | Buy price, sell price, shipping, packaging → eBay fee (13%), payment fee → net profit, margin %, ROI |
| **Trend Detection** | Google Trends + Reddit scanner for rising search terms and early hype signals |
| **Listing Generator** | eBay-optimised title, description, bullet points, category, item specifics — bulk mode included |
| **Competitor Tracker** | Monitor specific eBay sellers, track listings, get alerts on new products |
| **Product Watchlist** | Price history per product, alert when buy price drops or sell price rises |
| **Weekly Report** | Top products by category with trend direction (rising / stable / declining) |
| **Notifications** | Telegram (primary), Email, Discord webhook, Google Sheets export |
| **Web Dashboard** | Margin calculator, digest preview, analytics, Discovery Hub, workflow nav — PWA, works offline |
| **Discovery Hub** | Unified discovery: competitor stores (StoreLeads), TikTok ad spy (PiPiADS), Google Trends — one search |
| **Service Adapters** | Keepa (Amazon price history), StoreLeads (store intelligence), PiPiADS (ad spy) — user-owned API keys |
| **Multi-language** | English · Русский · 中文 — full i18n across bot and dashboard |
| **Multi-user** | Per-user profiles, settings, and history — self-hosted, no SaaS |
| **Hosted Mode** | Optional hosted deployment with encrypted user-owned API keys, Telegram deep-linking, onboarding wizard |

<br/>

## Business models supported

**Model 1 — US Retail Arbitrage**
Source from Amazon, Walmart, Target, Costco, BestBuy → sell on eBay. Focus: price gaps, fast US shipping, $5–30 margin per item.

**Model 2 — China Dropshipping**
Source from AliExpress, CJDropshipping → sell on eBay or Shopify. Focus: high markup, trend products, 3–10x margin.

<br/>

## Quick start

```bash
git clone https://github.com/Efsirr/dropagent.git
cd dropagent
# Create the single real runtime config file:
cp .env.example .env
# Then edit only `.env`
docker compose up --build
```

Dashboard opens at `http://localhost:8000`.
Bot starts automatically once `TELEGRAM_BOT_TOKEN` is set.

<br/>

## Telegram commands

| Command | Description |
|---|---|
| `/calc 25 49.99` | Quick margin calculation |
| `/digest` | Run and deliver today's digest |
| `/trends electronics` | Rising keywords in a category |
| `/listing AirPods Pro` | Generate eBay listing |
| `/watchlist` | Manage tracked products |
| `/competitor` | Track eBay sellers |
| `/weekly electronics` | Weekly category report |
| `/settings` | Update preferences |
| `/language` | Switch EN / RU / ZH |

<br/>

## CLI tools

```bash
python3 calc.py 25 49.99                        # margin calculator
python3 digest.py --query "airpods pro"          # daily digest
python3 trends.py --category electronics         # trend scan
python3 weekly_report.py --category electronics  # weekly report
python3 -m bot.main                              # Telegram bot
python3 -m dashboard.backend.server              # web dashboard
```

<br/>

## Project structure

```
dropagent/
├── agent/           # Core logic: scanner, analyzer, trends, listings, competitor
│   ├── sources/     # Marketplace adapters: Amazon, Walmart, AliExpress, CJ
│   └── adapters/    # Service integrations: Keepa, StoreLeads, PiPiADS
├── bot/             # Telegram bot, handlers, keyboards, onboarding
├── dashboard/       # Web dashboard — FastAPI backend + vanilla JS frontend (PWA)
├── db/              # SQLAlchemy models, Alembic migrations
├── i18n/            # Translation files EN / RU / ZH
├── tests/           # 384 passing tests
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

<br/>

## API keys needed

| Service | Where to get it | Required |
|---|---|---|
| Telegram Bot Token | [@BotFather](https://t.me/BotFather) | **Yes** |
| eBay App ID | [developer.ebay.com](https://developer.ebay.com) | For scanning |
| Amazon PA-API | [affiliate-program.amazon.com](https://affiliate-program.amazon.com) | Model 1 |
| Walmart API | [developer.walmart.com](https://developer.walmart.com) | Model 1 |
| AliExpress API | [AliExpress Open Platform](https://developers.aliexpress.com) | Model 2 |
| CJDropshipping API | [app.cjdropshipping.com](https://app.cjdropshipping.com) | Model 2 |
| Keepa API | [keepa.com](https://keepa.com/#!api) | Amazon history (optional) |
| StoreLeads API | [storeleads.app](https://storeleads.app/api) | Store discovery (optional) |
| PiPiADS API | [pipiads.com](https://pipiads.com) | TikTok ad spy (optional) |

<br/>

## Tech stack

- **Python 3.9+** with `httpx` for async HTTP
- **SQLAlchemy 2.0** + Alembic migrations (SQLite default, PostgreSQL ready)
- **pytrends** for Google Trends, **PRAW** for Reddit
- **Vanilla JS** dashboard — no framework, no build step
- **Docker Compose** — single command to run everything

<br/>
