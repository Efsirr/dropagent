# Agent Coordination Protocol

## Purpose

This file defines how Codex, Claude, and Antigravity should coordinate work in this repository without conflicting with each other.

Use this together with [TASKS.md](/Users/efsir/Projects/Dropshipping%20agent(Totik)/TASKS.md).

`TASKS.md` is the live board.
This file is the operating protocol behind that board.

## Active Agents

- `Codex`
- `Claude`
- `Antigravity`

If another agent joins later, add it explicitly before assigning work.

## Source Of Truth

- Task ownership lives in [TASKS.md](/Users/efsir/Projects/Dropshipping%20agent(Totik)/TASKS.md)
- Repo-structure cleanup context lives in [docs/internal/REPO_HYGIENE_HANDOFF.md](/Users/efsir/Projects/Dropshipping%20agent(Totik)/docs/internal/REPO_HYGIENE_HANDOFF.md)
- This file defines the coordination rules

If there is a conflict between chat assumptions and `TASKS.md`, follow `TASKS.md`.

## Status Markers

Use these markers consistently:

- `[ ]` not started
- `[~]` claimed / in progress
- `[x]` done
- `[blocked]` waiting on another agent or decision

Ownership format:

- `[~] **Task name** [Codex]`
- `[~] **Task name** [Claude]`
- `[~] **Task name** [Antigravity]`
- `[blocked] **Task name** [Codex -> Claude]`

## Claim Rules

Before any agent starts coding:

1. Read `TASKS.md`
2. Check whether the task is already claimed
3. Add the agent name beside the task
4. Add or update the file scope if needed
5. Only then start implementation

No agent should begin coding first and update the board later.

## File Scope Rule

Every in-progress task should declare its intended file area when there is any chance of overlap.

Examples:

- `Files: dashboard/frontend/app.js, dashboard/frontend/index.html, dashboard/frontend/styles.css`
- `Files: agent/discovery.py, db/service.py, tests/test_discovery.py`

If two agents need the same file area, they must not work in parallel unless the split is explicit and safe.

## Default Ownership Split

Use this split unless the task clearly calls for something else.

### Codex

Owns:

- backend logic
- persistence
- alerts
- APIs
- integrations
- env/deployment mechanics
- migrations
- tests for backend behavior

Usually touches:

- `agent/`
- `db/`
- `dashboard/backend/`
- `tests/`
- infra docs

### Claude

Owns:

- dashboard UX
- onboarding clarity
- empty states
- wording
- visual polish
- user-facing flow cleanup

Usually touches:

- `dashboard/frontend/`
- user-facing docs
- copy-heavy areas

### Antigravity

Owns:

- discovery UX concepts
- interaction shaping
- card layout refinement
- workflow cohesion across surfaces

Usually touches:

- `dashboard/frontend/`
- discovery-specific presentation layers
- lightweight product-surface docs when needed

## Conflict Prevention Rules

### Safe parallel work

Safe:

- Codex in `agent/` and `db/` while Claude works in `dashboard/frontend/`
- Codex on backend APIs while Antigravity improves layout that consumes existing endpoints
- Claude on empty states while Antigravity works on different frontend sections

Unsafe without explicit split:

- Claude and Antigravity both editing `dashboard/frontend/app.js`
- Codex and another agent both editing shared API contract files
- multiple agents changing the same README or root process doc at the same time

## When A Task Must Be Split

If a task spans backend and frontend, split it into sub-items in `TASKS.md`.

Good:

- `A2a backend save-store action [Codex]`
- `A2b dashboard discovery action UI [Claude]`

Bad:

- one broad task claimed by two agents with no file boundary

## Handoff Rules

When an agent pauses or finishes:

- update the task marker
- leave a short note under the task if context matters
- mention blockers, touched files, and next obvious step

Short handoff note format:

- `Note: backend API done; frontend wiring still needed`
- `Files touched: dashboard/backend/api.py, tests/test_dashboard_api.py`
- `Next: Claude can wire button state and success feedback`

## Blocked State

If a task cannot continue because another agent owns a dependency, mark it explicitly:

- `[blocked] **B1 — Discovery-based alerts UI** [Claude -> Codex]`

That means:

- Claude is waiting
- Codex owns the dependency
- nobody should silently duplicate the missing work

## DevOps Agent Behavior

If a chat is acting as the coordination or DevOps agent, its job is:

- keep `TASKS.md` current
- prevent duplicate claims
- split unsafe parallel work into sub-tasks
- redirect agents to different scopes when collisions appear
- preserve context in docs instead of leaving it trapped in chat history

This role should avoid large feature edits unless the user explicitly asks for them.

## Recommended Workflow

1. Coordination agent refreshes `TASKS.md`
2. Codex claims backend-heavy task
3. Claude claims UX-heavy task
4. Antigravity claims discovery-polish or flow task
5. Each agent updates status before and after implementation
6. Cross-agent dependencies are marked as `blocked`, not silently assumed

## Current Intent

At the moment, the repository should be coordinated around:

- Codex for actionable discovery, alerts, hosted mechanics, backend hardening
- Claude for empty states, clarity, onboarding, and public-facing polish
- Antigravity for Discovery Hub experience and dashboard cohesion

## Last Updated

2026-04-10
