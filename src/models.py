from dataclasses import dataclass
from typing import Optional

@dataclass
class Source:
    url: str
    type: str # "RSS" or "HTML"
    selector: Optional[str] = None

@dataclass
class Article:
    title: str
    link: str
    summary: str
    source: str
    published: str = ""
    category: str = "ニュース" # Used after summarization
