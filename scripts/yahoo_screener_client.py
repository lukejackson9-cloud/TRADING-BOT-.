"""
Yahoo Finance unofficial screener client — free, no API key, international
coverage (region-specific predefined screeners exist for the UK and other
markets), closing the gap that FMP (blocks non-US on free tier) and
Massive.com (US-only equity coverage) both leave open.

**THIS IS UNOFFICIAL AND UNSUPPORTED.** There is no published Yahoo Finance
API agreement for this endpoint — it's the same internal endpoint
finance.yahoo.com's own screener pages use, and it is exactly what the
popular `yfinance` Python library scrapes. It can rate-limit, change
response shape, or stop working entirely without notice (there is an open
GitHub issue against yfinance literally titled "Screener Is Broken" as of
research done 2026-09-06). Treat every call defensively:
  - Wrap calls in try/except and fall back to skills/screen.md's WebSearch
    step if this errors, rather than letting a screen.md run fail outright.
  - Don't assume today's response shape is permanent — if fields look
    different from what's documented below, that's this endpoint changing
    under you, not a bug in this file necessarily.
  - Mention to the user once per session if this stops working, same rule
    CLAUDE.md already applies to FMP/Massive/T212 network failures.

STATUS AS OF 2026-09-06: BLOCKED (network policy) AND UNTESTED. Add
`query1.finance.yahoo.com` and `query2.finance.yahoo.com` to this
environment's Custom network allowlist (claude.ai/code -> cloud icon ->
gear -> Network access -> Custom) before this can be verified against a
live response -- both hostnames, Yahoo uses them somewhat interchangeably
across different unofficial endpoints. Response shape below is inferred
from public documentation of the yfinance/yahooquery libraries that wrap
this same endpoint, NOT confirmed against a real call.

Known predefined screener IDs (from public documentation, unverified this
session): "day_gainers", "day_losers", "most_actives" (US, region=US);
region-specific variants exist for at least the UK ("day_gainers_gb",
"day_losers_gb") -- other region codes (DE, FR, JP, HK, etc.) are plausible
by the same naming pattern but NOT individually confirmed. Verify each
region code actually returns real data before trusting it; don't assume
the pattern holds for every market.

No install beyond `requests` (already used elsewhere in this repo).
"""

import requests

BASE_URL = "https://query2.finance.yahoo.com"
HEADERS = {
    # Yahoo's unofficial endpoints reject requests with no browser-like
    # User-Agent -- this is not a real credential, just a compatibility
    # header every scraper of this endpoint uses.
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


def get_predefined_screener(scr_id, region="US", count=25):
    """
    Run one of Yahoo's predefined screeners (e.g. "day_gainers_gb" for UK
    day gainers). Response shape (UNVERIFIED, inferred from yfinance/
    yahooquery library source -- confirm against a live call before
    trusting this):
      {"finance": {"result": [{"id": ..., "quotes": [
          {"symbol": ..., "shortName": ..., "regularMarketPrice": ...,
           "regularMarketChangePercent": ..., "regularMarketVolume": ...,
           "fullExchangeName": ..., ...}, ...
      ]}]}}
    Raises requests.HTTPError or returns unexpected shape if Yahoo has
    changed or blocked this endpoint -- callers MUST handle that and fall
    back to WebSearch (see skills/screen.md), not crash the whole screen.
    """
    resp = requests.get(
        f"{BASE_URL}/v1/finance/screener/predefined/saved",
        headers=HEADERS,
        params={
            "formatted": "false",
            "lang": "en-US",
            "region": region,
            "scrIds": scr_id,
            "count": count,
            "corsDomain": "finance.yahoo.com",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def get_uk_gainers(count=25):
    """UK (LSE) day gainers -- the specific gap this client exists to fill."""
    return get_predefined_screener("day_gainers_gb", region="GB", count=count)


def get_uk_losers(count=25):
    """UK (LSE) day losers."""
    return get_predefined_screener("day_losers_gb", region="GB", count=count)


def extract_quotes(screener_response):
    """
    Pull the flat list of quote dicts out of get_predefined_screener()'s
    nested response shape -- convenience helper so callers don't all have
    to know the ["finance"]["result"][0]["quotes"] path. Returns [] (not
    an error) if the shape doesn't match what's expected, since that's a
    signal this endpoint changed -- let the caller decide whether to
    WebSearch-fallback rather than raising.
    """
    try:
        return screener_response["finance"]["result"][0]["quotes"]
    except (KeyError, IndexError, TypeError):
        return []


if __name__ == "__main__":
    # quick manual sanity check
    data = get_uk_gainers(count=10)
    quotes = extract_quotes(data)
    print(f"got {len(quotes)} UK gainers")
    for q in quotes[:5]:
        print(q.get("symbol"), q.get("shortName"), q.get("regularMarketChangePercent"))
