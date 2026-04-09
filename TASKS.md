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

Repository hygiene context:
- Read [docs/internal/REPO_HYGIENE_HANDOFF.md](/Users/efsir/Projects/Dropshipping%20agent(Totik)/docs/internal/REPO_HYGIENE_HANDOFF.md) before doing repo-structure cleanup, GitHub-readiness work, or reverting root-level documentation changes.

---

## In Progress
_Nothing in progress — pick a task below_

---

## Up Next (priority order)

- [x] **Step 7A** — Trend detection: Google Trends scanner (`agent/trends.py`) [Codex]
  - pytrends integration, rising keywords, configurable categories
  - i18n keys for all 3 languages
  - Tests in `tests/test_trends.py`

- [x] **Step 7B** — Trend detection: Reddit scanner (`agent/trends.py`)
  - PRAW integration, niche subreddit monitoring
  - Hype signal scoring
  - Tests in `tests/test_trends.py`

- [x] **Step 8** — Listing generator (`agent/listings.py`) [Codex]
  - eBay-optimized title + description generator
  - Bullet points, category suggestion, item specifics
  - Bulk mode (multiple products at once)
  - Telegram `/listing` command handler
  - Tests in `tests/test_listings.py`

- [x] **Step 9** — Multi-user support [Codex]
  - Wire user profiles to all handlers (bot already has user_id)
  - Per-user settings isolation (DB layer exists)
  - Per-user digest schedule
  - Tests in `tests/test_multiuser.py`

- [x] **Dashboard: frontend polish** [Claude]
  - Connect `app.js` to real backend API endpoints
  - Display digest results in dashboard
  - Language switcher UI (EN/RU/ZH)
  - Soft-dark + emerald money-positive redesign per `.impeccable.md`

- [x] **Docker: production-ready compose** [Codex]
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
- [x] **Dashboard: animations & micro-interactions** (`styles.css`, `app.js`)
  - Page entrance: hero fade+slide, staggered card reveal via IntersectionObserver
  - Hero glow pulse, eyebrow/label shimmer gradient
  - Card hover lift with shadow bloom, stat box hover accent
  - Button ripple effect, press feedback, primary glow shadow
  - Input focus glow, language switcher bounce, source option hover lift
  - Tracked items staggered slide-in, hover shift, danger remove button
  - Calc result cascading entrance (badge pop → metrics → breakdown rows)
  - Status indicator pulse dot, error shake, footer fade-in
  - Custom scrollbar, prefers-reduced-motion accessibility support
- [x] **Dashboard: full i18n coverage** (`index.html`, `app.js`)
  - Added data-i18n to all hardcoded HTML: form labels, buttons, select options, legend, empty states, footer
  - ~50 new translation keys across EN, RU, ZH
  - Status messages, error messages, tracked query metadata, profile summary — all translated
  - applyLanguage() re-renders dynamic content (tracked queries, profile summary, calc result) on language switch
  - `<html lang>` attribute updates on language switch
- [x] **Bot: full i18n coverage** (`i18n/*.json`, `bot/handlers/*.py`, `bot/main.py`)
  - 150 translation keys across EN, RU, ZH — all matched
  - All handler responses: usage, success, error messages — fully translated
  - /help command, settings display, tracked queries, watchlist, schedule — all use t()
  - Auto-digest skip message translated
  - Fixed zh.json JSON syntax error (curly quotes → brackets)

---

## Backlog (no priority yet)

- [x] AliExpress source (`agent/sources/aliexpress.py`) — Model 2 [Codex]
- [x] CJDropshipping source (`agent/sources/cj.py`) — Model 2 [Codex]
- [x] Competitor tracker (`agent/competitor.py`) [Codex]
- [x] Product watchlist with price history [Codex]
- [x] Weekly category report [Codex]
- [x] Google Sheets export (`agent/export_sheets.py`) [Claude]
  - Exports: digest, margin results, tracked queries, watchlist
  - Auto-creates sheet tabs, clears old data, service-account auth
  - 16 tests in `tests/test_export_sheets.py`
- [x] Email notifications (`agent/notify_email.py`) [Claude]
  - SMTP/STARTTLS, plain-text + HTML (dark-themed) emails
  - Alert, digest summary (table with stats), margin result emails
  - 19 tests in `tests/test_notify_email.py`
- [x] Discord webhook notifications (`agent/notify_discord.py`) [Claude]
  - Rich embeds with colour-coded profit/loss, timestamps, footer
  - Message, alert, digest summary (top 10 + stats), margin result
  - 14 tests in `tests/test_notify_discord.py`
- [x] Telegram inline/reply keyboards (`bot/keyboards/`) [Claude]
  - Reply keyboards: main menu (6 commands), settings sub-menu (5 settings + back)
  - Inline keyboards: language picker (EN/RU/ZH), settings quick-access, schedule selector, tracked query remove buttons, export actions (Sheets/Email/Discord), source marketplace toggles
  - `BotResponse` wrapper: handlers can return text + keyboard
  - `send_message` upgraded with `reply_markup` support
  - `answer_callback_query` method added to `TelegramBotClient`
  - `process_callback_query` routes lang/schedule/untrack/settings callbacks
  - `/start` shows main menu keyboard, `/settings` shows inline buttons, `/language` shows picker
  - 21 tests in `tests/test_keyboards.py`
- [x] Dashboard: notifications panel (`dashboard/frontend/`) [Claude]
  - 3-column notification grid: Discord, Email, Google Sheets
  - Each channel: config input + test/digest action buttons
  - Status feedback bar with success/error states
  - 14 new i18n keys × 3 languages (EN/RU/ZH)
  - Responsive: stacks to single column on mobile
  - CSS: hover lift, focus glow, glassmorphism channel cards
- [x] Dashboard: PWA support (`manifest.json`, `sw.js`) [Claude]
  - Web App Manifest with app metadata, theme colours, 192/512 icons
  - Service Worker: cache-first for static assets, network-first for API
  - Offline app shell precaching (HTML, CSS, JS, icons)
  - Apple iOS standalone mode meta tags
  - Auto-generated app icon (emerald chart arrow)

---

_Last updated: 2026-04-09 | Tests: 272 passing_
