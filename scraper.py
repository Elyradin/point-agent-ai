import os
import re
import time
import logging
from dataclasses import dataclass
from typing import List, Optional

import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("scraper")

MAX_SUMMARY_WORDS = 150
CHUNK_CHAR_SIZE = 6000
MIN_CONTENT_CHARS_BEFORE_JS_FALLBACK = 200
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3


@dataclass
class ScrapeResult:
    url: str
    text: str
    used_js_fallback: bool = False


class FetchError(Exception):
    pass


def _build_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=MAX_RETRIES,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; SupportBot/1.0)"})
    return session


def _extract_readable_text(html: str) -> str:
    """Buang boilerplate, kembalikan teks utama halaman saja."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "noscript"]):
        tag.decompose()

    noise_selectors = [
        ".navbox", ".sidebar", ".infobox", ".vector-toc", ".mw-jump-link",
        ".hatnote", ".mw-editsection", ".reflist", "#mw-navigation",
        ".ambox", ".metadata",
    ]
    for selector in noise_selectors:
        for el in soup.select(selector):
            el.decompose()

    main = soup.find("article") or soup.find("main") or soup.body or soup
    text = main.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fetch_static(url: str, session: requests.Session) -> str:
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        raise FetchError(f"Static fetch gagal untuk {url}: {e}") from e


def _fetch_rendered(url: str) -> Optional[str]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright belum terinstall - skip JS-render fallback untuk %s", url)
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, timeout=REQUEST_TIMEOUT * 1000, wait_until="networkidle")
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        logger.warning("JS-render fallback gagal untuk %s: %s", url, e)
        return None


def scrape(url: str) -> ScrapeResult:
    session = _build_session()
    html = _fetch_static(url, session)
    text = _extract_readable_text(html)
    used_js_fallback = False

    if len(text) < MIN_CONTENT_CHARS_BEFORE_JS_FALLBACK:
        logger.info("Konten terlalu tipis (%d char) - coba JS render fallback untuk %s", len(text), url)
        rendered_html = _fetch_rendered(url)
        if rendered_html:
            rendered_text = _extract_readable_text(rendered_html)
            if len(rendered_text) > len(text):
                text = rendered_text
                used_js_fallback = True

    if not text:
        raise FetchError(f"Tidak ada konten yang bisa diekstrak dari {url}")

    return ScrapeResult(url=url, text=text, used_js_fallback=used_js_fallback)


# ---------- Chunking ----------
def chunk_text(text: str, chunk_size: int = CHUNK_CHAR_SIZE) -> List[str]:
    if len(text) <= chunk_size:
        return [text]

    sentences = re.split(r"(?<=[.!?]) +", text)
    chunks, current = [], ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 > chunk_size:
            if current:
                chunks.append(current.strip())
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current.strip())
    return chunks


# ---------- Backend summarization ----------
class Summarizer:
    
    def __init__(self):
        provider = os.environ.get("SUMMARIZER_PROVIDER", "").lower()
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        self.gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.provider = None
        self._client = None

        if provider == "anthropic" and self.anthropic_key:
            self._init_anthropic()
        elif provider == "gemini" and self.gemini_key:
            self._init_gemini()
        elif self.anthropic_key:
            self._init_anthropic()
        elif self.gemini_key:
            self._init_gemini()
        else:
            logger.info("Tidak ada API key ditemukan - pakai fallback summarizer")

    def _init_anthropic(self):
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.anthropic_key)
            self.provider = "anthropic"
        except ImportError:
            logger.warning("Package anthropic belum terinstall - pakai fallback summarizer")

    def _init_gemini(self):
        try:
            from google import genai
            self._client = genai.Client(api_key=self.gemini_key)
            self.provider = "gemini"
        except ImportError:
            logger.warning("Package google-genai belum terinstall - pakai fallback summarizer")

    def summarize(self, text: str, max_words: int) -> str:
        if self.provider == "anthropic":
            return self._summarize_anthropic(text, max_words)
        if self.provider == "gemini":
            return self._summarize_gemini(text, max_words)
        return self._summarize_fallback(text, max_words)

    def _prompt(self, text: str, max_words: int) -> str:
        return (
            f"Summarize the following content in no more than {max_words} words. "
            f"Be concise and factual, do not invent details that are not present.\n\n{text}"
        )

    def _summarize_anthropic(self, text: str, max_words: int) -> str:
        message = self._client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            messages=[{"role": "user", "content": self._prompt(text, max_words)}],
        )
        return "".join(block.text for block in message.content if block.type == "text").strip()

    def _summarize_gemini(self, text: str, max_words: int) -> str:
        try:
            response = self._client.models.generate_content(
                model="gemini-2.0-flash",
                contents=self._prompt(text, max_words),
            )
            return (response.text or "").strip()
        except Exception as e:
            logger.warning("Gemini call gagal (%s) - pakai fallback untuk chunk ini", e)
            return self._summarize_fallback(text, max_words)

    def _summarize_fallback(self, text: str, max_words: int) -> str:
        words = text.split()
        return " ".join(words[:max_words])


# ---------- Guardrail ----------
def enforce_word_limit(summary: str, max_words: int) -> str:
    words = summary.split()
    if len(words) <= max_words:
        return summary
    logger.warning("Ringkasan melebihi %d kata (%d) - dipotong paksa", max_words, len(words))
    return " ".join(words[:max_words]).rstrip(",.;:") + "..."


def summarize_long_text(text: str, summarizer: Summarizer, max_words: int = MAX_SUMMARY_WORDS) -> str:
    chunks = chunk_text(text)

    if len(chunks) == 1:
        raw_summary = summarizer.summarize(chunks[0], max_words)
        return enforce_word_limit(raw_summary, max_words)

    logger.info("Konten dipecah jadi %d chunk - jalankan map-reduce summarization", len(chunks))
    partial_summaries = [summarizer.summarize(c, max_words=80) for c in chunks]
    combined = " ".join(partial_summaries)
    final_summary = summarizer.summarize(combined, max_words)
    return enforce_word_limit(final_summary, max_words)


# ---------- Entry point publik ----------
def scrape_and_summarize(url: str, max_words: int = MAX_SUMMARY_WORDS) -> dict:
    start = time.time()
    try:
        result = scrape(url)
    except FetchError as e:
        logger.error(str(e))
        return {"url": url, "error": str(e)}

    summarizer = Summarizer()
    summary = summarize_long_text(result.text, summarizer, max_words)

    return {
        "url": url,
        "summary": summary,
        "word_count": len(summary.split()),
        "source_chars": len(result.text),
        "used_js_fallback": result.used_js_fallback,
        "elapsed_seconds": round(time.time() - start, 2),
    }


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python scraper.py <url> [max_words]")
        sys.exit(1)

    target_url = sys.argv[1]
    words_limit = int(sys.argv[2]) if len(sys.argv) > 2 else MAX_SUMMARY_WORDS
    output = scrape_and_summarize(target_url, words_limit)
    print(json.dumps(output, indent=2, ensure_ascii=False))