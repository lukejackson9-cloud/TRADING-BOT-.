# Skill: Monitor

Goal: check any positions the user is holding against the strategy's exit
rules, as an advisory check-in — not an automated action, since there is no
connected account in this mode (see CLAUDE.md "ACCOUNT CONNECTION STATUS").

## Steps
1. Do NOT call `scripts/trading212_client.py get_portfolio()` — it cannot
   authenticate. Instead, ask the user (or use what they've told you
   recently in chat) which positions they're holding, at what entry price
   and date.
2. For each position, check /data/trades.log or /data/pending_trades.json
   for the suggested_stop / suggested_target recorded when the idea was
   proposed.
3. Get a current price for each position:
   - Prefer `scripts/alpaca_client.py`'s `get_latest_trade(symbol)` (or
     `get_latest_trades([...])` for several at once) if `ALPACA_API_KEY`/
     `ALPACA_API_SECRET` are set — this is genuine real-time (IEX feed)
     data during market hours, not end-of-day. Note it's IEX-only (~2-4%
     of a stock's volume), so treat it as "close enough to catch a stop/
     target approach," not an execution-grade precise price.
   - If Alpaca is unset/unreachable, fall back to WebSearch for an
     approximate current price and flag it explicitly as approximate, not
     a live quote.
4. If a position looks to have hit its suggested stop or target, tell the
   user directly and suggest they consider closing it themselves in the
   T212 app. Do not write an "exit order" anywhere — there's nothing to
   execute.
5. If a position has been held 5+ trading days without hitting stop or
   target, flag the time-stop the same way.
6. If the user mentions their account is down significantly on the day,
   note that skills/propose_trades.md should hold off on new ideas for the
   rest of the day.
7. Log a one-line status per position discussed to /data/trades.log,
   noting whether the price came from Alpaca (real-time) or a WebSearch
   approximation.
