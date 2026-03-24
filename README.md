# Athinorama Theatre Scraper

A scraper for theatre performances listed on [athinorama.gr](https://www.athinorama.gr/theatre/), plus a small webapp to browse the results.

## What it does

1. **Discovers** every theatre performance URL from the athinorama.gr theatre section
2. **Fetches** each detail page conservatively (jittered delays, retries, low concurrency)
3. **Parses** each page into a structured record: title, venue, schedule, price, description, credits, director, run-until date, and ticket links
4. **Saves** results to `data/performances.json` and `data/performances.csv`
5. **Resumes** from a checkpoint if interrupted
6. **Displays** results in a filterable webapp sorted by content quality

## Project structure

```
athinorama_scraper/   # Scraper package
  discovery.py        # Finds all performance URLs from the seed page
  fetch.py            # HTTP client with rate limiting and retries
  parse_detail.py     # Parses a detail page into a Performance record
  pipeline.py         # Orchestrates discovery, fetching, parsing, and export
  storage.py          # JSON/CSV export and checkpoint management
  models.py           # Performance and Venue dataclasses
  cli.py              # Command-line entry point
webapp/
  app.py              # Flask webapp
  templates/
    index.html        # Card grid UI with category filters
data/
  performances.json   # Scraped output (391 records)
  performances.csv    # Flattened CSV export
tests/
  fixtures/           # Saved HTML for offline testing
  test_discovery.py
  test_parse_detail.py
```

## Setup

```bash
pip install -r requirements.txt
```

## Run the scraper

```bash
python -m athinorama_scraper.cli
```

Outputs are written to `data/`. Re-running resumes from the checkpoint and skips already-scraped pages.

## Run the webapp

```bash
python3 webapp/app.py
```

Open `http://127.0.0.1:5000`. The webapp shows the top 50 performances ranked by data completeness, with category filters.

## Run the tests

```bash
pytest
```

## Data schema

Each performance record includes:

| Field | Description |
|---|---|
| `title` | Performance title |
| `performance_id` | Numeric ID from the URL |
| `category` | Genre (e.g. Κωμωδία, Δράμα) |
| `description` | Full description text |
| `author_text` | Playwright credit |
| `director_text` | Director credit |
| `credits_text` | Full cast and crew |
| `duration_minutes` | Duration in minutes |
| `run_until_iso` | Last performance date (ISO format) |
| `venues` | List of venue blocks (name, area, address, phone, schedule, price) |
| `ticket_urls` | External ticketing links |
