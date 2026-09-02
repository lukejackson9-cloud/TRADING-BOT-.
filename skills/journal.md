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

## Two things this maintains
1. **Per-ticker history**: /data/journal/tickers/{TICKER}.md — every time
   this ticker is screened, researched, put through council, or its
   outcome is checked, append an entry. So the next time GTLB comes up,
   research.md and council.md aren't starting from nothing.
2. **Cross-ticker lessons**: /data/journal/lessons.md — a short, curated
   digest of patterns that have actually shown up more than once, with
   evidence (dates, tickers, counts) — not vibes. This is what gets read
   at the start of research.md and council.md, kept short on purpose so it
   doesn't bloat every future pass.

## Steps
1. Find ideas worth checking: entries in /data/pending_trades.json (any
   status) whose proposed_at is 5+ trading days old (the CLAUDE.md
   time-stop), plus any WATCH/PASS verdicts in recent
   /data/research/YYYY-MM-DD/{TICKER}.md or _council.md files that are
   worth a look back (a WATCH is a testable prediction — did waiting turn
   out to be right?).
2. For each, use WebSearch to find the ticker's price action since the
   idea/verdict date. You're checking, honestly:
   - If it was a proposed BUY idea: did it hit suggested_stop,
     suggested_target, or run past the time-stop with neither hit?
   - If it was a council WATCH/PASS: did the price move the way the
     concern implied (e.g. faded/pulled back, validating caution), or did
     it keep running (meaning the caution cost a good trade)? Say
     which, plainly — don't spin a miss into a near-win.
3. Append an entry to /data/journal/tickers/{TICKER}.md:
   ```
   ## {date of this check} — reviewing {date of original idea/verdict}
   Original call: {verdict/idea and why}
   What actually happened: {price action, with a source}
   Assessment: correct / incorrect / unclear (be honest — "correct" needs
   the outcome to actually match the call, not just "the stock went up
   eventually")
   ```
4. After appending a handful of new outcomes (don't do this on every single
   run — only when there's enough new evidence to matter), review
   /data/journal/tickers/*.md for a real pattern: something that's shown up
   3+ times, not a one-off. If you find one, update
   /data/journal/lessons.md with a dated bullet, citing the specific
   tickers/dates behind it. Remove or revise old lessons if new evidence
   contradicts them — this file should reflect current best understanding,
   not accumulate forever.

## How research.md and council.md use this
- research.md: before writing a fresh research note, check if
  /data/journal/tickers/{TICKER}.md exists and skim it for this specific
  ticker's history. Check /data/journal/lessons.md for general patterns.
- council.md: give both the bull and bear agents the same ticker journal
  history (if any) as shared factual background — this doesn't bias which
  side wins, it's just prior track record, not either agent's opinion.

## Hard rules
- Never let the journal's lessons override fresh, specific evidence on a
  new ticker — a pattern from 3 past trades is context, not a rule. State
  it as "worth weighing," not "therefore skip this."
- Never write "correct" or "incorrect" without a specific, sourced
  price-action check. If you can't find enough information to judge the
  outcome, write "unclear" honestly rather than guessing.
- Never let lessons.md grow into a wall of hedge-everything platitudes —
  if a pattern isn't specific and evidenced, it doesn't belong there.
- This skill has no execution capability and never will, same as every
  other skill in this repo (see CLAUDE.md "ACCOUNT CONNECTION STATUS").
