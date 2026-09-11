# Scorecard — updated 2026-09-11 (17 unchecked outcomes cleared via OHLCV; calibration corrected)

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
Total checked: 94 (was 77; the 17 previously-unchecked rows were all
resolved 2026-09-11 via authoritative OHLCV — see the note below)
Call validated: 36 (was 32; +4 newly resolved — BMNR, ZOOZ, BIAF, DOCN)
Call cost a winner: 7 (XP, FCEL-tentative, AEHL-so far, CLS-tentative,
  CCC.L-leaning, OXM, AEHR) — **no new misses found this pass**
Unclear: 40 | Provisional (too recent to grade, see below): 12
Accuracy: 36/(36+7) = **83.7%** (up from 82.1%)

**The 18 "unchecked" rows are now cleared — but the headline finding is
about WHY they were stuck.** They were logged as needing "a dedicated
follow-up pass" after a WebSearch budget ran out, implying search effort
was the blocker. It wasn't. Two things were:
1. **Method**: WebSearch was the wrong tool. All 17 rows (the 18th, GSK.L,
   is a non-directional process call) resolved in a single batch by
   pulling dated OHLCV directly — exactly what lessons.md #2 already says
   to do when a fact is load-bearing. No search budget was needed at all.
2. **Time, not effort**: 12 of the 17 STILL can't be graded, because the
   project's own 5-trading-day time-stop hasn't elapsed. Nine were 09-10
   verdicts with ONE session behind them. These are marked "Provisional"
   with their live numbers rather than forced into a hit/miss bucket, and
   need a re-check once 5 sessions have passed — re-checking them sooner
   would just be grading noise.
Method used (repeat it rather than WebSearching): entry at the next
session's OPEN after the verdict date (backtest_ta.py's no-lookahead
convention), then CLAUDE.md's own exit rule — -4% stop / +8% target /
5-day time-stop — applied against subsequent daily highs/lows, stop
assumed first when a single day touches both. Massive had not settled the
2026-09-11 session ~40min post-close (the staleness window CLAUDE.md
documents), so Alpaca daily bars supplied that session; the two agreed to
within 0.04% on overlapping days (ADBE 09-10: $248.83 vs $248.73), which
is the cross-check that makes the Alpaca IEX prices trustworthy here
despite its partial-volume feed.

## Calibration — research-note Confidence vs. actual outcome (2026-09-11, CORRECTED SAME DAY)
Backfilled from the `## Confidence` field in all 132 research notes,
joined to the appendix table's Outcome column. **An earlier version of
this table published in the same session was wrong** — it used crude text
matching that counted hedged outcomes ("unclear — leans cost a winner")
as confirmed misses, reporting high-confidence accuracy as 75% and
calling calibration clearly inverted. Corrected figures, using bucketing
that reproduces this file's own 7-miss list exactly:

| Confidence at write-up | HIT | MISS | provisional | unclear | Accuracy |
|---|---|---|---|---|---|
| high   |  5 | 1 | 1 |  2 | **83%** (n=6) |
| medium | 22 | 5 | 6 | 21 | **81%** (n=27) |
| low    |  8 | 0 | 5 | 17 | **100%** (n=8) |

**What this does and doesn't say.** Low-confidence calls still resolve
better than high-confidence ones, so some inversion is present at the
extremes. But high is no longer the worst bucket, the spread is much
narrower than first reported, and with n=6 in the high bucket a single
outcome decides its number. This is not evidence to recalibrate on. See
lessons.md #10, which was demoted from a lesson to a watch-only
hypothesis once these corrected numbers came in.

**Bucketing rules — use these exactly, or the numbers won't reconcile:**
- Verdict contains "no thesis" → EXCLUDED from the denominator entirely
  (bare screened movers with no directional call, 10 rows).
- Outcome starts with "unclear", or contains "possibly cost" → unclear.
  A hedged lean is not a confirmed outcome, in either direction.
- Outcome contains "provisional" or starts with "leans validated" →
  provisional (graded but too recent to count).
- Otherwise "cost a winner" → MISS; "validated" → HIT.
- Sanity check before trusting any run: the MISS list must come out as
  exactly FCEL, XP, AEHL, AEHR, CLS, CCC.L, OXM. If it doesn't, the
  bucketing drifted — fix that before reporting percentages.

## Structured postmortem on the misses (2026-09-11, per the methodology review)
Not a tally — grouping every miss by the *reasoning pattern* that
produced it, to find fixable failure modes rather than counting errors.
57 of 147 research notes (39%) lean on staleness / "already priced in" /
"sell the news" reasoning, so it is the single dominant rejection
rationale in this system, not an occasional one. Of the staleness-citing
calls with a resolvable outcome: **8 validated, 3 cost a winner = 72.7%**,
against the 83.7% baseline for research-level calls overall. The dominant
rejection rationale underperforms the system's own average by ~11 points —
the single most actionable finding in this file.

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
3. **Clean structural-negative story reversed** — OXM (confirmed miss,
   high confidence) plus EGAN (high confidence, but only "unclear — leans
   cost a winner", NOT a confirmed miss). One-and-a-half instances, which
   does not clear lessons.md's evidence bar — #10 is explicitly demoted to
   a watch-only hypothesis, not an active lesson. Do not act on it.

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
(MM-DD, TICKER), and join to the `| Date | Ticker | ... | Outcome |` rows
in trade_ledger.md's appendix. Bucket using the rules in the Calibration
section above — NOT ad-hoc text matching, which is exactly what produced
the wrong numbers on this file's first attempt. Re-run on every journal
pass rather than hand-editing.

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
