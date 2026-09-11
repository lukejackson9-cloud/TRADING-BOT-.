# RACC — 2026-09-08

## Catalyst
**Insufficient/unreliable information — the price move itself could not be
verified.** The brief for today states RACC fell -7.5% to $11.44 on the
2026-09-03→09-04 session. Multiple independent live sources checked
during this research (stockanalysis.com, TradingView, Robinhood, via
WebSearch) instead show NASDAQ:RACC (Research Alliance Corporation III, a
SPAC in the process of merging with Oak Hill Bio/OHB Pediatrics) trading
in the **$24-25 range** in this same general timeframe — e.g. "$24.70,
+5.11%" and "$24.45, -3.23% in the past 24 hours," consistent with an
all-time high of $25.74 on 2026-08-07 and a 52-week low around $10-10.21
set back on 2026-05-20 (its IPO). No source found any RACC print near
$11-12 in September 2026, and no news turned up of the OHB Pediatrics deal
being terminated, a mass redemption, or any other event that would cut the
stock roughly in half from its recent trading range — the merger
(announced 2026-07-26, ~$160M base equity value + SAFEs, expected to close
H2 2026 as "Oak Hill Bio, Inc.") appears to be proceeding normally per the
latest SEC filings.

This is not a new problem for this ticker: this project's watchlist
already flagged a RACC data failure on 2026-09-03 ("screener's -37.4% move
could not be verified against any source (actual range $24-25)"). Today's
figure has the same shape — a large, specific-looking move that doesn't
reconcile with any live source — so per that same standard this is
treated as another unverifiable screener read, not confirmed fact.

Two further wrinkles worth logging, not treated as resolving the
discrepancy: (1) RACC is a genuinely ambiguous ticker — NASDAQ:RACC
(Research Alliance Corp III, the one a whole-US-market screener like
Massive.com would return) is a different company from EGX:RACC (Raya
Contact Center, an Egyptian call-center company trading in EGP, recently
~10.19-10.37 EGP with a 52-week range of 6.75-12.14 EGP) — if $11.44 got
attached to this ticker via a currency or exchange mix-up, that's a
plausible mechanical explanation, but not one this research can confirm.
(2) A TradingView technical-consensus pull (step 1b, live 2026-09-08) for
NASDAQ:RACC came back SELL (7 buy / 11 sell / 4 neutral) — but since that
query resolves against TradingView's live price for the real security
(likely near the $24-25 range other sources show), it says nothing about
whatever event supposedly happened at $11.44, and isn't treated as
evidence either way for this ticker's -7.5% move.

## Sentiment
No sentiment call can be responsibly made — the underlying premise (a
-7.5% move to $11.44) isn't supported by any source, so there's no move to
have a documented catalyst or sentiment about.

## Risks
- Screener/data-source reliability: this is the second unverified/
  conflicting RACC read from Massive.com's whole-market feed in under a
  week (see 2026-09-03 watchlist entry) — worth a note back to whoever
  maintains that data pipeline that this specific ticker (or a ticker
  colliding with it) may need special handling.
- SPAC pre-merger volatility (redemption dynamics, deal-completion risk)
  is real for NASDAQ:RACC generally, just not evidenced as the cause here.
- If a trade were ever proposed on unverified pricing, sizing and stop-
  loss/take-profit logic would be built on numbers that may not exist.

## Sources
- [Research Alliance Corporation III (RACC) Stock Price & Overview — stockanalysis.com](https://stockanalysis.com/stocks/racc/)
- [RACC Stock Price and Chart — NASDAQ:RACC — TradingView](https://www.tradingview.com/symbols/NASDAQ-RACC/)
- [Research Alliance Corp III: RACC Stock Price Quote & News — Robinhood](https://robinhood.com/us/en/stocks/RACC/)
- [Research Alliance to Acquire OHB Pediatrics in Stock Deal Valued at $160 Million Plus SAFEs — TradingView News](https://www.tradingview.com/news/tradingview:8da7ba941d7b7:0-research-alliance-to-acquire-ohb-pediatrics-in-stock-deal-valued-at-160-million-plus-safes/)
- [Raya Contact Center Co Stock Price Today — EGX:RACC — Investing.com](https://www.investing.com/equities/raya-contact-center)
- scripts/tradingview_client.py get_rating("RACC","NASDAQ") — live 2026-09-08

## Verdict
PASS — insufficient/unverifiable information. The stated price move
cannot be corroborated by any source found, echoing (not just resembling)
a data-reliability problem this project already flagged for this exact
ticker on 2026-09-03. Not treating an unconfirmed number as a real
catalyst.

## Confidence
low
