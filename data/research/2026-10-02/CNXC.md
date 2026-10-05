# CNXC — 2026-10-02

## Step 0: prior context
No entry for CNXC in /data/journal/trade_ledger.md or
/data/journal/lessons.md — first appearance. Lessons.md #2 (WebSearch
summaries are unreliable for precise facts; verify against authoritative
OHLCV when sources disagree) applies directly and was the deciding factor
below — two WebSearch sources gave flatly contradictory framing for what
turned out to be the same underlying multi-day move.

## Identity check
Concentrix Corporation (NASDAQ: CNXC) — the real customer-experience/BPO
outsourcing company. Confirmed real, not a collision.

## Catalyst
Real and dated, but the price action around it is genuinely confusing
across sources — resolved below with authoritative OHLCV per lessons.md
#2. Concentrix reported fiscal Q3 2026 results (quarter ended 8/31/2026)
via 8-K on **2026-09-29**:
- Revenue $2,453.7M, down 1.2% YoY, **below** analyst estimates (a real
  miss).
- Non-GAAP diluted EPS $2.92, **up** 5.0% YoY and ~8.1% above consensus
  (a real beat).
- Record operating cash flow ($268.2M) and adjusted free cash flow
  ($218.3M); dividend raised to $0.37/share.
- Next-quarter revenue guidance of $2.44B, ~3.3% below estimates
  (disappointing).
- BofA Securities cut its price target to $29 from $30 (Hold) on
  **2026-10-01**, citing macro headwinds.
Two WebSearch sources described this same earnings event in opposite
terms — one headlined "stock drops 10%," another "CNXC rallies... record
operating cash flow" — which is exactly the kind of contradiction
lessons.md #2 flags as unreliable; resolved with real OHLCV below rather
than picking a side.

## Price reaction (verified via scripts/alpaca_client.py — the full
multi-day picture, not just the single day asked about)
- 2026-09-29 close (pre-earnings-reaction): $24.85
- 2026-09-30 close (earnings-reaction day): $24.96 — nets out almost
  flat, but masks a **huge intraday round trip**: low $22.70 (-8.7%
  intraday) recovering all the way back to roughly flat by the close.
  This is almost certainly the source of the "stock drops 10%" headlines
  — a real intraday plunge on the revenue miss that fully reversed
  same session.
- **2026-10-01 close: $27.00** (+8.2% from 9/30's close — this is the
  task's "mover," $24.95→$27.01) — a further, continued bounce the day
  *after* the earnings reaction, not the earnings reaction itself.
- **2026-10-02 (today, partial session): opened $27.00, last $24.925 —
  down -7.7% intraday, erasing almost the entire 10/1 gain.** This is a
  real, live, already-in-progress reversal confirmed by the same data
  source, not a guess.

## Sentiment
The full picture argues this is a whipsaw/overreaction unwind, not a
sustained bullish re-rating: an initial sharp (and reversed) intraday
plunge on the revenue miss, a one-day relief bounce on the EPS-beat
headline (the move being researched here), and then an immediate,
substantial giveback the very next session — while the one dated
post-earnings analyst action (BofA, 10/1) was a price-target **cut**, not
a raise. TradingView's aggregated technical consensus (NASDAQ:CNXC):
**SELL (2 buy / 16 sell / 8 neutral)** — the most lopsided bearish reading
of any ticker researched today, consistent with the reversal already
under way.

## Risks
- The 10/1 bounce being asked about here has already round-tripped by
  the time of this research pass (10/2) — treating it as a fresh,
  still-live opportunity would be chasing a move that's already fading,
  precisely the pattern lessons.md #1 warns about.
- Underlying fundamentals are mixed-to-negative, not positive: revenue
  miss, soft next-quarter guide, analyst price-target cut — none of which
  support the bull case the 10/1 bounce might otherwise suggest.
- If CNXC stabilizes after this reversal completes and the EPS-beat/
  margin-expansion/record-cash-flow story reasserts itself without
  further revenue deterioration, that would be a materially different
  setup worth a fresh look — not what the data shows as of this pass.

## Sources
- https://finance.yahoo.com/markets/stocks/articles/concentrix-nasdaq-cnxc-reports-sales-205327073.html
- https://marketchameleon.com/articles/b/2026/9/30/cnxc-q3-2026-results-record-operating-cash-flow-goodwill-impairment
- https://stockstory.org/us/stocks/nasdaq/cnxc/news/earnings/concentrix-nasdaqcnxc-reports-sales-below-analyst-estimates-in-q3-2026-earnings-stock-drops-10percent
- https://www.gurufocus.com/news/9103990/concentrix-corp-cnxc-q3-2026-earnings-call-highlights-margin-expansion-and-ai-momentum-offset-revenue-headwinds
- https://www.investing.com/equities/concentrix
- scripts/alpaca_client.py live pull (get_historical_bars, CNXC, 2026-09-28 to 2026-10-02) — authoritative OHLCV, the deciding evidence here
- scripts/tradingview_client.py live pull (NASDAQ:CNXC technical-rating summary)

## Verdict
PASS (the 10/1 "mover" is already reversing hard as of today, 10/2,
per live authoritative OHLCV — erasing almost the entire gain within one
session. The underlying earnings catalyst itself was mixed-to-negative
(revenue miss, soft guide, a same-week price-target cut), and the bounce
being asked about reads as a fading overreaction, not a fresh bullish
setup. This is a clean real-time confirmation of lessons.md #1's
"sell the news" pattern, not a counter-example.)

## Confidence
high
