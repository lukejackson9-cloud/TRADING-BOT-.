# Mortgage insurer / mortgage REIT cooling-off cluster — 2026-10-01 (compact note, lessons.md #3)

Covers 6 same-session movers from `screen_market_movers('2026-09-30',
'2026-09-29')`, all down 6.5-8.5% on 2026-09-30: MTG, ESNT, NMIH, BXMT,
CIM, NLY.

## Step 0: prior context
No prior trade_ledger.md entries for any of these 6 tickers (checked via
grep across the ledger — first appearance for all). No watchlist.txt
EARNINGS pre-catalyst tags apply. lessons.md #3 (sector-wide moves
masquerading as independent opportunities) is the directly relevant
pattern and is exactly what this note tests for before writing anything
up as an individual opportunity.

## Identity verification (ticker collision check)
- **MTG** = MGIC Investment Corporation (NYSE), Milwaukee-based private
  mortgage insurer, founded 1957. Confirmed, no collision.
- **ESNT** = Essent Group Ltd (NYSE), Bermuda-holding-company private
  mortgage insurer (main subsidiary Essent Guaranty, Radnor PA), founded
  2008. Confirmed, no collision.
- **NMIH** = NMI Holdings, Inc. (NASDAQ), private mortgage guaranty
  insurer via National Mortgage Insurance Corporation. Confirmed, no
  collision.
- **BXMT** = Blackstone Mortgage Trust Inc (NYSE, Class A), externally
  managed commercial real estate finance REIT (senior loans, CRE debt).
  Confirmed, no collision.
- **CIM** = Chimera Investment Corporation (NYSE), residential mortgage
  REIT. Confirmed, no collision.
- **NLY** = Annaly Capital Management, Inc. (NYSE), diversified mortgage
  REIT (residential + commercial agency/non-agency assets). Confirmed,
  no collision.

## Cluster identification — this is ONE sector-wide macro move, not 6
independent stories
Explicitly checked per lessons.md #3 before researching each name
individually, and the answer is unambiguous:

- **Root macro driver**: the 10-year Treasury yield spiked sharply
  through late September 2026 — 5.27-5.29% by 2026-09-30, its largest
  quarterly surge since 1994, driven by inflation concerns tied to
  energy prices from the Iran/Ukraine conflicts. The average 30-year
  fixed mortgage rate rose to ~7.6% the same week, its highest level
  since late 2023.
- **Mechanism for the mortgage insurers (MTG, ESNT, NMIH)**: higher
  mortgage rates -> weaker housing demand + elevated default-risk
  concerns, directly pressuring private mortgage insurers' forward
  volume and credit-loss assumptions. Compounding this on the exact same
  date: updated FHFA/GSE Private Mortgage Insurer Eligibility
  Requirements (PMIERs) became fully effective 2026-09-30, tightening
  capital/eligibility standards for PMI providers — a real, dated,
  sector-specific regulatory event, but one that hits all PMI
  underwriters (MTG, ESNT, NMIH, plus Radian/Enact/Stewart, all reported
  down the same session per WebSearch) identically, not any one of them
  specifically.
- **Mechanism for the mortgage REITs (BXMT, CIM, NLY)**: these are
  leveraged, rate-sensitive vehicles (agency/non-agency MBS and CRE debt
  portfolios) whose book value and financing costs move inversely with
  rate spikes — the same Treasury-yield surge directly pressures all
  three via book-value and spread compression, independent of any
  company-specific news. BXMT's stock additionally sits near a 52-week
  low off an already-known Q2 EPS miss ($0.31 vs. $0.41 est.) — stale,
  prior-quarter news, not a fresh 09-30 catalyst.
- **Cross-checked explicitly for a discrete single-company event tying
  the whole cluster together**: none found for any of the 6. Every
  source frames these as "sector pressure" / "sector-wide mortgage
  insurer weakness" / "industry headwinds," consistent across
  gurufocus, Seeking Alpha, and StockStory coverage, and explicitly names
  peers outside this list (Radian, Enact, Stewart Information Services)
  moving the same direction the same day.
- NMIH's decline is also a **continuation, not a fresh one-day event**:
  this was its twelfth consecutive down session per WebSearch — a
  prolonged downtrend overlapping with, but predating, 09-30's broader
  sector move.

This is the textbook case lessons.md #3 exists for: 6 same-sector,
same-session movers in the same direction, with a clean shared causal
chain (one macro rate shock, amplified for the insurers by one shared
regulatory date) and no independent company-specific story found for any
of the 6.

