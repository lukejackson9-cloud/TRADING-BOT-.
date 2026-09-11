"""
Tests the EXIT RULE itself, which every other backtest in this project
holds fixed and therefore cannot see.

WHY
---
`scripts/counterfactual.py` (2026-09-11) found that the whole market
returned -1.71%/trade under CLAUDE.md's -4% stop / +8% target / 5-day
time-stop over the 2026-09-02..09-11 window -- identical to what the
council's rejected names returned. The arithmetic behind that: a -4%/+8%
rule needs p*8 = (1-p)*4, i.e. a **33.3% win rate**, just to break even.
The market delivered 6.9-22.3%.

Every backtest in this repo -- backtest_ta, backtest_ict,
backtest_confluence, all 26 mechanical variants -- measures its signal
against this one rule, by design ("so results are measured against the
rule this project already trades by"). If the rule is the binding
constraint, then all 26 "no edge" verdicts may be measuring the rule
rather than the signals, and no amount of additional signal-hunting will
change them. That is a different problem from "no signal works," and it
has a different fix.

THE ONE QUESTION THAT MATTERS: SIGNAL MINUS BASELINE
----------------------------------------------------
A wider stop will improve almost any rule's average return, because it
stops converting ordinary volatility into realized losses. That is NOT
edge -- an unconditional buy gets the same benefit. So this script always
computes TWO populations under every candidate rule:

  baseline  -- every liquid ticker-day in the window (unconditional entry)
  signal    -- only days where backtest_ta's own iter_signals() fired

and reports **signal minus baseline**. A rule only matters to this
project if it widens that gap. A rule that lifts both equally has found
beta, not alpha, and adopting it would just be taking more market risk
with extra steps.

DATA
----
Reads data/reference/backtest_cache/ day-files, which since 2026-09-11
are written by the SURVIVORSHIP-BIAS-FIXED fetch_range() -- so unlike
every historical number currently in CLAUDE.md, these are not filtered
through today's active-ticker list. See backtest_ta.py's module docstring.
Uses backtest_ta's own liquidity filters and iter_signals() so the
signal population here is identical to the one those backtests use.

Entry is the next session's open after the signal/entry day, matching
_simulate_exit's convention exactly. The stop-first-on-both-touched
convention is preserved too.

SCOPE CAVEAT -- READ BEFORE QUOTING ANY NUMBER FROM THIS
--------------------------------------------------------
This runs on whatever is cached. As of 2026-09-11 that is 63 consecutive
sessions (2024-09-11..2024-12-06) plus a detached 8-day 2026 block. Three
months is ONE regime, and a bull-quarter regime at that. A rule that
looks better here may simply suit this stretch of tape. This is a
hypothesis generator, not evidence for changing CLAUDE.md's Strategy
section -- that needs the full 2-year fetch (parked at 63/520 days) and,
per the standing 2026-09-03/09-09 user decisions, an explicit user
decision regardless of what the numbers say.

Usage:
  python scripts/exit_rule_sweep.py                 # sweep the cached window
  python scripts/exit_rule_sweep.py 2024-09-11 2024-12-06
"""

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from backtest_ta import (  # noqa: E402
    _load_series, iter_signals, CACHE_DIR,
    PRICE_MIN, PRICE_MAX, VOLUME_MIN,
    STOP_PCT, TARGET_PCT, TIME_STOP_DAYS,
)

STOPS = [-0.02, -0.04, -0.06, -0.08, -0.12, None]   # None = no stop
TARGETS = [0.04, 0.06, 0.08, 0.12, 0.16, None]      # None = no target
TIME_STOPS = [5, 10, 20]
MAX_HORIZON = max(TIME_STOPS)


