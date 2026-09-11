# SMR — 2026-09-11

## Catalyst
**Prior context (checked first, per instructions):** trade_ledger.md
already has a 2026-09-09 entry — "WATCH low confidence | real news but
pre-revenue story stock" — logged when SMR was UP +15.3% on real dated
AI-partnership/milestone news, flagged even then as "pre-revenue story
stock, brutal 1yr drawdown, possible AI-infra correlation with CRWV."
The ledger's own outcome column already marked that call "Validated —
-6% the day after (AI-partnership bump didn't hold)," i.e. the
09-09 pop had already faded by 09-10, before today's much larger move.
config/watchlist.txt has the same 09-09 entry plus a fresh 09-11 line
flagging today's "-15.7% intraday move today per FMP most-active, on top
of the existing 09-09 WATCH low-confidence entry -- re-checking given the
escalation." lessons.md has no SMR-specific lesson yet, but #1 ("sell the
news"/overextension) and #7 (a company's own repeat pattern is
predictive) are both directly relevant: this is now the second sharp move
in three sessions on this ticker, first up then down, which itself echoes
#1's pattern of an unsustained pop.

**Today's specific driver (separate from 09-09's AI-partnership news, as
instructed):** UBS initiated/cut SMR to Sell from Neutral today
(2026-09-11) and slashed its price target to $6, implying further
downside from a level UBS itself now sees as ~40% overvalued. UBS's bear
case rests on three concrete points: (1) an estimated construction
timeline of 5+ years for NuScale's SMR technology to actually deliver
revenue-generating plants, (2) the absence of any firm, signed customer
commitments underpinning the AI-power narrative that drove the 09-09 pop,
and (3) a forecast ~$700M of cumulative cash burn from 2026-2028 against
Q2 revenue of just $75,000 (confirmed real — not a typo — against $1.9B
cash on hand). This is a genuine, dated, company-specific analyst action
tied to concrete financial modeling, not a vague sentiment shift.

**Verification note (lessons.md #2 applies):** several WebSearch article
headlines (Schaeffer's, 24/7 Wall St, Benzinga) described today's move as
"down 4-5%," which would UNDER-state the scale given in this task's
prompt (-15.7% intraday per FMP). Pulled Alpaca daily bars directly to
resolve this: 2026-09-10 close was $10.205; today's (09-11) bar shows
open $9.66 (already gapped down before the cash session even started, on
the UBS note), low $8.57, and a live quote around $8.61 as of this
research pass — i.e. roughly -15.6% from yesterday's close to the current
price, which matches the -15.7% figure in the prompt and is materially
worse than what most WebSearch article headlines captured (they appear
to have been published earlier in the session, before the stock fell
further intraday, or to be measuring from today's open rather than
yesterday's close). Treating the larger, OHLCV-confirmed number as
correct per the lesson's own guidance.

## Sentiment
Bearish, and getting more so intraday. This is a real, dated,
company-specific analyst action (not a sector-wide note — no other SMR-
peer names were reported moving on this specific UBS call, unlike CRWV's
09-09 pop which was explicitly sector-wide) directly attacking the
credibility of the very AI-partnership narrative that drove the 09-09
spike. TradingView's aggregated technical rating (get_rating) is
STRONG_SELL (1 buy / 16 sell / 9 neutral of ~26 indicators) — the most
lopsided reading of any of today's three tickers. Stock is down 28% YTD
and 70% over the last 12 months per today's coverage, consistent with the
"brutal 1yr drawdown" already noted in watchlist.txt on 09-09.

## Risks
- This is a downside/bearish catalyst, not a bullish one — nothing here
  supports a long entry; if anything it's confirmation that the 09-09
  bullish thesis (AI-partnership pop) may not hold up to scrutiny, per
  UBS's own point about the absence of firm customer commitments.
- Still a single sell-side note, weighted per lessons.md #5 below a
  company's own reported numbers — though UBS's argument leans heavily on
  NuScale's own reported financials (Q2 revenue $75K, cash position),
  which makes this a stronger-than-average analyst call, not a pure
  sentiment/momentum one.
- Pre-revenue story stock already flagged twice in this project's own
  records (09-09 ledger entry, 09-11 watchlist note) — this is now a
  repeat, escalating pattern on the same name in under a week, which
  per lessons.md #7 deserves real weight: two sharp moves in three
  sessions on a thin fundamental base is a volatility/story-stock pattern,
  not evidence of a tradeable edge either direction.
- No new information found today about the underlying AI-partnership/
  milestone story itself (positive or negative) — today's move is
  entirely an analyst reassessment of an existing narrative, not a new
  fact about NuScale's actual project execution.

## Sources
- [Nuscale Stock Slumps After Downgrade, Price Target Cut - Schaeffer's Investment Research](https://www.schaeffersresearch.com/content/news/2026/09/11/nuscale-stock-slumps-after-downgrade-price-target-cut)
- [NuScale Power Drops 5% as UBS Cuts to Sell on Timeline and Cash Burn, Oklo Slips - 24/7 Wall St.](https://247wallst.com/investing/2026/09/11/nuscale-power-drops-5-as-ubs-cuts-to-sell-on-timeline-and-cash-burn-oklo-slips/)
- [UBS Downgrades NuScale Power to Sell, Sees 40% Downside - Benzinga](https://www.benzinga.com/trading-ideas/movers/26/09/61736378/ubs-downgrades-nuscale-power-to-sell-sees-40-downside)
- data/journal/trade_ledger.md (09-09 SMR entry) and config/watchlist.txt (09-09 and 09-11 SMR lines) — prior in-project context
- Alpaca daily bars + live quote (scripts/alpaca_client.py), 2026-09-09 to 2026-09-11, used to verify the actual magnitude of today's move against conflicting WebSearch headlines
- TradingView aggregated rating (scripts/tradingview_client.py get_rating), checked 2026-09-11

## Verdict
PASS

## Confidence
medium
