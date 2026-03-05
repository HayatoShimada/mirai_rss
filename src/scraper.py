import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any

def scrape_html_sources(sources: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Scrapes HTML from a list of source dicts {"url": "...", "selector": "..."}.
    Returns a list of extracted text articles/items.
    """
    articles = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for src in sources:
        url = src.get("url")
        selector = src.get("selector")
        
        if not url or not selector:
            continue
            
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            elements = soup.select(selector)
            
            for index, el in enumerate(elements):
                # Limiting to first 10 items per site to prevent overflow
                if index >= 10:
                    break
                    
                text = el.get_text(separator="\n", strip=True)
                if text:
                    # Find first link inside the element, or default to page URL
                    link_el = el.find('a')
                    item_link = url
                    if link_el and link_el.has_attr('href'):
                        href = link_el['href']
                        if href.startswith('http'):
                            item_link = href
                        else:
                            # Basic relative URL resolution
                            from urllib.parse import urljoin
                            item_link = urljoin(url, href)

                    articles.append({
                        "title": f"New Update from {soup.title.string if soup.title else 'Website'}",
                        "link": item_link,
                        "published": "", # Unreliable to parse from arbitrary HTML
                        "summary": text,
                        "source": url
                    })
        except Exception as e:
            print(f"Error scraping {url}: {e}")

    return articles

if __name__ == "__main__":
    # Test
    test_src = [{"url": "https://www.city.nanto.toyama.jp/cms-sypher/www/info/index.jsp", "selector": ".info_list li"}]
    arts = scrape_html_sources(test_src)
    for a in arts[:3]: # print first 3
        print(f"- {a['summary'][:50]}... ({a['link']})")
