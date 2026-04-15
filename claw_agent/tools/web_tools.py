"""Web tools — fetch pages and search the internet."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import unquote, urlparse

import httpx


_TRUSTED_SOURCE_WEIGHTS = {
    "reuters.com": 120,
    "apnews.com": 115,
    "bloomberg.com": 105,
    "ft.com": 100,
    "wsj.com": 100,
    "bbc.com": 95,
    "bbc.co.uk": 95,
    "nytimes.com": 92,
    "theguardian.com": 88,
    "npr.org": 85,
    "gov": 125,
    "mil": 125,
    "state.gov": 130,
    "defense.gov": 130,
    "whitehouse.gov": 130,
    "treasury.gov": 130,
    "congress.gov": 128,
    "un.org": 118,
}

_SEARCH_ENDPOINTS = (
    "https://html.duckduckgo.com/html/",
    "https://lite.duckduckgo.com/lite/",
)


def _display_host(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return "unknown"
    if host.startswith("www."):
        host = host[4:]
    return host or "unknown"


def _trust_score(url: str, index: int) -> int:
    host = _display_host(url)
    score = max(0, 50 - index)
    for domain, weight in _TRUSTED_SOURCE_WEIGHTS.items():
        if host == domain or host.endswith(f".{domain}"):
            return score + weight
        if domain == "gov" and host.endswith(".gov"):
            return score + weight
        if domain == "mil" and host.endswith(".mil"):
            return score + weight
    return score


def _clean_search_url(href: str) -> str:
    url_match = re.search(r"uddg=([^&]+)", href)
    actual_url = url_match.group(1) if url_match else href
    return unquote(actual_url)


def _clean_html_text(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value).strip()


def _parse_search_results(html: str, num_results: int) -> list[dict[str, str | int]]:
    """Extract search results from DuckDuckGo HTML and Lite pages."""
    link_patterns = (
        re.compile(r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>(.+?)</a>', re.DOTALL),
        re.compile(r"<a[^>]+class=['\"]result-link['\"][^>]+href=['\"]([^'\"]+)['\"][^>]*>(.+?)</a>", re.DOTALL),
    )
    snippet_patterns = (
        re.compile(r'<a class="result__snippet"[^>]*>(.+?)</a>', re.DOTALL),
        re.compile(r"<td[^>]+class=['\"]result-snippet['\"][^>]*>(.+?)</td>", re.DOTALL),
    )

    links: list[tuple[str, str]] = []
    snippets: list[str] = []

    for pattern in link_patterns:
        links = pattern.findall(html)
        if links:
            break

    for pattern in snippet_patterns:
        snippets = pattern.findall(html)
        if snippets:
            break

    results = []
    for i, (href, title) in enumerate(links[:num_results]):
        title_clean = _clean_html_text(title)
        snippet = _clean_html_text(snippets[i]) if i < len(snippets) else ""
        actual_url = _clean_search_url(href)
        results.append({
            "title": title_clean,
            "url": actual_url,
            "snippet": snippet,
            "host": _display_host(actual_url),
            "score": _trust_score(actual_url, i),
        })

    return results


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
    errors: list[str] = []
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            results = []
            for endpoint in _SEARCH_ENDPOINTS:
                try:
                    resp = client.get(
                        endpoint,
                        params={"q": query},
                        headers={
                            "User-Agent": "ClawAgent/0.1 (autonomous coding agent)",
                            "Accept-Language": "en-US,en;q=0.9",
                        },
                    )
                    resp.raise_for_status()
                    results = _parse_search_results(resp.text, num_results)
                    if results:
                        break
                    errors.append(f"{endpoint}: parsed 0 results")
                except Exception as endpoint_error:
                    errors.append(f"{endpoint}: {endpoint_error}")

        if not results:
            details = "; ".join(errors[:3])
            return f"No results found for: {query}" + (f"\nSearch backends tried: {details}" if details else "")

        deduped = []
        seen_urls = set()
        for result in sorted(results, key=lambda item: item["score"], reverse=True):
            if result["url"] in seen_urls:
                continue
            seen_urls.add(result["url"])
            deduped.append(result)
            if len(deduped) >= num_results:
                break

        rendered = []
        for index, result in enumerate(deduped, 1):
            rendered.append(
                f"{index}. {result['title']}\n"
                f"   Source: {result['host']}\n"
                f"   URL: {result['url']}\n"
                f"   Snippet: {result['snippet']}"
            )

        return (
            f"Search results for: {query}\n"
            "Use web_fetch on the most relevant and trustworthy sources before treating claims as verified.\n\n"
            + "\n\n".join(rendered)
        )

    except Exception as e:
        return f"Error searching: {e}"
