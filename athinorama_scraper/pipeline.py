"""Pipeline: orchestrates discovery → fetch → parse → store."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from . import config
from .discovery import discover_all
from .fetch import Fetcher
from .models import Performance
from .parse_detail import parse_performance
from .storage import (
    append_checkpoint,
    load_checkpoint,
    load_existing_performances,
    save_checkpoint,
    save_csv,
    save_json,
    save_run_summary,
)

logger = logging.getLogger(__name__)


async def run_pipeline(limit: int = 0) -> dict:
    """Run the full scraping pipeline. Returns a run summary dict.

    Args:
        limit: Max detail pages to scrape (0 = all).
    """
    start_time = datetime.utcnow()
    fetcher = Fetcher()

    try:
        # ── Discovery ────────────────────────────────────────────────
        logger.info("Starting discovery phase")
        discovered = await discover_all(fetcher)
        logger.info("Discovered %d unique performance URLs", len(discovered))

        if not discovered:
            logger.error("No performance URLs discovered, aborting")
            return _make_summary(start_time, 0, 0, 0, [])

        # ── Resume support ───────────────────────────────────────────
        scraped_ids = load_checkpoint()
        existing = load_existing_performances()
        performances: list[Performance] = list(existing)
        existing_ids = {p.performance_id for p in existing}

        to_scrape = [
            d for d in discovered
            if d["performance_id"] not in scraped_ids
        ]
        skipped = len(discovered) - len(to_scrape)
        logger.info(
            "Scraping %d URLs (%d already checkpointed)",
            len(to_scrape), skipped,
        )

        # ── Apply limit ─────────────────────────────────────────────
        if limit > 0:
            to_scrape = to_scrape[:limit]
            logger.info("Limiting to %d pages", limit)

        # ── Scrape detail pages (concurrent) ─────────────────────────
        success_count = 0
        fail_count = 0
        total = len(to_scrape)

        async def _scrape_one(item: dict) -> Performance | None:
            url = item["url"]
            html = await fetcher.fetch(url)
            if html is None:
                logger.error("Failed to fetch %s", url)
                return None
            try:
                return parse_performance(html, url)
            except Exception:
                logger.exception("Failed to parse %s", url)
                return None

        batch_size = config.MAX_CONCURRENCY
        for batch_start in range(0, total, batch_size):
            batch = to_scrape[batch_start : batch_start + batch_size]
            logger.info(
                "[%d-%d/%d] Scraping batch of %d",
                batch_start + 1,
                min(batch_start + batch_size, total),
                total,
                len(batch),
            )
            results = await asyncio.gather(
                *(_scrape_one(item) for item in batch)
            )
            for item, perf in zip(batch, results):
                if perf is None:
                    fail_count += 1
                    continue
                if perf.performance_id not in existing_ids:
                    performances.append(perf)
                    existing_ids.add(perf.performance_id)
                success_count += 1
                append_checkpoint(item["performance_id"], scraped_ids)

        # ── Export ───────────────────────────────────────────────────
        json_path = save_json(performances)
        csv_path = save_csv(performances)

        summary = _make_summary(
            start_time,
            discovered_count=len(discovered),
            scraped_count=success_count + len(existing),
            failed_count=fail_count,
            output_paths=[str(json_path), str(csv_path)],
            skipped_checkpoint=skipped,
        )
        save_run_summary(summary)

        logger.info(
            "Pipeline complete: %d discovered, %d scraped, %d failed",
            len(discovered), success_count, fail_count,
        )
        return summary

    finally:
        await fetcher.close()


def _make_summary(
    start_time: datetime,
    discovered_count: int,
    scraped_count: int,
    failed_count: int,
    output_paths: list[str],
    skipped_checkpoint: int = 0,
) -> dict:
    end_time = datetime.utcnow()
    return {
        "started_at": start_time.isoformat(timespec="seconds") + "Z",
        "finished_at": end_time.isoformat(timespec="seconds") + "Z",
        "duration_seconds": round((end_time - start_time).total_seconds(), 1),
        "discovered_count": discovered_count,
        "scraped_count": scraped_count,
        "failed_count": failed_count,
        "skipped_checkpoint": skipped_checkpoint,
        "output_paths": output_paths,
    }
