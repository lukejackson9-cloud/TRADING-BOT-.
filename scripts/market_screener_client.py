"""
Financial Modeling Prep (FMP) client — a real market screener, unlike the
WebSearch-based guessing skills/screen.md used before this existed.
Docs: https://site.financialmodelingprep.com/developer/docs

Requires env var: FMP_API_KEY

Free-tier notes, confirmed live against a real key on 2026-09-02:
  - FMP retired the /api/v3/ namespace for keys created after 2025-08-31 —
    it now returns a "Legacy Endpoint" error. Use /stable/ instead (this
    module does). If a future session sees that error again, re-check
    FMP's docs for another namespace change before assuming the key is bad.
  - /stable/biggest-gainers, /stable/biggest-losers, /stable/most-actives,
    /stable/quote, and /stable/earnings-calendar all work on the free tier.
  - /stable/stock-screener (whole-market price/volume/sector filter) and
    /stable/company-screener both return empty/"Restricted Endpoint" on the
    free tier — screen_stocks() below is kept for reference in case of a
    plan upgrade, but don't rely on it; screen.md's fallback is to filter
    gainers/losers/most-actives by price client-side and check volume via
    get_quote() on the shortlist instead of a whole-market screener call.
  - The movers endpoints (gainers/losers/actives) do not include volume —
    only get_quote() does. Confirm volume there, not from the movers list.
  - No batch quotes — /stable/quote only accepts one symbol at a time.

Install: pip install requests --break-system-packages
"""

import os
import requests

API_KEY = os.environ["FMP_API_KEY"]
BASE_URL = "https://financialmodelingprep.com/stable"


def _get(path, **params):
    params["apikey"] = API_KEY
    resp = requests.get(f"{BASE_URL}{path}", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_gainers():
    """Today's biggest % gainers across the market."""
    return _get("/biggest-gainers")


def get_losers():
    """Today's biggest % losers across the market."""
    return _get("/biggest-losers")


def get_most_active():
    """Today's highest-volume names."""
    return _get("/most-actives")


def screen_stocks(price_more_than=5, price_less_than=500, volume_more_than=1_000_000,
                   market_cap_more_than=None, sector=None, limit=100):
    """
    Whole-market screener by price/volume/sector. NOT AVAILABLE on FMP's
    free tier as of 2026-09-02 (returns [] or "Restricted Endpoint") — kept
    for reference in case of a plan upgrade. Use gainers/losers/actives +
    get_quote() instead; see module docstring.
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
    return _get("/earnings-calendar", **{"from": from_date, "to": to_date})


def get_quote(symbol):
    """Current price/volume/market-cap snapshot for one ticker."""
    result = _get("/quote", symbol=symbol)
    return result[0] if result else None


if __name__ == "__main__":
    # quick manual sanity check
    print(get_gainers()[:5])
