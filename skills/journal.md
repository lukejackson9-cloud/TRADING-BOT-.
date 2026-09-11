# Skill: Journal Keeper

Goal: this is the third council member (alongside the bull and bear agents
in skills/council.md), but it doesn't debate a ticker in real time — its
job is memory. It checks what actually happened to past ideas, writes an
honest retrospective, and feeds real lessons back into future
research/council passes so the system can actually improve instead of
re-running the same reasoning fresh every time.

## Why this exists
Without this, research.md and council.md have no memory — every ticker is
evaluated from zero, and there's no way to know whether the bull agent, the
bear agent, or the moderator tends to be right. This closes the loop:
propose an idea → find out what actually happened → write it down honestly
→ let future passes read that history before forming a new opinion.

## Three things this maintains
1. **Trade ledger**: /data/journal/trade_ledger.md — ONE chronological log
   of every ticker-decision (research verdict, council verdict, and the
   outcome once known), not scattered per-ticker files. Built this way
   (2026-09-09, per user request) specifically so it can be read in one
   pass and reflected on before forming a fresh opinion on a new ticker,
   rather than globbing many small files. So the next time GTLB comes up,
   research.md and council.md aren't starting from nothing — grep the
   ledger for the ticker name. (Supersedes the original per-ticker-file
   design — /data/journal/tickers/ is kept only as an empty legacy
   directory, don't resurrect it.)
2. **Cross-ticker lessons**: /data/journal/lessons.md — a short, curated
   digest of patterns that have actually shown up more than once, with
   evidence (dates, tickers, counts) — not vibes. This is what gets read
   at the start of research.md and council.md, kept short on purpose so it
   doesn't bloat every future pass.
3. **Scorecard**: /data/journal/scorecard.md — a running numeric summary
   recomputed from every outcome recorded in step 3 below. This turns
   lessons.md's qualitative patterns into an actual base rate instead of a
   handful of anecdotes, and honestly tracks whether council.md's
   downgrades are net helping or hurting.

## Steps
1. Find ideas worth checking: entries in /data/pending_trades.json (any
   status) whose proposed_at is 5+ trading days old (the CLAUDE.md
   time-stop), plus EVERY ticker with a verdict in
   /data/research/YYYY-MM-DD/{TICKER}.md or _council.md that's 5+ trading
   days old — not just ones that reached council. Restricting outcome-
   checking to council-reviewed CANDIDATEs alone badly under-samples the
   system (most tickers never reach council), so default to the full set:
   every PASS, WATCH, and CANDIDATE verdict is a testable prediction (did
   waiting/skipping turn out to be right?), and checking only the
   headline-grabbing council cases produces an unreliable, cherry-picked
   read on accuracy. Skip a ticker only if there's a specific reason
   (e.g. genuinely no findable price history).
2. For each, use WebSearch to find the ticker's price action since the
   idea/verdict date. You're checking, honestly:
   - If it was a proposed BUY idea: did it hit suggested_stop,
     suggested_target, or run past the time-stop with neither hit?
   - If it was a council WATCH/PASS: did the price move the way the
     concern implied (e.g. faded/pulled back, validating caution), or did
     it keep running (meaning the caution cost a good trade)? Say
     which, plainly — don't spin a miss into a near-win.
3. Update /data/journal/trade_ledger.md: find the ticker's existing entry
   (full narrative entry under "CANDIDATE / Council-reviewed trades" if it
   reached council, or its row in the appendix table otherwise) and change
   its Outcome from PENDING to RESOLVED, adding:
   ```
   **How it ended (RESOLVED {date of this check})**: {price action, with
   a source — prefer scripts/massive_client.py's OHLCV over WebSearch
   summaries when they'd conflict, see lessons.md #2}. {Assessment: correct
   / incorrect / unclear — be honest, "correct" needs the outcome to
   actually match the call, not just "the stock went up eventually"}.
   ```
   If the ticker doesn't have an entry yet (a new one since the last
   ledger update), add one in whichever section fits (full narrative if
   it reached council, appendix row otherwise) rather than skipping it.
