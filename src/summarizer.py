import json
import logging
import datetime
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY
from src.models import Article

logger = logging.getLogger(__name__)

_fetch_cache = {}

def fetch_website_text(url: str) -> str:
    """Fetches text content from the given URL. Use this to read the latest updates from a website."""
    if url in _fetch_cache:
        return _fetch_cache[url]
        
    try:
        logger.info(f"Gemini Tool called: fetching {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        from urllib.parse import urljoin
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        # Append absolute URLs to anchor texts so Gemini can follow links
        for a in soup.find_all('a', href=True):
            href = a['href']
            abs_url = urljoin(url, href)
            # Only append if it looks like a valid http link and not an anchor
            if abs_url.startswith('http') and not href.startswith('#'):
                link_text = a.get_text(strip=True)
                if link_text:
                    a.string = f"{link_text} ( URL: {abs_url} )"
                else:
                    a.string = f"( URL: {abs_url} )"
                    
        text = soup.get_text(separator='\n')
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        result_text = text[:4000] # Limit to avoid context bloat
        _fetch_cache[url] = result_text
        return result_text
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.info(f"Gemini Tool exploration hit 404 Not Found: {url}")
        else:
            logger.warning(f"Failed to fetch {url}: {e}")
        error_msg = f"Error fetching {url}: {e}\n\n[SYSTEM]: This URL is invalid or inaccessible. DO NOT try to fetch this exact URL again. Please proceed with other information or stop searching."
        _fetch_cache[url] = error_msg
        return error_msg
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        error_msg = f"Error fetching {url}: {e}\n\n[SYSTEM]: This URL is invalid or inaccessible. DO NOT try to fetch this exact URL again. Please proceed with other information or stop searching."
        _fetch_cache[url] = error_msg
        return error_msg

def load_prompt_template(filepath: str = "prompt.txt") -> str:
    try:
        return Path(filepath).read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to load prompt template from {filepath}: {e}")
        # Fallback minimal prompt
        return "以下の記事から最も重要な5件を要約してください。\n記事一覧:\n{articles_text}"

def summarize_articles(
    main_articles: List[Article], 
    fallback_articles: List[Article], 
    main_html_urls: List[str] = None,
    fallback_html_urls: List[str] = None,
    posted_urls: List[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Summarizes RSS articles and HTML URLs using the Gemini API.
    Selects up to 5 articles, categorizes them, and removes duplicates.
    Provides fallback news if main sources are empty.
    Skips articles matching URLs in `posted_urls`.
    """
    if posted_urls is None:
        posted_urls = []
    if main_html_urls is None:
        main_html_urls = []
    if fallback_html_urls is None:
        fallback_html_urls = []

    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not set. Skipping summarization.")
        return None

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        has_main = len(main_articles) > 0 or len(main_html_urls) > 0
        
        # If there are very few main articles and URLs, include fallback articles to give Gemini more choices
        all_articles = main_articles.copy()
        all_html_urls = main_html_urls.copy()
        
        if len(main_articles) + len(main_html_urls) < 10:
            all_articles.extend(fallback_articles)
            all_html_urls.extend(fallback_html_urls)
            
        # Filter out previously posted articles BEFORE sending to Gemini if possible
        articles_to_process = [art for art in all_articles if art.link not in posted_urls]
        
        if not articles_to_process and not all_html_urls:
            logger.info("No new, unposted articles to process and no HTML URLs to check.")
            return {
                "has_main": False,
                "message": "本日は新しくお伝えできるお知らせや、関連ニュースがありませんでした。",
                "articles": []
            }

        # Prepare payload
        articles_text = ""
        for i, art in enumerate(articles_to_process):
            articles_text += f"[{i+1}] Title: {art.title}\n"
            articles_text += f"Link: {art.link}\n"
            articles_text += f"Source: {art.source}\n"
            if art.summary:
                articles_text += f"Summary: {art.summary[:200]}...\n"
            articles_text += "\n"

        prompt_template = load_prompt_template()
        has_main_text = "ありました。できるだけ南砺市の記事を優先して選出しつつ、枠が余る場合はその他の有益な情報から選出してください。" if has_main else "ありませんでした。代わりに提供された全国や近隣県の有益なニュースから提供してください。"
        
        # Format the current date for the prompt
        current_date_text = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y年%m月%d日 %H時%M分')
        
        # Optionally, format the posted URLs if the prompt needs them
        posted_urls_text = "\n".join([f"- {url}" for url in posted_urls]) if posted_urls else "なし"
        
        # Format HTML URLs
        html_urls_text = "\n".join([f"- {url}" for url in all_html_urls]) if all_html_urls else "なし"
        
        prompt = prompt_template.format(
            has_main_text=has_main_text,
            current_date_text=current_date_text,
            articles_text=articles_text,
            html_urls_text=html_urls_text,
            posted_urls_text=posted_urls_text
        )

        logger.info(f"Sending {len(articles_to_process)} articles to Gemini for summarization.")
        logger.info(f"=== GENERATED PROMPT ===\n{prompt}\n========================")

        schema = {
            "type": "OBJECT",
            "properties": {
                "message": {
                    "type": "STRING",
                    "description": "全体への挨拶や、南砺市ニュースの有無に関する一言メッセージ。"
                },
                "articles": {
                    "type": "ARRAY",
                    "description": "厳選された最大5件の記事リスト",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "title": {"type": "STRING", "description": "記事のタイトル"},
                            "category": {"type": "STRING", "description": "カテゴリ ('ニュース', '補助金・支援', '空き家・DIY', '集客・コミュニティ')"},
                            "summary": {"type": "STRING", "description": "小規模事業者に向けた簡潔な要約（2〜3行）"},
                            "link": {"type": "STRING", "description": "元の記事のURL"}
                        },
                        "required": ["title", "category", "summary", "link"]
                    }
                }
            },
            "required": ["message", "articles"]
        }

        chat = client.chats.create(
            model='gemini-3.1-pro-preview',
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.3,
                tools=[fetch_website_text],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=False,
                    maximum_remote_calls=20
                )
            )
        )

        response = chat.send_message(prompt)

        if not response.text:
            logger.error("Gemini failed to generate text response. It may have hit the remote call limit or failed.")
            return None

        result = json.loads(response.text)
        
        # Filter out articles that incorrectly use a top-level URL instead of a detailed article URL
        valid_articles = []
        for art in result.get("articles", []):
            if art.get("link") in all_html_urls:
                logger.warning(f"Skipped article '{art.get('title')}' because its link is a top-level URL: {art.get('link')}")
                continue
            valid_articles.append(art)
        
        result["articles"] = valid_articles
        result["has_main"] = has_main
        
        logger.info(f"Successfully generated summary with {len(valid_articles)} valid articles.")
        return result

    except Exception as e:
        logger.error(f"Error during Gemini summarization: {e}", exc_info=True)
        return None
