import json
import logging
from pathlib import Path
from typing import List

import csv
import datetime

logger = logging.getLogger(__name__)

POSTED_ARTICLES_FILE = Path("posted_articles.json")
ARTICLES_CSV_FILE = Path("articles_history.csv")

def save_articles_to_csv(articles_list: List[dict]) -> None:
    """Saves a list of article dictionaries to a CSV file for dashboard analytics."""
    if not articles_list:
        return
        
    file_exists = ARTICLES_CSV_FILE.exists()
    
    try:
        with open(ARTICLES_CSV_FILE, mode='a', encoding='utf-8', newline='') as f:
            fieldnames = ['timestamp', 'title', 'category', 'summary', 'link']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
                
            timestamp = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M:%S')
            
            for article in articles_list:
                row = {
                    'timestamp': timestamp,
                    'title': article.get('title', ''),
                    'category': article.get('category', ''),
                    'summary': article.get('summary', ''),
                    'link': article.get('link', '')
                }
                writer.writerow(row)
        logger.info(f"Appended {len(articles_list)} articles to {ARTICLES_CSV_FILE}")
    except Exception as e:
        logger.error(f"Failed to save articles to {ARTICLES_CSV_FILE}: {e}")

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
