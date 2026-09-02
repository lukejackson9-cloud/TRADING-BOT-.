# Skill: Research

Goal: for each ticker in /config/watchlist.txt, produce a documented, honest
research note before any trade decision is made.

## Steps
0. Before searching, check if /data/journal/tickers/{TICKER}.md exists
   (skills/journal.md's per-ticker history) and skim it — has this ticker
   come up before, what was called, what actually happened? Also check
   /data/journal/lessons.md for general patterns. Treat both as context,
   not a rule — a past pattern doesn't decide this ticker's verdict, fresh
   evidence does. Neither file existing yet is normal; skip this step if
   they don't.
1. For each ticker, use the WebSearch tool directly (not
   `scripts/perplexity_client.py` — this project doesn't use a paid
   Perplexity API; Claude Code's built-in web search covers this instead).
   Search for recent news (last 48h), any earnings/catalyst, analyst
   sentiment shifts, and notable risks for that ticker. Run a couple of
   targeted searches per ticker (e.g. "{TICKER} stock news today", "{TICKER}
   earnings catalyst") rather than one vague one.
2. Write your findings + summary to /data/research/YYYY-MM-DD/{TICKER}.md
   using this template:

   ```
   # {TICKER} — {date}

   ## Catalyst
   (what's driving interest today, in your own words)

   ## Sentiment
   (bullish/bearish/mixed, and why)

   ## Risks
   (earnings whipsaw, macro exposure, thin float, etc.)

   ## Sources
   (links from the searches you ran)

   ## Verdict
   PASS or WATCH or CANDIDATE (only "CANDIDATE" tickers move to skills/propose_trades.md)

   ## Confidence
   low / medium / high
   ```

3. Be skeptical. Most tickers should end in PASS or WATCH. "CANDIDATE" should
   be rare and require a real catalyst, not just "price went up."
4. If web search returns nothing substantive, write "insufficient
   information" and mark PASS — never invent a catalyst.
5. If watchlist.txt tags this ticker `EARNINGS {date} — pre-catalyst watch`
   and that date hasn't happened yet, the verdict is capped at WATCH no
   matter how good the setup looks — the print itself is unresolved binary
   risk, not a documented catalyst (see screen.md). Once the date has
   passed, treat it like any other ticker and evaluate the actual reaction.

## Output
One markdown file per ticker in /data/research/YYYY-MM-DD/. Only tickers
marked CANDIDATE are eligible for skills/propose_trades.md.
