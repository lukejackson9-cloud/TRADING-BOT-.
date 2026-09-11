# RELY — 2026-09-11

## Catalyst
No prior trade_ledger.md entry for RELY (first appearance in this project).
No directly relevant lessons.md pattern either, though #2 (verify moves
against OHLCV when sources disagree) and #5 (analyst actions are weaker
evidence than company fundamentals) both apply here.

RELY fell -8.89% on the 2026-09-10 session (confirmed via Alpaca daily
bars: 2026-09-09 close $24.07 -> 2026-09-10 close $21.935 = -8.87%,
matching the reported figure within rounding). The move was driven by a
JMP Securities price-target cut to $23 from $32 (a ~28% PT reduction),
while JMP kept its "Market Outperform" rating. JMP's three stated
concerns: (1) management's own commentary suggests Q3 guidance is
already accurate with no room for a beat-and-raise, and 2026 Street
revenue estimates may be too optimistic; (2) unanswered questions about
the unit economics, funding strategy, and credit risk of Remitly's new
lending products; (3) ongoing news flow about the downstream impact of
ICE immigration enforcement on remittance volumes, explicitly citing
Tricolor Holdings' recent bankruptcy as an analogous downstream effect.
This is a single sell-side note, not a company-issued guidance cut or
earnings miss — RELY has not reported since its Q2 beat-and-raise in
August.

## Sentiment
Bearish near-term. One firm cut its price target sharply while keeping a
bullish long-term rating, so this reads as "growth story intact, but no
near-term upside catalyst and real emerging risks" rather than a thesis
reversal. TradingView's aggregated technical rating (get_rating) is SELL
(4 buy / 15 sell / 7 neutral across ~26 indicators as of today),
consistent with continued near-term weakness. Stock closed 2026-09-11 at
$21.98, essentially flat vs. 09-10's close — no bounce, no further
breakdown either.

## Risks
- This is a single analyst's price-target cut, not a company-specific
  fundamental deterioration (no earnings miss, no management guidance
  cut) — per lessons.md #5, weight this lower than a company's own
  reported numbers.
- Immigration-enforcement/remittance-volume risk (ICE activity, Tricolor
  bankruptcy cited as an analog) is a real, dateable macro overhang for a
  remittance company but is speculative/forward-looking, not a confirmed
  RELY-specific data point yet.
- New lending products' credit risk and unit economics are explicitly
  called out as unresolved questions by the analyst who wrote the note —
  i.e., this is uncertainty, not a documented bad outcome.
- No fresh, dated, company-specific event (earnings, regulatory action,
  contract loss) underlies this move — it is entirely a reaction to one
  firm's interpretation of existing public information.
- This is a decline, not a bullish catalyst — there is no case here for
  a long entry on a fresh positive catalyst; the only way this becomes
  actionable is as a documented risk that has now been priced in, which
  is not what this project's momentum+catalyst strategy screens for.

## Sources
- [Why Remitly (RELY) Stock Is Falling Today](https://finance.yahoo.com/news/why-remitly-rely-stock-falling-154631263.html)
- [Remitly Global (NASDAQ:RELY) Stock Price Down 7.4% - Here's What Happened](https://www.marketbeat.com/instant-alerts/price-remitly-global-nasdaq-rely-stock-price-down-74-heres-what-happened-2026-09-10/)
- [Remitly Global stock price target lowered to $23 by JMP on headwinds](https://www.investing.com/news/analyst-ratings/remitly-global-stock-price-target-lowered-to-23-by-jmp-on-headwinds-93CH-4238123)
- Alpaca daily bars (scripts/alpaca_client.py), 2026-09-08 to 2026-09-11, used to verify the exact move
- TradingView aggregated rating (scripts/tradingview_client.py get_rating), checked 2026-09-11

## Verdict
PASS

## Confidence
medium
