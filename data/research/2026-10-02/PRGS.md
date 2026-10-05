# PRGS — 2026-10-02

## Step 0: prior context
No entry for PRGS in /data/journal/trade_ledger.md or
/data/journal/lessons.md — first appearance. The shape of this catalyst
(EPS beat undercut by weak forward guidance) closely matches the project's
own documented pattern from GWRE (2026-09-04), HPE (2026-09-03), ASO
(2026-09-10), and BRZE (2026-09-10, not yet checked) — all council-
downgraded or capped for exactly this "beat-but-soft-guide" shape. Noted
as context, not a predetermined verdict — this is PRGS's own fresh
evaluation.

## Identity check
Progress Software Corporation (NASDAQ: PRGS) — the real enterprise
infrastructure-software company (application development, data
connectivity, and, following a 2026 acquisition, Domo's AI/data
platform). Confirmed real, not a collision.

## Catalyst
Real, dated, and company-specific. Progress Software reported fiscal Q3
2026 earnings on 2026-10-01:
- **EPS beat**: $1.69 vs. ~$1.52 consensus — a real, sizeable beat (~11%).
- **Revenue slight miss**: $246.0M vs. ~$246.7M consensus — essentially
  in-line, not a meaningful miss on its own.
- **The actual driver of the selloff — weak Q4 guidance**: adjusted EPS
  guidance of $1.24–$1.33 for the next quarter, below the $1.37 analyst
  consensus. Lower operating expenses and stronger margins drove the Q3
  beat, but the forward guide disappointed.
- **Contradictory signal worth flagging**: the company simultaneously
  **raised full-year FY2026 adjusted EPS guidance to $6.15–$6.23**,
  citing a better-than-expected contribution from the recently closed
  Domo AI/Data Platform acquisition. DA Davidson reiterated a Buy rating
  the same day (2026-10-02) with an unchanged $55 price target — roughly
  50% above the post-selloff price, and explicitly cited Domo's
  contribution coming in ahead of its own model.

## Price reaction (verified via scripts/alpaca_client.py)
- 2026-09-30 close: $40.11
- 2026-10-01 close: $36.56 (**-8.85%**, matches the task's -8.48% closely)
- 2026-10-02 (today, partial session): opened $37.18, low $35.94, last
  $36.99 — a modest ~+1.2% stabilization, not a reversal.

## Sentiment
Mixed, leaning bearish on the immediate reaction despite one real
contrarian analyst voice. TradingView's aggregated technical consensus
(NASDAQ:PRGS): **SELL (3 buy / 14 sell / 9 neutral)** — the market/
technical read does not share DA Davidson's bullishness. The guide-down
quarter-over-quarter (even against a raised full-year number) reads as
the market discounting near-term execution risk more than it's crediting
the Domo upside story — the same "soft underneath the headline beat"
shape as GWRE/HPE/ASO above.

## Risks
- **This project is long-only.** The immediate reaction here is negative
  — there is no documented bullish catalyst to act on today, only a
  single analyst's standing (not fresh) price target that the market is
  currently ignoring.
- DA Davidson's $55 target is a real, dated data point (reiterated
  2026-10-02) but is a single sell-side opinion against a broader SELL
  technical consensus — per lessons.md #5, weighted lower than the
  company's own guidance numbers, which were the actual proximate driver
  of the drop.
- If PRGS stabilizes and the FY26 guidance raise (Domo-driven) starts
  showing up in the next quarter's actual numbers rather than just
  guidance, that would be a materially different, re-checkable setup —
  not what's in front of us today.

## Sources
- https://www.gurufocus.com/news/9107810/prgs-maintained-by-da-davidson-price-target-stays-at-5500
- https://www.investing.com/news/analyst-ratings/da-davidson-reiterates-buy-on-progress-software-stock-55-target-93CH-4929980
- https://www.marketbeat.com/instant-alerts/price-progress-software-nasdaq-prgs-shares-down-63-time-to-sell-2026-10-01/
- https://finance.yahoo.com/markets/stocks/articles/progress-software-corporation-q3-2026-123000917.html
- https://www.investing.com/equities/progress-software
- scripts/alpaca_client.py live pull (get_historical_bars, PRGS, 2026-09-28 to 2026-10-02) — authoritative OHLCV
- scripts/tradingview_client.py live pull (NASDAQ:PRGS technical-rating summary)

## Verdict
PASS (real, dated, negative-leaning catalyst — an EPS beat overshadowed
by weak forward quarterly guidance, despite a raised full-year number and
one analyst's bullish target. Same beat-but-soft-guide shape this project
has repeatedly downgraded before; this project is long-only and has no
actionable bull thesis for a stock that just sold off on its own
forward guidance.)

## Confidence
medium
