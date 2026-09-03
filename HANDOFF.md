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
5. ~~Run `skills/journal.md` once the WATCH calls are ~5 trading days
   old~~ — **scheduled**, not yet run: a one-shot check-in
   (`trig_01XEBQ2MxWoDMfBftebRXbrR`) fires 2026-09-11 14:00 UTC into this
   same session to do exactly this, across all 9 tickers from both
   2026-09-02 and 2026-09-03 (not just the original 8). If that session
   context is gone by the time this file is read, just run journal.md
   manually against everything in /data/research/2026-09-02/ and
   /data/research/2026-09-03/ — the trigger is a convenience, not the only
   way this gets done. This is how the "Open question"/"9-for-9" sections
   get answered honestly, and per CLAUDE.md's new "Council calibration"
   rule, any resulting recalibration goes to the user first.
6. ~~Test api.massive.com reachability~~ / ~~wire massive_client.py into
   skills/screen.md~~ — both done 2026-09-03. `screen_market_movers()` is
   now step 0 of screen.md (whole-market, equity-only, price/volume
   filtered), with FMP demoted to step 0b (same-day intraday framing +
   earnings calendar, since Massive is always one session behind — see
   RESOLVED section above). Live-tested: 5,315 common-stock tickers
   fetched, 1,356 passed the $5-$500/>1M-volume filter for 2026-09-02 vs
   2026-09-01 — most of those never appeared in FMP's top-50 lists at all
   (SWVL, FCEL, MLYS, OABI, CCOI, SION, UAMY, JLHL, FMC, ASTS, TARS, GIII,
   STDN, WNC, PLAY, VRNS among the top 20 movers alone). **Next: run a real
   screen.md pass with the new pipeline** and push the resulting watchlist
   through research.md/council.md — not done yet this session, this was
   wiring + validation only, not a fresh screen-to-candidate cycle.
   `get_common_stock_tickers()` caches to `/data/reference/equity_tickers.json`
   (gitignored, 7-day freshness) — already fetched once, don't re-fetch
   needlessly (costs ~9 rate-limited API calls, ~70s).

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

## Third batch (2026-09-03): first screen.md run on the new Massive.com pipeline — 8-for-8 now
Ran the newly-wired whole-market screen for real (see RESOLVED: Massive.com
above) — 17 tickers reviewed (11 new, 6 reused verdicts from 2026-09-02:
BIAF, CRDO, DELL, MDB, CNH, GTLB, none of which changed). 2 of the 11 new
names reached CANDIDATE: ASTS (Berenberg Buy init + insider buy) and VRNS
(Bloomberg-reported Proofpoint takeover talks). **Both downgraded to WATCH
by council** — full writeups in `/data/research/2026-09-03/ASTS_council.md`
and `VRNS_council.md`.

| Ticker | Why it didn't clear the bar |
|---|---|
| ASTS | Berenberg's "Buy" init was independently verified to be a 4-stock sector-wide space-coverage launch (Rocket Lab, ASTS, Planet Labs, HawkEye 360), not an ASTS-specific call — undercuts the bull thesis's core premise. Real launch delay to 2027, $1.15B dilutive convert, insider selling far outweighing the highlighted buy. |
| VRNS | This is the SECOND unconverted takeover rumor on this exact ticker in under 3 months (June 2026 Blackstone/Thoma Bravo/Vista report, independently verified, also popped the stock and produced no deal). Citi's target on today's own news sits BELOW the post-pop price. Active securities fraud suit tied to a real Oct 2025 disclosure failure. |

**Running total after this batch: 8-for-8 council downgrades.** This is no
longer "one uncertain week" — it's held across two different screening
methodologies (FMP top-50-based, then genuine whole-market via Massive)
and a wide range of catalyst types (earnings beats, analyst upgrades, M&A
rumors). Still can't be settled without real outcome data (see Open
question above — this note extends it, doesn't replace it), but the
pattern is getting harder to explain away as "just this week's macro."

## Fourth pass, same day (2026-09-03): user explicitly asked "is there ANY buy opportunity" — widened the screen, still 9-for-9
After the 8-for-8 result above, user asked directly whether anything at
all looked buyable. Rather than re-present a rejected name, looked past
the top ~35 movers already reviewed into ranks 36-100 of the same
1,356-name Massive.com filtered list, specifically hunting for distinct
single-name stories rather than sector-wide themes (skipped duplicate
LatAm-fintech/solar/steel clusters, researched one representative each).

