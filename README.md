# Short-Term Stock Research Assistant (Claude Code + Trading 212)

Short-term stock research assistant. Claude Code acts as the
scheduler/executor; this repo's files are its "brain" (see CLAUDE.md). It
screens and researches candidates and writes up advisory trade ideas — it
never places any order, live or paper.

## Current mode: ADVISORY-ONLY, account not connected
This instance is deliberately **not connected** to a Trading 212 account —
only a T212 API *key* was provided, not the secret required to authenticate
(see CLAUDE.md "ACCOUNT CONNECTION STATUS"). That's intentional: the goal
right now is trading advice/research, not live or even paper execution.
Concretely:
- `scripts/trading212_client.py` cannot make any authenticated call and the
  skills are written to never attempt one.
- `skills/execute_approved.md` is inert — nothing in this repo can place an
  order. Any trade idea is something you act on yourself, manually, in the
  T212 app, if you choose to.
- Position sizing in proposals is in % of portfolio, not a live balance.

If you later want this connected to a real (or demo) account for sizing
against your actual balance, you'd need to add the T212 API secret and
explicitly ask for the account to be connected — that's a deliberate,
separate step, not a default.

## What this is (and isn't)
- IS: a research/screening assistant that writes up sized trade *ideas*
  with documented reasoning, for you to evaluate and act on yourself.
- IS NOT: a system that reliably predicts short-term price moves, or one
  that places any trades on your behalf in this mode.

## The advisory flow
1. A routine runs skills/screen.md → skills/research.md → skills/propose_trades.md.
   This writes trade ideas to /data/pending_trades.json and pings you via
   ClickUp (if configured). **No order is ever sent — there's no account to
   send one to.**
2. You review the ideas — in the file, in ClickUp, or by asking Claude Code
   directly ("show me today's trade ideas").
3. You decide what to do with them, and place anything you like yourself in
   the T212 app. This repo has no execution capability while unconnected.

## Setup
1. `cp .env.example .env` and fill in the keys you're using:
   - Trading 212: optional in this mode. If you only want advice, you can
     leave `T212_API_KEY`/`T212_API_SECRET` unset entirely — nothing in the
     advisory flow calls the T212 API. Only fill both in if you later
     decide to connect the account for real.
   - Perplexity: sign up at perplexity.ai, get an API key — this is what
     actually powers the research/screening.
   - ClickUp: optional. Create a Personal API Token and a task if you want
     the daily digest; skip it if you're fine reading /data/ directly.
2. `pip install requests --break-system-packages`
3. Export the env vars (or use `direnv` / your shell profile) so Claude
   Code's shell has access to them when it runs scripts.
4. Edit /config/watchlist.txt with a starter list of tickers you're interested in.
5. Review CLAUDE.md — this is where you tune strategy and the "not
   connected" status. Read it fully before turning this on.

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
  3. Do NOT schedule skills/execute_approved.md — it's inert in advisory-only
     mode anyway (no connected account), and even if that changes later it
     should only ever be run on demand, never unattended.
  4. Each routine should point Claude Code at CLAUDE.md first so it always
     has the full ruleset loaded, then the specific skill file for that run.

## File structure

trading-agent/
├── CLAUDE.md                  # the brain — rules, strategy, "not connected" status
├── config/
│   ├── settings.json          # broker, mode, risk %, ClickUp task id
│   └── watchlist.txt          # tickers under consideration
├── skills/
│   ├── screen.md               # find candidates (Perplexity-based, not T212 data)
│   ├── research.md             # Perplexity-based research per ticker
│   ├── propose_trades.md       # size ideas, write to pending_trades.json — advisory only
│   ├── execute_approved.md     # INERT in this mode — no connected account
│   ├── monitor.md              # advisory position check-in, based on what you report
│   └── report.md               # daily ClickUp summary of ideas produced
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
