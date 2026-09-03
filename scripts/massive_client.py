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
  - Data is end-of-day / delayed, not real-time -- matches this project's
    strategy (screen.md runs pre-market/mid-day, not intraday scalping).

Install: pip install requests --break-system-packages
"""

import os
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


if __name__ == "__main__":
    # quick manual sanity check -- pick a recent past trading date
    import datetime
    d = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    data = get_grouped_daily(d)
    print(f"status: {data.get('status')}, resultsCount: {data.get('resultsCount')}")
    print(data.get("results", [])[:3])
