"""
Tests whether MULTIPLE mechanical signals agreeing produces a real edge
beyond any single signal alone -- scoped 2026-09-11 per the user's point
that real traders synthesize several signals rather than relying on one
strategy in isolation, and every setup tested individually so far
(5 TA setups, 12 ICT variants -- see CLAUDE.md) has come back flat or
negative alone.

Three tests, all reusing ALREADY-CACHED data -- no new API calls:
  Test 1 -- TA setup agreement: does a ticker firing >=2 of
    backtest_ta.py's 5 setups on the SAME signal day beat firing just 1?
    Full market universe, full 2020-08-05..2026-09-04 window already
    cached in data/reference/backtest_cache/.
  Test 2 -- TA + macro-calendar proximity: do TA signals landing on a
    real FOMC/NFP/CPI day (reusing backtest_ict.py's verified date sets)
    behave differently than ones that don't? Same universe/window as
    Test 1 -- this is the same question backtest_ict.py already asked for
    the ICT model, just not yet asked for the TA setups.
  Test 3 -- TA + ICT same-symbol/same-day overlap: restricted to
    backtest_ict.py's 30-symbol universe (the only place both signal
    types exist) -- does a daily TA signal land on a day the ICT model
    ALSO fired a trade (any of its 6 tracked mechanisms) do better than a
    TA signal on a day it didn't? Reuses the already-cached ICT
    trade-result JSON files rather than recomputing the ICT model itself.

IMPORTANT CAVEAT (see lessons.md #1): this only tests MECHANICAL signal
agreement (TA x TA, TA x macro-calendar, TA x ICT). It does NOT test
"TA + a real news catalyst" -- the 2026-09-07 attempt to proxy a catalyst
with an overnight price gap made results WORSE, because by the time a gap
exists the reaction has already fired. A genuine catalyst-confluence
dimension needs a forward-only paper-trade track (tagging real dated news
as it happens, the way research.md already does), not a historical
backtest built on a price-derived proxy -- see HANDOFF.md 2026-09-11.

Success criteria, fixed BEFORE running (same discipline as every other
backtest in this project -- see the vcp_breakout 2yr/6yr reversal and the
OTE/NVDA concentration catch in CLAUDE.md):
  - net positive avg return/trade after the existing realistic exit rule
  - a genuine uplift over the relevant solo baseline, not just "positive"
  - no single ticker driving more than ~35% of total positive return
  - holds up in BOTH halves of the window, not just one
  - at least ~50 trades before drawing any conclusion at all
None of these are relaxed after seeing results.

Usage:
  python scripts/backtest_confluence.py test1 2020-08-05 2026-09-04
  python scripts/backtest_confluence.py test2 2020-08-05 2026-09-04
  python scripts/backtest_confluence.py test3
  python scripts/backtest_confluence.py all 2020-08-05 2026-09-04
"""

import sys
import json
import datetime
from pathlib import Path
from collections import defaultdict, Counter

sys.path.insert(0, str(Path(__file__).parent))
from backtest_ta import _load_series, _spy_closes, iter_signals, _simulate_exit  # noqa: E402
from backtest_ict import (  # noqa: E402
    UNIVERSE as ICT_UNIVERSE, FOMC_DATES, CPI_DATES, _is_nfp_day,
    CACHE_DIR as ICT_CACHE_DIR,
)

OUT_DIR = Path("data/reference/backtest_confluence")
ALL_TA_SETUPS = ("breakout", "ema_cross", "mean_reversion", "vcp_breakout", "relative_strength")

# Cached ICT backtest result files were generated for exactly this range
# (see data/reference/backtest_ict_cache/) -- Test 3 uses that range
# regardless of what's passed on the command line, since it's reading
# already-computed trades, not resimulating anything.
ICT_RESULT_RANGE = ("2021-06-01", "2026-09-04")
ICT_RESULT_SUFFIXES = ["", "_orderblock", "_ote", "_inversefvg", "_eqhl", "_nypm"]


def _midpoint_date(start, end):
    d0, d1 = datetime.date.fromisoformat(start), datetime.date.fromisoformat(end)
    return (d0 + (d1 - d0) / 2).isoformat()


