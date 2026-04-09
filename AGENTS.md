# DropAgent (Тотик) — AI-Powered Dropshipping Assistant

## Project Overview
DropAgent is an open-source AI agent that automates daily product research for eBay dropshippers. It monitors multiple marketplaces, detects price gaps and trends, and delivers actionable reports via Telegram bot and a web dashboard.

Built for real-world use. No fluff.

---

## Who It's For
- **Primary user:** eBay resellers doing US-based retail arbitrage (Amazon/Walmart → eBay)
- **Secondary user:** China-model dropshippers (AliExpress/CJ → Shopify/eBay)
- **Self-hosted:** Anyone can clone, configure, and run their own instance

---

## Business Models Supported

### Model 1 — US Retail Arbitrage (default)
- Source: Amazon, Walmart, Target, Costco, BestBuy
- Sell: eBay
- Focus: price gaps, fast shipping, US stock only
- Margin: typically $5–30 per item, volume-based

### Model 2 — China Dropshipping
- Source: AliExpress, CJDropshipping
- Sell: eBay or Shopify
- Focus: high markup, trend products
- Margin: 3–10x markup

---

## Core Features

### 1. Daily Morning Digest
- Scans best sellers across configured marketplaces every morning
- Compares prices and calculates net margin after all fees
- Ranks products by profit potential
- Delivered via Telegram and visible on web dashboard

### 2. Weekly Category Report
- Top products grouped by category
- Trend direction (rising / stable / declining)
- Configurable — user selects which categories to track

### 3. Real-Time Alerts
- Instant Telegram notification when a high-margin product is detected
- Price drop alerts on tracked products
- Stock availability alerts from US suppliers

### 4. Trend Detection
- Google Trends monitoring for rising search terms
- Reddit scanner (niche subreddits) for early hype signals
- Upcoming release calendar — movies, shows, games, sports events with merch potential (next 90 days)

### 5. Margin Calculator
- Input: product URL or manual price
- Output: full breakdown — buy price, shipping, eBay fee (13%), payment processing, packaging, net profit, margin %
- Available as `/calc` command in Telegram and as standalone tool in dashboard

### 6. Listing Generator
- Input: product name or URL
- Output: eBay-optimized title, description, bullet points, suggested category, item specifics
- Bulk mode: process multiple products at once

### 7. Competitor Tracker
- Monitor specific eBay sellers
- Track their listings, pricing, best performers
- Get alerts when they add new products

### 8. Product Watchlist
- Add specific products to track over time
- Price history chart
- Alert when buy price drops or sell price rises

### 9. User Settings Panel
- Select marketplaces to scan
- Choose product categories
- Set minimum margin threshold (e.g. only show $10+ profit)
- Set maximum buy price
- Configure alert schedule
- Select business model (Model 1 or Model 2)

---

## Integrations

### Marketplaces (Sources)
- Amazon Product Advertising API
- Walmart Open API
- Target, Costco, BestBuy — scraping
- AliExpress API (Model 2)
- CJDropshipping API (Model 2)

### Selling Platforms
- eBay API — sold listings data, listing creation, store analytics
- Shopify API — for Model 2 users

### Trend & Data
- Google Trends (pytrends)
- Reddit API (PRAW)
- Google Sheets export

### Notifications
- Telegram Bot API (primary)
- Email (secondary)
- Discord webhook (optional)

---

## Architecture

```
dropagent/
├── AGENTS.md                  ← you are here
├── README.md
├── docker-compose.yml
├── .env.example
│
├── agent/                     ← core AI agent logic
│   ├── scanner.py             ← marketplace price scanning
│   ├── analyzer.py            ← margin calculation, scoring
│   ├── trends.py              ← Google Trends + Reddit monitor
│   ├── listings.py            ← eBay listing generator
│   └── scheduler.py           ← daily/weekly report scheduling
│
├── bot/                       ← Telegram bot
│   ├── main.py
│   ├── handlers/
│   └── keyboards/
│
├── dashboard/                 ← web dashboard
│   ├── frontend/              ← Next.js or plain HTML/CSS/JS
│   └── backend/               ← API server
│
├── db/                        ← database
│   ├── models.py
│   └── migrations/
│
└── skills/                    ← Codex skills
    ├── scanner-skill.md
    ├── margin-skill.md
    └── listing-skill.md
```

---

## Language Support
- Three languages: English (en), Russian (ru), Chinese (zh)
- User selects preferred language in settings
- All bot messages, reports, and dashboard UI must be translatable
- Translation files stored in `i18n/` directory
- English is the default fallback language
- Code, comments, and documentation remain in English

---

## Multi-User Support
- Each user has their own profile, settings, and history
- Self-hosted: clone repo, deploy, invite users
- No SaaS, no subscription, fully open-source
- User data isolated per account

---

## Tech Decisions
- Let Codex choose the best stack for each module
- Prefer simplicity over complexity
- Must be deployable with a single `docker-compose up` command
- All API keys stored in `.env` — never hardcoded

---

## Code Style
- Write clean, readable code with comments
- Every module must have a README explaining what it does
- English for all code, comments, and documentation
- Keep functions small and single-purpose
- Always handle API rate limits gracefully

---

## What NOT to Build
- No payment/monetization features (open-source only)
- No admin panel for managing other users (self-hosted model)
- No mobile app (Telegram bot covers mobile)
- Keep it lean — no feature creep

---

## Project Status
Early development. Build in this order:
1. Margin calculator (core logic)
2. eBay sold listings scanner
3. Amazon/Walmart price fetcher
4. Daily digest generator
5. Telegram bot
6. Web dashboard
7. Trend detection
8. Listing generator
9. Multi-user support
