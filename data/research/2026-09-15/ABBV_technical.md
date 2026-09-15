# ABBV — Technical Context Specialist Report
Date: 2026-09-15 | Council step 3 (Technical Context specialist, non-argumentative fact report)

**Framing reminder (per CLAUDE.md's "Signal confluence testing" and
skills/council.md): none of the numbers below are evidence this trade is
more likely to win. This project tested matching mechanical TA/ICT
signals across 9 combinations and found no edge anywhere. This report
exists only to catch overextension/chasing risk with real numbers.**

## Data source
Alpaca (`scripts/alpaca_client.py get_historical_bars`, 1Day bars, IEX
feed), ABBV and SPY, ~52 trading days fetched (2026-07-02 through
2026-09-15, today's bar included). Signals computed by importing
`iter_signals()` directly from `scripts/backtest_ta.py` (not
reimplemented), with SPY closes supplied so `relative_strength` is also
evaluated.

## Most recent bar (2026-09-15)
O=260.40 H=264.79 L=257.94 C=261.88 V=195,211

## 20-day range position
- Prior 20-trading-day high (excl. today): **266.88** (set 2026-08-19)
- Prior 20-trading-day low (excl. today): **247.43** (set 2026-09-09)
- Distance from 20-day high: **-1.87%** (below it, has not made a new
  20-day high)
- Distance from 20-day low: **+5.84%** (well off the recent low)

## Volume
- Prior 20-day average volume: 171,511
- Today's volume vs. 20-day avg: **+13.82%**
- Trailing 5-day avg volume vs. 20-day avg: **+7.94%**
- Read: modestly elevated, not a dramatic volume spike. No single day in
  the last 30 shows volume anywhere near the 1.5x threshold this
  project's `breakout` setup requires, except in combination with price
  action that didn't clear the prior high (see below).

## Signal check (`iter_signals()`, verbatim from backtest_ta.py)
Ran across the full ~52-day fetched window, including today:
**NONE of breakout / ema_cross / mean_reversion / vcp_breakout /
relative_strength fired on today's bar, and none fired anywhere in this
window at all.**
- `breakout` doesn't fire because today's close (261.88) is still below
  the prior-20-day high (266.88) — the underlying condition requires a
  NEW high, not just a move up.
- `ema_cross`: EMA9 (258.04) is currently above EMA21 (257.13) — an
  established short-term uptrend — but the actual cross happened earlier
  in this window, not today, so it doesn't re-fire.
- `mean_reversion` (RSI(14) crossing up through 30): RSI is currently
  57.5 (mid-range, up from 45.3 five days ago) — nowhere near the
  oversold-bounce zone this setup requires.
- `vcp_breakout`: subset of breakout; can't fire without breakout firing
  first.
- `relative_strength`: no crossing of the +15pp trailing-outperformance
  threshold detected in this window.

## Secondary cross-check: TradingView `get_rating()` (non-deciding)
NYSE:ABBV, 1d interval — Summary: **BUY** (15 buy / 2 sell / 9 neutral).
Moving averages sub-rating: STRONG_BUY. Oscillators sub-rating: NEUTRAL
(consistent with RSI at 57.5 — trending up but not overbought). This is
someone else's black-box aggregation, included only as a secondary data
point per council.md, not a decision input.

## 30-trading-day price context
- Close 30 trading days ago (2026-08-04): 243.70
- Close today (2026-09-15): 261.88
- **30-day move: +7.46%**
- Shape of the move (not a straight line): ABBV jumped from ~250 to a
  local peak of 266.88 in a fast 2-day move (2026-08-17→08-19, roughly
  +6%), pulled back over the following ~3 weeks to a low of 247.43 on
  2026-09-09, and has since climbed back to 261.88 as of today — the leg
  research.md flagged (9/9 → 9/14/9/15) is this second, more recent
  climb, not the original August spike.

## Extended vs. early-stage — explicit answer
**Neither cleanly "already extended" nor a fresh, un-run breakout — this
is a partial re-test of a prior high, not a new one.** Specifically:
- It is NOT sitting at a fresh 20-day high or showing a parabolic/blow-off
  shape — it's still -1.87% below the August 19 high, and no breakout
  signal has fired.
- It is NOT oversold or at a fresh base either — RSI (57.5) is mid-range,
  not extended (would expect >70 for a genuinely overbought/chasing
  entry), and price is already +5.84% off its own 20-day low.
- The move being reported to council (9/9 low → now) is a real,
  identifiable ~4.4% recovery leg (250.92 → 261.88) riding back toward a
  high the stock already touched once in August and failed to hold —
  i.e., there is a specific overhead level (266.88) worth flagging to the
  bull/bear agents as the level this move would need to clear to be a
  genuine new high rather than a round-trip back to a prior ceiling.
  Volume on this leg has been only modestly elevated, not a surge
  consistent with urgent, broad buying pressure.

## Summary for bull/bear agents and moderator
No mechanical TA signal is present on ABBV today. Price is in the
upper-middle of its 20-day range, in a short-term uptrend (EMA9>EMA21,
RSI 57.5), but has not yet cleared its own recent (Aug 19) high of
266.88 — so the current move reads as a recovery/re-test of a prior high
rather than either a fresh breakout or an already-blown-out extended
move. Volume is only mildly elevated. TradingView's own consensus rating
is BUY (secondary, non-deciding). Flag the 266.88 level as the relevant
overhead reference point for the bull/bear discussion.
