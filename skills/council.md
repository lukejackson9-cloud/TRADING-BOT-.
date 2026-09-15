# Skill: Council Review

Goal: pressure-test a CANDIDATE verdict from skills/research.md before it's
allowed to reach skills/propose_trades.md, using independent perspectives
that cover the bases a single research pass can miss — so one enthusiastic
research pass doesn't turn into overconfident advice. This step only runs
on tickers already marked CANDIDATE; WATCH/PASS tickers don't need it.

## Why this exists
CLAUDE.md already says "CANDIDATE should be rare... require a real
catalyst." A single research pass can still talk itself into a good story,
especially once it's already found a catalyst it likes. This runs a
structured second look — closer to a real investment committee than a
single analyst — before anything reaches the user as advice. The point
isn't theater: if this step never downgrades anything, it isn't doing its
job, and that should be said out loud, not hidden.

## Council structure — expanded 2026-09-15 to four roles
Built per explicit user request: "a single strategy alone will not help us
win trades, it needs multiple alongside news in most cases" — the original
two-role council (bull/bear) only covered the news/fundamentals angle.
Nothing was checking the technical picture or whether a move was really
independent evidence versus one sector-wide bet wearing several tickers.
Four roles now, not two:

1. **Technical Context specialist** (new, non-argumentative)
2. **Correlation & Macro specialist** (new, non-argumentative)
3. **Bull case agent** (unchanged)
4. **Bear case / risk critic agent** (unchanged)

Roles 1-2 are FACT-REPORTERS, not advocates — they don't vote bull or bear,
they establish grounded, sourced facts that roles 3-4 and the moderator
then reason about. This is different from the bull/bear "no anchoring"
rule below, which is about not sharing ARGUMENTS or OPINIONS — sharing
verified facts (like journal history, already an existing exception) isn't
anchoring, it's giving everyone the same accurate picture to reason from
independently.

