"""
Massive.com (formerly Polygon.io) client — a genuine whole-market screener,
unlike FMP's free tier (see market_screener_client.py's docstring), which
only exposes a curated top-50 gainers/losers/actives list on its free plan.

Docs: https://massive.com/docs (formerly polygon.io/docs)

Requires env var: MASSIVE_API_KEY

STATUS AS OF 2026-09-03: WORKING, confirmed live. api.massive.com is
reachable from this environment (network policy fixed by the user) and
get_grouped_daily() was run for real against 2026-09-02 -- returned
resultsCount 12,541 with the exact response shape documented below. Note:
api.polygon.io (the old domain) is STILL blocked -- that's fine, this
client only uses api.massive.com, but don't assume the old domain works
if some other tool references it.

Why this one, out of the free options researched on 2026-09-03: the
`/v2/aggs/grouped/...` endpoint below returns EVERY US stock's OHLCV for a
whole trading day in ONE API call -- a real whole-market screen, not a
curated top-N list (12,541 tickers in the live test above, vs FMP's free
tier which only exposes a top-50 gainers/losers/actives list -- see
market_screener_client.py). Free tier: 5 calls/min, no credit card
required. Data is end-of-day (or 15-min-delayed intraday on some plans)
-- fine for this project's days-to-2-week horizon, not fine for
same-second execution (moot here, this project doesn't execute trades
anyway).

Free-tier notes (re-verify against current docs once network access is
confirmed -- API terms/limits change):
  - 5 requests/minute on the free plan. The grouped-daily call below is ONE
    request regardless of market size, so this limit is not the constraint
    it would be for a per-ticker-quote approach.
  - Data is end-of-day, NOT real-time or even intraday -- confirmed live:
    requesting the grouped-daily for the CURRENT trading day while the
    market is still open returns status "NOT_AUTHORIZED", not partial
    data. The most recent usable date is always the last COMPLETED
    session. This matters for screen.md: a pre-market or mid-day run
    should treat Massive's data as "yesterday's session," not "today so
    far" -- use FMP's gainers/losers/actives (market_screener_client.py)
    for genuine same-day intraday framing, and Massive for whole-market
    breadth on the last completed day. They're complementary, not
    interchangeable.

Install: pip install requests --break-system-packages
"""

import os
import time
import json
from pathlib import Path

import requests

API_KEY = os.environ["MASSIVE_API_KEY"]
BASE_URL = "https://api.massive.com"


