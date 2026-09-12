"""
Fundamental data for the scored council — whole market, free tier.

WHY THIS EXISTS
---------------
The project spent weeks on price-derived signals and `feature_ic.py` showed
they carry no cross-sectional information. The 2026-09-12 decision was to
change game: a 3-12 month horizon where the questions are about the business,
not the chart. That needs fundamentals, and the assumption had been that we
did not have them.

We do. Measured live 2026-09-12:
  FMP /stable/ratios-ttm, income-statement, balance-sheet, analyst-estimates
      WORK, but only for a curated ~78-name universe. Everything outside it
      returns 402 Payment Required (CENX, DRH, BAND, ROIV, TARS, AEHR, BIAF,
      GWRE, ASTS all refused).
  Massive /vX/reference/financials
      WORKS FOR THE WHOLE MARKET, free, including every name FMP refused —
      micro-caps included. Four statements, ~50 usable line items, TTM plus
      quarterly history.
So Massive is the base and FMP is optional enrichment for the names it
covers, not the other way round.

THE RATE LIMIT SHAPES THE PIPELINE
-----------------------------------
Massive's free tier is 5 requests/minute. An early probe fired 10 requests
0.25s apart and six came back empty; they were 429s, not missing coverage —
AEHR, TARS and BIAF all returned full statements once paced. Anything built
on this MUST pace itself, and must never read an empty result as "no data
for this company". So: screen down to ~20-30 names FIRST, then pull
fundamentals for those (~6 minutes), rather than fetching broadly.

WHAT IS NOT IN THE DATA, AND IS THEREFORE NOT REPORTED
-------------------------------------------------------
The balance sheet carries `liabilities` but no debt breakdown, and the cash
flow statement has no capex line. So:
  * leverage is TOTAL LIABILITIES / equity, labelled as such. It is NOT
    debt/equity and must never be called that -- for a bank or an insurer
    they differ enormously.
  * there is no free cash flow. Operating cash flow is reported raw. A
    capex-less "FCF" would be a fabricated number.
Any field the filing does not carry returns None and prints "n/a", never a
zero and never an estimate. A missing value that looks like a real one is
worse than a gap, and this project's first non-negotiable is not fabricating.

Usage:
  python scripts/fundamentals.py card AEHR
  python scripts/fundamentals.py cards AEHR CENX BAND
"""

import os
import sys
import json
import time
import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))

CACHE = Path("data/reference/fundamentals_cache")
MASSIVE_URL = "https://api.massive.com/vX/reference/financials"
RATE_SLEEP = 13          # 5 req/min free tier, with margin
CACHE_DAYS = 7           # filings do not change; a week is conservative


def _key():
    k = os.environ.get("MASSIVE_API_KEY")
    if not k:
        raise RuntimeError("MASSIVE_API_KEY not set — source .env first")
    return k


def fetch(ticker, periods=14, refresh=False):
    """Statements for one ticker, newest first. Cached for CACHE_DAYS.

    Raises on a 429 rather than returning empty: an empty list here would be
    indistinguishable from "this company files nothing", which is exactly the
    misreading that made a rate-limited probe look like missing coverage."""
    CACHE.mkdir(parents=True, exist_ok=True)
    cf = CACHE / f"{ticker.upper()}.json"
    if cf.exists() and not refresh:
        d = json.loads(cf.read_text())
        age = (datetime.date.today() - datetime.date.fromisoformat(d["fetched"])).days
        if age <= CACHE_DAYS:
            return d["results"]
    r = requests.get(MASSIVE_URL, params={"ticker": ticker.upper(), "limit": periods,
                                          "apiKey": _key()}, timeout=30)
    if r.status_code == 429:
        raise RuntimeError(f"{ticker}: rate limited (5/min) — pace the caller, "
                           f"do NOT treat this as 'no data'")
    r.raise_for_status()
    res = r.json().get("results", [])
    cf.write_text(json.dumps({"fetched": datetime.date.today().isoformat(), "results": res}))
    time.sleep(RATE_SLEEP)
    return res