## Per-ticker notes (compact — see cluster-wide verdict below)
- **MTG**: -8.53% ($28.25 -> $25.84). No company-specific news found
  beyond the sector/PMIERs story above.
- **ESNT**: -8.43% ($63.24 -> $57.91). No company-specific news found
  beyond the sector/PMIERs story above.
- **NMIH**: -8.37% ($40.73 -> $37.32). 12th consecutive down session; no
  company-specific news found beyond the sector/PMIERs story above.
- **BXMT**: -6.99% ($12.31 -> $11.45), new 52-week low. Only
  company-specific fact found is a Q2 EPS miss that is already stale
  (prior quarter, not a 09-30 event).
- **CIM**: -6.57% ($10.20 -> $9.53). No company-specific news found
  beyond the rate-driven REIT mechanism above.
- **NLY**: -7.04% ($20.32 -> $18.89). No company-specific news found
  beyond the rate-driven REIT mechanism above.

## Sentiment
Bearish across the cluster, macro/regulatory-driven rather than
idiosyncratic. No bull case independent of "rates stop rising" exists for
any of the 6 based on what was found.

## Risks
- This project is long-only with no edge on a further-rates-up scenario;
  a PASS here is not a signal to short.
- If the 10-year yield keeps climbing, PMIERs-driven and
  book-value-driven pressure on this whole cluster plausibly continues
  rather than mean-reverts quickly — not treated as a dip-buy setup.
- Per CLAUDE.md's Hard Risk Rules, if any of these 6 ever individually
  reached CANDIDATE on a future, clearly idiosyncratic catalyst, it
  would still need an explicit `correlation_flag` against the other 5 —
  they are one correlated bet (rate exposure + PMI-regulatory exposure),
  not six independent positions.

## Sources
- https://www.gurufocus.com/news/9104373/mgic-investment-corp-mtg-shares-drop-9-amid-sector-pressure-on-september-30-2026
- https://www.gurufocus.com/news/9104448/nmi-holdings-nmih-shares-slide-837-amid-industry-headwinds-and-prolonged-downtrend
- https://finance.yahoo.com/real-estate/articles/nmi-holdings-mgic-investment-essent-002113447.html
- https://seekingalpha.com/news/4648780-mgic-investment-corp-drops-9-amid-sector-wide-mortgage-insurer-weakness
- https://www.gurufocus.com/news/9104359/essent-group-esnt-shares-drop-over-8-amid-rising-interest-rate-concerns
- https://seekingalpha.com/news/4648794-nmi-holdings-retreats-8-extends-slide-amid-sector-weakness
- https://www.marketbeat.com/instant-alerts/price-blackstone-mortgage-trust-nyse-bxmt-stock-falls-48-heres-why-2026-09-30/
- https://www.investing.com/news/company-news/blackstone-mortgage-trust-stock-hits-52week-low-at-1147-usd-93CH-4925785
- https://finance.yahoo.com/markets/stocks/articles/blackstone-mortgage-trust-bxmt-stock-looks-expensive-after-a-25-slide-041604219.html
- https://www.housingwire.com/articles/fhfa-updates-capital-requirements-for-private-mortgage-insurers/
- https://www.fhfa.gov/sites/default/files/2024-05/Draft-PMIERs.pdf
- https://www.washingtonpost.com/business/2026/09/23/10-year-treasury-yield-rose-wednesday-its-highest-level-nearly-two-decades/
- https://wrenews.com/10-year-treasury-yield-5-27-mortgage-rates-september-2026/
- https://www.nbcnews.com/business/economy/mortgage-rates-treasury-yields-markets-rcna600894

## Verdict (applies to all 6 members listed above)
PASS for all six — this is one correlated sector/macro move (Treasury
yield spike, amplified for the insurers by a same-day PMIERs capital-
standard update), not 6 independent company-specific opportunities. No
company-specific dated catalyst was found for any individual name beyond
the shared macro/regulatory story and (for NMIH) a pre-existing 12-day
downtrend. A matching mechanical TA/ICT signal, if any fired on these
names, is not treated as adding confidence per CLAUDE.md.

## Confidence
high (the sector-wide framing is well-corroborated across multiple
independent sources for both sub-groups — insurers and REITs — and the
macro driver, rate levels, and PMIERs date are all independently
verifiable facts, not a single source's interpretation).