4. After resolving a handful of new outcomes (don't do this on every single
   run — only when there's enough new evidence to matter), review
   /data/journal/trade_ledger.md for a real pattern: something that's shown
   up 3+ times, not a one-off. If you find one, update
   /data/journal/lessons.md with a dated bullet, citing the specific
   tickers/dates behind it. Remove or revise old lessons if new evidence
   contradicts them — this file should reflect current best understanding,
   not accumulate forever.
5. Every time you resolve new outcomes, recompute and rewrite
   /data/journal/scorecard.md in full (it's a summary, not an append-only
   log) by tallying every RESOLVED entry's assessment in
   /data/journal/trade_ledger.md, using this template:
   ```
   # Scorecard — updated {date}

   ## Proposed ideas (survived council, reached propose_trades.md)
   Total checked: {N}
   Hit target: {X} | Hit stop: {Y} | Time-stopped, neither hit: {Z} | Unclear: {U}
   Win rate (target vs. stop, excludes unclear/time-stopped): {X}/({X}+{Y}) = {P}%

   ## Council downgrades (research.md CANDIDATE -> council.md WATCH/PASS)
   Total checked: {N}
   Downgrade validated (price faded or didn't continue): {X}
   Downgrade cost a winner (price kept running without us): {Y}
   Unclear: {U}
   Downgrade accuracy: {X}/({X}+{Y}) = {P}%

   ## Research-level WATCH/PASS calls (never reached council)
   The much larger sample: every ticker research.md screened but didn't
   even mark CANDIDATE. Same question as above (did the price move the
   way the PASS/WATCH reasoning implied?) but at a scale council-only
   checking can't reach — most tickers never make it to council, so
   restricting outcome-checking to that subset badly under-samples the
   system's actual accuracy. Use this category by default; the narrower
   "Council downgrades" category above is a useful subset view, not a
   substitute.
   Total checked: {N}
   Call validated (price faded/stayed flat/moved against the thesis,
     matching the PASS/WATCH reasoning): {X}
   Call cost a winner (price moved the way a CANDIDATE would have,
     without us): {Y}
   Unclear: {U}
   Accuracy: {X}/({X}+{Y}) = {P}%

   ## Council calibration (Confidence vs. actual outcome)
   Every council review since 2026-09-11 records a Confidence
   (low/medium/high) and a Near-miss note BEFORE the outcome is known
   (see skills/council.md's hard rules — never adjusted in hindsight).
   Once a reviewed ticker resolves, bucket it here by the Confidence it
   was given at review time:
   High confidence:   {X} correct / {N} resolved ({P}%)
   Medium confidence: {X} correct / {N} resolved ({P}%)
   Low confidence:    {X} correct / {N} resolved ({P}%)
   A well-calibrated system's high-confidence bucket should resolve
   correctly MORE often than its low-confidence bucket — if the rates are
   similar (or inverted), Confidence isn't tracking anything real yet,
   which is itself useful to know and worth saying plainly rather than
   quoting the raw downgrade-accuracy % as if it were calibration. This is
   a stronger signal than the raw accuracy % above once there's enough
   per-bucket sample to compute it (each bucket needs its own N — don't
   report a bucket's % with fewer than ~5 resolved).
   Near-miss tally (informational, not a pass/fail number): {X} reviews
   marked "close" / {N} total reviewed. Report this even at low N — its
   value is qualitative (does council ever record a close call, or is
   every review a blowout) as much as numeric; see skills/council.md's
   "Why this requirement exists" section for what this is checking.

   ## Sample size note
   With this few observations (N < ~20), these percentages are directional
   only, not statistically meaningful — don't let a short streak (in
   either direction) drive a strategy change on its own. Say this plainly
   in reports rather than presenting a percentage without the caveat.
   ```
   If there aren't yet enough outcomes to compute a category, write
   "not enough data yet (N={N})" for that line instead of a fabricated or
   misleadingly precise percentage.

## How research.md and council.md use this
- research.md: before writing a fresh research note, check
  /data/journal/trade_ledger.md for this specific ticker's history (it may
  not have one yet — that's normal). Check /data/journal/lessons.md for
  general patterns.
- council.md: give both the bull and bear agents the same ticker journal
  history (if any) as shared factual background — this doesn't bias which
  side wins, it's just prior track record, not either agent's opinion.
- report.md: when /data/journal/scorecard.md exists, include its headline
  numbers (win rate, downgrade accuracy) in the periodic digest, with the
  sample-size caveat intact — don't quote a percentage without it.

## Hard rules
- Never let the journal's lessons override fresh, specific evidence on a
  new ticker — a pattern from 3 past trades is context, not a rule. State
  it as "worth weighing," not "therefore skip this."
- Never write "correct" or "incorrect" without a specific, sourced
  price-action check. If you can't find enough information to judge the
  outcome, write "unclear" honestly rather than guessing.
- Never quote a scorecard percentage without its sample-size caveat, and
  never let a short streak in scorecard.md (good or bad) drive a change to
  CLAUDE.md's strategy on its own — flag it to the user as a pattern
  worth their attention, let them decide whether to act on it.
- Never let lessons.md grow into a wall of hedge-everything platitudes —
  if a pattern isn't specific and evidenced, it doesn't belong there.
- This skill has no execution capability and never will, same as every
  other skill in this repo (see CLAUDE.md "ACCOUNT CONNECTION STATUS").
