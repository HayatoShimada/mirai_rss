import logging
import requests
import json
from src.config import DISCORD_WEBHOOK_URL

logger = logging.getLogger(__name__)

# Constants that could be moved to .env / config
BOT_USERNAME = "ミライ店主会 RSS Bot"
BOT_AVATAR_URL = "https://cdn-icons-png.flaticon.com/512/3062/3062634.png"
COLOR_MAP = {
    "ニュース": 3447003,      # Blue
    "補助金・法律": 15105570, # Orange/Yellow
    "イベント": 10181046,     # Purple
}

def post_to_discord(summary_data: dict, dry_run: bool = False):
    """
    Formats the summary data into a Discord message with Embeds
    and posts it to the configured webhook URL.
    """
    if not summary_data:
        logger.info("No summary data to post.")
        return

    if not DISCORD_WEBHOOK_URL and not dry_run:
        logger.warning("DISCORD_WEBHOOK_URL is not set. Cannot post to Discord.")
        return

    message = summary_data.get("message", "本日のニュースまとめ")
    articles = summary_data.get("articles", [])
    
    embeds = []
    for art in articles:
        cat = art.get('category', 'ニュース')
        color = COLOR_MAP.get(cat, 3447003) # Default to blue
        
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

    # Append the dashboard URL to the main message
    message += "\n\n📊 **過去の配信ログ**: https://mirairss-n2uvbf24ntjhvndtfipbjl.streamlit.app/"

    payload = {
        "content": message,
        "embeds": embeds,
        "username": BOT_USERNAME,
        "avatar_url": BOT_AVATAR_URL
    }

    if dry_run:
        logger.info("--- DRY RUN: Discord Payload ---")
        logger.info(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Successfully posted to Discord.")
    except Exception as e:
        logger.error(f"Failed to post to Discord: {e}", exc_info=True)
