import feedparser
import datetime
from typing import List, Dict, Any

def fetch_rss_feeds(urls: List[str], hours_limit: int = 24) -> List[Dict[str, Any]]:
    """
    Fetches rss feeds from a list of URLs and returns articles published within the hours_limit.
    """
    articles = []
    
    # Calculate the cutoff time (naive UTC for simplicity if feed returns UTC, 
    # butfeedparser parsed_datetime is a time struct. We'll convert to timestamp)
    now_ts = datetime.datetime.now().timestamp()
    cutoff_ts = now_ts - (hours_limit * 3600)

    for url in urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # Try to get the published time
                pub_tuple = entry.get('published_parsed') or entry.get('updated_parsed')
                if pub_tuple:
                    import time
                    article_ts = time.mktime(pub_tuple)
                    if article_ts >= cutoff_ts:
                        articles.append({
                            "title": entry.get('title', ''),
                            "link": entry.get('link', ''),
                            "published": entry.get('published', ''),
                            "summary": entry.get('summary', '') or entry.get('description', ''),
                            "source": feed.feed.get('title', url)
                        })
                else:
                    # If no date is found, we might want to include it anyway, or skip. 
                    # Let's skip for stricter time filtering.
                    pass
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    return articles

if __name__ == "__main__":
    test_urls = ["https://news.yahoo.co.jp/rss/topics/top-picks.xml"]
    print(f"Fetching {test_urls} for articles in the last 24h...")
    arts = fetch_rss_feeds(test_urls)
    for a in arts:
        print(f"- {a['title']} ({a['published']})")
