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

# FOMC decision-day dates (the 2nd day of each 2-day meeting, when the 2pm ET
# announcement happens), verified via WebSearch against Federal Reserve
# schedule announcements -- NOT computed/guessed. Covers 2021-06 through
# 2026-09 (this script's backtest range). CPI dates were also researched but
# could not be reliably compiled into a complete, verified multi-year list
# in this session (BLS's own schedule pages are blocked by this
# environment's network egress policy, and WebSearch only surfaced scattered
# sample dates, not a full verified set) -- deliberately excluded rather
# than guess-filled, per this project's non-negotiable rule against
# fabricating research. NFP is not listed here since it's a fixed calendar
# rule (see _is_nfp_day) needing no external source.
FOMC_DATES = {
    "2021-06-16", "2021-07-28", "2021-09-22", "2021-11-03", "2021-12-15",
    "2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15", "2022-07-27",
    "2022-09-21", "2022-11-02", "2022-12-14",
    "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26",
    "2023-09-20", "2023-11-01", "2023-12-13",
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31",
    "2024-09-18", "2024-11-07", "2024-12-18",
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30",
    "2025-09-17", "2025-10-29", "2025-12-10",
    "2026-01-28", "2026-03-18",
}


def _is_nfp_day(date_str):
    """NFP releases at 8:30am ET on the first Friday of each month (the one
    fixed, no-exceptions-in-this-window rule among the "big three" releases
    -- unlike FOMC/CPI, this needs no external source to get right)."""
    d = datetime.date.fromisoformat(date_str)
    if d.weekday() != 4:  # Friday
        return False
    return d.day <= 7


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


def _compute_rsi(bars, period=14):
    """Wilder's RSI, computed over `bars` in chronological order. Annotates
    each bar dict in place with `_rsi` (None for the warmup period before
    `period` closes are available)."""
    for b in bars:
        b["_rsi"] = None
    if len(bars) <= period:
        return
    gains, losses = [], []
    for i in range(1, len(bars)):
        change = bars[i]["c"] - bars[i - 1]["c"]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    bars[period]["_rsi"] = 100.0 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rsi = 100.0 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))
        bars[i + 1]["_rsi"] = rsi


def _load_days(symbol):
    """Returns {date_str: [bar, ...]} -- bars grouped by NY-local trading
    date, each bar annotated with its NY-local time for session logic and
    its RSI(14) computed over the full chronological series (so early-day
    bars still get a real value using the prior session's tail, not reset
    to a fresh warmup every day)."""
    cache_file = CACHE_DIR / f"{symbol}.json"
    if not cache_file.exists():
        return {}
    bars = json.loads(cache_file.read_text())
    for b in bars:
        ts = datetime.datetime.fromisoformat(b["t"].replace("Z", "+00:00")).astimezone(NY)
        b["_ny_time"] = ts.time()
        b["_ts"] = ts
    bars.sort(key=lambda b: b["_ts"])
    _compute_rsi(bars)
    days = defaultdict(list)
    for b in bars:
        days[b["_ts"].date().isoformat()].append(b)
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


def _find_order_block_zone(bars, lo, hi, direction):
    """Order block: the last candle of the OPPOSITE color to the impulse,
    immediately before that impulse, in bars[lo:hi] -- the classic ICT
    "last down candle before the up move" (and mirror for bearish). Returns
    (low, high) of that candle's full range, or None if no opposite-color
    candle exists in the window."""
    opposite_is_red = direction == "bullish"  # bullish impulse -> look for a red (down) candle
    for i in range(hi - 1, lo - 1, -1):
        b = bars[i]
        is_red = b["c"] < b["o"]
        if is_red == opposite_is_red:
            return b["l"], b["h"]
    return None


def _find_ote_zone(bars, lo, hi, direction):
    """Optimal Trade Entry: the 62%-79% Fibonacci retracement zone of the
    impulse leg spanning bars[lo:hi] (leg_low/leg_high = the extremes
    reached across that window). Returns (zone_low, zone_high), or None if
    the leg has zero range."""
    leg_low = min(b["l"] for b in bars[lo:hi])
    leg_high = max(b["h"] for b in bars[lo:hi])
    rng = leg_high - leg_low
    if rng <= 0:
        return None
    if direction == "bullish":
        return leg_high - 0.79 * rng, leg_high - 0.62 * rng
    else:
        return leg_low + 0.62 * rng, leg_low + 0.79 * rng


