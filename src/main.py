import argparse
import sys
import logging
from src.config import load_sources_list, setup_logging
from src.rss_fetcher import fetch_rss_feeds
from src.summarizer import summarize_articles
from src.discord_notifier import post_to_discord
from src.storage import load_posted_urls, save_posted_urls, save_articles_to_csv

logger = logging.getLogger(__name__)

def process_sources(sources_list, hours_limit):
    """
    Separates sources into RSS and HTML.
    Fetches RSS feeds normally, but leaves HTML sources as raw URLs for Gemini to browse.
    """
    rss_sources = [s for s in sources_list if s.type == "RSS"]
    html_sources = [s for s in sources_list if s.type == "HTML"]
    
    articles = []
    if rss_sources:
        articles.extend(fetch_rss_feeds(rss_sources, hours_limit=hours_limit))
        
    return articles, html_sources

def main():
    parser = argparse.ArgumentParser(description="Mirai RSS Bot")
    parser.add_argument("--dry-run", action="store_true", help="Run without posting to Discord")
    parser.add_argument("--hours", type=int, default=48, help="Fetch articles from the last N hours (default 48 hours)")
    args = parser.parse_args()

    setup_logging()
    logger.info(f"Starting Mirai RSS Bot (Dry run: {args.dry_run}, Hours: {args.hours})")

    # 1. Load Sources
    sources_dict = load_sources_list("sources.md")
    main_sources = sources_dict.get("main", [])
    fallback_sources = sources_dict.get("fallback", [])

    if not main_sources and not fallback_sources:
        logger.error("No sources found. Please configure sources.md.")
        sys.exit(1)

    # 2. Fetch Data (RSS)
    logger.info("Fetching main articles...")
    main_articles, main_html_sources = process_sources(main_sources, args.hours)
    logger.info(f"Found {len(main_articles)} main RSS articles.")

    logger.info("Fetching fallback articles...")
    fallback_articles, fallback_html_sources = process_sources(fallback_sources, args.hours)
    logger.info(f"Found {len(fallback_articles)} fallback RSS articles.")

    # 3. Load Posted URLs History
    posted_urls = load_posted_urls()
    logger.info(f"Loaded {len(posted_urls)} previously posted URLs from history.")

    # 4. Summarize with Gemini
    logger.info("Summarizing articles and searching HTML URLs with Gemini...")
    summary_data = summarize_articles(
        main_articles=main_articles, 
        fallback_articles=fallback_articles, 
        main_html_urls=[s.url for s in main_html_sources],
        fallback_html_urls=[s.url for s in fallback_html_sources],
        posted_urls=posted_urls[-50:]  # Token optimization: Only pass the 50 most recent URLs to Gemini
    )
    
    if not summary_data:
        logger.error("Failed to generate summary.")
        sys.exit(1)

    # 5. Save Posted URLs History
    if "articles" in summary_data and summary_data["articles"]:
        newly_posted = [art.get("link") for art in summary_data["articles"] if art.get("link")]
        if newly_posted:
            logger.info(f"Adding {len(newly_posted)} URLs to posted history.")
            # Important: Keep the order and append to the end. storage module only keeps the latest 300
            posted_urls.extend(newly_posted)
            save_posted_urls(posted_urls)
            # Save articles to CSV for dashboard analytics
            save_articles_to_csv(summary_data["articles"])

    # 6. Post to Discord
    logger.info("Posting to Discord...")
    post_to_discord(summary_data, dry_run=args.dry_run)

    logger.info("Mirai RSS Bot execution finished successfully.")

if __name__ == "__main__":
    main()
