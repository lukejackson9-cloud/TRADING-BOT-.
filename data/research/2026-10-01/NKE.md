# NKE — 2026-10-01

## Step 0: prior context
No prior entry for NKE in /data/journal/trade_ledger.md (checked both the
full-detail council section and the compact appendix table) and no
NKE-specific mention in /data/journal/lessons.md — this is genuinely the
ticker's first appearance in the project's memory. The only existing
record is config/watchlist.txt's pre-catalyst line ("NKE # EARNINGS
2026-10-01 -- pre-catalyst watch, not yet a candidate"), which was never
a verdict, just a flag to come back today. Per research.md's rule, now
that the earnings date has passed, this gets a fresh, uncapped evaluation
of the actual reaction — the pre-catalyst tag no longer applies.

## Catalyst
Nike reported Q1 FY2027 earnings (quarter ended 2026-08-31) today,
2026-10-01, with the release landing right around/after the 4:00pm ET
close (regular-session trading on 10/1 itself was calm — see Price
reaction below — and the real move happened in the after-hours tape).

**Headline numbers**: EPS $0.48 vs. ~$0.4365-0.44 consensus (a real ~9-10%
beat). Revenue $11.21B vs. ~$11.32-11.33B consensus (a slight miss, -4.2%
to -4.3% YoY) — matches the exact figures given in the task brief. Gross
margin actually improved: 42.8%, +60bps YoY — the EPS beat is real
operating performance, not just a one-time item (contrast with Q4 FY26,
where the beat was almost entirely a one-time tariff-refund benefit).

**Where it gets worse — Greater China**: revenue fell 22% YoY to
~$1.18-1.2B (two independently-sourced figures agree on this; one earlier
search result said -26%, but that reading isn't corroborated elsewhere
and is set aside as the less-reliable one, per lessons.md #2's "verify
against a second source when they disagree" practice). More importantly,
Greater China segment EBIT came in around $250M vs. ~$310M expected — a
real **margin** miss in the region, not just a top-line one. This is a
sharp acceleration from Q4 FY26's already-bad -17% constant-currency
China decline reported back in June/July.

**FY2027 guidance, the actual reason for the selloff**: full-year revenue
guided to decline high-single-digits (worse than the Street had modeled),
and adjusted EPS guided to $1.15-$1.35 vs. ~$1.65 consensus — a guidance
cut on the order of 20-30% below what analysts were modeling for the
year. CFO commentary: margin improvement unlikely before fiscal Q2 2027.

**New structural news**: Nike announced "Pace," a multi-year
restructuring/cost-transformation plan targeting $2.5B in savings by
FY2031 — realigning into three geographies, modernizing the supply
chain, building a new campus in India, and reducing headcount, with
layoffs beginning in 2027. This adds a 15-cent EPS restructuring charge
to FY2027 itself, on top of the soft guidance above.

**Other segment detail**: North America wholesale +9% (a genuine bright
spot) but North America Nike Direct -6%. EMEA wholesale -1%, EMEA Nike
Direct -12%. Company-wide Nike Direct -8% reported/-9% constant-currency
(Nike Brand Digital -13%, Nike-owned stores -5%) — the direct-to-consumer
channel is weakening broadly, not just in China. Inventory is actually
down 3% to $7.8B (a genuine positive — no fresh inventory overhang).

## Price reaction (verified via scripts/alpaca_client.py, not just
WebSearch summaries)
WebSearch alone gave an inconsistent picture here — one source claimed
NKE was "up 0.82% to $35.69" this morning, others said "-3%," "-5.54% to
$33.20," and "-6.3% to $33.00" — a spread wide enough to trigger
lessons.md #2's rule (verify against authoritative OHLCV when sources
disagree on a load-bearing number). Pulled Alpaca's real 1-day and 5-min
bars directly:
- Prior close (2026-09-30): $35.38
- Regular-session close (2026-10-01, essentially pre-release): $35.06
  (-0.90% — the regular session itself was unremarkable; this is not a
  "stock popped 2% intraday then earnings tanked it" story, the whole
  move happened after the bell)
- Earnings dropped right at/just after the 4:00pm ET close: the stock
  gapped immediately to an after-hours low of $32.85 (-6.3% vs. the
  regular close, -7.2% vs. prior close) in the first ~15 minutes
- By the most recent print available (~4:56pm ET), it had stabilized
  higher, at $33.86 (-3.4% vs. regular close, -4.3% vs. prior close)
The earlier WebSearch figures weren't actually contradictory sources —
they were different snapshots of the same falling-then-stabilizing
after-hours tape (an early "-3%" headline, then a deeper "-5.5% to -6.3%"
mid-dip reading). The "+0.82%" figure appears to be a stale/mistimed read
and is discarded. Multiple outlets (Benzinga, FXStreet) independently
describe the post-earnings level as NKE's **lowest since 2013** — a
genuine ~12-year low, not headline exaggeration.

