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


# ---------------------------------------------------------------------------
# LONG-HORIZON GRADING
#
# The original report() graded picks through counterfactual.grade(), which
# applies CLAUDE.md's short-horizon rule: -4% stop / +8% target / 5-day time
# stop. That was correct while this project traded two-week momentum. It is
# WRONG for the 3-12 month council and would have quietly destroyed the first
# six weeks of data.
#
# Why it breaks: a perfectly sound company routinely draws down 4% in a week
# on noise. Grading a 3-12 month thesis with a 5-day -4% stop means nearly
# every pick "resolves" as a stop-out within days, long before the thesis has
# any chance to be right or wrong. The track would have reported failure that
# meant nothing at all -- and, worse, it would have looked like a real result.
#
# So: fixed holds at the actual horizon, NO stop, and measured against SPY
# over the IDENTICAL window. Against zero, any hold in a rising market looks
# like skill; the benchmark is the whole point.
# ---------------------------------------------------------------------------

HORIZONS = [(21, "1 month"), (63, "3 months"), (126, "6 months"), (252, "12 months")]
MANDATE_MIN = 63          # 3-12 months is the mandate; 21d is an early read only
_BARS_CACHE = Path("data/reference/ranker_bars")


def _bars(ticker, refresh_days=1):
    """Daily bars to TODAY. Unlike counterfactual's cache this must keep
    extending forward, because a pick made today is graded 1/3/6/12 months
    from now — a frozen cache would silently stop maturing picks."""
    _BARS_CACHE.mkdir(parents=True, exist_ok=True)
    f = _BARS_CACHE / f"{ticker.upper()}.json"
    if f.exists():
        d = json.loads(f.read_text())
        age = (datetime.date.today() - datetime.date.fromisoformat(d["fetched"])).days
        if age <= refresh_days:
            return [tuple(b) for b in d["bars"]]
    from alpaca_client import get_historical_bars
    try:
        raw = get_historical_bars(ticker, "2026-08-01T00:00:00Z",
                                  f"{datetime.date.today()}T23:59:59Z", timeframe="1Day")
    except Exception:
        return []
    bars = [(b["t"][:10], b["o"], b["h"], b["l"], b["c"], b["v"]) for b in raw]
    f.write_text(json.dumps({"fetched": datetime.date.today().isoformat(), "bars": bars}))
    return bars


def _hold_return(bars, date, sessions):
    """Buy at the open after `date`, hold `sessions` sessions, no stop.

    Returns (pct_return, matured). `matured` False means the window has not
    elapsed yet — the partial number is returned for visibility but must
    never be averaged in with matured ones, which would bias the result
    toward whatever the newest picks are doing."""
    prior = [i for i, b in enumerate(bars) if b[0] <= date]
    if not prior:
        return None, False
    i = prior[-1]
    if i + 1 >= len(bars):
        return None, False
    entry = bars[i + 1][1]
    if entry <= 0:
        return None, False
    end = i + 1 + sessions
    matured = end < len(bars)
    last = bars[min(end, len(bars) - 1)][4]
    return (last - entry) / entry, matured


