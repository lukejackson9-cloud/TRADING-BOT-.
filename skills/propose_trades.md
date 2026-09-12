# Skill: Propose Trades

Goal: turn CANDIDATE research notes into a fully-specified, human-readable
trade *idea* for the user to consider — WITHOUT sending any order. In
advisory-only mode (see CLAUDE.md) this is as far as this skill ever goes,
full stop — there is no execution path to hand off to.

## Preconditions
- /data/research/{today}/{TICKER}.md exists and Verdict == CANDIDATE
- /data/research/{today}/{TICKER}_council.md exists (see skills/council.md)
  and its Moderator decision is also CANDIDATE. If council.md hasn't been
  run yet for this ticker, run it first — never propose a trade idea off
  the research.md verdict alone.

## Steps
1. Do NOT call `scripts/trading212_client.py` — there is no connected
   account (advisory-only mode, see CLAUDE.md) and every call would fail
   auth. Do not try to "check" this by calling it anyway.
2. If the user has told you their approximate portfolio value in chat
   recently, use it for a dollar-figure example. Otherwise, size the idea
   purely in **% of portfolio** terms.
3. Compute a proposed position size = 5% of portfolio value (the hard cap
   from CLAUDE.md), expressed as a percentage, or a dollar amount/share
   count only if you have a real portfolio value and a recent price (use
   WebSearch for an approximate current price — flag it as approximate,
   not a live quote).
4. Compute a suggested stop-loss (-4%) and take-profit (+8%) level relative
   to the entry price. These are advisory reference points for the user to
   set themselves in the T212 app — this agent cannot attach or monitor
   live orders.
5. Correlation/concentration check — do this before finalizing size, not
   after. Read every entry in /data/pending_trades.json that isn't
   WITHDRAWN/EXECUTED/FAILED, and everything in /data/positions.json. Ask
   honestly: does this new ticker share a sector or theme (e.g. AI
   infrastructure, regional banks, a single commodity, a single supplier's
   customer base) with any of them? CLAUDE.md's 50% total-exposure cap
   counts dollars, not correlation — three "different" 5% ideas that are
   all really one AI-infrastructure bet isn't diversification, it's a 15%
   concentrated bet wearing three tickers. If you find real overlap:
   - Say so explicitly in the proposal (`correlation_flag` field below) —
     don't silently adjust the size without explaining why.
   - Consider whether the size should be smaller than the standard 5% cap
     given the combined exposure, and say what you'd recommend and why.
   - If there's no real overlap, set `correlation_flag` to `"none"` — an
     explicit "checked, no overlap" is more honest than omitting the field.
6. Append the idea to /data/pending_trades.json as a new entry:
   ```json
   {
     "id": "2026-09-02-NVDA-01",
     "ticker": "NVDA",
     "action": "BUY",
     "size_pct_of_portfolio": 5,
     "est_price": 187.40,
     "suggested_stop": 179.90,
     "suggested_target": 202.40,
     "research_file": "/data/research/2026-09-02/NVDA.md",
     "correlation_flag": "none",
     "status": "ADVISORY_ONLY",
     "proposed_at": "2026-09-02T14:03:00Z"
   }
   ```
   `correlation_flag` example when there IS overlap:
   `"correlation_flag": "Same AI-infrastructure theme as pending idea 2026-09-01-SMCI-01 (still open); combined exposure would be 10%, consider sizing this one at 3% instead of 5%."`
7. Notify via `scripts/clickup_client.py post_report()` if ClickUp is
   configured.

## Hard rule
This skill NEVER calls `place_market_order()` or `place_limit_order()`, and
never calls any other `trading212_client.py` function either, since there is
no connected account in this mode. It only ever writes to
/data/pending_trades.json and optionally notifies via ClickUp.

## Daily ranked pick — ALWAYS run this, including (especially) on a day nothing passes

Added 2026-09-12. This runs **after** council, **regardless of council's
verdict**, and does not depend on anything surviving.

**Why it exists.** Council has downgraded 15 of 15 CANDIDATEs, and
`counterfactual.py` showed those downgrades returned -1.71%/trade against a
date-matched market baseline of -1.71%/trade — identical. Rejecting
everything is not skill, it is an absence of measurement: a system that never
buys never learns whether it can pick. The gate answers *is this good
enough?* and the honest answer is almost always no, because every stock has a
flaw. This answers the different question a buyer actually faces: *of the
names I saw today, which is best, and is the price paying me for the flaw?*

**What to do.** From the shortlist research.md looked at today — NOT only
CANDIDATEs, the whole shortlist including WATCH and PASS — pick the 1-3 you
would most want to own for the next 5 sessions and record each:

```
python scripts/ranker.py pick {DATE} {TICKER} {RANK} high|medium|low {POOL_SIZE} "{one-line thesis}"
```

- `RANK` 1 = your best idea that day. Rank honestly; if rank 1 never beats
  rank 3 the ordering is arbitrary and that is itself the finding.
- `POOL_SIZE` = how many names the shortlist held. "Best of 3" and "best of
  30" are different claims and the grader needs to know which one was made.
- `CONVICTION` is checked for calibration later, the same way journal.md
  checks council's. Do not put `high` on everything; a label that never
  varies carries no information.
- The thesis is required. A pick with no recorded reasoning can only be
  scored right or wrong, never learned from.

**Rules that are not negotiable.**
- This is NOT a trade proposal. Nothing here goes to the user as advice,
  reaches /data/pending_trades.json, or touches the T212 demo account.
- It does NOT change council's verdict or bar. Council stays exactly as
  strict; per CLAUDE.md's 2026-09-03 and 2026-09-09 decisions, only the user
  changes that. This records what the system WOULD have picked, alongside.
- Record a pick even when every name was rejected — that is the whole point.
  If the day's best name was genuinely poor, say so in the thesis and rank it
  anyway with `low` conviction.
- Never skip a day to protect the record. Skipping the unattractive days is
  how a ledger becomes a highlight reel, and it would invalidate the whole
  measurement.
