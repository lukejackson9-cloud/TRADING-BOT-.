"""
Tags TA/ICT paper-trade signals with whether a REAL, dated, company-
specific catalyst existed around the signal date -- built 2026-09-11 as
the forward-only counterpart to scripts/backtest_confluence.py. The
historical confluence tests could only check MECHANICAL signal agreement
(TA x TA, TA x macro-calendar, TA x ICT) and found nothing; they
explicitly could NOT test "TA/ICT signal + a real news catalyst", because
the only historical proxy tried for "news happened" (an overnight price
gap, 2026-09-07) made results worse -- it captures the reaction after it
fires, not the catalyst itself (see lessons.md #1). There is no
authoritative historical company-news database at this project's data
tier, so this dimension can only be measured going forward, tagged in
real time, the way research.md already tags catalysts for the advisory
pipeline.

CATALYST DEFINITION (fixed up front, same discipline as everything else
in this project -- do not loosen it to get more "has_catalyst" trades):
a dated, COMPANY-SPECIFIC event -- earnings (that day or the trading day
before), M&A, an FDA/regulatory decision, a guidance change, or a
material analyst action carrying genuinely new information. NOT "the
stock moved" (that's the exact mistake the gap-proxy made) and not a
stale/recycled story (see lessons.md #6). If a WebSearch check is
inconclusive, tag "unclear" -- never guess.

This script does NOT call WebSearch itself (it's a script, not an
agent) -- see skills/catalyst_tag.md for the actual daily procedure: an
agent session (the same one the paper-trade routines already run in)
calls `pending` to find which tickers need a check, does one WebSearch
per unique ticker, then calls `tag` to record the verdict. Tags are
written into whichever of data/paper_trades.json / data/ict_paper_trades.json
has a matching (ticker/symbol, date) entry with catalyst still unset --
a ticker firing 3 TA setups the same day gets ONE check, applied to all 3
entries at once. Already-tagged entries are left alone (idempotent
re-runs, and a later correction requires deleting the tag by hand first,
not silently overwriting).

No retroactive tagging: only signals opened FROM WHEN THIS WENT LIVE
forward get tagged. Reconstructing "was there a catalyst" on a past date
with today's hindsight would bias the result exactly the way this whole
design exists to avoid -- entries that pre-date this feature simply have
no "catalyst" key (see the two migration notes in paper_trader.py /
ict_paper_trader.py), not a backfilled guess.

Usage:
  python scripts/tag_catalyst.py pending 2026-09-15
  python scripts/tag_catalyst.py tag AAPL 2026-09-15 true "Q4 earnings beat, printed after close 09-14"
  python scripts/tag_catalyst.py tag XYZ 2026-09-15 false "no dated news found"
  python scripts/tag_catalyst.py tag XYZ 2026-09-15 unclear "WebSearch inconclusive"
  python scripts/tag_catalyst.py report
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

TA_LEDGER = Path("data/paper_trades.json")
ICT_LEDGER = Path("data/ict_paper_trades.json")
MIN_SAMPLE = 50  # floor before drawing any conclusion -- same bar as backtest_confluence.py


def _load(path):
    return json.loads(path.read_text()) if path.exists() else []


def _save(path, data):
    path.write_text(json.dumps(data, indent=2))


def pending(date):
    """Unique tickers with an untagged signal on `date`, across both
    ledgers -- what skills/catalyst_tag.md's daily procedure checks."""
    tickers = set()
    for p in _load(TA_LEDGER):
        if p.get("entry_date") == date and p.get("catalyst") is None and "catalyst" in p:
            tickers.add(p["ticker"])
    for t in _load(ICT_LEDGER):
        if t.get("date") == date and t.get("catalyst") is None and "catalyst" in t:
            tickers.add(t["symbol"])
    print(f"{len(tickers)} ticker(s) need a catalyst check for {date}: {sorted(tickers)}")
    return sorted(tickers)