def _find_equal_levels(extremes, tolerance=0.0015):
    """Given a list of (date, price) extremes (e.g. each of the last N
    days' regular-session highs, or lows), finds the first pair within
    `tolerance` (relative) of each other and returns their average as the
    "equal highs/lows" liquidity level. Returns None if no pair is close
    enough -- genuinely equal levels are the point, not just "the max of
    the lookback window" relabeled."""
    for i in range(len(extremes)):
        for j in range(i + 1, len(extremes)):
            p1, p2 = extremes[i][1], extremes[j][1]
            if abs(p1 - p2) / max(p1, p2) <= tolerance:
                return (p1 + p2) / 2
    return None


def _has_divergence(bar, direction, swing_bars):
    """Bias/divergence filter: does the sweep bar's RSI fail to confirm its
    own price extreme against the most extreme prior swing bar? A bearish
    sweep (new/equal high) with WEAKER RSI than the prior swing high is
    bearish divergence (momentum fading into the sweep, not confirming it)
    -- and the mirror for a bullish sweep -- treated as confirming bias for
    the reversal this model is already betting on. Requires both bars to
    have a real RSI (past the warmup period); returns False (no filter
    pass) if either is missing rather than guessing."""
    if bar["_rsi"] is None:
        return False
    if direction == "bearish":
        ref = max(swing_bars, key=lambda b: b["h"])
        if ref["_rsi"] is None:
            return False
        return bar["h"] >= ref["h"] and bar["_rsi"] < ref["_rsi"]
    else:
        ref = min(swing_bars, key=lambda b: b["l"])
        if ref["_rsi"] is None:
            return False
        return bar["l"] <= ref["l"] and bar["_rsi"] > ref["_rsi"]


def _simulate_day(killzone_bars, pdh, pdl, all_day_bars, kz_start_idx, require_divergence=False, entry_mode="fvg"):
    """Runs the sweep -> MSS -> {FVG,order_block,OTE} model against one
    day's killzone bars. Returns a trade dict or None. all_day_bars/
    kz_start_idx let the target/stop simulation continue past 11:00 using
    the rest of the day's bars.
    require_divergence=True adds an RSI-divergence bias filter at the
    sweep bar (see _has_divergence) -- a cheap sanity test of whether a
    momentum-confirmation filter closes the near-miss gap in the baseline
    model's win rate, using bars already cached, no new data fetch.
    entry_mode selects the zone the model waits for a retracement into:
    "fvg" (baseline), "order_block", or "ote" -- isolates the effect of
    changing ONLY the entry-zone definition, keeping sweep/MSS/stop/target
    logic identical across all three so results are directly comparable."""
    if pdh is None or pdl is None:
        return None
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

        if require_divergence and not _has_divergence(bar, direction, swing_bars):
            continue

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

        if entry_mode == "order_block":
            zone = _find_order_block_zone(killzone_bars, k, mss_idx + 1, direction)
        elif entry_mode == "ote":
            zone = _find_ote_zone(killzone_bars, k, mss_idx + 1, direction)
        else:
            zone = _find_fvg(killzone_bars, k, mss_idx + 1, direction)
        if zone is None:
            continue
        gap_low, gap_high = zone
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


def _report(all_trades, label, start, end, suffix):
    n = len(all_trades)
    if n == 0:
        print(f"{label}: 0 trades in range")
        return
    wins = [t for t in all_trades if t["return_r"] > 0]
    win_rate = len(wins) / n * 100
    avg_r = sum(t["return_r"] for t in all_trades) / n
    print(f"{label}: {n} trades, win rate {win_rate:.1f}%, avg {avg_r:.2f}R/trade")
    out_path = CACHE_DIR / f"results_{start}_{end}{suffix}.json"
    out_path.write_text(json.dumps(all_trades, indent=2))
    print(f"full trade list written to {out_path}")


