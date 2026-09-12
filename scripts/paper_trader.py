"""
Automated forward paper-trading for the TA setups researched in
scripts/backtest_ta.py -- all five setups iter_signals() yields (breakout,
ema_cross, mean_reversion, vcp_breakout, relative_strength as of
2026-09-11, once spy_closes was wired into scan_for_new_signals below;
this file makes no setup-specific assumptions, so it always tracks
whatever iter_signals() defines, by design).

This is NOT the advisory pipeline (skills/screen.md -> research.md ->
council.md -> propose_trades.md) and it never touches that flow -- it's a
separate, fully mechanical evaluation track with no human judgment and no
proposal to the user. Positions here are SIMULATED against real market
data, never real trades, and are never something the user is asked to act
on. It exists purely to build a live, forward track record for the TA
setups, so that the decision about promoting one to CLAUDE.md's main
screening layer is made on real forward evidence, not just a historical
backtest that could be overfit to the tested window. See
scripts/backtest_ta.py's docstring for the historical side of this same
question.

CLAUDE.md's "no trade is ever placed without human approval" rule is about
REAL trades -- there is no brokerage account connected in this project's
current mode, and nothing here calls trading212_client.py or any
execution path. This ledger is exactly as inert as the historical
backtest, just extended forward day by day instead of computed once over
history.

Ledger: data/paper_trades.json -- list of positions:
  {"ticker", "setup", "entry_date", "entry_price", "stop_price",
   "target_price", "days_held", "status": "open"|"closed",
   "exit_date", "exit_price", "exit_reason": "stop"|"target"|"time_stop",
   "pct_return", "catalyst": None|{"has_catalyst", "note", "tagged_on"}}
  "catalyst" (added 2026-09-11) starts None on every new entry and is
  filled in by scripts/tag_catalyst.py per skills/catalyst_tag.md's daily
  procedure -- see that script's docstring for why (the forward-only
  counterpart to backtest_confluence.py's historical tests, which could
  never honestly test "signal + a real news catalyst"). Entries from
  before 2026-09-11 simply lack this key entirely, not None -- never
  backfilled with hindsight.

Meant to run once per trading day, after the session settles (same
post-close timing rationale as skills/screen.md -- Massive's grouped-daily
data is end-of-day only, confirmed unreliable if queried intraday):
  1. check_open_positions(as_of_date) -- pulls the latest completed
     session's OHLC for every open position's ticker and applies the same
     -4%/+8%/5-trading-day exit rule as backtest_ta.py, closing any that
     resolve.
  2. scan_for_new_signals(as_of_date) -- pulls/caches the last ~35
     calendar days of grouped-daily data (reusing backtest_ta.py's cache
     so repeat daily runs mostly hit disk, not the API), runs
     backtest_ta.iter_signals() on each ticker's trailing window, and
     opens one new paper position per (ticker, setup) signal on the most
     recent day, unless that exact (ticker, setup) already has an open
     position.

Usage:
  python scripts/paper_trader.py run 2026-09-04   # as_of_date = last completed session
"""

import sys
import json
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from massive_client import get_grouped_daily  # noqa: E402
from backtest_ta import (  # noqa: E402
    fetch_range, _load_series, iter_signals, _spy_closes,
    STOP_PCT, TARGET_PCT, TIME_STOP_DAYS,
)

LEDGER_PATH = Path("data/paper_trades.json")
SCAN_LOOKBACK_DAYS = 35  # calendar days -- comfortably covers 21+ trading days


def _load_ledger():
    if LEDGER_PATH.exists():
        return json.loads(LEDGER_PATH.read_text())
    return []


def _save_ledger(ledger):
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2))


