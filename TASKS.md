# DropAgent — Shared Task Board

> **Both Claude and Codex read this file before starting work.**
> Claim a task by adding `[Claude]` or `[Codex]` next to it, then commit.
> Mark done with `[x]` when complete.

---

## Rules
- Always `git pull` before starting a task
- Claim your task here first, then commit the claim before coding
- Commit after each task with a clear message: `feat: <what>` or `fix: <what>`
- Run `python3 -m pytest tests/ -q` before committing — all tests must pass
- Never work on a file another agent has claimed

---

## In Progress
_Nothing in progress — pick a task below_

---

## Up Next (priority order)

- [x] **Step 7A** — Trend detection: Google Trends scanner (`agent/trends.py`) [Codex]
  - pytrends integration, rising keywords, configurable categories
  - i18n keys for all 3 languages
  - Tests in `tests/test_trends.py`

- [ ] **Step 7B** — Trend detection: Reddit scanner (`agent/trends.py`)
  - PRAW integration, niche subreddit monitoring
  - Hype signal scoring
  - Tests in `tests/test_trends.py`

- [ ] **Step 8** — Listing generator (`agent/listings.py`)
  - eBay-optimized title + description generator
  - Bullet points, category suggestion, item specifics
  - Bulk mode (multiple products at once)
  - Telegram `/listing` command handler
  - Tests in `tests/test_listings.py`

- [ ] **Step 9** — Multi-user support
  - Wire user profiles to all handlers (bot already has user_id)
  - Per-user settings isolation (DB layer exists)
  - Per-user digest schedule
  - Tests in `tests/test_multiuser.py`

- [x] **Dashboard: frontend polish** [Claude]
  - Connect `app.js` to real backend API endpoints
  - Display digest results in dashboard
  - Language switcher UI (EN/RU/ZH)

- [ ] **Docker: production-ready compose**
  - Add bot service to `docker-compose.yml`
  - Add dashboard backend service
  - Health checks for all services

---

## Done

- [x] **Step 1** — Margin calculator (`agent/analyzer.py`) — 12 tests
- [x] **Step 2** — eBay sold listings scanner (`agent/scanner.py`) — 13 tests
- [x] **Step 3** — Amazon price fetcher (`agent/sources/amazon.py`)
- [x] **Step 3** — Walmart price fetcher (`agent/sources/walmart.py`)
- [x] **Step 3** — Price comparator engine (`agent/comparator.py`) — 12 tests
- [x] **Step 4** — Daily digest generator (`agent/digest.py`) — 10 tests
- [x] **Step 4** — Digest scheduler (`agent/scheduler.py`) — 13 tests
- [x] **Step 4** — Digest CLI (`digest.py`) — 15 tests
- [x] **Step 5** — Telegram bot (`bot/main.py` + handlers) — ~60 tests
- [x] **Step 6** — Web dashboard backend (`dashboard/backend/`) — 27 tests
- [x] **Step 6** — Web dashboard frontend (`dashboard/frontend/`)
- [x] **Infra** — Database layer (`db/models.py`, `db/service.py`, 2 migrations)
- [x] **Infra** — i18n system EN/RU/ZH (`i18n/`) — 11 tests
- [x] **Infra** — Docker Compose base setup
- [x] **Infra** — Git initialized

---

## Backlog (no priority yet)

- [ ] AliExpress source (`agent/sources/aliexpress.py`) — Model 2
- [ ] CJDropshipping source (`agent/sources/cj.py`) — Model 2
- [ ] Competitor tracker (`agent/competitor.py`)
- [ ] Product watchlist with price history
- [ ] Weekly category report
- [ ] Google Sheets export
- [ ] Email notifications
- [ ] Discord webhook notifications

---

_Last updated: 2026-04-09 | Tests: 131 passing_
