# PSKY — 2026-10-02

## Step 0: prior context
No entry for PSKY in /data/journal/trade_ledger.md or /data/journal/lessons.md
— first appearance of this ticker in the project's memory. However,
/data/research/2026-09-22/WBD.md (WATCH) directly concerns the other side
of the same transaction: Warner Bros. Discovery's acquisition by Paramount
Skydance. That note found WBD trading ~99% of its $31/share deal price
with no spread left (merger-arb shape, not a momentum setup) and flagged
the deal as still not formally closed. This is a genuinely different
ticker/thesis (PSKY is the acquirer financing the deal with new debt, not
the arb target), so it gets its own fresh evaluation, but the merger
timeline context from that note carries forward and is confirmed/updated
below.

## Identity check
Paramount Skydance Corporation (NASDAQ: PSKY, Class B) — the combined
Paramount/Skydance Media entity formed earlier in 2026, now in the
process of acquiring Warner Bros. Discovery. Confirmed real, large-cap
operating media company (Paramount Pictures, CBS, Nickelodeon,
Paramount+, Pluto TV), not a shell or ticker-collision name.

## Catalyst
Real, dated, and company-specific. On 2026-10-01, Paramount Skydance
priced and announced over **$41.4 billion in senior secured notes and
term-loan financing** (maturities out to 2066, coupons 6.30%–9.125%) to
fund the Warner Bros. Discovery acquisition — a debt package that by
itself exceeds PSKY's entire ~$10.77B market cap. This lands directly
inside the confirmed merger timeline: Paramount Skydance and WBD jointly
announced on 2026-09-30 that the merger is expected to **close October 6,
2026** (WBD shareholders to receive $31.00/share plus a small daily
accretion — ~$31.02/share if it closes exactly on schedule). Compounding
the news flow this week: PSKY's board authorized withdrawing its Class B
stock from Nasdaq and moving to the NYSE (trading ends on Nasdaq ~Oct 5,
begins on NYSE ~Oct 6), a 2-for-1 stock split scheduled before market
open Monday Oct 5, and a subsequent rename to "Skydance Corporation"
(new ticker SKYD) once the deal closes. None of this is rumor — all
confirmed via SEC 8-K filings and the companies' own press releases.

## Price reaction (verified via scripts/alpaca_client.py)
- 2026-09-30 close: $10.34
- 2026-10-01 close: $9.33 (**-9.77%**, matches the task's -9.58% figure
  closely — small variance is normal across data feeds, both describe
  the same real move)
- 2026-10-02 (today, partial session): opened $9.35, low $8.975, last
  $9.505 — a modest ~+1.9% bounce off yesterday's close, still well below
  pre-selloff levels. No sign of a sharp reversal.

## Sentiment
Bearish, and driven by credit/leverage concerns rather than doubt about
the deal closing. **S&P Global Ratings downgraded PSKY to "BB" from
"BB+"**, citing leverage near 7.6x EBITDA through 2027. Needham kept a
Hold, flagging post-synergy net debt above 4x EBITDA as its main concern.
Citizens is the lone holdout with a Market Outperform and $14 target.
TradingView's aggregated technical consensus (NASDAQ:PSKY):
**SELL (1 buy / 15 sell / 10 neutral)** — consistent with the fundamental
leverage concern, not contradicting it. General financial-media framing
("deal risks mount," "debt outweighs antitrust win") matches the
quantitative picture: this is a real, substantial negative catalyst, not
headline exaggeration.

## Risks
- **This project is long-only** (Hard Risk Rules — no shorting, no CFDs).
  A negative catalyst like this has no actionable bullish angle regardless
  of how real or well-sourced it is.
- Genuine complicating noise ahead: the Oct 5 stock split and Oct 5-6
  Nasdaq→NYSE listing transfer mean PSKY's price series will look
  discontinuous in the next few days — any future look at this ticker
  needs to account for the split before comparing prices across that date.
- Possible (low-confidence) contrarian angle for a future pass: the
  antitrust/regulatory side of the deal is now fully cleared (DOJ, FCC,
  state AG settlement per the 2026-09-22 WBD note) — the only live risk
  left is financing cost, which is now priced and known rather than an
  open unknown. Not enough to flip today's verdict, but worth noting if
  PSKY stabilizes post-close.
- Connects to, but does not change, the 09-22 WBD WATCH verdict: WBD
  itself remains a capped merger-arb trade near its deal price; this
  PSKY move is about the acquirer's own balance sheet, a separate risk.

## Sources
- https://www.gurufocus.com/news/9106540/paramount-skydance-psky-shares-drop-nearly-10-after-41b-debt-financing-announcement
- https://seekingalpha.com/news/4649569-paramount-skydance-falls-10-percent-amid-41b-debt-pricing-for-warner-bros-deal
- https://www.kucoin.com/news/flash/paramount-and-warner-bros-discovery-announce-expected-merger-closing-date-of-october-6-2026
- https://ir.wbd.com/news-and-events/financial-news/financial-news-details/2026/Paramount-Skydance-and-Warner-Bros--Discovery-Announce-Anticipated-Closing-Date-of-Paramount-Merger/default.aspx
- https://www.marketbeat.com/instant-alerts/split-paramount-skydance-shares-set-to-split-on-monday-october-5th-nasdaq-psky-2026-10-01/
- https://www.gurufocus.com/news/9098267/paramount-skydance-psky-to-transfer-listing-to-nyse-and-sets-warrant-distribution-record-date
- https://variety.com/2026/film/news/name-of-paramount-warner-bros-unveiled-skydance-1236893761/
- https://www.timothysykes.com/news/paramount-skydance-corporation-psky-news-2026_10_01/
- scripts/alpaca_client.py live pull (get_historical_bars, PSKY, 2026-09-28 to 2026-10-02) — authoritative OHLCV
- scripts/tradingview_client.py live pull (NASDAQ:PSKY technical-rating summary)

## Verdict
PASS (real, dated, well-sourced negative catalyst — a $41.4B debt
financing announcement that exceeds the company's own market cap,
immediately followed by an S&P downgrade, tied to a confirmed Oct 6
merger close. This project is long-only with no shorting capability; a
negative catalyst, however real, is not actionable here.)

## Confidence
high