def check_open_positions(as_of_date):
    """Closes any open position whose stop/target/time-stop has resolved
    as of as_of_date's session (must be a completed session's date -- same
    caveat as everywhere else in this project that touches Massive)."""
    ledger = _load_ledger()
    open_positions = [p for p in ledger if p["status"] == "open"]
    if not open_positions:
        return ledger

    data = get_grouped_daily(as_of_date)
    if data.get("status") != "OK":
        print(f"check_open_positions: {as_of_date} not a usable session ({data.get('status')}), skipping")
        return ledger
    day = {r["T"]: r for r in data.get("results", [])}

    for p in open_positions:
        if p["entry_date"] >= as_of_date:
            continue  # entry_price is that day's close (see scan_for_new_signals) --
            # checking stop/target against the SAME day's own low/high would test the
            # position against the very bar that set its entry price, not a real
            # forward move. Only evaluate starting from a session strictly after entry.
        row = day.get(p["ticker"])
        if row is None:
            continue  # no print/data today (halted, delisted) -- leave open, check again next run
        if p.get("last_checked_date") == as_of_date:
            continue  # already processed this date (re-run safety)

        p["days_held"] = p.get("days_held", 0) + 1
        p["last_checked_date"] = as_of_date

        if row["l"] <= p["stop_price"]:
            p.update(status="closed", exit_date=as_of_date, exit_price=p["stop_price"],
                      exit_reason="stop", pct_return=STOP_PCT)
        elif row["h"] >= p["target_price"]:
            p.update(status="closed", exit_date=as_of_date, exit_price=p["target_price"],
                      exit_reason="target", pct_return=TARGET_PCT)
        elif p["days_held"] >= TIME_STOP_DAYS:
            pct = (row["c"] - p["entry_price"]) / p["entry_price"]
            p.update(status="closed", exit_date=as_of_date, exit_price=row["c"],
                      exit_reason="time_stop", pct_return=pct)

    _save_ledger(ledger)
    closed_now = [p for p in open_positions if p["status"] == "closed" and p.get("exit_date") == as_of_date]
    print(f"check_open_positions: {len(open_positions)} were open, {len(closed_now)} closed today")
    return ledger


def scan_for_new_signals(as_of_date):
    """Opens a new paper position for each (ticker, setup) that signals on
    as_of_date's session, unless that exact combination already has an
    open position (avoids re-opening the same signal every day it stays
    technically true, e.g. price still above the breakout level).
    Includes relative_strength (added 2026-09-11) alongside the other four
    setups -- the only one of backtest_ta.py's five setups that wasn't
    already being forward-tracked, since it needs spy_closes wired in."""
    end = datetime.date.fromisoformat(as_of_date)
    start = (end - datetime.timedelta(days=SCAN_LOOKBACK_DAYS)).isoformat()
    fetch_range(start, as_of_date)  # cache-aware; only fetches days not already cached
    series = _load_series(start, as_of_date)
    spy_closes = _spy_closes(start, as_of_date)

    ledger = _load_ledger()
    already_open = {(p["ticker"], p["setup"]) for p in ledger if p["status"] == "open"}
    opened = 0

    for ticker, bars in series.items():
        if len(bars) < 25 or bars[-1][0] != as_of_date:
            continue  # not enough history, or ticker had no print on as_of_date
        last_i = len(bars) - 1
        for i, date, setup in iter_signals(bars, spy_closes=spy_closes):
            if i != last_i:
                continue  # only care about a signal firing on the most recent day
            if (ticker, setup) in already_open:
                continue
            # KNOWN DIVERGENCE FROM THE BACKTEST (documented 2026-09-12).
            # backtest_ta._simulate_exit enters at the NEXT session's OPEN;
            # this track enters at the SIGNAL DAY'S CLOSE because it runs
            # once daily after the close and cannot know tomorrow's open.
            # This module's docstring claims the two tracks "can never
            # define a signal differently" -- true of the SIGNAL, but the
            # ENTRY has silently differed all along.
            # Re-graded all 51 closed trades with the backtest's next-open
            # convention on 2026-09-12: aggregate was IDENTICAL (-3.48%/trade,
            # 4% win either way; mean overnight gap -0.68%, 24/46 gapping
            # down). So this is a real inconsistency to fix, but it is NOT
            # what produced the bad numbers -- entry-date concentration was
            # (see _entry_date_concentration). Proper fix is two-phase:
            # record the signal today, set entry from tomorrow's open on the
            # next run. Not done yet; do not quietly "fix" it by changing
            # the number here, which would just mislabel the same close.
            entry_price = bars[i][4]  # today's close -- real entry would be tomorrow's
            # open; using today's close as a same-day approximation since
            # this runs once daily after close, not intraday.
            ledger.append({
                "ticker": ticker, "setup": setup,
                "entry_date": as_of_date, "entry_price": entry_price,
                "stop_price": entry_price * (1 + STOP_PCT),
                "target_price": entry_price * (1 + TARGET_PCT),
                "days_held": 0, "status": "open",
                # None = not yet checked; see scripts/tag_catalyst.py /
                # skills/catalyst_tag.md (added 2026-09-11) -- older
                # entries simply lack this key entirely, not None, so
                # tag_catalyst.py's `pending` never mistakes them for
                # something awaiting a check.
                "catalyst": None,
            })
            already_open.add((ticker, setup))
            opened += 1

    _save_ledger(ledger)
    print(f"scan_for_new_signals: opened {opened} new paper position(s) as of {as_of_date}")
    return ledger


