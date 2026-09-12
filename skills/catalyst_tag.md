# Skill: Tag paper-trade signals with real catalysts

Goal: the forward-only counterpart to `scripts/backtest_confluence.py`'s
historical tests. Those tests could only check MECHANICAL signal
agreement (TA×TA, TA×macro-calendar, TA×ICT) and found no edge in any
combination (see CLAUDE.md's "Signal confluence testing" section) — they
explicitly could NOT test "a TA/ICT signal plus a REAL news catalyst",
because the only historical proxy tried for "news happened" (an
overnight price gap, 2026-09-07) made results worse, since it captures
the reaction after it fires, not the catalyst itself. There is no
authoritative historical company-news database at this project's data
tier, so this can only be measured going forward, tagged in real time —
this skill is that tagging step.

**This is still not the advisory pipeline.** No proposal to the user, no
research.md/council.md review, no promotion of anything based on a
single day's read. Purely evaluation data, same posture as
skills/paper_trade_ta.md and the ICT paper-trade routine.

## Catalyst definition (do not loosen this to get more "has_catalyst" trades)
A dated, **company-specific** event: earnings (that day or the trading
day before), M&A, an FDA/regulatory decision, a guidance change, or a
material analyst action carrying genuinely new information.
- **NOT** "the stock moved a lot" — that's the exact mistake the
  2026-09-07 gap-proxy made (see lessons.md #1).
- **NOT** a stale or recycled story already priced in days/weeks ago
  (see lessons.md #6).
- If WebSearch is inconclusive, tag `unclear` — never guess to force a
  true/false.

## Steps (run immediately after the existing daily paper-trade scripts)
1. After `scripts/paper_trader.py run {date}` and
   `scripts/ict_paper_trader.py run {date}` have both run for the day,
   find which tickers need a check:
   ```
   python scripts/tag_catalyst.py pending {date}
   ```
   This returns the deduplicated set of tickers with a fresh signal that
   day and no catalyst tag yet — usually a handful (rough historical
   rate: ~3-8 unique tickers/day across both trackers combined).
2. For each ticker in that list, ONE WebSearch query — e.g. "{TICKER}
   stock news {date}" or "{TICKER} earnings {date}" — checking
   specifically for the dated, company-specific catalyst types listed
   above. One query covers the ticker regardless of how many setups/
   mechanisms fired on it that day.
3. Record the verdict:
   ```
   python scripts/tag_catalyst.py tag {TICKER} {date} true|false|unclear "{short sourced note}"
   ```
   The note should name what was found (or that nothing was found) — not
   just the true/false, so a future read of the ledger can see why. This
   writes the same tag into every matching entry across BOTH ledgers at
   once (paper_trades.json and ict_paper_trades.json) — idempotent, an
   already-tagged entry is left alone rather than overwritten.
4. Do not act on any individual day's result. No push notification, no
   chat summary, same silent-unless-erroring posture as the two paper-
   trade routines this rides alongside.

## When to actually look at the results
- Only once there's a real sample: `python scripts/tag_catalyst.py
  report` prints win rate/avg return for HAS-catalyst vs NO-catalyst vs
  unclear, across both TA and ICT ledgers, plus a per-symbol
  concentration check on the HAS-catalyst bucket (same discipline that
  caught OTE's NVDA false positive). It will say plainly if the sample
  is still too small (<50 HAS-catalyst trades) to conclude anything —
  respect that, don't round up to "promising" on a thin read.
- Fold this into skills/journal.md's periodic pass once the sample is
  large enough to be worth a paragraph, not every single run.
- Never promote anything off this data without: (a) it clearing the same
  kind of bar backtest_confluence.py's tests were held to (net positive,
  a real uplift over the no-catalyst baseline, no single-ticker
  concentration, consistent over time, real sample size), AND (b)
  discussing it with the user first — identical standard to every other
  promotion decision in this project.

## Why no retroactive tagging
Only signals opened from when this skill went live (2026-09-11) forward
get tagged. Reconstructing "was there a catalyst" on a past date with
today's hindsight would bias the result exactly the way the rest of this
project's backtesting discipline exists to prevent — entries from before
this date simply have no `catalyst` key at all (not `null`), and
`scripts/tag_catalyst.py`'s `pending` command correctly ignores them
rather than treating them as awaiting a check.

## File Map addition
- `data/paper_trades.json` / `data/ict_paper_trades.json` — both gained a
  `"catalyst"` field on every entry created from 2026-09-11 onward: `null`
  until tagged, then `{"has_catalyst": true|false|"unclear", "note",
  "tagged_on"}`. See `scripts/tag_catalyst.py`'s docstring for the exact
  shape.
