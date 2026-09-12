# Skill: Execute Approved Trades

## THIS SKILL IS CURRENTLY INERT — DO NOT RUN IT
Per CLAUDE.md's "ACCOUNT CONNECTION STATUS", the user has withheld the
Trading 212 API secret and explicitly asked for advice only, not live
trading. There is no connected account to place an order into, and
`scripts/trading212_client.py` cannot authenticate. If asked to "execute" or
"approve" a trade, explain this to the user instead of running these steps
— they act on advisory ideas manually, in the T212 app themselves. Only
resume following the steps below if the user later supplies the API secret
AND explicitly asks to connect the account for real execution, and
CLAUDE.md's status section has been updated accordingly.

---

Goal (once re-enabled): place orders for trades the user has explicitly
approved — and only those. This is the ONLY skill allowed to call
`place_market_order()` / `place_limit_order()`.

## How approval works
The user reviews /data/pending_trades.json (or the ClickUp notification) and
changes an entry's "status" field from "PENDING_APPROVAL" to "APPROVED" —
either by editing the file directly, or by telling Claude Code directly in
chat, e.g.: "approve trade 2026-09-02-NVDA-01" or "approve all pending trades".

If the user approves via chat rather than editing the file, update the
status field in /data/pending_trades.json yourself before proceeding, so the
approval is recorded, then continue with the steps below.

## Steps (run only when explicitly invoked, e.g. by chat command or a
## routine that first confirms with the user — never fully unattended)
1. Read /data/pending_trades.json. Collect entries with status == "APPROVED".
2. If there are none, stop and report "no approved trades to execute."
3. For each approved entry:
   a. Re-check preconditions from CLAUDE.md (position size %, total exposure
      %, daily loss limit) using fresh data from `get_account_cash()` and
      `get_portfolio()` — market conditions may have changed since proposal.
   b. If preconditions still pass, call `place_market_order(ticker, quantity)`.
   c. If preconditions now fail, mark status "SKIPPED_RISK_LIMIT" and log why
      — do not execute.
   d. Update the entry's status to "EXECUTED" (or "SKIPPED_RISK_LIMIT" /
      "FAILED") and record the order response.
4. Append every outcome (executed, skipped, failed) to /data/trades.log.
5. Send a ClickUp confirmation of what was actually executed.

## Hard rules
- Never execute an entry that is not status == "APPROVED".
- Never re-approve or infer approval — if it's ambiguous, skip and ask.
- Never execute the same "id" twice — check /data/trades.log first.
