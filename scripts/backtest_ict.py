"""
Backtests one specific, well-documented ICT ("Inner Circle Trader" / smart
money concepts) day-trading model against Alpaca's real intraday 5-minute
bars: liquidity sweep -> market structure shift (MSS) -> fair value gap
(FVG) entry, during the NY AM killzone.

WHY THIS ONE MODEL: ICT is a large, loosely-standardized body of concepts
(order blocks, breaker blocks, equal highs/lows, optimal trade entry,
multiple killzones, multiple liquidity-pool definitions, etc.) with many
practitioner variants. Implementing "all of ICT" isn't a coherent goal --
this backtests one specific, commonly-taught model precisely enough to
get a real answer, rather than a vague approximation of everything. If
this doesn't show edge, that's evidence against THIS model, not a verdict
on every possible ICT interpretation.

THE MODEL (per symbol, per trading day):
  1. Liquidity pool = previous trading day's regular-session high (PDH)
     and low (PDL) -- the most standard, simplest ICT liquidity
     reference (other variants use session opens, equal highs/lows,
     weekly levels, etc. -- not implemented here).
  2. During the NY AM killzone (9:30-11:00 ET), scan 5-min bars for a
     SWEEP: a bar's high wicks above PDH (or low wicks below PDL) and
     then CLOSES back on the other side of that level within the same
     bar -- a rejection, not a genuine breakout continuation.
  3. Look for a MARKET STRUCTURE SHIFT after the sweep: a subsequent
     bar's close breaks the most recent minor swing low (after a PDH
     sweep, confirming bearish intent) or swing high (after a PDL sweep,
     confirming bullish intent). "Swing low/high" here = the min/max of
     the 6 bars immediately preceding the sweep bar -- a simplified,
     fixed-lookback stand-in for full ICT fractal swing detection.
  4. Find the FAIR VALUE GAP left by the MSS's impulse move: any 3
     consecutive bars in the model's direction where bar[i-1]'s high is
     below bar[i+1]'s low (bullish FVG) or bar[i-1]'s low is above
     bar[i+1]'s high (bearish FVG), searched in the bars from the sweep
     through the MSS confirmation.
  5. ENTRY: the first subsequent bar whose range touches back into that
     FVG zone (a retracement fill), at the FVG's midpoint.
  6. STOP: beyond the sweep bar's extreme (the wick that swept PDH/PDL).
  7. TARGET: 2x the stop distance (fixed 1:2 R:R -- a simplification;
     real ICT practice often targets the opposing liquidity pool
     instead, which would need per-trade case-by-case sizing).
  8. TIME-STOP: exit at that day's regular-session close (16:00 ET) if
     neither stop nor target is hit -- ICT day-trading setups are
     intraday, not held overnight, unlike the swing setups in
     backtest_ta.py.

UNIVERSE: a fixed list of ~30 large-cap, high-volume US equities (see
UNIVERSE below) -- NOT a whole-market screen like backtest_ta.py's.
Multi-year 5-minute bars across the full market would be an impractical
amount of data/calls even at Alpaca's generous 200 req/min free-tier
limit, and ICT concepts are traditionally applied to liquid, heavily-
traded names (or futures/FX) where institutional order flow is
meaningful -- not thin small-caps.

DATA DEPTH: Alpaca's free/IEX tier serves real intraday history back to
~mid-2021 (confirmed live 2026-09-07 -- 2020-06 and earlier returned 0
bars on a confirmed weekday, 2021-06 onward returned real data), roughly
5 years as of now -- more than backtest_ta.py's 2-year Massive.com limit.

Two-pass design, same shape as backtest_ta.py:
  fetch: pulls scripts/alpaca_client.py's get_historical_bars() per
    symbol, caches each to data/reference/backtest_ict_cache/{symbol}.json
    (gitignored, regenerable). Resumable -- already-cached symbols are
    skipped.
  backtest: pure in-memory, walks each symbol's cached 5-min bars day by
    day, running the model above.

Usage:
  python scripts/backtest_ict.py fetch 2021-06-01 2026-09-04
  python scripts/backtest_ict.py backtest 2021-06-01 2026-09-04
"""

