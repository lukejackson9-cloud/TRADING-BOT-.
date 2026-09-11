# REPL — 2026-09-11

## Catalyst
No prior trade_ledger.md entry for REPL. No directly relevant lessons.md
pattern found for this specific setup, though #2 (verify moves against
OHLCV) and #6 (recycled narrative is a red flag, not a fresh catalyst)
are both relevant to how this note was checked.

REPL fell -8.37% on the 2026-09-10 session (confirmed via Alpaca daily
bars: 2026-09-09 close $14.43 -> 2026-09-10 close $13.225 = -8.35%,
matching the reported figure). Replimune's actual FDA history is
well-documented but NOT fresh: RP1 (now approved as Tudriqev) received a
Complete Response Letter in an earlier round, then won a favorable 10-3
FDA advisory committee vote in late July 2026, and was ultimately granted
accelerated approval alongside Opdivo for advanced melanoma before
September — all of that is old news relative to this specific
09-10 drop, not a fresh catalyst dated 09-10 or 09-11.
Searching specifically for what happened on/around 09-10 turned up no
new company announcement, earnings release, or regulatory update dated
that day. What IS dated close to this window: a securities class-action
lawsuit (covering an October 2025-April 2026 purchase period, tied to the
ORIGINAL Complete Response Letter and alleged misstatements about the
BLA resubmission) had lead-plaintiff-deadline reminder press releases
circulating 2026-09-08 (Levi & Korsinsky, SBS Law, "SueWallSt") — but
these are law-firm solicitation releases about litigation from a much
earlier event, not a new development, and they don't obviously explain a
same-week price move on their own. A $150M common stock + pre-funded
warrant offering priced back in August 2026 is dilution overhang that
predates this move by roughly a month. No fresh, dated,
company-specific catalyst was found for the 09-10 decline specifically.

## Sentiment
Bearish/negative drift with no identified fresh trigger. Analyst opinion
is split and stale either direction: Piper upgraded to Overweight in
July 2026 on approval odds (since realized), J.P. Morgan has reaffirmed
Buy, but Barclays and Wedbush hold price targets as low as $3-4,
reflecting the stock's ~84% cumulative decline from its pre-CRL high.
TradingView's aggregated technical rating (get_rating) is SELL (7 buy /
10 sell / 9 neutral). Stock continued down to $12.94 on 2026-09-11,
extending the slide rather than bouncing.

## Risks
- No dated, company-specific catalyst was found for this specific move —
  per this project's own rule, that alone should cap this well below
  CANDIDATE.
- Active securities class action (Complete Response Letter-era
  misstatement allegations) is an ongoing overhang, unresolved, with a
  lead-plaintiff deadline of 2026-10-05 — real but not new.
  info this session found.
- Recent $150M dilutive equity offering (Aug 2026) is a real structural
  headwind on the share count, separate from the price action being
  researched here.
- Extreme historical volatility (a fallen-84%-from-highs biotech with a
  documented FDA rejection-then-approval whipsaw) means low-conviction
  moves in either direction are common and hard to read as signal.
- Insider selling reported as recently as May 2026 (CFO), adding to a
  generally negative insider-sentiment read, though modest in size.

## Sources
- [Replimune Group (NASDAQ:REPL) Shares Down 6.9% - Here's Why](https://www.marketbeat.com/instant-alerts/price-replimune-group-nasdaq-repl-shares-down-69-heres-why-2026-09-10/)
- [Replimune Announces Favorable Outcome of FDA's Cellular, Tissue, and Gene Therapies Advisory Committee Meeting for RP1](https://ir.replimune.com/news-releases/news-release-details/replimune-announces-favorable-outcome-fdas-cellular-tissue-and)
- [Replimune rebounds to win FDA approval of melanoma drug - BioPharma Dive](https://www.biopharmadive.com/news/replimune-tudriqev-fda-approve-melanoma-rp1/827226/)
- [REPL Deadline Alert: Levi & Korsinsky Securities Class Action Deadline October 5, 2026](https://www.prnewswire.com/news-releases/repl-deadline-alert-levi--korsinsky-reminds-replimune-group-inc-repl-investors-of-securities-class-action-deadline-on-october-5-2026-302873300.html)
- [Replimune Prices $150 Million Common Stock and Pre-Funded Warrant Offering](https://www.quiverquant.com/news/Replimune+Prices+$150+Million+Common+Stock+and+Pre-Funded+Warrant+Offering)
- Alpaca daily bars (scripts/alpaca_client.py), 2026-09-08 to 2026-09-11, used to verify the exact move
- TradingView aggregated rating (scripts/tradingview_client.py get_rating), checked 2026-09-11

## Verdict
PASS

## Confidence
medium
