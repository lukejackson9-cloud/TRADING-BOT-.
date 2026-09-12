"""
The advisory pipeline's missing evaluation track: what would have happened
if we had actually BOUGHT the tickers this project decided to skip?

WHY THIS EXISTS (read before changing anything here)
----------------------------------------------------
As of 2026-09-11 the council has reviewed 15 CANDIDATEs and downgraded
every single one -- 15 WATCH verdicts, zero approvals, ever. That produces
a specific and serious evidence gap, flagged first by the external
methodology review and confirmed here: scorecard.md's headline "90.9%
downgrade accuracy" measures only the NO branch. Council has never said
yes, so there is no data whatsoever on its skill at saying yes.

That gap blocks everything downstream. CLAUDE.md's "Trade execution &
approval" promotion criteria were written for the mechanical TA/ICT
setups -- (a) a historical backtest edge, (b) forward paper-trade
agreement, (c) user confirmation -- and the advisory pipeline can satisfy
NONE of them as written: (a) is impossible because a discretionary
research pipeline can't be replayed over years of history, and (b)
requires approvals that do not exist. So the advisory pipeline currently
has no achievable promotion path at all. It isn't failing the bar; there
is no bar it could pass.

This script builds the one experiment that closes the gap without
risking anything and without needing a single approval: grade the
COUNTERFACTUAL. For every verdict this project has ever issued, simulate
buying it anyway under CLAUDE.md's own exit rule, and ask what the
skipped trades would have done.

The result is decision-relevant in both directions, which is the point:
  - If the council's WATCH downgrades would have LOST money RELATIVE TO
    THE MARKET BASELINE, council is earning its keep.
  - If they would have BEATEN that baseline, council is too strict, and
    that is hard evidence for the recalibration conversation CLAUDE.md's
    standing 2026-09-03/09-09 decisions reserve for the user.
Either outcome is worth more than a connected demo account sitting idle
waiting for an approval that may statistically never arrive.

FIRST RESULT (2026-09-11) -- AND WHY THE BASELINE IS NOT OPTIONAL
-----------------------------------------------------------------
Run bare, `run` reported council's downgrades at -1.71%/trade and that
reads like vindication: the skipped trades lost money. Then `baseline`
returned the date-matched whole-market figure for the same days:
**-1.71%/trade. Identical.** The names council rejected performed exactly
as well as buying any liquid stock at random on the same dates. Council
demonstrated no measurable selection skill on this sample -- not bad
skill, NO skill, in either direction. Reporting the -1.71% alone would
have been actively misleading, which is why `run` must never be quoted
without `baseline` beside it.

What is actually generating every number here is the EXIT RULE. Solve for
the break-even win rate of -4% stop / +8% target: p*8 = (1-p)*4, so
p = 33.3%. The market delivered 6.9-22.3% depending on the date, and this
project's own picks 25.5%. Every strategy tested against this rule has to
lift a ~20% base rate above 33.3% to make money -- which may be the
common cause behind all 26 mechanical variants coming back flat or
negative, since backtest_ta/backtest_ict/backtest_confluence all measure
against this same rule by design.
Do NOT over-extend that: this baseline covers ONE eight-session window
(2026-09-02..09-11) and cannot support a general claim about the rule.
Against it, backtest_ta's own 6-year numbers (breakout -0.06%/trade,
ema_cross +0.01%) sit far closer to zero, which suggests this particular
window was unusually hostile rather than the rule being -1.7% forever.
The missing piece is a LONG-RUN whole-market baseline under this rule --
which is exactly what the survivorship-fixed `backtest_ta.py fetch` would
make computable, and a strong argument for finishing that fetch.

WHAT THIS IS NOT
----------------
Not a trading system. It places no orders, imports no order-placing code,
and never will -- same standing rule as every other skill/script in this
repo. It only reads verdicts off disk and prices off a market-data API.
It is also NOT the advisory pipeline itself: nothing here proposes a
trade, and a good counterfactual number is not a buy signal.

EXIT RULE PARITY
----------------
The stop/target/time-stop simulation is `backtest_ta._simulate_exit`,
IMPORTED rather than reimplemented, for the same reason paper_trader.py
reuses backtest_ta's signal function: two tracks that define the same
rule separately will eventually define it differently. Entry is the NEXT
session's open after the verdict date (no lookahead -- the verdict was
written using information through that day), exits at whichever of
-4% / +8% / 5-trading-days lands first, stop assumed first when a single
day's range touches both.

RESOLVED vs PROVISIONAL
-----------------------
A verdict whose 5-trading-day window has not fully elapsed is reported as
PROVISIONAL and is EXCLUDED from every headline aggregate. This matters
more than it sounds: on 2026-09-11, 12 of the 17 most recent verdicts
were too young to grade, and folding their partial returns into an
average would have been grading noise. `_simulate_exit` returning None is
exactly this case and is treated as such, never as a zero.

DATA SOURCE
-----------
Alpaca daily bars by default: it carries the most recent session (Massive
does not settle until ~30-90min post-close, see CLAUDE.md) and its free
tier allows ~200 req/min against Massive's 5, which is the difference
between a 30-second run and an 18-minute one. Its IEX feed is
partial-VOLUME, but this script only reads prices, and prices were
confirmed to agree with Massive's full tape to within 0.04% (ADBE 09-10:
$248.83 Massive vs $248.73 Alpaca). Do not take that on faith -- the
`verify` command re-measures that agreement against Massive and prints
the worst divergence it finds. Run it before trusting any number here for
a real decision, per lessons.md #2.

Usage:
  python scripts/counterfactual.py run            # grade everything
  python scripts/counterfactual.py run --refresh  # ignore cached bars
  python scripts/counterfactual.py baseline        # THE CONTROL -- never quote `run` without it
  python scripts/counterfactual.py verify 8       # cross-check 8 tickers vs Massive
"""

