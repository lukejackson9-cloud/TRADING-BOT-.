"""
Forward earnings calendar — the missing input that kept this project's
advisory pipeline structurally unable to produce a buy.

THE PROBLEM THIS FIXES (measured 2026-09-12, not assumed)
---------------------------------------------------------
skills/screen.md ranks the whole market by |% change| and hands
research.md the top movers. So by construction EVERY ticker research.md
has ever seen is one that has ALREADY made its move. And the single most
common reason research.md rejects a ticker is that the move already
happened — "stale / already priced in / sell the news" appears in 57 of
147 research notes (39%), per scorecard.md's miss postmortem.

The pipeline finds movers, then rejects them for being movers. That is a
closed loop, and it explains a week with zero CANDIDATEs better than any
claim about the market.

CLAUDE.md already anticipated this: the watchlist is supposed to be
"both reactive (today's movers) and forward-looking (screen.md's
earnings-calendar lookahead, so research.md can catch a reaction
same-session instead of chasing a move that already happened)". The
forward arm was effectively dead:
    FMP earnings calendar, next 2 weeks .................  2 entries
    watchlist lines carrying a pre-catalyst tag .........  4 of 174
    research notes with any forward/pending framing .....  7 of 136
~95% of everything ever researched was a stock at the worst possible
moment to buy it.

SOURCES — WHAT WORKS AND WHAT DOESN'T (all tested live 2026-09-12)
------------------------------------------------------------------
    api.nasdaq.com/api/calendar/earnings ... BLOCKED by this
        environment's egress proxy (ProxyError, not a 4xx).
    Massive/Polygon /benzinga/v1/earnings .. 403 "not entitled" —
        earnings are a paid add-on on this key.
    Yahoo quoteSummary calendarEvents ...... 429 on query1 AND query2,
        including the /v1/test/getcrumb warm-up, i.e. the shared egress
        IP is rate-limited, not fixable with headers. The repo's own
        yahoo_screener_client is currently 500-ing too.
    FMP /stable/earnings-calendar .......... WORKS. Used here.

FMP FREE TIER'S REAL LIMIT — IT IS NOT WHAT THE OLD NOTE SAID
--------------------------------------------------------------
CLAUDE.md described this feed as "sparse (~17 entries across a 6-week
window)" and prior sessions treated that as useless. Measured properly,
the limit is a UNIVERSE limit, not a date limit:
    next   7 days ->  1 entry   (FDX)
    next  30 days -> 13 entries (BAC, C, CCL, COST, DAL, FDX, GS, JNJ,
                                 JPM, NKE, PEP, TLRY, WFC)
    next  90 days -> 78 entries (AAPL, AMD, AMZN, BA, BABA, ABBV, ...)
So the free tier covers a curated set of roughly 78 large/liquid names
and reports their real dates. "2 entries this fortnight" means only two
of its covered names report then — not that the feed is broken.

That is genuinely useful: ~78 major names is a real forward watchlist.
**But absence from this calendar is NOT evidence a company has no
earnings coming.** Never write "no upcoming earnings" on the strength of
this feed alone — it means "not in FMP's covered set," which is a
different claim. `upcoming()` returns that caveat with every result so it
cannot be quietly dropped.

WIDENING IT: `merge` accepts entries the agent verified by WebSearch, so
skills/screen.md can extend coverage beyond FMP's universe without this
script pretending to a breadth it does not have. Merged entries are
tagged with their source and require a citation.

WHAT THIS DOES NOT DO
---------------------
It does not propose or rank trades. A pending earnings date is NOT a
catalyst — screen.md and research.md step 5 both cap a pre-catalyst
ticker at WATCH until the print actually lands. The entire value is
timing: research.md gets to evaluate the REACTION on the day, instead of
meeting the stock three days later as a +12% "mover" and correctly
rejecting it for having already moved.

Usage:
  python scripts/earnings_calendar.py refresh 90     # pull FMP, cache it
  python scripts/earnings_calendar.py upcoming 14    # what reports soon
  python scripts/earnings_calendar.py merge NVDA 2026-11-19 "verified: investor relations page"
"""

import os
import sys
import json
import datetime
from pathlib import Path

import requests

