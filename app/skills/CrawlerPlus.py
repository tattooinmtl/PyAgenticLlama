"""
CrawlerPlus — deep semantic web search skill.
Searches DDG, scrapes up to 10 pages, chunks text, builds a FAISS vector
index with sentence-transformers, then returns the most relevant passages.

First call takes 15–30 seconds (model download + scraping).
Subsequent calls with same query are instant (index is cached in memory).

Usage: execute(query="fusion energy breakthroughs", top_k=5)
"""

def execute(**kwargs):
    query   = str(kwargs.get("query", "")).strip()
    top_k   = int(kwargs.get("top_k", 5))
    max_pages  = int(kwargs.get("max_pages", 8))
    chunk_size = int(kwargs.get("chunk_size", 400))

    if not query:
        return "Error: query is required."

    _ensure_deps()

    searcher = _get_searcher()
    index = searcher.build(query, max_pages=max_pages, chunk_size=chunk_size)
    results = index.search(query, top_k=top_k)

    if not results:
        return f"No relevant results found for: {query}"

    lines = [f"Deep semantic search results for: {query}\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] Relevance: {r['score']:.3f}")
        lines.append(f"    Source: {r['url']}")
        lines.append(f"    {r['text'][:600]}")
        lines.append("")

    return "\n".join(lines)


# ── Internals ──────────────────────────────────────────────────────

import re

_searcher_instance = None   # Lazy-loaded singleton

def _get_searcher():
    global _searcher_instance
    if _searcher_instance is None:
        print("[CrawlerPlus] Loading embedding model (first call only)...")
        _searcher_instance = _WebVectorSearch()
    return _searcher_instance


class _WebVectorSearch:

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self._cache: dict = {}   # query → built index

    def build(self, query: str, max_pages: int = 8, chunk_size: int = 400):
        cache_key = f"{query}|{max_pages}|{chunk_size}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        from duckduckgo_search import DDGS
        import faiss

        print(f"[CrawlerPlus] Searching: {query}")
        urls = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_pages):
                if "href" in r:
                    urls.append(r["href"])

        docs, url_map = [], []
        for url in urls:
            text = _scrape_page(url)
            if not text:
                continue
            for chunk in _chunk(text, chunk_size):
                docs.append(chunk)
                url_map.append(url)
            if len(docs) >= 400:
                break

        if not docs:
            return _EmptyIndex()

        print(f"[CrawlerPlus] Embedding {len(docs)} chunks...")
        vecs = self.embedder.encode(docs, show_progress_bar=False, convert_to_numpy=True)
        faiss.normalize_L2(vecs)
        idx = faiss.IndexFlatIP(vecs.shape[1])
        idx.add(vecs)

        result = _Index(docs, url_map, idx, self.embedder)
        self._cache[cache_key] = result
        return result


class _Index:
    def __init__(self, docs, url_map, idx, embedder):
        self.docs = docs
        self.url_map = url_map
        self.idx = idx
        self.embedder = embedder

    def search(self, query: str, top_k: int = 5):
        import faiss
        q = self.embedder.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(q)
        scores, ids = self.idx.search(q, min(top_k, len(self.docs)))
        return [
            {"score": float(s), "text": self.docs[i], "url": self.url_map[i]}
            for s, i in zip(scores[0], ids[0])
            if i < len(self.docs)
        ]


class _EmptyIndex:
    def search(self, *_): return []


def _scrape_page(url: str) -> str:
    try:
        import requests
        from bs4 import BeautifulSoup
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script","style","nav","header","footer","aside","noscript"]):
            tag.decompose()
        text = " ".join(soup.get_text(" ", strip=True).split())
        # Strip emails and punctuation noise
        text = re.sub(r'\S+@\S+', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip().lower()
    except Exception:
        return ""


def _chunk(text: str, size: int) -> list[str]:
    words = text.split()
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size)]


def _ensure_deps():
    import subprocess, sys
    needed = {
        "requests":              "requests",
        "bs4":                   "beautifulsoup4",
        "duckduckgo_search":     "duckduckgo-search",
        "sentence_transformers": "sentence-transformers",
        "faiss":                 "faiss-cpu",
        "numpy":                 "numpy",
        "nltk":                  "nltk",
    }
    for mod, pkg in needed.items():
        try:
            __import__(mod)
        except ImportError:
            print(f"Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg], stdout=subprocess.DEVNULL)
