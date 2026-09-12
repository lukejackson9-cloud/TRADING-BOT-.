"""
Reports which mechanical TA setups have fired recently on one ticker, for
skills/research.md to read as CONTEXT before writing a verdict.

WHAT THIS IS FOR — AND THE TRAP IT IS BUILT TO AVOID
----------------------------------------------------
The advisory pipeline (screen -> research -> council -> propose) and the
mechanical TA/ICT track have never spoken to each other; verified
2026-09-12, zero cross-references in either direction. This is the first
bridge, and it is deliberately one-way and non-binding: research.md may
READ this, nothing here decides anything.

The trap: a naive "breakout fired on AAPL today" line handed to a research
pass reads as bullish corroboration. **It is not, and the project's own
data says so.** Volatility-matched against same-session, same-volatility
peers over 63 bias-corrected sessions (2024-09-11..2024-12-06), every
setup underperforms, all sign-consistent across halves:

    breakout           -0.21%/trade   (n=2,460)
    ema_cross          -0.16%/trade   (n=1,327)
    relative_strength  -0.23%/trade   (n=1,024)
    mean_reversion     -0.45%/trade   (n=677)
    vcp_breakout       -0.19%/trade   (n=73)

and 0 of 72 in-mandate stop/target/time-stop tweaks produce a positive,
split-half-consistent edge. So every report this script prints carries
those numbers inline. A future session cannot pick up a "breakout fired"
line without also seeing that breakout has no measured predictive value.

WHAT IT IS LEGITIMATELY GOOD FOR
--------------------------------
A fired TA setup is evidence about WHERE IN A MOVE the price already is,
not evidence the move continues. "Closed above its 20-day high on 1.5x
volume" means the move has ALREADY HAPPENED — which is exactly the
situation lessons.md #1 is about (a real catalyst whose reaction has
already fired is a weaker setup, not a stronger one), and which the
2026-09-07 gap-proxy test confirmed quantitatively (requiring a gap made
results monotonically WORSE, because entry lands after the reaction).

So the honest use is as a CAUTION/positioning input, and as a second
feed for the catalyst_tag question (does "signal + real news" behave
differently from either alone?). Not as confirmation.

Signals come from backtest_ta.iter_signals, IMPORTED not reimplemented,
so this can never drift from what the backtests and paper trader count as
a signal.

Usage:
  python scripts/ta_context.py check NVDA
  python scripts/ta_context.py check NVDA --days 10
"""

import sys
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from backtest_ta import iter_signals  # noqa: E402
from alpaca_client import get_historical_bars  # noqa: E402

# Volatility-matched edge per setup, from exit_rule_sweep.py --per-setup
# (2026-09-12). Printed with every report so a firing signal is never
# mistaken for corroboration. Update these if that analysis is re-run.
MEASURED_EDGE = {
    "breakout": ("-0.21%/trade", 2460),
    "ema_cross": ("-0.16%/trade", 1327),
    "relative_strength": ("-0.23%/trade", 1024),
    "mean_reversion": ("-0.45%/trade", 677),
    "vcp_breakout": ("-0.19%/trade", 73),
}


def _bars(ticker, lookback_days=150):
    """Massive FIRST, Alpaca only as a flagged fallback.

    This is not a style preference, it is a correctness requirement found
    by a live test on 2026-09-12: BAND closed ABOVE its prior 20-day high
    on 1.8x average volume — a textbook `breakout` — and this script
    reported "no setup fired". Cause: Alpaca's free tier is the IEX feed,
    which carries only a partial slice of consolidated volume (ADBE
    2026-09-10: 269k on IEX vs 10.4M on Massive's full tape, ~2.6%).
    iter_signals applies backtest_ta's VOLUME_MIN >= 1,000,000 liquidity
    filter, so on IEX volume essentially every ticker is filtered out
    before any setup can fire, and the report silently reads as "clean".

    Under-reporting signals is worse than erroring here — research.md
    would record "no TA context" as a fact when it is an artifact. So:
    full-tape Massive by default, and when falling back the caller is told
    the volume is partial and signals are likely under-reported.

    Returns (bars, source, partial_volume)."""
    end = datetime.date.today()
    start = end - datetime.timedelta(days=lookback_days)
    try:
        from massive_client import get_ticker_range_aggs
        raw = get_ticker_range_aggs(ticker, start.isoformat(), end.isoformat())
        if raw:
            bars = [(datetime.datetime.fromtimestamp(
                b["t"] / 1000, tz=datetime.timezone.utc).date().isoformat(),
                b["o"], b["h"], b["l"], b["c"], b["v"]) for b in raw]
            return bars, "Massive (full consolidated tape)", False
    except Exception as e:
        print(f"  [Massive unavailable for {ticker}: {e} — falling back to Alpaca]")
    raw = get_historical_bars(ticker, f"{start}T00:00:00Z",
                              f"{end}T23:59:59Z", timeframe="1Day")
    bars = [(b["t"][:10], b["o"], b["h"], b["l"], b["c"], b["v"]) for b in raw]
    return bars, "Alpaca IEX (PARTIAL VOLUME)", True


