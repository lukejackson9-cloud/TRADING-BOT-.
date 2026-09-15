# ABBV — Correlation & Macro specialist report — 2026-09-15

## 1. Sector-wide peer movement (09-09 through 09-15)
**A genuine, broad healthcare/pharma sector rally is underway in this exact
window — this materially weakens how independent ABBV's move is from a
pure sector tailwind, even though the company-specific catalysts
research.md found are real.**

- XLV (Health Care Select Sector SPDR) was **up 3.3% over the past 5
  trading sessions**, making healthcare the **top-performing S&P 500
  sector for the week** — versus the S&P 500 itself up less than 0.5% the
  same week. (Yahoo Finance, "Healthcare Stocks Are on Fire")
- XBI (biotech) is near 52-week highs, up ~8.9% trailing 30 days / ~26%
  trailing quarter, driven by rate-cut expectations, FDA approvals, and
  record M&A deal volume (nearly 70 deals in 2025, 20 drug-developer IPOs
  in 2026 already vs. 11 all of last year). (Yahoo Finance / BioPharma
  Dive)
- A named peer catalyst landed in the SAME window: **Merck (MRK) rallied
  on a Phase 3 lung-cancer drug cutting tumor-progression risk by 65%**
  — i.e. another large pharma name got a positive trial readout the same
  week, not an ABBV-only event.
- Broader narrative found repeatedly across sources: **rotation out of
  expensive tech/AI names and into defensive healthcare** — improving
  earnings visibility, attractive relative valuations, rate-cut
  sensitivity — is cited as a sector-wide driver independent of any
  single company's news.

**Read for council**: ABBV's catalysts (LUNA trial, Apogee close, HSBC PT
raise, MS conference appearance) are real, dated, and company-specific —
not fabricated or imagined. But they are landing inside a week where
large-cap pharma/biotech broadly outperformed for sector-level reasons
(rotation, M&A wave, rate-cut expectations, a peer's own positive trial
data). Some portion of ABBV's +3.8% since 09-09 is plausibly sector beta,
not 100% attributable to ABBV-specific news — same pattern as the
XP/RUN and KLAC/ALAB/NBIS clusters flagged in lessons.md #3. This doesn't
mean the catalyst is fake; it means "the whole sector moved" should
temper how much independent weight the bull case puts on stock-specific
causation.

## 2. Macro-news-day check (informational only)
Checked `scripts/backtest_ict.py`'s `FOMC_DATES`, `CPI_DATES`, and
`_is_nfp_day()` directly for every date 2026-09-09 through 2026-09-15:

| Date | FOMC | CPI | NFP |
|---|---|---|---|
| 2026-09-09 | no | no | no |
| 2026-09-10 | no | no | no |
| 2026-09-11 | no | no | no |
| 2026-09-12 | no | no | no |
| 2026-09-13 | no | no | no |
| 2026-09-14 | no | no | no |
| 2026-09-15 | no | no | no |

**No verified macro-news day in this window.** Per lessons.md, this
finding would only ever be a minor, inconsistent modifier even if
present — it's absent here, so it's a non-factor either way, not a
tiebreaker in ABBV's favor or against it.

## 3. Portfolio overlap check
- `/data/pending_trades.json`: one entry total (`2026-09-02-GTLB-01`,
  ticker GTLB, software/AI-competition theme — not pharma/biotech).
  Status: `WITHDRAWN_COUNCIL_DOWNGRADE` — terminal, not an open idea. No
  non-terminal entries exist at all.
- `/data/positions.json`: empty (`{}`) — no positions on file.

**No open pending idea or held position overlaps with ABBV's
pharma/healthcare theme** — there is simply nothing else on the book to
be correlated with.

## correlation_flag
`"none"` — no overlapping open pending idea or position exists in
/data/pending_trades.json or /data/positions.json for sizing purposes.
(Note for the moderator/bull-bear agents: this is distinct from finding
1 above — there IS a real sector-wide rally coinciding with ABBV's move,
which bears on how independently to weight ABBV's specific catalysts,
even though it doesn't trigger a portfolio-exposure correlation_flag
since nothing else pharma/healthcare is currently open.)
