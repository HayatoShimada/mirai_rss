import argparse
import sys
from src.config import load_sources_list
from src.rss_fetcher import fetch_rss_feeds
from src.scraper import scrape_html_sources
from src.summarizer import summarize_articles
from src.discord_notifier import post_to_discord

def process_sources(sources_list, hours_limit):
    """
    Separates sources into RSS and HTML, fetches data from both, 
    and returns a combined list of articles/items.
    """
    rss_urls = [s["url"] for s in sources_list if s["type"] == "RSS"]
    html_sources = [s for s in sources_list if s["type"] == "HTML"]
    
    articles = []
    if rss_urls:
        articles.extend(fetch_rss_feeds(rss_urls, hours_limit=hours_limit))
    if html_sources:
        articles.extend(scrape_html_sources(html_sources))
        
    return articles

def main():
    parser = argparse.ArgumentParser(description="Mirai RSS Bot")
    parser.add_argument("--dry-run", action="store_true", help="Run without posting to Discord")
    parser.add_argument("--hours", type=int, default=24, help="Fetch articles from the last N hours")
    args = parser.parse_args()

    print(f"Starting Mirai RSS Bot (Dry run: {args.dry_run}, Hours: {args.hours})")

    # 1. Load Sources
    sources_dict = load_sources_list("sources.md")
    main_sources = sources_dict.get("main", [])
    fallback_sources = sources_dict.get("fallback", [])

    if not main_sources and not fallback_sources:
        print("No sources found. Please configure sources.md.")
        sys.exit(1)

    # 2. Fetch Data (RSS + Scraped HTML)
    print("Fetching main articles...")
    main_articles = process_sources(main_sources, args.hours)
    print(f"Found {len(main_articles)} main articles.")

    print("Fetching fallback articles...")
    fallback_articles = process_sources(fallback_sources, args.hours)
    print(f"Found {len(fallback_articles)} fallback articles.")

    # 3. Summarize with Gemini
    print("Summarizing articles with Gemini...")
    summary_data = summarize_articles(main_articles, fallback_articles)
    
    if not summary_data:
        print("Failed to generate summary.")
        sys.exit(1)

    # 4. Post to Discord
    print("Posting to Discord...")
    post_to_discord(summary_data, dry_run=args.dry_run)

    print("Done!")

if __name__ == "__main__":
    main()
