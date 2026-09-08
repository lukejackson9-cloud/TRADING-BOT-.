# Session Handoff — last updated 2026-09-06

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

## Sixth pass, same day (2026-09-03, later still): user asked why the daily pool is so small, then to keep going until real coverage was reached
User asked why only ~40 tickers get reviewed when the market has
thousands of stocks — answer: the screen genuinely covers thousands
(5,315 common stocks via Massive, ~150 slots via FMP movers), but only the
biggest movers get individually researched, since that's a deliberate
design choice (momentum strategy = signal concentrates in what's actually
moving; deep research doesn't scale to hundreds of names/day). User then
explicitly asked to keep reviewing until a genuine candidate turns up,
adding "I don't want to only watch a minority." **Important: this was
answered by widening data coverage, NOT by lowering the bar** — see the
exchange in chat where this was made explicit: finding a CANDIDATE cannot
become the goal itself (with 5,000+ stocks, sheer chance guarantees
something will look interesting on a shallow pass — that's noise, not
edge, and is exactly what council exists to catch). If a future session
gets a similar request, hold this same line: widen coverage, keep the same
rigor, don't manufacture a yes.

Widened the live FMP screen from the original 8 tickers (RARE/PSNY/MEI/
MSTR/MARA/BMNR/AVGO/VALE, all PASS/WATCH) through the rest of the
2026-09-03 live movers list — 28 more tickers, 36 total for the day.
Notable finding: **9 tickers that looked like huge individual movers were
actually leveraged/inverse single-stock ETF products** (SMST, CRCG, BULG,
BTDL, MRAL, BMNG, GEMG, GLGG, CONX, PLTZ, HFSP — 2x daily wrappers on
MSTR/CRCL/BULL/BTDR/MARA/BMNR/GEMI/GLXY/COIN/PLTR, not real companies) —
correctly excluded, but worth remembering these show up disguised as
massive movers in any live gainers/losers list and need identity-checking
before research, not just a price/volume filter. Also one confirmed
data-quality failure: RACC's screener-reported -37.4% move could not be
verified against ANY source (real trading range is $24-25, barely moved) —
flagged rather than inventing a catalyst for a move that may not have
happened.

**Two genuine CANDIDATEs surfaced: SPCX (SpaceX, now public) and HPE.**
Both went to council. Both downgraded to WATCH.

| Ticker | Why it didn't clear the bar |
|---|---|
| SPCX | Fresh Oppenheimer target raise + Starship Flight 14 (targeted Sept 15) inside the 2-week window — but the bull's own research found the decisive counter-facts: a real insider-lockup tranche unlocks Sept 9 (independently verified), inside the same window and before the launch even happens, and the only precedent for a Starship test on this stock (Flight 13, July 24) saw shares fall despite technical progress. ~$2T valuation, 51-78x P/S, leaves no room for disappointment. |
| HPE | Genuine Q3 beat-and-raise, but the bull's own research found no dated catalyst inside the 2-week window (next event Sept 30) and that Morgan Stanley cut its target the same day other desks raised theirs (independently verified) — confirming this print validates MS's Nov 2025 memory-supercycle downgrade thesis rather than resolving it. Management itself said supply constraints (DDR5/DDR4/NAND/wafer) may persist "through 2028." Stock already up 120-149% YTD. |

**Running total: 11-for-11 council downgrades**, across four distinct
screening passes now (FMP top-50, Massive whole-market top ~35, a widened
Massive pass to ALNY, and today's full live-intraday FMP pass). Both
today's downgrades were genuinely close calls — both bull agents rated
their own cases weak-to-moderate BEFORE the bear case was weighed, and
both found the decisive counter-fact themselves. That's a meaningfully
different texture than early in this streak (e.g. GTLB's "the target
barely moved" or DUOL's stale JPMorgan number) — the system is finding
real, specific, dated reasons every time now, not generic hedges. Still
not enough to conclude anything on its own — that's still journal.md's
job (see the scheduled 2026-09-11 check-in, now covering all ~76 tickers
across both days' full sessions, not just the 11 that reached council).

## Recurring daily screen set up (2026-09-04)
User asked for the screening pipeline to run daily on its own and notify
them, instead of only running when they ask in chat. Set up
`trig_0149vd3ymUFWFhDyRxza7aA4` ("Daily short-term stock screen") — cron
`30 21 * * 1-5`, ~5:30 PM ET weekdays, bound to this session. See
CLAUDE.md's "Routine Cadence" section for why that time and not the
original 8am/10am split: both data sources confirmed live to only return
fresh, non-stale data once the session has actually closed and settled.
Each firing runs screen → research → council → propose_trades end to end,
commits/pushes its own changes, sends a PushNotification, and posts a
chat summary leading with any surviving CANDIDATE (or a brief "nothing
today" per the Reporting preference). **First live firing: today,
2026-09-04 ~21:30 UTC** — a new session picking this up before then should
know the routine exists and not duplicate it by hand.

Two other standing triggers, for context if a new session needs the full
picture: `trig_01XEBQ2MxWoDMfBftebRXbrR` (one-shot journal.md check-in,
2026-09-11) and nothing else scheduled. All three (this one included) are
bound to the same persistent session, so `list_triggers` from that session
is the source of truth if this file and reality ever drift.

## First live daily-screen firing (2026-09-04): 1 CANDIDATE, downgraded — 12-for-12
Ran Massive's whole-market screen for the just-completed 2026-09-03 session
(1,305 tickers passed filters) plus FMP's live movers for 2026-09-04 itself
(53 new names after excluding leveraged ETFs and everything already
researched). Kept this proportionate to a daily routine, not a repeat of
the prior marathon — researched the 10 most significant, non-duplicate
movers: LULU, GWRE, PATH, TSLA, NFLX, ASAN, AEHR, TITN, SMMT, CLS.

**GWRE reached CANDIDATE, downgraded to WATCH by council.** The decisive,
independently-verified fact: this is the SECOND time in three months GWRE
has run the identical "beat on revenue/EPS, guide down on ARR, crash
10-20%" sequence (same pattern, same analysts trimming targets while
keeping Buy ratings, first time was June 5 2026) — and the recovery from
that first instance took roughly a quarter, not two weeks. Full writeup:
`/data/research/2026-09-04/GWRE_council.md`.

The other 9 were PASS/WATCH at research.md, mostly negative catalysts this
long-only bot has no edge on (LULU, TSLA, PATH, NFLX, ASAN) or real stories
that were already stale/priced-in by the time of research (AEHR, TITN,
SMMT, CLS).

**Running total: 12-for-12 council downgrades**, now across five distinct
screening passes/days. GWRE's repeat-pattern precedent is arguably the
single most concrete piece of evidence in the whole streak — a demonstrated
behavioral precedent on the exact same stock, not a generic valuation or
sector argument. Worth remembering when the Sept 11 journal check-in runs:
GWRE's June 2026 crash-and-recovery is itself now a testable prior case
that could be checked for the scorecard, if the June research/council
files exist somewhere — worth a quick check, not an assumption either way.

## Alpaca client added for skills/monitor.md (2026-09-06)
User asked for live/real-time market access, specifically for intraday
position monitoring (not screening — the daily routine's post-close timing
is deliberate and correct for the strategy, see RESOLVED sections above).
Researched current options: Alpaca Markets gives genuine real-time quotes
free (IEX exchange feed only, ~2-4% of volume, not the full consolidated
tape — good enough to catch a stop/target approach, not execution-grade).
IEX Cloud, the other well-known free real-time option, shut down
permanently in Aug 2024 — don't suggest it if it comes up in old notes or
search results.

Wrote `scripts/alpaca_client.py` (`get_latest_trade`, `get_latest_quote`,
`get_latest_trades` for batches) and wired it into `skills/monitor.md` as
the preferred price source, WebSearch as fallback. Also fixed a stale
Perplexity-API reference left over in monitor.md's step 3 while editing.

**RESOLVED (2026-09-06): user fixed the network policy, confirmed live.**
`data.alpaca.markets` is now reachable and all three client functions
(`get_latest_quote`, `get_latest_trade`, `get_latest_trades`) were run for
real against AAPL/MSFT/TSLA — response shapes match what's now documented
in the script (updated from "unverified" to confirmed).

One real finding from testing on a Sunday (market closed): `get_latest_quote`
showed an unrealistically wide bid/ask spread (~10% on AAPL) — an artifact
of no active market-making while the market is shut, not a data error.
`get_latest_trade`'s last-print price was sane for the same moment.
`skills/monitor.md`/future sessions should prefer `get_latest_trade` over
`get_latest_quote` when checking a position outside active market hours;
the quote endpoint is more meaningful once the market is actually open.
This is genuinely a free real-time feed now available for intraday
position monitoring — not yet exercised in a real `skills/monitor.md` run
against an actual position (no positions in `/data/positions.json` to test
against yet).

## International screening: real gap confirmed, one fragile lead found (2026-09-06)
User pushed on a real, fair concern: everything screened so far has been
US-only, and "surely something globally has a real catalyst." Researched
properly rather than assuming: Massive (US-only equity coverage) and FMP
(blocks non-US symbols on free tier) both confirmed dead ends for
international coverage. Checked Finnhub (no whole-market screener endpoint
at all, just per-symbol lookups), Twelve Data (has an international
movers endpoint but it's confirmed Pro-plan-only), Alpha Vantage
(gainers/losers is US-only anyway), Marketstack (no confirmed screener
endpoint) — none work free. This mirrors the US pattern (screening
capability gated behind paid tiers) but international has no lucky
exception like Massive's grouped-daily was for the US.

**One real lead**: Yahoo Finance's unofficial regional screeners
(`query2.finance.yahoo.com`, e.g. `day_gainers_gb` for the UK) — free, no
key, genuinely international. But it's UNOFFICIAL/UNSUPPORTED — the same
endpoint the `yfinance` library scrapes, known to break or rate-limit
without notice (there's a live GitHub issue against that library titled
exactly that). User explicitly chose to pursue this AND keep WebSearch as
a real, formalized fallback rather than leaning on Yahoo alone.

Wrote `scripts/yahoo_screener_client.py` and a new step 0c in
`skills/screen.md`: Yahoo screener first for international markets,
WebSearch fallback if Yahoo errors, is unreachable, or looks wrong (stale
data, empty results).

**RESOLVED same day: user added the network allowlist entries, confirmed
live.** `get_uk_gainers()`/`get_uk_losers()` both ran for real and returned
genuine data. Two confirmed findings from that live test, both now
documented in the script and screen.md:
1. The GBp/pence gotcha is real, not theoretical — a live quote showed
   `regularMarketPrice: 2.25, currency: "GBp"`, i.e. 2.25 pence (£0.0225),
   not £2.25. Any price filter must check the `currency` field and convert
   before comparing against a dollar-equivalent band.
2. The `_gb` screeners mix genuine UK-domestic stocks (`fullExchangeName`
   `"LSE"`/`"Aquis AQSE"`, priced in GBp) with **International Order Book
   ("IOB") cross-listings** — foreign companies also traded on the LSE but
   priced in their OWN home currency (confirmed live: EUR, SEK, NOK, CHF,
   RON all appeared in one 10-row sample). IOB rows aren't really "UK
   stocks" for research purposes despite showing up in a UK-region
   screener — research/size them in whatever currency they're actually in.

International screening (confirmed for the UK; other region codes are
untested, verify each before trusting) is genuinely live now, alongside
the existing US pipeline (Massive + FMP).

## First full international pipeline test (2026-09-06): fallback chain worked exactly as designed
User asked to run a full screen to test the system. Real, important
finding: **Yahoo's UK predefined screeners (day_gainers_gb, day_losers_gb,
most_actives_gb) are dominated by AIM penny stocks, not genuine liquid
large-cap movers.** Confirmed live: all 72 UK-domestic (LSE/Aquis) rows
across gainers+losers failed a £4-£400 / >1M-volume filter after correct
GBp→GBP conversion — literally zero survived. `most_actives_gb` was no
better (e.g. one stock had 3.5 billion shares of volume at 0.0091p — huge
raw share count, near-zero actual value traded). Unlike FMP's US
most-actives list (AAPL/NVDA/TSLA-caliber names), there's no UK screener
ID found so far that surfaces genuinely liquid, analyst-covered names —
this looks structural (penny stocks naturally dominate "biggest % mover"
and "most shares traded" rankings), not a filter-tuning problem to fix.

**This is exactly the scenario the WebSearch fallback (step 0c) was built
for, and it worked**: switched to WebSearch for "FTSE 100/250 movers this
week," which surfaced two real, dated, sourced catalysts — a Goldman
Sachs double-upgrade on Vodafone (Sell→Buy, target 85p→155p) and a UBS
target raise on Computacenter — plus a third lead (GSK) that research
correctly determined was based on a stale premise (the assumed "this
week" upgrade was actually from May-July) and reported that honestly
rather than manufacturing a catalyst. Full writeups in
`/data/research/2026-09-06/`. VOD.L and CCC.L are both WATCH — real
catalysts, but VOD.L is a lone-outlier-sized upgrade against a still-mixed
Street consensus and real balance-sheet deterioration, and CCC.L is
already near record highs riding a broader sector rally.

**Net assessment of the international pipeline**: the primary layer
(Yahoo screener) is real but currently low-value for the UK specifically
— it finds volatility, not quality. The documented fallback isn't a
backup plan collecting dust, it's carrying the actual useful signal right
now. Worth revisiting whether a different Yahoo screener ID (large-cap-
focused, if one exists for GB) or a different region's screener behaves
better before concluding this pattern holds for every non-US market.

## 2026-09-07: TA/ICT backtesting, execution-policy decision, daily screen
Big session: built and ran two mechanical-strategy backtests per the
user's friend's suggestion, then the user decided to move toward
automatic paper/live execution once a strategy actually earns it.

**TA setups (`scripts/backtest_ta.py`)**: 20-day breakout+volume and
9/21-EMA-crossover, backtested against Massive.com's full 2-year history
(free tier's actual limit, confirmed live — not 3 years as first assumed).
2-month sanity check: ~37-38% win rate, ~0% avg return/trade for both —
no edge. Full 2-year backtest fetch ran most of the day (background
process died once mid-run when this environment doesn't reliably keep a
manually-`nohup`'d process alive across tool calls — switch to the Bash
tool's own `run_in_background` for anything long-running here, it
actually persists). Results pending as of this entry.

**ICT model (`scripts/backtest_ict.py`)**: one specific, coded
interpretation (liquidity sweep of prior-day high/low → market structure
shift → fair value gap entry, NY AM killzone) using Alpaca's free-tier
intraday bars — confirmed live to go back to ~mid-2021 (5 years, deeper
and more granular than Massive's daily-bar limit). 987 trades over 30
large-caps: 32.6% win rate, -0.11R/trade — just under the ~33.3%
breakeven this model's fixed 1:2 R:R needs. No edge, but this tests one
model, not "ICT" broadly.

**Forward paper-trading (`scripts/paper_trader.py` +
`skills/paper_trade_ta.md`)**: automates the TA setups going forward in
real time (not just historical), separate from the advisory pipeline,
wired to a daily routine. Live-tested, works.

**Execution policy change**: user explicitly decided neither TA setup nor
ICT has earned automation yet (correctly — both are flat/negative), but
wants automatic paper/demo execution once one does, and eventually fully
automatic live execution too (no per-trade approval) as a later separate
decision. This revises the project's original absolute "no trade without
human approval" rule — see CLAUDE.md's new "Trade execution & approval"
section for the full staged plan and the mandatory safeguards (fill
notifications, daily-loss circuit breaker, in-code risk-rule enforcement)
that apply regardless of backtest performance. User also sent T212 demo
API key+secret mid-session; stored in .env, connectivity blocked by this
environment's network policy (not yet allowlisted, not urgent since
nothing is being connected until a setup earns it).

**Daily screen**: 10 tickers researched (FMP-sourced; Massive's
whole-market screen was skipped this run to avoid colliding with the
concurrent 2-year backtest fetch's rate limit), 5 WATCH / 5 PASS, zero
CANDIDATEs — consistent with the ongoing calibration pattern.

## 2026-09-07: TradingView alerts bridge (setup pending user action)
User chose the third-party-bridge option for receiving TradingView alerts
(option 2 of 3 presented: connect Gmail / third-party bridge / manual
relay). Plan, since this session can't create the user's Zapier/Google/
TradingView accounts:

1. **User creates a Google Sheet** (header row: Timestamp, Ticker,
   Message) and publishes it to the web as CSV (File > Share > Publish to
   web > CSV). This makes a public, unauthenticated, unguessable CSV URL
   — no Google credential needed on this project's side at all.
2. **User creates a Zapier Zap**: trigger "Webhooks by Zapier" -> "Catch
   Hook" (gives a webhook URL), action "Google Sheets" -> "Create
   Spreadsheet Row" mapped to the sheet from step 1.
3. **User creates a TradingView alert** on their strategy/indicator,
   enables Webhook URL in the alert's Notifications tab, pastes the Zap's
   webhook URL, and formats the alert message as JSON using TradingView's
   placeholders, e.g. `{"ticker": "{{ticker}}", "message":
   "{{strategy.order.action}} at {{close}}", "time": "{{time}}"}`.
   Requires a paid TradingView plan (Essential+) for webhook alerts —
   flagged to the user, not yet confirmed they have one.
4. **User gives this session the published CSV URL**, which goes in
   `.env` as `TRADINGVIEW_ALERTS_CSV_URL`.

Built `scripts/tradingview_alerts_client.py` (reading side) already —
polls the CSV over plain HTTP, tracks a row-count cursor in
`data/reference/tradingview_alerts_cursor.json` (gitignored) so repeated
polls only return genuinely new rows. Not yet wired into any routine
(nothing to poll until the URL exists) and not yet tested live (no real
CSV to test against). Once the user provides the URL: test
`get_new_alerts()` live, then decide with them how alerts should surface
(a routine checking periodically? push notification per alert? logged
only?) — that's a separate design question from the plumbing itself.

Separately, TradingView's own technical-analysis rating (unofficial
`tradingview-ta` library, NOT the alerts bridge above) is already live —
see scripts/tradingview_client.py, wired into skills/research.md as an
optional cross-check.

## 2026-09-08: Daily screen -- TARS reaches council, downgraded (13-for-13)
Second daily-screen firing since Labor Day (09-07 was a holiday, no new
session). Ran Massive's full whole-market screen this time (free of the
backtest fetch that blocked it yesterday) and found real candidates FMP's
top-15 lists missed: TYRA, PSQL, GOLD, RACC, TARS, CHPT, ADSK, KLAC, ALAB,
NBIS. Confirmed KLAC/ALAB/NBIS (plus AXTI/TSEM/FORM/UCTT/TTMI/SMTC/BE)
were one correlated sector-wide semiconductor/AI-infra rally, not
independent stories.

**TARS reached CANDIDATE** (real converging catalysts: Alkeus acquisition
close + Jefferies Strong-Buy upgrade to $105, both dated 2026-09-04) --
first CANDIDATE since GWRE/HPE on 2026-09-04. Council review: bull and
bear agents, working independently with no visibility into each other,
both surfaced the SAME major risk cluster (an unresolved, unrebutted
Culper Research anti-kickback allegation on TARS's only approved product;
real dilution from the Alkeus deal's financing at $61.38/share vs. ~$90
current; insider selling with zero buying) -- that unprompted convergence
was treated as strong evidence, not coincidence. The bull agent's own
honest confidence was only low-medium despite being tasked with building
the strongest case FOR. Moderator downgraded to WATCH. Along the way,
fact-checked and resolved a price-data conflict the bull agent flagged
(wildly inconsistent WebSearch-sourced prices) using Massive.com's own
OHLCV directly -- same lesson as the DOCU case from 2026-09-06, precise
market data beats ambiguous WebSearch summaries.

**Running council-downgrade total: 13-for-13** (9-for-9 as of 2026-09-03,
+GWRE/+HPE on 09-04, +TARS today). Per CLAUDE.md's calibration rule, this
is reported plainly and is not itself being read as proof of
miscalibration -- the 2026-09-11 journal.md check-in remains the actual
answer to that question.

Also corrected: ticker GOLD is no longer Barrick (renamed Barrick
Mining/"B" in 2025) -- now Gold.com Inc. And RACC's screener-implied move
could not be verified against any live source for the second time (same
issue flagged 2026-09-03) -- worth considering whether RACC's data is
just unreliable at the source and should be filtered out going forward
rather than re-litigated each time it appears.
