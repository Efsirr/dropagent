# DropAgent — Unified Task Board

One roadmap. One source of truth.

Goal: take DropAgent from a strong working core to a polished, public-friendly, daily-use product for dropshippers.

Current honest progress: about `78%`.
Target: push the project to the closest realistic `100%` by finishing workflow completeness, hosted readiness, and product polish.

---

## Rules

- Read this file before starting work.
- Claim tasks by adding `[Codex]` or `[Antigravity]` if parallel work is active.
- Never claim the same file-heavy task in parallel without an explicit split.
- Run `python3 -m pytest tests/ -q` before closing a task.
- Keep the product simple for non-technical users.
- Prefer shipping complete user workflows over adding isolated features.

---

## Product State

Already strong:
- Core scanner, margin engine, digest, weekly report
- Telegram bot
- Dashboard
- Multi-user DB
- Watchlist, competitor tracker, listing generator
- Hosted mode foundation
- User-owned integrations with encrypted storage
- Discovery Hub
- Keepa, StoreLeads, PiPiADS live paths

Still missing to feel “done”:
- Discovery actions into saved workflows
- Alert system tied to real discoveries
- Hosted launch hardening and public bot flow
- More complete dashboard workflow UX
- Production hardening / cleanup / final docs

---

## Phase A — Actionable Discovery

Purpose: turn discovery from “interesting data” into “do something with this now”.

- [x] **A1 — Discovery actions: save query from Discovery Hub** [Codex]
  - Add action from discovery results to tracked queries.
  - User should be able to save a niche/keyword in one click.
  - Wire into digest and weekly flows naturally.

- [ ] **A2 — Discovery actions: save store to competitor workflow**
  - Let user save a discovered store/domain as a monitored competitor lead.
  - If needed, create a separate “store leads” saved list instead of forcing it into eBay seller tracker.

- [ ] **A3 — Discovery actions: save product/ad into watchlist workflow**
  - Allow simple “watch this” action from discovery results.
  - Keep the UX simple: one click, minimal required fields.

- [ ] **A4 — Discovery memory layer**
  - Save discovery runs/history per user.
  - Show recent discovery searches in dashboard.
  - Make repeated research feel persistent, not disposable.

---

## Phase B — Alerts That Matter

Purpose: make the system proactive, not only reactive to manual checks.

- [ ] **B1 — Discovery-based alerts**
  - Alert when a tracked discovery query shows stronger signals than before.
  - Examples: more competitor stores, stronger ad score, stronger search movement.

- [ ] **B2 — Watchlist alerts**
  - Trigger when buy price drops, sell price rises, or spread improves.
  - Reuse Telegram as primary channel.

- [ ] **B3 — Competitor alerts**
  - Alert when tracked sellers add new items or shift category behavior.

- [ ] **B4 — Alert rules panel**
  - Simple dashboard section for enabling/disabling alert types.
  - No noisy enterprise settings. Keep it human.

---

## Phase C — Dashboard Workflow Completion

Purpose: make dashboard feel like one calm daily workspace.

- [/] **C1 — Discovery Hub polish** [Antigravity] in progress
  - Add better cards, compact summaries, and clear next actions.
  - Make it obvious what the user should save or ignore.

- [ ] **C2 — Daily workflow layout**
  - Tighten flow between Discovery, Digest, Watchlist, Competitors.
  - Reduce the feeling of “separate tools”.

- [ ] **C3 — Saved views / recent activity**
  - Show recent discovery runs, latest alerts, and recently changed tracked items.

- [~] **C4 — Empty states and first-value UX** [Claude — in progress]
  - Improve zero-data experience in dashboard for first-time hosted users.
  - Explain what to do next in plain language.

---

## Phase D — Hosted Public Launch Readiness

Purpose: move from “it can be hosted” to “it is safe and clear to launch”.

- [ ] **D1 — Public bot startup flow audit**
  - End-to-end pass on `/start`, `/setup`, dashboard deep-link, service connection.
  - Make first-run path obvious for non-technical users.

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

Purpose: finish the last boring-but-important 10-15%.

- [ ] **E1 — Error-state hardening**
  - Improve user-facing errors for missing keys, failed external APIs, rate limits, and partial discovery results.

- [ ] **E2 — Docs cleanup**
  - Update README, hosted docs, and setup docs to match the current product exactly.
  - Remove stale references and duplicate explanations.

- [ ] **E3 — Task/docs hygiene**
  - Keep this single board current.
  - Remove stale planning leftovers if any remain.

- [ ] **E4 — Final UX + regression pass**
  - End-to-end sanity pass across bot + dashboard.
  - Validate main workflows:
    - setup
    - connect service
    - discovery
    - save
    - digest
    - alerts

---

## Recommended Parallel Split

If both Codex and Claude are working:

- **Codex**
  - A1, A2, A3, A4
  - B1, B2, B3, B4
  - D2, D3, D4
  - E1

- **Claude**
  - C1, C2, C3, C4
  - D1
  - E2, E4

Safe split principle:
- Codex focuses on backend logic, persistence, alerts, hosted mechanics.
- Claude focuses on dashboard UX, clarity, onboarding, product surface polish.

---

## Immediate Next Recommendation

Start here:

- [x] **A1 — Discovery actions: save query from Discovery Hub** [Codex]

Reason:
- it is the cleanest continuation from the current Discovery Hub work
- it turns discovery into workflow
- it unlocks better digest + alerts naturally

Then:

- [ ] **C1 — Discovery Hub polish** [Antigravity]

Reason:
- while backend makes discovery actionable, frontend can make those actions feel obvious and pleasant

---

## Completed Foundations

These are already done and do not need separate task files anymore:

- Margin calculator
- eBay sold scanner
- Source connectors: Amazon, Walmart, AliExpress, CJ
- Comparator engine
- Daily digest + scheduler + CLI
- Telegram bot core
- Dashboard backend + frontend base
- Multi-user DB layer
- Watchlist + price history
- Competitor tracker
- Weekly category report
- Listing generator
- Google Trends + Reddit signals
- Hosted mode foundation
- Encrypted user-owned service keys
- Keepa integration path
- StoreLeads integration path
- PiPiADS integration path
- Discovery Hub base

---

Last refreshed: `2026-04-10`
