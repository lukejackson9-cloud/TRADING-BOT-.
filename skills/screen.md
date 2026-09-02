# Skill: Screen

Goal: produce a short list (5–15 tickers) of candidates worth researching today.

## Steps
0. Prefer `scripts/market_screener_client.py` over WebSearch guessing
   whenever it's reachable — it's a real screener (queries the whole
   market by price/volume/sector, not a sample of whatever a search engine
   surfaced). Try it first:
   - `screen_stocks()` for the price/volume-filtered universe directly
     (defaults already match step 3's filters).
   - `get_gainers()` / `get_most_active()` for today's movers.
   - `get_earnings_calendar(from_date, to_date)` for step 2's lookahead,
     with real dates instead of a WebSearch guess.
   If the call fails on a network/connection error (not an auth error),
   that's most likely this environment's network policy blocking
   `financialmodelingprep.com` — don't retry blindly (same rule as
   T212 in CLAUDE.md). Fall back to the WebSearch approach below for this
   run, and mention to the user once per session that the screener is
   unreachable, so they know to fix the network policy or run locally
   rather than assuming the screener is broken.
1. WebSearch fallback (only if step 0 is unreachable, or to sanity-check a
   surprising screener result): pull pre-market movers and volume leaders
   via WebSearch (e.g. "stock market pre-market movers today", "biggest
   stock gainers premarket") — a sample of what's out there, not
   comprehensive, so widen the query angles (analyst upgrades, sector
   rotation, earnings calendar) rather than trusting one narrow search.
2. Separately, look ahead: earnings calendar for the coming week (real
   dates from step 0's screener when reachable, WebSearch otherwise). This
   exists because reacting only to today's movers means always chasing a
   catalyst that already happened — the GTLB case in /data/journal/ is the
   example: by the time it showed up as a "mover," it was already up 20%
   and multiple analysts had already moved targets. Flagging earnings
   dates in advance lets research.md catch the reaction same-session
   instead of days late. Add promising names (that would otherwise pass
   the filters below) with a distinct comment tag: `# EARNINGS {date} —
   pre-catalyst watch, not yet a candidate`. These are watch-and-be-ready
   entries, not movers.
3. Filter (both lists from steps 1 and 2): price between $5–$500 (avoid
   penny stocks and needing huge capital), average daily volume > 1M shares
   (avoid illiquid names you can't exit). Already applied if step 0's
   screener was used.
4. Cross-reference against /config/watchlist.txt (manual adds always included).
5. Write the resulting list to /config/watchlist.txt, overwriting stale entries
   older than 5 trading days unless still flagged manually.
6. Do NOT research or trade in this step — screening only narrows the list.

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
