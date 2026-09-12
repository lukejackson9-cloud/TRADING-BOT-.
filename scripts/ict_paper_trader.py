"""
Forward paper-trading for the ICT models in scripts/backtest_ict.py.

WHY THIS LOOKS DIFFERENT FROM scripts/paper_trader.py (the TA setups'
forward tracker): TA setups (breakout, ema_cross, etc.) open a position
and hold it for up to 5 trading days, so that tracker has to persist open
positions and check them daily. ICT setups open AND resolve within the
same trading session (stop/target/time-stop all fire by that day's 16:00
ET close) -- there is no multi-day position to track. So "forward paper
trading" for ICT is simply: once a session is complete, run each
mechanism against that day's real bars (the exact same simulation code
the backtest uses) and log whatever trades result. This is not a
weaker form of paper trading -- it's what these same-day models actually
need instead of what daily-position tracking would give them.

SCOPE (deliberate, see CLAUDE.md/HANDOFF.md 2026-09-11 for the
reasoning): tracks the 6 genuinely distinct mechanisms tested in
backtest_ict.py -- fvg (baseline), order_block, ote, inverse_fvg, eqhl,
nypm (killzone variant of baseline) -- using the standard 5-min Alpaca
IEX bars, same data source/cadence as the historical backtest. Does NOT
track the divergence-bias or news-calendar filters as separate entries
(those are analytical modifiers on the baseline, not independent
strategies) and does NOT attempt daily 1-min or Massive full-tape
fetches (that would add real ongoing complexity/rate-limit management
for a precision question already answered for now -- see the 2026-09-11
decision not to purchase extended full-tape history).

Ledger: data/ict_paper_trades.json -- a flat list of
{date, symbol, setup, direction, return_r, catalyst}, one entry per
trade that actually fired (no signal that day = no entry, same as the
backtest). NOT the advisory pipeline -- no proposal to the user, no
research/council review, purely evaluation data for whether any ICT
mechanism earns a place in Strategy, same purpose as data/paper_trades.json
for the TA setups.

"catalyst" (added 2026-09-11) starts None on every new trade and is
filled in by scripts/tag_catalyst.py per skills/catalyst_tag.md's daily
procedure -- see that script's docstring for why (the forward-only
counterpart to backtest_confluence.py's historical tests, which could
never honestly test "signal + a real news catalyst"). Entries from
before 2026-09-11 simply lack this key entirely, not None -- never
backfilled with hindsight.

Usage:
  python scripts/ict_paper_trader.py run 2026-09-10
"""

import sys
import json
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import backtest_ict as ict  # noqa: E402

LEDGER_PATH = Path("data/ict_paper_trades.json")
LOOKBACK_DAYS_FOR_EQHL = 5


def _load_ledger():
    if LEDGER_PATH.exists():
        return json.loads(LEDGER_PATH.read_text())
    return []


def _save_ledger(trades):
    LEDGER_PATH.write_text(json.dumps(trades, indent=2))


def _ensure_day_cached(date):
    """Fetches and merges `date` (plus the prior LOOKBACK_DAYS_FOR_EQHL
    calendar days, for EQH/EQL's lookback) into the existing 5-min cache
    if not already present -- same merge approach used for the
    2026-09-11 backfill, so re-running on an already-cached day is a
    cheap no-op."""
    from alpaca_client import get_historical_bars

    start = (datetime.date.fromisoformat(date) - datetime.timedelta(days=LOOKBACK_DAYS_FOR_EQHL + 3)).isoformat()
    for symbol in ict.UNIVERSE:
        cache_file = ict.CACHE_DIR / f"{symbol}.json"
        existing = json.loads(cache_file.read_text()) if cache_file.exists() else []
        existing_dates = {b["t"][:10] for b in existing}
        if date in existing_dates:
            continue
        new_bars = get_historical_bars(symbol, f"{start}T00:00:00Z", f"{date}T23:59:59Z", timeframe="5Min")
        seen = {b["t"] for b in existing}
        merged = existing + [b for b in new_bars if b["t"] not in seen]
        merged.sort(key=lambda b: b["t"])
        cache_file.write_text(json.dumps(merged))


def _day_pdh_pdl(days, date, sorted_dates):
    i = sorted_dates.index(date)
    if i == 0:
        return None, None
    prev_bars = days[sorted_dates[i - 1]]
    regular = [b for b in prev_bars if datetime.time(9, 30) <= b["_ny_time"] <= ict.SESSION_CLOSE]
    if not regular:
        return None, None
    return max(b["h"] for b in regular), min(b["l"] for b in regular)


def _day_eqh_eql(days, date, sorted_dates):
    i = sorted_dates.index(date)
    window = sorted_dates[max(0, i - LOOKBACK_DAYS_FOR_EQHL):i]
    highs, lows = [], []
    for d in window:
        regular = [b for b in days[d] if datetime.time(9, 30) <= b["_ny_time"] <= ict.SESSION_CLOSE]
        if regular:
            highs.append((d, max(b["h"] for b in regular)))
            lows.append((d, min(b["l"] for b in regular)))
    return ict._find_equal_levels(highs), ict._find_equal_levels(lows)


