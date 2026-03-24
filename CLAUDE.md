# CLAUDE

## Project Context

You are working on a scraper for theatre performances on `athinorama.gr`.

Primary targets:

- Seed page: `https://www.athinorama.gr/theatre/`
- Reference detail page: `https://www.athinorama.gr/theatre/performance/o_kos_zul-10089257/`

Interpret "all performances" as all theatre performance detail pages discoverable from the theatre section, unless the user says otherwise.

## What To Build

Build a small, production-lean scraper that:

- discovers every unique theatre performance URL
- fetches each detail page conservatively
- parses the page into structured records
- saves JSON and CSV outputs
- can resume after interruption
- includes tests using saved HTML fixtures

## Technical Preferences

- Prefer Python 3.11+
- Prefer `httpx` + `BeautifulSoup` + `lxml`
- Use Playwright only if direct HTTP is not enough
- Keep the implementation simple and readable
- Use type hints
- Keep parsing logic separate from network and storage code

## Parsing Guidance

From each detail page, try to extract:

- title
- performance ID from URL
- duration text and minutes
- category
- author text
- director text
- description
- credits text
- run-until date
- venue name
- area
- address
- phone
- schedule summary
- price text
- daily schedule lines
- ticket URLs

Treat missing fields as normal. The scraper should not fail just because one page omits a block.

## Discovery Guidance

Start from the theatre seed page and use the `Όλες οι Παραστάσεις` section as the primary discovery source.

Only keep links matching the theatre performance pattern:

- `/theatre/performance/`

Ignore:

- articles
- reviews
- venue pages
- category pages
- region pages
- ticketing domains

## Safety and Respect

- Use low concurrency and throttling.
- Add jittered delays between requests.
- Respect `robots.txt` and site terms before broad runs.
- Do not bypass anti-bot protections or gated content.

## Quality Bar

- Favor robust text-anchored parsing over fragile selector chains.
- Keep raw text fallbacks for fields that may drift.
- Save HTML fixtures for the theatre index and the reference detail page.
- Add tests for URL discovery, detail parsing, and duplicate handling.

## Deliverables

Expected project outputs:

- scraper code
- tests
- fixtures
- `data/performances.json`
- `data/performances.csv`
- `data/run_summary.json`

## Working Style

- Make small, reviewable changes.
- Verify behavior locally after changes.
- If the site structure differs from expectations, update the parser based on the live HTML rather than guessing.