import sys
import json
import time
import datetime
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from backtest_ta import _simulate_exit, STOP_PCT, TARGET_PCT, TIME_STOP_DAYS  # noqa: E402
from alpaca_client import get_historical_bars  # noqa: E402

RESEARCH_DIR = Path("data/research")
CACHE_DIR = Path("data/reference/counterfactual_cache")
OUT_PATH = Path("data/reference/counterfactual_results.json")
# Wide enough that every verdict date has >=5 following sessions available
# once they exist; start is bounded by the free tier's ~2yr lookback anyway.
FETCH_START, FETCH_END = "2026-08-01", None  # None -> today


def _today():
    return datetime.date.today().isoformat()


def load_verdicts():
    """Every verdict this project has issued, from the research notes
    themselves rather than from trade_ledger.md -- the ledger is a curated
    human-readable summary and has known gaps (17 rows sat marked 'Not
    checked' until 2026-09-11), while the notes are the primary record.

    A ticker researched on several dates yields several independent
    verdicts; that's correct, each was a separate decision made on
    separate information."""
    out = []
    council = {}
    for f in sorted(RESEARCH_DIR.glob("*/*_council.md")):
        date, tick = f.parent.name, f.stem[:-len("_council")]
        for line in f.read_text().splitlines():
            if line.strip().startswith("Verdict:"):
                council[(date, tick)] = line.split("Verdict:", 1)[1].strip()
                break
    for f in sorted(RESEARCH_DIR.glob("*/*.md")):
        if f.stem.endswith("_council"):
            continue
        date, tick, txt = f.parent.name, f.stem, f.read_text()
        verdict = confidence = None
        lines = txt.splitlines()
        for i, line in enumerate(lines):
            h = line.strip().lower()
            nxt = next((x.strip() for x in lines[i + 1:] if x.strip()), "")
            if h.startswith("## verdict") and not verdict:
                verdict = nxt.split()[0].upper().strip(".,—-") if nxt else None
            elif h.startswith("## confidence") and not confidence:
                confidence = nxt.split()[0].lower().strip(".,—-") if nxt else None
        out.append({
            "date": date, "ticker": tick, "verdict": verdict,
            "confidence": confidence,
            "council_verdict": council.get((date, tick)),
            "reached_council": (date, tick) in council,
        })
    return out


