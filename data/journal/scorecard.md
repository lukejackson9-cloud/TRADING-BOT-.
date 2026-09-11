# Scorecard — updated 2026-09-11 (calibration backfill + miss postmortem added this pass)

## Proposed ideas (survived council, reached propose_trades.md)
Total checked: 0
Hit target: 0 | Hit stop: 0 | Time-stopped, neither hit: 0 | Unclear: 0
Win rate (target vs. stop, excludes unclear/time-stopped): not enough data yet (N=0) — no CANDIDATE has ever survived council to reach propose_trades.md, so this category has nothing to check yet.

## Council downgrades (research.md CANDIDATE -> council.md WATCH/PASS)
Total checked: 14 (GTLB, HOOD, DUOL, SIRI, DELL, SOFI, ASTS, VRNS, ALNY, GWRE, HPE, TARS, ROIV, ASO)
Downgrade validated (price faded or didn't continue): 10 (GTLB, DUOL, SIRI, SOFI, ASTS, VRNS, ALNY, GWRE, HPE, TARS)
Downgrade cost a winner (price kept running without us): 1 (DELL)
Unclear: 3 (HOOD, ROIV, ASO — ROIV/ASO both simply too recent, re-check in a few days)
Downgrade accuracy: 10/(10+1) = 90.9%

**Every single CANDIDATE that has ever reached council (14 for 14) has been
downgraded to WATCH.** Of the 11 with a resolvable outcome so far, 10
validated the downgrade and only 1 (DELL) cost a winner — a real, if
still small, sample suggesting council's skepticism has been earning its
keep, not just suppressing activity. Per the 2026-09-03/09-09 user
decisions, this is NOT license to loosen anything unilaterally — it's the
first real evidence to bring back to the user for that conversation.

## Research-level WATCH/PASS calls (never reached council)
Total checked: 77
Call validated (price faded/stayed flat/moved against the thesis,
  matching the PASS/WATCH reasoning): 32
Call cost a winner (price moved the way a CANDIDATE would have,
  without us): 7 (XP, FCEL-tentative, AEHL-so far, CLS-tentative, CCC.L-leaning,
  OXM, AEHR — AEHR is the standout, a genuine +69% miss on a "sell the
  news" call, see lessons.md #1's new counter-example note)
Unclear: 38 (mostly missing a clean verdict-date or current-date baseline
  price rather than contradictory evidence — see the trade_ledger.md
  appendix's per-ticker notes for exactly what's missing on each)
Accuracy: 32/(32+7) = 82.1%

Separately, 18 tickers (BMNR, PUR, ZOOZ, and the full 09-09/09-10 batch —
FCUV, BIAF, DOCN, VIAV, ADBE, CHWY, NET, PINS, VRT, BAND, KRMN, TBBK,
BRZE, SIG, plus 2 more) were **not checked at all** this pass — the
outcome-check subagents ran out of WebSearch budget before reaching them,
not because the evidence contradicted anything. These are not "unclear"
outcomes, they're unattempted ones; they need a dedicated follow-up pass
(ADBE especially, since CLAUDE.md/HANDOFF.md specifically wanted its
earnings-reaction checked) before being folded into this scorecard.
9 more (the 09-02 screened-movers batch: CNH, ONDS, IREN, NU, CDE, RIG,
SOFI, PLTR, PCG, NVDA) had no directional thesis to grade in the first
place (bare price/volume movers logged without a bull/bear call) and are
excluded from the denominator entirely, not counted as validated,
missed, or unclear.

## Calibration — research-note Confidence vs. actual outcome (FIRST RUN, 2026-09-11)
Backfilled from the `## Confidence` field already present in all 132
research notes, joined to the appendix table's Outcome column in
trade_ledger.md. Reproduce with the parser described at the bottom of
this section — this is not a hand count.

| Confidence at write-up | HIT | MISS | unclear | unchecked | Accuracy |
|---|---|---|---|---|---|
| high   |  6 | 2 |  1 |  2 | **75%** (n=8) |
| medium | 21 | 6 | 25 |  9 | **78%** (n=27) |
| low    |  7 | 1 | 17 |  7 | **88%** (n=8) |

**The ordering is inverted.** A well-calibrated system's high-confidence
bucket should be its most accurate; here it is the least. See lessons.md
#10 for the mechanism behind this (both high-confidence misses — OXM,
EGAN — are clean structural-negative PASS calls that then snapped back),
which is a more useful finding than the percentages themselves.

**Read this with the sample sizes in front of you**: n=8 in both the high
and low buckets means one outcome flip moves either number by 12+ points,
and the two buckets are separated by a single miss. The medium bucket has
25 unresolved "unclear" outcomes — more unresolved than resolved — so the
resolvable subset may not be representative of the whole. This is a
hypothesis to keep testing as outcomes resolve, NOT a basis for changing
how confidence is assigned or how council rules. Per CLAUDE.md's standing
2026-09-03/09-09 decisions that stays the user's explicit call.

Every logged MISS with the confidence it carried at write-up time (the
raw material behind the table — kept so a future pass can re-derive this
rather than trusting the percentages):
PLTR (medium, no thesis), FCEL (medium), XP (medium), AEHL (medium),
AEHR (medium), CLS (no confidence field parsed), CCC.L (medium),
OXM (**high**), EGAN (**high**), NBIS (low).

## Structured postmortem on the misses (2026-09-11, per the methodology review)
Not a tally — grouping every miss by the *reasoning pattern* that
produced it, to find fixable failure modes rather than counting errors.
57 of 147 research notes (39%) lean on staleness / "already priced in" /
"sell the news" reasoning, so it is the single dominant rejection
rationale in this system, not an occasional one. Of the staleness-citing
calls with a resolvable outcome: **8 validated, 3 cost a winner = 72.7%**,
against the 82.1% baseline for research-level calls overall. The dominant
rejection rationale underperforms the system's own average.

Three distinct failure modes, which need different fixes:
1. **A pending dated catalyst was ahead and wasn't checked** — AEHR
   (+69% into a 2026-09-10 investor conference). Fixed by research.md
   step 3a's checklist and council.md's falsifiability requirement, both
   added 2026-09-11. Only ONE clean instance so far, so the fix is
   well-targeted but not yet proven at scale.
2. **No dated catalyst existed, correctly verified, and the move
   continued anyway** on an estimate-revision trend — CLS, CCC.L. The
   checklist from mode 1 does NOT catch these; see lessons.md #9 for the
   proposed handling.
3. **Clean structural-negative story reversed** — OXM, EGAN, both rated
   high confidence. See lessons.md #10.

**Data discrepancy found during this pass, unresolved, needs a re-check**:
the ledger credits OXM's rebound to "a 9/10 earnings beat," but OXM's own
research note documents Q2 FY2026 results reported on **2026-09-03**, four
days BEFORE the 09-07 verdict. Both cannot be right. This matters because
it decides whether OXM belongs in failure mode 1 (a dated catalyst was
pending and ignored — which would double that mode's evidence) or mode 3
(a reversal with no new event). Resolve with a dated source per
lessons.md #2 before either mode's count is treated as settled; it is
currently counted under mode 3 only because that's what OXM's own note
supports.

**How to reproduce the calibration table**: parse `## Confidence` from
each `data/research/*/*.md` (skipping `_council` files), key on
(MM-DD, TICKER), join to the `| Date | Ticker | ... | Outcome |` rows in
trade_ledger.md's appendix, and bucket Outcome text on "cost a winner" →
MISS, "validated" → HIT, "unclear"/"trajectory only" → unclear,
"not checked"/"not applicable" → unchecked. Re-run it on every journal
pass rather than editing these numbers by hand.

## Sample size note
With N=14 (council) and N=77 (research-level), these percentages are
directional only, not statistically meaningful — a single additional
DELL-shaped miss would move the council number several points. Both
categories currently read as "the skepticism is earning its keep more
often than not," which is a genuinely useful first real data point after
a week and a half of pure PENDING entries, but it is nowhere near enough
to justify loosening research.md's skepticism, council's calibration, or
either TA/ICT promotion bar on its own. Per the standing 2026-09-03/09-09
user decisions, that stays a decision for the user to make explicitly,
not something this file's numbers trigger on their own.
