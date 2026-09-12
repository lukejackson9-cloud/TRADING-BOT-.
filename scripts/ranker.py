"""
A RANKER, not a gate — the buy-side counterpart to a pipeline that only
knows how to say no.

WHY THIS EXISTS
---------------
This project's advisory pipeline has produced 15 CANDIDATEs and downgraded
15 of them. That reads as discipline, and `counterfactual.py` showed it is
not: grading every downgrade as if bought anyway returned -1.71%/trade
against a date-matched market baseline of -1.71%/trade. Identical. The
rejected names did exactly as well as random liquid stocks. A machine that
says no to everything has no measurable skill in either direction, and a
system that never buys never generates the data that would tell you whether
it can pick.

The cause is structural, not a tuning problem:
  * council's decision rule requires the bull to win EVERY point while the
    bear needs one. Every stock has a flaw, so "is this flawless?" returns
    no by construction, regardless of the truth.
  * the screen ranks by |% change|, so every name it surfaces has already
    moved, and "already priced in" is 39% of all rejections.
A rejector asks *is this good enough?* A selector asks *which of today's
names is best, and is the price paying me for the flaw?* Those are
different questions and only the second one can ever produce a buy.

WHAT THIS DOES, AND WHAT IT DELIBERATELY DOES NOT
--------------------------------------------------
It records the daily shortlist's TOP FEW names by conviction, with the
reasoning, and grades them later against the same market baseline. It has
no pass mark. Nothing is gated, nothing is proposed to the user as a trade,
and no real or demo order is ever placed from it.

Critically, IT CONTAINS NO SCORING FORMULA. `feature_ic.py` established that
the price-derived features carry no cross-sectional information (7 of 8
noise, 318,505 stock-days), so another mechanical score would be variant 27
and is exactly what CLAUDE.md's RESEARCH PROGRAMME CLOSED section forbids.
The ranking judgment comes from the daily research/council reasoning over
REAL NEWS -- the one input never tested. This file is the ledger and the
grader for that judgment, nothing more.

It does not loosen council. Council keeps its exact current bar and keeps
downgrading; this runs alongside and records what the system WOULD have
picked. That makes it additive instrumentation of the same kind as the
2026-09-11 diagnostics, not the recalibration that CLAUDE.md reserves for
an explicit user decision.

WHAT WOULD COUNT AS IT WORKING
-------------------------------
Fixed here, before the data exists, because a bar chosen afterwards is not
a bar:
  * >=30 graded picks AND >=20 distinct pick dates (the paper track's
    "n=51" was really 2 sessions -- trade count is not sample size);
  * picks beat the DATE-MATCHED market baseline, not zero;
  * no single ticker driving >35% of the net positive return;
  * the advantage holds in both halves of the window;
  * ideally rank 1 beats rank 3, and high conviction beats low -- if the
    ordering carries no information then "best available" is arbitrary even
    if the pooled average looks fine.

Usage:
  python scripts/ranker.py pick 2026-09-15 NVDA 1 high 28 "beat + raised guidance, reaction day 1"
  python scripts/ranker.py list
  python scripts/ranker.py report
"""

import sys
import json
import datetime
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

PICKS = Path("data/ranked_picks.json")
MIN_PICKS, MIN_DATES = 30, 20
CONVICTIONS = ("high", "medium", "low")


def _load():
    return json.loads(PICKS.read_text()) if PICKS.exists() else []


def _save(rows):
    PICKS.parent.mkdir(parents=True, exist_ok=True)
    PICKS.write_text(json.dumps(rows, indent=2))


def pick(date, ticker, rank, conviction, pool_size, reason):
    """Record one ranked pick. Idempotent per (date, ticker).

    `pool_size` is how many names the shortlist held that day -- without it
    "we picked the best one" is unmeasurable, because picking the best of 3
    and the best of 30 are completely different claims.

    `reason` is required and must be the actual thesis. A pick with no
    recorded reasoning cannot be reviewed later for WHY it was right or
    wrong, only whether it was, which is how a system learns nothing from
    its own history."""
    datetime.date.fromisoformat(date)
    if conviction not in CONVICTIONS:
        raise SystemExit(f"conviction must be one of {CONVICTIONS}, got {conviction!r}")
    if not reason.strip():
        raise SystemExit("a reason is required — an unexplained pick teaches nothing later")
    rows = _load()
    for r in rows:
        if r["date"] == date and r["ticker"] == ticker.upper():
            print(f"already recorded: {ticker.upper()} on {date} (rank {r['rank']})")
            return
    rows.append({"date": date, "ticker": ticker.upper(), "rank": int(rank),
                 "conviction": conviction, "pool_size": int(pool_size),
                 "reason": reason.strip(),
                 "recorded_at": datetime.datetime.now(datetime.timezone.utc)
                 .isoformat(timespec="seconds")})
    rows.sort(key=lambda r: (r["date"], r["rank"]))
    _save(rows)
    print(f"recorded #{rank} {ticker.upper()} on {date} "
          f"({conviction} conviction, best of {pool_size})")