def fetch_bars(ticker, refresh=False):
    """Daily bars for one ticker, cached. Returns backtest_ta's bar shape:
    [(date, o, h, l, c, v), ...] chronological, so _simulate_exit can be
    used directly without any reshaping."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = CACHE_DIR / f"{ticker.replace('/', '_')}.json"
    if cache.exists() and not refresh:
        return [tuple(b) for b in json.loads(cache.read_text())]
    end = FETCH_END or _today()
    try:
        raw = get_historical_bars(ticker, f"{FETCH_START}T00:00:00Z",
                                  f"{end}T23:59:59Z", timeframe="1Day")
    except Exception as e:
        print(f"  {ticker}: fetch error ({e})")
        return []
    bars = [(b["t"][:10], b["o"], b["h"], b["l"], b["c"], b["v"]) for b in raw]
    cache.write_text(json.dumps(bars))
    time.sleep(0.32)  # 200 req/min free tier, safety margin
    return bars


def grade(v, bars):
    """Counterfactual outcome of BUYING this verdict's ticker anyway.

    Returns (status, return_or_None, detail). status is one of:
      resolved     -- the full 5-day window elapsed and the rule fired
      provisional  -- window still open; partial state reported, NOT graded
      no_data      -- ticker not available from the price feed
      no_session   -- no trading session after the verdict date yet
    """
    if not bars:
        return "no_data", None, "not on the price feed (foreign listing, OTC, or delisted)"
    prior = [i for i, b in enumerate(bars) if b[0] <= v["date"]]
    if not prior:
        return "no_data", None, "no bars at or before the verdict date"
    idx = prior[-1]
    if idx + 1 >= len(bars):
        return "no_session", None, "no session after the verdict date yet"
    r = _simulate_exit(bars, idx)
    entry = bars[idx + 1][1]
    fwd = bars[idx + 1: idx + 1 + TIME_STOP_DAYS]
    if r is None:
        last = fwd[-1][4]
        return "provisional", None, (f"{len(fwd)}/{TIME_STOP_DAYS} sessions elapsed, "
                                     f"currently {(last - entry) / entry * 100:+.1f}%")
    if abs(r - STOP_PCT) < 1e-9:
        d = "stop -4% hit"
    elif abs(r - TARGET_PCT) < 1e-9:
        d = "target +8% hit"
    else:
        d = f"time-stop, {r * 100:+.1f}%"
    return "resolved", r, d


def _stats(rows):
    """rows: list of (label, return). Returns a printable summary line."""
    n = len(rows)
    if not n:
        return "no resolved observations"
    rets = [r for _, r in rows]
    wins = sum(1 for r in rets if r > 0)
    avg = sum(rets) / n
    tgt = sum(1 for r in rets if abs(r - TARGET_PCT) < 1e-9)
    stp = sum(1 for r in rets if abs(r - STOP_PCT) < 1e-9)
    return (f"n={n:<4} avg {avg * 100:+.2f}%/trade   win {wins / n * 100:4.1f}%   "
            f"target {tgt:<3} stop {stp:<3} time-stop {n - tgt - stp}")


def run(refresh=False):
    verdicts = load_verdicts()
    print(f"Loaded {len(verdicts)} verdicts from {RESEARCH_DIR}/")
    tickers = sorted({v["ticker"] for v in verdicts})
    print(f"Fetching bars for {len(tickers)} unique tickers "
          f"({'refreshing' if refresh else 'cached where available'})...")
    bars = {t: fetch_bars(t, refresh) for t in tickers}

    buckets = defaultdict(list)
    provisional, nodata = [], []
    results = []
    for v in verdicts:
        status, r, detail = grade(v, bars[v["ticker"]])
        results.append({**v, "status": status, "return": r, "detail": detail})
        tag = f"{v['date']} {v['ticker']}"
        if status == "resolved":
            buckets["ALL"].append((tag, r))
            if v["reached_council"]:
                buckets["council-reviewed (all downgraded to WATCH)"].append((tag, r))
            else:
                buckets[f"research-level {v['verdict'] or '?'}"].append((tag, r))
            if v["confidence"]:
                buckets[f"confidence={v['confidence']}"].append((tag, r))
        elif status == "provisional":
            provisional.append((tag, detail))
        else:
            nodata.append((tag, detail))

    print(f"\n{'=' * 78}\nCOUNTERFACTUAL: what if we had BOUGHT every verdict anyway?")
    print(f"Exit rule: {STOP_PCT * 100:+.0f}% stop / {TARGET_PCT * 100:+.0f}% target / "
          f"{TIME_STOP_DAYS}-day time-stop, entry at the next session's open")
    print(f"{'=' * 78}")
    print(f"\n{'bucket':<44}summary")
    print("-" * 78)
    order = (["ALL", "council-reviewed (all downgraded to WATCH)"]
             + sorted(k for k in buckets if k.startswith("research-level"))
             + sorted(k for k in buckets if k.startswith("confidence=")))
    for k in order:
        if k in buckets:
            print(f"{k:<44}{_stats(buckets[k])}")

    print(f"\nPROVISIONAL ({len(provisional)}) — window still open, EXCLUDED from the above:")
    for tag, d in provisional:
        print(f"  {tag:<18}{d}")
    if nodata:
        print(f"\nNOT GRADED ({len(nodata)}):")
        for tag, d in nodata:
            print(f"  {tag:<18}{d}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps({"generated": _today(), "results": results}, indent=2))
    print(f"\nPer-verdict detail written to {OUT_PATH}")

    key = buckets.get("council-reviewed (all downgraded to WATCH)", [])
    if key:
        avg = sum(r for _, r in key) / len(key)
        print(f"\n{'=' * 78}\nTHE HEADLINE: buying every council downgrade would have averaged "
              f"{avg * 100:+.2f}%/trade over {len(key)} resolved verdicts.")
        print("Positive => council may be too strict. Negative => its skepticism is earning its keep.")
        print("Either way this is EVIDENCE FOR A CONVERSATION, not a trigger: CLAUDE.md's standing")
        print("2026-09-03/09-09 decisions reserve any change to council's bar for the user.")
        print("=" * 78)


def baseline(refresh=False):
    """THE CONTROL, without which the `run` numbers mean nothing.

    `run` says buying the council's downgrades would have averaged about
    -1.7%/trade. On its own that reads as "council's skepticism is
    earning its keep" -- but it is uninterpretable until you know what
    ANY stock would have returned under the same rule over the same days.
    A -4% stop against a +8% target is structurally punishing: a typical
    liquid name moves 2-3% a day, so the stop sits inside the noise band
    and gets tagged constantly regardless of whether the thesis was
    right. If the whole market averages -1.4% under this rule over this
    window, the pipeline has NO selection skill, good or bad, and the
    exit rule is what's producing the number.

    So: apply the identical rule to every liquid stock on the SAME
    verdict dates, weighted by the same date distribution the project's
    own verdicts have (date-matching matters -- the verdicts cluster on a
    handful of days, and those days aren't interchangeable).

    Reuses backtest_ta's fetch_range/_load_series/_simulate_exit, so the
    control and the thing it controls for cannot define the rule or the
    liquidity filter differently. Needs Massive credentials; ~9 calls at
    the free tier's 5/min."""
    from backtest_ta import fetch_range, _load_series, PRICE_MIN, PRICE_MAX, VOLUME_MIN
    start, end = "2026-09-01", _today()
    print(f"Fetching whole-market daily bars {start}..{end} (Massive, ~13s/day)...")
    fetch_range(start, end)
    series = _load_series(start, end)
    print(f"Loaded {len(series)} tickers\n")

    verdict_dates = [v["date"] for v in load_verdicts()]
    by_date = defaultdict(list)
    for tick, bars in series.items():
        for i, b in enumerate(bars):
            date, o, h, l, c, v = b
            if not (PRICE_MIN <= c <= PRICE_MAX and v >= VOLUME_MIN):
                continue
            r = _simulate_exit(bars, i)
            if r is not None:
                by_date[date].append(r)

    print(f"{'verdict date':<14}{'market n':>10}{'market avg':>13}{'market win%':>13}")
    print("-" * 52)
    matched = []
    for d in sorted(set(verdict_dates)):
        # a verdict dated D enters at D+1's open, same as the market sample keyed on D
        rs = by_date.get(d, [])
        if not rs:
            print(f"{d:<14}{'-':>10}{'not resolvable yet':>26}")
            continue
        avg = sum(rs) / len(rs)
        win = sum(1 for r in rs if r > 0) / len(rs) * 100
        n_verdicts = verdict_dates.count(d)
        matched += [avg] * n_verdicts  # weight by how many verdicts that date carried
        print(f"{d:<14}{len(rs):>10}{avg * 100:>12.2f}%{win:>12.1f}%")

    if matched:
        mb = sum(matched) / len(matched)
        print(f"\nDate-matched market baseline: {mb * 100:+.2f}%/trade")
        print("Compare against `run`'s buckets. The pipeline only demonstrates selection")
        print("skill to the extent its numbers differ from THIS, not from zero.")


def verify(n=8):
    """Re-measure the Alpaca-vs-Massive price agreement this script's
    speed/accuracy trade-off rests on. Prices only -- IEX volume is known
    to be partial and is not compared."""
    from massive_client import get_ticker_range_aggs
    verdicts = load_verdicts()
    tickers = sorted({v["ticker"] for v in verdicts})[:n]
    print(f"Cross-checking {len(tickers)} tickers, Alpaca vs Massive (13s apart, 5 req/min)...\n")
    worst = 0.0
    for t in tickers:
        a = {b[0]: b[4] for b in fetch_bars(t)}
        try:
            m = {datetime.datetime.utcfromtimestamp(b["t"] / 1000).date().isoformat(): b["c"]
                 for b in get_ticker_range_aggs(t, FETCH_START, FETCH_END or _today())}
        except Exception as e:
            print(f"  {t:<7} massive error: {e}")
            continue
        shared = sorted(set(a) & set(m))
        if not shared:
            print(f"  {t:<7} no overlapping sessions")
            continue
        diffs = [abs(a[d] - m[d]) / m[d] for d in shared if m[d]]
        mx = max(diffs) * 100
        worst = max(worst, mx)
        print(f"  {t:<7} {len(shared):>3} shared sessions, max close divergence {mx:.3f}%")
        time.sleep(13)
    print(f"\nWorst divergence across all checked: {worst:.3f}%")
    print("Under ~0.1% means Alpaca prices are safe for this script's purpose.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "run":
        run(refresh="--refresh" in sys.argv)
    elif cmd == "baseline":
        baseline(refresh="--refresh" in sys.argv)
    elif cmd == "verify":
        verify(int(sys.argv[2]) if len(sys.argv) > 2 else 8)
    else:
        print(__doc__.strip().split("Usage:")[-1])