def tag(ticker, date, verdict_str, note=""):
    """Writes {has_catalyst, note} into every matching, currently-untagged
    ledger entry for (ticker, date) in BOTH ledgers -- a ticker that fired
    multiple TA setups or ICT mechanisms the same day gets the same tag
    applied everywhere at once, since it's one real-world fact (was there
    a catalyst that day), not a per-setup one."""
    if verdict_str not in ("true", "false", "unclear"):
        print(f"error: verdict must be true/false/unclear, got {verdict_str!r}")
        return
    verdict = {"true": True, "false": False, "unclear": "unclear"}[verdict_str]
    payload = {"has_catalyst": verdict, "note": note, "tagged_on": date}

    updated = 0
    ta = _load(TA_LEDGER)
    for p in ta:
        if p.get("ticker") == ticker and p.get("entry_date") == date and p.get("catalyst") is None:
            p["catalyst"] = payload
            updated += 1
    _save(TA_LEDGER, ta)

    ict = _load(ICT_LEDGER)
    for t in ict:
        if t.get("symbol") == ticker and t.get("date") == date and t.get("catalyst") is None:
            t["catalyst"] = payload
            updated += 1
    _save(ICT_LEDGER, ict)

    print(f"tagged {updated} ledger entries for {ticker} on {date}: has_catalyst={verdict}")


def _bucket_report(label, trades, return_key):
    n = len(trades)
    if n == 0:
        print(f"  {label}: 0 trades")
        return
    wins = sum(1 for t in trades if t[return_key] > 0)
    avg = sum(t[return_key] for t in trades) / n
    unit = "%" if return_key == "pct_return" else "R"
    scale = 100 if return_key == "pct_return" else 1
    print(f"  {label}: {n} trades, {wins/n*100:.1f}% win, {avg*scale:.2f}{unit}/trade")


def _concentration(trades, ticker_key, return_key):
    positive = [t for t in trades if t[return_key] > 0]
    total = sum(t[return_key] for t in positive)
    if total <= 0:
        return
    by_ticker = defaultdict(float)
    for t in positive:
        by_ticker[t[ticker_key]] += t[return_key]
    top, val = max(by_ticker.items(), key=lambda kv: kv[1])
    share = val / total * 100
    flag = " <-- CONCENTRATION WARNING (>35%)" if share > 35 else ""
    print(f"      concentration: top contributor {top} = {share:.1f}% of positive return{flag}")


def report():
    """Compares HAS-catalyst vs NO-catalyst forward paper-trade results,
    across both TA (closed trades only -- open ones haven't resolved yet)
    and ICT (always same-day resolved) ledgers. Applies the same MIN_SAMPLE
    floor as backtest_confluence.py -- do not read a conclusion into this
    before there's a real sample, especially in the HAS-catalyst bucket,
    which will naturally fill much more slowly than NO-catalyst."""
    ta_tagged = [p for p in _load(TA_LEDGER) if p.get("status") == "closed" and p.get("catalyst") is not None]
    ict_tagged = [t for t in _load(ICT_LEDGER) if t.get("catalyst") is not None]

    print("=== TA setups (closed, tagged trades) ===")
    for label, val in (("HAS catalyst", True), ("NO catalyst", False), ("unclear", "unclear")):
        bucket = [t for t in ta_tagged if t["catalyst"]["has_catalyst"] == val]
        _bucket_report(label, bucket, "pct_return")
        if val is True and bucket:
            _concentration(bucket, "ticker", "pct_return")

    print("\n=== ICT mechanisms (tagged trades) ===")
    for label, val in (("HAS catalyst", True), ("NO catalyst", False), ("unclear", "unclear")):
        bucket = [t for t in ict_tagged if t["catalyst"]["has_catalyst"] == val]
        _bucket_report(label, bucket, "return_r")
        if val is True and bucket:
            _concentration(bucket, "symbol", "return_r")

    has_catalyst_n = sum(1 for t in ta_tagged if t["catalyst"]["has_catalyst"] is True) + \
        sum(1 for t in ict_tagged if t["catalyst"]["has_catalyst"] is True)
    if has_catalyst_n < MIN_SAMPLE:
        print(f"\nHAS-catalyst sample is only {has_catalyst_n} trades (want >={MIN_SAMPLE}) -- "
              f"too early to conclude anything, keep collecting.")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "pending":
        pending(sys.argv[2])
    elif cmd == "tag":
        note = sys.argv[5] if len(sys.argv) > 5 else ""
        tag(sys.argv[2], sys.argv[3], sys.argv[4], note)
    elif cmd == "report":
        report()
    else:
        print("usage: tag_catalyst.py pending DATE | tag TICKER DATE true|false|unclear [NOTE] | report")