def _report_group(label, trades, mid_date):
    n = len(trades)
    if n == 0:
        print(f"  {label}: 0 trades")
        return
    wins = [t for t in trades if t["return"] > 0]
    win_rate = len(wins) / n * 100
    avg = sum(t["return"] for t in trades) / n * 100
    print(f"  {label}: {n} trades, win rate {win_rate:.1f}%, avg {avg:.2f}%/trade")
    for half_label, half in (
        ("first half", [t for t in trades if t["date"] < mid_date]),
        ("second half", [t for t in trades if t["date"] >= mid_date]),
    ):
        if not half:
            print(f"      {half_label}: 0 trades")
            continue
        hn = len(half)
        havg = sum(t["return"] for t in half) / hn * 100
        hwr = sum(1 for t in half if t["return"] > 0) / hn * 100
        print(f"      {half_label}: {hn} trades, {hwr:.1f}% win, {havg:.2f}%/trade")


def _concentration_report(trades):
    if not trades:
        print("  concentration check: n/a (0 trades)")
        return
    total_positive = sum(t["return"] for t in trades if t["return"] > 0)
    if total_positive <= 0:
        print("  concentration check: n/a (no net positive contribution to check)")
        return
    by_ticker = defaultdict(float)
    for t in trades:
        if t["return"] > 0:
            by_ticker[t["ticker"]] += t["return"]
    top_ticker, top_val = max(by_ticker.items(), key=lambda kv: kv[1])
    share = top_val / total_positive * 100
    flag = " <-- CONCENTRATION WARNING (>35%)" if share > 35 else ""
    print(f"  concentration check: top contributor {top_ticker} = {share:.1f}% of total positive return{flag}")


def _save(data, name):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{name}.json"
    out.write_text(json.dumps(data, indent=2))
    print(f"  saved: {out}")


def test1_setup_agreement(start, end):
    """Does a ticker firing >=2 of the 5 TA setups on the SAME signal day
    (same ticker, same bar) beat firing just 1? vcp_breakout is a STRICT
    SUBSET of breakout by construction (it can only fire where breakout's
    own trigger is already true -- see iter_signals), so a bare
    {breakout, vcp_breakout} pair is not independent agreement and is
    collapsed to solo "breakout" rather than counted as confluence."""
    print(f"=== TEST 1: TA setup agreement, {start}..{end} ===")
    series = _load_series(start, end)
    spy_closes = _spy_closes(start, end)
    mid = _midpoint_date(start, end)

    solo_trades, confluence_trades = [], []
    combo_counter = Counter()

    for ticker, bars in series.items():
        if len(bars) < 25:
            continue
        by_i = defaultdict(set)
        for i, date, setup in iter_signals(bars, spy_closes=spy_closes):
            by_i[i].add(setup)
        for i, setups in by_i.items():
            effective = set(setups)
            if effective == {"breakout", "vcp_breakout"}:
                effective = {"breakout"}
            r = _simulate_exit(bars, i)
            if r is None:
                continue
            date = bars[i][0]
            if len(effective) >= 2:
                combo = frozenset(effective)
                combo_counter[combo] += 1
                confluence_trades.append({"ticker": ticker, "date": date, "return": r, "combo": sorted(combo)})
            elif len(effective) == 1:
                solo_trades.append({"ticker": ticker, "date": date, "return": r, "setup": next(iter(effective))})

    _report_group("SOLO (exactly 1 independent setup fires)", solo_trades, mid)
    _report_group("CONFLUENCE (>=2 independent setups agree)", confluence_trades, mid)
    print("\n  Combo breakdown:")
    for combo, n in combo_counter.most_common():
        combo_trades = [t for t in confluence_trades if frozenset(t["combo"]) == combo]
        avg = sum(t["return"] for t in combo_trades) / len(combo_trades) * 100
        wr = sum(1 for t in combo_trades if t["return"] > 0) / len(combo_trades) * 100
        print(f"    {'+'.join(sorted(combo))}: {n} trades, {wr:.1f}% win, {avg:.2f}%/trade")
    _concentration_report(confluence_trades)
    _save(solo_trades, "test1_solo")
    _save(confluence_trades, "test1_confluence")


def _is_news_day(date):
    return date in FOMC_DATES or date in CPI_DATES or _is_nfp_day(date)