def check(ticker, recent_days=5):
    try:
        bars, source, partial = _bars(ticker)
    except Exception as e:
        print(f"TA CONTEXT for {ticker}: data fetch failed ({e}) — treat as "
              f"'no TA context available', not as 'no signal fired'.")
        return
    if len(bars) < 30:
        print(f"TA CONTEXT for {ticker}: only {len(bars)} sessions available, "
              f"too few for the 20-day lookbacks — no context.")
        return

    try:
        spy = {d: c for d, _o, _h, _l, c, _v in _bars("SPY")[0]}
    except Exception:
        spy = None

    fired = [(i, d, s) for i, d, s in iter_signals(bars, spy_closes=spy)]
    cutoff = bars[-recent_days][0] if len(bars) > recent_days else bars[0][0]
    recent = [(d, s) for _i, d, s in fired if d >= cutoff]

    last = bars[-1]
    hi20 = max(b[2] for b in bars[-21:-1])
    lo20 = min(b[3] for b in bars[-21:-1])
    pos = (last[4] - lo20) / (hi20 - lo20) * 100 if hi20 > lo20 else float("nan")
    avg_vol = sum(b[5] for b in bars[-21:-1]) / 20

    print(f"## TA context — {ticker} (as of {last[0]}, source: {source})")
    # Massive settles ~30-90min post-close (CLAUDE.md), so an intraday or
    # early-evening run routinely lacks the current session -- and that is
    # exactly the session a same-day research pass cares about. Say so
    # rather than letting the as-of date pass unnoticed in the header.
    today = datetime.date.today()
    lag = (today - datetime.date.fromisoformat(last[0])).days
    if lag > 1:
        print(f"  !! DATA IS {lag} DAYS OLD (last bar {last[0]}, today {today}). Any move in")
        print(f"     the missing session(s) is NOT reflected above. If the catalyst being")
        print(f"     researched is from those sessions, this context predates it — say so")
        print(f"     in the note rather than treating it as current.")
    if partial:
        print("  !! PARTIAL-VOLUME FEED: iter_signals applies a >=1M volume filter,")
        print("     which this feed cannot satisfy for most tickers. Setups are")
        print("     UNDER-REPORTED — read 'none fired' as 'unknown', not as 'clean'.")
    rng = f"{pos:.0f}% of its 20-day range"
    if pos > 100:
        rng += " (ABOVE the prior 20-day high — the move has already happened)"
    elif pos < 0:
        rng += " (BELOW the prior 20-day low)"
    print(f"Close ${last[4]:.2f} | {rng} | "
          f"volume {last[5] / avg_vol:.1f}x the 20-day average")
    if not recent:
        print(f"No mechanical setup fired in the last {recent_days} sessions.")
    else:
        print(f"Setups fired in the last {recent_days} sessions:")
        for d, s in sorted(set(recent)):
            edge, n = MEASURED_EDGE.get(s, ("untested", 0))
            print(f"  {d}  {s:<18} [measured edge {edge}, n={n}]")
    print()
    print("HOW research.md MUST USE THIS (see this script's docstring):")
    print("- This is CONTEXT, never corroboration. Every setup above has a")
    print("  NEGATIVE volatility-matched edge; a firing signal is not evidence")
    print("  the move continues, and must never be cited as a reason to upgrade")
    print("  a verdict toward CANDIDATE.")
    print("- Its legitimate reading is POSITIONAL: a fired breakout means the")
    print("  move has ALREADY happened, which is lessons.md #1's situation (a")
    print("  reaction that already fired is a weaker setup, not a stronger one).")
    print("  A high % of the 20-day range says the same thing.")
    print("- Record what this said in the research note either way, so the")
    print("  catalyst_tag track can later compare 'signal + real news' against")
    print("  news alone. Absence of a signal is as loggable as presence.")


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "check":
        print(__doc__.strip().split("Usage:")[-1])
        sys.exit(0)
    days = 5
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])
    check(sys.argv[2].upper(), days)