def _first_touch(bars, entry_idx):
    """One forward pass per entry, reused by every parameter combo.

    Returns (entry_price, stop_touch, target_touch, closes) where
    stop_touch[s] / target_touch[t] is the 1-based day that threshold was
    first crossed (or None), and closes[d] is the close on day d. Doing
    this once per entry instead of once per (entry, combo) is what keeps
    a 90-combo sweep over ~100k entries tractable in pure Python."""
    if entry_idx + 1 >= len(bars):
        return None
    entry = bars[entry_idx + 1][1]  # next session's open
    if entry <= 0:
        return None
    stop_touch = {s: None for s in STOPS if s is not None}
    target_touch = {t: None for t in TARGETS if t is not None}
    closes = {}
    for d in range(1, MAX_HORIZON + 1):
        idx = entry_idx + d
        if idx >= len(bars):
            break
        _, _o, h, l, c, _v = bars[idx]
        closes[d] = c
        for s in stop_touch:
            if stop_touch[s] is None and l <= entry * (1 + s):
                stop_touch[s] = d
        for t in target_touch:
            if target_touch[t] is None and h >= entry * (1 + t):
                target_touch[t] = d
    return entry, stop_touch, target_touch, closes


def _outcome(rec, stop, target, ts):
    """Return for one (stop, target, time-stop) combo, or None if the
    window ran off the end of available data (never counted as zero --
    same discipline as counterfactual.py's provisional handling)."""
    entry, stop_touch, target_touch, closes = rec
    if ts not in closes:
        return None
    sd = stop_touch.get(stop) if stop is not None else None
    td = target_touch.get(target) if target is not None else None
    sd = sd if (sd is not None and sd <= ts) else None
    td = td if (td is not None and td <= ts) else None
    if sd is not None and (td is None or sd <= td):
        return stop          # stop first; ties go to the stop (conservative)
    if td is not None:
        return target
    return (closes[ts] - entry) / entry


