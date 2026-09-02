# Skill: Screen

Goal: produce a short list (5–15 tickers) of candidates worth researching today.

## Steps
1. Pull pre-market movers and volume leaders. In advisory-only mode (see
   CLAUDE.md) `scripts/trading212_client.py` cannot authenticate — do not
   call it. Instead use the WebSearch tool directly (e.g. "stock market
   pre-market movers today", "biggest stock gainers premarket") to find
   today's notable pre-market movers/momentum names with a real catalyst
   behind them, not just a random gainer list.
2. Separately, look ahead: WebSearch for "companies reporting earnings this
   week" (or next week if it's Thursday/Friday). This exists because
   reacting only to today's movers means always chasing a catalyst that
   already happened — the GTLB case in /data/journal/ is the example: by
   the time it showed up as a "mover," it was already up 20% and multiple
   analysts had already moved targets. Flagging earnings dates in advance
   lets research.md catch the reaction same-session instead of days late.
   Add promising names (that would otherwise pass the filters below) with
   a distinct comment tag: `# EARNINGS {date} — pre-catalyst watch, not
   yet a candidate`. These are watch-and-be-ready entries, not movers.
3. Filter (both lists from steps 1 and 2): price between $5–$500 (avoid
   penny stocks and needing huge capital), average daily volume > 1M shares
   (avoid illiquid names you can't exit).
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