## Sentiment
Unambiguously bearish, and this was already the prevailing tone BEFORE
the print, not just a surprise reaction: Bank of America downgraded NKE
to Underperform the week of earnings, cutting its target to $30 from
$47; Piper Sandler cut to $38 (Neutral); Evercore ISI cut to $34 (In
Line); Barclays cut to $48 while keeping Overweight, explicitly framing
the turnaround as "margins before sales" and warning the path back to
growth "will not be linear." Pre-earnings consensus was already just
Hold, average target ~$43.75. TradingView's aggregated technical-rating
cross-check (scripts/tradingview_client.py, NYSE:NKE) came back SELL (1
buy / 15 sell / 10 neutral across ~26 indicators) — consistent with, not
contradicting, the fundamental read. There is no credible bull framing
in anything surfaced here: even outlets noting the EPS beat and
inventory discipline frame the quarter as a miss once guidance and China
are weighed in.

## Risks (for any future contrarian look, not a basis for today's verdict)
- The EPS beat and improved gross margin are real, and inventory
  discipline is genuinely better than a year ago — a stock already down
  to a 12-year low and already broadly expected to disappoint (multiple
  pre-earnings downgrades) could mechanically be closer to "bad news
  already priced in" than a name getting its first negative surprise.
  Not enough on its own to flip this to a buy case today, but worth
  remembering if NKE is revisited.
- China's segment EBIT miss (~$250M vs. ~$310M expected) is a genuine,
  dated, quantified deterioration, not vague sentiment — this project's
  own lessons.md #7 (a company's own repeat pattern is predictive) points
  toward continued China weakness being the base case, not a one-quarter
  blip, given Q4 FY26 already showed accelerating decline in the same
  direction.
- This project is long-only with no shorting capability (Hard Risk
  Rules) — none of the above risk detail converts into an actionable
  idea either way; it is logged for completeness and for a future
  research pass, not as grounds to act today.

## Sources
- https://www.gurufocus.com/news/9106342/nike-nke-q1-earnings-beat-eps-estimates-but-revenue-declines-dividend-sustainability-in-focus
- https://www.cnbc.com/2026/10/01/nike-nke-q1-2027-earnings.html
- https://247wallst.com/investing/2026/10/01/live-will-nike-crush-q1-earnings-tonight-after-a-2-intraday-pop/
- https://www.gurufocus.com/news/9106504/nike-nke-reports-disappointing-earnings-shares-drop-over-40-this-year
- https://investinglive.com/stocks/nike-beats-q1-profit-estimates-but-sees-fiscal-2027-revenue-falling-high-single-digits/
- https://www.tipranks.com/news/company-announcements/nike-announces-q1-results-and-pace-restructuring-plan
- https://finance.yahoo.com/markets/stocks/articles/nke-stock-slips-premarket-bofa-123222943.html
- https://finance.yahoo.com/markets/stocks/articles/nike-stock-focus-barclays-cuts-114951994.html
- https://finance.yahoo.com/markets/stocks/articles/nke-stock-focus-piper-sandler-130409571.html
- https://www.gurufocus.com/news/9106343/nike-nke-faces-sales-headwinds-in-china-and-ecommerce-shares-drop-after-q1-results
- https://www.fxstreet.com/news/nike-misses-revenue-consensus-shares-down-4-to-new-12-year-low-202610012115
- https://www.benzinga.com/markets/earnings/26/10/62124308/nike-stock-sinks-to-lowest-level-since-2013-after-q1-earnings
- https://www.investing.com/news/stock-market-news/nike-falls-as-revenue-miss-overshadows-earnings-beat-4928309
- markets.financialcontent.com stockstory recap (NKE Q3 CY2026 / Q1 FY27, sales-below-estimate framing)
- scripts/alpaca_client.py live pull (get_latest_trade, get_historical_bars 1Day and 5Min, NKE, 2026-09-28 through 2026-10-01) — authoritative price/volume data, not a WebSearch summary
- scripts/tradingview_client.py live pull (NYSE:NKE technical-rating summary)

## Verdict
PASS (real, dated, negative-leaning catalyst — an EPS beat overshadowed
by a revenue miss, FY2027 guidance cut well below consensus, an
accelerating Greater China deterioration at both the revenue and segment-
margin level, and a new restructuring/layoffs plan; stock gapped down to
a ~12-year low after the print and sentiment was already bearish going
in. This project only trades long and has no bullish catalyst to act on
here — not a dip-buy setup, no documented reversal thesis, nothing that
clears research.md's bar for CANDIDATE.)

## Confidence
high
