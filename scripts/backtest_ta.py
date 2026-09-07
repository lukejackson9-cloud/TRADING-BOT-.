"""
Backtests two classic short-term momentum TA setups against Massive.com's
historical whole-market daily data, using CLAUDE.md's existing exit rule
(-4% stop / +8% target / 5-trading-day time-stop) so results are measured
against the rule this project already trades by, not an arbitrary new one.

Setups (both chosen to fit CLAUDE.md's existing "momentum + news catalyst"
style -- momentum-continuation, not mean-reversion):
  - breakout: today's close > the prior 20-trading-day high, AND today's
    volume >= 1.5x the prior 20-day average volume.
  - ema_cross: 9-day EMA crosses above the 21-day EMA (yesterday 9EMA <=
    21EMA, today 9EMA > 21EMA) -- "trend just turned up".

Entry is simulated at the NEXT trading day's open after a signal (the
signal itself is only knowable using data through the signal day's close
-- no lookahead). Exit is whichever of -4% / +8% / 5-trading-days hits
first, checked day by day against each subsequent day's high/low/close.
If a single day's range hits both stop and target, this conservatively
assumes the stop hit first (standard, conservative backtest convention
when intraday sequencing isn't known from daily bars alone) -- a real
limitation of daily-bar backtesting, not a bug; noted in the report.

Universe: get_common_stock_tickers() (~5,300 US common stocks), filtered
to $5-$500 price and >1M volume ON THE SIGNAL DAY -- matching CLAUDE.md's
existing screening filters, so this measures "would this rule have found
tradeable, liquid setups", not a survivorship-biased universe.

CONFIRMED LIVE (2026-09-07): Massive's free tier only serves 2 years of
grouped-daily history -- every date before 2024-09-08 returned 403
Forbidden in a live test (2024-09-08 itself returned OK with
resultsCount 0, i.e. no trading that day; 2023-09-07 and multiple 2024
dates all 403'd). This is a rolling window tied to today's date, not a
fixed date -- don't assume 3 years is available; re-verify the cutoff
live before requesting anything older than ~2 years back.

Two-pass design:
  Pass 1 (fetch_range): pulls get_grouped_daily() day by day, caching each
    day's compact {ticker: [o,h,l,c,v]} to
    data/reference/backtest_cache/{date}.json (gitignored -- regenerable
    infrastructure, not project memory, same category as equity_tickers.json).
    Resumable: already-cached days are skipped, so an interrupted run picks
    up where it left off. Massive's free tier is 5 req/min; this sleeps
    between uncached fetches to stay under that.
  Pass 2 (run_backtest): pure in-memory, no network calls -- walks each
    ticker's cached series chronologically, computes both setups' signals
    with a rolling window, and simulates the exit rule forward using that
    ticker's own already-fetched future days.

Usage:
  python scripts/backtest_ta.py fetch 2023-09-07 2026-09-04
  python scripts/backtest_ta.py backtest 2023-09-07 2026-09-04
"""

import sys
import json
import time
import datetime
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from massive_client import get_grouped_daily, get_common_stock_tickers  # noqa: E402

CACHE_DIR = Path("data/reference/backtest_cache")
PRICE_MIN, PRICE_MAX, VOLUME_MIN = 5, 500, 1_000_000
STOP_PCT, TARGET_PCT, TIME_STOP_DAYS = -0.04, 0.08, 5


def _trading_days(start, end):
    d = datetime.date.fromisoformat(start)
    end_d = datetime.date.fromisoformat(end)
    while d <= end_d:
        if d.weekday() < 5:  # Mon-Fri; holidays handled by empty-result skip below
            yield d.isoformat()
        d += datetime.timedelta(days=1)


def fetch_range(start, end):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    equities = get_common_stock_tickers()
    days = list(_trading_days(start, end))
    fetched = 0
    for date in days:
        cache_file = CACHE_DIR / f"{date}.json"
        if cache_file.exists():
            continue
        data = get_grouped_daily(date)
        if data.get("status") == "OK" and data.get("results"):
            compact = {
                r["T"]: [r["o"], r["h"], r["l"], r["c"], r["v"]]
                for r in data["results"]
                if r["T"] in equities
            }
            cache_file.write_text(json.dumps({"status": "OK", "results": compact}))
            print(f"{date}: cached {len(compact)} tickers")
        else:
            # holiday/weekend/no data -- cache the miss so we don't retry it
            cache_file.write_text(json.dumps({"status": data.get("status", "EMPTY"), "results": {}}))
            print(f"{date}: no data ({data.get('status')}), cached as empty")
        fetched += 1
        time.sleep(13)  # free tier: 5 req/min (sliding window -- space every call, not just every 5th)
    print(f"done: {len(days)} calendar weekdays checked, {fetched} newly fetched")


