# Session Handoff — last updated 2026-09-02

Read this after CLAUDE.md when picking this project up in a new session.
CLAUDE.md is the permanent ruleset; this file is "where we actually got to."

## Who this is for / what the user wants
- £1000, explicitly **speculative money** — user confirmed they're fine with
  a 20-30% drawdown and treat this as engagement/learning as much as returns.
- They want **short-term trade ideas** (days to ~2 weeks), NOT long-term
  index investing. They act on any advice manually in the Trading 212 app.
- They have repeatedly asked for **honest, realistic** output over
  optimistic output. Take that seriously — they pushed back (correctly)
  when an early screen was too shallow, and that pushback improved the
  system. Do not soften bad news or manufacture a pick to seem useful.

## Current mode (see CLAUDE.md for the binding rules)
- **Advisory-only. No brokerage connection.** User gave a T212 API *key*
  but deliberately withheld the *secret*. This is intentional — they don't
  want the bot touching their account. `skills/execute_approved.md` is inert.
- Research runs on **Claude Code's built-in WebSearch**, not Perplexity —
  the user declined to set up a paid Perplexity subscription.
  `scripts/perplexity_client.py` is dead code kept for reference.

## The council (skills/council.md + skills/journal.md)
Three members: independent **bull** and **bear** subagents (never see each
other's work), with **you moderating** and fact-checking their load-bearing
claims, plus the **Journal Keeper** (skills/journal.md) for memory across
time. Every CANDIDATE must survive council before reaching the user.

## BLOCKED: market screener needs a network allowlist entry
`scripts/market_screener_client.py` (Financial Modeling Prep) is written and
ready — it gives screen.md a real whole-market screener instead of guessing
at WebSearch terms. **It cannot run until `financialmodelingprep.com` is
added to this environment's network allowlist** (claude.ai/code → cloud icon
→ gear → Network access → Custom).

**First thing to do in a new session**: test it, don't assume.
```bash
curl -sS --max-time 10 -o /dev/null -w "%{http_code}\n" https://financialmodelingprep.com
```
- If it connects: the screener works. Run a real market-wide screen — this
  is the big upgrade the user has been waiting for.
- If it 403s: still blocked. Tell the user plainly, fall back to WebSearch.

## Keys — must be recreated, they are NOT in the repo
`.env` is gitignored (correctly — secrets never get committed), so a fresh
clone has no keys. `cp .env.example .env` and ask the user to re-paste:
- `FMP_API_KEY` — the one that actually matters right now
- `T212_API_KEY` — optional, unusable without the secret anyway

## Where we got to (2026-09-02)
Reviewed 8 tickers. **All 8 came out WATCH. Zero buys.** Full research and
council writeups are in `/data/research/2026-09-02/`.

| Ticker | Why it didn't clear the bar |
|---|---|
| DUOL | Closest call of the day — real bounce + Evercore's doubled target, but 2026's own guidance shows margin compression (25% vs 29.5%) |
| SIRI | Real turnaround metrics, but the +7.5% pop already happened; structural subscriber/vehicle-conversion risk unresolved |
| HOOD | Strong 4-firm analyst cluster, undercut by live legal attack on the exact growth segment (9th Circuit already ruled against Robinhood) |
| GTLB | Real earnings beat, but already +20% and consensus target didn't follow the pop |
| IHG | UBS's $188 target contradicts other sources' $134-159 estimates |
| CAT | Good business, no fresh 1-2 week trigger, already +32.6% YTD |
| OGE | Modest upgrade against an unresolved Oklahoma rate case + revenue miss |
| ORCL | Pre-catalyst — **earnings ~2026-09-09**, hard-capped at WATCH until it prints |

## Open question — do not quietly ignore this
Going 0-for-8 is a real signal and it's **unresolved which way it cuts**:
1. Genuinely uncertain macro week (elevated bond yields, Iran/oil tension,
   rotation out of the AI trade) and the caution is earning its keep, or
2. Council moderation has calibrated too strict now that it's actually
   being applied with rigor.

This is logged in `/data/trades.log`. Don't assume either answer — once
`skills/journal.md` has outcome data on these WATCH calls, the scorecard
answers it with evidence. Flag the pattern to the user, let them weigh in.

## Sensible next actions
1. Test the FMP domain (above). If unblocked, run a real screen.
2. **ORCL reports ~2026-09-09** — research the actual reaction that day.
3. Run `skills/journal.md` once these WATCH calls are ~5 trading days old
   (i.e. from ~2026-09-09) to check what actually happened and start the
   scorecard. This is how the 0-for-8 question gets answered honestly.
