# Skill: Monitor

Goal: check open positions against the strategy's exit rules; the broker's
own bracket orders (stop/target) handle most exits automatically where
supported, so this is a secondary safety net plus a time-stop check.

## Steps
1. Pull current positions via `scripts/trading212_client.py get_portfolio()`.
2. For each position, check /data/trades.log for entry date and the
   suggested_stop / suggested_target recorded when it was proposed
   (T212's live API may not support attached stop/target orders — verify
   current docs — so this is often a manual check, not an automatic one).
3. If a position has hit its suggested stop or target, PROPOSE a closing
   sell in /data/pending_trades.json (status PENDING_APPROVAL) rather than
   closing it automatically — the same approval gate applies to exits.
4. If a position has been held 5+ trading days without hitting stop or
   target, propose a time-stop close the same way.
5. If total account is down 3%+ on the day, log a WARNING and note that
   skills/propose_trades.md should not propose new entries for the rest of
   the day.
6. Log a one-line status per position to /data/trades.log.