def test2_macro_proximity(start, end):
    """Do TA signals landing on a verified FOMC/NFP/CPI day behave
    differently than ones that don't? Note: FOMC_DATES only covers
    through 2026-03-18 and CPI_DATES through 2026-08-12 (this project's
    verified-date sets, sourced via WebSearch/FRED for backtest_ict.py) --
    the small stretch of this window past those dates simply has no news
    days flagged, a minor undercount near the end of the range, not a bug."""
    print(f"=== TEST 2: TA + macro-calendar proximity, {start}..{end} ===")
    series = _load_series(start, end)
    spy_closes = _spy_closes(start, end)
    mid = _midpoint_date(start, end)

    news = defaultdict(list)
    nonews = defaultdict(list)
    for ticker, bars in series.items():
        if len(bars) < 25:
            continue
        for i, date, setup in iter_signals(bars, spy_closes=spy_closes):
            r = _simulate_exit(bars, i)
            if r is None:
                continue
            record = {"ticker": ticker, "date": date, "return": r}
            (news if _is_news_day(date) else nonews)[setup].append(record)

    for setup in ALL_TA_SETUPS:
        print(f"\n  --- {setup} ---")
        _report_group("NEWS DAY (FOMC/NFP/CPI)", news[setup], mid)
        _report_group("NON-NEWS DAY", nonews[setup], mid)
    _save({s: news[s] for s in ALL_TA_SETUPS}, "test2_news_days")
    _save({s: nonews[s] for s in ALL_TA_SETUPS}, "test2_nonnews_days")


def _load_ict_signal_days():
    ict_start, ict_end = ICT_RESULT_RANGE
    signal_days = set()
    for suffix in ICT_RESULT_SUFFIXES:
        path = ICT_CACHE_DIR / f"results_{ict_start}_{ict_end}{suffix}.json"
        if not path.exists():
            print(f"  (missing {path}, skipping)")
            continue
        for t in json.loads(path.read_text()):
            signal_days.add((t["symbol"], t["date"]))
    return signal_days


def test3_ta_ict_overlap():
    """Restricted to the 30-symbol ICT universe -- the only place both
    signal types exist. Uses the ALREADY-CACHED ICT backtest result files
    (baseline + order_block + ote + inverse_fvg + eqhl + nypm) to build
    the set of (symbol, date) days the ICT model fired ANY trade on,
    rather than recomputing the ICT model here."""
    ict_start, ict_end = ICT_RESULT_RANGE
    print(f"=== TEST 3: TA + ICT same-symbol/day overlap, {ict_start}..{ict_end} "
          f"({len(ICT_UNIVERSE)}-symbol ICT universe only) ===")
    signal_days = _load_ict_signal_days()
    print(f"  {len(signal_days)} (symbol, date) ICT-signal-days loaded from cached results")

    series = _load_series(ict_start, ict_end)
    spy_closes = _spy_closes(ict_start, ict_end)
    mid = _midpoint_date(ict_start, ict_end)

    overlap, non_overlap = [], []
    for ticker in ICT_UNIVERSE:
        bars = series.get(ticker)
        if not bars or len(bars) < 25:
            continue
        for i, date, setup in iter_signals(bars, spy_closes=spy_closes):
            r = _simulate_exit(bars, i)
            if r is None:
                continue
            record = {"ticker": ticker, "date": date, "setup": setup, "return": r}
            (overlap if (ticker, date) in signal_days else non_overlap).append(record)

    _report_group("TA signal WITH a same-day ICT signal", overlap, mid)
    _report_group("TA signal, no ICT signal that day", non_overlap, mid)
    _concentration_report(overlap)
    _save(overlap, "test3_overlap")
    _save(non_overlap, "test3_non_overlap")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "test1":
        test1_setup_agreement(sys.argv[2], sys.argv[3])
    elif cmd == "test2":
        test2_macro_proximity(sys.argv[2], sys.argv[3])
    elif cmd == "test3":
        test3_ta_ict_overlap()
    elif cmd == "all":
        start, end = sys.argv[2], sys.argv[3]
        test1_setup_agreement(start, end)
        test2_macro_proximity(start, end)
        test3_ta_ict_overlap()
    else:
        print("usage: backtest_confluence.py [test1|test2] START END | test3 | all START END")
