"""Storage: JSON/CSV export and checkpoint management."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

from . import config
from .models import Performance

logger = logging.getLogger(__name__)


# ── Checkpoint ───────────────────────────────────────────────────────────

def load_checkpoint() -> set[str]:
    """Load set of already-scraped performance IDs from checkpoint file."""
    if config.CHECKPOINT_PATH.exists():
        try:
            data = json.loads(config.CHECKPOINT_PATH.read_text(encoding="utf-8"))
            ids = set(data.get("scraped_ids", []))
            logger.info("Loaded checkpoint with %d scraped IDs", len(ids))
            return ids
        except (json.JSONDecodeError, KeyError):
            logger.warning("Corrupt checkpoint file, starting fresh")
    return set()


def save_checkpoint(scraped_ids: set[str]) -> None:
    """Save scraped performance IDs to checkpoint file."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = {"scraped_ids": sorted(scraped_ids)}
    config.CHECKPOINT_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def append_checkpoint(perf_id: str, scraped_ids: set[str]) -> None:
    """Add a single ID and persist immediately for crash safety."""
    scraped_ids.add(perf_id)
    save_checkpoint(scraped_ids)


# ── JSON export ──────────────────────────────────────────────────────────

def save_json(performances: list[Performance], path: Path | None = None) -> Path:
    """Export performances to JSON."""
    path = path or config.PERFORMANCES_JSON
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [p.to_dict() for p in performances]
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("Saved %d records to %s", len(data), path)
    return path


# ── CSV export ───────────────────────────────────────────────────────────

def save_csv(performances: list[Performance], path: Path | None = None) -> Path:
    """Export performances to CSV (venues/tickets as JSON strings)."""
    path = path or config.PERFORMANCES_CSV
    path.parent.mkdir(parents=True, exist_ok=True)

    if not performances:
        path.write_text("", encoding="utf-8")
        return path

    rows = [p.flat_dict() for p in performances]
    fieldnames = list(rows[0].keys())

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info("Saved %d records to %s", len(rows), path)
    return path


# ── Run summary ──────────────────────────────────────────────────────────

def save_run_summary(summary: dict, path: Path | None = None) -> Path:
    """Save run summary to JSON."""
    path = path or config.RUN_SUMMARY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("Run summary saved to %s", path)
    return path


# ── Load existing records (for resume) ───────────────────────────────────

def load_existing_performances() -> list[Performance]:
    """Load previously exported performances from JSON for resume merge."""
    if not config.PERFORMANCES_JSON.exists():
        return []
    try:
        data = json.loads(config.PERFORMANCES_JSON.read_text(encoding="utf-8"))
        performances = []
        for d in data:
            venues_data = d.pop("venues", [])
            from .models import Venue
            venues = [Venue(**v) for v in venues_data]
            performances.append(Performance(**d, venues=venues))
        logger.info("Loaded %d existing performance records", len(performances))
        return performances
    except Exception as exc:
        logger.warning("Could not load existing performances: %s", exc)
        return []
