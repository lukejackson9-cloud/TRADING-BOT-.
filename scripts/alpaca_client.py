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

STATUS AS OF 2026-09-06: BLOCKED, untested against live data. Key/secret
were provided and added to .env, but `data.alpaca.markets` is rejected by
this environment's network egress policy (confirmed via the proxy's
relay-failure log: "gateway answered 403 to CONNECT (policy denial or
upstream failure)") — the same kind of block FMP and Massive.com both had
before their domains were added to this environment's Custom network
allowlist (claude.ai/code -> cloud icon -> gear -> Network access ->
Custom). Add `data.alpaca.markets` there (or run from a local Claude Code
session) before relying on this client — then re-verify the response
shape below actually matches a real call, since it was written from
Alpaca's public docs, not confirmed against a live response.

Free-tier limitation, important to keep in view: this is the IEX feed
only, not the full consolidated SIP tape across all US exchanges — IEX is
typically ~2-4% of a given stock's total volume. That means the "latest
quote" here can occasionally lag or slightly diverge from what you see in
the T212 app (which presumably uses a fuller feed). Treat it as "real-time
enough to catch a stop/target approach," not as a precise execution-grade
price -- this project has no execution path anyway, so that's an
acceptable tradeoff for an advisory check-in.

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
    per Alpaca's public docs (UNVERIFIED against a live call):
      {"symbol": "AAPL", "quote": {"t": <RFC3339 timestamp>, "ax": <ask exchange>,
       "ap": <ask price>, "as": <ask size>, "bx": <bid exchange>, "bp": <bid price>,
       "bs": <bid size>, ...}}
    Use ("ap" + "bp") / 2 as an approximate mid-price for a stop/target check
    -- this is a quote, not a trade print, so there's no single "last price"
    field here; get_latest_trade() below gives the actual last executed price.
    """
    return _get(f"/v2/stocks/{symbol}/quotes/latest", feed="iex")


def get_latest_trade(symbol):
    """
    Most recent actual executed trade for one symbol, IEX feed. Simpler
    "what's it trading at right now" check than the bid/ask spread above.
    Response shape (UNVERIFIED):
      {"symbol": "AAPL", "trade": {"t": <timestamp>, "p": <price>, "s": <size>, ...}}
    """
    return _get(f"/v2/stocks/{symbol}/trades/latest", feed="iex")


def get_latest_trades(symbols):
    """
    Batch version of get_latest_trade for multiple symbols in one call --
    prefer this over looping get_latest_trade() when checking several open
    positions at once (e.g. skills/monitor.md checking a whole watchlist).
    symbols: list of ticker strings.
    Response shape (UNVERIFIED): {"trades": {"AAPL": {...}, "MSFT": {...}}}
    """
    return _get("/v2/stocks/trades/latest", symbols=",".join(symbols), feed="iex")


if __name__ == "__main__":
    # quick manual sanity check
    print(get_latest_trade("AAPL"))
