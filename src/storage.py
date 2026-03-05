import json
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

POSTED_ARTICLES_FILE = Path("posted_articles.json")

def load_posted_urls() -> List[str]:
    """Loads a list of previously posted URLs from a JSON file."""
    if not POSTED_ARTICLES_FILE.exists():
        return []
    try:
        content = POSTED_ARTICLES_FILE.read_text(encoding="utf-8")
        data = json.loads(content)
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        logger.error(f"Failed to load {POSTED_ARTICLES_FILE}: {e}")
        return []

def save_posted_urls(urls: List[str]) -> None:
    """Saves a list of posted URLs to a JSON file."""
    try:
        # Keep only the latest 300 to prevent the file from growing indefinitely
        urls_to_save = urls[-300:] 
        content = json.dumps(urls_to_save, ensure_ascii=False, indent=2)
        POSTED_ARTICLES_FILE.write_text(content, encoding="utf-8")
        logger.info(f"Saved {len(urls_to_save)} URLs to {POSTED_ARTICLES_FILE}")
    except Exception as e:
        logger.error(f"Failed to save {POSTED_ARTICLES_FILE}: {e}")
