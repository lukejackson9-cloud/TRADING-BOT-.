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

STATUS AS OF 2026-09-06: WORKING, confirmed live. `get_uk_gainers()` and
`get_uk_losers()` were both run for real and returned genuine data —
response shape matches what's documented below. A bare request with no
User-Agent gets a 429 from Yahoo directly (confirmed) — that's Yahoo's own
bot-defense, not this environment's network policy; the User-Agent header
below is required, not optional.

**Confirmed finding: `day_gainers_gb`/`day_losers_gb` return a MIX of
exchanges, not just genuine UK-domestic stocks** — check `fullExchangeName`
on every quote:
  - `"LSE"` or `"Aquis AQSE"` — genuine UK-domestic stocks, priced in GBp
    (pence) per the `currency` field. Confirmed live: a stock with
    `regularMarketPrice: 2.25, currency: "GBp"` is 2.25 PENCE (£0.0225),
    not £2.25 — convert before applying any price filter (see screen.md's
    international price-filter gotcha). Volume can be enormous for
    sub-penny names (confirmed: one at $0.0091 GBp had 3.5 BILLION shares
    volume) — that's a sign of a worthless penny stock, not real liquidity;
    don't let raw volume alone pass a filter without a sane price floor.
  - `"IOB"` (International Order Book) — foreign companies cross-listed on
    the LSE, priced in THEIR OWN home currency (confirmed live: EUR, SEK,
    NOK, CHF, RON all appeared in one 10-row sample), not GBP/GBX at all.
    These aren't really "UK stocks" for research purposes even though
    they show up in a `_gb`-region screener — treat them as whatever
    market their `currency` field says, and research/size them in that
    currency, not GBP.

Known predefined screener IDs (from public documentation): "day_gainers",
"day_losers", "most_actives" (US, region=US); UK variants confirmed live
("day_gainers_gb", "day_losers_gb"). Other region codes (DE, FR, JP, HK,
etc.) are plausible by the same naming pattern but NOT individually
confirmed — verify each one actually returns real data before trusting it,
don't assume the pattern holds for every market.

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
    day gainers). Response shape CONFIRMED against live calls (2026-09-06):
      {"finance": {"result": [{"id": ..., "quotes": [
          {"symbol": ..., "shortName": ..., "regularMarketPrice": ...,
           "regularMarketChangePercent": ..., "regularMarketVolume": ...,
           "fullExchangeName": ..., "currency": ...}, ...
      ]}]}}
    IMPORTANT: check "currency" and "fullExchangeName" on every quote --
    see the module docstring's confirmed finding on GBp-vs-other-currency
    mixing in the `_gb` screeners. Don't assume the number in
    "regularMarketPrice" is in the currency you expect.
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
