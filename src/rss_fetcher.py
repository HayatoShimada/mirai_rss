import logging
import feedparser
import datetime
import requests
from dateutil import parser as date_parser
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential

from src.models import Source, Article

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
def fetch_url(url: str, timeout: int = 30) -> bytes:
    """Fetches url content with a timeout and retry logic."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.content

def fetch_rss_feeds(sources: List[Source], hours_limit: int = 24) -> List[Article]:
    """
    Fetches RSS feeds from a list of Source objects and returns Article objects 
    published within the hours_limit.
    """
    articles = []
    
    # We use aware datetimes for accurate comparison
    now_aware = datetime.datetime.now(datetime.timezone.utc)
    cutoff_time = now_aware - datetime.timedelta(hours=hours_limit)

    for src in sources:
        if src.type != "RSS":
            continue
            
        logger.info(f"Fetching RSS feed: {src.url}")
        try:
            content = fetch_url(src.url)
            feed = feedparser.parse(content)
            source_title = feed.feed.get('title', src.url)
            
            for entry in feed.entries:
                pub_string = entry.get('published') or entry.get('updated')
                
                # Check timeframe if a date exists
                if pub_string:
                    try:
                        pub_dt = date_parser.parse(pub_string)
                        # Ensure timezone awareness
                        if pub_dt.tzinfo is None:
                            pub_dt = pub_dt.replace(tzinfo=datetime.timezone.utc)
                            
                        if pub_dt < cutoff_time:
                            continue # Skip old articles
                            
                    except ValueError:
                        logger.warning(f"Could not parse date '{pub_string}' from {src.url}. Including article anyway.")
                        pass # Include if we can't parse

                articles.append(Article(
                    title=entry.get('title', 'No Title'),
                    link=entry.get('link', ''),
                    published=pub_string or '',
                    summary=entry.get('summary', '') or entry.get('description', ''),
                    source=source_title
                ))
                
        except Exception as e:
            logger.error(f"Error fetching RSS {src.url}: {e}")

    return articles
