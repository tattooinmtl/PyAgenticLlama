"""
Fast web search skill — DuckDuckGo + light scraping.
No API key, no heavy ML model. Results in ~2 seconds.

Usage as a skill:
  execute(query="latest Python news", max_results=5, scrape=True)
"""

def execute(**kwargs):
    query       = str(kwargs.get("query", "")).strip()
    max_results = int(kwargs.get("max_results", 5))
    scrape      = bool(kwargs.get("scrape", True))   # fetch page content for top 3

    if not query:
        return "Error: query is required."

    _ensure_deps()

    from duckduckgo_search import DDGS
    import requests
    from bs4 import BeautifulSoup

    # ── 1. DuckDuckGo search ────────────────────────────────────────
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(r)
    except Exception as e:
        return f"Search error: {e}"

    if not results:
        return "No results found."

    # ── 2. Build output ─────────────────────────────────────────────
    lines = [f"Web search results for: {query}\n"]

    for i, r in enumerate(results, 1):
        title   = r.get("title", "No title")
        url     = r.get("href", "")
        snippet = r.get("body", "")
        lines.append(f"[{i}] {title}")
        lines.append(f"    URL: {url}")
        if snippet:
            lines.append(f"    {snippet[:300]}")

        # Fetch full page content for top 3 results
        if scrape and i <= 3 and url:
            content = _scrape(url)
            if content:
                lines.append(f"    --- Page content ---")
                lines.append(f"    {content[:1500]}")

        lines.append("")

    return "\n".join(lines)


def _scrape(url: str) -> str:
    try:
        import requests
        from bs4 import BeautifulSoup
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=8)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript"]):
            tag.decompose()
        text = " ".join(soup.get_text(" ", strip=True).split())
        return text[:2000]
    except Exception:
        return ""


def _ensure_deps():
    import subprocess, sys
    needed = {"requests": "requests", "bs4": "beautifulsoup4", "duckduckgo_search": "duckduckgo-search"}
    for mod, pkg in needed.items():
        try:
            __import__(mod)
        except ImportError:
            print(f"Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg], stdout=subprocess.DEVNULL)
