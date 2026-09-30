# Scorecard — updated 2026-09-30

## Proposed ideas (survived council, reached propose_trades.md)
Total checked: 0
Hit target: 0 | Hit stop: 0 | Time-stopped, neither hit: 0 | Unclear: 0
Win rate (target vs. stop, excludes unclear/time-stopped): not enough data yet (N=0) — no CANDIDATE has ever survived council to reach propose_trades.md, so this category has nothing to check yet.

## Council downgrades (research.md CANDIDATE -> council.md WATCH/PASS)
Total checked: 19 (GTLB, HOOD, DUOL, SIRI, DELL, SOFI, ASTS, VRNS, ALNY, GWRE, HPE, TARS, ROIV, ASO, ABBV, NRXS, GNRC, RARE, SECZ)
Downgrade validated (price faded or didn't continue): 13 (GTLB, DUOL, SIRI, SOFI, ASTS, VRNS, ALNY, GWRE, HPE, TARS, ABBV, GNRC, RARE)
Downgrade cost a winner (price kept running without us): 2 (DELL, SECZ)
Unclear: 4 (HOOD, ROIV, ASO, NRXS)
Downgrade accuracy: 13/(13+2) = 86.7%

Streak note: every single CANDIDATE that has ever reached council (24 for
24 as of 2026-09-29, including TWST/KOD/CAAP below which are too fresh to
resolve yet) has been downgraded to WATCH. Of the 15 with a resolvable
outcome so far, 13 validated the downgrade and 2 (DELL, SECZ) cost a
winner — 86.7% accuracy on a still-small sample. This is the second real
data point (after the 2026-09-11 pass) suggesting council's skepticism is
earning its keep more often than not, even through a specifically bullish
2-week stretch — but per the 2026-09-03/09-09 user decisions, this is NOT
license to loosen anything unilaterally on its own.

TWST (09-24), KOD (09-28), and CAAP (09-29) are logged in
trade_ledger.md as PENDING — all three are too fresh (<5 trading days) to
resolve as of this update and are excluded from the tallies above.

## Research-level WATCH/PASS calls (never reached council)
The much larger sample: every ticker research.md screened but didn't
even mark CANDIDATE. Same question as above (did the price move the way
the PASS/WATCH reasoning implied?) but at a scale council-only checking
can't reach — most tickers never make it to council, so restricting
outcome-checking to that subset badly under-samples the system's actual
accuracy. Use this category by default; the narrower "Council downgrades"
category above is a useful subset view, not a substitute.
Total checked: 103
Call validated (price faded/stayed flat/moved against the thesis,
  matching the PASS/WATCH reasoning): 50
Call cost a winner (price moved the way a CANDIDATE would have,
  without us): 14 (XP, FCEL-tentative(09-03), AEHL-so far, CLS-tentative,
  CCC.L-leaning, OXM, AEHR — plus this pass's CRWD, TEM(09-16), VICR, DNA,
  MRNA, GRAL, DSP)
Unclear: 39
Accuracy: 50/(50+14) = 78.1%

## 2026-09-30 outcome-check pass detail (user-requested)
Prompted directly by the user pointing out a bullish 2-week market stretch
("we have nothing to show") — checked 5 council downgrades (folded into
the category above) plus 26 research-level WATCH calls from
~2026-09-15 to 09-24 against real Massive.com OHLCV. Combined N=31 for
this pass alone: 21 Validated, 8 Cost a winner, 2 Unclear.
Accuracy excluding unclear: 21/(21+8) = 72.4%.

This pass's honest headline: roughly **1 in 4 resolvable calls** during
this specific bullish stretch were real, identifiable misses — genuine
catalysts where the WATCH/downgrade caution was about timing, extension,
or valuation rather than the catalyst being fake, and the market simply
kept running anyway (CRWD +8.35%, TEM +16.7% same-session, VICR +30.5%,
DNA +52-68%, MRNA +17.7%, GRAL +36%, DSP a clean +8% target hit, SECZ
+17-26%). See lessons.md #9 for the specific shape of these misses
(real catalyst + extension/valuation objection tends to cost more than
thin/sector-wide catalyst objections during a bullish tape) — flagged to
the user directly per CLAUDE.md's calibration rule, not acted on
unilaterally.

Full per-ticker detail: see trade_ledger.md's "Outcome-check pass,
2026-09-30" section and the updated ABBV/NRXS/GNRC/RARE/SECZ entries
above it.

## Sample size note
With N=19 (council) and N=103 (research-level), these percentages are
directional, getting more meaningful but still not statistically
decisive — a handful of additional misses in either direction would move
both numbers several points. Both categories currently read as "the
skepticism is earning its keep more often than not, but at a real,
non-trivial cost during strongly bullish stretches specifically" — a more
nuanced read than the pre-09-30 scorecard's cleaner "mostly validated"
picture. This is a genuinely useful data point to bring to the user for
the calibration conversation CLAUDE.md's rules require, but it is still
not, on its own, a trigger to change council.md, research.md, or either
TA/ICT promotion bar — that stays an explicit decision for the user to
make.