def grade_long():
    """Grade ranked picks at the horizon they were actually chosen for."""
    rows = _load()
    if not rows:
        print("no picks recorded yet — nothing to grade.")
        return
    spy = _bars("SPY")
    if not spy:
        print("WARNING: no SPY bars. Returns below are against ZERO, which in a")
        print("rising market flatters everything. Treat them as uninterpretable.")

    print("=" * 78)
    print("SAMPLE QUALITY")
    print("=" * 78)
    dates = sorted({r["date"] for r in rows})
    print(f"{len(rows)} picks over {len(dates)} date(s)"
          f"{f' ({dates[0]}..{dates[-1]})' if dates else ''}")
    if len(dates) < MIN_DATES:
        print(f"  ! {len(dates)}/{MIN_DATES} distinct dates — clustered picks measure the"
              f" tape, not the picking")
    print()

    for sessions, label in HORIZONS:
        # Every pick must land in exactly ONE bucket and the totals must
        # reconcile with len(rows). An earlier version returned None for a
        # pick with no session after its date yet (recorded at the close, so
        # not yet buyable) and that pick vanished from BOTH counters — three
        # picks in, two accounted for, no warning. Silent loss is how a
        # measurement rots without anyone noticing.
        mat, imm, no_entry, no_data = [], 0, 0, 0
        for r in rows:
            b = _bars(r["ticker"])
            if not b:
                no_data += 1
                continue
            ret, done = _hold_return(b, r["date"], sessions)
            if ret is None:
                no_entry += 1
                continue
            if not done:
                imm += 1
                continue
            sret, sdone = _hold_return(spy, r["date"], sessions) if spy else (None, False)
            mat.append((r, ret, sret if sdone else None))
        tag = "" if sessions >= MANDATE_MIN else "   [EARLY READ — below the 3-month mandate]"
        print(f"--- {label} ({sessions} sessions){tag}")
        accounted = len(mat) + imm + no_entry + no_data
        tally = (f"{len(mat)} matured / {imm} open / {no_entry} not yet entered"
                 f" / {no_data} no price data  = {accounted} of {len(rows)}")
        if accounted != len(rows):
            tally += "   <-- BUG: picks unaccounted for"
        if not mat:
            print(f"    none matured yet.  [{tally}]\n")
            continue
        avg = sum(x[1] for x in mat) / len(mat)
        bench = [x[2] for x in mat if x[2] is not None]
        line = (f"    n={len(mat):<4} picks {avg * 100:+.2f}%   "
                f"win {sum(1 for x in mat if x[1] > 0) / len(mat) * 100:.0f}%")
        if bench:
            ba = sum(bench) / len(bench)
            line += f"   SPY {ba * 100:+.2f}%   EXCESS {(avg - ba) * 100:+.2f}%"
        else:
            line += "   (no benchmark — NOT interpretable)"
        print(line)
        worst = min(x[1] for x in mat)
        big = sum(1 for x in mat if x[1] <= -0.20) / len(mat) * 100
        print(f"    worst {worst * 100:+.1f}%   losing >20%: {big:.0f}%")
        print(f"    [{tally}]")
        print()

    print("=" * 78)
    print("EXCESS OVER SPY IS THE NUMBER THAT MATTERS, NOT THE RAW RETURN.")
    print("Holding anything in a rising market produces a positive raw return; that is")
    print("beta and an index fund sells it cheaper. Only the excess is evidence of")
    print("picking. No stop is applied on purpose — at this horizon a tight stop exits")
    print("on noise before the thesis resolves, which is exactly the flaw this replaced.")
    print("Nothing here is readable until the 3-month column has a real sample across")
    print("many distinct dates; expect that to take months, by design.")
    print("=" * 78)


