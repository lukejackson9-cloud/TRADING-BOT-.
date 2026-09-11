"""
Alpaca Markets client — real-time (not delayed/EOD) US equity quotes, for
skills/monitor.md's intraday position check-ins. Unlike FMP/Massive (both
confirmed EOD-only on their free tiers as of 2026-09), Alpaca's free tier
streams/serves live IEX-exchange data during market hours.

Docs: https://docs.alpaca.markets/docs/about-market-data-api

Requires env vars: ALPACA_API_KEY, ALPACA_API_SECRET
Generate both from a free Alpaca account (paper trading is fine — this
project only ever reads market data, never places an Alpaca order):
https://alpaca.markets -> sign up -> dashboard -> API Keys (paper account
keys work for market data; no funding or identity verification needed
just to read quotes).

STATUS AS OF 2026-09-06: WORKING, confirmed live. `data.alpaca.markets`
is reachable (network policy fixed by the user) and all three functions
below were run for real against AAPL/MSFT/TSLA — response shapes match
what's documented in each function's docstring.

Free-tier limitation, important to keep in view: this is the IEX feed
only, not the full consolidated SIP tape across all US exchanges — IEX is
typically ~2-4% of a given stock's total volume. That means the "latest
quote" here can occasionally lag or slightly diverge from what you see in
the T212 app (which presumably uses a fuller feed). Treat it as "real-time
enough to catch a stop/target approach," not as a precise execution-grade
price -- this project has no execution path anyway, so that's an
acceptable tradeoff for an advisory check-in.

Confirmed live quirk worth remembering: get_latest_quote() during closed-
market hours (tested on a Sunday) returned a bid/ask spread of ~10% on
AAPL ($305.33 bid / $338.27 ask) -- wildly wider than AAPL's real intraday
spread, an artifact of no active market-making while the market is shut,
not a data error. get_latest_trade()'s last-print price ($319.80) was a
far more sensible number for the same closed-market moment. Prefer
get_latest_trade() over get_latest_quote() for a stop/target sanity check
outside active market hours; the quote endpoint is more meaningful while
the market is actually open.

Install: pip install requests --break-system-packages
"""

import os
import requests

API_KEY = os.environ["ALPACA_API_KEY"]
API_SECRET = os.environ["ALPACA_API_SECRET"]
DATA_BASE_URL = "https://data.alpaca.markets"

HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": API_SECRET,
}


def _get(path, **params):
    resp = requests.get(f"{DATA_BASE_URL}{path}", headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_latest_quote(symbol):
    """
    Latest bid/ask quote for one US equity symbol, IEX feed. Response shape
    CONFIRMED against a live call (AAPL, 2026-09-06):
      {"symbol": "AAPL", "quote": {"t": <RFC3339 timestamp>, "ax": <ask exchange>,
       "ap": <ask price>, "as": <ask size>, "bx": <bid exchange>, "bp": <bid price>,
       "bs": <bid size>, "c": [<condition codes>], "z": <tape>}}
    Use ("ap" + "bp") / 2 as an approximate mid-price for a stop/target check
    -- this is a quote, not a trade print, so there's no single "last price"
    field here; get_latest_trade() below gives the actual last executed price.
    NOTE: during closed-market hours this can show an unrealistically wide
    spread (confirmed: ~10% on AAPL on a Sunday) -- an artifact of no active
    market-making, not a data error. Prefer get_latest_trade() when the
    market is closed.
    """
    return _get(f"/v2/stocks/{symbol}/quotes/latest", feed="iex")


def get_latest_trade(symbol):
    """
    Most recent actual executed trade for one symbol, IEX feed. Simpler
    "what's it trading at right now" check than the bid/ask spread above,
    and more reliable outside active market hours (see get_latest_quote's
    note). Response shape CONFIRMED against a live call (AAPL, 2026-09-06):
      {"symbol": "AAPL", "trade": {"t": <RFC3339 timestamp>, "p": <price>,
       "s": <size>, "i": <trade id>, "x": <exchange>, "c": [<condition codes>],
       "z": <tape>}}
    """
    return _get(f"/v2/stocks/{symbol}/trades/latest", feed="iex")


def get_latest_trades(symbols):
    """
    Batch version of get_latest_trade for multiple symbols in one call --
    prefer this over looping get_latest_trade() when checking several open
    positions at once (e.g. skills/monitor.md checking a whole watchlist).
    symbols: list of ticker strings.
    Response shape CONFIRMED against a live call (AAPL/MSFT/TSLA, 2026-09-06):
      {"trades": {"AAPL": {...}, "MSFT": {...}, "TSLA": {...}}}
    (same per-symbol trade shape as get_latest_trade(), keyed by symbol
    instead of wrapped with a top-level "symbol" field)
    """
    return _get("/v2/stocks/trades/latest", symbols=",".join(symbols), feed="iex")


def get_historical_bars(symbol, start, end, timeframe="5Min", feed="iex"):
    """
    Paginated historical bars for one symbol between start/end (RFC3339
    timestamps, e.g. "2021-06-01T00:00:00Z"). Handles next_page_token
    looping -- CONFIRMED live (2026-09-07): a multi-year request returns
    ~2,000 bars per page regardless of a higher `limit` param, so a several
    year 5-min-bar pull needs dozens of pages; this function does that
    transparently and returns the full flat list.

    CONFIRMED live (2026-09-07): real intraday history starts mid-2021 --
    a confirmed-weekday request for 2020-06-03 and earlier returned 0 bars
    (status 200, just empty) while 2021-06-02 onward returned real data.
    This is a genuine data-depth limit on Alpaca's free/IEX tier, not a
    bug here -- don't request further back than ~2021-06 expecting data.

    Returns a flat list of bar dicts: [{"t":..., "o":..., "h":..., "l":...,
    "c":..., "v":...}, ...] in chronological order.
    """
    bars, page_token = [], None
    while True:
        params = {"timeframe": timeframe, "start": start, "end": end, "feed": feed, "limit": 10000}
        if page_token:
            params["page_token"] = page_token
        data = _get(f"/v2/stocks/{symbol}/bars", **params)
        bars.extend(data.get("bars") or [])
        page_token = data.get("next_page_token")
        if not page_token:
            break
    return bars


if __name__ == "__main__":
    # quick manual sanity check
    print(get_latest_trade("AAPL"))
