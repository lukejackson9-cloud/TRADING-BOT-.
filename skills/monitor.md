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
3. If a position looks to have hit its suggested stop or target (using a
   recent price the user gives you, or an approximate one from
   Perplexity — flag it as approximate), tell the user directly and suggest
   they consider closing it themselves in the T212 app. Do not write an
   "exit order" anywhere — there's nothing to execute.
4. If a position has been held 5+ trading days without hitting stop or
   target, flag the time-stop the same way.
5. If the user mentions their account is down significantly on the day,
   note that skills/propose_trades.md should hold off on new ideas for the
   rest of the day.
6. Log a one-line status per position discussed to /data/trades.log.
