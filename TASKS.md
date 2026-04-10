# DropAgent — Unified Task Board

One roadmap. One source of truth.

Goal: take DropAgent from a strong working core to a polished, public-friendly, daily-use product for dropshippers.

Current honest progress: about `95%`.
Target: finish E1 (error-state hardening) to reach the closest realistic `100%`.

---

## Live Dispatch

Use this section as the immediate assignment board for parallel work.

- **Codex**
  - Status: idle / awaiting next backend-safe split
  - Note: `E1` is currently owned by Claude per Phase E section below

- **Claude**
  - Task: `E1 — Error-state hardening`
  - Status: `[~] in progress`
  - Files: `dashboard/backend/api.py`, `dashboard/backend/service.py`, `bot/main.py`, `i18n/`
  - Do not touch: discovery frontend (Antigravity) unless a safe split is recorded

- **Antigravity**
  - Completed: `C5` (Heroicons), `C6` (mobile PWA), `C7` (install banner), `E2` (docs)
  - Status: idle — ready for next assignment
  - Do not touch: backend files (Codex), bot logic (Claude)

---

## Rules

- Read this file before starting work.
- Coordination protocol lives in [docs/internal/AGENT_COORDINATION.md](</Users/efsir/Projects/Dropshipping%20agent(Totik)/docs/internal/AGENT_COORDINATION.md>).
- Claim tasks by adding `[Codex]`, `[Claude]`, or `[Antigravity]`.
- Use status markers consistently: `[ ]`, `[~]`, `[x]`, `[blocked]`.
- Never claim the same file-heavy task in parallel without an explicit split.
- If a task may overlap, add a `Files:` note under the task before coding.
- Run `python3 -m pytest tests/ -q` before closing a task.
- Keep the product simple for non-technical users.
- Prefer shipping complete user workflows over adding isolated features.

---

## Product State

Already strong:

- Core scanner, margin engine, digest, weekly report
- Telegram bot with full onboarding flow
- Dashboard with workflow nav and empty states
- Multi-user DB
- Watchlist, competitor tracker, listing generator
- Hosted mode foundation
- User-owned integrations with encrypted storage
- Discovery Hub (search, stores, ads, trends)
- Actionable discovery: save query, save store, save product
- Discovery memory / recent run history
- Alert infrastructure (discovery-based alerts live)
- Keepa, StoreLeads, PiPiADS live paths

Still needed to feel "done":

- Error-state hardening across all surfaces (E1) — Claude in progress

---

## Phase A — Actionable Discovery

Purpose: turn discovery from "interesting data" into "do something with this now".

- [x] **A1 — Discovery actions: save query from Discovery Hub** [Codex]
  - Added "Save query" action from discovery results to tracked queries.
  - Wired into digest and weekly flows.

- [x] **A2 — Discovery actions: save store to competitor workflow** [Codex]
  - Save a discovered store/domain as a monitored competitor lead.
  - Separate "store leads" list created (not forced into eBay seller tracker).

- [x] **A3 — Discovery actions: save product/ad into watchlist workflow** [Codex]
  - "Watch this" action from discovery results into watchlist.
  - One-click with minimal required fields.

- [x] **A4 — Discovery memory layer** [Codex]
  - Discovery runs saved per user, shown in dashboard recent history.
  - localStorage persistence + server merge with deduplication.

---

## Phase B — Alerts That Matter

Purpose: make the system proactive, not only reactive to manual checks.

- [x] **B1 — Discovery-based alerts** [Codex]
  - Alerts when a tracked discovery query shows stronger signals than before.
  - Alert events stored in DB; shown in dashboard.

- [x] **B2 — Watchlist alerts** [Codex]
  - Trigger when buy price drops, sell price rises, or spread improves.
  - Reuse Telegram as primary channel.
  - Watchlist updates now create alert events and `/alerts` shows recent events.

- [x] **B3 — Competitor alerts** [Codex]
  - Alert when tracked sellers add new items or shift category behavior.
  - Competitor scans now create alert events for new items and category shifts.

- [x] **B4 — Alert rules panel** [Codex]
  - Simple dashboard section for enabling/disabling alert types.
  - No noisy enterprise settings. Keep it human.
  - Dashboard now has simple toggles for discovery, watchlist, and competitor alerts.
  - Disabled alert types are filtered at creation time, not only hidden in UI.