def run(date):
    _ensure_day_cached(date)
    ledger = _load_ledger()
    already_done = {(t["date"], t["symbol"], t["setup"]) for t in ledger}
    new_trades = []

    for symbol in ict.UNIVERSE:
        days = ict._load_days(symbol)
        sorted_dates = sorted(days.keys())
        if date not in sorted_dates:
            continue
        day_bars = sorted(days[date], key=lambda b: b["_ny_time"])
        kz = [b for b in day_bars if ict.KILLZONE_START <= b["_ny_time"] <= ict.KILLZONE_END]
        kz_start_idx = next((idx for idx, b in enumerate(day_bars) if b["_ny_time"] >= ict.KILLZONE_START), None)
        kz_pm = [b for b in day_bars if datetime.time(13, 30) <= b["_ny_time"] <= datetime.time(16, 0)]
        kz_pm_start_idx = next((idx for idx, b in enumerate(day_bars) if b["_ny_time"] >= datetime.time(13, 30)), None)
        pdh, pdl = _day_pdh_pdl(days, date, sorted_dates)
        eqh, eql = _day_eqh_eql(days, date, sorted_dates)

        checks = []
        if kz and kz_start_idx is not None and pdh is not None:
            checks.append(("fvg", kz, pdh, pdl, day_bars, kz_start_idx, {}))
            checks.append(("order_block", kz, pdh, pdl, day_bars, kz_start_idx, {"entry_mode": "order_block"}))
            checks.append(("ote", kz, pdh, pdl, day_bars, kz_start_idx, {"entry_mode": "ote"}))
        if kz_pm and kz_pm_start_idx is not None and pdh is not None:
            checks.append(("nypm", kz_pm, pdh, pdl, day_bars, kz_pm_start_idx, {}))
        if kz and kz_start_idx is not None and (eqh is not None or eql is not None):
            checks.append(("eqhl", kz, eqh, eql, day_bars, kz_start_idx, {}))

        for setup, killzone_bars, use_pdh, use_pdl, all_day_bars, start_idx, kwargs in checks:
            if (date, symbol, setup) in already_done:
                continue
            trade = ict._simulate_day(killzone_bars, use_pdh, use_pdl, all_day_bars, start_idx, **kwargs)
            if trade:
                new_trades.append({"date": date, "symbol": symbol, "setup": setup,
                                    "direction": trade["direction"], "return_r": trade["return_r"],
                                    "catalyst": None})

        if kz and kz_start_idx is not None and pdh is not None and (date, symbol, "inverse_fvg") not in already_done:
            trade = ict._simulate_day_inverse_fvg(kz, pdh, pdl, day_bars, kz_start_idx)
            if trade:
                new_trades.append({"date": date, "symbol": symbol, "setup": "inverse_fvg",
                                    "direction": trade["direction"], "return_r": trade["return_r"],
                                    "catalyst": None})

    ledger.extend(new_trades)
    _save_ledger(ledger)

    from collections import defaultdict
    by_setup = defaultdict(list)
    for t in new_trades:
        by_setup[t["setup"]].append(t)
    print(f"{date}: {len(new_trades)} new trade(s)")
    for setup, trades in sorted(by_setup.items()):
        print(f"  {setup}: {len(trades)} -- {[(t['symbol'], round(t['return_r'],2)) for t in trades]}")

    if not new_trades:
        print("  (no signals fired across any tracked mechanism today)")


def _health_banner():
    """Run the catalyst-track health check at the end of every daily run.

    Deliberately here in the CODE PATH rather than in the routine's prompt:
    the daily routines already run this script and are already told to
    surface anything the script flags, so a check that lives here cannot be
    lost to a prompt edit, a reworded routine, or a future session that runs
    the script by hand instead. It is also why this prints loudly rather
    than changing the exit code -- a non-zero exit from a run that actually
    SUCCEEDED would read as a crash and could stop the routine before it
    commits its ledger.

    Today's just-written entries are untagged at this moment by design
    (tagging runs after this script), which is exactly what health's grace
    period exists to absorb, so this cannot false-alarm on its own output.
    """
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from tag_catalyst import health
        print()
        if health() != 0:
            print("=" * 72)
            print("PLUMBING PROBLEM IN THE CATALYST TRACK — SURFACE THIS TO THE USER.")
            print("Send a PushNotification with the RESULT line above. This is a broken")
            print("pipeline, NOT a result about catalysts: an empty bucket because nothing")
            print("was ever written is not evidence, and must never be reported as any.")
            print("=" * 72)
    except Exception as e:
        print(f"\nwarn: health check could not run ({e}) — check scripts/tag_catalyst.py")


if __name__ == "__main__":
    cmd, date = sys.argv[1], sys.argv[2]
    if cmd == "run":
        run(date)
        _health_banner()
    else:
        print("usage: ict_paper_trader.py run YYYY-MM-DD")