Six names checked: KSS, CLF, FOUR, XP all PASS (stale or confirmed
sector-wide, not company-specific). RUN reached WATCH (a real same-day IRS
tax-credit catalyst, but sector-wide and layered on genuine cash-burn
concerns). **ALNY (Alnylam) reached CANDIDATE** — real Phase 3 HELIOS-B
clinical data at ESC Congress 2026, with same-window price-target raises
from five separate desks (TD Cowen, Canaccord, Raymond James, Bernstein,
BMO). This was the strongest-looking case of the whole day.

**Council downgraded it to WATCH anyway.** Full writeup:
`/data/research/2026-09-03/ALNY_council.md`. The decisive fact-checked
finding: at the same ESC Congress, rival AstraZeneca/Ionis's competing TTR
silencer Wainua's detailed trial data showed patients already on
background stabilizer therapy saw NO benefit when a silencer was added —
a live, unresolved mechanism question that applies to Alnylam's own drug
class, not just the failed competitor. Combined with post-crash analyst
targets (Wells Fargo $256, Jefferies $230) sitting near or below the
$246 price, no dated catalyst inside 2 weeks, and an unresolved securities-
fraud investigation into the July guidance-cut disclosure.

**Running total: 9-for-9 council downgrades**, across three separate
screening passes now (FMP top-50, Massive top ~35, and this widened
ranks-36-100 pass). Say this plainly to the user, and DO NOT interpret a
future pass finding a CANDIDATE as license to relax the council process —
if anything ALNY was the best-looking case yet and it still didn't survive
real scrutiny. Only `skills/journal.md` with actual outcome data on the
existing WATCH calls (starting ~2026-09-09, see Sensible next actions)
resolves whether this reflects genuinely risky market conditions or
overly strict moderation — don't let either explanation win by default
just because it's been said out loud enough times.

## Fifth pass, same day (2026-09-03, later): the Sept 3 session actually closed — fresh live data, still nothing
Massive.com's grouped-daily for 2026-09-03 stayed NOT_AUTHORIZED (its
free-tier lag runs longer than "market closed," at least a few hours),
but FMP's live quote timestamps confirmed the real 4pm ET close was in
(20:00:01 UTC) — genuinely fresh same-day data, not a repeat of the
Sept 2 snapshot. Ran a live-intraday FMP screen, excluded a large cluster
of leveraged single-stock crypto ETFs (MSTX, HOOX, COIA, CONL, XXRP, etc.
— all derivative products riding the same BTC move, not real companies),
and researched 8 genuinely new tickers: RARE, PSNY, MEI, MSTR, MARA,
BMNR, AVGO, VALE.

**All 8 came back PASS or WATCH — zero CANDIDATEs, no council.md run
needed.** RARE (-44%) and PSNY (-27.5%) both had clean, well-documented
negative catalysts (a failed Phase 3 trial; a US market-access loss) with
no bounce/overreaction case — this bot is long-only, so a purely negative
catalyst is never a buy setup regardless of size. MSTR/MARA/BMNR all track
a real, datable Bitcoin breakout above $80k (Fed Governor Waller dovish
comments) rather than having distinct company-level news — BMNR in
particular was mischaracterized in the initial screen data as
Bitcoin-adjacent when it's actually an Ethereum treasury company (pivoted
away from BTC mining in June 2025), corrected in its research file. AVGO
had a real catalyst (Q4 guidance miss) but a negative one, same long-only
issue.

**Data-quality flag worth remembering**: VALE, MARA, and BMNR all had
genuinely conflicting figures (price direction or magnitude) across
different WebSearch sources on the same fast-moving day — flagged
explicitly in each file rather than silently picked. Worth a second-source
check before treating any single figure as settled on a volatile session,
especially for a surprising or extreme move.

This doesn't change the running total's substance (still no CANDIDATE
reached council today) but is worth naming as a DIFFERENT kind of result
than the ALNY pass — this time nothing even reached the CANDIDATE bar at
research.md, versus ALNY reaching CANDIDATE and then getting downgraded.
Both are the system working as designed; neither should be read as
evidence either way about calibration on their own.
