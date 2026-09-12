"""
Trading 212 Public API client.
Docs: https://docs.trading212.com/  (API is in beta)

Environments:
  Paper/Demo: https://demo.trading212.com/api/v0
  Live:       https://live.trading212.com/api/v0

Auth: HTTP Basic, username=API_KEY, password=API_SECRET
Generate keys from the Trading 212 app: Settings > API (or "Switch to Practice"
first if you want a DEMO key instead of a LIVE key).

Requires env vars:
  T212_API_KEY
  T212_API_SECRET
  T212_BASE_URL   (defaults to demo/paper — see below)

Notes / current API limitations (check docs.trading212.com for updates,
this API is actively evolving):
  - Only "Invest" and "Stocks ISA" account types are supported (no CFD).
  - Live (real-money) environment: only MARKET orders can be executed via API.
    Limit/stop orders are documented but live support may be restricted —
    verify against current docs before relying on them live.
  - Orders execute only in your account's primary currency.
  - Ticker format is like "AAPL_US_EQ" — use the instruments endpoint to look
    up exact tickers rather than guessing.

Install: pip install requests --break-system-packages
"""

import os
import base64
import requests

API_KEY = os.environ["T212_API_KEY"]
API_SECRET = os.environ["T212_API_SECRET"]
BASE_URL = os.environ.get("T212_BASE_URL", "https://demo.trading212.com/api/v0")

_creds = base64.b64encode(f"{API_KEY}:{API_SECRET}".encode()).decode()
HEADERS = {
    "Authorization": f"Basic {_creds}",
    "Content-Type": "application/json",
}


def _get(path, **kwargs):
    resp = requests.get(f"{BASE_URL}{path}", headers=HEADERS, timeout=15, **kwargs)
    resp.raise_for_status()
    return resp.json()


def _post(path, payload):
    resp = requests.post(f"{BASE_URL}{path}", headers=HEADERS, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_account_cash():
    """Return account cash/value snapshot."""
    return _get("/equity/account/cash")


def get_portfolio():
    """Return current open positions."""
    return _get("/equity/portfolio")


def get_pending_orders():
    """Return all currently active (unfilled) orders."""
    return _get("/equity/orders")


def lookup_instrument(ticker_query):
    """
    Look up the exact T212 ticker code for a symbol before placing an order —
    don't guess the "_US_EQ" style suffix.
    """
    instruments = _get("/equity/metadata/instruments")
    return [i for i in instruments if ticker_query.upper() in i.get("ticker", "")]


def place_market_order(ticker, quantity, extended_hours=False):
    """
    Place a market order. Positive quantity = buy, negative = sell.
    NOTE: this function sends a REAL order the moment it's called — the
    approval gate belongs in skills/execute_approved.md, not here.
    """
    payload = {
        "ticker": ticker,
        "quantity": quantity,
        "extendedHours": extended_hours,
    }
    return _post("/equity/orders/market", payload)


def place_limit_order(ticker, quantity, limit_price, time_validity="DAY"):
    """Place a limit order (demo environment; verify live support in current docs)."""
    payload = {
        "ticker": ticker,
        "quantity": quantity,
        "limitPrice": limit_price,
        "timeValidity": time_validity,
    }
    return _post("/equity/orders/limit", payload)


if __name__ == "__main__":
    # quick manual sanity check
    print(get_account_cash())