def _entry_date_concentration(closed):
    """THE CHECK THAT SHOULD HAVE BEEN HERE FROM DAY ONE (added 2026-09-12).

    On 2026-09-12 this ledger showed 51 closed trades at -3.06%/trade with a
    7.8% win rate, which reads as catastrophic strategy failure. It is not.
    All 51 were opened on exactly TWO dates -- 2026-09-04 (28) and
    2026-09-08 (23) -- and those were the two worst sessions in the cached
    window for this exit rule. Whole-market baseline on the same dates and
    the same rule: -2.51% / 12.4% win on 09-04, -3.18% / 6.9% win on 09-08.
    The identical rule on 2026-09-01 returned +0.15% with a 42.1% win rate.

    So "n=51" was really n=2 independent days. Trades opened on one session
    share that session's forward tape almost entirely -- they are nowhere
    near independent observations. Same effective-sample-size trap that
    invalidated the 20-day backtest result (see exit_rule_sweep.py), now in
    the live track. There is a selection effect on top: breakout-type
    signals cluster on churny, high-dispersion days, which are precisely the
    days that mean-revert afterwards, so this ledger will keep
    over-sampling bad tape unless the date spread is watched.

    Never report this ledger's aggregate without this line beside it."""
    dates = sorted({p["entry_date"] for p in closed})
    n = len(closed)
    print(f"\n  entry-date spread: {n} closed trades across {len(dates)} distinct "
          f"entry date(s) -> ~{len(dates)} independent observations, NOT {n}")
    if dates:
        import collections
        c = collections.Counter(p["entry_date"] for p in closed)
        print("  " + ", ".join(f"{d}:{c[d]}" for d in dates))
    if len(dates) < 5:
        print("  *** TOO FEW DISTINCT DATES TO CONCLUDE ANYTHING. A bad (or good) tape on")
        print("      one session dominates the whole aggregate. Do not read the avg/win")
        print("      rate below as a verdict on the setups. ***")


def summary():
    ledger = _load_ledger()
    open_n = sum(1 for p in ledger if p["status"] == "open")
    closed = [p for p in ledger if p["status"] == "closed"]
    print(f"{open_n} open, {len(closed)} closed")
    _entry_date_concentration(closed)
    for setup in ("breakout", "ema_cross"):
        trades = [p for p in closed if p["setup"] == setup]
        if not trades:
            continue
        wins = sum(1 for p in trades if p["pct_return"] > 0)
        avg = sum(p["pct_return"] for p in trades) / len(trades) * 100
        print(f"  {setup}: {len(trades)} closed, {wins}/{len(trades)} wins, avg {avg:.2f}%/trade")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "run":
        as_of = sys.argv[2]
        check_open_positions(as_of)
        scan_for_new_signals(as_of)
        summary()
    elif cmd == "summary":
        summary()
    else:
        print("usage: paper_trader.py run AS_OF_DATE | paper_trader.py summary")
