# Skill: Screen

Goal: produce a short list (5–15 tickers) of candidates worth researching today.

## Steps
1. Pull pre-market movers and volume leaders (use Trading 212 market data via
   `scripts/trading212_client.py`, or another data source you configure).
2. Filter: price between $5–$500 (avoid penny stocks and needing huge capital),
   average daily volume > 1M shares (avoid illiquid names you can't exit).
3. Cross-reference against /config/watchlist.txt (manual adds always included).
4. Write the resulting list to /config/watchlist.txt, overwriting stale entries
   older than 5 trading days unless still flagged manually.
5. Do NOT research or trade in this step — screening only narrows the list.

## Output
Update /config/watchlist.txt with one ticker per line, plus a one-line reason
as a comment, e.g.:
  NVDA  # +6% premarket on earnings beat