def backtest():
    """Did the labels this system ALREADY recorded carry ordering information?

    The ranker's premise is that the pipeline can say "this one is better
    than that one" even when nothing clears the gate. That claim is testable
    right now, without waiting for new picks, because 136 verdicts already
    carry a `verdict` (CANDIDATE/WATCH/PASS) and a `confidence` assigned
    BEFORE the outcome was known. If those labels order the outcomes, the
    ranker has something to work with. If they do not, "best available" is
    arbitrary and the new track will likely find the same.

    WHY THE COMPARISON IS WITHIN EACH DATE
    ---------------------------------------
    Verdicts cluster on 9 sessions, and those sessions are wildly different
    tapes -- the same exit rule returned +0.15%/42% win on 2026-09-01 and
    -3.18%/6.9% win on 2026-09-08. Pooling across dates measures WHICH DAYS
    the pipeline happened to be busy, which is exactly the artifact that made
    the paper track look catastrophic. So every comparison here is made
    BETWEEN BUCKETS ON THE SAME DAY and only then averaged across days. Every
    name in a comparison experienced the identical tape, so the market
    cancels by construction -- the same design that made feature_ic.py's
    cross-sectional test clean, and it needs no separate control group.

    WHAT THIS IS NOT
    ----------------
    It is not a clean out-of-sample test of the new ranker, and must never be
    reported as one. The labels are real and pre-outcome, but they were
    produced by a pipeline whose whole purpose was gatekeeping, and the
    sample is 9 dates. Treat a positive result as "worth continuing", never
    as validation. A NEGATIVE result is the more informative direction: it
    would say the ordering signal is not there.
    """
    from counterfactual import load_verdicts, fetch_bars, grade, _stats

    verdicts = load_verdicts()
    print(f"grading {len(verdicts)} recorded verdicts (cached after first run)...\n")
    rows = []
    for v in verdicts:
        bars = fetch_bars(v["ticker"])
        status, ret, _ = grade(v, bars)
        if status == "resolved":
            rows.append((v, ret))

    dates = sorted({v["date"] for v, _ in rows})
    print("=" * 78)
    print("SAMPLE QUALITY")
    print("=" * 78)
    print(f"{len(rows)} of {len(verdicts)} verdicts resolved, over {len(dates)} distinct dates")
    print(f"  ! {len(dates)} dates is below the {MIN_DATES}-date bar the forward track uses.")
    print("  ! Verdicts cluster, so this is nearer 9 observations than 136. Every")
    print("    number below is a within-day comparison for that reason, but thin is thin.")
    print()

    def by_day(keyfn, order):
        """Average of (bucket - day mean) across days, so the tape cancels."""
        per_day = defaultdict(lambda: defaultdict(list))
        for v, r in rows:
            per_day[v["date"]][keyfn(v)].append(r)
        out = defaultdict(list)
        for d, buckets in per_day.items():
            allr = [r for rs in buckets.values() for r in rs]
            if len(allr) < 3 or len(buckets) < 2:
                continue          # need a real within-day contrast to compare
            day_mean = sum(allr) / len(allr)
            for k, rs in buckets.items():
                out[k].append((sum(rs) / len(rs)) - day_mean)
        for k in order:
            if out[k]:
                vals = out[k]
                n = sum(1 for v, _ in rows if keyfn(v) == k)
                yield k, n, len(vals), sum(vals) / len(vals)

    print("=" * 78)
    print("DOES THE VERDICT LABEL ORDER THE OUTCOMES?")
    print("=" * 78)
    print("Excess over the same day's average verdict. CANDIDATE should beat PASS.")
    print(f"{'label':<14}{'n':>6}{'days':>7}{'excess vs same-day avg':>26}")
    print("-" * 78)
    for k, n, d, x in by_day(lambda v: v["verdict"], ("CANDIDATE", "WATCH", "PASS")):
        print(f"{k:<14}{n:>6}{d:>7}{x * 100:>25.2f}%")

    print()
    print("=" * 78)
    print("DOES THE CONFIDENCE LABEL ORDER THE OUTCOMES?")
    print("=" * 78)
    print("If high does not beat low, the confidence label is decoration.")
    print(f"{'confidence':<14}{'n':>6}{'days':>7}{'excess vs same-day avg':>26}")
    print("-" * 78)
    for k, n, d, x in by_day(lambda v: v.get("confidence") or "none",
                             ("high", "medium", "low", "none")):
        print(f"{k:<14}{n:>6}{d:>7}{x * 100:>25.2f}%")

    print()
    print("Raw pooled figures (NOT date-adjusted — shown only so the gap between")
    print("these and the within-day numbers above is visible):")
    for lbl in ("CANDIDATE", "WATCH", "PASS"):
        sub = [(v["ticker"], r) for v, r in rows if v["verdict"] == lbl]
        if sub:
            print(f"  {lbl:<12}" + _stats(sub))

    # The tables above average each bucket over whatever days that bucket
    # appears on -- and those day sets DIFFER (CANDIDATE lands on far fewer
    # days than PASS). That is not a head-to-head: a bucket can look bad
    # purely because the days it appears on were bad for everything. The
    # only clean comparison restricts to days carrying BOTH labels.
    print()
    print("=" * 78)
    print("LIKE-FOR-LIKE: only days carrying BOTH a CANDIDATE and a PASS")
    print("=" * 78)
    print("The tables above are NOT a head-to-head — each bucket averages over a")
    print("different set of days. This one is the real comparison.")
    pd2 = defaultdict(lambda: defaultdict(list))
    for v, r in rows:
        pd2[v["date"]][v["verdict"]].append(r)
    print(f"{'date':<13}{'CAND n':>8}{'CAND avg':>11}{'PASS n':>8}{'PASS avg':>11}{'CAND-PASS':>12}")
    print("-" * 63)
    diffs = []
    for d in sorted(pd2):
        b = pd2[d]
        if "CANDIDATE" in b and "PASS" in b:
            ca = sum(b["CANDIDATE"]) / len(b["CANDIDATE"])
            pa = sum(b["PASS"]) / len(b["PASS"])
            diffs.append(ca - pa)
            print(f"{d:<13}{len(b['CANDIDATE']):>8}{ca * 100:>10.2f}%"
                  f"{len(b['PASS']):>8}{pa * 100:>10.2f}%{(ca - pa) * 100:>11.2f}%")
    if diffs:
        print("-" * 63)
        print(f"mean CANDIDATE-minus-PASS: {sum(diffs) / len(diffs) * 100:+.2f}% "
              f"over {len(diffs)} shared day(s); CANDIDATE won {sum(1 for x in diffs if x > 0)}"
              f"/{len(diffs)}")
        print("Count the days, not the trades, and check how many are degenerate (every")
        print("name stopped out => a 0.00% difference that carries no information).")

    print()
    print("=" * 78)
    print("A positive excess for CANDIDATE or for high confidence means the pipeline's")
    print("own ordering carried information even while its GATE rejected everything —")
    print("which is the ranker's premise and a reason to keep going. Flat or inverted")
    print("means the ordering is not there, and the forward track will most likely")
    print("confirm it. Either way: 9 dates, and labels made by a gatekeeper. Worth")
    print("continuing or worth worrying about — never validation.")
    print("=" * 78)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "pick":
        pick(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6],
             " ".join(sys.argv[7:]))
    elif cmd == "list":
        show(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == "report":
        report()
    elif cmd == "backtest":
        backtest()
    elif cmd == "grade":
        grade_long()
    else:
        print(__doc__.strip().split("Usage:")[-1])
