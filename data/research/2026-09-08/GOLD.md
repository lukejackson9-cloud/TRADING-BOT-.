# GOLD — 2026-09-08

## Catalyst
**Data-accuracy flag first, before the catalyst discussion:** the ticker
**GOLD does not belong to Barrick anymore.** Barrick Gold Corporation
renamed to Barrick Mining Corporation and changed its NYSE ticker from
"GOLD" to "B" effective 2025-05-09 (confirmed via Barrick's own investor-
relations press releases). Barrick/Barrick Mining now trades as NYSE:B,
around $44-46 as of early September 2026 — coincidentally close to the
$46.13 price given for this ticker, which is likely why the two got
conflated, but they are not the same instrument.

Since December 2025, NYSE:GOLD belongs to **Gold.com, Inc.** (formerly
A-Mark Precious Metals) — a precious-metals retail/dealer platform
(JM Bullion, Stack's Bowers Galleries, Goldline, Monex, Sunshine Mint),
not a gold miner. This note researches the company that actually trades
under GOLD today, since that's what any trade on this ticker would
actually execute against.

With that correction made, the catalyst for GOLD's (Gold.com's) move: the
company reported **fiscal Q4/FY2026 results on 2026-09-02** — revenue
+99% YoY to $5.01B (though down 52% sequentially and below the $5.67B
consensus), FY2026 revenue +132% YoY to $25.51B, FY EPS of $3.02 (vs
$0.71 prior year), FY EBITDA +179% to $179.8M. The board also declared a
**special cash dividend of $1.00/share** (on top of the regular $0.20)
same day, payable 2026-09-28 to holders of record 2026-09-16. The
09-03→09-04 pop (+11.2% to $46.13) reads as a delayed/continued market
reaction to this 09-02 print and dividend rather than a same-day fresh
trigger.

Cutting against that: two analysts trimmed price targets the same week —
Canaccord $70→$65 (kept Buy) and Northland $57→$55 (kept Outperform) —
both citing the sequential/consensus revenue miss, and the article
framing was that the earnings reaction was "mixed" and "tempered."
Separately, spot gold itself slipped below $4,400/oz around this period on
rate-hike expectations, a macro headwind for a precious-metals-linked
business, not a tailwind.

## Sentiment
Mixed-to-bullish, but genuinely conflicted: real, large YoY profit/EBITDA
growth and a shareholder-friendly special dividend on one hand; a revenue
miss vs. consensus, two same-week price-target cuts, and a softer gold-
price backdrop on the other. TradingView technical-consensus cross-check
(scripts/tradingview_client.py, step 1b, live 2026-09-08): **STRONG_BUY**
(16 buy / 1 sell / 9 neutral) — a notably strong technical read that
disagrees with the more cautious analyst commentary. Per research.md,
that disagreement is a prompt to look harder, not a tiebreaker; the
fundamental catalyst here is real, but it isn't unambiguous.

## Risks
- **Identity/ticker risk**: if this were ever proposed as a trade, the
  proposal must be unambiguous that it's Gold.com, Inc. (retail precious-
  metals platform), not Barrick — a mix-up here would size and reason
  about completely the wrong business.
- Revenue missed consensus and fell sharply sequentially (-52% QoQ); two
  analysts cut targets the same week the "bullish" catalyst printed.
- Gold spot price itself is a headwind right now (sub-$4,400, pressured by
  rate-hike expectations) — this is a business whose economics lean on
  precious-metals prices and volumes.
- The catalyst (09-02 earnings + dividend) is now several days old by the
  time this research lands — most of an efficient-market reaction to it
  should already be reflected in the price, raising "already priced in"
  risk for a fresh entry now.
- Company was already one of 2026's biggest gold-sector winners (~90% YTD
  through Feb per one source) — chasing further upside after a large prior
  run adds valuation risk.

## Sources
- [Barrick Rebrand As Barrick Mining Corporation, NYSE Ticker To Change From 'GOLD' To 'B' — Nasdaq](https://www.nasdaq.com/articles/barrick-rebrand-barrick-mining-corporation-nyse-ticker-change-gold-b)
- [Gold.com to Begin Trading on the NYSE Under Ticker Symbol "GOLD"](https://ir.gold.com/news-events/press-releases/detail/212/gold-com-to-begin-trading-on-the-new-york-stock-exchange-under-ticker-symbol-gold)
- [Gold.com Reports Fiscal Fourth Quarter and Full Year 2026 Results](https://www.globenewswire.com/news-release/2026/09/02/3355495/31746/en/gold-com-reports-fiscal-fourth-quarter-and-full-year-2026-results.html)
- [Gold.com FY 2026 Earnings: $3.02 EPS, $1 Dividend — StockTitan](https://www.stocktitan.net/news/GOLD/gold-com-reports-fiscal-fourth-quarter-and-full-year-2026-z10bgmufg8f3.html)
- [Gold.com (GOLD) Stock News & Updates — StockTitan](https://www.stocktitan.net/news/GOLD/) (Canaccord/Northland target cuts, 09-03)
- scripts/tradingview_client.py get_rating("GOLD","NYSE") — live 2026-09-08

## Verdict
WATCH — a real, dated, company-specific catalyst exists (strong FY2026
earnings + special dividend), but it's several days stale by now, the
market's own reaction to it was mixed (target cuts, revenue miss), and
the macro gold-price backdrop is currently a headwind. Also flagging for
the record: this is **not** Barrick Gold — any future proposal on this
ticker must be sized and reasoned about as Gold.com, Inc.

## Confidence
medium
