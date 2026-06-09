"""
parser.py - HTML and JSON parsing helpers.
"""

import json
from typing import Any, List, Optional
from bs4 import BeautifulSoup


def parse_html(html_content: str) -> BeautifulSoup:
    """Parse HTML content and return a BeautifulSoup object."""
    return BeautifulSoup(html_content, "lxml")


def extract_meta_title(soup: BeautifulSoup) -> Optional[str]:
    """Extract the page title from HTML."""
    title_tag = soup.find("title")
    return title_tag.get_text(strip=True) if title_tag else None


def extract_meta_description(soup: BeautifulSoup) -> Optional[str]:
    """Extract meta description from HTML."""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta:
        return meta.get("content", "").strip()
    return None


def count_h1_tags(soup: BeautifulSoup) -> int:
    """Count H1 tags in HTML."""
    return len(soup.find_all("h1"))


def count_images_missing_alt(soup: BeautifulSoup) -> int:
    """Count images without alt text."""
    images = soup.find_all("img")
    return sum(1 for img in images if not img.get("alt", "").strip())


def extract_links(soup: BeautifulSoup) -> List[str]:
    """Extract all links from HTML."""
    links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith(("http", "https")):
            links.append(href)
    return links


def safe_json_loads(text: Optional[str], default: Any = None) -> Any:
    """Safely parse JSON text, returning default on failure."""
    if not text:
        return default if default is not None else []
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


def safe_json_dumps(data: Any) -> str:
    """Safely convert data to JSON string."""
    try:
        return json.dumps(data, ensure_ascii=False)
    except (TypeError, ValueError):
        return "[]"
