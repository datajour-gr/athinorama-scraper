"""CLI entry point for the Athinorama scraper."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys

from . import config
from .pipeline import run_pipeline


def setup_logging() -> None:
    """Configure logging to file and stderr."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(config.LOG_PATH, encoding="utf-8"),
    ]

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape Athinorama theatre performances",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clear checkpoint and start a fresh run",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max number of detail pages to scrape (0 = all)",
    )
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    if args.clean:
        if config.CHECKPOINT_PATH.exists():
            config.CHECKPOINT_PATH.unlink()
            logger.info("Cleared checkpoint file")

    logger.info("Starting Athinorama scraper")
    summary = asyncio.run(run_pipeline(limit=args.limit))

    print("\n=== Run Summary ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
