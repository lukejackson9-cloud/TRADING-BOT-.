"""
Is there ANY predictive information in this project's features, before any
trading rule is imposed on them?

WHY THIS EXISTS, AND WHY IT IS NOT VARIANT #27
-----------------------------------------------
Every mechanical test in CLAUDE.md measures a BINARY RULE: breakout fires
or it doesn't, RSI crosses 30 or it doesn't, 2+ setups agree or they
don't. 26+ such variants, six confluence combinations and 180 exit-rule
cells have all come back flat or negative.

But a threshold destroys almost all the information in a continuous
variable. "RSI crossed up through 30" collapses the entire RSI
distribution into one bit. If a feature carried a weak, real signal, a
binary rule built on it could easily read as noise while the feature
itself did not. No test in this project has ever looked underneath the
rules at the features themselves.

This does. For each continuous feature it computes, per trading day, a
CROSS-SECTIONAL ranking of every qualifying stock, then measures:

  * Rank IC -- the Spearman correlation between a stock's feature rank
    today and its forward return. This is the standard quant diagnostic
    for "does this variable contain information", and this project has
    never run it.
  * Decile spread -- mean forward return of the top decile minus the
    bottom decile.

Both are computed WITHIN a single trading day, so market direction is
differenced out by construction: every stock in the comparison
experienced the same tape. That is a cleaner beta control than anything
used so far, because it needs no matched control group at all.

Forward return here is a RAW HOLD (next open to close h days later). No
stop, no target. That is deliberate: exit rules are already known to
dominate the numbers (see CLAUDE.md), and the question here is whether
information exists at all, not how to harvest it. An exit rule can only
subtract from information that is present; it cannot create it.

HOW TO READ THE RESULT
----------------------
A real effect must be SIGN-CONSISTENT ACROSS YEARS. 8 features x 2
horizons = 16 tests, so one or two good-looking cells are expected by
chance; the script prints how many of the 7 years each feature got right
and flags anything under 6/7 as noise. Typical published equity
anomalies run rank IC of roughly 0.01-0.03 -- small but persistent. An IC
that wanders around zero and flips sign every year is nothing.

If nothing here is sign-consistent, the mechanical daily-bar track is
closed properly: not "these 26 rules failed" but "the underlying
variables carry no usable cross-sectional information in this universe",
which is a much stronger and more final statement.

Uses the cache scripts/regime_test.py already fetched. No new API calls.

Usage:
  python scripts/feature_ic.py
"""

import sys
import json
import math
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

CACHE = Path("data/reference/regime_cache")
PRICE_MIN, PRICE_MAX = 5, 500
IEX_VOLUME_MIN = 50_000          # see regime_test.py for why not 1,000,000
HORIZONS = (5, 10)
MIN_NAMES_PER_DAY = 40           # need enough cross-section to decile


def _load():
    out = {}
    for p in CACHE.glob("*.json"):
        try:
            b = [tuple(x) for x in json.loads(p.read_text())]
            if len(b) > 300:
                out[p.stem] = b
        except Exception:
            pass
    return out


def _rsi(bars, period=14):
    out = [None] * len(bars)
    if len(bars) <= period:
        return out
    gains = losses = 0.0
    for i in range(1, period + 1):
        d = bars[i][4] - bars[i - 1][4]
        gains += max(d, 0.0)
        losses += max(-d, 0.0)
    ag, al = gains / period, losses / period
    for i in range(period, len(bars)):
        if i > period:
            d = bars[i][4] - bars[i - 1][4]
            ag = (ag * (period - 1) + max(d, 0.0)) / period
            al = (al * (period - 1) + max(-d, 0.0)) / period
        out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def _features(bars, spy_closes):
    """Yield (i, date, {feature: value}) for every bar with a full history."""
    rsi = _rsi(bars)
    ema9 = ema21 = None
    for i, (date, _o, _h, _l, c, v) in enumerate(bars):
        k9, k21 = 2 / 10, 2 / 22
        ema9 = c if ema9 is None else c * k9 + ema9 * (1 - k9)
        ema21 = c if ema21 is None else c * k21 + ema21 * (1 - k21)
        if i < 61 or c <= 0:
            continue
        if not (PRICE_MIN <= c <= PRICE_MAX) or v < IEX_VOLUME_MIN:
            continue
        w20 = bars[i - 20:i]
        hi20 = max(b[2] for b in w20)
        av20 = sum(b[5] for b in w20) / 20
        c5, c20, c60 = bars[i - 5][4], bars[i - 20][4], bars[i - 60][4]
        if min(c5, c20, c60, hi20, av20) <= 0:
            continue
        rets = []
        for k in range(i - 19, i + 1):
            p = bars[k - 1][4]
            if p > 0:
                rets.append((bars[k][4] - p) / p)
        if len(rets) < 10:
            continue
        m = sum(rets) / len(rets)
        sd = (sum((r - m) ** 2 for r in rets) / len(rets)) ** 0.5

        f = {
            "dist_20d_high": (c - hi20) / hi20,   # breakout's raw material
            "vol_ratio": v / av20,                # breakout's volume trigger
            "rsi14": rsi[i] if rsi[i] is not None else None,
            "ema_spread": (ema9 - ema21) / c,     # ema_cross's raw material
            "mom_60d": (c - c60) / c60,           # classic 3-month momentum
            "reversal_5d": -(c - c5) / c5,        # short-term reversal (sign flipped
                                                  # so positive = expected winner)
            "volatility_20d": sd,
            "rel_str_20d": None,
        }
        if spy_closes:
            s_now, s_then = spy_closes.get(date), spy_closes.get(bars[i - 20][0])
            if s_now and s_then and s_then > 0:
                f["rel_str_20d"] = (c - c20) / c20 - (s_now - s_then) / s_then
        if f["rsi14"] is None:
            continue
        yield i, date, f