---

## Phase C — Dashboard Workflow Completion

Purpose: make dashboard feel like one calm daily workspace.

- [x] **C1 — Discovery Hub polish** [Antigravity]
  - Richer cards: score badges, platform tags, discovery-metrics layout.
  - Summary bars, compact number formatting, shimmer loading animation.
  - Emoji-enhanced empty states, micro-hover effects, landing page links.

- [x] **C2 — Daily workflow layout** [Claude]
  - Sticky workflow nav: 01 Profile -> 02 Research -> 03 Track -> 04 Reports -> 05 Tools.
  - Sections reordered into logical daily flow; Tracked Queries next to Discovery Hub.
  - Phase dividers with step number, label, and description.
  - Intersection Observer highlights active nav tab on scroll.
  - Settings moved to end. i18n keys added (en/ru/zh).

- [x] **C3 — Saved views / recent activity** [Claude]
  - Compact activity strip showing recent searches, watchlist items, tracked queries.
  - Discovery chips clickable — one tap re-runs the search.
  - Color-coded: green=discovery, blue=watchlist, purple=query.

- [x] **C4 — Empty states and first-value UX** [Claude]
  - renderEmptyState() helper with icon, title, body, and scroll-and-focus CTA.
  - seedEmptyStates() seeds 7 dashboard sections on boot with contextual guidance.

- [x] **C5 — Frontend icon system standardization** [Antigravity]
  - Created `icons.js` — centralized Heroicons (outline, 24×24) icon system with 24 icons
  - `icon(name, cls, size)` function renders SVG strings from stored path data
  - Replaced ALL emoji UI icons and ALL inline SVGs across the frontend
  - Universal `data-icon` injection on page load; 7 CSS icon utility classes
  - Zero emojis and zero inline SVGs remaining in HTML/JS
  - Files: `dashboard/frontend/icons.js` [NEW], `index.html`, `app.js`, `styles.css`, `sw.js`

- [x] **C6 — PWA mobile adaptation and smooth app usage redesign** [Antigravity]
  - Added `viewport-fit=cover` for notch/dynamic island phones
  - Safe area insets: shell, footer, and PWA banner respect `env(safe-area-inset-*)`
  - iOS zoom prevention: all inputs forced to `16px` below `640px`
  - New `480px` breakpoint: compact shell, tighter padding, horizontal-scroll nav, single-column analytics
  - 44px minimum tap targets on all buttons/interactive elements below `480px`
  - Discovery cards: tighter mobile spacing, wrapping metrics and actions
  - Touch-friendly states: `@media (hover: none)` removes hover transforms, adds `:active` press feedback
  - Standalone PWA mode: hides install banner, adds top safe-area padding on nav
  - Hero section compact on small screens (1.3rem h1, 0.85rem subtitle)
  - Files: `dashboard/frontend/index.html`, `styles.css`

- [x] **C7 — PWA install guidance banner** [Antigravity]
  - Fixed bottom glassmorphic banner: `backdrop-filter: blur(16px)`, slide-up animation
  - Captures `beforeinstallprompt` event (Chrome/Edge) to trigger native install prompt
  - iOS/Safari fallback: shows banner after 10s on mobile user-agents
  - 7-day dismiss cooldown via `localStorage` (`dropagent.pwa_dismissed`)
  - Auto-hides in standalone PWA mode via `@media (display-mode: standalone)`
  - Install button triggers `prompt()` → hides banner; Dismiss sets cooldown
  - i18n: all 3 languages (EN/RU/ZH) with `pwa.install_title/desc/btn/dismiss_btn` keys
  - Heroicon integration: uses `arrow-top-right-on-square` icon via `data-icon`
  - Mobile responsive: stacks vertically at `480px`, full-width buttons
  - Files: `dashboard/frontend/index.html`, `app.js`, `styles.css`

---

## Phase D — Hosted Public Launch Readiness

Purpose: move from "it can be hosted" to "it is safe and clear to launch".

- [x] **D1 — Public bot startup flow audit** [Claude]
  - Dashboard deep-link auto-fills chat_id + username from URL params.
  - /start moved to top of router (was 2nd-to-last after 20+ checks).
  - Onboarding keyboard buttons i18n in EN/RU/ZH.
  - common.welcome shows quick-action hints for returning users.

