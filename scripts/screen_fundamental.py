"""
A COVERAGE screen for the 3-12 month council — replaces the mover screen.

THE CLOSED LOOP THIS BREAKS
----------------------------
`skills/screen.md` ranks the whole market by |% change| and hands research
the top movers. So by construction every name the pipeline has ever seen had
ALREADY made its move -- and "stale / already priced in / sell the news" is
the single most common reason it rejects a name (57 of 147 notes, 39%). The
pipeline found movers and then rejected them for being movers. That loop, not
the market, is the best explanation for weeks with zero candidates.

It is worse than merely circular at the new horizon. A |% change| ranking
selects for recent price strength, and `feature_ic.py` found 5-day REVERSAL
is the one real effect in this data -- so a mover screen systematically feeds
the council the wrong side of the only measurable effect present.

WHAT REPLACES IT: COVERAGE, NOT DISCOVERY
------------------------------------------
A fundamental investor does not re-screen the market every morning. They
maintain coverage of an investable universe and act when price and facts
line up. So this keeps a persistent universe and works through it, building
a fundamental card per name and refreshing stale ones -- the shortlist is
drawn from what is COVERED, not from what moved yesterday.

That change alone fixes the loop permanently: a name reaches the council
because it is in the investable universe and its filings say something
interesting, never because it jumped 12% on Tuesday.

THE RATE LIMIT IS THE BINDING CONSTRAINT, AND IT SHAPES THE DESIGN
-------------------------------------------------------------------
Massive's fundamentals are 5 requests/minute. ~24 names/hour, so scoring
5,000 stocks on fundamentals is impossible and always will be. Hence the
funnel: a cheap whole-market liquidity filter (ONE grouped-daily call covers
every ticker at once), then a coverage queue that spends the fundamental
budget deliberately -- never-covered names first, then the stalest.
Coverage compounds: a few dozen names a day becomes real breadth in weeks,
and unlike a mover list it does not evaporate overnight.

THIS SCREEN DOES NOT PREDICT RETURNS, AND MUST NOT BE BUILT TO
---------------------------------------------------------------
Its job is to narrow the market to names worth analyst attention. It needs no
edge; it needs to not systematically select bad candidates. A mechanical
fundamental score claiming to forecast returns would be variant 27 in a new
costume -- exactly what CLAUDE.md's RESEARCH PROGRAMME CLOSED section
forbids. The `shortlist` ordering below is an ATTENTION ORDER, and its output
says so on every run.

Usage:
  python scripts/screen_fundamental.py universe          # refresh investable universe
  python scripts/screen_fundamental.py cover 20          # spend today's budget (~5 min)
  python scripts/screen_fundamental.py shortlist 10      # today's council shortlist
  python scripts/screen_fundamental.py status
"""

import os
import sys
import json
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

UNIVERSE = Path("data/reference/fundamental_universe.json")
CARDS = Path("data/reference/fundamentals_cache")
PRICE_MIN, PRICE_MAX, VOLUME_MIN = 5, 500, 1_000_000
STALE_DAYS = 45          # refresh a card roughly once a reporting cycle


def _load_universe():
    return json.loads(UNIVERSE.read_text()) if UNIVERSE.exists() else {}


def universe(date=None):
    """Investable universe from ONE whole-market grouped-daily call.

    Liquidity and price only. Deliberately NOT ranked by anything here --
    ranking the universe by a price move is the exact mistake being undone.
    """
    from massive_client import get_grouped_daily, get_common_stock_tickers
    if date is None:
        d = datetime.date.today()
        while d.weekday() >= 5:
            d -= datetime.timedelta(days=1)
        date = (d - datetime.timedelta(days=1)).isoformat()   # EOD is a day behind
    print(f"whole-market grouped daily for {date} (1 call)...")
    raw = get_grouped_daily(date)
    rows = raw.get("results") or []
    if not rows:
        raise SystemExit(f"no results for {date} — try the previous trading day "
                         f"(Massive is EOD and one session behind; an empty result "
                         f"is NOT 'no liquid stocks today')")
    try:
        common = set(get_common_stock_tickers())
    except Exception as e:
        print(f"warn: common-stock list unavailable ({e}); ETFs may leak in")
        common = None
    keep = {}
    for r in rows:
        t, c, v = r.get("T"), r.get("c"), r.get("v")
        if not t or c is None or v is None:
            continue
        if not (PRICE_MIN <= c <= PRICE_MAX and v >= VOLUME_MIN):
            continue
        if common is not None and t not in common:
            continue
        if not t.isalpha():
            continue
        keep[t] = {"price": c, "volume": v, "as_of": date}
    UNIVERSE.parent.mkdir(parents=True, exist_ok=True)
    UNIVERSE.write_text(json.dumps({"built": date, "tickers": keep}, indent=1))
    print(f"investable universe: {len(keep)} liquid common stocks "
          f"(${PRICE_MIN}-${PRICE_MAX}, >{VOLUME_MIN:,} shares)")
    return keep


