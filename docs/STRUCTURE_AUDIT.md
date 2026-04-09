# Repository Structure Audit

## Overall Verdict

The project already has a solid feature-oriented backbone for a future GitHub repository:

- `agent/`, `bot/`, `dashboard/`, `db/`, `i18n/`, and `tests/` are sensible top-level domains
- module-level READMEs exist in important areas
- Docker, environment example, migrations, and tests are already present

The main weakness is not architecture. It is repository hygiene.

## What Looks Good

- Clear separation between core logic, delivery channels, database, and UI
- Tests are organized in a dedicated `tests/` directory
- CLI wrappers exist for important workflows
- Database migrations live in a conventional location
- The dashboard frontend/backend split is easy to understand

## Problems To Fix Before Treating This As a Clean GitHub Project

### 1. Weak root-level documentation

Before this audit, the repo had no root `README.md`. That is one of the first things GitHub visitors expect.

What should stay strong at the root:

- `README.md`
- `.env.example`
- `docker-compose.yml`
- `Dockerfile`
- `requirements.txt`
- one clear contribution/workflow document if needed

### 2. Local or generated files are mixed into the repo story

These are the biggest cleanup candidates:

- `.DS_Store`
  - macOS junk file
  - already ignored, but still tracked in git
  - should be removed from version control
- `.pytest_cache/`
  - generated test cache
  - already ignored, but should never be committed
- `.planning/`
  - useful for local agent workflows, but not part of the product itself
  - should be either ignored or explicitly documented as internal-only

Potentially unnecessary for a public OSS repo unless intentionally part of the workflow:

- `CLAUDE.md`
  - appears to overlap with `AGENTS.md`
- `.impeccable.md`
  - useful design context, but currently reads more like internal working guidance than public project docs
- `TASKS.md`
  - can be fine, but often becomes stale in public repos unless actively maintained

### 3. Root is starting to collect too many executable files

Current root CLI files:

- `calc.py`
- `digest.py`
- `trends.py`
- `weekly_report.py`

This is acceptable for an early-stage tool, but long-term it gets noisy.

Recommended future direction:

- move these into `scripts/`
- or create a package like `dropagent/cli/`

Example:

```text
scripts/
├── calc.py
├── digest.py
├── trends.py
└── weekly_report.py
```

or

```text
dropagent/
└── cli/
    ├── calc.py
    ├── digest.py
    ├── trends.py
    └── weekly_report.py
```

### 4. Top-level package naming is still transitional

`agent/` works internally, but for a public Python project it is generic.

Longer-term GitHub-ready option:

```text
dropagent/
├── core/
├── integrations/
├── bot/
├── dashboard/
└── cli/
```

This is not urgent, but it would age better if the project becomes a real installable package.

### 5. Public-vs-internal docs are not clearly separated

Right now the repo contains:

- user/project instructions
- AI collaboration instructions
- design instructions
- task board

That is useful during development, but on GitHub it can feel messy if everything sits at the root.

Recommended split:

- keep `README.md` public-facing
- keep `AGENTS.md` only if AI-collaboration is a deliberate project feature
- move internal process docs into `docs/internal/`

## Current “Trash” or Cleanup Candidates

High confidence trash:

- `.DS_Store`
- `.pytest_cache/`

Likely internal-only and worth relocating or ignoring:

- `.planning/`
- `.impeccable.md`

Needs a deliberate decision:

- `CLAUDE.md`
- `TASKS.md`

Not trash:

- `.github/copilot-instructions.md`
  - acceptable if you want AI coding guidance in the repo
- module `README.md` files
- root CLI files
  - messy long-term, but not wrong

## Recommended Target Structure

For the next cleanup pass, this would be a strong GitHub-friendly shape:

```text
.
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── AGENTS.md
├── docs/
│   ├── STRUCTURE_AUDIT.md
│   ├── architecture.md
│   ├── setup.md
│   └── internal/
│       ├── tasks.md
│       └── design-guidelines.md
├── scripts/
│   ├── calc.py
│   ├── digest.py
│   ├── trends.py
│   └── weekly_report.py
├── agent/
├── bot/
├── dashboard/
├── db/
├── i18n/
└── tests/
```

## Priority Cleanup Order

1. Remove tracked junk files from git
2. Keep root focused on public-facing project files
3. Move internal workflow docs under `docs/internal/`
4. Move root CLI scripts into `scripts/` or package them properly
5. Add `LICENSE` and contribution guidance

## Bottom Line

This repository is not trash. The feature structure is actually pretty good.

The issue is that it still feels like an active local workspace rather than a polished public repository. With a small cleanup pass around docs, root layout, and generated files, it can look very solid on GitHub.
