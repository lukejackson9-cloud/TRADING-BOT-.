"""
TradingView technical-analysis rating client, via the unofficial
`tradingview-ta` PyPI library (wraps TradingView's own public technical-
analysis summary endpoint -- the same one their website's TA widget uses,
no login/auth required, same category of "unofficial but publicly
reachable" as scripts/yahoo_screener_client.py).

**THIS IS UNOFFICIAL AND UNSUPPORTED.** No published API agreement exists
for this endpoint. Treat every call defensively (try/except, fall back to
skipping this cross-check rather than failing a whole screen/research run)
-- it can change shape or stop working without notice, same caveat as the
Yahoo client.

WHAT THIS ACTUALLY GIVES YOU: a per-symbol consensus rating (STRONG_BUY /
BUY / NEUTRAL / SELL / STRONG_SELL) aggregated across ~26 oscillators and
moving averages that TradingView itself computes -- a different KIND of
signal than this project's own OHLCV-based backtests (scripts/backtest_ta.py,
scripts/backtest_ict.py): it's someone else's black-box aggregation, not a
transparent rule we can inspect or backtest ourselves. Useful as a quick
cross-check ("does TradingView's own indicator consensus agree with what
we found"), NOT a replacement for this project's own backtested setups,
and NOT a market-mover screener -- it rates a symbol you already have, it
doesn't discover new ones. Slot it into research.md/council.md as
supporting context, not a standalone verdict source.

STATUS AS OF 2026-09-07: WORKING, confirmed live (network access to
scanner.tradingview.com required -- blocked by this environment's default
policy until explicitly allowlisted, same as every other new domain this
project has added). Confirmed live: single-symbol lookup (AAPL), batch
lookup (AAPL/MSFT/F in one call), and international coverage (VOD on LSE
via screener="uk") all returned real data.

Symbol format is exchange-specific and matters:
  - Single lookup (TA_Handler): symbol and exchange are separate params,
    e.g. symbol="AAPL", exchange="NASDAQ", screener="america".
  - Batch lookup (get_multiple_analysis): symbols are "EXCHANGE:SYMBOL"
    strings, e.g. "NASDAQ:AAPL", within one screener/interval.
  - screener is a market grouping, not just a country code -- confirmed
    values include "america" and "uk"; other markets are plausible by the
    same pattern but unverified here -- check before trusting one, same
    rule as Yahoo's region codes.

Install: pip install tradingview-ta --break-system-packages
"""

from tradingview_ta import TA_Handler, get_multiple_analysis


def get_rating(symbol, exchange, screener="america", interval="1d"):
    """
    One symbol's TA consensus. Response (a TA_Handler.get_analysis()
    Analysis object) has, per a live 2026-09-07 test:
      .summary          -- {"RECOMMENDATION": "BUY"/"SELL"/"NEUTRAL"/
                             "STRONG_BUY"/"STRONG_SELL", "BUY": n, "SELL": n,
                             "NEUTRAL": n} (vote counts across indicators)
      .oscillators["RECOMMENDATION"] / .moving_averages["RECOMMENDATION"]
                        -- same recommendation breakdown, oscillators-only
                           and moving-averages-only
      .indicators       -- dict of raw indicator values (RSI, Stoch.K, etc.)
                           if you need a specific number rather than the
                           aggregated recommendation
    Raises on an unknown symbol/exchange or if the endpoint is unreachable
    -- callers must handle that, not let one bad symbol kill a whole run.
    """
    handler = TA_Handler(symbol=symbol, exchange=exchange, screener=screener, interval=interval)
    return handler.get_analysis()


def get_ratings(exchange_symbol_pairs, screener="america", interval="1d"):
    """
    Batch version -- one call for multiple symbols, much cheaper than
    looping get_rating(). exchange_symbol_pairs: list of (exchange, symbol)
    tuples, e.g. [("NASDAQ","AAPL"), ("NYSE","F")] -- converted internally
    to TradingView's "EXCHANGE:SYMBOL" batch format. All symbols in one
    call must share the same screener (market) and interval.
    Returns {"EXCHANGE:SYMBOL": Analysis object or None (lookup failed)}.
    """
    symbols = [f"{exch}:{sym}" for exch, sym in exchange_symbol_pairs]
    return get_multiple_analysis(screener=screener, interval=interval, symbols=symbols)


if __name__ == "__main__":
    # quick manual sanity check
    a = get_rating("AAPL", "NASDAQ")
    print("AAPL:", a.summary)
