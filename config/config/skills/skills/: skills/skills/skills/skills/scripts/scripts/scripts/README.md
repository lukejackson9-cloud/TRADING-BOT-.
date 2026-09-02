# Short-Term Stock Research Assistant (Claude Code + Trading 212)

Short-term stock research assistant with a human-in-the-loop approval gate.
Claude Code acts as the scheduler/executor; this repo's files are its
"brain" (see CLAUDE.md). It screens, researches, and PROPOSES trades — it
never places an order without your explicit approval.

## What this is (and isn't)
- IS: a research/screening assistant that proposes sized trade ideas with
  documented reasoning, and only executes what you approve.
- IS NOT: a system that reliably predicts short-term price moves. No such
  system exists. Treat this as a disciplined way to screen ideas — not a
  path to guaranteed profit.

## The approval flow (this is the important part)
1. A routine runs skills/screen.md → skills/research.md → skills/propose_trades.md.
   This writes candidate trades to /data/pending_trades.json with status
   "PENDING_APPROVAL" and pings you via ClickUp. **No order is sent.**
2. You review the proposals — in the file, in ClickUp, or by asking Claude
   Code directly ("show me pending trades").
3. You approve specific trades, e.g. telling Claude Code in chat:
   "approve trade 2026-09-02-NVDA-01" — or by editing the JSON file yourself.
4. You (or a routine you trigger manually) run skills/execute_approved.md,
   which only places orders for entries marked "APPROVED", after re-checking
   risk limits with fresh data.

Do not set up a routine that runs skills/execute_approved.md on an
unattended schedule — that would defeat the point of the approval step.
Run it yourself, on demand, after reviewing proposals.

## Setup
1. `cp .env.example .env` and fill in your real keys:
   - Trading 212: in the app, go to Settings > API. Click "Switch to
     Practice" first if you want DEMO/paper keys (recommended to start).
     The public API is in beta — check docs.trading212.com for the latest
     capabilities before relying on anything not covered here.
   - Perplexity: sign up at perplexity.ai, get an API key
   - ClickUp: create a Personal API Token, and a task to receive notifications
2. `pip install requests --break-system-packages`
3. Export the env vars (or use `direnv` / your shell profile) so Claude
   Code's shell has access to them when it runs scripts.
4. Edit /config/watchlist.txt with a starter list of tickers you're interested in.
5. Review CLAUDE.md — this is where you tune strategy, risk limits, and the
   approval rule. Read it fully before turning this on.

## Running it manually first (do this before scheduling anything)
From this directory, open Claude Code and say something like:
  "Follow CLAUDE.md and skills/screen.md, then skills/research.md.
   Don't propose any trades yet, just show me what you'd research."
Watch what it does for a few days before letting it propose trades, and
review several rounds of proposals before approving any.

## Setting up the schedule (Claude Code routines)
Claude Code routines replace cron. In Claude Code:
  1. Open this project directory.
  2. Set up a routine (check Claude Code's docs for current syntax/UI —
     search "Claude Code routines" if it's not obvious) for each cadence:
     - 8:00 AM ET  → "Follow skills/screen.md"
     - 10:00 AM ET → "Follow skills/research.md then skills/propose_trades.md"
     - 1:00 PM ET  → "Follow skills/monitor.md"
     - 4:15 PM ET  → "Follow skills/report.md"
  3. Do NOT schedule skills/execute_approved.md — run that one yourself,
     on demand, after you've reviewed and approved proposals.
  4. Each routine should point Claude Code at CLAUDE.md first so it always
     has the full ruleset loaded, then the specific skill file for that run.

## File structure

trading-agent/
├── CLAUDE.md                  # the brain — rules, strategy, risk limits, approval rule
├── config/
│   ├── settings.json          # broker, mode, risk %, ClickUp task id
│   └── watchlist.txt          # tickers under consideration
├── skills/
│   ├── screen.md               # find candidates
│   ├── research.md             # Perplexity-based research per ticker
│   ├── propose_trades.md       # size trades, write proposals — NEVER executes
│   ├── execute_approved.md     # only skill that places real orders; approval-gated
│   ├── monitor.md              # position checks, proposes exits (also gated)
│   └── report.md               # daily ClickUp summary incl. pending approvals
├── scripts/
│   ├── trading212_client.py
│   ├── perplexity_client.py
│   └── clickup_client.py
├── data/
│   ├── research/YYYY-MM-DD/{TICKER}.md
│   ├── pending_trades.json    # proposals awaiting your approval
│   ├── trades.log
│   └── positions.json
└── .env.example