def _v(period, statement, field):
    """One line item, or None if the filing does not carry it."""
    try:
        return period["financials"][statement][field]["value"]
    except (KeyError, TypeError):
        return None


def _div(a, b):
    return None if (a is None or b in (None, 0)) else a / b


def _price(ticker):
    """Latest close, for the valuation role. Alpaca: 200 req/min, no pacing
    problem. Prices are accurate on the free IEX feed even though its VOLUME
    is partial (that distinction cost this project a day once already)."""
    try:
        from alpaca_client import get_historical_bars
        end = datetime.date.today()
        bars = get_historical_bars(ticker, f"{end - datetime.timedelta(days=10)}T00:00:00Z",
                                   f"{end}T23:59:59Z", timeframe="1Day")
        return bars[-1]["c"] if bars else None
    except Exception:
        return None


def metrics(ticker):
    """Derived metrics grouped by the council role that owns them.

    Every value is either a real derivation from a reported field or None.
    Nothing is imputed, averaged in, or defaulted to zero."""
    res = fetch(ticker)
    if not res:
        return None
    # The API returns periods UNORDERED and mixed -- a real response was
    # [TTM2025, FY2025, Q12026, Q22026, FY2024, Q12025]. Positional indexing
    # is therefore meaningless: an earlier version took quarters[3] as "a year
    # ago" and would have compared Q1 against Q2, i.e. reported seasonality as
    # growth. Always match on the fiscal label, never on position.
    ttm = next((p for p in res if p.get("fiscal_period") == "TTM"), res[0])
    quarters = sorted((p for p in res if p.get("fiscal_period", "").startswith("Q")),
                      key=lambda p: p.get("end_date") or "", reverse=True)

    rev = _v(ttm, "income_statement", "revenues")
    gp = _v(ttm, "income_statement", "gross_profit")
    op = _v(ttm, "income_statement", "operating_income_loss")
    ni = _v(ttm, "income_statement", "net_income_loss")
    eq = _v(ttm, "balance_sheet", "equity")
    assets = _v(ttm, "balance_sheet", "assets")
    ca = _v(ttm, "balance_sheet", "current_assets")
    cl = _v(ttm, "balance_sheet", "current_liabilities")
    liab = _v(ttm, "balance_sheet", "liabilities")
    ocf = _v(ttm, "cash_flow_statement", "net_cash_flow_from_operating_activities")
    shares = _v(ttm, "income_statement", "diluted_average_shares")
    eps = _v(ttm, "income_statement", "diluted_earnings_per_share")

    # SHARE COUNT: BOTH candidate fields are unreliable, in different ways.
    #   reported `diluted_average_shares` — HUBG gives 180,826 against ~61M
    #     real shares (units); WU 1.98x and DAN 3.18x too high (TTM appears to
    #     sum quarterly averages). 3 of 10 sampled names wrong by >10%.
    #   `diluted_earnings_per_share` — BE reports 280 (real EPS ~1.09), and
    #     AGNC reports the integer 2, so a derived count inherits that error.
    # Deriving from EPS alone fixed HUBG and broke BE. Since neither field can
    # be trusted on its own, they must AGREE, with revenue x price as an
    # independent plausibility anchor to break ties. Where the two cannot be
    # reconciled the honest output is NOTHING: market cap and everything
    # derived from it (P/S, P/B, earnings yield, cash-flow yield) go to None
    # with a reason. A confidently wrong valuation at the top of the council's
    # list is far worse than a gap -- HUBG at a 1619% earnings yield, and then
    # BE at 101.7%, were both exactly that.
    px = _price(ticker)

    # Reject EPS outright when it is impossible relative to the share price.
    # BE reports diluted EPS of 280 against a ~$279 share price — a P/E of
    # 1.0, which essentially never occurs. Annual EPS above half the share
    # price (P/E < 2) is corrupt far more often than it is a genuine deep-
    # value situation, and the cost of wrongly excluding a real one is a gap,
    # while the cost of accepting a corrupt one is a fabricated valuation at
    # the top of the list. BE reached the shortlist at a 101.7% earnings
    # yield this way, immediately after the same slot was vacated by HUBG.
    eps_usable = (eps is not None and abs(eps) > 0.01
                  and not (px and abs(eps) > px / 2))
    shares_implied = None
    if ni is not None and eps_usable:
        cand = ni / eps
        if cand > 0:
            shares_implied = cand

    def _plausible(sh):
        """Is this share count consistent with price and revenue? A $36 stock
        with $3.7bn of revenue does not have 180,826 shares outstanding."""
        if not sh or not px or not rev or rev <= 0:
            return None
        return 0.02 <= (px * sh) / rev <= 50

    ok_rep, ok_imp = _plausible(shares), _plausible(shares_implied)
    agree = (shares and shares_implied
             and 0.8 < shares / shares_implied < 1.25)

    if agree:
        shares, share_basis = shares_implied, "reported and EPS-derived agree"
    elif ok_imp and not ok_rep:
        share_basis = "EPS-derived (reported figure implausible vs price x revenue)"
        shares = shares_implied
    elif ok_rep and not ok_imp:
        share_basis = "reported (EPS-derived implausible vs price x revenue)"
    elif shares_implied and shares:
        shares, share_basis = None, (
            f"UNVERIFIABLE — reported and EPS-derived disagree "
            f"({shares / shares_implied:.2f}x) and neither is clearly right; "
            f"market-cap metrics suppressed")
    elif shares or shares_implied:
        shares = shares or shares_implied
        share_basis = "single source, uncorroborated — treat cap metrics with care"
    else:
        share_basis = "no share count available"

    mcap = px * shares if (px and shares) else None

    # growth: the newest quarter vs the SAME fiscal quarter one year earlier,
    # located by label, so seasonality cannot masquerade as a trend. If the
    # year-ago quarter is not in the response, this stays None rather than
    # silently comparing against whatever period happens to be nearby.
    rev_growth = growth_basis = None
    if quarters:
        q0 = quarters[0]
        try:
            want_year = str(int(q0.get("fiscal_year")) - 1)
        except (TypeError, ValueError):
            want_year = None
        prior = next((p for p in quarters
                      if p.get("fiscal_period") == q0.get("fiscal_period")
                      and str(p.get("fiscal_year")) == want_year), None)
        if prior is not None:
            r0 = _v(q0, "income_statement", "revenues")
            r1 = _v(prior, "income_statement", "revenues")
            # Growth is UNDEFINED against a non-positive base. DBRG reported
            # Q2-2025 revenue of -$3.2M (real: fair-value/carried-interest
            # adjustments at an asset manager), and (508.7M - -3.2M)/3.2M
            # printed as +15,961% growth -- arithmetically fine, economically
            # meaningless, and it would have read to the council as a
            # spectacular business. Report it as undefined, with the reason.
            if r0 is not None and r1 is not None and r1 > 0:
                rev_growth = (r0 - r1) / r1
                growth_basis = (f"{q0.get('fiscal_period')}{q0.get('fiscal_year')}"
                                f" vs {prior.get('fiscal_period')}{prior.get('fiscal_year')}")
                if abs(rev_growth) > 5:      # >500%: real but needs a human look
                    growth_basis += "  [EXTREME — verify against the filing]"
            elif r1 is not None and r1 <= 0:
                growth_basis = (f"undefined — base period "
                                f"{prior.get('fiscal_period')}{prior.get('fiscal_year')} "
                                f"revenue was {r1:,.0f}")

    return {
        "ticker": ticker.upper(),
        "company": ttm.get("company_name"),
        "period": f"{ttm.get('fiscal_period')}{ttm.get('fiscal_year')} "
                  f"({ttm.get('start_date')}..{ttm.get('end_date')})",
        "price": px,
        "market_cap": mcap,
        "share_count_basis": share_basis,
        "quality": {
            "revenue_ttm": rev,
            "gross_margin": _div(gp, rev),
            "operating_margin": _div(op, rev),
            "net_margin": _div(ni, rev),
            # ROE is MEANINGLESS when equity is negative: a profitable company
            # with negative book equity yields a large negative ROE that reads
            # as catastrophic losses. Seen live — A printed -618% and ABBV
            # -107% while both were profitable. Suppress it and flag instead.
            "return_on_equity": (_div(ni, eq) if (eq or 0) > 0 else None),
            "return_on_assets": _div(ni, assets),
            "revenue_growth_yoy_q": rev_growth,
            "growth_basis": growth_basis,
        },
        "valuation": {
            "pe_ttm": (_div(px, eps) if (px and eps and eps > 0 and eps_usable)
                       else None),
            "price_to_sales": _div(mcap, rev),
            "price_to_book": _div(mcap, eq),
            "op_cashflow_yield": _div(ocf, mcap),
            "earnings_yield": _div(ni, mcap),
        },
        "health": {
            "current_ratio": _div(ca, cl),
            "total_liabilities_to_equity": _div(liab, eq),   # NOT debt/equity
            "operating_cash_flow_ttm": ocf,                  # NOT free cash flow
            "cash_flow_positive": None if ocf is None else ocf > 0,
            "profitable": None if ni is None else ni > 0,
            "negative_equity": None if eq is None else eq < 0,
        },
    }


