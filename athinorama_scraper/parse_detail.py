"""Parse a single performance detail page into a structured record."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag, NavigableString

from .models import Performance, Venue

logger = logging.getLogger(__name__)

# ── URL parsing ──────────────────────────────────────────────────────────

_SLUG_ID_RE = re.compile(r"/theatre/performance/([\w_]+)-(\d+)/?$")


def parse_url(url: str) -> tuple[str | None, str | None]:
    """Extract (slug, performance_id) from a performance URL."""
    m = _SLUG_ID_RE.search(url)
    if m:
        return m.group(1), m.group(2)
    return None, None


# ── Date normalization ───────────────────────────────────────────────────

_DATE_DD_MM_YYYY = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")


def _normalize_date(text: str) -> str | None:
    """Convert DD/MM/YYYY to ISO YYYY-MM-DD."""
    m = _DATE_DD_MM_YYYY.search(text)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return f"{y:04d}-{mo:02d}-{d:02d}"
        except ValueError:
            return None
    return None


# ── Duration parsing ─────────────────────────────────────────────────────

_DURATION_RE = re.compile(r"(\d+)\s*[΄'′΄']")


def _parse_duration(text: str) -> int | None:
    m = _DURATION_RE.search(text)
    return int(m.group(1)) if m else None


# ── Main parser ──────────────────────────────────────────────────────────

def parse_performance(html: str, source_url: str) -> Performance:
    """Parse a performance detail page into a Performance record."""
    soup = BeautifulSoup(html, "lxml")
    slug, perf_id = parse_url(source_url)

    perf = Performance(
        source_url=source_url,
        performance_id=perf_id or "",
        slug=slug,
        scraped_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
    )

    # ── Title ────────────────────────────────────────────────────────
    h1 = soup.find("h1")
    if h1:
        perf.title = h1.get_text(strip=True)

    # ── Duration ─────────────────────────────────────────────────────
    duration_span = soup.find("span", class_="duration")
    if duration_span:
        perf.duration_text = duration_span.get_text(strip=True)
        perf.duration_minutes = _parse_duration(perf.duration_text)

    # ── Tags: category, author, director ─────────────────────────────
    tags_ul = soup.find("ul", class_="review-tags")
    if tags_ul:
        for a_tag in tags_ul.find_all("a"):
            text = a_tag.get_text(strip=True)
            if text.startswith("Σκηνοθ"):
                perf.director_text = text
            elif text.startswith("του ") or text.startswith("της ") or text.startswith("των "):
                perf.author_text = text
            else:
                if not perf.category:
                    perf.category = text

    # ── Description ──────────────────────────────────────────────────
    summary_div = soup.find("div", class_="summary")
    if summary_div:
        # Get the first direct summary div (not the one inside venues)
        # The summary div we want is a sibling of the review-tags ul
        parent = summary_div
        # Check it's at the top level (not inside location blocks)
        if not parent.find_parent("div", class_="location"):
            perf.description = parent.get_text(strip=True)

    # ── Credits ──────────────────────────────────────────────────────
    hr_tag = soup.find("hr")
    if hr_tag:
        next_p = hr_tag.find_next_sibling("p")
        if next_p:
            perf.credits_text = next_p.get_text(strip=True)

    # ── Run until ────────────────────────────────────────────────────
    for h4 in soup.find_all("h4"):
        h4_text = h4.get_text(strip=True)
        if "Παραστάσεις" in h4_text and "έως" in h4_text:
            # The date is in the next <a> or text node
            next_a = h4.find_next("a")
            if next_a:
                text = next_a.get_text(strip=True)
                perf.run_until_text = text
                perf.run_until_iso = _normalize_date(text)
            break

    # ── Venues ───────────────────────────────────────────────────────
    perf.venues = _parse_venues(soup)

    # ── Ticket URLs ──────────────────────────────────────────────────
    perf.ticket_urls = _parse_ticket_urls(soup)

    return perf


def _parse_venues(soup: BeautifulSoup) -> list[Venue]:
    """Parse venue blocks from the page.

    Structure: div.location contains:
    - div.sticky-breaker-title > h2 > a (area name)
    - div.item.card-item (venue card with name, address, phone)
    - div.item.horizontal-dt (schedule/price block)
    """
    venues: list[Venue] = []
    locations_list = soup.find("div", class_="locations-list")
    if not locations_list:
        return venues

    for location_div in locations_list.find_all("div", class_="location", recursive=False):
        venue = Venue()

        # Area name from sticky-breaker-title > h2
        area_div = location_div.find("div", class_="sticky-breaker-title")
        if area_div:
            h2 = area_div.find("h2")
            if h2:
                venue.area = h2.get_text(strip=True)

        # Venue name from item-title h2
        card = location_div.find("div", class_="card-item")
        if card:
            title_h2 = card.find("h2", class_="item-title")
            if title_h2:
                venue.venue_name = title_h2.get_text(strip=True)

            # Address from <address> or div.details
            address_tag = card.find("address")
            if address_tag:
                venue.address = address_tag.get_text(strip=True)
            else:
                details_div = card.find("div", class_="details")
                if details_div:
                    venue.address = details_div.get_text(strip=True)

            # Phone from tel: link
            phone_a = card.find("a", href=lambda h: h and h.startswith("tel:"))
            if phone_a:
                venue.phone = phone_a["href"].replace("tel:", "")

        # Schedule, price, until from schedule-infos
        sched_ul = location_div.find("ul", class_="schedule-infos")
        if sched_ul:
            for inner in sched_ul.find_all("div", class_="inner"):
                label = inner.find("strong", class_="room-box")
                if not label:
                    continue
                label_text = label.get_text(strip=True)

                if "Παραστάσεις" in label_text:
                    sched_div = inner.find("div", class_="schedules")
                    if sched_div:
                        venue.schedule_summary = sched_div.get_text(strip=True)
                elif "Τιμές" in label_text:
                    # Price is a text node after the <strong>
                    price_text = _get_text_after_element(inner, label)
                    if price_text:
                        venue.price_text = price_text.strip()
                    if not venue.price_text:
                        venue.price_text = inner.get_text(strip=True).replace(label_text, "").strip()

        # Until short text: look for <strong>Εως:</strong> followed by date
        for strong in location_div.find_all("strong"):
            strong_text = strong.get_text(strip=True)
            if "ως" in strong_text.lower():
                li = strong.find_parent("li")
                if li:
                    venue.until_short_text = li.get_text(strip=True)
                else:
                    next_text = _get_text_after_element(strong.parent, strong)
                    if next_text:
                        venue.until_short_text = f"{strong_text}{next_text.strip()}"

        # Daily schedule from <time> elements
        for time_tag in location_div.find_all("time"):
            text = time_tag.get_text(strip=True)
            if text:
                venue.daily_schedule.append(text)

        venues.append(venue)

    return venues


def _get_text_after_element(container: Tag, element: Tag) -> str | None:
    """Get the text node immediately after an element within container."""
    found = False
    for child in container.children:
        if child is element:
            found = True
            continue
        if found and isinstance(child, NavigableString):
            text = str(child).strip()
            if text:
                return text
    return None


def _parse_ticket_urls(soup: BeautifulSoup) -> list[str]:
    """Extract external ticket purchase URLs."""
    ticket_urls: list[str] = []
    ticket_domains = {"more.com", "viva.gr", "ticketservices", "public.gr", "cosmote.gr"}

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        text = a_tag.get_text(strip=True)

        if not href.startswith("http"):
            continue

        is_ticket = (
            "Αγόρασε" in text
            or "εισιτήρι" in text.lower()
            or any(domain in href for domain in ticket_domains)
        )
        # Exclude false positives that are actually performance links
        if is_ticket and "/theatre/performance/" not in href:
            if href not in ticket_urls:
                ticket_urls.append(href)

    return ticket_urls
