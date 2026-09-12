# Skill: Report

Goal: summarize the day's activity and send it as a ClickUp task/comment so
the user gets a daily digest without needing to check logs manually.

## Steps
1. Read today's entries from /data/trades.log.
2. Read today's research files from /data/research/{today}/.
3. Read /data/pending_trades.json for today's advisory ideas.
4. Do NOT call `scripts/trading212_client.py get_account_cash()` — no
   connected account in this mode (see CLAUDE.md). Skip account
   equity/P&L entirely rather than guessing at it.
5. Compose a short summary:
   - Tickers screened, tickers researched
   - Trade IDEAS produced today (advisory only — nothing was proposed for
     execution, since there is no execution path)
   - Any correlation_flag warnings on today's ideas (see propose_trades.md)
   - Any positions discussed in skills/monitor.md today, based on what the
     user told you (not a live sync)
   - If /data/journal/scorecard.md exists, its headline win rate/downgrade
     accuracy numbers, WITH the sample-size caveat — never bare percentages
   - Any warnings/errors logged today
6. Send via `scripts/clickup_client.py post_report(summary)` as a comment on
   the configured ClickUp task (see /config/settings.json "clickup_task_id"),
   if ClickUp is configured.

## Output
A ClickUp comment/task update. Keep it under ~300 words — this is a digest,
not the full research (link to /data/research/ for detail if needed).
