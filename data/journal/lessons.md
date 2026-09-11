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
