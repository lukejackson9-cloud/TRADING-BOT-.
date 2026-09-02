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

## Steps
1. Precondition: /data/research/{today}/{TICKER}.md exists with
   Verdict == CANDIDATE.
2. Check if /data/journal/tickers/{TICKER}.md exists (skills/journal.md's
   per-ticker history — past verdicts on this exact ticker and what
   actually happened). If it exists, its content is fair shared background
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
   d. Write the outcome to
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
