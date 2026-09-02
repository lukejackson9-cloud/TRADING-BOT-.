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

## RESOLVED (2026-09-02): FMP is reachable, and free-tier limits are now mapped
The earlier network block is gone in this environment — `financialmodelingprep.com`
answers normally. `scripts/market_screener_client.py` now targets FMP's
`/stable/` namespace; the old `/api/v3/` paths are retired for any key made
after 2025-08-31 ("Legacy Endpoint" error) — if a future session sees that
error again, re-check FMP's docs before assuming the key is bad, not before.

**Free-tier ceiling found by actually calling it, not guessing:**
- `/stable/biggest-gainers`, `/biggest-losers`, `/most-actives`,
  `/earnings-calendar` all work and return real whole-market movers.
- `/stable/quote` (needed for volume) only works for a curated allowlist of
  large/liquid symbols (confirmed: AAPL, AAL, F, INTC, NOK, NVDA, PFE, PLTR,
  SOFI, T, TSLA) — any other symbol 402s with "Special Endpoint... not
  available under your current subscription." So volume can be verified
  precisely only for that allowlist; for everything else the fallback is
  "did it also appear in most-actives" (real proxy, most-actives is
  volume-sorted) or, failing that, an explicit UNCONFIRMED flag rather than
  assuming it's liquid.
- `/stable/stock-screener` and `/company-screener` (the actual whole-market
  price/volume/sector filter) are both gated on the free tier — empty `[]`
  or an explicit "Restricted Endpoint" message. So there's no single call
  that replaces the old workflow; screen.md now does gainers+losers+actives
  unioned, price-filtered client-side, volume-checked as above.
- `/stable/earnings-calendar` is real but sparse on the free tier — only 17
  entries market-wide across 2026-09-01 to 2026-10-15. It does **not**
  contain ORCL at all in that window, which neither confirms nor refutes
  the ~09-09 WebSearch-sourced guess below — treat the calendar as
  incomplete, not authoritative, until proven otherwise.

Net effect: this is a real upgrade over WebSearch-guessing for gainers/
losers/actives/earnings-calendar breadth, but it is not the fully-verified
whole-market screener the original plan assumed — some volume claims below
are confirmed, some are "appeared in most-actives" (a fair proxy), and a
few are flagged unconfirmed and pushed to research.md/WebSearch to verify
before they can become CANDIDATEs.

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
1. ~~Test the FMP domain~~ — done, see "RESOLVED" above. **Next: run
   `skills/research.md` on today's new FMP-screened candidates below** (they
   have not been researched or council-reviewed yet — screen.md only
   narrows the list, per its own step 6).
2. **ORCL reports ~2026-09-09** — research the actual reaction that day.
   FMP's calendar doesn't confirm or deny this date (see above); keep using
   the WebSearch-sourced estimate until closer to the date.
3. Run `skills/journal.md` once these WATCH calls are ~5 trading days old
   (i.e. from ~2026-09-09) to check what actually happened and start the
   scorecard. This is how the 0-for-8 question gets answered honestly.

## New candidates from the 2026-09-02 FMP screen — NOT yet researched
`config/watchlist.txt` now has 15 new tickers added by a real FMP-based
screen (see script docstring / RESOLVED section above for methodology):
DELL, BIAF, CNH, ONDS, IREN, NU, CDE, RIG, SOFI, PLTR, PCG, NVDA, MDB, CRDO,
DOCU (DOCU is EARNINGS 2026-09-03 pre-catalyst, not yet a candidate per
screen.md's hard rule). MDB and CRDO have unconfirmed volume (see above) —
have research.md sanity-check liquidity via WebSearch before treating them
as real candidates, not just their price move. None of these 15 has been
through `skills/research.md` or `skills/council.md` yet — that's the next
session's job, same two-step gate as the original 8 (see table above).