def run_backtest(start, end, require_divergence=False, entry_mode="fvg", killzone=None):
    kz_start, kz_end = killzone or (KILLZONE_START, KILLZONE_END)
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
            kz = [b for b in day_bars if kz_start <= b["_ny_time"] <= kz_end]
            if not kz:
                continue
            kz_start_idx = next((idx for idx, b in enumerate(day_bars) if b["_ny_time"] >= kz_start), None)
            if kz_start_idx is None:
                continue

            trade = _simulate_day(kz, pdh, pdl, day_bars, kz_start_idx,
                                   require_divergence=require_divergence, entry_mode=entry_mode)
            if trade:
                trade.update(symbol=symbol, date=date)
                all_trades.append(trade)

    if killzone is not None:
        label, suffix = "ICT sweep+MSS+FVG model (NY PM killzone)", "_nypm"
    elif require_divergence:
        label, suffix = "ICT sweep+MSS+FVG+divergence-bias model", "_divergence"
    elif entry_mode == "order_block":
        label, suffix = "ICT sweep+MSS+order-block-entry model", "_orderblock"
    elif entry_mode == "ote":
        label, suffix = "ICT sweep+MSS+OTE-entry model", "_ote"
    else:
        label, suffix = "ICT sweep+MSS+FVG model", ""
    _report(all_trades, label, start, end, suffix)


def _simulate_day_inverse_fvg(killzone_bars, pdh, pdl, all_day_bars, kz_start_idx):
    """Inverse FVG variant: same sweep -> MSS -> FVG detection as the
    baseline, but instead of entering on the FIRST retracement into the
    gap, watches for the gap to be VIOLATED first (a later bar closes back
    through it, meaning the original impulse failed) and then trades the
    REVERSAL -- entering on a retracement back into that same zone, now
    acting as resistance/support in the opposite direction. This is a
    materially different mechanism from the baseline's "gap holds, trade
    the continuation" bet -- it's "gap fails, trade the flip.\""""
    if pdh is None or pdl is None:
        return None
    for k in range(len(killzone_bars)):
        bar = killzone_bars[k]
        swept_high = bar["h"] > pdh and bar["c"] < pdh
        swept_low = bar["l"] < pdl and bar["c"] > pdl
        if not (swept_high or swept_low):
            continue

        direction = "bearish" if swept_high else "bullish"

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

        # Watch for violation: a bar closing back through the gap against
        # the original direction, after the MSS confirmation.
        violation_idx = None
        for v in range(mss_idx + 1, len(killzone_bars)):
            vb = killzone_bars[v]
            if direction == "bullish" and vb["c"] < gap_low:
                violation_idx = v
                break
            if direction == "bearish" and vb["c"] > gap_high:
                violation_idx = v
                break
        if violation_idx is None:
            continue

        new_direction = "bearish" if direction == "bullish" else "bullish"
        # New stop reference: the most extreme price reached in the
        # ORIGINAL direction between the MSS and the violation -- the high
        # (for a failed bullish move) or low (for a failed bearish move)
        # that the reversal needs to invalidate to prove itself wrong.
        pre_violation = killzone_bars[mss_idx:violation_idx + 1]
        new_stop = max(b["h"] for b in pre_violation) if new_direction == "bearish" else min(b["l"] for b in pre_violation)

        entry_price = (gap_low + gap_high) / 2
        entry_idx = None
        for e in range(violation_idx + 1, len(killzone_bars)):
            if killzone_bars[e]["l"] <= entry_price <= killzone_bars[e]["h"]:
                entry_idx = e
                break
        if entry_idx is None:
            continue

        risk = abs(entry_price - new_stop)
        if risk <= 0:
            continue
        target_price = entry_price + (2 * risk if new_direction == "bullish" else -2 * risk)

        global_entry_idx = kz_start_idx + entry_idx
        for f in range(global_entry_idx + 1, len(all_day_bars)):
            fb = all_day_bars[f]
            if fb["_ny_time"] > SESSION_CLOSE:
                break
            if new_direction == "bullish":
                if fb["l"] <= new_stop:
                    return {"return_r": -1.0, "direction": new_direction}
                if fb["h"] >= target_price:
                    return {"return_r": 2.0, "direction": new_direction}
            else:
                if fb["h"] >= new_stop:
                    return {"return_r": -1.0, "direction": new_direction}
                if fb["l"] <= target_price:
                    return {"return_r": 2.0, "direction": new_direction}
        last_close = all_day_bars[min(global_entry_idx + 1, len(all_day_bars) - 1)]["c"]
        pct = (last_close - entry_price) / risk if new_direction == "bullish" else (entry_price - last_close) / risk
        return {"return_r": pct, "direction": new_direction}
    return None


