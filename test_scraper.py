import sys
import logging
from src.config import load_sources_list, setup_logging
from src.rss_fetcher import fetch_rss_feeds
from src.scraper import scrape_html_sources

logger = logging.getLogger(__name__)

def main():
    setup_logging()
    
    # 1. Load Sources
    sources_dict = load_sources_list("sources.md")
    main_sources = sources_dict.get("main", [])
    fallback_sources = sources_dict.get("fallback", [])

    print("--- MAIN ARTICLES ---")
    rss_main = [s for s in main_sources if s.type == "RSS"]
    html_main = [s for s in main_sources if s.type == "HTML"]
    for src in rss_main:
        for p in fetch_rss_feeds([src], hours_limit=168):
            print(f"- {p.title}")
    for src in html_main:
        for p in scrape_html_sources([src]):
            print(f"- {p.title}")

    print("\n--- FALLBACK ARTICLES ---")
    rss_fallback = [s for s in fallback_sources if s.type == "RSS"]
    html_fallback = [s for s in fallback_sources if s.type == "HTML"]
    for src in rss_fallback:
        for p in fetch_rss_feeds([src], hours_limit=168):
            print(f"- {p.title}")
    for src in html_fallback:
        for p in scrape_html_sources([src]):
            print(f"- {p.title}")

if __name__ == "__main__":
    main()
