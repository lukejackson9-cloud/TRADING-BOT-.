6# Skill: Research

Goal: for each ticker in /config/watchlist.txt, produce a documented, honest
research note before any trade decision is made.

## Steps
1. For each ticker, call `scripts/perplexity_client.py research(ticker)` with
   a prompt asking for: recent news (48h), any earnings/catalyst, analyst
   sentiment shifts, and notable risks.
2. Write the raw findings + your own summary to
   /data/research/YYYY-MM-DD/{TICKER}.md using this template:

   {TICKER} — {date}
Catalyst
(what's driving interest today, in your own words)
Sentiment
(bullish/bearish/mixed, and why)
Risks
(earnings whipsaw, macro exposure, thin float, etc.)
Verdict
PASS or WATCH or CANDIDATE (only "CANDIDATE" tickers move to skills/propose_trades.md)
Confidence
low / medium / high

3. Be skeptical. Most tickers should end in PASS or WATCH. "CANDIDATE" should
be rare and require a real catalyst, not just "price went up."
4. If Perplexity returns nothing substantive, write "insufficient information"
and mark PASS — never invent a catalyst.

## Output
One markdown file per ticker in /data/research/YYYY-MM-DD/. Only tickers
marked CANDIDATE are eligible for skills/propose_trades.md.