def _card_age(t):
    f = CARDS / f"{t}.json"
    if not f.exists():
        return None
    try:
        d = json.loads(f.read_text())
        return (datetime.date.today() - datetime.date.fromisoformat(d["fetched"])).days
    except Exception:
        return None


def queue(n=20):
    """Which names today's fundamental budget should be spent on.

    Never-covered first, then the stalest. Deliberately NOT 'most
    interesting' -- choosing what to cover based on a price signal would
    smuggle the mover screen back in through the queue."""
    u = _load_universe().get("tickers", {})
    if not u:
        raise SystemExit("no universe — run `universe` first")
    never, stale = [], []
    for t in sorted(u):
        age = _card_age(t)
        if age is None:
            never.append(t)
        elif age >= STALE_DAYS:
            stale.append((age, t))
    stale.sort(reverse=True)
    picked = never[:n] + [t for _, t in stale[:max(0, n - len(never))]]
    return picked[:n], len(never), len(stale)


def cover(n=20):
    """Pull fundamentals for the next n queued names. ~13s each."""
    from fundamentals import fetch
    picked, n_never, n_stale = queue(n)
    if not picked:
        print("coverage is current — nothing uncovered or stale.")
        return
    print(f"{n_never} never covered, {n_stale} stale. Covering {len(picked)} "
          f"(~{len(picked) * 13 // 60}m{len(picked) * 13 % 60}s at 5 req/min)\n")
    ok = fail = 0
    for i, t in enumerate(picked, 1):
        try:
            res = fetch(t)
            ok += 1
            print(f"  [{i}/{len(picked)}] {t:<6} {len(res)} period(s)")
        except Exception as e:
            fail += 1
            print(f"  [{i}/{len(picked)}] {t:<6} FAILED: {str(e)[:70]}")
    print(f"\ncovered {ok}, failed {fail}. "
          f"A 429 here means the pacing is wrong, NOT that a company files nothing.")


def shortlist(n=10):
    """Today's council shortlist, drawn from COVERED names.

    The ordering is an ATTENTION ORDER, not a return forecast. It puts
    profitable, cash-generative, non-extremely-valued businesses in front of
    the council first, because those are where a 3-12 month thesis is most
    likely to be analysable -- not because this ordering is believed to
    predict anything. Names it ranks low are not rejected; they are simply
    further down the queue for analyst time.
    """
    from fundamentals import metrics
    u = _load_universe().get("tickers", {})
    covered = [t for t in sorted(u) if (CARDS / f"{t}.json").exists()]
    if not covered:
        raise SystemExit("nothing covered yet — run `cover` first")
    rows = []
    for t in covered:
        try:
            m = metrics(t)
        except Exception:
            continue
        if not m:
            continue
        h, q, v = m["health"], m["quality"], m["valuation"]
        # transparent, non-predictive attention filters
        flags = []
        if h["profitable"] is False:
            flags.append("unprofitable")
        if h["cash_flow_positive"] is False:
            flags.append("cash-burn")
        # explicit None checks, not `or` defaults: a current ratio of exactly
        # 0 is falsy and would be replaced by 99, so the most distressed case
        # would go unflagged. Missing data is flagged as missing, not as fine.
        cr = h["current_ratio"]
        if cr is None:
            flags.append("liquidity?")
        elif cr < 1:
            flags.append("current<1")
        ps = v["price_to_sales"]
        if ps is not None and ps > 20:
            flags.append("P/S>20")
        if h.get("negative_equity"):
            flags.append("neg-equity")
        # Valuation rests on a share count that is wrong for ~30% of names.
        # Where it could not be corroborated, say so on the line rather than
        # letting an uncorroborated P/S or earnings yield read like a fact.
        # ROE above ~200% is the denominator collapsing, not quality: UNIT
        # showed 666.9% and HRB 624.4% on near-zero book equity. The cut sits
        # at 200% deliberately — AAPL's 119.9% is genuine (heavy buybacks
        # shrink book equity at a real business), so a lower threshold would
        # flag the very companies the quality role should be looking at.
        roe = q.get("return_on_equity")
        if roe is not None and roe > 2.0:
            flags.append("tiny-equity")
        basis = m.get("share_count_basis", "")
        if basis.startswith("UNVERIFIABLE"):
            flags.append("shares?")
        elif "uncorroborated" in basis or "implausible" in basis:
            flags.append("shares~")
        # A name with no reported figures triggers no flags, so without this it
        # would rank ABOVE names with real data and one blemish — absence of
        # information reading as absence of problems, which is the same trap
        # fundamentals.py refuses to fall into by printing n/a rather than 0.
        key = ("earnings_yield", "price_to_sales", "return_on_equity", "current_ratio")
        missing = sum(1 for k in key
                      if (v.get(k) if k in v else q.get(k) if k in q else h.get(k)) is None)
        if missing >= 3:
            flags.append(f"no-data({missing}/{len(key)})")
        ey = v["earnings_yield"]
        # sort: fewest flags, then most data, then highest earnings yield
        rows.append((len(flags), missing, -(ey if ey is not None else -9), t, m, flags))
    rows.sort()
    print(f"# Council shortlist — {len(covered)} names covered, showing {min(n, len(rows))}")
    print("# ATTENTION ORDER, NOT a return forecast. Low rank is not a rejection.")
    print("# flags: shares? = share count unverifiable, cap metrics suppressed;")
    print("#        shares~ = share count from a single uncorroborated source.")
    print(f"# Universe: liquid common stocks, coverage-based — NOT today's movers.")
    print(f"{'ticker':<8}{'earn yld':>10}{'P/S':>8}{'ROE':>8}{'rev YoY':>10}  flags")
    print("-" * 68)
    out = []
    for _, _, _, t, m, flags in rows[:n]:
        v, q = m["valuation"], m["quality"]
        f = lambda x, p=1: "n/a" if x is None else f"{x * 100:.{p}f}%"
        ps = "n/a" if v["price_to_sales"] is None else f"{v['price_to_sales']:.1f}"
        print(f"{t:<8}{f(v['earnings_yield']):>10}{ps:>8}"
              f"{f(q['return_on_equity']):>8}{f(q['revenue_growth_yoy_q']):>10}"
              f"  {','.join(flags) if flags else '-'}")
        out.append(t)
    print(f"\nRun the council on these: python scripts/fundamentals.py cards {' '.join(out[:5])}")
    return out