def run(start, end):
    series = _load_series(start, end)
    print(f"Loaded {len(series)} tickers from {CACHE_DIR} for {start}..{end}")

    baseline, signal = [], []
    for ticker, bars in series.items():
        if len(bars) < 25:
            continue
        sig_idx = {i for i, _d, _s in iter_signals(bars)}
        for i, b in enumerate(bars):
            _date, _o, _h, _l, c, v = b
            if not (PRICE_MIN <= c <= PRICE_MAX and v >= VOLUME_MIN):
                continue
            rec = _first_touch(bars, i)
            if rec is None:
                continue
            baseline.append(rec)
            if i in sig_idx:
                signal.append(rec)
    print(f"{len(baseline):,} baseline entries (every liquid ticker-day), "
          f"{len(signal):,} signal entries (iter_signals fired)\n")
    if not baseline:
        print("No entries -- is the cache populated for this range?")
        return

    def stats(pop, stop, target, ts):
        rs = [r for r in (_outcome(rec, stop, target, ts) for rec in pop) if r is not None]
        if not rs:
            return None, None, 0
        return sum(rs) / len(rs), sum(1 for r in rs if r > 0) / len(rs), len(rs)

    def lbl(stop, target, ts):
        s = "none" if stop is None else f"{stop * 100:+.0f}%"
        t = "none" if target is None else f"{target * 100:+.0f}%"
        return f"stop {s:<5} target {t:<5} {ts:>2}d"

    rows = []
    for ts in TIME_STOPS:
        for stop in STOPS:
            for target in TARGETS:
                b_avg, b_win, b_n = stats(baseline, stop, target, ts)
                s_avg, s_win, s_n = stats(signal, stop, target, ts)
                if b_avg is None or s_avg is None or s_n < 30:
                    continue
                rows.append({
                    "label": lbl(stop, target, ts), "stop": stop,
                    "target": target, "ts": ts,
                    "b_avg": b_avg, "b_win": b_win, "b_n": b_n,
                    "s_avg": s_avg, "s_win": s_win, "s_n": s_n,
                    "edge": s_avg - b_avg,
                })

    cur = next((r for r in rows if r["stop"] == STOP_PCT and r["target"] == TARGET_PCT
                and r["ts"] == TIME_STOP_DAYS), None)

    print("=" * 100)
    print("EXIT-RULE SWEEP — every combo, ranked by SIGNAL MINUS BASELINE (the only column that means anything)")
    print("=" * 100)
    print(f"{'rule':<30}{'baseline':>11}{'signal':>11}{'EDGE':>10}{'b.win':>8}{'s.win':>8}{'sig n':>9}")
    print("-" * 100)
    for r in sorted(rows, key=lambda r: -r["edge"])[:15]:
        mark = "  <-- CURRENT" if r is cur else ""
        print(f"{r['label']:<30}{r['b_avg'] * 100:>10.2f}%{r['s_avg'] * 100:>10.2f}%"
              f"{r['edge'] * 100:>9.2f}%{r['b_win'] * 100:>7.1f}%{r['s_win'] * 100:>7.1f}%"
              f"{r['s_n']:>9,}{mark}")

    if cur:
        print("\n" + "-" * 100)
        print("CLAUDE.md's CURRENT rule, for comparison:")
        print(f"{cur['label']:<30}{cur['b_avg'] * 100:>10.2f}%{cur['s_avg'] * 100:>10.2f}%"
              f"{cur['edge'] * 100:>9.2f}%{cur['b_win'] * 100:>7.1f}%{cur['s_win'] * 100:>7.1f}%"
              f"{cur['s_n']:>9,}")
        rank = sorted(rows, key=lambda r: -r["edge"]).index(cur) + 1
        print(f"Ranked {rank} of {len(rows)} combos by edge.")

    # First-half / second-half consistency -- this project's standard
    # honesty check, the one that caught vcp_breakout's false positive and
    # the macro-calendar aggregate. An edge that flips sign across halves
    # is noise dressed up by a convenient aggregate, and is reported as
    # such rather than as a finding.
    dates = sorted({b[0] for bars in series.values() for b in bars})
    mid = dates[len(dates) // 2]
    print("\n" + "=" * 100)
    print(f"SPLIT-HALF CHECK (first half < {mid} <= second half) — does the edge survive?")
    print("=" * 100)
    print(f"{'rule':<30}{'edge H1':>10}{'edge H2':>10}{'consistent?':>14}")
    print("-" * 100)

    def half_pop(pop_bars, first):
        out = []
        for ticker, bars in series.items():
            if len(bars) < 25:
                continue
            sig_idx = {i for i, _d, _s in iter_signals(bars)} if pop_bars == "signal" else None
            for i, b in enumerate(bars):
                date, _o, _h, _l, c, v = b
                if (date < mid) != first:
                    continue
                if not (PRICE_MIN <= c <= PRICE_MAX and v >= VOLUME_MIN):
                    continue
                if sig_idx is not None and i not in sig_idx:
                    continue
                rec = _first_touch(bars, i)
                if rec is not None:
                    out.append(rec)
        return out

    halves = {(p, h): half_pop(p, h) for p in ("baseline", "signal") for h in (True, False)}
    for r in sorted(rows, key=lambda r: -r["edge"])[:6] + ([cur] if cur else []):
        edges = []
        for h in (True, False):
            b_avg, _, _ = stats(halves[("baseline", h)], r["stop"], r["target"], r["ts"])
            s_avg, _, s_n = stats(halves[("signal", h)], r["stop"], r["target"], r["ts"])
            edges.append(None if (b_avg is None or s_avg is None or s_n < 15) else s_avg - b_avg)
        e1, e2 = edges
        if e1 is None or e2 is None:
            verdict = "insufficient n"
        elif (e1 > 0) == (e2 > 0):
            verdict = "consistent" if e1 > 0 else "consistently NEG"
        else:
            verdict = "FLIPS — noise"
        f = lambda e: "   n/a" if e is None else f"{e * 100:>9.2f}%"
        tag = "  <-- CURRENT" if r is cur else ""
        print(f"{r['label']:<30}{f(e1)}{f(e2)}{verdict:>14}{tag}")

    best = max(rows, key=lambda r: r["edge"])
    print("\n" + "=" * 100)
    print(f"Best edge: {best['label']}  =>  {best['edge'] * 100:+.2f}%/trade over baseline")
    if cur:
        print(f"Current:   {cur['label']}  =>  {cur['edge'] * 100:+.2f}%/trade over baseline")
    print("\nREAD THIS BEFORE ACTING: a rule that lifts BOTH columns has found beta, not alpha.")
    print("Only the EDGE column reflects whether the signal knows something. And this is one")
    print("~3-month regime on a partially-fetched cache — a hypothesis, not a mandate to change")
    print("CLAUDE.md's Strategy section, which per the standing user decisions is the user's call.")
    print("=" * 100)


if __name__ == "__main__":
    a = sys.argv[1:]
    run(a[0] if a else "2024-09-11", a[1] if len(a) > 1 else "2024-12-06")
