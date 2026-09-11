# Skill: Report

Goal: summarize the day's activity and send it as a ClickUp task/comment so
the user gets a daily digest without needing to check logs manually.

## Steps
1. Read today's entries from /data/trades.log.
2. Read today's research files from /data/research/{today}/.
3. Read /data/pending_trades.json for anything still awaiting approval.
4. Pull current account snapshot via `scripts/trading212_client.py get_account_cash()`.
5. Compose a short summary:
   - Tickers screened, tickers researched
   - Trades PROPOSED today, and how many are still awaiting your approval
     (make this prominent — it's the main action item for the user)
   - Trades actually EXECUTED today (only ones you approved)
   - Open positions and unrealized P&L
   - Account equity vs. yesterday
   - Any warnings/errors logged today
6. Send via `scripts/clickup_client.py post_report(summary)` as a comment on
   the configured ClickUp task (see /config/settings.json "clickup_task_id").

## Output
A ClickUp comment/task update. Keep it under ~300 words — this is a digest,
not the full research (link to /data/research/ for detail if needed).
