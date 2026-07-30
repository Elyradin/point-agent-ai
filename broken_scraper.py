import requests
from bs4 import BeautifulSoup
import anthropic

client = anthropic.Anthropic() 


def scrape_and_summarize(url: str) -> str:
    response = requests.get(url)  
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text()  

    prompt = f"Summarize this: {text}" 

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    summary = message.content[0].text

    return summary


if __name__ == "__main__":
    import sys

    url = sys.argv[1]
    print(scrape_and_summarize(url))