def status():
    u = _load_universe()
    tick = u.get("tickers", {})
    covered = [t for t in tick if (CARDS / f"{t}.json").exists()]

    # An 11% slice of "covered" carries NO financials, and they are not random
    # failures: AEG, AEM, AQN, AZN, BCE, BEP, BIRK, AU ... are foreign issuers
    # and ADRs. Massive's financials are built from SEC filings, and foreign
    # private issuers file 20-F/40-F, which this dataset does not carry. They
    # are cached (correctly -- retrying them forever would waste the budget)
    # but counting them as covered overstates real coverage, so report both.
    def _has_data(t):
        try:
            return bool(json.loads((CARDS / f"{t}.json").read_text()).get("results"))
        except Exception:
            return False
    with_data = [t for t in covered if _has_data(t)]
    # `(_card_age(t) or 999)` would be wrong: a card fetched TODAY has age 0,
    # which is falsy, so it would be scored 999 days old — the freshest cards
    # counted as the stalest. Compare against None explicitly.
    def _age_or_stale(t):
        a = _card_age(t)
        return 999 if a is None else a
    fresh = [t for t in covered if _age_or_stale(t) < STALE_DAYS]
    print(f"universe    {len(tick)} liquid common stocks (built {u.get('built', 'never')})")
    print(f"covered     {len(covered)} ({len(covered) / max(len(tick), 1) * 100:.1f}%)")
    print(f"  with data  {len(with_data)}")
    print(f"  no filings {len(covered) - len(with_data)} (foreign issuers/ADRs — "
          f"file 20-F/40-F, not in this dataset; permanent, not a retry)")
    print(f"fresh       {len(fresh)} (<{STALE_DAYS}d old)")
    if tick:
        rem = len(tick) - len(covered)
        # 5 req/min is 300/hour, not 24. An earlier version divided by 24 and
        # reported 56h instead of ~5h — an 11x overstatement of the only real
        # cost of the free tier, which is exactly the number a decision about
        # paying for data would turn on.
        from fundamentals import RATE_SLEEP
        print(f"remaining   {rem} uncovered — {rem * RATE_SLEEP / 3600:.1f}h of wall clock "
              f"at {60 / RATE_SLEEP:.1f} req/min")
    print("\nCoverage compounds; a mover list does not. Breadth here is cumulative.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    if cmd == "universe":
        universe(arg)
    elif cmd == "cover":
        cover(int(arg or 20))
    elif cmd == "shortlist":
        shortlist(int(arg or 10))
    else:
        status()