def _fmt(k, v):
    if k == "growth_basis":
        return f"    {'(growth compares)':<30} {v}" if v else ""
    if v is None:
        return f"    {k:<30} n/a (not reported in the filing)"
    if isinstance(v, bool):
        return f"    {k:<30} {'yes' if v else 'NO'}"
    if abs(v) >= 1e6:
        return f"    {k:<30} {v / 1e6:,.1f}M"
    if k.endswith(("margin", "growth_yoy_q", "yield")) or k.startswith("return_on"):
        return f"    {k:<30} {v * 100:.1f}%"
    return f"    {k:<30} {v:,.2f}"


def card(ticker):
    """The card the four council roles read. Grouped by role on purpose:
    each member should be looking at its own evidence, not the same blob."""
    m = metrics(ticker)
    if not m:
        print(f"{ticker}: no filings returned — check the ticker, or it may be a fund/ADR")
        return None
    print("=" * 64)
    print(f"{m['ticker']}  {m['company'] or ''}")
    print(f"period: {m['period']}")
    px = f"${m['price']:,.2f}" if m["price"] else "n/a"
    mc = f"${m['market_cap'] / 1e9:,.2f}B" if m["market_cap"] else "n/a"
    print(f"price: {px}   market cap: {mc}")
    if m.get("share_count_basis", "reported") != "reported":
        print(f"shares: {m['share_count_basis']}")
    print("=" * 64)
    for role, label in (("quality", "BUSINESS QUALITY"), ("valuation", "VALUATION"),
                        ("health", "FINANCIAL HEALTH")):
        print(f"  {label}")
        for k, v in m[role].items():
            line = _fmt(k, v)
            if line:
                print(line)
    print("  FALSIFIER — no metrics by design: this role states what would have")
    print("    to be TRUE for the thesis to fail, and whether it is checkable.")
    print("  NOTE: leverage is total liabilities/equity, not debt/equity (no debt")
    print("    line is filed). Operating cash flow is not free cash flow (no capex).")
    return m


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "card"
    if cmd == "card":
        card(sys.argv[2])
    elif cmd == "cards":
        for t in sys.argv[2:]:
            card(t)
            print()
    else:
        print(__doc__.strip().split("Usage:")[-1])
