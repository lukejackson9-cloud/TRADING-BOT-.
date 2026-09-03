# Session Handoff — last updated 2026-09-03

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

## RESOLVED (2026-09-03): Massive.com (formerly Polygon.io) — real whole-market screener, confirmed live
User asked what other free market-screener options exist beyond FMP (whose
free tier only exposes a curated top-50 gainers/losers/actives list, not a
true whole-market filter — see RESOLVED/FMP section above). Researched real
2026 free tiers (WebSearch, not memory — these change often): Finnhub (60
calls/min, no whole-market screener endpoint though), Alpha Vantage (down
to 25 requests/DAY, unusable), EODHD (20/day, also too thin), Twelve Data
(800/day, 8/min). **Massive.com stood out**: its `/v2/aggs/grouped/...`
endpoint returns every US stock's OHLCV for a whole day in ONE call — a
genuine whole-market screen, not a top-N list.

User provided `MASSIVE_API_KEY` (now in `.env`) and initially both
`api.massive.com` and `api.polygon.io` were blocked by this environment's
network policy — user then fixed the network setting. **`api.massive.com`
is now confirmed reachable and `scripts/massive_client.py` was run live**:
`get_grouped_daily('2026-09-02')` returned `status: OK, resultsCount:
12541` with the exact response shape documented in the script (fields `T`
ticker, `o`/`h`/`l`/`c` OHLC, `v` volume as a float not always int, `vw`
VWAP, `t` ms-epoch timestamp, `n` trade count). `api.polygon.io` (the old
domain) is STILL blocked — irrelevant, the client only uses
`api.massive.com`.

**One real finding from the live test**: the grouped-daily payload
includes ALL US securities, not just single-name equities — XRP (a
cryptocurrency) showed up in the results. Price/volume filtering alone
won't exclude ETFs or other non-equity tickers; screen.md's ticker list
should filter by a known-equity check (or against a maintained exclude
list, same idea as the leveraged-ETF exclusion already used with FMP's
movers lists) before treating a grouped-daily hit as a stock candidate.

**Recommended going forward**: prefer `massive_client.get_grouped_daily()`
for the price/volume screening step (whole market in one call, 5 req/min
free tier easily covers this) over FMP's top-50 movers lists. Keep FMP for
gainers/losers *framing* (useful context even if not comprehensive) and
its earnings-calendar endpoint, which massive_client.py doesn't replace.
Not yet wired into skills/screen.md itself — that's the next step, not
done this session.

## Keys — must be recreated, they are NOT in the repo
`.env` is gitignored (correctly — secrets never get committed), so a fresh
clone has no keys. `cp .env.example .env` and ask the user to re-paste:
- `FMP_API_KEY` — works today, real but limited (see RESOLVED above)
- `MASSIVE_API_KEY` — works today, confirmed live 2026-09-03 (see above)
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

(See "Open question" further down — merged with the second batch's result
rather than duplicated here.)

## Sensible next actions
1. ~~Test the FMP domain~~ — done, see "RESOLVED" above.
2. ~~Run research.md + council.md on the 15 FMP-screened candidates~~ —
   done, see "Second batch" below. **Next: nothing urgent from this batch**
   — 0 CANDIDATEs survived council, so there's nothing to propose today.
3. **ORCL reports ~2026-09-09** — research the actual reaction that day.
   FMP's calendar doesn't confirm or deny this date (see above); keep using
   the WebSearch-sourced estimate until closer to the date.
4. **DOCU reports 2026-09-03 (tomorrow as of this writing)** — same
   pre-catalyst treatment as ORCL; research the actual reaction once it
   prints, don't research the "will it beat" question again.
5. Run `skills/journal.md` once the original 8 WATCH calls are ~5 trading
   days old (i.e. from ~2026-09-09) to check what actually happened and
   start the scorecard. This is how the "Open question" section near the
   bottom of this file gets answered honestly — it covers both batches
   now, not just the first 8.
6. ~~Test api.massive.com reachability~~ — done, confirmed live 2026-09-03,
   see "RESOLVED: Massive.com" above. **Next: wire `massive_client.py`
   into `skills/screen.md`** as the primary price/volume filter (replacing
   or supplementing the FMP-movers-based approach), with an equity-only
   filter added (grouped-daily includes ETFs/crypto — see the finding
   above). Not done yet — worth doing before the next screen.md run so
   that run gets genuine whole-market coverage instead of FMP's top-50.

## Second batch (2026-09-02, same day, after FMP screen): 15 reviewed, 2 reached council, 0 survived
DELL and SOFI both made CANDIDATE in research.md; both got downgraded to
WATCH in council.md. Full writeups: `/data/research/2026-09-02/DELL.md`,
`DELL_council.md`, `SOFI.md`, `SOFI_council.md`.

| Ticker | Why it didn't clear the bar |
|---|---|
| DELL | Real Q2 FY27 beat-and-raise, but a climax-volume single-day 16% pop already at consensus target; Evercore ISI pulled it from their own "Tactical Outperform" list right after the print — verified, not just cited. Bull agent's own self-assessment called it weak before the bear case even weighed in. |
| SOFI | Real, dated Scotiabank initiation today, but most of the bounce pre-dates that catalyst, stock is still below all 3 major moving averages, broader 15-analyst consensus is still Hold, and a live bond-yield spike hits this exact rate-sensitive business model. Closer call than DELL — not a knockout, but ties go to WATCH per council.md's rule. |

The other 13 (BIAF, CNH, ONDS, IREN, NU, CDE, RIG, PLTR, PCG, NVDA, MDB,
CRDO, DOCU) never reached CANDIDATE in research.md — mostly stale catalysts
already priced in, sector-beta moves with no single-name cause, or (DOCU)
the pre-catalyst earnings cap. Full reasoning in each `{TICKER}.md`.

## Free-tier data-quality note carried over from this batch
Two research subjects (MDB, CRDO) had FMP-unconfirmed volume per the
RESOLVED section above — research.md's WebSearch pass confirmed both are
normal, liquid, well-covered large/mid-caps reacting to their own earnings,
not a data-quality problem. Worth remembering FMP's free-tier volume gate
doesn't mean "illiquid," just "not on FMP's free allowlist" — don't treat
an UNCONFIRMED tag as a red flag on its own, always check WebSearch before
discarding a name on that basis alone.

## Open question — do not quietly ignore this, it just got a bit more data
Going 0-for-8 on the first batch, then 0-for-2-at-council on this second
batch (6-for-6 council downgrades total today, all 2026-09-02), is a real
signal and it's **still unresolved which way it cuts**:
1. Genuinely uncertain macro week (elevated bond yields — literally the
   highest since Oct 2023 as of yesterday per this batch's SOFI research —
   Iran/oil tension, rotation out of the AI trade) and the caution is
   earning its keep, or
2. Council moderation has calibrated too strict now that it's actually
   being applied with rigor.

One data point worth naming: this batch's downgrades were closer calls
than the first batch's (DELL and SOFI both had genuinely real, dated,
verified catalysts; the bear case had to work harder than "the target
fell" or "the pop already happened" alone). That's weak evidence toward
(1) over (2), but it's not enough to call it — `skills/journal.md` with
real outcome data is still the honest way to settle this, not more
narrative pattern-matching. Flag both batches to the user together next
time this comes up, don't treat them as separate open questions.
