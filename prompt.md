You are Claude Opus working in a fresh repository. Build a respectful, resumable scraper for **Athinorama theatre performances** on `athinorama.gr`.

Goal:

- Scrape all theatre performance detail pages reachable from `https://www.athinorama.gr/theatre/`
- Use this reference detail page to validate the parser:
  - `https://www.athinorama.gr/theatre/performance/o_kos_zul-10089257/`

Important assumption:

- Interpret "all performances" as all theatre performance pages under the Athinorama theatre section, because the reference URL is a theatre performance page.

What I want you to deliver:

1. A Python 3.11+ scraper project.
2. A CLI entry point to run discovery + scraping end to end.
3. Structured outputs in:
   - `data/performances.json`
   - `data/performances.csv`
   - `data/run_summary.json`
4. Basic tests and saved HTML fixtures for:
   - the theatre seed page
   - the reference performance page
5. Checkpointing / resume support so interrupted runs can continue.

Use this crawl strategy unless live HTML proves otherwise:

1. Start at `https://www.athinorama.gr/theatre/`
2. Locate the `Όλες οι Παραστάσεις` section
3. Extract every unique link matching `/theatre/performance/`
4. Normalize to absolute URLs
5. Deduplicate by URL and by the numeric ID at the end of the slug
6. Visit each detail page and parse structured fields

If the `Όλες οι Παραστάσεις` section is unavailable or incomplete, fall back to scanning the full theatre page for `/theatre/performance/` links, and only then consider paginated theatre listing pages.

Preferred stack:

- `httpx`
- `beautifulsoup4`
- `lxml`
- `pytest`
- `pydantic` or `dataclasses`

Use Playwright only if direct HTTP cannot retrieve the needed HTML reliably.

For each performance detail page, extract as much of the following as is available:

- `source_url`
- `performance_id`
- `slug`
- `title`
- `duration_text`
- `duration_minutes`
- `category`
- `author_text`
- `director_text`
- `description`
- `credits_text`
- `run_until_text`
- `run_until_iso`
- `venues[]`
- `ticket_urls[]`
- `scraped_at`

Each `venues[]` item should support:

- `area`
- `venue_name`
- `address`
- `phone`
- `schedule_summary`
- `price_text`
- `until_short_text`
- `daily_schedule[]`

Implementation requirements:

- Keep network, parsing, models, storage, and CLI separated into different modules.
- Preserve Greek text exactly in raw fields.
- Normalize dates to ISO where possible.
- Treat missing fields as normal; do not crash on sparse pages.
- Keep raw-text fallbacks for brittle fields.
- Save logs and a run summary.
- Add retries only for transient failures.
- Use conservative rate limiting:
  - concurrency `1-2`
  - jittered delays, e.g. `1.5-3.0s`
- Use a descriptive user agent.
- Respect `robots.txt` and the site’s terms before broad runs.
- Do not bypass anti-bot controls, auth gates, or access restrictions.

Please create a clean project layout like:

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
  test_discovery.py
  test_parse_detail.py
data/
```

Validation requirements:

- Prove that discovery returns a non-zero set of performance URLs.
- Prove that the reference page parses the correct title and performance ID.
- Prove that duplicate URLs do not produce duplicate output rows.
- Ensure JSON and CSV export the same number of records.

Working style:

- Inspect the live HTML first; do not invent selectors.
- Prefer robust text-anchored parsing over brittle CSS-class chains.
- Make small, readable commits or change groups.
- At the end, summarize:
  - discovered URL count
  - successfully scraped count
  - failed count
  - output file paths
  - any assumptions or known parser limitations
