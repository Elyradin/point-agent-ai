import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

if not google_api_key:
    raise ValueError("GOOGLE_API_KEY atau GEMINI_API_KEY belum diatur")

llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=google_api_key)


def scrape_and_summarize(url: str) -> str:
    response = requests.get(url, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text("\n", strip=True)

    prompt = f"Ringkas konten berikut dalam bahasa Indonesia:\n\n{text[:12000]}"
    response = llm.invoke(prompt)

    content = getattr(response, "content", response)
    if isinstance(content, list):
        return "\n".join(
            item["text"] for item in content if isinstance(item, dict) and item.get("type") == "text"
        )
    return str(content)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python scraper_gemini.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    print(scrape_and_summarize(url))