def _load_series(start, end):
    series = defaultdict(list)  # ticker -> [(date, o,h,l,c,v), ...] chronological
    for date in _trading_days(start, end):
        cache_file = CACHE_DIR / f"{date}.json"
        if not cache_file.exists():
            continue
        data = json.loads(cache_file.read_text())
        for ticker, ohlcv in data["results"].items():
            series[ticker].append((date, *ohlcv))
    return series


def _ema(prev_ema, price, n):
    k = 2 / (n + 1)
    return price * k + prev_ema * (1 - k) if prev_ema is not None else price


def _simulate_exit(bars, entry_idx):
    """bars: full chronological list for one ticker. entry_idx: index of the
    signal day. Enters at bars[entry_idx+1]'s open, exits per the stop/
    target/time-stop rule using subsequent bars. Returns pct_return or None
    if there aren't enough future bars to simulate (still open at data end)."""
    if entry_idx + 1 >= len(bars):
        return None
    entry_price = bars[entry_idx + 1][1]  # open
    stop_price = entry_price * (1 + STOP_PCT)
    target_price = entry_price * (1 + TARGET_PCT)
    for i in range(1, TIME_STOP_DAYS + 1):
        idx = entry_idx + i
        if idx >= len(bars):
            return None  # ran off the end of available data before resolving
        _, o, h, l, c, v = bars[idx]
        if l <= stop_price:
            return STOP_PCT
        if h >= target_price:
            return TARGET_PCT
        if i == TIME_STOP_DAYS:
            return (c - entry_price) / entry_price
    return None


def run_backtest(start, end):
    series = _load_series(start, end)
    results = {"breakout": [], "ema_cross": []}

    for ticker, bars in series.items():
        if len(bars) < 25:
            continue
        ema9 = ema21 = None
        prev_ema9 = prev_ema21 = None
        for i, (date, o, h, l, c, v) in enumerate(bars):
            prev_ema9, prev_ema21 = ema9, ema21
            ema9 = _ema(ema9, c, 9)
            ema21 = _ema(ema21, c, 21)

            if i < 21:
                continue
            if not (PRICE_MIN <= c <= PRICE_MAX) or v < VOLUME_MIN:
                continue

            window = bars[i - 20:i]  # prior 20 days, excludes today
            prior_high = max(b[2] for b in window)
            prior_avg_vol = sum(b[5] for b in window) / 20
            if c > prior_high and v >= 1.5 * prior_avg_vol:
                r = _simulate_exit(bars, i)
                if r is not None:
                    results["breakout"].append({"ticker": ticker, "date": date, "return": r})

            if prev_ema9 is not None and prev_ema21 is not None:
                if prev_ema9 <= prev_ema21 and ema9 > ema21:
                    r = _simulate_exit(bars, i)
                    if r is not None:
                        results["ema_cross"].append({"ticker": ticker, "date": date, "return": r})

    for setup, trades in results.items():
        n = len(trades)
        if n == 0:
            print(f"\n{setup}: 0 trades in range")
            continue
        wins = [t for t in trades if t["return"] > 0]
        win_rate = len(wins) / n * 100
        avg_return = sum(t["return"] for t in trades) / n * 100
        print(f"\n{setup}: {n} trades, win rate {win_rate:.1f}%, avg return/trade {avg_return:.2f}%")

    out_path = CACHE_DIR / f"results_{start}_{end}.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nfull trade list written to {out_path}")


if __name__ == "__main__":
    cmd, start, end = sys.argv[1], sys.argv[2], sys.argv[3]
    if cmd == "fetch":
        fetch_range(start, end)
    elif cmd == "backtest":
        run_backtest(start, end)
    else:
        print("usage: backtest_ta.py [fetch|backtest] START END")