def _get(path, **params):
    params["apiKey"] = API_KEY
    resp = requests.get(f"{BASE_URL}{path}", params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def get_grouped_daily(date, adjusted=True):
    """
    Every US stock's OHLCV for one trading date (YYYY-MM-DD string) in a
    single call. Response shape CONFIRMED against a live call for
    2026-09-02 (resultsCount 12,541):
      {
        "results": [
          {"T": "AAPL", "o": ..., "h": ..., "l": ..., "c": ...,
           "v": ..., "vw": ..., "t": <ms epoch>, "n": <trade count>},
          ...
        ],
        "resultsCount": <int>, "status": "OK", "queryCount": <int>,
        "adjusted": <bool>
      }
    Note "v" (volume) is a float in the live response, not always an int
    (e.g. fractional-share-inclusive volume) -- cast/round as needed rather
    than assuming int. Use "T" for ticker, "c" for close price, "v" for
    volume when filtering (e.g. screen.md's $5-$500 price / >1M volume
    rules) -- apply those filters client-side on this one payload rather
    than per-ticker calls. This includes ALL US securities (stocks, ETFs,
    even some crypto-adjacent tickers like XRP showed up in testing) --
    filter by known-equity criteria (price/volume bounds alone won't
    exclude ETFs) if screen.md wants single-name equities only.
    """
    return _get(f"/v2/aggs/grouped/locale/us/market/stocks/{date}", adjusted=str(adjusted).lower())


def get_previous_close(ticker, adjusted=True):
    """Single ticker's most recent daily OHLCV -- for spot-checking one name."""
    return _get(f"/v2/aggs/ticker/{ticker}/prev", adjusted=str(adjusted).lower())


def get_common_stock_tickers(cache_path="data/reference/equity_tickers.json", max_age_days=7, max_pages=20):
    """
    Full list of active US common-stock tickers (type=CS) -- used to filter
    get_grouped_daily()'s output down to single-name equities, since that
    payload includes ETFs/crypto-adjacent tickers too (confirmed live: XRP
    appeared in a 2026-09-02 grouped-daily pull).

    Paginates /v3/reference/tickers (1000/page, ~8-9 pages for the full US
    common-stock universe) and caches the result to cache_path (relative to
    the CWD -- run this from the repo root, same convention as every other
    script here). This list changes rarely (new IPOs/delistings), and
    re-fetching 8+ pages on every screen.md run would burn a big chunk of
    the free tier's 5 req/min limit for no reason -- pass max_age_days=0 to
    force a refresh (e.g. after a known IPO you want to catch).
    """
    cache_file = Path(cache_path)
    if cache_file.exists():
        cached = json.loads(cache_file.read_text())
        age_days = (time.time() - cached.get("fetched_at", 0)) / 86400
        if age_days < max_age_days:
            return set(cached["tickers"])

    tickers = []
    url = f"{BASE_URL}/v3/reference/tickers"
    params = {"market": "stocks", "type": "CS", "active": "true", "limit": 1000, "apiKey": API_KEY}
    for page in range(max_pages):
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        tickers.extend(r["ticker"] for r in data.get("results", []))
        next_url = data.get("next_url")
        if not next_url:
            break
        url, params = next_url, {"apiKey": API_KEY}
        if page < max_pages - 1:
            time.sleep(13)  # free tier: 5 req/min -- stay safely under

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps({"fetched_at": time.time(), "tickers": sorted(set(tickers))}, indent=2))
    return set(tickers)


def screen_market_movers(date, prev_date, price_min=5, price_max=500, volume_min=1_000_000, equity_only=True):
    """
    A real whole-market screen: pulls get_grouped_daily() for `date` and
    `prev_date` (YYYY-MM-DD, both must be completed trading days -- see the
    module docstring on same-day data not being available), computes
    close-to-close % change, and filters to price_min-price_max and
    volume_min -- matching CLAUDE.md's screening rules. equity_only=True
    (default, recommended) restricts results to get_common_stock_tickers(),
    excluding ETFs/other non-equity tickers.

    Returns a list of dicts sorted by absolute % change, descending:
      [{"ticker": ..., "close": ..., "prev_close": ..., "pct_change": ...,
        "volume": ...}, ...]

    Caller is responsible for picking two real, consecutive-ish trading
    days -- weekends/holidays return empty or NOT_AUTHORIZED; if a chosen
    `date` comes back with resultsCount 0 or a non-OK status, step back a
    day and retry rather than trusting an empty/partial result.
    """
    today_data = get_grouped_daily(date)
    prev_data = get_grouped_daily(prev_date)
    prev_close = {r["T"]: r["c"] for r in prev_data.get("results", [])}

    equities = get_common_stock_tickers() if equity_only else None

    out = []
    for r in today_data.get("results", []):
        ticker = r["T"]
        if equities is not None and ticker not in equities:
            continue
        close = r["c"]
        volume = r["v"]
        if not (price_min <= close <= price_max):
            continue
        if volume < volume_min:
            continue
        pc = prev_close.get(ticker)
        if not pc:
            continue
        pct_change = (close - pc) / pc * 100
        out.append({
            "ticker": ticker, "close": close, "prev_close": pc,
            "pct_change": pct_change, "volume": volume,
        })

    out.sort(key=lambda x: abs(x["pct_change"]), reverse=True)
    return out


if __name__ == "__main__":
    # quick manual sanity check -- pick a recent past trading date
    import datetime
    d = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    data = get_grouped_daily(d)
    print(f"status: {data.get('status')}, resultsCount: {data.get('resultsCount')}")
    print(data.get("results", [])[:3])
