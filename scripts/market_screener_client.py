"""
Financial Modeling Prep (FMP) client — a real market screener, unlike the
WebSearch-based guessing skills/screen.md used before this existed.
Docs: https://site.financialmodelingprep.com/developer/docs

Requires env var: FMP_API_KEY

Free-tier notes (verify current limits/endpoints against FMP's docs before
relying on this — their API has changed shape before, e.g. a "stable"
endpoint namespace alongside the older /api/v3/ one):
  - Free tier is rate-limited (historically ~250 requests/day) and some
    endpoints (e.g. analyst upgrade/downgrade feeds) may be paid-tier only.
    If a call returns 401/403 or an "Upgrade your plan" style payload,
    that's the likely cause — don't retry blindly, log it and move on.

Install: pip install requests --break-system-packages
"""

import os
import requests

API_KEY = os.environ["FMP_API_KEY"]
BASE_URL = "https://financialmodelingprep.com/api/v3"


def _get(path, **params):
    params["apikey"] = API_KEY
    resp = requests.get(f"{BASE_URL}{path}", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_gainers():
    """Today's biggest % gainers across the market."""
    return _get("/stock_market/gainers")


def get_losers():
    """Today's biggest % losers across the market."""
    return _get("/stock_market/losers")


def get_most_active():
    """Today's highest-volume names."""
    return _get("/stock_market/actives")


def screen_stocks(price_more_than=5, price_less_than=500, volume_more_than=1_000_000,
                   market_cap_more_than=None, sector=None, limit=100):
    """
    A real screener: filter the whole market by criteria instead of
    guessing at search terms. Defaults match CLAUDE.md's price/volume
    filters ($5-$500, >1M avg volume).
    """
    params = {
        "priceMoreThan": price_more_than,
        "priceLowerThan": price_less_than,
        "volumeMoreThan": volume_more_than,
        "limit": limit,
    }
    if market_cap_more_than is not None:
        params["marketCapMoreThan"] = market_cap_more_than
    if sector is not None:
        params["sector"] = sector
    return _get("/stock-screener", **params)


def get_earnings_calendar(from_date, to_date):
    """
    Companies reporting earnings between from_date and to_date
    (YYYY-MM-DD strings). Powers screen.md's pre-catalyst earnings lookahead
    with real dates instead of a WebSearch guess.
    """
    return _get("/earning_calendar", **{"from": from_date, "to": to_date})


def get_quote(symbol):
    """Current price/volume/market-cap snapshot for one ticker."""
    result = _get(f"/quote/{symbol}")
    return result[0] if result else None


if __name__ == "__main__":
    # quick manual sanity check
    print(get_gainers()[:5])
