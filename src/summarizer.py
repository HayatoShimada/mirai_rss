import json
import logging
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY
from src.models import Article

logger = logging.getLogger(__name__)

def load_prompt_template(filepath: str = "prompt.txt") -> str:
    try:
        return Path(filepath).read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to load prompt template from {filepath}: {e}")
        # Fallback minimal prompt
        return "以下の記事から最も重要な3件を要約してください。\n記事一覧:\n{articles_text}"

def summarize_articles(main_articles: List[Article], fallback_articles: List[Article], posted_urls: List[str] = None) -> Optional[Dict[str, Any]]:
    """
    Summarizes articles using the Gemini API.
    Selects up to 3 articles, categorizes them, and removes duplicates.
    Provides fallback news if main_articles is empty.
    Skips articles matching URLs in `posted_urls`.
    """
    if posted_urls is None:
        posted_urls = []

    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not set. Skipping summarization.")
        return None

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        has_main = len(main_articles) > 0
        
        # If there are very few main articles, include fallback articles to give Gemini more choices
        # This prevents Gemini from hallucinating or picking extremely old articles just to fulfill the "3 items" request
        all_articles = main_articles.copy()
        if len(main_articles) < 10:
            all_articles.extend(fallback_articles)
            
        # Filter out previously posted articles BEFORE sending to Gemini if possible
        articles_to_process = [art for art in all_articles if art.link not in posted_urls]
        
        if not articles_to_process:
            logger.info("No new, unposted articles to process.")
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
        
        prompt = prompt_template.format(
            has_main_text=has_main_text,
            current_date_text=current_date_text,
            articles_text=articles_text,
            posted_urls_text=posted_urls_text
        )

        logger.info(f"Sending {len(articles_to_process)} articles to Gemini for summarization.")

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
                            "category": {"type": "STRING", "description": "カテゴリ ('ニュース', '補助金・法律', 'イベント')"},
                            "summary": {"type": "STRING", "description": "小規模事業者に向けた簡潔な要約（2〜3行）"},
                            "link": {"type": "STRING", "description": "元の記事のURL"}
                        },
                        "required": ["title", "category", "summary", "link"]
                    }
                }
            },
            "required": ["message", "articles"]
        }

        response = client.models.generate_content(
            model='gemini-3.1-flash-lite-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.3,
            ),
        )

        result = json.loads(response.text)
        result["has_main"] = has_main
        
        logger.info(f"Successfully generated summary with {len(result.get('articles', []))} articles.")
        return result

    except Exception as e:
        logger.error(f"Error during Gemini summarization: {e}", exc_info=True)
        return None
