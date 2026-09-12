# Skill: Council Review

Goal: pressure-test a CANDIDATE verdict from skills/research.md before it's
allowed to reach skills/propose_trades.md, using independent adversarial
perspectives — so one enthusiastic research pass doesn't turn into
overconfident advice. This step only runs on tickers already marked
CANDIDATE; WATCH/PASS tickers don't need it.

## Why this exists
CLAUDE.md already says "CANDIDATE should be rare... require a real
catalyst." A single research pass can still talk itself into a good story,
especially once it's already found a catalyst it likes. This runs a
structured, adversarial second look — closer to a real investment
committee than a single analyst — before anything reaches the user as
advice. The point isn't theater: if this step never downgrades anything,
it isn't doing its job, and that should be said out loud, not hidden.

## The failure mode this is designed to avoid
Multi-agent setups usually fail by having every "agent" agree with
whatever the first one said — the illusion of scrutiny without the
substance. This design avoids that on purpose:
- The bull and bear agents each research and write independently — neither
  ever sees the other's output, or your framing of the ticker, before
  forming its own case. No anchoring.
- Both are told explicitly to be honest, not persuasive: a weak bull case
  should say it's weak; a bear case that finds nothing real should say so
  rather than manufacturing doubt.
- The bear case is mandatory even when the bull case looks obviously
  strong — that's exactly when overconfidence does the most damage.
- You (the moderator) do not default to the bull case. Ties, or "not
  clearly weaker," go to WATCH/PASS, not CANDIDATE.

## Why this requirement exists (14-for-14 downgrades, added 2026-09-11)
As of 2026-09-11 every single CANDIDATE that has ever reached council (14
for 14, see scorecard.md) has been downgraded. That streak is genuinely
consistent with two very different explanations, and this design as
originally written can't tell them apart:
1. The market really is that unforgiving for this project's screening
   criteria and horizon, and skepticism is correctly earning its keep
   (scorecard.md's 90.9% downgrade-validation rate is real evidence for
   this).
2. Step c above ("does the bull case clearly survive the bear case")
   means bull must win on EVERY point while bear only needs ONE — by that
   rule, a 100% downgrade rate is what the rule produces mechanically,
   whether or not council's actual calibration is any good. A structural
   rule can't be validated by its own output volume.
This project's data can't fully separate these two explanations yet (14
CANDIDATEs is a small sample, and there's no recorded case where bull
came close but still lost — every review before this fix recorded only
the final verdict). Two changes address this without loosening anything:
- The falsifiability requirement above makes bear's objections concrete
  enough to fact-check instead of "vague risk = automatic loss" (a vague
  risk is cheap for bear to raise and hard for bull to overrule, which
  could explain part of the streak on its own, independent of whether the
  underlying calls are right).
- The near-miss field (step e below) starts recording, per review,
  whether bull came close — not to change today's verdict, but so a
  future pass (or the user) can look back and tell whether the gate is
  well-tuned or just permanently closed. Do not let a string of "not
  close" near-miss notes become a reason to loosen the verdict rule on
  its own — that's still the user's call per CLAUDE.md's standing
  2026-09-03 decision. This is diagnostic instrumentation, not a policy
  change.
