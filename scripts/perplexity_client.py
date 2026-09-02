"""
Perplexity API client — used for short-term catalyst/news/sentiment research.
Docs: https://docs.perplexity.ai/

Requires env var: PERPLEXITY_API_KEY
Install: pip install requests --break-system-packages
"""

import os
import requests

API_KEY = os.environ["PERPLEXITY_API_KEY"]
API_URL = "https://api.perplexity.ai/chat/completions"


def research(ticker: str, model: str = "sonar-pro") -> str:
    """
    Ask Perplexity for recent news/catalyst/sentiment on a ticker.
    Returns raw text response for the agent to summarize into
    /data/research/{date}/{TICKER}.md
    """
    prompt = (
        f"Give a short-term trading research brief on {ticker} stock. "
        f"Cover: (1) any news or catalyst in the last 48 hours, "
        f"(2) analyst sentiment or notable rating changes, "
        f"(3) key near-term risks. Be concise and factual, cite what you're basing this on."
    )

    resp = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    print(research(ticker))
