"""
Tests exit rules across MARKET REGIMES, not one quarter.

WHY THIS EXISTS
---------------
`exit_rule_sweep.py --realistic` (2026-09-12) found that widening the stop
transforms the absolute numbers: CLAUDE.md's -4%/+8%/5d returned
-0.08%/trade with 39.1% of trades stopped out, while a volatility-scaled
2-sigma stop on a 10-day hold returned +1.23%/trade with only 8.1%
stopped. That is a big enough swing to change the strategy on.

But it was measured over 2024-09-11..2024-12-06 — ONE bull quarter,
including the November 2024 post-election melt-up. A wide stop is exactly
the kind of parameter that flatters a rising tape and then takes
outsized losses when the tape turns: you are deliberately choosing to sit
through drawdowns that a tight stop would have cut. Adopting it on
bull-quarter evidence would be the vcp_breakout mistake again (a 2-year
window that reversed when extended to 6).

So this fetches a multi-year sample spanning 2020-2026 — which includes
the 2022 bear market — and reports every rule BY CALENDAR YEAR and BY
SPY REGIME, so the bull/bear split is visible rather than averaged away.

THE SURVIVORSHIP TRADE-OFF, AND WHY IT IS ACCEPTABLE *HERE*
-----------------------------------------------------------
The universe is sampled from today's liquid tickers, so it carries the
classic survivorship bias: companies that delisted between 2020 and 2026
are absent. That genuinely inflates every absolute number here, and these
figures must never be quoted as "what the strategy returns".

It is nonetheless the right tool for THIS question, because the question
is COMPARATIVE: does the widened rule's advantage over the tight rule
survive a bear market? Both rules are measured on the identical universe,
so the bias inflates both roughly equally and largely cancels in the
difference. What does NOT cancel is regime, which is precisely what is
being measured.

Deliberately kept in a SEPARATE cache dir (data/reference/regime_cache/).
It must never be written into data/reference/backtest_cache/, which is
Massive-sourced and survivorship-FIXED — mixing a today's-tickers-only
Alpaca set into it would silently reintroduce the bias that fix removed.

Usage:
  python scripts/regime_test.py fetch 400      # sample 400 liquid names, 2020-2026
  python scripts/regime_test.py run
"""

import os
import sys
import json
import math
import time
import random
import datetime
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from alpaca_client import get_historical_bars  # noqa: E402

CACHE = Path("data/reference/regime_cache")
START, END = "2020-08-01", "2026-09-11"
PRICE_MIN, PRICE_MAX, VOLUME_MIN = 5, 500, 1_000_000
# Alpaca's free feed reports IEX-only volume. Measured against Massive's
# full tape on 2026-09-10 across this exact 401-ticker sample, IEX carries a
# median 5.1% of consolidated volume (p5 2.7%, p95 8.8%), so the project's
# 1M-share consolidated floor translates to ~50k IEX shares. Applying the
# raw 1M figure to IEX bars -- which the first run of this script did --
# silently screens for ~20M+ consolidated volume, i.e. mega-caps only, and
# gets STRICTER the further back you go because IEX market share was lower.
# That produced 32 signal entries in 2020 against 409 in 2026 and made the
# per-year comparison unreadable. Approximate by construction: the 2.7-8.8%
# spread means individual names sit either side of the intended line.
IEX_VOLUME_MIN = 50_000


