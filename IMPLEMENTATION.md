# Athinorama Theatre Scraper Implementation

## Scope

This project is for scraping **theatre performance pages** from `athinorama.gr`, based on the reference detail page:

- `https://www.athinorama.gr/theatre/performance/o_kos_zul-10089257/`

Assumption: "all performances" means the theatre-performance catalog reachable from:

- `https://www.athinorama.gr/theatre/`

This assumption is based on the reference URL and on the observed structure of the theatre section on **March 24, 2026**.

## Observed Site Structure

The theatre landing page contains an `Όλες οι Παραστάσεις` section with links to performance detail pages.

Observed patterns:

- Seed page: `https://www.athinorama.gr/theatre/`
- Detail page pattern: `https://www.athinorama.gr/theatre/performance/<slug>-<numeric_id>/`
- A detail page contains, when available:
  - title
  - duration
  - category / genre
  - author text
  - director text
  - long description
  - credits / cast block
  - run-until date
  - one or more venue blocks
  - address
  - phone
  - schedule summary
  - price text
  - per-day schedule lines
  - external ticket link

The theatre page also contains extra sections such as articles, reviews, venues, categories, and regions. The scraper must ignore those and collect only links matching the theatre performance detail pattern.

## Recommended Stack

Prefer a simple, server-rendered-first stack:

- Python 3.11+
- `httpx` for HTTP
- `beautifulsoup4` with `lxml` parser for HTML parsing
- `tenacity` or custom retry logic
- `pydantic` or `dataclasses` for structured records
- `pytest` for tests

Use Playwright only if direct HTTP fetching cannot retrieve the required HTML reliably.

## Crawl Strategy

### 1. Discovery

Start from:

- `https://www.athinorama.gr/theatre/`

From that page:

- locate the `Όλες οι Παραστάσεις` section
- collect all anchor tags whose `href` matches `/theatre/performance/`
- resolve relative URLs to absolute URLs
- deduplicate by:
  - normalized absolute URL
  - extracted numeric performance ID

Fallback if the `Όλες οι Παραστάσεις` block cannot be parsed:

- scan the full page for any `/theatre/performance/` links
- if needed, crawl paginated theatre listing pages and apply the same filter

### 2. Detail Scrape

Visit each unique performance URL and extract the structured record.

The parser should be resilient to:

- missing fields
- reordered blocks
- Greek labels with small punctuation differences
- multiple venue blocks on the same performance page

### 3. Persistence

Write outputs to:

- `data/performances.json`
- `data/performances.csv`
- `data/run_summary.json`

Also keep:

- a checkpoint file with processed URLs / IDs
- structured logs for failures and retries

## Proposed Output Schema

```json
{
  "source_url": "https://www.athinorama.gr/theatre/performance/o_kos_zul-10089257/",
  "source_site": "athinorama.gr",
  "scraped_at": "2026-03-24T18:00:00Z",
  "performance_id": "10089257",
  "slug": "o_kos_zul",
  "title": "Ο κος Ζυλ",
  "duration_text": "90'",
  "duration_minutes": 90,
  "category": "Κοινωνικό",
  "author_text": "του Θωμά Μοσχόπουλου",
  "director_text": "Σκηνοθ.: Θ. Μοσχόπουλος",
  "description": "full normalized description text",
  "credits_text": "Ερμηνεύουν: ...",
  "run_until_text": "05/04/2026",
  "run_until_iso": "2026-04-05",
  "venues": [
    {
      "area": "Αμπελόκηποι",
      "venue_name": "Πόρτα",
      "address": "Λεωφ. Μεσογείων 59, Αμπελόκηποι",
      "phone": "2107711333",
      "schedule_summary": "Παρ., Σάβ. 9 μ.μ., Κυρ. 8 μ.μ.",
      "price_text": "€ 20-12.",
      "until_short_text": "05/04",
      "daily_schedule": [
        "Παρασκευή 13 Μαρ. 21:00",
        "Σάββατο 14 Μαρ. 21:00",
        "Κυριακή 15 Μαρ. 20:00"
      ]
    }
  ],
  "ticket_urls": [
    "https://www.more.com/..."
  ],
  "raw_text_blocks": {
    "header": "...",
    "body": "...",
    "venue_sections": ["..."]
  }
}
```

## Parsing Rules

Use normalized UTF-8 text and preserve Greek characters.

Recommended rules:

- `performance_id`: final numeric segment in the detail-page slug
- `title`: main page title
- `duration_minutes`: parse digits from duration text if present
- `description`: join narrative paragraphs before credits / venue sections
- `credits_text`: keep as raw text if fine-grained parsing is brittle
- `run_until_iso`: convert `DD/MM/YYYY` to ISO when the year is present
- `venues`: always model as an array, even if only one venue exists
- `ticket_urls`: collect external ticketing links, do not assume only `more.com`

When a field is unavailable:

- store `null` for scalar normalized fields
- store `[]` for empty arrays
- keep the raw text block if present

## Anti-Brittleness Rules

- Anchor discovery on URL patterns first, not page cosmetics
- Prefer headings and nearby labels over absolute DOM positions
- Avoid depending on CSS classes unless they are clearly stable
- Save a few HTML fixtures locally for regression tests
- Keep raw text alongside normalized fields so parser refinements are possible later

## Rate Limiting and Safety

The scraper should behave conservatively:

- default concurrency: `1-2`
- add jittered delay between requests, for example `1.5-3.0s`
- retry only transient failures
- use a descriptive user agent
- respect `robots.txt` and site terms before broad runs
- do not attempt to bypass anti-bot controls, login walls, or access restrictions

## Suggested Project Layout

```text
athinorama_scraper/
  __init__.py
  cli.py
  config.py
  discovery.py
  fetch.py
  models.py
  parse_detail.py
  pipeline.py
  storage.py
tests/
  fixtures/
    theatre_index.html
    performance_o_kos_zul.html
  test_discovery.py
  test_parse_detail.py
data/
```

## Validation Plan

Minimum validation:

- confirm the theatre seed page yields a non-zero set of detail URLs
- confirm the reference page parses the expected title and performance ID
- confirm at least one venue block is extracted from the reference page
- confirm JSON and CSV exports contain the same record count
- confirm duplicate URLs do not create duplicate output rows

Good validation additions:

- snapshot tests for the reference page
- a second fixture with a different structure
- a run summary showing:
  - discovered URL count
  - scraped success count
  - skipped duplicate count
  - failed count

## Acceptance Criteria

The implementation is successful when it:

- discovers all reachable theatre performance URLs from the theatre section
- extracts structured data from each detail page without crashing on missing fields
- produces stable JSON and CSV outputs
- can resume after interruption
- includes at least basic tests and one saved reference fixture
- uses conservative request behavior
