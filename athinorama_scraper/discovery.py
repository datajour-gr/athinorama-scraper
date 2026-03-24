"""Discover theatre performance URLs from the Athinorama theatre section."""

from __future__ import annotations

import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from . import config

logger = logging.getLogger(__name__)

# Matches /theatre/performance/<slug>-<numeric_id>/
_PERF_HREF_RE = re.compile(r"/theatre/performance/([\w_]+)-(\d+)/?$")


def extract_performance_urls(html: str, base_url: str = config.SEED_URL) -> list[dict]:
    """Extract unique performance URLs from a theatre listing page.

    Returns list of dicts with keys: url, performance_id, slug.
    Deduplicates by performance_id.
    """
    soup = BeautifulSoup(html, "lxml")
    seen_ids: set[str] = set()
    results: list[dict] = []

    # Strategy 1: Find the "Όλες οι Παραστάσεις" accordion button,
    # then get its next sibling (the accordion-panel with all perf links).
    links_to_scan: list = []
    for btn_div in soup.find_all("div", class_="accordion-button"):
        text = btn_div.get_text(strip=True)
        if re.search(r"Όλες\s+οι\s+Παραστάσεις", text):
            panel = btn_div.find_next_sibling("div", class_="accordion-panel")
            if panel:
                links_to_scan = panel.find_all("a", href=True)
                logger.info(
                    "Found 'Όλες οι Παραστάσεις' accordion panel with %d links",
                    len(links_to_scan),
                )
            break

    # Fallback: scan entire page for performance links
    if not links_to_scan:
        links_to_scan = soup.find_all("a", href=True)
        logger.info("Fallback: scanning full page (%d links)", len(links_to_scan))

    for a_tag in links_to_scan:
        href = a_tag.get("href", "")
        m = _PERF_HREF_RE.search(href)
        if not m:
            continue
        slug, perf_id = m.group(1), m.group(2)
        if perf_id in seen_ids:
            continue
        seen_ids.add(perf_id)
        abs_url = urljoin(base_url, href)
        results.append({
            "url": abs_url,
            "performance_id": perf_id,
            "slug": slug,
        })

    logger.info("Extracted %d unique performance URLs", len(results))
    return results


async def discover_all(fetcher) -> list[dict]:
    """Discover all performance URLs from the theatre section.

    The seed page contains all performance links in an accordion panel,
    so pagination is not needed.
    """
    logger.info("Fetching seed page: %s", config.SEED_URL)
    html = await fetcher.fetch(config.SEED_URL)
    if html is None:
        logger.error("Failed to fetch seed page")
        return []

    results = extract_performance_urls(html)
    logger.info("Discovery complete: %d unique performance URLs", len(results))
    return results
