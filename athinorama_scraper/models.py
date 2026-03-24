"""Data models for scraped performance records."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Venue:
    area: Optional[str] = None
    venue_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    schedule_summary: Optional[str] = None
    price_text: Optional[str] = None
    until_short_text: Optional[str] = None
    daily_schedule: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Performance:
    source_url: str
    performance_id: str
    slug: Optional[str] = None
    title: Optional[str] = None
    duration_text: Optional[str] = None
    duration_minutes: Optional[int] = None
    category: Optional[str] = None
    author_text: Optional[str] = None
    director_text: Optional[str] = None
    description: Optional[str] = None
    credits_text: Optional[str] = None
    run_until_text: Optional[str] = None
    run_until_iso: Optional[str] = None
    venues: list[Venue] = field(default_factory=list)
    ticket_urls: list[str] = field(default_factory=list)
    scraped_at: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    def flat_dict(self) -> dict:
        """Flattened dict for CSV export (venues/tickets as JSON strings)."""
        import json
        d = self.to_dict()
        d["venues"] = json.dumps(d["venues"], ensure_ascii=False)
        d["ticket_urls"] = json.dumps(d["ticket_urls"], ensure_ascii=False)
        return d
