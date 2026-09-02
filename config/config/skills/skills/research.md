# Skill: Research

Goal: for each ticker in /config/watchlist.txt, produce a documented, honest
research note before any trade decision is made.

## Steps
1. For each ticker, call `scripts/perplexity_client.py research(ticker)` with
   a prompt asking for: recent news (48h), any earnings/catalyst, analyst
   sentiment shifts, and notable risks.
2. Write the raw findings + your own summary to
   /data/research/YYYY-MM-DD/{TICKER}.md using this template:
