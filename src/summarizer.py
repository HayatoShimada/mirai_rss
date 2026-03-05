import json
import logging
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

def summarize_articles(main_articles: List[Article], fallback_articles: List[Article]) -> Optional[Dict[str, Any]]:
    """
    Summarizes articles using the Gemini API.
    Selects up to 3 articles, categorizes them, and removes duplicates.
    Provides fallback news if main_articles is empty.
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not set. Skipping summarization.")
        return None

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        has_main = len(main_articles) > 0
        articles_to_process = main_articles if has_main else fallback_articles
        
        if not articles_to_process:
            logger.info("No articles to process (both main and fallback are empty).")
            return {
                "has_main": False,
                "message": "本日は南砺市関連のニュース、および代替ニュースのどちらも取得できませんでした。",
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
        has_main_text = "ありました。南砺市の記事から選出してください。" if has_main else "ありませんでした。代わりに全国や近隣県のニュースを提供します。"
        
        prompt = prompt_template.format(
            has_main_text=has_main_text, 
            articles_text=articles_text
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
                    "description": "厳選された最大3件の記事リスト",
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
            model='gemini-2.5-flash',
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
