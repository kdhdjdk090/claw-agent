"""Web tools — fetch pages and search the internet."""

from __future__ import annotations

import re
from html.parser import HTMLParser

import httpx


class _TextExtractor(HTMLParser):
    """Simple HTML to text converter."""

    def __init__(self):
        super().__init__()
        self._pieces: list[str] = []
        self._skip = False
        self._skip_tags = {"script", "style", "noscript", "svg", "head"}

    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags:
            self._skip = True
        if tag in ("p", "br", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr"):
            self._pieces.append("\n")

    def handle_endtag(self, tag):
        if tag in self._skip_tags:
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self._pieces.append(data)

    def get_text(self) -> str:
        text = "".join(self._pieces)
        # Collapse whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def web_fetch(url: str, max_chars: int = 20000) -> str:
    """Fetch a web page and extract its text content."""
    if not url.startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"

    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(url, headers={
                "User-Agent": "ClawAgent/0.1 (autonomous coding agent)",
            })
            resp.raise_for_status()

        content_type = resp.headers.get("content-type", "")

        if "text/html" in content_type:
            parser = _TextExtractor()
            parser.feed(resp.text)
            text = parser.get_text()
        elif "text/plain" in content_type or "application/json" in content_type:
            text = resp.text
        else:
            text = resp.text

        if len(text) > max_chars:
            text = text[:max_chars] + f"\n... [truncated at {max_chars} chars]"

        return text
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.reason_phrase}"
    except httpx.ConnectError:
        return f"Error: Could not connect to {url}"
    except Exception as e:
        return f"Error fetching URL: {e}"


def web_search(query: str, num_results: int = 5) -> str:
    """Search the web using DuckDuckGo HTML (no API key required)."""
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            resp = client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={
                    "User-Agent": "ClawAgent/0.1 (autonomous coding agent)",
                },
            )
            resp.raise_for_status()

        # Parse results from DuckDuckGo HTML
        results = []

        # Extract result links and snippets
        link_pattern = re.compile(r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>(.+?)</a>', re.DOTALL)
        snippet_pattern = re.compile(r'<a class="result__snippet"[^>]*>(.+?)</a>', re.DOTALL)

        links = link_pattern.findall(resp.text)
        snippets = snippet_pattern.findall(resp.text)

        for i, (href, title) in enumerate(links[:num_results]):
            title_clean = re.sub(r"<[^>]+>", "", title).strip()
            snippet = ""
            if i < len(snippets):
                snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip()

            # Extract actual URL from DuckDuckGo redirect
            url_match = re.search(r'uddg=([^&]+)', href)
            actual_url = url_match.group(1) if url_match else href
            # URL decode
            from urllib.parse import unquote
            actual_url = unquote(actual_url)

            results.append(f"{i+1}. {title_clean}\n   {actual_url}\n   {snippet}")

        if not results:
            return f"No results found for: {query}"

        return f"Search results for: {query}\n\n" + "\n\n".join(results)

    except Exception as e:
        return f"Error searching: {e}"
