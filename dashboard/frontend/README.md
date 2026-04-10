# DropAgent Dashboard Frontend

This directory contains the static analytics-first frontend for the DropAgent dashboard.

What it does:
- Loads a user profile by Telegram chat id
- Shows setup baseline status and recommended integrations
- Shows one clear next step so non-technical users know what to do next
- Shows compact overview metrics for the current user
- **Discovery Hub** — unified search across StoreLeads (stores), PiPiADS (ads), Google Trends
- **Workflow navigation** — sticky 5-tab nav (Profile / Research / Track / Reports / Tools) with Heroicons + IntersectionObserver
- **Discovery history** — recent runs with re-run buttons, localStorage persistence
- Updates settings for language, min profit, max buy price, sources, and schedule
- Saves business model and integration selections from the web onboarding block
- Lists tracked queries in a simplified table
- Visualizes watchlist price history with inline charts
- Manages competitor sellers and runs seller scans
- Previews weekly category reports
- Adds and removes tracked queries
- Previews a saved digest
- Runs the margin calculator
- Sends notifications via Discord, Email, and Google Sheets

Implementation notes:
- Plain HTML, CSS, and JavaScript only — no framework, no build step
- Talks to the existing backend API under `/api`
- Designed to be easy to serve from any static host or the backend server
- PWA-ready: service worker, manifest.json, offline support, install banner
- Multi-language: EN / RU / ZH with data-i18n attribute system
- Optimized for a calm dashboard workflow instead of spreadsheet-style export-first usage
- Uses simple feature gating: baseline-required actions are clearly marked
- Heroicons (outline, 24×24) icon system — zero emojis, zero inline SVGs
- Score badges (hot / warm / cool) for trend and ad signals
- Shimmer loading animations during API calls
- Mobile-first: safe area insets, 44px tap targets, touch-friendly states, compact 480px layout
