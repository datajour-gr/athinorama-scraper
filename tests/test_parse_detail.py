"""Tests for the detail page parser."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from athinorama_scraper.parse_detail import parse_performance, parse_url
from athinorama_scraper.storage import save_json, save_csv
from athinorama_scraper import config

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REF_URL = "https://www.athinorama.gr/theatre/performance/o_kos_zul-10089257/"


def _load_fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


class TestUrlParsing:
    def test_parse_url_reference(self):
        slug, perf_id = parse_url(REF_URL)
        assert slug == "o_kos_zul"
        assert perf_id == "10089257"

    def test_parse_url_no_match(self):
        slug, perf_id = parse_url("https://example.com/other/")
        assert slug is None
        assert perf_id is None


class TestReferencePageParsing:
    def setup_method(self):
        html = _load_fixture("performance_o_kos_zul.html")
        self.perf = parse_performance(html, REF_URL)

    def test_title(self):
        assert self.perf.title == "Ο κος Ζυλ"

    def test_performance_id(self):
        assert self.perf.performance_id == "10089257"

    def test_slug(self):
        assert self.perf.slug == "o_kos_zul"

    def test_duration(self):
        assert self.perf.duration_minutes == 90
        assert "90" in self.perf.duration_text

    def test_category(self):
        assert self.perf.category == "Κοινωνικό"

    def test_author(self):
        assert "Μοσχόπουλου" in self.perf.author_text

    def test_director(self):
        assert "Σκηνοθ" in self.perf.director_text
        assert "Μοσχόπουλος" in self.perf.director_text

    def test_description(self):
        assert self.perf.description is not None
        assert "Τζούλια" in self.perf.description

    def test_credits(self):
        assert self.perf.credits_text is not None
        assert "Ερμηνεύουν" in self.perf.credits_text

    def test_run_until(self):
        assert self.perf.run_until_text == "26/04/2026"
        assert self.perf.run_until_iso == "2026-04-26"

    def test_has_venue(self):
        assert len(self.perf.venues) >= 1

    def test_venue_details(self):
        v = self.perf.venues[0]
        assert v.area == "Αμπελόκηποι"
        assert v.venue_name == "Πόρτα"
        assert "Μεσογείων" in v.address
        assert v.phone == "2107711333"

    def test_venue_schedule(self):
        v = self.perf.venues[0]
        assert v.schedule_summary is not None
        assert "μ.μ." in v.schedule_summary

    def test_venue_price(self):
        v = self.perf.venues[0]
        assert v.price_text is not None
        assert "€" in v.price_text or "20" in v.price_text

    def test_venue_until_short(self):
        v = self.perf.venues[0]
        assert v.until_short_text is not None
        assert "26/04" in v.until_short_text

    def test_daily_schedule(self):
        v = self.perf.venues[0]
        assert len(v.daily_schedule) > 0
        assert any("21:00" in d for d in v.daily_schedule)

    def test_ticket_urls(self):
        assert len(self.perf.ticket_urls) >= 1
        assert "more.com" in self.perf.ticket_urls[0]

    def test_scraped_at(self):
        assert self.perf.scraped_at is not None
        assert self.perf.scraped_at.endswith("Z")

    def test_source_url(self):
        assert self.perf.source_url == REF_URL


class TestExportConsistency:
    """Verify JSON and CSV export the same number of records."""

    def test_json_csv_same_count(self, tmp_path):
        html = _load_fixture("performance_o_kos_zul.html")
        perf = parse_performance(html, REF_URL)
        performances = [perf]

        json_path = save_json(performances, tmp_path / "test.json")
        csv_path = save_csv(performances, tmp_path / "test.csv")

        with open(json_path, encoding="utf-8") as f:
            json_data = json.load(f)

        with open(csv_path, encoding="utf-8") as f:
            lines = f.readlines()
            csv_count = len(lines) - 1  # minus header

        assert len(json_data) == csv_count == 1


class TestMissingFields:
    """Parser should not crash on minimal HTML."""

    def test_empty_page(self):
        perf = parse_performance("<html><body></body></html>", REF_URL)
        assert perf.performance_id == "10089257"
        assert perf.title is None
        assert perf.venues == []
        assert perf.ticket_urls == []

    def test_title_only(self):
        perf = parse_performance(
            "<html><body><h1>Test Show</h1></body></html>",
            REF_URL,
        )
        assert perf.title == "Test Show"
        assert perf.duration_minutes is None
