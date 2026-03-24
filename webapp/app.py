"""Simple Flask webapp to display top Athens theatre performances."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path

from flask import Flask, render_template, request

DATA_PATH = Path(__file__).parent.parent / "data" / "performances.json"

app = Flask(__name__)

# Normalize near-duplicate category names to a canonical form.
_CATEGORY_ALIASES: dict[str, str] = {
    "Δραματοποιημένο Μυθιστόρημα": "Δραματοποιημένο",
    "Δραματοποιημένο Διήγημα": "Δραματοποιημένο",
    "Δραματοποιημένη Νουβέλα": "Δραματοποιημένο",
    "Δραματοποιημένη λογοτεχνία": "Δραματοποιημένο",
    "Δραματοποιημένη Λογοτεχνία": "Δραματοποιημένο",
    "Δραματοποιημένο Αφήγημα": "Δραματοποιημένο",
    "Δραματοποιημένο ποίημα": "Δραματοποιημένο",
    "Stand up comedy – Music show": "Stand Up Comedy",
    "Stand up Comedy": "Stand Up Comedy",
    "Μουσικό Θέατρο": "Μουσικό / Μιούζικαλ",
    "Μουσικοθεατρική": "Μουσικό / Μιούζικαλ",
    "Μουσική Παράσταση": "Μουσικό / Μιούζικαλ",
    "Μιούζικαλ": "Μουσικό / Μιούζικαλ",
    "Κουκλοθέατρο": "Παιδικό / Κουκλοθέατρο",
    "Θέατρο Κούκλας": "Παιδικό / Κουκλοθέατρο",
    "Θέατρο Σκιών": "Παιδικό / Κουκλοθέατρο",
    "Χορευτική performance": "Performance / Χορός",
    "Performance/Εγκατάσταση": "Performance / Χορός",
    "Performance": "Performance / Χορός",
    "Χοροθέατρο": "Performance / Χορός",
    "Χορός": "Performance / Χορός",
}

# Categories with fewer than this many performances are grouped under "Άλλο".
_MIN_COUNT = 5


def _normalize_category(cat: str | None) -> str | None:
    if cat is None:
        return None
    return _CATEGORY_ALIASES.get(cat, cat)


def _score(p: dict) -> int:
    """Rank a performance by data completeness as a proxy for quality coverage."""
    s = 0
    if p.get("description"):
        s += 3
    if p.get("credits_text"):
        s += 2
    if p.get("director_text"):
        s += 1
    if p.get("author_text"):
        s += 1
    if p.get("ticket_urls"):
        s += 2
    if p.get("duration_minutes"):
        s += 1
    run_until = p.get("run_until_iso")
    if run_until and run_until >= date.today().isoformat():
        s += 1
    return s


def _load() -> list[dict]:
    with open(DATA_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # Attach normalized category in-place so the template can use it.
    for p in raw:
        p["_category"] = _normalize_category(p.get("category"))
    return raw


def _build_filter_list(performances: list[dict]) -> list[tuple[str, int]]:
    """Return (canonical_category, count) sorted by count descending.

    Categories below _MIN_COUNT are omitted (shown as "Άλλο" in the template).
    """
    counts: Counter[str] = Counter(
        p["_category"] for p in performances if p.get("_category")
    )
    return [(cat, n) for cat, n in counts.most_common() if n >= _MIN_COUNT]


@app.route("/")
def index() -> str:
    category = request.args.get("category", "")
    performances = _load()

    filters = _build_filter_list(performances)

    if category:
        performances = [p for p in performances if p.get("_category") == category]

    performances.sort(key=_score, reverse=True)
    top = performances[:50]

    return render_template(
        "index.html",
        performances=top,
        filters=filters,
        selected_category=category,
        total=len(performances),
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
