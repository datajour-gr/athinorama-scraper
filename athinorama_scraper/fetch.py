"""HTTP fetching with rate limiting, retries, and jittered delays."""

from __future__ import annotations

import asyncio
import logging
import random

import httpx

from . import config

logger = logging.getLogger(__name__)


class Fetcher:
    """Async HTTP client with conservative rate limiting."""

    def __init__(
        self,
        min_delay: float = config.MIN_DELAY,
        max_delay: float = config.MAX_DELAY,
        max_retries: int = config.MAX_RETRIES,
        timeout: float = config.REQUEST_TIMEOUT,
    ):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": config.USER_AGENT},
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    async def _throttle(self) -> None:
        """Wait a jittered delay before each request."""
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)

    async def fetch(self, url: str) -> str | None:
        """Fetch a URL with retries and rate limiting. Returns HTML or None."""
        async with self._semaphore:
            for attempt in range(1, self.max_retries + 1):
                await self._throttle()
                try:
                    client = await self._get_client()
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        return resp.text
                    if resp.status_code in (429, 500, 502, 503, 504):
                        wait = config.RETRY_BACKOFF * attempt + random.random()
                        logger.warning(
                            "HTTP %d for %s, retry %d/%d in %.1fs",
                            resp.status_code, url, attempt, self.max_retries, wait,
                        )
                        await asyncio.sleep(wait)
                        continue
                    logger.error("HTTP %d for %s, not retrying", resp.status_code, url)
                    return None
                except (httpx.TimeoutException, httpx.ConnectError) as exc:
                    wait = config.RETRY_BACKOFF * attempt + random.random()
                    logger.warning(
                        "%s for %s, retry %d/%d in %.1fs",
                        type(exc).__name__, url, attempt, self.max_retries, wait,
                    )
                    await asyncio.sleep(wait)
            logger.error("All %d retries exhausted for %s", self.max_retries, url)
            return None

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
