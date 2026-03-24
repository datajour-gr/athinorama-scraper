"""Scraper configuration constants."""

from pathlib import Path

# URLs
SEED_URL = "https://www.athinorama.gr/theatre/"
BASE_URL = "https://www.athinorama.gr"

# Patterns
PERFORMANCE_PATH_RE = r"/theatre/performance/[\w_]+-(\d+)/"

# HTTP
USER_AGENT = (
    "AthinoramaScraper/1.0 "
    "(educational project; respectful crawling; +https://github.com)"
)
REQUEST_TIMEOUT = 30.0
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # seconds base for exponential backoff

# Rate limiting
MIN_DELAY = 0.5  # seconds
MAX_DELAY = 1.5  # seconds
MAX_CONCURRENCY = 8

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHECKPOINT_PATH = DATA_DIR / "checkpoint.json"
PERFORMANCES_JSON = DATA_DIR / "performances.json"
PERFORMANCES_CSV = DATA_DIR / "performances.csv"
RUN_SUMMARY_PATH = DATA_DIR / "run_summary.json"
LOG_PATH = DATA_DIR / "scraper.log"
