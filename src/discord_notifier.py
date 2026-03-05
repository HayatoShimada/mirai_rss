import requests
from src.config import DISCORD_WEBHOOK_URL

def post_to_discord(summary_data, dry_run=False):
    """
    Formats the summary data into a Discord message with Embeds
    and posts it to the configured webhook URL.
    """
    if not summary_data:
        print("No summary data to post.")
        return

    if not DISCORD_WEBHOOK_URL and not dry_run:
        print("Warning: DISCORD_WEBHOOK_URL is not set.")
        return

    message = summary_data.get("message", "本日のニュースまとめ")
    articles = summary_data.get("articles", [])
    
    # Category colors
    color_map = {
        "ニュース": 3447003,      # Blue
        "補助金・法律": 15105570, # Orange/Yellow
        "イベント": 10181046,     # Purple
    }

    embeds = []
    for art in articles:
        cat = art.get('category', 'ニュース')
        color = color_map.get(cat, 3447003) # Default to blue if unknown
        
        embed = {
            "title": art.get('title', 'No Title'),
            "url": art.get('link', ''),
            "description": art.get('summary', ''),
            "color": color,
            "fields": [
                {
                    "name": "カテゴリ",
                    "value": cat,
                    "inline": True
                }
            ]
        }
        embeds.append(embed)

    payload = {
        "content": message,
        "embeds": embeds,
        "username": "ミライ店主会 RSS Bot",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/3062/3062634.png" # Generic RSS icon
    }

    if dry_run:
        import json
        print("\n--- DRY RUN: Discord Payload ---")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print("--------------------------------\n")
        return

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("Successfully posted to Discord.")
    except Exception as e:
        print(f"Failed to post to Discord: {e}")

if __name__ == "__main__":
    test_data = {
        "has_main": True,
        "message": "こんにちは！本日の南砺市関連ニュースです。",
        "articles": [
            {
                "title": "井波で新しいマルシェ開催",
                "category": "イベント",
                "summary": "今週末、井波エリアで地元クリエイターが集まるマルシェが開催されます。新規出店者向けの交流会も同日開催予定です。",
                "link": "https://example.com/event"
            }
        ]
    }
    post_to_discord(test_data, dry_run=True)
