# Replacement prompt for the daily screen routine

Paste this over the prompt of `trig_0149vd3ymUFWFhDyRxza7aA4`
("Daily short-term stock screen") in the session that owns it
(`session_016iH5aNy36JTes3cWw5Geez`). The other two routines — TA and ICT
paper trading — need NO changes; they keep accumulating catalyst data.

---

First: `git pull origin main`. If it conflicts or fails, say so and stop —
do not run on stale code. CLAUDE.md changed substantially on 2026-09-12;
read the "GAME CHANGE" section before anything else.

Then run the 3-12 month fundamental pipeline:

1. **Coverage.** `python scripts/screen_fundamental.py status`. If any names
   are uncovered or stale, `python scripts/screen_fundamental.py cover 200`
   (~45 min, paced at 5 req/min — a 429 is NEVER "this company files
   nothing"). Weekly, refresh the universe first with
   `python scripts/screen_fundamental.py universe`.

2. **Shortlist.** `python scripts/screen_fundamental.py shortlist 10`.
   This is an ATTENTION ORDER, not a return forecast; a low rank is not a
   rejection. Respect the flags: `shares?` means valuation metrics are
   suppressed because the share count could not be corroborated, `shares~`
   means a single uncorroborated source, `tiny-equity` means ROE is the
   denominator collapsing, `no-data(n/4)` means the filing lacks the fields.
   Never read a flagged number as a fact.

3. **Council** (`skills/council.md`). For each shortlisted name run
   `python scripts/fundamentals.py card {TICKER}` and score four dimensions
   1-5, each citing a specific number: business quality, valuation,
   financial health, falsifier. **Nobody has a veto.** A serious flaw is a
   low score, not a rejection. The falsifier states 2-3 *checkable* failure
   conditions and whether any is already true.

4. **Record the ranked picks** — this is the whole point, and it happens
   every day regardless of how good the names are:
   `python scripts/ranker.py pick {DATE} {TICKER} {RANK} high|medium|low {POOL} "{thesis}"`
   Conviction: high 16-20, medium 11-15, low <=10. Record the top 1-3 even
   when the day is weak — "best of a poor day, low conviction" is real data.
   **Skipping a day to protect the record invalidates the measurement.**

5. `python scripts/ranker.py grade` to refresh the running record, then
   commit and push.

6. Report to chat: the top pick and its thesis in two lines. If the day was
   weak, say so plainly. Do NOT walk through every name.

**Hard rules.** Nothing here is a trade proposal, advice, or an order — no
pending_trades.json entry, no T212 call. Price action is not an input at
this horizon. Do not run skills/execute_approved.md. Do not start any new
backtest: CLAUDE.md's RESEARCH PROGRAMME CLOSED section explains why, and
the answer to "but what if we tried X" is in the feature-IC results.
