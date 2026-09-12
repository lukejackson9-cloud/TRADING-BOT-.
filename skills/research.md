# Skill: Research

Goal: for each ticker in /config/watchlist.txt, produce a documented, honest
research note before any trade decision is made.

## Steps
0. Before searching, check /data/journal/trade_ledger.md for this ticker
   (skills/journal.md's trade ledger) — has this ticker come up before,
   what was called, what actually happened? Also check
   /data/journal/lessons.md for general patterns. Treat both as context,
   not a rule — a past pattern doesn't decide this ticker's verdict, fresh
   evidence does. No entry yet for this ticker, or an empty lessons.md, is
   normal; skip this step if so.
0b. **TA context (added 2026-09-12, user request — read it, don't obey
   it)**. Run `python scripts/ta_context.py check {TICKER}`. This is the
   first and only bridge between the mechanical TA track and this
   advisory pipeline; before it, the two had zero cross-references in
   either direction. It reports which mechanical setups fired recently
   plus where the price sits in its 20-day range.
   **It is not corroboration, and the numbers it prints beside each setup
   say why.** Every setup carries a NEGATIVE volatility-matched edge
   (breakout -0.21%/trade over 2,460 entries, ema_cross -0.16%,
   relative_strength -0.23%, mean_reversion -0.45%, vcp_breakout -0.19%),
   and 0 of 72 in-mandate exit-rule variants produce a positive,
   split-half-consistent edge. So:
   - NEVER cite a fired setup as a reason to move a verdict toward
     CANDIDATE. A setup firing has no measured predictive value in this
     project's own data. Doing so would import noise into the one layer
     that still shows signal.
   - DO read it positionally. "Closed above its 20-day high on 1.5x
     volume" means the move has ALREADY happened — lessons.md #1's exact
     situation, and the thing step 3a's checklist exists to weigh. A
     reading above ~100% of the 20-day range is a caution flag about
     chasing, not a green light.
   - Heed its warnings. If it reports a partial-volume feed or stale
     data, record "TA context unavailable/stale", NOT "no setup fired" —
     those are different claims and only one of them is evidence.
   - Log what it said either way, including "nothing fired". The
     catalyst_tag track needs both arms to eventually compare "signal +
     real news" against news alone, and absence is as loggable as
     presence.
1. For each ticker, use the WebSearch tool directly (not
   `scripts/perplexity_client.py` — this project doesn't use a paid
   Perplexity API; Claude Code's built-in web search covers this instead).
   Search for recent news (last 48h), any earnings/catalyst, analyst
   sentiment shifts, and notable risks for that ticker. Run a couple of
   targeted searches per ticker (e.g. "{TICKER} stock news today", "{TICKER}
   earnings catalyst") rather than one vague one.
1b. Optional cross-check: `scripts/tradingview_client.py`'s `get_rating()`
    (unofficial, same caveats as scripts/yahoo_screener_client.py — wrap
    in try/except, skip silently if it errors) gives TradingView's own
    aggregated technical-analysis consensus (STRONG_BUY/BUY/NEUTRAL/SELL/
    STRONG_SELL across ~26 indicators) for a symbol. This is someone
    else's black-box aggregation, not a transparent rule like this
    project's own backtested setups — treat a strong disagreement between
    it and your WebSearch-based read as a prompt to look harder, not as a
    tiebreaker that overrides actual news/fundamentals. Never let this
    alone justify a verdict.
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

   ## TA context
   (verbatim gist of what scripts/ta_context.py reported — setups fired
   or "none fired", % of 20-day range, and any partial-feed/stale-data
   warning. Record it even when empty; see step 0b for why absence is
   as loggable as presence, and why a fired setup is never a reason to
   upgrade this verdict.)

   ## Sources
   (links from the searches you ran)

   ## Verdict
   PASS or WATCH or CANDIDATE (only "CANDIDATE" tickers move to skills/propose_trades.md)

   ## Confidence
   low / medium / high
   ```

3. Be skeptical. Most tickers should end in PASS or WATCH. "CANDIDATE" should
   be rare and require a real catalyst, not just "price went up."
3a. **"Stale story" / "already priced in" / "sell the news" override
    checklist (added 2026-09-11, after AEHR's 2026-09-04 WATCH missed a
    further +69% into a 2026-09-10 investor conference — see
    lessons.md #1's counter-example note in full)**. Before downgrading a
    ticker on the grounds that its driver is "stale" or "already fired,"
    explicitly check and record the answer to: is there a known, DATED,
    still-UPCOMING event for this specific company (an earnings date, an
    investor conference, a data readout, an FDA decision, a guidance
    update) within the project's ~2-week horizon? If yes, do not
    downgrade to "stale" without weighing that the pending event could be
    the next leg's actual trigger, not just noise on top of an already-
    told story — the two are different claims and this checklist exists
    specifically because they were conflated once already. If no such
    event is found after actually checking (not just assuming), staleness
    is a legitimate basis for WATCH/PASS as before. Either way, state in
    the Risks section which case applies and what was checked, not just
    the conclusion — a future outcome-check (skills/journal.md) needs to
    be able to tell whether this checklist was actually run or skipped.
3b. **Estimate-revision check (added 2026-09-11, see lessons.md #9)**.
    Step 3a catches the case where a dated event was pending and got
    missed. This catches the opposite one — where research correctly
    established that NO dated catalyst exists and treated that absence as
    itself bearish, while the stock kept re-rating anyway (CLS, CCC.L,
    both logged misses). Before writing "no fresh dated catalyst" as a
    reason to PASS/WATCH, check separately whether there is a
    corroborated UPWARD revision trend underneath: company guidance
    raised (especially a language upgrade like "ahead" → "comfortably
    ahead"), consensus EPS estimates revised up over recent weeks, or
    more than one broker independently moving the same direction. If
    there is, record it as its own line in the Catalyst section — not
    folded into "no dated event found" — and weigh it as a real positive
    signal rather than a neutral fact sitting next to a negative
    conclusion.
    Guard against the opposite overcorrection, which is equally wrong:
    this is NOT license to treat any extended stock with no catalyst as a
    buy. Lesson #1 (a fired catalyst with nothing behind it fades) still
    stands on its own, larger evidence base. The distinguishing question
    between the two is not "was there a dated catalyst" but "is the
    underlying estimate/guidance trend still moving upward" — state which
    of the two applies and why, rather than defaulting to either.
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