import sys
import json
import datetime
from pathlib import Path
from collections import defaultdict
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))
from alpaca_client import get_historical_bars  # noqa: E402

CACHE_DIR = Path("data/reference/backtest_ict_cache")
NY = ZoneInfo("America/New_York")

# Large-cap, high-volume names across sectors -- see module docstring for why
# this fixed list instead of a whole-market screen.
UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "JPM", "V",
    "UNH", "XOM", "JNJ", "WMT", "PG", "HD", "MA", "BAC", "DIS", "ADBE",
    "CRM", "NFLX", "AMD", "INTC", "KO", "PEP", "COST", "MRK", "ABBV",
    "CVX", "ORCL",
]

KILLZONE_START, KILLZONE_END = datetime.time(9, 30), datetime.time(11, 0)
SESSION_CLOSE = datetime.time(16, 0)
SWING_LOOKBACK = 6


def fetch_universe(start, end):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for symbol in UNIVERSE:
        cache_file = CACHE_DIR / f"{symbol}.json"
        if cache_file.exists():
            print(f"{symbol}: already cached, skipping")
            continue
        bars = get_historical_bars(symbol, f"{start}T00:00:00Z", f"{end}T23:59:59Z")
        cache_file.write_text(json.dumps(bars))
        print(f"{symbol}: cached {len(bars)} bars")


def _load_days(symbol):
    """Returns {date_str: [bar, ...]} -- bars grouped by NY-local trading
    date, each bar annotated with its NY-local time for session logic."""
    cache_file = CACHE_DIR / f"{symbol}.json"
    if not cache_file.exists():
        return {}
    bars = json.loads(cache_file.read_text())
    days = defaultdict(list)
    for b in bars:
        ts = datetime.datetime.fromisoformat(b["t"].replace("Z", "+00:00")).astimezone(NY)
        b["_ny_time"] = ts.time()
        days[ts.date().isoformat()].append(b)
    return days


def _find_fvg(bars, lo, hi, direction):
    """Searches bars[lo:hi] for a 3-bar fair value gap in `direction`
    ("bullish" or "bearish"). Returns (gap_low, gap_high) of the first one
    found, or None."""
    for i in range(lo + 1, hi - 1):
        b1, b3 = bars[i - 1], bars[i + 1]
        if direction == "bullish" and b1["h"] < b3["l"]:
            return b1["h"], b3["l"]
        if direction == "bearish" and b1["l"] > b3["h"]:
            return b3["h"], b1["l"]
    return None


