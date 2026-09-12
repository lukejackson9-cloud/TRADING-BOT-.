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


def _prior_vol(bars, i, window=20):
    """Realized volatility over the `window` sessions ENDING at bar i --
    strictly information available when the signal fired, no lookahead.
    Stdev of daily close-to-close returns, as a plain fraction."""
    if i < window:
        return None
    rets = []
    for k in range(i - window + 1, i + 1):
        p, c = bars[k - 1][4], bars[k][4]
        if p > 0:
            rets.append((c - p) / p)
    if len(rets) < window // 2:
        return None
    m = sum(rets) / len(rets)
    return (sum((r - m) ** 2 for r in rets) / len(rets)) ** 0.5


def volmatch(start, end):
    """Separates the two diagnoses the plain sweep cannot tell apart:

      (a) the signals genuinely pick worse-performing stocks, or
      (b) the signals pick MORE VOLATILE stocks, and a stop/target rule
          mechanically punishes volatility -- a -4% stop sits inside the
          daily noise band of a high-vol name and outside it for a
          sleepy one, so the same rule is effectively a different rule
          depending on what you point it at.

    These have completely different fixes, and the unmatched comparison in
    run() cannot distinguish them because it compares signal names against
    a baseline dominated by lower-volatility tickers.

    Method: compare every signal entry only against NON-signal entries
    from the SAME SESSION and the SAME within-day volatility decile, then
    average the per-entry differences. Same-date matching matters because
    day effects are large and already measured (counterfactual.py found
    whole-market returns swinging -1.34% to -3.18% across adjacent verdict
    dates); decile matching is computed per-date so it ranks each name
    against that day's own cross-section rather than a fixed threshold."""
    series = _load_series(start, end)
    print(f"Loaded {len(series)} tickers for {start}..{end}\n")

    entries = []  # (date, vol, is_signal, rec)
    for ticker, bars in series.items():
        if len(bars) < 25:
            continue
        sig_idx = {i for i, _d, _s in iter_signals(bars)}
        for i, b in enumerate(bars):
            date, _o, _h, _l, c, v = b
            if not (PRICE_MIN <= c <= PRICE_MAX and v >= VOLUME_MIN):
                continue
            vol = _prior_vol(bars, i)
            if vol is None:
                continue
            rec = _first_touch(bars, i)
            if rec is not None:
                entries.append((date, vol, i in sig_idx, rec))

    sig_vols = sorted(v for _d, v, s, _r in entries if s)
    ctl_vols = sorted(v for _d, v, s, _r in entries if not s)
    if not sig_vols or not ctl_vols:
        print("not enough entries")
        return
    med = lambda xs: xs[len(xs) // 2]
    print("=" * 96)
    print("STEP 1 — is the premise even true? Are signal names actually more volatile?")
    print("=" * 96)
    print(f"  signal entries  n={len(sig_vols):>6,}   median 20d vol {med(sig_vols) * 100:.2f}%/day")
    print(f"  control entries n={len(ctl_vols):>6,}   median 20d vol {med(ctl_vols) * 100:.2f}%/day")
    ratio = med(sig_vols) / med(ctl_vols) if med(ctl_vols) else float("nan")
    print(f"  ratio: {ratio:.2f}x  -> "
          + ("premise HOLDS, matching is necessary" if ratio > 1.1 else
             "premise is WEAK; the confound may not be doing much work"))

    # per-date volatility deciles
    by_date = defaultdict(list)
    for e in entries:
        by_date[e[0]].append(e)
    celled = defaultdict(lambda: {"sig": [], "ctl": []})
    for date, es in by_date.items():
        vs = sorted(e[1] for e in es)
        cuts = [vs[int(len(vs) * q / 10)] for q in range(1, 10)]
        for date_, vol, is_sig, rec in es:
            d = sum(1 for c in cuts if vol > c)
            celled[(date_, d)]["sig" if is_sig else "ctl"].append(rec)

    def matched(stop, target, ts, cells=None):
        """Mean of (signal return - same-cell control mean)."""
        cells = cells if cells is not None else celled
        diffs, raw_s, raw_c = [], [], []
        for _key, cell in cells.items():
            ctl = [r for r in (_outcome(rec, stop, target, ts) for rec in cell["ctl"]) if r is not None]
            if not ctl:
                continue
            cm = sum(ctl) / len(ctl)
            raw_c += ctl
            for rec in cell["sig"]:
                r = _outcome(rec, stop, target, ts)
                if r is not None:
                    diffs.append(r - cm)
                    raw_s.append(r)
        if not diffs:
            return None, None, None, 0
        return (sum(diffs) / len(diffs),
                sum(raw_s) / len(raw_s),
                sum(raw_c) / len(raw_c), len(diffs))

    rules = [(STOP_PCT, TARGET_PCT, TIME_STOP_DAYS), (-0.08, 0.08, 5),
             (-0.08, None, 20), (None, None, 20), (None, None, 5)]
    print("\n" + "=" * 96)
    print("STEP 2 — signal vs VOLATILITY-MATCHED control (same session, same within-day vol decile)")
    print("=" * 96)
    print("NOTE: MATCHED EDGE is the mean of per-entry (signal - its own cell's control mean).")
    print("It deliberately does NOT equal the gap between the two pooled columns beside it --")
    print("signal entries cluster in high-vol cells, where controls also do worse, and that")
    print("re-weighting is the entire point of matching.")
    print(f"{'rule':<30}{'signal':>10}{'matched ctl':>13}{'MATCHED EDGE':>15}{'n':>9}")
    print("-" * 96)
    out = {}
    for stop, target, ts in rules:
        edge, s_avg, c_avg, n = matched(stop, target, ts)
        if edge is None:
            continue
        s = "none" if stop is None else f"{stop * 100:+.0f}%"
        t = "none" if target is None else f"{target * 100:+.0f}%"
        label = f"stop {s:<5} target {t:<5} {ts:>2}d"
        cur = "  <-- CURRENT" if (stop, target, ts) == (STOP_PCT, TARGET_PCT, TIME_STOP_DAYS) else ""
        out[(stop, target, ts)] = edge
        print(f"{label:<30}{s_avg * 100:>9.2f}%{c_avg * 100:>12.2f}%{edge * 100:>14.2f}%{n:>9,}{cur}")

    # split-half on the matched estimator too -- same discipline as run()
    dates = sorted(by_date)
    mid = dates[len(dates) // 2]
    h1 = {k: v for k, v in celled.items() if k[0] < mid}
    h2 = {k: v for k, v in celled.items() if k[0] >= mid}
    print("\n" + "=" * 96)
    print(f"STEP 3 — split-half on the MATCHED edge (first half < {mid} <= second half)")
    print("=" * 96)
    print(f"{'rule':<30}{'H1':>10}{'H2':>10}{'verdict':>18}")
    print("-" * 96)
    for stop, target, ts in rules:
        if (stop, target, ts) not in out:
            continue
        e1 = matched(stop, target, ts, h1)[0]
        e2 = matched(stop, target, ts, h2)[0]
        s = "none" if stop is None else f"{stop * 100:+.0f}%"
        t = "none" if target is None else f"{target * 100:+.0f}%"
        label = f"stop {s:<5} target {t:<5} {ts:>2}d"
        if e1 is None or e2 is None:
            v = "insufficient n"
        elif (e1 > 0) == (e2 > 0):
            v = "consistent POS" if e1 > 0 else "consistent NEG"
        else:
            v = "FLIPS — noise"
        f = lambda e: "     n/a" if e is None else f"{e * 100:>9.2f}%"
        print(f"{label:<30}{f(e1)}{f(e2)}{v:>18}")
    print("\n" + "=" * 96)
    print("HOW TO READ THIS: if the matched edge is ~0 while the UNMATCHED edge in `run` was")
    print("clearly negative, the signals were being punished for picking volatile names, not for")
    print("picking bad ones — diagnosis (b), and the fix is position sizing / a vol-scaled stop.")
    print("If the matched edge stays negative and consistent, it is diagnosis (a): the signals")
    print("genuinely select worse-than-peer names, and no exit-rule change will save them.")
    print("=" * 96)


def realistic(start, end):
    """Compare CLAUDE.md's current exit rule against volatility-realistic
    alternatives — the "widen the stop and target" question, run properly.

    WHY THE CURRENT RULE MISFIRES (measured, not asserted). Signal-day
    20-day realised volatility across 4,504 signals: median 2.33%/day,
    p75 3.88%, p90 6.69%. Expected move over a 5-session hold is roughly
    vol*sqrt(5), so:
        median name: 5.2% expected  -> a -4% stop is 0.77x that
        p75    name: 8.7% expected  -> a -4% stop is 0.46x
        p90    name: 15.0% expected -> a -4% stop is 0.27x
    A stop set INSIDE one standard deviation of the move you are trying to
    capture is not protection against being wrong, it is a near-guarantee
    of being stopped by ordinary noise. That is the mechanical reason the
    forward paper track logged 47 stops against 4 targets.

    THE RATIO TRAP, stated up front so the comparison is not misread:
    widening stop and target TOGETHER in proportion does NOT change the
    break-even win rate. -4%/+8% and -8%/+16% are both 2:1, both need
    p*2 = (1-p) -> p = 33.3%. Widening buys fewer noise stop-outs, not a
    lower bar. Only changing the RATIO moves the bar.

    THE BETTER INSTRUMENT: a flat percentage stop is the wrong tool when
    the p90 name is 3x as volatile as the median — the same -8% means
    "thesis broken" for one and "Tuesday" for the other. So this also
    tests a VOLATILITY-SCALED stop: stop = k * (20d vol * sqrt(days)),
    target = 2x the stop distance. That makes the stop mean the same
    thing across names.

    Reports ABSOLUTE return (what a trader actually banks) AND matched
    edge vs a same-session, same-volatility-decile control (whether the
    SIGNAL knows anything). Both, because they answer different questions
    and yesterday's sweep showed a rule can lift the first while leaving
    the second at zero — that is captured beta, not skill, and it is worth
    having but must not be called an edge."""
    series = _load_series(start, end)
    try:
        from backtest_ta import _spy_closes
        spy = _spy_closes(start, end)
    except Exception:
        spy = None
        print("WARNING: no SPY closes; relative_strength will not fire\n")

    # (date, vol, is_signal, bars, idx)
    entries = []
    for ticker, bars in series.items():
        if len(bars) < 25:
            continue
        sig = {i for i, _d, _s in iter_signals(bars, spy_closes=spy)}
        for i, b in enumerate(bars):
            date, _o, _h, _l, c, v = b
            if not (PRICE_MIN <= c <= PRICE_MAX and v >= VOLUME_MIN):
                continue
            vol = _prior_vol(bars, i)
            if vol is None or i + 1 >= len(bars):
                continue
            entries.append((date, vol, i in sig, bars, i))
    print(f"{len(entries):,} entries ({sum(1 for e in entries if e[2]):,} signal)\n")

    def outcome(bars, i, stop_pct, tgt_pct, ts):
        """Per-entry thresholds, so a volatility-scaled stop can differ per
        trade. Same conventions as _outcome: next open entry, stop assumed
        first when a single session touches both, None if the window runs
        off the end of the data (never counted as zero)."""
        entry = bars[i + 1][1]
        if entry <= 0:
            return None
        s, g = entry * (1 + stop_pct), entry * (1 + tgt_pct)
        for k in range(1, ts + 1):
            if i + k >= len(bars):
                return None
            _, _o, h, l, c, _v = bars[i + k]
            if l <= s:
                return stop_pct
            if h >= g:
                return tgt_pct
            if k == ts:
                return (c - entry) / entry
        return None

    import math
    configs = [
        ("CURRENT  -4% / +8%  / 5d", lambda v: (-0.04, 0.08), 5),
        ("widened  -8% / +16% / 10d", lambda v: (-0.08, 0.16), 10),
        ("widened -12% / +24% / 10d", lambda v: (-0.12, 0.24), 10),
        ("ratio 1:3 -8% / +24% / 10d", lambda v: (-0.08, 0.24), 10),
        ("vol-scaled 1.5sig, 2:1, 10d", lambda v: (-1.5 * v * math.sqrt(10), 3.0 * v * math.sqrt(10)), 10),
        ("vol-scaled 2.0sig, 2:1, 10d", lambda v: (-2.0 * v * math.sqrt(10), 4.0 * v * math.sqrt(10)), 10),
    ]

    dates = sorted({e[0] for e in entries})
    mid = dates[len(dates) // 2]
    print(f"{'rule':<30}{'sig abs':>10}{'win%':>7}{'stop%':>7}{'ctl abs':>10}{'EDGE':>9}{'breakeven':>11}{'split-half':>14}")
    print("-" * 100)
    for label, fn, ts in configs:
        cells = defaultdict(lambda: {"sig": [], "ctl": []})
        by_date = defaultdict(list)
        for e in entries:
            by_date[e[0]].append(e)
        for date, es in by_date.items():
            vs = sorted(x[1] for x in es)
            cuts = [vs[int(len(vs) * q / 10)] for q in range(1, 10)]
            for date_, vol, is_sig, bars, i in es:
                d = sum(1 for c in cuts if vol > c)
                sp, tp = fn(vol)
                r = outcome(bars, i, sp, tp, ts)
                if r is None:
                    continue
                cells[(date_, d)]["sig" if is_sig else "ctl"].append((r, sp, tp))
        sig = [x for c in cells.values() for x in c["sig"]]
        ctl = [x for c in cells.values() for x in c["ctl"]]
        if len(sig) < 50:
            print(f"{label:<30}  insufficient n ({len(sig)})")
            continue
        diffs = []
        for (dt, dec), c in cells.items():
            if not c["ctl"]:
                continue
            cm = sum(x[0] for x in c["ctl"]) / len(c["ctl"])
            diffs += [(dt, x[0] - cm) for x in c["sig"]]
        sa = sum(x[0] for x in sig) / len(sig)
        ca = sum(x[0] for x in ctl) / len(ctl)
        win = sum(1 for x in sig if x[0] > 0) / len(sig) * 100
        stopped = sum(1 for x in sig if abs(x[0] - x[1]) < 1e-12) / len(sig) * 100
        edge = sum(d for _dt, d in diffs) / len(diffs) if diffs else float("nan")
        # break-even win rate implied by this rule's average reward:risk
        rr = (sum(x[2] for x in sig) / len(sig)) / abs(sum(x[1] for x in sig) / len(sig))
        be = 1 / (1 + rr) * 100
        h1 = [d for dt, d in diffs if dt < mid]
        h2 = [d for dt, d in diffs if dt >= mid]
        if len(h1) > 20 and len(h2) > 20:
            e1, e2 = sum(h1) / len(h1), sum(h2) / len(h2)
            sh = "consistent" if (e1 > 0) == (e2 > 0) else "FLIPS"
            sh += f" {e1*100:+.1f}/{e2*100:+.1f}"
        else:
            sh = "thin"
        print(f"{label:<30}{sa*100:>9.2f}%{win:>6.1f}%{stopped:>6.1f}%{ca*100:>9.2f}%{edge*100:>8.2f}%{be:>10.1f}%{sh:>14}")

    print("\n" + "=" * 100)
    print("sig abs = what the signal actually returned. ctl abs = same-session, same-vol-decile")
    print("control. EDGE = sig minus its own matched control; only THAT is skill. breakeven =")
    print("win rate this rule's realised reward:risk requires. stop% = share of trades stopped out.")
    print("A rule that lifts 'sig abs' but leaves EDGE at ~0 has bought market beta, which is real")
    print("money but is NOT evidence the signals work — size it as beta, not as an edge.")
    print("=" * 100)


def tweak(start, end):
    """"What if we changed the rule SLIGHTLY?" — the in-mandate version of
    the exit-rule question, and the only version this cache can answer.

    The 2026-09-12 per-setup run found breakout/relative_strength looking
    positive at 20-day holds, then showed that result rests on ~1.1
    independent episodes and is untestable here. But a 20-day hold is also
    OUT OF MANDATE: CLAUDE.md specifies an "intraday to ~2 week horizon".
    So this sweeps only horizons that are both in-mandate and testable —
    5 and 10 trading days (10 = two weeks exactly) — across every
    stop/target pair, using the volatility-matched estimator rather than
    the naive one, since signal names run 1.20x the control's volatility
    and a fixed stop is not neutral between them.

    Every number is signal-minus-matched-control. A rule that lifts the
    raw return but not this has bought beta, not edge.

    MULTIPLE COMPARISONS: 6 stops x 6 targets x 2 horizons = 72 cells.
    Picking the best of 72 guarantees a flattering number, so the ranking
    is NOT the output — the questions are (a) does ANY combo come back
    positive AND sign-consistent across halves, and (b) where does the
    current rule sit. Both are printed."""
    series = _load_series(start, end)
    try:
        from backtest_ta import _spy_closes
        spy = _spy_closes(start, end)
    except Exception:
        spy = None
        print("WARNING: no SPY closes — relative_strength will not fire\n")

    entries = []
    for ticker, bars in series.items():
        if len(bars) < 25:
            continue
        sig = {i for i, _d, _s in iter_signals(bars, spy_closes=spy)}
        for i, b in enumerate(bars):
            date, _o, _h, _l, c, v = b
            if not (PRICE_MIN <= c <= PRICE_MAX and v >= VOLUME_MIN):
                continue
            vol = _prior_vol(bars, i)
            if vol is None:
                continue
            rec = _first_touch(bars, i)
            if rec is not None:
                entries.append((date, vol, i in sig, rec))

    by_date = defaultdict(list)
    for e in entries:
        by_date[e[0]].append(e)
    cells = defaultdict(lambda: {"sig": [], "ctl": []})
    for date, es in by_date.items():
        vs = sorted(e[1] for e in es)
        cuts = [vs[int(len(vs) * q / 10)] for q in range(1, 10)]
        for date_, vol, is_sig, rec in es:
            d = sum(1 for c in cuts if vol > c)
            cells[(date_, d)]["sig" if is_sig else "ctl"].append(rec)

    dates = sorted(by_date)
    mid = dates[len(dates) // 2]
    h1 = {k: v for k, v in cells.items() if k[0] < mid}
    h2 = {k: v for k, v in cells.items() if k[0] >= mid}

    def matched(stop, target, ts, src=None):
        src = src if src is not None else cells
        diffs, raws = [], []
        for _k, cell in src.items():
            ctl = [r for r in (_outcome(rec, stop, target, ts) for rec in cell["ctl"]) if r is not None]
            if not ctl:
                continue
            cm = sum(ctl) / len(ctl)
            for rec in cell["sig"]:
                r = _outcome(rec, stop, target, ts)
                if r is not None:
                    diffs.append(r - cm)
                    raws.append(r)
        if not diffs:
            return None, None, 0
        return sum(diffs) / len(diffs), sum(raws) / len(raws), len(diffs)

    print("=" * 100)
    print("EFFECTIVE SAMPLE (in-mandate horizons only; 10 trading days = the 2-week mandate limit)")
    print("=" * 100)
    for ts in (5, 10):
        got = {d for (d, _dec), cell in cells.items()
               for rec in cell["sig"] if _outcome(rec, None, None, ts) is not None}
        eff = len(got) / ts
        print(f"  {ts:>2}d hold: {len(got):>3} dates with resolvable entries  ->  ~{eff:.1f} independent episodes"
              + ("   <-- thin, treat as indicative only" if eff < 4 else ""))
    print()

    rows = []
    for ts in (5, 10):
        for stop in STOPS:
            for target in TARGETS:
                edge, raw, n = matched(stop, target, ts)
                if edge is None or n < 100:
                    continue
                e1 = matched(stop, target, ts, h1)[0]
                e2 = matched(stop, target, ts, h2)[0]
                if e1 is None or e2 is None:
                    verdict = "insufficient n"
                elif (e1 > 0) == (e2 > 0):
                    verdict = "CONSISTENT POS" if e1 > 0 else "consistent neg"
                else:
                    verdict = "flips — noise"
                s = "none" if stop is None else f"{stop * 100:+.0f}%"
                t = "none" if target is None else f"{target * 100:+.0f}%"
                rows.append({"label": f"stop {s:<5} target {t:<5} {ts:>2}d", "edge": edge,
                             "raw": raw, "n": n, "e1": e1, "e2": e2, "verdict": verdict,
                             "key": (stop, target, ts)})

    cur = next((r for r in rows if r["key"] == (STOP_PCT, TARGET_PCT, TIME_STOP_DAYS)), None)
    ranked = sorted(rows, key=lambda r: -r["edge"])
    print("=" * 100)
    print("ALL IN-MANDATE RULE TWEAKS, volatility-matched, ranked by edge (top 12 of "
          f"{len(rows)})")
    print("=" * 100)
    print(f"{'rule':<30}{'raw sig':>10}{'MATCHED EDGE':>14}{'H1':>9}{'H2':>9}{'n':>8}{'verdict':>18}")
    print("-" * 100)
    f = lambda x: "    n/a" if x is None else f"{x * 100:>8.2f}%"
    for r in ranked[:12]:
        tag = "  <-- CURRENT" if r is cur else ""
        print(f"{r['label']:<30}{r['raw'] * 100:>9.2f}%{r['edge'] * 100:>13.2f}%"
              f"{f(r['e1'])}{f(r['e2'])}{r['n']:>8,}{r['verdict']:>18}{tag}")
    if cur and cur not in ranked[:12]:
        print("  ...")
        print(f"{cur['label']:<30}{cur['raw'] * 100:>9.2f}%{cur['edge'] * 100:>13.2f}%"
              f"{f(cur['e1'])}{f(cur['e2'])}{cur['n']:>8,}{cur['verdict']:>18}  <-- CURRENT")

    pos = [r for r in rows if r["verdict"] == "CONSISTENT POS"]
    print("\n" + "=" * 100)
    print(f"THE ACTUAL QUESTION: of {len(rows)} in-mandate rule tweaks, how many are positive AND")
    print(f"sign-consistent across halves?  ANSWER: {len(pos)}")
    for r in pos:
        print(f"   {r['label']}   edge {r['edge'] * 100:+.2f}%  (H1 {r['e1'] * 100:+.2f}%, "
              f"H2 {r['e2'] * 100:+.2f}%, n={r['n']:,})")
    if cur:
        print(f"\nCurrent rule ranks {ranked.index(cur) + 1} of {len(rows)} — "
              f"edge {cur['edge'] * 100:+.2f}%, {cur['verdict']}.")
    print("\nRemember 72 cells were searched. Treat any single winner as a candidate to RETEST,")
    print("not a result — and note the effective-episode counts above before believing either half.")
    print("=" * 100)


def per_setup(start, end):
    """Per-setup volatility-matched edge, and the fix for a bug in this
    script's own earlier runs.

    BUG, found 2026-09-12: run() and volmatch() both call
    `iter_signals(bars)` with no `spy_closes`, and iter_signals only emits
    "relative_strength" when that argument is supplied. So every result
    this script produced on 2026-09-11 covered FOUR setups, not five --
    the write-ups saying "all 5 TA setups pooled" were wrong. This
    function passes spy_closes, so relative_strength actually fires here.

    WHY PER-SETUP MATTERS: pooling five setups into one "signal"
    population hides the case where one setup carries a real edge and is
    diluted by four bad ones. It equally hides the reverse -- one setup
    dragging down four neutral ones.

    MULTIPLE COMPARISONS, stated before looking at the output: testing 5
    setups x 3 rules = 15 comparisons. At these sample sizes, one or two
    landing positive by chance alone is the EXPECTED result, not a
    finding. The split-half column is the guard -- a genuine setup edge
    should hold sign in both halves. Nothing here gets promoted on a
    headline number, per CLAUDE.md's standing promotion criteria."""
    series = _load_series(start, end)
    try:
        from backtest_ta import _spy_closes
        spy = _spy_closes(start, end)
        print(f"Loaded {len(series)} tickers; SPY closes for {len(spy)} sessions "
              f"(relative_strength ENABLED — unlike this script's 2026-09-11 runs)\n")
    except Exception as e:
        spy = None
        print(f"WARNING: could not load SPY closes ({e}) — relative_strength will NOT fire, "
              f"reproducing the original bug. Fix before trusting this output.\n")

    entries = []  # (date, vol, frozenset(setups), rec)
    for ticker, bars in series.items():
        if len(bars) < 25:
            continue
        fired = defaultdict(set)
        for i, _d, setup in iter_signals(bars, spy_closes=spy):
            fired[i].add(setup)
        for i, b in enumerate(bars):
            date, _o, _h, _l, c, v = b
            if not (PRICE_MIN <= c <= PRICE_MAX and v >= VOLUME_MIN):
                continue
            vol = _prior_vol(bars, i)
            if vol is None:
                continue
            rec = _first_touch(bars, i)
            if rec is not None:
                entries.append((date, vol, frozenset(fired.get(i, ())), rec))

    counts = defaultdict(int)
    for _d, _v, setups, _r in entries:
        for s in setups:
            counts[s] += 1
    print("Signal counts per setup (entries passing the liquidity filter):")
    for s, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {s:<20}{n:>7,}")
    if "relative_strength" not in counts:
        print("  relative_strength     0  <-- still not firing; check RS_WINDOW warmup vs window length")
    print()

    by_date = defaultdict(list)
    for e in entries:
        by_date[e[0]].append(e)
    cells = defaultdict(lambda: defaultdict(list))  # (date,decile) -> setup/"__ctl__" -> recs
    for date, es in by_date.items():
        vs = sorted(e[1] for e in es)
        cuts = [vs[int(len(vs) * q / 10)] for q in range(1, 10)]
        for date_, vol, setups, rec in es:
            d = sum(1 for c in cuts if vol > c)
            if setups:
                for s in setups:
                    cells[(date_, d)][s].append(rec)
            else:
                cells[(date_, d)]["__ctl__"].append(rec)

    def matched(setup, stop, target, ts, subset=None):
        src = subset if subset is not None else cells
        diffs = []
        for _k, cell in src.items():
            ctl = [r for r in (_outcome(rec, stop, target, ts) for rec in cell.get("__ctl__", []))
                   if r is not None]
            if not ctl:
                continue
            cm = sum(ctl) / len(ctl)
            for rec in cell.get(setup, []):
                r = _outcome(rec, stop, target, ts)
                if r is not None:
                    diffs.append(r - cm)
        if not diffs:
            return None, 0
        return sum(diffs) / len(diffs), len(diffs)

    dates = sorted(by_date)
    mid = dates[len(dates) // 2]
    h1 = {k: v for k, v in cells.items() if k[0] < mid}
    h2 = {k: v for k, v in cells.items() if k[0] >= mid}
    rules = [(STOP_PCT, TARGET_PCT, TIME_STOP_DAYS), (-0.08, None, 20), (None, None, 20)]

    # EFFECTIVE SAMPLE SIZE -- the check that caught this script lying to
    # itself on 2026-09-12. With daily entries and an N-day hold,
    # consecutive entries share N-1 of their N forward days, so they are
    # nowhere near independent: effective independent episodes is roughly
    # (distinct entry dates) / (holding period), NOT the trade count. On a
    # 62-session cache a 20-day hold leaves ~20 usable entry dates, i.e.
    # about ONE independent episode -- and a split-half of one episode is
    # not a robustness check, it is two halves of the same event. The raw
    # n= column below will still read in the thousands; ignore it in
    # favour of this.
    print("=" * 92)
    print("EFFECTIVE SAMPLE SIZE (read this BEFORE the tables — the n= column is misleading)")
    print("=" * 92)
    print(f"{'hold':<8}{'dates w/ resolvable entries':>29}{'in H1':>8}{'in H2':>8}{'~indep. episodes':>19}")
    print("-" * 92)
    for ts in sorted({r[2] for r in rules}):
        # count from ACTUAL resolvable entries, not the global calendar --
        # tickers have differing bar coverage, so a calendar approximation
        # prints "0 in H2" beside tables that clearly used H2 entries.
        got = {d for (d, _dec), cell in cells.items()
               for key, recs in cell.items() if key != "__ctl__"
               for rec in recs if _outcome(rec, None, None, ts) is not None}
        h1d = sorted(d for d in got if d < mid)
        h2d = sorted(d for d in got if d >= mid)
        eff = len(got) / ts if ts else float("nan")
        warn = "  <-- TOO FEW TO TEST" if eff < 3 else ""
        print(f"{ts:>3}d{'':<4}{len(got):>29}{len(h1d):>8}{len(h2d):>8}{eff:>19.1f}{warn}")
    print()

    for stop, target, ts in rules:
        s = "none" if stop is None else f"{stop * 100:+.0f}%"
        t = "none" if target is None else f"{target * 100:+.0f}%"
        cur = "   <-- CLAUDE.md's CURRENT rule" if (stop, target, ts) == (
            STOP_PCT, TARGET_PCT, TIME_STOP_DAYS) else ""
        print("=" * 92)
        print(f"RULE: stop {s}  target {t}  {ts}-day{cur}")
        print("=" * 92)
        print(f"{'setup':<22}{'matched edge':>14}{'n':>9}{'H1':>10}{'H2':>10}{'verdict':>20}")
        print("-" * 92)
        for setup in sorted(counts, key=lambda x: -counts[x]):
            edge, n = matched(setup, stop, target, ts)
            if edge is None or n < 30:
                print(f"{setup:<22}{'insufficient n':>14}{n:>9}")
                continue
            e1, _ = matched(setup, stop, target, ts, h1)
            e2, _ = matched(setup, stop, target, ts, h2)
            if e1 is None or e2 is None:
                v = "insufficient n"
            elif (e1 > 0) == (e2 > 0):
                v = "CONSISTENT POS" if e1 > 0 else "consistent neg"
            else:
                v = "flips — noise"
            f = lambda x: "   n/a" if x is None else f"{x * 100:>9.2f}%"
            print(f"{setup:<22}{edge * 100:>13.2f}%{n:>9,}{f(e1)}{f(e2)}{v:>20}")
        print()

    print("=" * 92)
    print("READING THIS: vcp_breakout is a strict SUBSET of breakout by construction, so those two")
    print("rows are not independent observations. 5 setups x 3 rules = 15 comparisons — one or two")
    print("positive by chance is expected, which is why the split-half columns, not the headline")
    print("edge, decide whether anything here is real. Nothing is promoted on this output alone;")
    print("CLAUDE.md's promotion criteria (backtest edge + forward agreement + user sign-off) stand.")
    print("=" * 92)


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("-")]
    start = a[0] if a else "2024-09-11"
    end = a[1] if len(a) > 1 else "2024-12-06"
    if "--realistic" in sys.argv:
        realistic(start, end)
    elif "--tweak" in sys.argv:
        tweak(start, end)
    elif "--per-setup" in sys.argv:
        per_setup(start, end)
    elif "--volmatch" in sys.argv:
        volmatch(start, end)
    else:
        run(start, end)
