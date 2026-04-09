# DropAgent — Copilot / Codex Instructions

This file mirrors the project instructions in `CLAUDE.md` and `AGENTS.md`.
For full project context, read `CLAUDE.md` in the repo root.
For the shared task board, read `TASKS.md` before starting work.

---

## Design Context

### Users
**Primary:** eBay resellers running US retail arbitrage (Amazon/Walmart → eBay). They spend hours a day scanning marketplaces looking for price gaps. They are **not designers or developers** — they are small business operators who want tools that are fast, trustworthy, and make them money.

**Secondary:** China-model dropshippers (AliExpress/CJ → Shopify/eBay).

**Context of use:** Long research sessions, often morning routine. Scanning dozens of products, running margin calculations, reading digest reports. They need a tool that doesn't fatigue their eyes and makes financial decisions obvious.

**Job to be done:** "Show me which products will make me money today — fast, clearly, without making me do math in my head."

### Brand Personality

**Three words:** Friendly · Trustworthy · Money-positive

**Voice:** Direct and encouraging. Not corporate, not playful-to-a-fault. Like a knowledgeable friend who happens to know eBay inside-out. Uses plain language ("Net Profit" not "Adjusted Net Revenue").

**Emotional goals:**
- **Confidence** — users should trust the numbers
- **Calm** — long research sessions shouldn't feel draining
- **Anticipation** — "what will I find today?" not "ugh, another tool"

### Aesthetic Direction

**Theme:** Soft dark — think Linear, Raycast, Cal.com. Dark but not pitch black. Background should feel like "low-light workspace" not "hacker terminal".

**Color philosophy:** Money is the hero. **Emerald green** is the primary accent — it signals profit, go, success. Cyan/blue felt cold and technical; green feels positive and on-brand for a dropshipping tool. Red is reserved exclusively for losses/errors so it carries weight.

**References (what we want to feel like):**
- **Linear** — soft dark, calm, generous whitespace, clear hierarchy
- **Raycast** — friendly without being cute, great typography
- **Cal.com** — approachable and trustworthy
- **Stripe Dashboard** — data-rich but never overwhelming

**Anti-references (what we do NOT want):**
- Sci-fi / hacker aesthetic (no cyan glows, no radial gradients, no "matrix" vibes)
- Pitch-black backgrounds (fatiguing)
- Corporate blue fintech (too cold, too stiff)
- Flashy SaaS landing page (we're a tool, not a marketing page)
- Dense Bloomberg-terminal layouts (users aren't quants)

**Typography:**
- **Inter** for UI — clean, friendly, excellent number legibility
- Generous line-height (1.5–1.6 for body text)
- Numbers should be emphasized with `font-variant-numeric: tabular-nums` so columns align

### Design Principles

1. **Money is the hero.** Profit numbers are the largest, greenest, boldest thing on screen. Every other visual decision supports making those numbers pop.

2. **Soft, not harsh.** Backgrounds are soft dark (`#0b0d12`), borders are subtle (`#24272f`), corners are rounded (14–20px), shadows are light. Nothing jarring.

3. **Breathing room over density.** Generous padding, clear grouping, whitespace between sections. Users should never feel crowded.

4. **Clarity over decoration.** No gradients on cards, no radial background glows, no unnecessary animation. Every pixel earns its place by helping the user understand or decide.

5. **Friendly plain language.** "Net Profit" not "Adjusted Revenue". "Load profile" not "Initialize context". Empty states are reassuring, not cryptic.

### Color Tokens

```
Background:        #0b0d12  (soft dark, slight warmth)
Surface:           #13161d  (cards, flat — NO gradients)
Surface elevated:  #1a1e27  (hover states, modals)
Border:            #24272f  (subtle dividers)
Border strong:     #2e323c  (card outlines)

Text primary:      #e8ecf1  (warm white, never pure #fff)
Text secondary:    #9ba3b4  (labels, helper text)
Text muted:        #6b7280  (placeholders, disabled)

Accent primary:    #10b981  (emerald — MONEY, profit, success, primary CTA)
Accent hover:      #059669  (darker emerald for hover)
Accent soft:       rgba(16, 185, 129, 0.12)  (subtle green tint backgrounds)

Secondary accent:  #6366f1  (indigo — for non-money actions like language, info)

Profit:            #10b981  (same as primary)
Loss:              #f87171  (soft red — never pure red)
Warning:           #f59e0b  (amber)
Info:              #6366f1  (indigo)
```

### Radii

```
Small:   8px   (badges, tags, small buttons)
Medium:  12px  (inputs, standard buttons)
Large:   16px  (cards, containers)
XL:      20px  (hero / main panels)
```

### Spacing

Base unit: 4px. Use multiples: 4, 8, 12, 16, 20, 24, 32, 40, 48.

Cards: 24–28px internal padding.
Sections: 20–24px gap between.
Form rows: 14–16px gap.

---

*The canonical design context lives in `.impeccable.md`. Keep both files in sync when updating.*
