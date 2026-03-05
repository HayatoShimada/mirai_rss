import logging
import requests
from bs4 import BeautifulSoup
from typing import List
from urllib.parse import urljoin
from tenacity import retry, stop_after_attempt, wait_exponential

from src.models import Source, Article

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _fetch_html_with_retry(url: str, headers: dict) -> bytes:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.content

def scrape_html_sources(sources: List[Source]) -> List[Article]:
    """
    Scrapes HTML from a list of Source objects.
    Returns a list of extracted Article objects.
    """
    articles = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for src in sources:
        if src.type != "HTML" or not src.selector:
            continue
            
        try:
            logger.info(f"Scraping HTML from {src.url} using selector '{src.selector}'")
            content = _fetch_html_with_retry(src.url, headers)
            
            soup = BeautifulSoup(content, 'html.parser')
            # Handle multiple selectors by joining them with comma (CSS standard)
            elements = soup.select(src.selector)
            
            logger.debug(f"Found {len(elements)} elements matching '{src.selector}' on {src.url}")
            
            for index, el in enumerate(elements):
                # Limiting to first 10 items per site to prevent overflow
                if index >= 10:
                    break
                    
                text = el.get_text(separator="\n", strip=True)
                if text:
                    link_el = el.find('a')
                    item_link = src.url
                    if link_el and link_el.has_attr('href'):
                        href = link_el['href']
                        if href.startswith('http'):
                            item_link = href
                        else:
                            item_link = urljoin(src.url, href)

                    articles.append(Article(
                        title=f"New Update from {soup.title.string if soup.title else 'Website'}",
                        link=item_link,
                        summary=text,
                        source=src.url
                    ))
        except Exception as e:
            logger.error(f"Error scraping {src.url}: {e}", exc_info=True)

    return articles
