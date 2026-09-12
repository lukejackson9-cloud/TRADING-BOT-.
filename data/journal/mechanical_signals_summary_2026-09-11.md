# Mechanical Signal Testing — Full Summary as of 2026-09-11

Compiled at the user's request: one final comparison table across every
mechanical (TA + ICT) setup tested by this project to date, plus a
same-day "what fires right now" check across every ICT variant. This is
a reference document, not a new finding — every number here was already
computed and logged individually in `data/trades.log` and `CLAUDE.md`;
this just puts them side by side.

## TA setups (`scripts/backtest_ta.py`) — 6-year window, 2020-08-05 to 2026-09-04

| Setup | Trades | Avg return/trade | Verdict |
|---|---|---|---|
| breakout | 2,666 | -0.06% | Negative |
| ema_cross | 887 | +0.01% | Statistically zero |
| mean_reversion | 562 | -0.46% | Negative |
| vcp_breakout (default 0.7) | 138 | -0.07% | Negative (reversed from a +0.24% 2-year read) |
| relative_strength | varies by threshold | mixed, non-monotonic | Noise, not a pattern |

None promoted. Full detail: CLAUDE.md's "Technical-analysis screening
layer" section.

## ICT setups (`scripts/backtest_ict.py`) — 5-year window unless noted, 2021-06-01 to 2026-09-04, 30-symbol universe

| Variant | Trades | Win% | Avg R/trade | Note |
|---|---|---|---|---|
| Baseline (sweep+MSS+FVG) | 987 | 32.6% | -0.11 | |
| + RSI-divergence filter | 175 | 33.1% | -0.19 | Filter made it worse |
| Order-block entry | 2,835 | 35.3% | -0.02 | Closest to flat, broadly distributed |
| OTE (Fibonacci) entry | 3,871 | 34.1% | +0.02 headline | 70% of the positive R was one symbol (NVDA); ex-NVDA: +0.007, statistically zero |
| Inverse FVG | 326 | 31.3% | -0.16 | |
| EQH/EQL liquidity pool | 218 | 30.7% | -0.13 | |
| News-exclude (NFP+FOMC+CPI) | 872 | 32.7% | -0.11 | ~Unchanged from baseline |
| News-only (NFP+FOMC+CPI) | 115 | 32.2% | -0.15 | Worse than NFP+FOMC alone (-0.07) |
| NY PM killzone | 1,337 | 33.9% | -0.14 | |
| 1-min bars (Alpaca IEX, 5yr) | 2,860 | 33.3% | -0.01 | Closest-to-breakeven full-history result |
| 1-min bars (Alpaca IEX, same 2yr as below) | 1,132 | 35.0% | +0.04 | Same symbols/window, lower precision |
| 1-min bars (Massive full-tape, 2yr only) | 1,527 | 37.5% | +0.10 | Real precision effect vs. IEX, but unconfirmed beyond 2yr — likely partly a favorable-period effect (declined to pay to extend) |

None promoted. Full detail and reasoning: CLAUDE.md's "ICT" subsection.

## Overall: 17 distinct mechanical signal variants tested, zero promoted

Every one is either clearly negative, statistically indistinguishable
from zero, or (the 1-min full-tape case) real-but-unconfirmed and likely
partly explained by a short favorable window. This is the complete,
honest state of mechanical/technical signal testing for this project as
of tonight — see the "Goals & pace" and "Council calibration" sections
of CLAUDE.md for why this hasn't been treated as a reason to lower any
bar.

## Live check: what fires on the most recent completed session (2026-09-10)

Not a new backtest — a same-day pass of each ICT variant against the
30-symbol universe's actual 2026-09-10 killzone data, to see what each
model would have flagged. **This is not a trade proposal or research
pass** — none of this has been through skills/research.md or
skills/council.md, and sample sizes are far too small (single-day) to
mean anything statistically. Shown for completeness only.

- Baseline, inverse-FVG, EQH/EQL: 0 signals.
- **Order-block**: 7 signals — MSFT (bullish, +2.0R), AMZN (bullish,
  +0.13R), TSLA (bullish, -1.0R), XOM (bearish, +2.0R), MA (bullish,
  -1.0R), NFLX (bullish, +0.21R), CVX (bullish, +0.06R). 71.4% "win rate"
  on 7 trades is not meaningful — the same setup's real, full-sample
  result is -0.02R/trade over 2,835 trades.
- **OTE**: 5 signals — MSFT (bullish, -1.0R), META (bearish, +2.0R),
  TSLA (bullish, -1.0R), MA (bullish, -1.0R), NFLX (bullish, +2.0R).

TA setups already screen the whole market daily via the existing
`skills/paper_trade_ta.md` routine — no separate live check needed there;
see `data/paper_trades.json` for current open positions by setup.