Do NOT add a third generic debate seat (another bull- or bear-style
agent) to address this — one more agent arguing the same bull/bear frame
most likely just adds another "no" vote, not new information, and makes
the review harder to audit without adding real sample size. If a
genuinely new failure mode is identified (like the "stale story despite a
pending dated catalyst" pattern AEHR exposed), give it a narrow,
falsifiable check tied to that specific pattern — as done above for the
sell-the-news case — rather than a generic peer.

## Steps
1. Precondition: /data/research/{today}/{TICKER}.md exists with
   Verdict == CANDIDATE.
2. Check /data/journal/trade_ledger.md for this ticker (skills/journal.md's
   trade ledger — past verdicts on this exact ticker and what actually
   happened). If it has an entry, that content is fair shared background
   for BOTH agents below — it's factual track record, not either agent's
   opinion, so handing it to both doesn't bias which side wins.
3. Spawn two subagents in parallel with the Agent tool. Give each ONLY the
   ticker, today's date, and the journal history from step 2 if any — not
   the research.md file, not each other's output, not your own opinion of
   the trade:
   - **Bull case agent**: research and build the strongest honest case FOR
     entering this trade. Use WebSearch for its own sources — don't just
     hand it research.md's citations to rephrase. Must cite real,
     checkable sources for every factual claim. Explicitly instructed:
     if the case is weak, say so plainly rather than inflating it.
   - **Bear case / risk critic agent**: research and build the strongest
     honest case AGAINST entering. Actively hunt for reasons this could be
     a trap: is the move already exhausted / already priced in, is there a
     sector headwind, insider selling, a valuation red flag, guidance that
     sounds better than the underlying numbers, a pattern resembling past
     failed breakouts in similar names. Must cite real sources for every
     claim, not vague hedging.
     **Falsifiability requirement (added 2026-09-11, see "Why this
     requirement exists" below)**: every objection must be a specific,
     checkable claim with a concrete "this would be wrong if X" condition
     — e.g. "this catalyst is already priced in because the stock moved
     +12% on the news day itself, per {source}" (checkable: was there
     actually a same-day pop that size?) or "there's a dated event on
     {date} that could reignite this even though the initial move has
     faded" (checkable: does that event exist and is it still pending?).
     A generic risk with no concrete condition ("sentiment could turn",
     "valuation looks stretched", "this could be overextended") is not
     acceptable on its own — if that's genuinely the best objection
     available, the agent must say the case against is weak, the mirror
     image of the bull agent's instruction to say a weak bull case is
     weak. **Specifically applies to any "stale story" / "already priced
     in" / "sell the news" objection**: it must explicitly state whether
     it checked for a known, dated, still-upcoming catalyst (an earnings
     date, a conference, a data readout, an FDA decision) and found none
     — not just assert staleness because the initial move already
     happened. AEHR (2026-09-04 WATCH, missed a further +69% into a
     2026-09-10 investor conference — see lessons.md #1's counter-example)
     is the concrete case this exists to catch: "every driver is 3+ weeks
     stale" was true and still the wrong call, because a live dated event
     was still ahead of it.
4. Once both return, act as moderator yourself — this step is not
   delegated:
   a. Fact-check both cases against their own cited sources. Reject or
      flag any claim you can't verify was actually said by the source
      (CLAUDE.md's "never fabricate research" rule applies here too).
   b. Weigh them honestly against each other. The bull case does not win
      by default, and having already called this a CANDIDATE in
      research.md is not a reason to protect that verdict.
   c. Decide: does the bull case clearly survive the bear case, with
      real, sourced substance? Only then does CANDIDATE stand.
   d. Reject any bear objection that fails the falsifiability requirement
      above (generic, no concrete checkable condition) before weighing
      it — note in the fact-check section that it was discounted and why,
      don't just quietly not mention it.
   e. Record how close it was, not just the verdict: did the bull case
      come close to surviving (a real, specific, sourced case that only
      lost to one strong bear point), or was it a clear blowout either
      way? This is the "near-miss" field in the template below — see "Why
      this requirement exists" for why this is tracked even though it
      doesn't change today's verdict.
   f. Write the outcome to
      /data/research/{today}/{TICKER}_council.md using the template below.
5. Only a ticker that keeps CANDIDATE status after this step moves to
   skills/propose_trades.md. A downgrade here is a normal, expected
   outcome — tell the user plainly when it happens and why, don't bury it.

## Council note template
```
# {TICKER} — Council Review — {date}

## Bull case (from independent agent)
Summary:
Key sources:

## Bear case (from independent agent)
Summary:
Key sources:

## Fact-check notes
(claims from either side you couldn't verify against their cited source,
or corrected)

## Moderator decision
Verdict: CANDIDATE | WATCH | PASS
Reasoning: (why the bull case did, or didn't, survive the bear case —
be specific, not "on balance")
Near-miss: (blowout either way / close — bull had a real, specific,
sourced case that lost to exactly one strong bear point) — recorded for
every review regardless of verdict, see "Why this requirement exists"
above
Discounted bear claims: (any bear objection rejected under the
falsifiability requirement above, and why — "none" if all objections were
concrete and checkable)
Confidence: low / medium / high
```

## Hard rules
- Never skip the bear case, including when you personally already feel
  confident about the bull case from research.md.
- Never let the bull or bear subagent see the other's output, or the
  original research.md verdict, before it forms its own case.
- Never let a CANDIDATE from research.md survive council review just
  because downgrading feels like wasted work — the wasted work already
  happened in research.md; the cost of a bad trade idea reaching the user
  is much higher than the cost of a discarded research pass.
- If several tickers in a row all survive council as CANDIDATE, treat that
  as a signal the bear agent's prompt or your own moderation needs to get
  tougher, not as a sign the tickers are all genuinely strong.
- Never record Confidence or Near-miss retroactively adjusted toward
  whatever the eventual outcome turned out to be — both are written the
  day of the review, before the outcome is known, specifically so
  skills/journal.md can later check calibration (does "high confidence"
  actually predict being right more often than "low confidence" does)
  honestly against a real prediction, not a hindsight-adjusted one.
