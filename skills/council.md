# Skill: Council (scored, 3-12 month horizon)

**Rewritten 2026-09-12 on the user's explicit decision.** The previous
adversarial gate is preserved verbatim at `skills/council_shortterm_superseded.md`.
Read "Why this replaced a gate" before changing anything here.

Goal: given the day's shortlist, produce a **ranked conviction score** for a
**3-12 month** holding period. Not a pass/fail. This always produces a best
idea, including on days when every idea is mediocre.

## Why this replaced a gate (read before touching the scoring)
The old council downgraded 15 of 15 candidates. `counterfactual.py` graded
those downgrades as if bought anyway: **-1.71%/trade against a date-matched
market baseline of -1.71%** — identical. Rejecting everything is not skill,
it is an absence of measurement.

The cause was the decision rule, not the analysts: bull had to win on EVERY
point while bear needed ONE. Every company has a flaw, so "is this flawless?"
returns no by construction, regardless of truth. Adding more members to that
structure makes it stricter, not better — which is why this rewrite changes
the **aggregation** and only then the roles.

Each member now owns a **dimension** and scores it. Nobody argues a side and
**nobody has a veto.** A serious problem shows up as a low score that drags
the total, which is how a real analyst weighs a flaw — against the price —
rather than as a trapdoor.

## Horizon: 3-12 months. This changes what counts as evidence.
At two weeks the only question was "is this catalyst already priced in", and
`feature_ic.py` showed the price-derived features answering it carry no
information. Over 3-12 months the questions are about the business and the
price paid, and the evidence is filings, not charts.
- **Momentum and recent price action are NOT evidence here.** A name being
  up 12% this week is neither a reason to buy nor to avoid. Ignore it.
- A pending earnings date is still not a thesis, but at this horizon you are
  buying through several prints, so a single reaction matters far less.

## Inputs
Run `python scripts/fundamentals.py card {TICKER}` for each name. Whole-market
coverage via Massive; FMP's richer ratios exist only for its ~78-name set.
**Pace it — 5 requests/minute.** An empty result is a rate limit, never
"this company files nothing".
Read `data/journal/lessons.md` and `trade_ledger.md` for base rates first, as
context, never as an override.

## The four members
Each scores **1-5** and must cite a **specific number or a dated, sourced
fact**. A score with no figure behind it is not a score. Where the data is
missing, say so and score 3 — never guess, and never let a gap read as good
news.

**1. Business quality** — is this a good business?
Margins and their direction, return on equity/assets, revenue growth on a
like-for-like quarter, whether the advantage is durable.
`5` durable and improving · `3` ordinary or mixed · `1` deteriorating

**2. Valuation** — is the price sane for what you get?
P/E, price/sales, price/book, cash-flow and earnings yield. Owns the verdict
"good company, bad price", which is the most common reason a quality name is
still a poor buy.
`5` cheap for the quality · `3` fair · `1` priced for perfection

**3. Financial health** — can it survive to the end of the horizon?
Current ratio, total-liabilities/equity, operating cash flow, profitability.
Over 3-12 months solvency risk is real in a way it is not over 5 days.
`5` fortress · `3` adequate · `1` stressed or burning cash with no runway

**4. Falsifier** — what would have to be TRUE for this to fail?
Not "raise risks". State 2-3 **specific, checkable** failure conditions, then
check whether any is **already true**. "Competition could increase" is not a
falsifier. "Gross margin falls below 30% for two consecutive quarters — it is
currently 35.3%" is.
`5` failure conditions are specific and none currently hold · `3` one is
partly true or unverifiable · `1` at least one is **already true today**
This member has real weight and no veto. An already-true failure condition
scoring 1 pulls the total down hard, and that is the mechanism.

## Output — always produce this, for every name reviewed
```
{TICKER}  quality X/5  valuation X/5  health X/5  falsifier X/5  = TOTAL/20
Thesis (one line, 3-12 month):
Falsification conditions: 1) ... 2) ...  [already true? yes/no]
Data gaps:
```
Then rank the day's names by total, break ties on valuation, and record the
top 1-3:
```
python scripts/ranker.py pick {DATE} {TICKER} {RANK} high|medium|low {POOL} "{thesis}"
```
Conviction: `high` 16-20 · `medium` 11-15 · `low` ≤10. **Record the top name
even when its total is low** — "the best of a weak day, conviction low" is a
real and useful data point. Never skip a day to protect the record; that turns
the ledger into a highlight reel and invalidates the measurement.

## Hard rules
- **No vetoes.** No member may reject a name outright. Score it.
- **A low total is not a rejection**, it is a ranking. Nothing here is a
  trade proposal, advice to the user, or an order — scoring is not buying.
- **Never inflate a score to manufacture a candidate.** The point of scoring
  was never to produce more buys; it was to stop discarding the ordering
  information a gate throws away. A 6/20 recorded honestly is worth more than
  a 14/20 talked up.
- Do not score on price action. See the horizon section.
- CLAUDE.md's Hard Risk Rules are untouched and still bind everything
  downstream.

## Known gap — the screen still feeds the wrong names
`skills/screen.md` ranks the whole market by |% change|, which is a 2-week
mover screen. Feeding those into a 3-12 month fundamental council is a
mismatch: the universe is selected for having just moved, which is irrelevant
at this horizon and correlated with the one real effect in the data (5-day
reversal). Until the screen is rebuilt around the fundamental horizon, score
what arrives, and treat the universe as a known limitation of every result.
