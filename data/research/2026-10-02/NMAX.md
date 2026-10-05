# NMAX — 2026-10-02

## Step 0: prior context
No entry for NMAX in /data/journal/trade_ledger.md or
/data/journal/lessons.md — first appearance.

## Identity check
Newsmax, Inc. (NYSE: NMAX) — the real cable-news/media company, confirmed
via multiple independent sources (recently went public, trades on NYSE).
Not a ticker collision.

## Catalyst
**No fresh, dated, company-specific catalyst found for 2026-10-01.** The
negative commentary found is a mix of stale and generic:
- Wall Street Zen downgraded NMAX from Buy to Hold — dated
  **2026-09-19**, 12 days stale relative to today, not a same-day driver.
- Weiss Ratings maintains a standing "Sell" rating (not newly issued).
- General references to "insider selling pressure" and "profitability
  concerns" (net margin still negative despite a recent EPS beat) are
  background/structural, not a dated event for 10-01.
- A genuinely recent, but non-negative, item: an AI content-licensing
  partnership with Meta Platforms — described as a positive development,
  not a reason for the stock to fall.
- One source frames this as a continuation of an existing ~20% monthly
  decline rather than a fresh trigger.
No earnings release, guidance change, lawsuit, executive departure, or
other dated company-specific negative event was found tied to 2026-10-01.

## Price reaction (verified via scripts/alpaca_client.py)
- 2026-09-30 close: $10.81
- 2026-10-01 close: $9.875 (**-8.65%**, matches the task's -8.70% closely)
- 2026-10-02 (today, partial session): opened $10.01, low $9.345, last
  $9.495 — the decline is continuing (**-3.8% more today**), not
  stabilizing. Two straight down days with no sign of a bounce.

## Sentiment
Bearish and already-established before this move, not a surprise shift:
MarketBeat's aggregate rating is "Sell," Weiss Ratings maintains "Sell,"
and the recent WSZ downgrade (9/19) to Hold was itself already a step
down. TradingView's aggregated technical consensus (NYSE:NMAX):
**SELL (4 buy / 13 sell / 9 neutral)** — consistent with, not
contradicting, the fundamental picture. No credible bullish framing was
found anywhere in the search results for this specific move.

## Risks
- No documented dated catalyst exists for this exact drop — per
  research.md step 4, that alone caps this at PASS regardless of the
  negative tone, since there is nothing concrete to log as "the
  catalyst," only a continuation of an existing bearish drift.
- Real, if pre-existing, negative fundamentals: negative net margin
  despite a recent quarterly EPS beat, ongoing insider selling, elevated
  short interest (~10.17% of float as of mid-September) — all background
  risk, not new information today.
- The continuing slide into 10-02 (no stabilization) argues against any
  "oversold bounce" read if this ticker is revisited soon.

## Sources
- https://www.marketbeat.com/instant-alerts/price-newsmax-nyse-nmax-stock-falls-51-heres-why-2026-10-01/
- https://www.gurufocus.com/news/2911086/newsmax-nmax-sees-significant-decline-as-shares-drop-nmax-stock-news
- https://finance.yahoo.com/news/newsmax-nmax-evaluating-valuation-following-111856485.html
- https://www.marketbeat.com/instant-alerts/analyst-newsmax-nyse-nmax-downgraded-by-wall-street-zen-to-hold-2026-09-19/ (dated 2026-09-19)
- https://www.marketbeat.com/stocks/NYSE/NMAX/short-interest/
- scripts/alpaca_client.py live pull (get_historical_bars, NMAX, 2026-09-28 to 2026-10-02) — authoritative OHLCV
- scripts/tradingview_client.py live pull (NYSE:NMAX technical-rating summary)

## Verdict
PASS (no real, dated, company-specific catalyst found for this move —
the cited negative analyst action is 12 days stale, and the rest is
general bearish sentiment/structural weakness rather than a fresh
trigger. Per research.md step 4, no documented catalyst means PASS.
The continuing slide into today argues this is drift, not a
dip-worth-reconsidering.)

## Confidence
medium