def show(date=None):
    rows = [r for r in _load() if date is None or r["date"] == date]
    if not rows:
        print("no picks recorded" + (f" for {date}" if date else ""))
        return
    for r in rows:
        print(f"{r['date']}  #{r['rank']} {r['ticker']:<6} {r['conviction']:<7}"
              f"(of {r['pool_size']:>3})  {r['reason'][:70]}")
    print(f"\n{len(rows)} pick(s) over {len({r['date'] for r in rows})} date(s)")


def _guardrails(rows, graded):
    """Print the sample-quality checks BEFORE any return number.

    Deliberately first, and deliberately blunt: this project has twice
    mistaken a tiny effective sample for a result (the 20-day backtest's
    ~1.1 independent episodes, and the paper track's 51 trades that were
    really 2 sessions). Returns printed above their own sample-size caveat
    get quoted without it."""
    dates = sorted({r["date"] for r in rows})
    print(f"picks recorded {len(rows)} over {len(dates)} date(s)"
          f"{f' ({dates[0]}..{dates[-1]})' if dates else ''}")
    print(f"graded so far   {len(graded)}")
    ok = True
    if len(graded) < MIN_PICKS:
        print(f"  ! {len(graded)}/{MIN_PICKS} graded picks — below the pre-registered floor")
        ok = False
    if len(dates) < MIN_DATES:
        print(f"  ! {len(dates)}/{MIN_DATES} distinct dates — trade count is NOT sample size;"
              f" clustered dates measure the tape, not the picking")
        ok = False
    if graded:
        by_t = defaultdict(float)
        pos = sum(r for _, r, _ in graded if r > 0)
        for t, r, _ in graded:
            if r > 0:
                by_t[t] += r
        if pos > 0:
            top, share = max(by_t.items(), key=lambda kv: kv[1])
            if share / pos > 0.35:
                print(f"  ! {top} alone is {share / pos * 100:.0f}% of net positive return"
                      f" (>35%) — the result is one stock, not a method")
                ok = False
    print("  VERDICT: " + ("sample clears the pre-registered bar — read the numbers below"
                           if ok else
                           "NOT YET READABLE as evidence. Numbers below are progress, not findings."))
    return ok


def report():
    rows = _load()
    if not rows:
        print("no picks recorded yet.\n"
              "The daily screen records them with:\n"
              "  python scripts/ranker.py pick DATE TICKER RANK high|medium|low POOL \"reason\"")
        return
    from counterfactual import fetch_bars, grade, _stats

    graded, pending = [], []
    for r in rows:
        bars = fetch_bars(r["ticker"])
        status, ret, detail = grade({"date": r["date"], "ticker": r["ticker"]}, bars)
        if status == "resolved":
            graded.append((r["ticker"], ret, r))
        else:
            pending.append((r, status, detail))

    print("=" * 78)
    print("SAMPLE QUALITY — read this before any return below")
    print("=" * 78)
    readable = _guardrails(rows, graded)
    print()

    if graded:
        print("=" * 78)
        print("PICKS")
        print("=" * 78)
        print("all picks      " + _stats([(t, r) for t, r, _ in graded]))

        # Does the ORDERING carry information? If rank 1 is no better than
        # rank 3, "best available" is arbitrary even when the pool average is fine.
        print("\nby rank (does the ordering mean anything?)")
        by_rank = defaultdict(list)
        for t, ret, r in graded:
            by_rank[r["rank"]].append((t, ret))
        for k in sorted(by_rank):
            print(f"  rank {k:<10}" + _stats(by_rank[k]))

        # Calibration: high conviction should beat low, or the confidence
        # label is decoration. Same check journal.md applies to council.
        print("\nby conviction (is the confidence label informative?)")
        by_c = defaultdict(list)
        for t, ret, r in graded:
            by_c[r["conviction"]].append((t, ret))
        for c in CONVICTIONS:
            if by_c[c]:
                print(f"  {c:<15}" + _stats(by_c[c]))

        halves = sorted({r["date"] for _, _, r in graded})
        if len(halves) >= 4:
            mid = halves[len(halves) // 2]
            h1 = [(t, x) for t, x, r in graded if r["date"] < mid]
            h2 = [(t, x) for t, x, r in graded if r["date"] >= mid]
            print(f"\nsplit-half (noise flips sign here; a real effect does not)")
            print(f"  first half     " + _stats(h1))
            print(f"  second half    " + _stats(h2))
        print()

    if pending:
        print(f"{len(pending)} pick(s) not yet gradeable:")
        for r, status, detail in pending[:10]:
            print(f"  {r['date']} {r['ticker']:<6} {status}: {detail}")
        print()

    print("=" * 78)
    print("THE COMPARISON THAT DECIDES THIS")
    print("=" * 78)
    print("An average above zero is NOT the test. Run")
    print("  python scripts/counterfactual.py baseline")
    print("and compare against the date-matched market figure. This project's picks")
    print("have already once matched the market EXACTLY (-1.71% vs -1.71%), which")
    print("looked like skill until the control was computed. Beating zero in a rising")
    print("month is beta; beating the same days' market is the only evidence of picking.")
    if not readable:
        print("\nAnd none of it counts until the sample clears the bar above.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "pick":
        pick(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6],
             " ".join(sys.argv[7:]))
    elif cmd == "list":
        show(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == "report":
        report()
    else:
        print(__doc__.strip().split("Usage:")[-1])