def fetch(n=400, seed=11):
    """Sample liquid common stocks and pull 6 years of daily bars.

    Sampled RANDOMLY across the liquid set rather than taking the top N by
    volume — a mega-cap-only universe would be a different (and much
    easier) market than the one this project actually screens."""
    CACHE.mkdir(parents=True, exist_ok=True)
    src = Path("data/reference/backtest_cache/2026-09-10.json")
    if not src.exists():
        raise SystemExit(f"need {src} to pick a universe from")
    rows = json.loads(src.read_text())["results"]
    try:
        from massive_client import get_common_stock_tickers
        cs = get_common_stock_tickers()
    except Exception as e:
        print(f"warn: no common-stock list ({e}); ETFs may leak into the sample")
        cs = None
    liquid = [t for t, v in rows.items()
              if PRICE_MIN <= v[3] <= PRICE_MAX and v[4] >= VOLUME_MIN
              and t.isalpha() and (cs is None or t in cs)]
    random.Random(seed).shuffle(liquid)
    # SPY is not in the common-stock universe (it is an ETF) but relative_strength
    # cannot fire without it, so it is fetched explicitly rather than sampled.
    universe = sorted(set(liquid[:n]) | {"SPY"})
    print(f"{len(liquid)} liquid common stocks available; sampling {n} + SPY (seed={seed})")
    done = {p.stem for p in CACHE.glob("*.json")}
    todo = [t for t in universe if t not in done]
    print(f"{len(done)} already cached, {len(todo)} to fetch\n")
    for i, t in enumerate(todo, 1):
        try:
            bars = get_historical_bars(t, f"{START}T00:00:00Z", f"{END}T23:59:59Z", timeframe="1Day")
            (CACHE / f"{t}.json").write_text(json.dumps(
                [(b["t"][:10], b["o"], b["h"], b["l"], b["c"], b["v"]) for b in bars]))
            if i % 50 == 0:
                print(f"  {i}/{len(todo)} ... {t} ({len(bars)} bars)")
        except Exception as e:
            print(f"  {t}: {str(e)[:60]}")
        time.sleep(0.32)
    print(f"done: {len(list(CACHE.glob('*.json')))} tickers cached")


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


def _vol(bars, i, w=20):
    if i < w:
        return None
    rs = []
    for k in range(i - w + 1, i + 1):
        p, c = bars[k - 1][4], bars[k][4]
        if p > 0:
            rs.append((c - p) / p)
    if len(rs) < w // 2:
        return None
    m = sum(rs) / len(rs)
    return (sum((r - m) ** 2 for r in rs) / len(rs)) ** 0.5


def _outcome(bars, i, stop, tgt, ts):
    if i + 1 >= len(bars):
        return None
    e = bars[i + 1][1]
    if e <= 0:
        return None
    s, g = e * (1 + stop), e * (1 + tgt)
    for k in range(1, ts + 1):
        if i + k >= len(bars):
            return None
        _, _o, h, l, c, _v = bars[i + k]
        if l <= s:
            return stop
        if h >= g:
            return tgt
        if k == ts:
            return (c - e) / e
    return None


