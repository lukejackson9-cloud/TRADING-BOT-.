# Lessons

Short, evidenced, cross-ticker patterns — not per-trade detail (that's
data/journal/trade_ledger.md). Each entry must point to real evidence
already gathered, not a hunch. research.md and council.md read this for
context before forming a fresh opinion — never as an override, a past
pattern doesn't decide a new ticker's verdict, fresh evidence does.

A lesson earns a place here once it's shown up more than once with real
sourcing behind it — not after a single anecdote.

---

## 1. Buying right after a big catalyst-driven gap tends to be a worse
entry, not a better one ("sell the news" / overextension)
Evidenced three independent ways:
- **Quantitatively**: scripts/backtest_ta.py's gap-confirmation test
  (2026-09-07) — requiring an overnight gap as a catalyst proxy made both
  breakout and ema_cross WORSE, monotonically with gap size (breakout
  -0.25%→-0.57%, ema_cross +0.07%→-0.54% at a 5% threshold), because
  simulated entry is the day AFTER the signal, i.e. after the reaction
  already happened.
- **Discretionarily, repeatedly**: AEHR ("every driver is 3+ weeks
  stale... likely sell-the-news setup"), CHPT on 09-03 ("+75% today...
  already fully priced by the time of research"), MSTR ("the company's
  own news is 4 days stale"), NX on 09-07 ("the actual pop happened the
  day before, today just confirms the level held").
- **In council**: TARS (09-08) — entry would have been at an all-time
  high the day after both positive catalysts had already fired.
Action: when a research pass finds a real catalyst, check whether the
PRICE has already moved on it before treating the move as still
actionable — a real catalyst with an already-fired reaction is a weaker
setup than a real catalyst about to be revealed (see screen.md's
earnings-lookahead design, which exists specifically to catch a reaction
same-session instead of chasing one that already happened).

**Counter-example, logged honestly (2026-09-11 outcome check)**: AEHR's
2026-09-04 WATCH ("every driver is 3+ weeks stale... likely sell-the-news
setup") did NOT play out — the stock surged a further +69% (from $86.26
to ~$145.61) into/past its 52-week high at a 2026-09-10 investor
conference, rather than fading. This is the same pattern this lesson is
built on (DOCU, AEHR's own earlier appearances, CHPT, MSTR, NX, TARS) but
running the opposite direction on this specific occasion. Not treated as
disproving the pattern — it's still evidenced 5+ ways above — but logged
so a future pass doesn't smooth over the one clean miss: "stale drivers"
is a real caution worth raising, not a reliable predictor of a fade on
its own, and a live, dated event (the investor conference) can still
reignite a "stale" story. Don't downgrade a real near-term dated event
(even one attached to an already-running story) to "stale" without
weighing that it could still be the next leg's actual trigger.

**Turned into an explicit checklist (2026-09-11)**, not left as a
one-line caveat: skills/research.md step 3a now requires research.md to
explicitly check for, and record, whether a dated near-term company event
exists before downgrading anything as "stale" — and skills/council.md's
falsifiability requirement makes the same check mandatory for any bear
case leaning on "already priced in." The gap this closes specifically:
AEHR's own research note correctly identified every driver as stale
without ever checking whether a NEW dated event (the conference) was
still ahead — the checklist forces that second question to be asked and
answered on the record, not just the first.

## 2. WebSearch summaries are unreliable for precise facts (price levels,
% moves, even direction) — verify against authoritative OHLCV when
sources disagree
Evidenced repeatedly:
- **DOCU** (09-06): two WebSearch headlines gave contradictory framing
  ("stock soars" vs. "another selloff") for the same session — resolved
  by pulling Massive.com's actual OHLCV directly, which showed both were
  each capturing part of one volatile session (a real +3.7% close-to-
  close gain with a 9.7% intraday range).
- **MARA** (09-03): sources gave conflicting BTC price levels for the
  same claimed catalyst.
- **VALE** (09-03): sources disagreed even on the DIRECTION of the move
  (-2.7% vs. +4.0%) — treated as unconfirmed rather than picking one.
- **TARS council** (09-08): the bull-case agent's WebSearch results gave
  a ~25% price spread for "today's" price across sources — resolved
  using Massive.com's OHLCV directly ($90.78 confirmed correct).
Action: when a fact is load-bearing for a verdict (an exact price, a %
move, which direction something went) and WebSearch sources disagree,
pull the number directly from scripts/massive_client.py or
scripts/alpaca_client.py rather than trying to adjudicate between
conflicting summaries.

## 3. A sector-wide rally produces clusters of simultaneous "movers" that
look like independent opportunities but are really one correlated bet
Evidenced:
- **2026-09-08**: KLAC, ALAB, NBIS, AXTI, TSEM, FORM, UCTT, TTMI, SMTC,
  BE all moved together on one semiconductor/AI-infrastructure rally —
  confirmed live via research, no single discrete news event tied the
  whole cluster together.
- **2026-09-03**: XP's move was confirmed sector-wide (STNE/PAGS/PicPay
  moved together too), not XP-specific — marked PASS specifically for
  this reason.