BASE_URL = "https://financialmodelingprep.com/stable"
CACHE = Path("data/earnings_calendar.json")
COVERAGE_NOTE = ("FMP free tier covers a curated ~78-name universe, NOT the whole market "
                 "(measured 2026-09-12). Absence here means 'not in FMP's covered set', "
                 "NEVER 'this company has no earnings coming'.")


def _key():
    k = os.environ.get("FMP_API_KEY")
    if not k:
        raise RuntimeError("FMP_API_KEY not set — source .env first")
    return k


def _load():
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    return {"fetched_at": None, "entries": {}}


def _save(d):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(d, indent=1, sort_keys=True))


def refresh(days=90):
    """Pull FMP's forward calendar and merge into the cache. Never drops
    manually-merged entries — FMP's narrow universe would otherwise wipe
    out anything widened in by WebSearch."""
    today = datetime.date.today()
    end = today + datetime.timedelta(days=days)
    r = requests.get(f"{BASE_URL}/earnings-calendar",
                     params={"from": today.isoformat(), "to": end.isoformat(), "apikey": _key()},
                     timeout=30)
    r.raise_for_status()
    rows = r.json()
    if not isinstance(rows, list):
        print(f"unexpected response: {str(rows)[:200]}")
        return
    d = _load()
    added = updated = 0
    for row in rows:
        sym, date = row.get("symbol"), row.get("date")
        if not sym or not date:
            continue
        prev = d["entries"].get(sym)
        entry = {"date": date, "source": "fmp",
                 "eps_estimated": row.get("epsEstimated"),
                 "revenue_estimated": row.get("revenueEstimated")}
        if prev is None:
            added += 1
        elif prev.get("date") != date:
            updated += 1
        # never let FMP overwrite a hand-verified entry's provenance silently
        if prev and prev.get("source", "").startswith("verified") and prev.get("date") == date:
            continue
        d["entries"][sym] = entry
    d["fetched_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    _save(d)
    print(f"FMP returned {len(rows)} rows for {today}..{end} ({days}d): "
          f"{added} new, {updated} date-changed, {len(d['entries'])} total cached")
    print(f"NOTE: {COVERAGE_NOTE}")


def merge(ticker, date, note):
    """Add an entry the agent verified itself (e.g. via WebSearch on the
    company's IR page). Requires a note — an unsourced date is exactly the
    kind of thing lessons.md #2 says not to trust."""
    datetime.date.fromisoformat(date)  # validate or raise
    if not note.strip():
        raise SystemExit("a sourcing note is required — never store an unsourced earnings date")
    d = _load()
    d["entries"][ticker.upper()] = {"date": date, "source": f"verified: {note.strip()}"}
    _save(d)
    print(f"merged {ticker.upper()} -> {date}  [{note.strip()}]")


def upcoming(days=14):
    d = _load()
    today = datetime.date.today()
    end = today + datetime.timedelta(days=days)
    rows = []
    for sym, e in d["entries"].items():
        try:
            dt = datetime.date.fromisoformat(e["date"])
        except Exception:
            continue
        if today <= dt <= end:
            rows.append((dt, sym, e.get("source", "?")))
    rows.sort()
    stamp = d.get("fetched_at") or "never"
    print(f"# Upcoming earnings, next {days} days ({today} .. {end})")
    print(f"# cache last refreshed: {stamp}")
    if not rows:
        print("# none in the cached universe for this window.")
    for dt, sym, src in rows:
        days_out = (dt - today).days
        print(f"{sym:<8} {dt}  (in {days_out:>2}d)   [{src}]")
    print(f"\n# CAVEAT: {COVERAGE_NOTE}")
    print("# A pending earnings date is NOT a catalyst. Tag these onto the watchlist as")
    print("# 'EARNINGS {date} — pre-catalyst watch'; research.md step 5 caps them at WATCH")
    print("# until the print actually lands. The point is to be WATCHING on the day.")
    return rows


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "upcoming"
    if cmd == "refresh":
        refresh(int(sys.argv[2]) if len(sys.argv) > 2 else 90)
    elif cmd == "upcoming":
        upcoming(int(sys.argv[2]) if len(sys.argv) > 2 else 14)
    elif cmd == "merge":
        merge(sys.argv[2], sys.argv[3], " ".join(sys.argv[4:]))
    else:
        print(__doc__.strip().split("Usage:")[-1])
