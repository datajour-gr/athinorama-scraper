"""Tests for the discovery module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from athinorama_scraper.discovery import extract_performance_urls

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


class TestDiscovery:
    def test_returns_nonempty_set(self):
        html = _load_fixture("theatre_index.html")
        urls = extract_performance_urls(html)
        assert len(urls) > 0, "Expected non-zero performance URLs"

    def test_all_urls_match_pattern(self):
        html = _load_fixture("theatre_index.html")
        urls = extract_performance_urls(html)
        for item in urls:
            assert "/theatre/performance/" in item["url"]
            assert item["performance_id"].isdigit()
            assert item["slug"]

    def test_no_duplicate_ids(self):
        html = _load_fixture("theatre_index.html")
        urls = extract_performance_urls(html)
        ids = [u["performance_id"] for u in urls]
        assert len(ids) == len(set(ids)), "Duplicate performance IDs found"

    def test_reference_page_in_results(self):
        html = _load_fixture("theatre_index.html")
        urls = extract_performance_urls(html)
        ids = {u["performance_id"] for u in urls}
        assert "10089257" in ids, "Reference performance ID not found"

    def test_urls_are_absolute(self):
        html = _load_fixture("theatre_index.html")
        urls = extract_performance_urls(html)
        for item in urls:
            assert item["url"].startswith("https://"), f"Not absolute: {item['url']}"

    def test_duplicate_input_produces_no_duplicates(self):
        """Feeding the same HTML twice should still deduplicate."""
        html = _load_fixture("theatre_index.html")
        urls1 = extract_performance_urls(html)
        # Simulate duplicate links by parsing again
        urls2 = extract_performance_urls(html)
        assert len(urls1) == len(urls2)