- **2026-09-03**: RUN's move was sector-wide (CSIQ moved too) on a common
  IRS clarification, not RUN-specific.
Action: before treating several same-session movers in one sector as
independent CANDIDATEs, check whether the whole sector moved together —
if so, treat any that reach council as ONE correlated bet
(`correlation_flag` per CLAUDE.md's Hard Risk Rules), not several
independent ones, even if each has some individual-company case on top.

## 4. Some tickers' screener-implied price moves cannot be verified
against any live source — treat as unreliable data, not a real catalyst
Evidenced: **RACC**, twice — 2026-09-03 ("DATA FAILURE -- screener's
-37.4% move could not be verified against any source, actual range
$24-25") and again 2026-09-08 ("-7.5% per screener... could not verify
this move against ANY live source, all show RACC trading $24-25"). Same
ticker, same failure mode, five days apart.
Action: if RACC (or any ticker) shows this exact pattern a third time,
consider filtering it out of the screening universe entirely rather than
re-researching the same unverifiable signal each time it appears — this
is now a documented, repeat data-quality problem with this specific
ticker's screener feed, not a one-off.

## 5. A single sell-side analyst action — especially a sector-wide one —
is weaker evidence than company-specific fundamental news
Evidenced: ASTS's Berenberg init was sector-wide, not ASTS-specific,
with a launch delay and dilutive convert underneath, downgraded at
council. HOOD/DUOL/SIRI's analyst-upgrade-driven pops were all downgraded
partly for being sentiment-driven with a real structural risk still
underneath. RUN's IRS-clarification pop was sector-wide (see #3).
Action: an analyst upgrade/init is a real, checkable fact worth logging,
but weigh it lower than a company's own reported numbers (earnings,
guidance, a completed deal) when deciding whether a catalyst is strong
enough to survive council.

## 6. A recurring/recycled narrative is a red flag for thin-float pump
behavior, not a real catalyst
Evidenced: AEHL ("recycled Bitcoin-treasury 'Genius Plan' narrative, 3rd+
time this year -- serial thin-float pump pattern"), VRNS ("documented
repeat unconverted rumor pattern since June 2026" on the same
Proofpoint-takeover story, downgraded at council partly for this reason
plus an active securities fraud lawsuit).
Action: when research.md finds a "catalyst" that resembles a story
already told about this exact ticker before, explicitly check whether
it's actually the same recycled narrative rather than fresh news — ask
"has this exact claim been made about this ticker before" as a specific
skepticism check, not just "is this claim true."

## 7. A company's own past repeat of the same pattern is highly
predictive of what happens next
Evidenced: GWRE's 2026-09-04 beat-then-ARR-guide-down crash is the EXACT
same pattern that happened to GWRE in June 2026, where recovery took ~3
months — directly informed the council downgrade (the 2-week trading
window this project uses doesn't fit a 3-month recovery pattern).
Action: when a ticker has any documented history in this project (or
findable via WebSearch) of a similar setup before, weight that company-
specific precedent heavily — it's more directly predictive than general
sector base rates.

## 8. Independent bull/bear agents converging on the same risk cluster
without seeing each other's work is unusually strong evidence
Evidenced: TARS council review (09-08) — the bull-case agent, tasked with
building the strongest case FOR the trade, independently surfaced the
same major risks (the Culper Research allegation, deal dilution, insider
selling) that the bear-case agent built its argument around, despite
neither agent having any visibility into the other's research. This
convergence was treated as stronger evidence than either side's framing
alone, and was decisive in the WATCH downgrade.
Action: when moderating council, explicitly check whether both sides
independently found the same facts (not just whether they disagree on
interpretation) — unprompted agreement on a specific risk is more
reliable than either side's argued position.

## 9. "No fresh dated catalyst" is not a reason a move will stop — a
rising-estimate-revision story can keep running with no new event at all
This is the failure mode lesson #1's new AEHR checklist does NOT catch,
found by the 2026-09-11 structured postmortem on every logged miss (see
scorecard.md's calibration section for the full method). AEHR was a case
where a dated event WAS pending and got missed. These are the opposite —
cases where research correctly verified no dated catalyst existed, and
the move continued anyway:
- **CLS** (09-04, WATCH, "cost a winner (tentative)", +5-6% in under a
  week): the note explicitly checked and correctly established that the
  next earnings were Oct 26, ">7 weeks out, past this bot's ~2-week
  horizon — no near-term binary event to trade around," and treated that
  absence as a reason to stand aside. What it also recorded, and then
  weighed as neutral-to-negative, was that FY26 EPS estimates were +11.4%
  and FY27 +30.2% over the prior 60 days, with multiple brokers raising
  targets.
- **CCC.L** (09-06, WATCH, "leans cost a winner", kept rising to new
  record highs 5,700-5,825p): same shape — "no fresh company-specific
  news accompanied this particular UBS note... a target/estimate revision
  layered on already-known H1/July information," plus "near record highs"
  treated as extension risk. Underneath it: the company's own July
  guidance upgrade ("ahead" → "comfortably ahead of market
  expectations"), H1 adjusted PBT guided to roughly double, and a second
  broker (Berenberg) independently upgrading.
Both notes reasoned that an already-known story with no fresh dated event
had nothing left to give. In both cases the stock kept re-rating on the
estimate-revision trend itself. Note this is the exact opposite direction
from lesson #1 — which is why both belong here rather than one replacing
the other: a fired catalyst with nothing behind it fades (#1), but a
rising estimate/guidance trend with no single dated event can keep going
(#9). The distinguishing feature is not "was there a dated catalyst" but
"is the underlying estimate trend still moving."
Action: treat a corroborated, multi-source UPWARD estimate/guidance
revision trend (company guidance raised, consensus EPS revised up over
weeks, more than one broker moving the same way) as a real signal in its
own right, not as "no catalyst, therefore pass." Record it explicitly as
a distinct line in the research note's Catalyst section rather than
folding it into "no dated event found." This does NOT mean buying
extended stocks with no catalyst — the opposite overcorrection is just as
wrong, and lesson #1 still stands on its own evidence. It means the
absence of a dated event is not itself bearish, and shouldn't be written
up as though it were.
**Candidate third instance, found 2026-09-11, not yet resolved**: BAND
(09-10, PASS, reason given: "no confirmed dated catalyst despite bullish
backdrop") rose **+7.5% on the very first session after the verdict, with
an intraday high +7.9% — within 0.1pp of this project's +8% target**, on
day one of five. Same shape as CLS and CCC.L: the absence of a dated
catalyst was written up as the reason to stand aside, and the stock moved
anyway. Deliberately NOT counted as a miss yet — one session is not a
resolution, and it could still round-trip before the 5-day time-stop.
Re-check at 5/5 sessions; if it holds, this lesson has three instances
and the ordering question ("is the estimate trend still moving") becomes
worth raising with the user directly rather than just logging.
Sample-size caveat, stated plainly: N=2 clean instances (+1 pending), and
BOTH resolved ones are logged in the ledger as tentative/leaning ("cost a
winner (tentative)", "leans cost a winner") rather than cleanly resolved —
this clears this file's "more than once with real sourcing" bar but is
nowhere near strong enough to change a verdict rule on its own. Re-check
all three outcomes with a proper dated-source price comparison before this
is treated as settled.

## 10. [DOWNGRADED TO HYPOTHESIS, same day it was written — does NOT meet
this file's evidence bar] Possible pattern: clean structural-negative
stories snapping back
**Read the correction first.** This lesson was written earlier on
2026-09-11 claiming calibration was clearly inverted (high 75%, medium
78%, low 88%) and that "both high-confidence misses" shared a snapback
shape. Re-running the tally the same day with bucketing corrected to match
scorecard.md's own documented methodology — hedged outcomes like "unclear
— leans cost a winner" count as UNCLEAR, not as confirmed misses, and
no-thesis rows are excluded — changed the picture materially:
- High-confidence accuracy is **83% (n=6)**, not 75%. EGAN, one of the two
  claimed high-confidence misses, is logged as "Unclear (leans cost a
  winner)" and should never have been counted as a confirmed miss.
- Corrected calibration: high 83% (n=6), medium 81% (n=27), low 100%
  (n=8). The low bucket still outperforms the high bucket, so *some*
  inversion remains at the extremes — but high is no longer the worst
  bucket, the gap is far smaller than first reported, and n=6 in the high
  bucket means a single outcome decides it.
- The snapback pattern therefore rests on **one confirmed instance (OXM)
  plus one leaning (EGAN)** — which does not clear this file's stated bar
  of "shown up more than once with real sourcing."
Kept here, explicitly demoted rather than deleted, for the same reason
vcp_breakout's reversal was kept in CLAUDE.md: the mistake is instructive.
A crude text-matching bucket rule inflated a finding into a confident
claim about the system's calibration within a single pass. Any future
calibration claim must state its bucketing rules and reproduce
scorecard.md's miss list exactly (FCEL, XP, AEHL, AEHR, CLS, CCC.L, OXM)
before its percentages are trusted.
The underlying hypothesis, still worth watching as more outcomes resolve:
- **OXM** (09-07, PASS, high confidence): "clean earnings-miss-and-
  guide-down story," full-year EPS guidance cut well below consensus,
  next quarter guided to a loss, explicitly written up as a
  "falling-knife pattern." Then +23% in three sessions.
- **EGAN** (09-07, PASS, high confidence): "structural decline, swing to
  GAAP net loss." Ledger: "leans cost a winner — data suggestive of a
  rebound."
The pattern is intuitive in hindsight and worth naming: the cleaner and
more one-sided the bad news, the more confidently this system writes it
off — and clean, fully-digested bad news is also exactly the setup where
positioning gets crowded and oversold snapbacks happen. High confidence
here is tracking "how unambiguous is the story," which is not the same
thing as "how likely am I to be right about the next two weeks."
Action while this remains a hypothesis: no behaviour change. Do NOT adjust
how confidence is assigned, and do not add a "clean bear case" check to
research.md on this evidence — one confirmed instance is an anecdote. What
to do instead is purely observational: when the next structural-negative
PASS at HIGH confidence resolves, record it here. Three confirmed
instances would make this a real lesson; continued 80%+ high-confidence
accuracy would retire it.
Sample-size reality: n=6 (high) and n=8 (low). A single outcome flip moves
either by 12-17 points. The medium bucket still carries 21 unresolved
"unclear" outcomes — more unresolved than resolved — so the graded subset
may not represent the whole. Per CLAUDE.md's standing 2026-09-03/09-09
user decisions, any actual change to confidence-rating behaviour or
council's bar is the user's call, and nothing here comes close to
justifying one.

## 11. An absolute volume/liquidity filter silently becomes a different
##     filter when the data feed changes — and the distortion is worst in
##     the oldest data, exactly where multi-year tests need it least
Evidence (2026-09-12, found while building `scripts/regime_test.py`):
`backtest_ta.iter_signals()` screens for >=1,000,000 shares. That was
written against Massive's full consolidated tape. Alpaca's free feed
reports **IEX-only** volume, measured at a median **5.1%** of consolidated
volume (p5 2.7%, p95 8.8%) across a 401-name sample on 2026-09-10. So the
same line of code means ">1M shares" on one feed and ">~20M shares" on the
other — a mega-cap-only screen wearing a liquidity screen's clothes.
Worse, it is not a constant distortion: IEX's market share was lower in
earlier years, so the filter tightens as you go back. First run of the
regime test yielded **32 signal entries in 2020 against 409 in 2026** and
was unusable as a per-year comparison. With the floor corrected to 50,000
IEX shares the years came out balanced (1,136-5,146 each) and the totals
rose from 1,019 to 24,867 signal entries.
Two general points worth carrying:
- **A threshold is only meaningful relative to the feed it was calibrated
  on.** Ratios (today's volume vs. its own 20-day average, as the breakout
  trigger uses) survive a feed change; absolute levels do not. Prefer
  ratios where the logic allows it.
- **Check the per-period sample counts before reading any per-period
  table.** The distortion here announced itself as a 13x imbalance across
  years. That imbalance was visible in the output before any number in it
  was interpreted — the same class of check that caught the 20-day
  effective-sample-size problem and the two-date paper-trade artifact.
Consequence for existing numbers: every 6-year Alpaca backtest in
CLAUDE.md's TA section ran through the unadjusted floor and is mega-cap-
skewed on top of its documented survivorship bias. Not re-run; treated as
another reason those figures are not load-bearing.
