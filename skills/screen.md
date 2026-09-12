# Skill: Screen (coverage-based, 3-12 month horizon)

**Rewritten 2026-09-12 with the council rewrite.** The mover screen is
preserved verbatim at `skills/screen_movers_superseded.md`.

Goal: maintain coverage of an investable universe and hand the council a
shortlist drawn from **what is covered**, never from what moved yesterday.

## The closed loop this breaks (measured, not asserted)
The old screen ranked the whole market by |% change|. So by construction
every name research ever saw had ALREADY made its move — and "stale /
already priced in / sell the news" is the single most common rejection
reason, **57 of 147 notes (39%)**. The pipeline found movers, then rejected
them for being movers. That loop explains weeks of zero candidates better
than any claim about the market.

At the new horizon it is worse than circular. Ranking by |% change| selects
for recent price strength, and `feature_ic.py` found **5-day reversal** is
the one real effect in this data — so a mover screen fed the council the
wrong side of the only measurable effect present.

## Coverage, not discovery
A fundamental investor does not re-screen the market each morning. They
maintain coverage and act when facts and price line up. A name now reaches
the council because it is in the investable universe and its filings say
something, **never because it jumped on Tuesday**.

Coverage also compounds. A mover list evaporates overnight; a covered
universe is cumulative — a few dozen names a day becomes real breadth in
weeks.

## Daily steps
1. **Refresh the universe** (weekly is enough — one API call):
   `python scripts/screen_fundamental.py universe`
   Liquid US common stocks, $5-$500, >1M shares. Currently ~1,350 names.
   Deliberately unranked: ranking the universe by a price move is the exact
   mistake being undone.
2. **Spend the day's coverage budget:**
   `python scripts/screen_fundamental.py cover 20`   (~4-5 minutes)
   Never-covered names first, then the stalest. **Not "most interesting"** —
   choosing what to cover from a price signal would smuggle the mover screen
   back in through the queue.
3. **Produce the shortlist:**
   `python scripts/screen_fundamental.py shortlist 10`
4. Hand it to `skills/council.md` for scoring.

## How to read the shortlist — this matters
- It is an **ATTENTION ORDER, not a return forecast.** It puts analysable
  businesses in front of the council first. It is not claimed to predict
  anything, and building it into something that does would be the variant-27
  mistake CLAUDE.md's RESEARCH PROGRAMME CLOSED section forbids.
- **A low rank is not a rejection.** It is further down the queue for
  analyst time.
- **Flags are prompts, not verdicts.** `neg-equity` is routine for a
  heavy-buyback company (ABBV, AAL) and fatal elsewhere; ROE is suppressed
  there because it is undefined, not because the company lost money.
  `no-data(n/4)` means the filing did not carry the fields — never that the
  company is fine.
- Price action is **not** an input and must not be reintroduced as one.

## Rate limit — the binding constraint
Massive fundamentals are **5 requests/minute** — that is ~277 names/hour at
the 13s spacing used, so the whole 1,348-name universe is **~5 hours of wall
clock**, not weeks. Spread over daily runs it is a few days at 200/day, or
about two months at 20/day. Pick the batch size accordingly.
**An empty or failed result is a 429, not "this company files nothing"** —
that misreading already happened once, when a fast probe made AEHR, TARS and
BIAF look uncovered. `fundamentals.py` raises rather than returning empty so
it cannot recur.

## What did not change
- CLAUDE.md's Hard Risk Rules bind everything downstream.
- Screening still never researches or trades — it only narrows.
- International coverage remains a real gap: Massive and FMP are both
  US-only. The old skill's Yahoo/UK fallback is in
  `screen_movers_superseded.md` if that becomes wanted again.
