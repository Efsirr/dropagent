# DropAgent Dashboard Frontend

This directory contains the initial static frontend for the DropAgent dashboard.

What it does:
- Loads a user profile by Telegram chat id
- Updates settings for language, min profit, max buy price, sources, and schedule
- Lists tracked queries
- Adds and removes tracked queries
- Previews a saved digest
- Runs the margin calculator

Implementation notes:
- Plain HTML, CSS, and JavaScript only
- Talks to the existing backend API under `/api`
- Designed to be easy to serve from any static host or the backend server