**Non-negotiable framing for the Technical Context specialist**:
`CLAUDE.md`'s "Signal confluence testing" section tested exactly the idea
that a matching mechanical TA/ICT signal makes a trade more likely to win
— across 9 different combinations, with pre-registered success criteria —
and found NO edge anywhere, the best result indistinguishable from zero.
**A matching technical signal must never be used to argue increased
confidence in this council's decision.** The specialist's job is narrower
and still genuinely useful: report the ticker's actual technical state
(is it already extended, is volume elevated, is a signal from
`backtest_ta.py`'s `iter_signals()` actually present) so the bull/bear
agents and the moderator can catch a "the reaction already happened, this
would be chasing it" risk (lessons.md #1) with real numbers instead of a
vague impression. Context, not confidence.

## The failure mode this is designed to avoid
Multi-agent setups usually fail by having every "agent" agree with
whatever the first one said — the illusion of scrutiny without the
substance. This design avoids that on purpose:
- The bull and bear agents each research and write independently — neither
  ever sees the other's output, or your framing of the ticker, before
  forming its own case. No anchoring on ARGUMENTS or OPINIONS.
- Both are told explicitly to be honest, not persuasive: a weak bull case
  should say it's weak; a bear case that finds nothing real should say so
  rather than manufacturing doubt.
- The bear case is mandatory even when the bull case looks obviously
  strong — that's exactly when overconfidence does the most damage.
- The two new specialist roles are mandatory too, even when the story
  looks clean — a real catalyst riding a sector-wide move, or a real
  catalyst on a stock that's already run 20% into resistance, are exactly
  the cases a pure news read would miss.
- You (the moderator) do not default to the bull case. Ties, or "not
  clearly weaker," go to WATCH/PASS, not CANDIDATE. A correlated move with
  no independent angle on top, or a technically exhausted setup, are each
  independently sufficient grounds for WATCH/PASS on their own — a clean
  bull case doesn't override either.

## Steps
1. Precondition: /data/research/{today}/{TICKER}.md exists with
   Verdict == CANDIDATE.
2. Check /data/journal/trade_ledger.md for this ticker (skills/journal.md's
   trade ledger — past verdicts on this exact ticker and what actually
   happened) and /data/journal/lessons.md for relevant patterns. This is
   fair shared background for every role below — factual track record,
   not anyone's opinion.
3. Spawn the two specialist subagents (can run in parallel with each
   other; each is independent of the other):
   - **Technical Context specialist**: pull the ticker's recent daily bars
     (scripts/massive_client.py or scripts/alpaca_client.py) for the last
     ~30 trading days. Report, with real numbers: % distance from the
     20-day high/low, whether today's bar would trigger a breakout/
     ema_cross/mean_reversion/vcp_breakout/relative_strength signal per
     `scripts/backtest_ta.py`'s shared `iter_signals()` (reuse that
     function directly, don't reimplement the logic — same reason
     scripts/paper_trader.py does), and whether volume is elevated vs.
     the 20-day average. Optionally cross-check
     `scripts/tradingview_client.py`'s `get_rating()` as a secondary,
     non-deciding data point. Explicitly flag if the setup looks already
     extended (a big move already happened, entering now means chasing)
     versus early-stage. Follow the non-negotiable framing above — this
     is context, never a confidence signal.
   - **Correlation & Macro specialist**: (a) check whether other same-
     sector/theme tickers moved the same session for a similar reason
     (WebSearch — the same check that caught the XP/RUN and KLAC/ALAB/
     NBIS clusters; see lessons.md #3), (b) check `backtest_ict.py`'s
     `FOMC_DATES`/`CPI_DATES`/`_is_nfp_day()` for whether today is a
     verified macro-news day (informational only — lessons.md's own
     confluence testing found at most a small, inconsistent effect, never
     a tiebreaker), (c) read every non-terminal entry in
     /data/pending_trades.json and everything in /data/positions.json for
     sector/theme overlap (this is propose_trades.md's step 5, pulled
     earlier so a correlated bet can be caught before it's ever called a
     survivor, not just sized down after). Output an explicit
     `correlation_flag`: `"none"` or a specific named overlap, same
     format propose_trades.md already uses.
4. Once both specialists return, spawn the bull and bear subagents in
   parallel with the Agent tool. Give each the ticker, today's date, the
   journal history from step 2, AND both specialists' factual reports from
   step 3 — but NOT the research.md file, not each other's output, not
   your own opinion of the trade:
   - **Bull case agent**: research and build the strongest honest case FOR
     entering this trade. Use WebSearch for its own sources — don't just
     hand it research.md's citations to rephrase. Must cite real,
     checkable sources for every factual claim. Explicitly instructed:
     if the case is weak, say so plainly rather than inflating it, and
     explicitly address the technical/correlation facts it was given
     rather than ignoring inconvenient ones.
   - **Bear case / risk critic agent**: research and build the strongest
     honest case AGAINST entering. Actively hunt for reasons this could be
     a trap: is the move already exhausted / already priced in, is there a
     sector headwind, insider selling, a valuation red flag, guidance that
     sounds better than the underlying numbers, a pattern resembling past
     failed breakouts in similar names. Must cite real sources for every
     claim, not vague hedging, and must explicitly weigh in on what the
     technical/correlation specialists found.
5. Once both return, act as moderator yourself — this step is not
   delegated:
   a. Fact-check all four reports against their own cited sources. Reject
      or flag any claim you can't verify was actually said by the source
      (CLAUDE.md's "never fabricate research" rule applies here too).
   b. Weigh them honestly against each other. The bull case does not win
      by default, and having already called this a CANDIDATE in
      research.md is not a reason to protect that verdict.
   c. Decide: does the bull case clearly survive the bear case, WITH a
      clean (or adequately explained) technical picture and no
      unaddressed correlation overlap? Only then does CANDIDATE stand. A
      real correlation_flag with no independent company-specific angle on
      top, or a technical picture showing the move already fully played
      out, is each independently sufficient to downgrade even a strong
      bull case.
   d. Write the outcome to
      /data/research/{today}/{TICKER}_council.md using the template below.
6. Only a ticker that keeps CANDIDATE status after this step moves to
   skills/propose_trades.md. A downgrade here is a normal, expected
   outcome — tell the user plainly when it happens and why, don't bury it.
   Pass this step's `correlation_flag` finding through to
   skills/propose_trades.md so it isn't re-derived from scratch there —
   propose_trades.md only needs to re-check pending_trades.json for
   anything added since council ran.

## Council note template
```
# {TICKER} — Council Review — {date}

## Technical context (from independent specialist)
Summary: (extended vs. early-stage, real backtest_ta.py signal present?,
volume)
Key data:

## Correlation & macro context (from independent specialist)
Summary:
correlation_flag: "none" | "{specific overlap}"

## Bull case (from independent agent)
Summary:
Key sources:

## Bear case (from independent agent)
Summary:
Key sources:

## Fact-check notes
(claims from any of the four you couldn't verify against their cited
source, or corrected)

## Moderator decision
Verdict: CANDIDATE | WATCH | PASS
Reasoning: (why the bull case did, or didn't, survive the bear case AND
the technical/correlation context — be specific, not "on balance")
Confidence: low / medium / high
```

## Hard rules
- Never skip the bear case, including when you personally already feel
  confident about the bull case from research.md.
- Never skip either specialist, including when the news story looks
  clean — a sector-wide move or an already-extended chart are exactly the
  things a clean news story hides.
- Never let the Technical Context specialist's findings be used to argue
  a trade is MORE likely to win because a mechanical signal matches —
  CLAUDE.md's confluence testing already found no edge there. Use it only
  to catch overextension/conflict risk.
- Never let the bull or bear subagent see the other's output, the
  specialists' opinions (only their facts), or the original research.md
  verdict, before it forms its own case.
- Never let a CANDIDATE from research.md survive council review just
  because downgrading feels like wasted work — the wasted work already
  happened in research.md; the cost of a bad trade idea reaching the user
  is much higher than the cost of a discarded research pass.
- If several tickers in a row all survive council as CANDIDATE, treat that
  as a signal the bear agent's prompt or your own moderation needs to get
  tougher, not as a sign the tickers are all genuinely strong.
