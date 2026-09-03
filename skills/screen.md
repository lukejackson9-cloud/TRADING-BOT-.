# Skill: Screen

Goal: produce a short list (5–15 tickers) of candidates worth researching today.

## Steps
0. Primary source: `scripts/massive_client.py` — a genuine whole-market
   screen, not a curated top-N list (confirmed live 2026-09-03: 5,315 US
   common-stock tickers, 1,356 of them passing the price/volume filter on
   a single real trading day — FMP's free-tier top-50 lists miss the large
   majority of that).
   - `screen_market_movers(date, prev_date)` returns every common-stock
     ticker priced $5–$500 with >1M volume, ranked by |% change| close-to-
     close between the two dates. Defaults already match step 3's filters
     and exclude non-equity tickers (ETFs, etc. — see the module docstring
     on why that filter exists).
   - **Massive's data is END-OF-DAY, one session behind** — requesting the
     still-open current trading day returns `NOT_AUTHORIZED`, not partial
     data (confirmed live). `date`/`prev_date` must be the last two
     COMPLETED trading days (skip weekends/holidays; if a chosen date
     comes back empty or non-OK, step back a day and retry — don't trust
     an empty result as "no movers today").
   - Take the top ~30 by |% change| from `screen_market_movers()`'s output
     as this step's working pool — that's deliberately wider than the
     5–15 final target, because research.md's skepticism is what narrows
     it the rest of the way (see step 5), and a whole-market screen will
     surface far more real movers than a top-50 list ever could.
   - If the call errors on a network/connection error (not an auth error),
     that's likely this environment's network policy blocking
     `api.massive.com` — don't retry blindly (same rule as T212 in
     CLAUDE.md). Fall back to step 0b for this run, and mention to the
     user once per session that Massive is unreachable.
0b. Supplement: `scripts/market_screener_client.py` (FMP) — Massive covers
    breadth but is always a day stale, so use FMP for what it's actually
    good for instead of duplicating step 0:
    - `get_gainers()` / `get_losers()` / `get_most_active()` for genuine
      SAME-DAY intraday framing — useful context on top of Massive's list,
      and a way to catch a move that started after Massive's last
      completed session.
    - `get_earnings_calendar(from_date, to_date)` for step 2's lookahead,
      with real dates instead of a WebSearch guess. Free-tier coverage is
      sparse (~17 entries across a 6-week window as of 2026-09-02) — treat
      it as incomplete, not authoritative; it may simply not have a name
      you're looking for.
    Same network-policy caveat as step 0 applies if `financialmodelingprep.com`
    is unreachable.
1. WebSearch fallback (only if BOTH 0 and 0b are unreachable, or to
   sanity-check a surprising result from either): pull pre-market movers
   and volume leaders via WebSearch (e.g. "stock market pre-market movers
   today", "biggest stock gainers premarket") — a sample of what's out
   there, not comprehensive, so widen the query angles (analyst upgrades,
   sector rotation, earnings calendar) rather than trusting one narrow
   search.
2. Separately, look ahead: earnings calendar for the coming week (real
   dates from step 0b's FMP call when reachable, WebSearch otherwise). This
   exists because reacting only to today's movers means always chasing a
   catalyst that already happened — the GTLB case in /data/journal/ is the
   example: by the time it showed up as a "mover," it was already up 20%
   and multiple analysts had already moved targets. Flagging earnings
   dates in advance lets research.md catch the reaction same-session
   instead of days late. Add promising names (that would otherwise pass
   the filters below) with a distinct comment tag: `# EARNINGS {date} —
   pre-catalyst watch, not yet a candidate`. These are watch-and-be-ready
   entries, not movers.
3. Filter (all lists from steps 0/0b/1/2): price between $5–$500 (avoid
   penny stocks and needing huge capital), average daily volume > 1M shares
   (avoid illiquid names you can't exit). Already applied if step 0's
   `screen_market_movers()` was used; apply manually to WebSearch/FMP
   movers-list results.
4. Cross-reference against /config/watchlist.txt (manual adds always included).
5. Narrow step 0's ~30-name pool (plus anything from 0b/1/2) down to the
   final 5–15: prioritize names with a plausible catalyst behind the move
   over a bare price move, exclude anything that looks like thin-float/
   reverse-split noise (see BIAF in /data/research/2026-09-02/ for what
   that looks like and why it's still worth a WATCH-level look, not an
   automatic discard), and prefer liquid, well-covered names over obscure
   micro-caps when the pool is larger than needed. This is a narrowing
   pass, not the research itself — don't research catalysts here, just use
   what's already in front of you (ticker, price, volume, % move) to cut
   the list to a workable size for research.md.
6. Write the resulting list to /config/watchlist.txt, overwriting stale entries
   older than 5 trading days unless still flagged manually.
7. Do NOT research or trade in this step — screening only narrows the list.

## Output
Update /config/watchlist.txt with one ticker per line, plus a one-line reason
as a comment, e.g.:
  NVDA  # +6% premarket on earnings beat
  AMD   # EARNINGS 2026-09-05 — pre-catalyst watch, not yet a candidate

## Hard rule on pre-catalyst (earnings look-ahead) tickers
An `EARNINGS {date} — pre-catalyst watch` tag is not itself a catalyst and
must never reach CANDIDATE before the earnings print happens — the earnings
result itself is unresolved binary risk, not a "documented catalyst" per
CLAUDE.md's strategy rules. research.md should hold these at WATCH until
after the print, then evaluate the *reaction* like any other ticker.
