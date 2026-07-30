import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "after"))

from scraper import enforce_word_limit, chunk_text, summarize_long_text, Summarizer


def test_enforce_word_limit_truncates_long_summary():
    long_summary = " ".join(["word"] * 300)
    result = enforce_word_limit(long_summary, max_words=150)
    assert len(result.split()) <= 151  
    assert result.endswith("...")


def test_enforce_word_limit_keeps_short_summary_untouched():
    short_summary = "This is a short summary."
    result = enforce_word_limit(short_summary, max_words=150)
    assert result == short_summary


def test_chunk_text_splits_long_content():
    long_text = "This is a sentence. " * 1000
    chunks = chunk_text(long_text, chunk_size=2000)
    assert len(chunks) > 1
    assert all(len(c) <= 2200 for c in chunks)


def test_chunk_text_keeps_short_content_as_single_chunk():
    short_text = "Short content here."
    chunks = chunk_text(short_text, chunk_size=2000)
    assert chunks == [short_text]


class DummySummarizer(Summarizer):

    def __init__(self):
        self.api_key = None
        self._client = None


def test_summarize_long_text_respects_guardrail_end_to_end():
    long_text = "This sentence repeats many times to simulate a very long page. " * 500
    dummy = DummySummarizer()
    result = summarize_long_text(long_text, dummy, max_words=50)
    assert len(result.split()) <= 51