- [x] **D2 — Vercel + Supabase env completeness** [Claude]
  - Applied 3 missing Supabase migrations (saved_store_leads, discovery_runs, alert_events).
  - Added TELEGRAM_WEBHOOK_SECRET, DASHBOARD_PUBLIC_URL, APP_SECRET_KEY to .env.example.
  - Fixed vercel.json `"framework": null` to stop build error (was picking up WSGI entrypoint).

- [x] **D3 — Telegram webhook launch checklist implementation** [Claude]
  - Documented setWebhook curl command, getWebhookInfo verify step, deleteWebhook rollback in HOSTED_MODE.md.
  - bot/webhook.py and api/telegram/webhook.py confirmed complete and wired to vercel.json.

- [x] **D4 — Hosted security hardening** [Claude]
  - Enabled RLS on all 11 Supabase tables (deny anon by default; service role bypasses).
  - HOSTED_MODE.md updated: documents RLS posture and warns against exposing DATABASE_URL in frontend.
  - verify_webhook_secret skips check only when TELEGRAM_WEBHOOK_SECRET is unset — safe for dev, enforce in prod.

---

## Phase E — Final Product Hardening

Purpose: finish the last boring-but-important 10%.

- [~] **E1 — Error-state hardening** [Claude]
  - Improve user-facing errors for missing keys, failed external APIs, rate limits, and partial discovery results.
  - Files: `dashboard/backend/api.py`, `dashboard/backend/service.py`, `bot/main.py`, `i18n/`

- [x] **E2 — Docs cleanup** [Antigravity]
  - README.md: test badge (384), Discovery Hub, Service Adapters, Hosted Mode, adapters directory
  - All 4 language READMEs (en/ru/zh/az) updated with current test count
  - Dashboard frontend README rewritten: 5-tab Heroicons nav, PWA install banner, mobile-first, zero emojis
  - Fixed `saved.item_id` → `saved.id` bug in `db/service.py:917` (watchlist alert metadata)
  - Fixed stale test assertions in `test_db.py` (alert count, watchlist ID access)
  - Verified: zero stale emoji refs, zero stale nav refs, all hosted docs accurate

- [x] **E3 — Task/docs hygiene** [Claude]
  - Refreshed board: updated Live Dispatch, progress %, product state.
  - Removed stale "Immediate Next Recommendation" section.
  - Completed task notes updated to reflect actual implementations.

- [x] **E4 — Final UX + regression pass** [Claude]
  - /start new user → onboarding; returning user → quick-action hints. Both verified.
  - /calc, /settings, /help, /status, /language all respond correctly.
  - i18n completeness verified: all keys present in ru and zh.
  - nav/phase/activity LABELS keys added to all 3 dashboard language blocks (were missing, would show as raw keys).
  - 384 tests passing.

---

## Remaining Work

- **Claude** — E1 (in progress: error-state hardening)
- **Codex** — idle, ready for next backend-safe split
- **Antigravity** — idle, ready for assignment

All other tracked tasks are complete. `E1` is the last active task on the board.

---

## Completed Foundations

- Margin calculator
- eBay sold scanner
- Source connectors: Amazon, Walmart, AliExpress, CJ
- Comparator engine
- Daily digest + scheduler + CLI
- Telegram bot core + onboarding
- Dashboard backend + frontend base
- Multi-user DB layer
- Watchlist + price history + alerts
- Competitor tracker + store leads + alerts
- Weekly category report
- Listing generator
- Google Trends + Reddit signals
- Hosted mode: Vercel + Supabase + webhook + RLS security
- Encrypted user-owned service keys
- Keepa, StoreLeads, PiPiADS integration paths
- Discovery Hub: actionable actions, memory layer, discovery-based alerts
- Heroicons icon system (zero emojis)
- PWA: service worker, manifest, offline support, install banner
- Mobile-first: safe areas, 44px tap targets, touch states, 480px breakpoint
- Dashboard workflow nav (5-tab, Heroicons, IntersectionObserver)
- Docs: all 4 README languages, dashboard README, hosted mode docs

---

Last refreshed: `2026-04-10` by Antigravity