def run_backtest_inverse_fvg(start, end):
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
            trade = _simulate_day_inverse_fvg(kz, pdh, pdl, day_bars, kz_start_idx)
            if trade:
                trade.update(symbol=symbol, date=date)
                all_trades.append(trade)
    _report(all_trades, "ICT sweep+MSS+inverse-FVG model", start, end, "_inversefvg")


def run_backtest_eqhl(start, end, lookback_days=5, tolerance=0.0015):
    """Same sweep -> MSS -> FVG model as the baseline, but the liquidity
    pool is genuine equal highs/equal lows over the trailing `lookback_days`
    regular sessions (two closes within `tolerance` of each other) instead
    of always using the prior day's high/low. Isolates the effect of the
    liquidity-pool DEFINITION, keeping entry/stop/target logic identical to
    baseline. A day with no qualifying equal-high or equal-low cluster has
    no pool on that side -- skipped, not silently replaced with PDH/PDL."""
    all_trades = []
    for symbol in UNIVERSE:
        days = _load_days(symbol)
        sorted_dates = sorted(days.keys())
        session_extremes = {}
        for d in sorted_dates:
            regular = [b for b in days[d] if datetime.time(9, 30) <= b["_ny_time"] <= SESSION_CLOSE]
            if regular:
                session_extremes[d] = (max(b["h"] for b in regular), min(b["l"] for b in regular))

        for i in range(lookback_days, len(sorted_dates)):
            date = sorted_dates[i]
            if not (start <= date <= end):
                continue
            window_dates = [sorted_dates[i - n] for n in range(1, lookback_days + 1) if sorted_dates[i - n] in session_extremes]
            highs = [(d, session_extremes[d][0]) for d in window_dates]
            lows = [(d, session_extremes[d][1]) for d in window_dates]
            pdh = _find_equal_levels(highs, tolerance)
            pdl = _find_equal_levels(lows, tolerance)
            if pdh is None and pdl is None:
                continue

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
    _report(all_trades, "ICT sweep(EQH/EQL)+MSS+FVG model", start, end, "_eqhl")


def run_backtest_newsfilter(start, end, mode):
    """Same baseline sweep+MSS+FVG model, but restricted by news-day status.
    mode="exclude": skip NFP/FOMC days entirely (the "avoid news noise"
    theory). mode="only": trade ONLY on NFP/FOMC days (the "news creates
    the real institutional liquidity sweep" theory). Isolates this one
    variable -- entry/stop/target logic is identical to baseline."""
    all_trades = []
    for symbol in UNIVERSE:
        days = _load_days(symbol)
        sorted_dates = sorted(days.keys())
        for i in range(1, len(sorted_dates)):
            date, prev_date = sorted_dates[i], sorted_dates[i - 1]
            if not (start <= date <= end):
                continue
            is_news_day = date in FOMC_DATES or _is_nfp_day(date)
            if mode == "exclude" and is_news_day:
                continue
            if mode == "only" and not is_news_day:
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

    label = f"ICT sweep+MSS+FVG model (news-{mode}: NFP+FOMC days)"
    suffix = f"_news{mode}"
    _report(all_trades, label, start, end, suffix)


if __name__ == "__main__":
    cmd, start, end = sys.argv[1], sys.argv[2], sys.argv[3]
    if cmd == "fetch":
        fetch_universe(start, end)
    elif cmd == "backtest":
        run_backtest(start, end)
    elif cmd == "backtest_divergence":
        run_backtest(start, end, require_divergence=True)
    elif cmd == "backtest_orderblock":
        run_backtest(start, end, entry_mode="order_block")
    elif cmd == "backtest_ote":
        run_backtest(start, end, entry_mode="ote")
    elif cmd == "backtest_inversefvg":
        run_backtest_inverse_fvg(start, end)
    elif cmd == "backtest_eqhl":
        run_backtest_eqhl(start, end)
    elif cmd == "backtest_newsexclude":
        run_backtest_newsfilter(start, end, mode="exclude")
    elif cmd == "backtest_newsonly":
        run_backtest_newsfilter(start, end, mode="only")
    elif cmd == "backtest_nypm":
        run_backtest(start, end, killzone=(datetime.time(13, 30), datetime.time(16, 0)))
    else:
        print("usage: backtest_ict.py [fetch|backtest|backtest_divergence|"
              "backtest_orderblock|backtest_ote|backtest_inversefvg|backtest_eqhl|"
              "backtest_newsexclude|backtest_newsonly] START END")