def _simulate_day(killzone_bars, pdh, pdl, all_day_bars, kz_start_idx):
    """Runs the sweep -> MSS -> FVG model against one day's killzone bars.
    Returns a trade dict or None. all_day_bars/kz_start_idx let the target/
    stop simulation continue past 11:00 using the rest of the day's bars."""
    for k in range(len(killzone_bars)):
        bar = killzone_bars[k]
        swept_high = bar["h"] > pdh and bar["c"] < pdh
        swept_low = bar["l"] < pdl and bar["c"] > pdl
        if not (swept_high or swept_low):
            continue

        direction = "bearish" if swept_high else "bullish"
        sweep_extreme = bar["h"] if swept_high else bar["l"]

        lookback_start = max(0, k - SWING_LOOKBACK)
        swing_bars = killzone_bars[lookback_start:k]
        if not swing_bars:
            continue
        swing_level = min(b["l"] for b in swing_bars) if direction == "bearish" else max(b["h"] for b in swing_bars)

        mss_idx = None
        for m in range(k + 1, len(killzone_bars)):
            if direction == "bearish" and killzone_bars[m]["c"] < swing_level:
                mss_idx = m
                break
            if direction == "bullish" and killzone_bars[m]["c"] > swing_level:
                mss_idx = m
                break
        if mss_idx is None:
            continue

        fvg = _find_fvg(killzone_bars, k, mss_idx + 1, direction)
        if fvg is None:
            continue
        gap_low, gap_high = fvg
        entry_price = (gap_low + gap_high) / 2

        entry_idx = None
        for e in range(mss_idx + 1, len(killzone_bars)):
            if killzone_bars[e]["l"] <= entry_price <= killzone_bars[e]["h"]:
                entry_idx = e
                break
        if entry_idx is None:
            continue

        risk = abs(entry_price - sweep_extreme)
        if risk <= 0:
            continue
        stop_price = sweep_extreme
        target_price = entry_price + (2 * risk if direction == "bullish" else -2 * risk)

        global_entry_idx = kz_start_idx + entry_idx
        for f in range(global_entry_idx + 1, len(all_day_bars)):
            fb = all_day_bars[f]
            if fb["_ny_time"] > SESSION_CLOSE:
                break
            if direction == "bullish":
                if fb["l"] <= stop_price:
                    return {"return_r": -1.0, "direction": direction}
                if fb["h"] >= target_price:
                    return {"return_r": 2.0, "direction": direction}
            else:
                if fb["h"] >= stop_price:
                    return {"return_r": -1.0, "direction": direction}
                if fb["l"] <= target_price:
                    return {"return_r": 2.0, "direction": direction}
        # time-stop: exit at last available bar's close
        last_close = all_day_bars[min(global_entry_idx + 1, len(all_day_bars) - 1)]["c"]
        pct = (last_close - entry_price) / risk if direction == "bullish" else (entry_price - last_close) / risk
        return {"return_r": pct, "direction": direction}
    return None


def run_backtest(start, end):
    all_trades = []
    for symbol in UNIVERSE:
        days = _load_days(symbol)
        sorted_dates = sorted(days.keys())
        for i in range(1, len(sorted_dates)):
            date, prev_date = sorted_dates[i], sorted_dates[i - 1]
            if not (start <= date <= end):
                continue
            prev_bars = days[prev_date]
            regular = [b for b in prev_bars if datetime.time(9, 30) <= b["_ny_time"] <= SESSION_CLOSE]
            if not regular:
                continue
            pdh, pdl = max(b["h"] for b in regular), min(b["l"] for b in regular)

            day_bars = sorted(days[date], key=lambda b: b["_ny_time"])
            kz = [b for b in day_bars if KILLZONE_START <= b["_ny_time"] <= KILLZONE_END]
            if not kz:
                continue
            kz_start_idx = next((idx for idx, b in enumerate(day_bars) if b["_ny_time"] >= KILLZONE_START), None)
            if kz_start_idx is None:
                continue

            trade = _simulate_day(kz, pdh, pdl, day_bars, kz_start_idx)
            if trade:
                trade.update(symbol=symbol, date=date)
                all_trades.append(trade)

    n = len(all_trades)
    if n == 0:
        print("0 trades in range")
        return
    wins = [t for t in all_trades if t["return_r"] > 0]
    win_rate = len(wins) / n * 100
    avg_r = sum(t["return_r"] for t in all_trades) / n
    print(f"ICT sweep+MSS+FVG model: {n} trades, win rate {win_rate:.1f}%, avg {avg_r:.2f}R/trade")

    out_path = CACHE_DIR / f"results_{start}_{end}.json"
    out_path.write_text(json.dumps(all_trades, indent=2))
    print(f"full trade list written to {out_path}")


if __name__ == "__main__":
    cmd, start, end = sys.argv[1], sys.argv[2], sys.argv[3]
    if cmd == "fetch":
        fetch_universe(start, end)
    elif cmd == "backtest":
        run_backtest(start, end)
    else:
        print("usage: backtest_ict.py [fetch|backtest] START END")
