# Skill: Paper-trade the TA setups

Goal: keep a live, forward-running paper track record for the mechanical
TA setups defined in `scripts/backtest_ta.py`'s shared `iter_signals()`
(20-day breakout + volume, 9/21-day EMA crossover, and — automatically,
since 2026-09-08, when mean_reversion was added to that shared function —
RSI(14) mean-reversion too), so the decision on whether any of them
becomes a new screening layer in CLAUDE.md is made on real forward
evidence, not just the historical backtest.

**This is a separate, fully mechanical track. It does not touch the
advisory pipeline** (screen.md -> research.md -> council.md ->
propose_trades.md) and produces nothing the user is asked to act on.
Positions here are simulated against real market data only, to answer one
question: "would this rule have made money if run for real, day after
day, without a human in the loop." Do not report individual paper-trade
opens/closes to the user as if they were trade ideas -- they aren't.

## Steps
1. Run once per trading day, after the session settles -- same timing as
   skills/screen.md (Massive's grouped-daily data is end-of-day only;
   don't run this pre-market or mid-session expecting today's data).
2. `python scripts/paper_trader.py run {last_completed_session_date}`
   - Closes any open position whose -4% stop / +8% target / 5-trading-day
     time-stop has resolved as of that date (`check_open_positions`).
   - Opens one new paper position for every (ticker, setup) that signals
     on that date and doesn't already have an open position under that
     exact setup (`scan_for_new_signals`).
3. Log a one-line NOTE to /data/trades.log with the day's open/close
   counts (not a per-ticker breakdown -- that detail lives in
   /data/paper_trades.json itself).
4. Do not act on anything here -- no proposal, no research.md entry, no
   council review. This is data collection, not advice.

## When to actually look at the results
- Weekly, or whenever skills/journal.md runs: pull a summary
  (`python scripts/paper_trader.py summary`) and fold the win
  rate/expectancy into the same conversation as the historical backtest
  results -- forward and historical numbers should broadly agree; if they
  diverge a lot, that itself is worth reporting (possible regime change,
  or the historical backtest window wasn't representative).
- Never promote a setup to CLAUDE.md's main screening layer without: (a)
  a completed multi-year historical backtest showing real edge, AND (b) a
  meaningful number of forward paper trades (not just a handful) agreeing
  with it, AND (c) discussing it with the user first -- same rule as
  CLAUDE.md's council-calibration section: real evidence, then a
  conversation, never a silent change.

## File Map addition
- /data/paper_trades.json -- the paper-trading ledger (see
  scripts/paper_trader.py's docstring for the exact shape). Tracked in
  git like pending_trades.json/positions.json -- it's part of the audit
  trail, not regenerable cache.
