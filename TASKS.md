# DropAgent — Unified Task Board

One roadmap. One source of truth.

Goal: take DropAgent from a strong working core to a polished, public-friendly, daily-use product for dropshippers.

Current honest progress: about `90%`.
Target: push the project to the closest realistic `100%` by finishing workflow completeness, hosted readiness, and product polish.

---

## Live Dispatch

Use this section as the immediate assignment board for parallel work.

- **Codex**
  - Task: `B2 — Watchlist alerts`
  - Status: `[~] in progress`
  - Files: `db/`, `bot/`, `dashboard/backend/`, `tests/`
  - Do not touch: `dashboard/frontend/` unless a frontend split is recorded

- **Claude**
  - Task: `E3 — Task/docs hygiene` (this cleanup), then `E4 — Final UX + regression pass`
  - Status: `[~] in progress`
  - Files: `TASKS.md`, `dashboard/frontend/` (E4)
  - Do not touch: backend files, discovery-specific UI owned by Antigravity

- **Antigravity**
  - Task: `E2 — Docs cleanup`
  - Status: `[/] in progress`
  - Files: `README.md`, `README.ru.md`, `README.zh.md`, `README.az.md`, `docs/`
  - Do not touch: `TASKS.md` while Claude is doing E3

---

## Rules

- Read this file before starting work.
- Coordination protocol lives in [docs/internal/AGENT_COORDINATION.md](/Users/efsir/Projects/Dropshipping%20agent(Totik)/docs/internal/AGENT_COORDINATION.md).
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
- Watchlist + competitor alerts (B2 in progress, B3 unclaimed)
- Alert rules panel for users (B4)
- Frontend icon system consistency (C5)
- Hosted deployment docs and env hardening (D2, D3, D4)
- Error-state hardening across all surfaces (E1)
- Final UX regression pass (E4)

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

- [~] **B2 — Watchlist alerts** [Codex]
  - Trigger when buy price drops, sell price rises, or spread improves.
  - Reuse Telegram as primary channel.
  - Files: `db/`, `bot/`, `dashboard/backend/`, `tests/`

- [ ] **B3 — Competitor alerts**
  - Alert when tracked sellers add new items or shift category behavior.

- [ ] **B4 — Alert rules panel**
  - Simple dashboard section for enabling/disabling alert types.
  - No noisy enterprise settings. Keep it human.

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

- [~] **C5 — Frontend icon system standardization** [Antigravity]
  - Use only Heroicons across the frontend.
  - Remove mixed icon usage (emoji used as UI icons, inconsistent SVG sets).
  - Keep icon treatment consistent across all surfaces.
  - Files: `dashboard/frontend/index.html`, `app.js`, `styles.css`

---

## Phase D — Hosted Public Launch Readiness

Purpose: move from "it can be hosted" to "it is safe and clear to launch".

- [x] **D1 — Public bot startup flow audit** [Claude]
  - Dashboard deep-link auto-fills chat_id + username from URL params.
  - /start moved to top of router (was 2nd-to-last after 20+ checks).
  - Onboarding keyboard buttons i18n in EN/RU/ZH.
  - common.welcome shows quick-action hints for returning users.

- [ ] **D2 — Vercel + Supabase env completeness**
  - Verify required env vars, deployment assumptions, and migration path.
  - Ensure docs match the real hosted architecture.

- [ ] **D3 — Telegram webhook launch checklist implementation**
  - Verify webhook setup path is complete and documented from inside the repo.

- [ ] **D4 — Hosted security hardening**
  - Review secret handling, unsafe responses, and public exposure risks.
  - Add missing protections if any are found.

---

## Phase E — Final Product Hardening

Purpose: finish the last boring-but-important 10%.

- [ ] **E1 — Error-state hardening**
  - Improve user-facing errors for missing keys, failed external APIs, rate limits, and partial discovery results.

- [/] **E2 — Docs cleanup** [Antigravity]
  - Update README, hosted docs, and setup docs to match the current product exactly.
  - Remove stale references and duplicate explanations.

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

## Remaining Parallel Split

- **Codex** — B2 (in progress), B3, B4, D2, D3, D4, E1
- **Claude** — E4, C5
- **Antigravity** — E2 (in progress), C5 (can split with Claude)

Safe split: Codex on backend/infra, Claude on UX/regression, Antigravity on docs + discovery polish.

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
- Watchlist + price history
- Competitor tracker + store leads
- Weekly category report
- Listing generator
- Google Trends + Reddit signals
- Hosted mode foundation
- Encrypted user-owned service keys
- Keepa, StoreLeads, PiPiADS integration paths
- Discovery Hub base + actionable actions
- Discovery memory layer
- Alert infrastructure (discovery-based)

---

Last refreshed: `2026-04-10` by Claude (E3)