def _fwd(bars, i, h):
    """Raw hold: next session's open to the close h sessions later."""
    if i + 1 + h >= len(bars):
        return None
    e = bars[i + 1][1]
    if e <= 0:
        return None
    return (bars[i + 1 + h][4] - e) / e


def _spearman(pairs):
    """Rank correlation. pairs = [(x, y), ...]"""
    n = len(pairs)
    if n < 10:
        return None

    def ranks(vals):
        order = sorted(range(n), key=lambda k: vals[k])
        r = [0.0] * n
        k = 0
        while k < n:
            j = k
            while j + 1 < n and vals[order[j + 1]] == vals[order[k]]:
                j += 1
            avg = (k + j) / 2 + 1
            for t in range(k, j + 1):
                r[order[t]] = avg
            k = j + 1
        return r

    rx, ry = ranks([p[0] for p in pairs]), ranks([p[1] for p in pairs])
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((rx[k] - mx) * (ry[k] - my) for k in range(n))
    dx = math.sqrt(sum((rx[k] - mx) ** 2 for k in range(n)))
    dy = math.sqrt(sum((ry[k] - my) ** 2 for k in range(n)))
    return None if dx == 0 or dy == 0 else num / (dx * dy)


def run():
    series = _load()
    if not series:
        raise SystemExit("no cached data — run `python scripts/regime_test.py fetch 400` first")
    spy = series.get("SPY")
    spy_closes = {b[0]: b[4] for b in spy} if spy else None
    print(f"loaded {len(series)} tickers"
          f"{'' if spy_closes else '  (no SPY — rel_str_20d will be skipped)'}\n")

    # by_date[date] = list of (features, {h: fwd_return})
    by_date = defaultdict(list)
    for t, bars in series.items():
        if t == "SPY":
            continue
        for i, date, f in _features(bars, spy_closes):
            fw = {h: _fwd(bars, i, h) for h in HORIZONS}
            if any(v is not None for v in fw.values()):
                by_date[date].append((f, fw))

    usable = {d: rows for d, rows in by_date.items() if len(rows) >= MIN_NAMES_PER_DAY}
    print(f"{sum(len(v) for v in usable.values()):,} stock-days across "
          f"{len(usable):,} trading days with >={MIN_NAMES_PER_DAY} names\n")

    feats = ["dist_20d_high", "vol_ratio", "rsi14", "ema_spread",
             "mom_60d", "reversal_5d", "volatility_20d", "rel_str_20d"]

    for h in HORIZONS:
        # ic[feature][year] = [daily ICs];  dec[feature][year] = [daily top-bottom spreads]
        ic = defaultdict(lambda: defaultdict(list))
        dec = defaultdict(lambda: defaultdict(list))
        for date, rows in usable.items():
            yr = date[:4]
            for fname in feats:
                pairs = [(f[fname], fw[h]) for f, fw in rows
                         if f.get(fname) is not None and fw[h] is not None]
                if len(pairs) < MIN_NAMES_PER_DAY:
                    continue
                r = _spearman(pairs)
                if r is not None:
                    ic[fname][yr].append(r)
                pairs.sort(key=lambda p: p[0])
                k = max(1, len(pairs) // 10)
                top = sum(p[1] for p in pairs[-k:]) / k
                bot = sum(p[1] for p in pairs[:k]) / k
                dec[fname][yr].append(top - bot)

        print("=" * 92)
        print(f"FORWARD {h}-DAY RAW HOLD  —  cross-sectional, within-day (market direction differenced out)")
        print("=" * 92)
        print(f"{'feature':<18}{'rank IC':>10}{'t-stat':>9}{'D10-D1':>10}"
              f"{'yrs same sign':>15}{'verdict':>22}")
        print("-" * 92)
        rows_out = []
        for fname in feats:
            allic = [x for y in ic[fname].values() for x in y]
            alldec = [x for y in dec[fname].values() for x in y]
            if len(allic) < 200:
                continue
            m = sum(allic) / len(allic)
            sd = (sum((x - m) ** 2 for x in allic) / len(allic)) ** 0.5
            t = m / (sd / math.sqrt(len(allic))) if sd > 0 else 0.0
            dm = sum(alldec) / len(alldec)
            yrs = sorted(ic[fname])
            yr_means = [sum(ic[fname][y]) / len(ic[fname][y]) for y in yrs if len(ic[fname][y]) > 20]
            same = sum(1 for x in yr_means if (x > 0) == (m > 0))
            consistent = len(yr_means) > 0 and same >= max(6, len(yr_means) - 1)
            verdict = ("SIGN-CONSISTENT" if consistent else "flips — noise")
            if consistent and abs(m) < 0.005:
                verdict = "consistent but tiny"
            rows_out.append((fname, m, t, dm, same, len(yr_means), verdict,
                             {y: sum(ic[fname][y]) / len(ic[fname][y]) for y in yrs
                              if len(ic[fname][y]) > 20}))
            print(f"{fname:<18}{m:>10.4f}{t:>9.1f}{dm*100:>9.2f}%"
                  f"{same:>11}/{len(yr_means):<3}{verdict:>22}")
        print()
        strong = [r for r in rows_out if r[6] == "SIGN-CONSISTENT"]
        if strong:
            print("  Per-year rank IC for the sign-consistent features "
                  "(a real effect should not depend on one year):")
            for r in sorted(strong, key=lambda r: -abs(r[1])):
                cells = "  ".join(f"{y}:{v:+.3f}" for y, v in sorted(r[7].items()))
                print(f"    {r[0]:<18}{cells}")
        else:
            print("  No feature is sign-consistent across years at this horizon.")
        print()

    print("=" * 92)
    print("HOW TO READ THIS")
    print("=" * 92)
    print("Rank IC is the correlation between a stock's feature rank today and its forward")
    print("return. Published equity anomalies typically run 0.01-0.03 — small, persistent.")
    print("The t-stat is inflated here: daily ICs overlap (a 5-day forward window shares 4 of")
    print("its 5 days with the next day's), so treat it as a rough screen, not a p-value. The")
    print("load-bearing column is 'yrs same sign'. Anything that flips is noise regardless of")
    print("how large the average looks.")
    print()
    print("A feature reading flat here means the binary rules built on it were never the")
    print("problem — there is no information underneath them to find. A feature that IS")
    print("consistent means the threshold was throwing the signal away, and is worth a")
    print("continuous, rank-based version. Either answer is more final than another variant.")
    print()
    print("Caveats: survivorship-biased universe (today's liquid names applied backwards) —")
    print("but cross-sectional, within-day ranking is largely immune to that, since every")
    print("stock in a comparison is drawn from the same biased pool on the same day. 8")
    print("features x 2 horizons = 16 tests, so the sign-consistency requirement is doing the")
    print("multiple-comparisons work. Raw holds only; no costs. IEX volume floor, see")
    print("regime_test.py.")
    print("=" * 92)


def reversal():
    """Follow-up on the one feature that came back sign-consistent.

    An IC table is not a strategy. Three things have to be true before
    5-day reversal means anything to THIS project, and each is checked
    here rather than assumed:

    1. LONG-ONLY. D10-D1 is a long-short spread and CLAUDE.md's Hard Risk
       Rules forbid shorting (T212's equity API is long-only anyway). Only
       the long leg's excess over the same day's average name is
       available, and it is typically much smaller than the spread.
    2. NET OF COSTS. A 5-day holding period is ~50 round trips a year.
       Reversal is the classic anomaly that exists on paper and dies on
       the spread, so the breakeven cost is the whole question.
    3. NOT CONCENTRATED IN JUNK. Reversal is strongest in the smallest,
       most volatile, widest-spread names -- precisely where the measured
       return is least capturable. If the effect only lives in the top
       volatility tercile it is not tradeable, it is a spread illusion.

    SURVIVORSHIP CUTS DIRECTLY INTO THIS ONE. The universe is today's
    liquid tickers applied backwards, so a stock that fell hard and then
    delisted is absent from the sample entirely. Big 5-day losers that
    never came back are exactly the observations missing, and they are
    exactly the observations that would hurt a buy-the-losers rule. Every
    number below is therefore biased in this feature's FAVOUR, by an
    amount this data cannot measure. That is a reason for caution
    proportional to how good the numbers look."""
    series = _load()
    if not series:
        raise SystemExit("no cached data — run `python scripts/regime_test.py fetch 400` first")
    spy = series.get("SPY")
    spy_closes = {b[0]: b[4] for b in spy} if spy else None

    by_date = defaultdict(list)
    for t, bars in series.items():
        if t == "SPY":
            continue
        for i, date, f in _features(bars, spy_closes):
            r = _fwd(bars, i, 5)
            if r is not None:
                by_date[date].append((f["reversal_5d"], r, f["volatility_20d"], bars[i][4]))
    usable = {d: r for d, r in by_date.items() if len(r) >= MIN_NAMES_PER_DAY}
    print(f"{sum(len(v) for v in usable.values()):,} stock-days, {len(usable):,} days\n")

    # 1 + 2. Long-only top-decile excess over the same day's average name, by year,
    # swept against round-trip cost.
    per_year = defaultdict(list)
    for date, rows in usable.items():
        rows = sorted(rows, key=lambda r: r[0])
        k = max(1, len(rows) // 10)
        top = sum(r[1] for r in rows[-k:]) / k
        allm = sum(r[1] for r in rows) / len(rows)
        per_year[date[:4]].append((top, allm))

    print("=" * 84)
    print("1+2. LONG-ONLY: buy the top reversal decile (biggest 5-day losers), hold 5 days")
    print("=" * 84)
    print(f"{'year':<8}{'days':>7}{'top decile':>13}{'avg name':>11}{'excess':>10}{'excess net 20bps':>19}")
    print("-" * 84)
    for y in sorted(per_year):
        v = per_year[y]
        t = sum(x[0] for x in v) / len(v)
        a = sum(x[1] for x in v) / len(v)
        print(f"{y:<8}{len(v):>7}{t*100:>12.2f}%{a*100:>10.2f}%{(t-a)*100:>9.2f}%{(t-a-0.0020)*100:>18.2f}%")
    allv = [x for v in per_year.values() for x in v]
    t = sum(x[0] for x in allv) / len(allv)
    a = sum(x[1] for x in allv) / len(allv)
    pos = sum(1 for y in per_year
              if sum(x[0] - x[1] for x in per_year[y]) > 0)
    print("-" * 84)
    print(f"{'ALL':<8}{len(allv):>7}{t*100:>12.2f}%{a*100:>10.2f}%{(t-a)*100:>9.2f}%{(t-a-0.0020)*100:>18.2f}%")
    print(f"\nyears with positive excess: {pos}/{len(per_year)}")
    print(f"breakeven round-trip cost: {(t-a)*10000:.0f} bps  "
          f"(a retail market order in a liquid US name is ~5-20 bps; a $5 stock more)")
    print()

    # 3. Is it only in the junk?
    print("=" * 84)
    print("3. WHERE THE EFFECT LIVES — if it is only in the most volatile/cheapest names,")
    print("   the measured return is spread, not profit")
    print("=" * 84)
    for label, keyfn in (("volatility_20d", lambda r: r[2]), ("price", lambda r: r[3])):
        buckets = defaultdict(list)
        for date, rows in usable.items():
            srt = sorted(rows, key=keyfn)
            n = len(srt)
            for bi, seg in enumerate((srt[:n // 3], srt[n // 3:2 * n // 3], srt[2 * n // 3:])):
                if len(seg) < 12:
                    continue
                seg = sorted(seg, key=lambda r: r[0])
                k = max(1, len(seg) // 5)          # top quintile within the tercile
                top = sum(r[1] for r in seg[-k:]) / k
                allm = sum(r[1] for r in seg) / len(seg)
                buckets[bi].append(top - allm)
        print(f"\n  by {label} tercile (excess of the high-reversal quintile within each):")
        for bi, name in enumerate(("low", "mid", "high")):
            v = buckets.get(bi, [])
            if v:
                print(f"    {name:<6}{sum(v)/len(v)*100:>8.2f}%   (n={len(v):,} days)")
    print()
    print("=" * 84)
    print("Read the long-only excess against the breakeven-cost line, not against zero, and")
    print("read both against the survivorship warning in this function's docstring: the")
    print("stocks missing from this universe are the ones that would hurt this rule most.")
    print("=" * 84)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reversal":
        reversal()
    else:
        run()
