# DropAgent Dashboard Frontend

This directory contains the static analytics-first frontend for the DropAgent dashboard.

What it does:
- Loads a user profile by Telegram chat id
- Shows setup baseline status and recommended integrations
- Shows one clear next step so non-technical users know what to do next
- Shows compact overview metrics for the current user
- Updates settings for language, min profit, max buy price, sources, and schedule
- Saves business model and integration selections from the web onboarding block
- Lists tracked queries in a simplified table
- Visualizes watchlist price history with inline charts
- Manages competitor sellers and runs seller scans
- Previews weekly category reports
- Adds and removes tracked queries
- Previews a saved digest
- Runs the margin calculator

Implementation notes:
- Plain HTML, CSS, and JavaScript only
- Talks to the existing backend API under `/api`
- Designed to be easy to serve from any static host or the backend server
- Optimized for a calm dashboard workflow instead of spreadsheet-style export-first usage
- Uses simple feature gating: baseline-required actions are clearly marked instead of hidden behind technical language
