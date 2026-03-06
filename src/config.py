import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List
from src.models import Source

# Load environment variables from .env if present
load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    # Suppress harmless "non-text parts" warning during automatic function calling
    logging.getLogger("google_genai.types").setLevel(logging.ERROR)

def load_sources_list(filepath="sources.md") -> Dict[str, List[Source]]:
    """
    Parses the sources.md file to extract URLs, types, and selectors by category.
    Returns a dictionary of categories and their corresponding lists of Source objects.
    """
    sources_dict = {
        "main": [],
        "fallback": []
    }
    
    path = Path(filepath)
    if not path.exists():
        logger.warning(f"{filepath} not found.")
        return sources_dict

    current_category = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("## メイン用"):
                current_category = "main"
                continue
            elif line.startswith("## 代替用"):
                current_category = "fallback"
                continue
                
            # Parse Markdown Table row
            if line.startswith("|") and current_category:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    url = parts[1]
                    src_type = parts[2].upper()
                    selector = None
                    
                    if url == "URL" or "---" in url:
                        # Skip header and separator rows
                        continue
                        
                    # Extract just the URL if there's text after it (e.g. "https://example.com (note)")
                    clean_url = url.split(" ")[0] if url.lower().startswith("http") else url
                        
                    if clean_url.startswith("http"):
                        sources_dict[current_category].append(
                            Source(url=clean_url, type=src_type, selector=selector)
                        )
                    
    logger.info(f"Loaded {len(sources_dict['main'])} main sources and {len(sources_dict['fallback'])} fallback sources")
    return sources_dict

if __name__ == "__main__":
    setup_logging()
    srcs = load_sources_list()
    logger.info(f"Main Sources: {srcs.get('main')}")
    logger.info(f"Fallback Sources: {srcs.get('fallback')}")
