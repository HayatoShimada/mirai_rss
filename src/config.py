import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def load_sources_list(filepath="sources.md"):
    """
    Parses the sources.md file to extract URLs, types, and selectors by category.
    Returns a dictionary of categories and their corresponding lists of dicts.
    """
    sources_dict = {
        "main": [],
        "fallback": []
    }
    
    path = Path(filepath)
    if not path.exists():
        print(f"Warning: {filepath} not found.")
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
                if len(parts) >= 4:
                    url = parts[1]
                    src_type = parts[2].upper()
                    selector = parts[3]
                    
                    if url == "URL" or "---" in url:
                        # Skip header and separator rows
                        continue
                        
                    if url.startswith("http"):
                        sources_dict[current_category].append({
                            "url": url,
                            "type": src_type,
                            "selector": selector
                        })
                    
    return sources_dict

if __name__ == "__main__":
    srcs = load_sources_list()
    print("Main Sources:", srcs.get("main"))
    print("Fallback Sources:", srcs.get("fallback"))
