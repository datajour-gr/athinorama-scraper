# AGENTS

This repository is intended for building a scraper for theatre performances on `athinorama.gr`.

If you use multiple agents, split the work by responsibility and file ownership so changes do not collide.

## Shared Goal

Build a respectful, resumable scraper that:

- discovers theatre performance URLs from `https://www.athinorama.gr/theatre/`
- scrapes each `/theatre/performance/` detail page
- exports structured JSON and CSV
- includes tests and checkpoints

## Agent Roles

### 1. Discovery Agent

Owns:

- `athinorama_scraper/discovery.py`
- `tests/test_discovery.py`
- seed-page fixtures related to URL extraction

Responsibilities:

- parse the theatre seed page
- locate `Όλες οι Παραστάσεις`
- collect only performance-detail URLs
- normalize and deduplicate links
- expose a clean function that returns unique URLs and IDs

### 2. Detail Parser Agent

Owns:

- `athinorama_scraper/parse_detail.py`
- `athinorama_scraper/models.py`
- `tests/test_parse_detail.py`

Responsibilities:

- parse one performance page into a structured record
- handle optional and missing fields
- keep raw text fallbacks when normalization is uncertain
- support multiple venue blocks

### 3. Pipeline Agent

Owns:

- `athinorama_scraper/fetch.py`
- `athinorama_scraper/pipeline.py`
- `athinorama_scraper/storage.py`
- `athinorama_scraper/cli.py`

Responsibilities:

- fetching, retries, throttling, checkpointing, export
- safe resume behavior
- JSON / CSV output generation
- run summary reporting

### 4. QA Agent

Owns:

- extra fixtures under `tests/fixtures/`
- parser regression tests
- end-to-end smoke test coverage

Responsibilities:

- compare parsed output against the reference page
- catch selector drift early
- verify duplicate handling and schema consistency

## Coordination Rules

- Do not change another agent's owned files unless necessary to unblock integration.
- If cross-file changes are required, keep them minimal and note them clearly.
- Do not weaken throttling or safety rules to improve speed.
- Prefer deterministic parsing over clever but brittle heuristics.
- Preserve Greek text exactly; normalize only into additional fields.

## Non-Negotiables

- Respect `robots.txt`, site terms, and reasonable request pacing.
- Do not bypass auth, rate limits, or anti-bot measures.
- Do not scrape non-theatre sections unless requirements change.
- Keep outputs reproducible and resumable.

## Definition of Done

The project is ready when:

- unique performance URLs are discovered reliably
- detail pages parse into a stable schema
- exports are produced successfully
- tests cover discovery and the reference detail page
- a run can resume after interruption