def run():
    series = _load()
    if not series:
        raise SystemExit("no cached data — run `fetch` first")
    print(f"loaded {len(series)} tickers\n")

    from backtest_ta import iter_signals
    spy = series.get("SPY")
    spy_closes = {b[0]: b[4] for b in spy} if spy else None

    # entries: (date, vol, is_signal, bars, i)
    entries = []
    for t, bars in series.items():
        if len(bars) < 60:
            continue
        sig = {i for i, _d, _s in iter_signals(bars, spy_closes=spy_closes,
                                               vol_min=IEX_VOLUME_MIN)}
        for i, b in enumerate(bars):
            date, _o, _h, _l, c, v = b
            if not (PRICE_MIN <= c <= PRICE_MAX and v >= IEX_VOLUME_MIN):
                continue
            vl = _vol(bars, i)
            if vl is None:
                continue
            entries.append((date, vl, i in sig, bars, i))
    yrs = sorted({e[0][:4] for e in entries})
    print(f"{len(entries):,} entries ({sum(1 for e in entries if e[2]):,} signal) "
          f"spanning {yrs[0]}..{yrs[-1]}\n")

    configs = [
        ("CURRENT -4%/+8%/5d", lambda v: (-0.04, 0.08), 5),
        ("flat   -8%/+16%/10d", lambda v: (-0.08, 0.16), 10),
        ("vol-scaled 2.0sig 2:1 10d", lambda v: (-2.0 * v * math.sqrt(10), 4.0 * v * math.sqrt(10)), 10),
    ]

    summary = []
    for label, fn, ts in configs:
        by_year = defaultdict(lambda: {"sig": [], "ctl": []})
        for date, vl, is_sig, bars, i in entries:
            r = _outcome(bars, i, *fn(vl), ts)
            if r is None:
                continue
            by_year[date[:4]]["sig" if is_sig else "ctl"].append(r)
        print("=" * 78)
        print(f"{label}")
        print("=" * 78)
        print(f"{'year':<8}{'sig n':>8}{'sig avg':>10}{'sig win%':>10}{'ctl avg':>10}{'EDGE':>9}")
        print("-" * 78)
        for y in sorted(by_year):
            s, c = by_year[y]["sig"], by_year[y]["ctl"]
            if len(s) < 30 or not c:
                continue
            sa, ca = sum(s) / len(s), sum(c) / len(c)
            print(f"{y:<8}{len(s):>8,}{sa*100:>9.2f}%{sum(1 for x in s if x>0)/len(s)*100:>9.1f}%"
                  f"{ca*100:>9.2f}%{(sa-ca)*100:>8.2f}%")
        alls = [x for y in by_year.values() for x in y["sig"]]
        allc = [x for y in by_year.values() for x in y["ctl"]]
        if alls and allc:
            sa, ca = sum(alls) / len(alls), sum(allc) / len(allc)
            print("-" * 78)
            print(f"{'ALL':<8}{len(alls):>8,}{sa*100:>9.2f}%"
                  f"{sum(1 for x in alls if x>0)/len(alls)*100:>9.1f}%{ca*100:>9.2f}%{(sa-ca)*100:>8.2f}%")
            b = by_year.get("2022", {"sig": [], "ctl": []})
            bs, bc = b["sig"], b["ctl"]
            srt = sorted(alls)
            summary.append({
                "label": label,
                "edge_all": sa - ca,
                "bear_sig": (sum(bs) / len(bs)) if bs else None,
                "bear_edge": ((sum(bs) / len(bs)) - (sum(bc) / len(bc))) if bs and bc else None,
                "p1": srt[max(0, int(0.01 * len(srt)) - 1)],
                "big_loss": sum(1 for x in alls if x <= -0.05) / len(alls),
                "sign_flips": sum(1 for y in sorted(by_year)
                                  if by_year[y]["sig"] and by_year[y]["ctl"]
                                  and (sum(by_year[y]["sig"]) / len(by_year[y]["sig"])
                                       - sum(by_year[y]["ctl"]) / len(by_year[y]["ctl"])) > 0),
                "years": sum(1 for y in by_year if by_year[y]["sig"] and by_year[y]["ctl"]),
            })
        print()

    # The risk side. A wider stop raises the average in a rising tape by
    # sitting through drawdowns a tight stop would have cut -- so the average
    # alone cannot be the basis for choosing a rule. These columns price what
    # is being bought with that average: how deep the bad trades run, how
    # often, and what happens in the one falling year in the sample.
    print("=" * 96)
    print("RISK SIDE — what the higher average costs")
    print("=" * 96)
    print(f"{'rule':<28}{'edge ALL':>10}{'2022 sig':>10}{'2022 edge':>11}"
          f"{'worst 1%':>10}{'loss>5%':>9}{'yrs edge+':>11}")
    print("-" * 96)
    for r in summary:
        print(f"{r['label']:<28}{r['edge_all']*100:>9.2f}%"
              f"{(r['bear_sig'] or 0)*100:>9.2f}%{(r['bear_edge'] or 0)*100:>10.2f}%"
              f"{r['p1']*100:>9.2f}%{r['big_loss']*100:>8.1f}%"
              f"{r['sign_flips']:>6}/{r['years']}")
    print()

    print("=" * 78)
    print("READ BY YEAR, NOT BY THE 'ALL' ROW. The question is whether a rule's advantage")
    print("survives a falling tape — 2022 is the bear year in this sample. A rule that only")
    print("wins in 2021/2023/2024 has found beta and will hand it back.")
    print("Absolute levels are inflated by survivorship (today's tickers applied backwards);")
    print("the COMPARISON between rules on the identical universe is what this is for.")
    print("=" * 78)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "fetch":
        fetch(int(sys.argv[2]) if len(sys.argv) > 2 else 400)
    else:
        run()
