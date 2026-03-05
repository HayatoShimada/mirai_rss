import json
from google import genai
from google.genai import types
from src.config import GEMINI_API_KEY

def summarize_articles(main_articles, fallback_articles):
    """
    Summarizes articles using the Gemini API.
    Selects up to 3 articles, categorizes them, and removes duplicates.
    Provides fallback news if main_articles is empty.
    """
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY is not set.")
        return None

    try:
        # Initialize Gemini Free Tier compatible model
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        has_main = len(main_articles) > 0
        articles_to_process = main_articles if has_main else fallback_articles
        
        if not articles_to_process:
            return {
                "has_main": False,
                "message": "本日は南砺市関連のニュース、および代替ニュースのどちらも取得できませんでした。",
                "articles": []
            }

        # Prepare payload
        articles_text = ""
        for i, art in enumerate(articles_to_process):
            articles_text += f"[{i+1}] Title: {art['title']}\n"
            articles_text += f"Link: {art['link']}\n"
            articles_text += f"Source: {art['source']}\n"
            if art['summary']:
                articles_text += f"Summary: {art['summary'][:200]}...\n" # Truncate long summaries
            articles_text += "\n"

        prompt = f"""
あなたは富山県南砺市で新しく小規模事業を始める人々（ミライ店主会）に向けた、有益な情報を提供するアシスタントです。
以下の記事リストから、重複する内容を排除し、彼らにとって最も有益・重要な記事を**最大3件**選出してください。

【ルール】
1. 以下のカテゴリのいずれかに分類してください：
   - ニュース (一般、地域問わず)
   - 補助金・法律 (ビジネスに直結する制度や法律変更など)
   - イベント (セミナー、地域の催し物など)
2. 同じトピックの記事は1つにまとめてください。
3. 要約は箇条書きや短い段落を用いて、パッと見て分かりやすいように2〜3行程度でまとめてください。
4. 必ず指定されたJSONスキーマに従って出力してください。Markdownのコードブロック(```json ... ```)は付けないでください。

【状態】
今回は南砺市関連のニュースが{"ありました。南砺市の記事から選出してください。" if has_main else "ありませんでした。代わりに全国や近隣県のニュースを提供します。"}

【記事一覧】
{articles_text}
"""

        # Define expected output schema
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
        return result

    except Exception as e:
        print(f"Error during Gemini summarization: {e}")
        return None

if __name__ == "__main__":
    # Test stub
    test_main = [{"title": "南砺市で新しい補助金が開始", "link": "http://example.com/1", "source": "Webun", "summary": "最大100万円の補助金"}]
    print(summarize_articles(test_main, []))
