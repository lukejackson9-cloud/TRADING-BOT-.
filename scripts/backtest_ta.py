"""
Backtests short-term TA setups against Massive.com's historical
whole-market daily data, using CLAUDE.md's existing exit rule (-4% stop /
+8% target / 5-trading-day time-stop) so results are measured against the
rule this project already trades by, not an arbitrary new one.

Setups (see iter_signals()'s docstring for the full, current list --
breakout, ema_cross, mean_reversion, vcp_breakout, relative_strength as
of 2026-09-09):
  - breakout: today's close > the prior 20-trading-day high, AND today's
    volume >= 1.5x the prior 20-day average volume.
  - ema_cross: 9-day EMA crosses above the 21-day EMA (yesterday 9EMA <=
    21EMA, today 9EMA > 21EMA) -- "trend just turned up".

Entry is simulated at the NEXT trading day's open after a signal (the
signal itself is only knowable using data through the signal day's close
-- no lookahead). Exit is whichever of -4% / +8% / 5-trading-days hits
first, checked day by day against each subsequent day's high/low/close.
If a single day's range hits both stop and target, this conservatively
assumes the stop hit first (standard, conservative backtest convention
when intraday sequencing isn't known from daily bars alone) -- a real
limitation of daily-bar backtesting, not a bug; noted in the report.

Universe: EVERY ticker Massive's grouped-daily endpoint returns for each
historical date, filtered to $5-$500 price and >1M volume ON THE SIGNAL
DAY -- matching CLAUDE.md's existing screening filters. This measures
"would this rule have found tradeable, liquid setups".

SURVIVORSHIP-BIAS FIX (2026-09-11): fetch_range() used to additionally
require `r["T"] in get_common_stock_tickers()` -- TODAY's active
common-stock list -- before caching a day's data. That silently dropped
every ticker that was later delisted, acquired, or went bankrupt from
EVERY historical day's cache, including days it was actually trading,
which systematically flatters every result (the exact bug CLAUDE.md's
"Standing caveat" section used to just disclose rather than fix). Fixed
by caching Massive's grouped-daily response for a date unfiltered by
ticker identity -- that endpoint already returns whatever was genuinely
trading on that date, not today's roster, so no client-side "is this
ticker still around" filter is needed or wanted.
Trade-off, stated plainly: Massive's grouped-daily payload has no
asset-type field (confirmed against a live response), so this can no
longer cheaply exclude ETFs/crypto-adjacent tickers (get_grouped_daily's
own docstring notes XRP showed up in a live pull) the way the old,
now-removed filter incidentally did. A handful of non-common-stock
instruments technically firing a breakout/ema_cross signal is a much
smaller distortion than systematically erasing every stock that ever
went to zero or got bought out -- survivorship bias inflates results in
one direction on every single trade; ETF contamination adds a small,
directionless amount of noise on a small minority of trades. Re-running
`fetch` end to end (needed to actually pick up the newly-uncensored
historical data -- the existing gitignored cache under
data/reference/backtest_cache/ still reflects the OLD, filtered fetch and
must be regenerated, not just re-analyzed) requires real Massive API
credentials and takes hours at the free tier's 5 req/min -- not done as
part of this fix, flagged for whichever session actually has `.env`
credentials loaded.
fetch_range_alpaca() (the 6-year extension) has a HARDER, NOT-YET-FIXED
version of the same bug: it fetches per-SYMBOL, iterating
get_common_stock_tickers() (today's list) up front, so it never even
attempts to fetch a delisted ticker's history in the first place -- there
is no per-day "whatever was trading" endpoint on the Alpaca free tier to
fall back on here. Properly fixing this needs a point-in-time historical
ticker/delisted-securities list (e.g. a paid data vendor or an
index-membership history), which this project doesn't currently have
access to. Until that exists, treat the 6-year Alpaca-extended results as
carrying the full, unmitigated version of this bias; the 2-year
Massive-sourced results above do not, once re-fetched per this fix.

CONFIRMED LIVE (2026-09-07): Massive's free tier only serves 2 years of
grouped-daily history -- every date before 2024-09-08 returned 403
Forbidden in a live test (2024-09-08 itself returned OK with
resultsCount 0, i.e. no trading that day; 2023-09-07 and multiple 2024
dates all 403'd). This is a rolling window tied to today's date, not a
fixed date -- don't assume 3 years is available; re-verify the cutoff
live before requesting anything older than ~2 years back.

Two-pass design:
  Pass 1 (fetch_range): pulls get_grouped_daily() day by day, caching each
    day's compact {ticker: [o,h,l,c,v]} to
    data/reference/backtest_cache/{date}.json (gitignored -- regenerable
    infrastructure, not project memory, same category as equity_tickers.json).
    Resumable: already-cached days are skipped, so an interrupted run picks
    up where it left off. Massive's free tier is 5 req/min; this sleeps
    between uncached fetches to stay under that.
  Pass 2 (run_backtest): pure in-memory, no network calls -- walks each
    ticker's cached series chronologically, computes both setups' signals
    with a rolling window, and simulates the exit rule forward using that
    ticker's own already-fetched future days.

Usage:
  python scripts/backtest_ta.py fetch 2023-09-07 2026-09-04
  python scripts/backtest_ta.py backtest 2023-09-07 2026-09-04
"""

import sys
import json
import time
import datetime
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from massive_client import get_grouped_daily, get_common_stock_tickers, get_ticker_range_aggs  # noqa: E402
from alpaca_client import get_historical_bars  # noqa: E402

CACHE_DIR = Path("data/reference/backtest_cache")
PRICE_MIN, PRICE_MAX, VOLUME_MIN = 5, 500, 1_000_000
STOP_PCT, TARGET_PCT, TIME_STOP_DAYS = -0.04, 0.08, 5
REGIME_SMA_WINDOW = 50  # short enough to fit this project's days-to-2-week
# horizon (a 200-day "bull/bear market" filter is the more classic choice,
# but it needs 200 days of warmup data we don't have within the 2-year
# free-tier window without eating deep into the test sample -- 50-day is a
# defensible, cheaper-to-warm-up stand-in, not a claim that it's the "right"
# lookback; worth revisiting with 200-day if this shows promise).
RSI_PERIOD, RSI_OVERSOLD = 14, 30
VCP_LOOKBACK = 20  # same window as breakout, split in half to compare
# recent vs. earlier volatility
VCP_CONTRACTION_RATIO = 0.7  # recent-half avg daily range must be <= 70%
# of the earlier half's -- a real tightening, not just "any" breakout
RS_WINDOW = 20  # trading days of trailing return to compare against SPY
RS_THRESHOLD = 0.15  # stock must be outperforming SPY by 15 percentage
# points over that window at the moment the signal fires (a crossing, not
# "still outperforming" -- see iter_signals)


def _trading_days(start, end):
    d = datetime.date.fromisoformat(start)
    end_d = datetime.date.fromisoformat(end)
    while d <= end_d:
        if d.weekday() < 5:  # Mon-Fri; holidays handled by empty-result skip below
            yield d.isoformat()
        d += datetime.timedelta(days=1)


def fetch_range(start, end):
    """No longer filters by get_common_stock_tickers() (today's active
    list) before caching -- see the module docstring's "SURVIVORSHIP-BIAS
    FIX" section for why that filter was removed and what it traded off."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    days = list(_trading_days(start, end))
    fetched = 0
    for date in days:
        cache_file = CACHE_DIR / f"{date}.json"
        if cache_file.exists():
            continue
        data = get_grouped_daily(date)
        if data.get("status") == "OK" and data.get("results"):
            compact = {
                r["T"]: [r["o"], r["h"], r["l"], r["c"], r["v"]]
                for r in data["results"]
            }
            cache_file.write_text(json.dumps({"status": "OK", "results": compact}))
            print(f"{date}: cached {len(compact)} tickers")
        else:
            # holiday/weekend/no data -- cache the miss so we don't retry it
            cache_file.write_text(json.dumps({"status": data.get("status", "EMPTY"), "results": {}}))
            print(f"{date}: no data ({data.get('status')}), cached as empty")
        fetched += 1
        time.sleep(13)  # free tier: 5 req/min (sliding window -- space every call, not just every 5th)
    print(f"done: {len(days)} calendar weekdays checked, {fetched} newly fetched")


def fetch_range_alpaca(start, end, batch_size=500):
    """Extends the SAME CACHE_DIR day-file cache fetch_range() builds, but
    sourced from Alpaca's per-symbol daily bars instead of Massive's
    whole-market-per-day endpoint -- added 2026-09-09 because Alpaca's
    free tier confirmed live to serve daily bars back to ~2020-08 (a
    single-symbol binary search: 2020-07-01 empty, 2020-08-05 real data),
    over 3x Massive's 2-year cap. Writes day-files in the EXACT same
    {"status": "OK", "results": {ticker: [o,h,l,c,v]}} shape fetch_range()
    does, so _load_series()/iter_signals()/run_backtest() all work
    unchanged on the combined dataset -- call this for the OLDER portion
    of the range (before Massive's 2024-09-08 cutoff) and leave the
    existing Massive-sourced files for the newer portion alone; a
    continuous multi-year dataset falls out of _load_series() reading
    both without any code caring which source a given day came from.

    Alpaca is per-SYMBOL (one API call gets a whole date range for one
    ticker), the opposite shape from Massive's per-DAY-whole-market call,
    so this fetches ticker by ticker and buffers results in memory,
    flushing to day-files every `batch_size` tickers to bound memory
    (~5,300 tickers x ~6 years of daily bars all held at once would be
    too much). A small manifest (CACHE_DIR/_alpaca_fetched.json) tracks
    which tickers are already done, for resumability if interrupted --
    same lesson as the manual nohup fetch that died mid-run on 2026-09-07,
    this uses the harness's own run_in_background tracking, not a
    detached shell process.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    equities = sorted(get_common_stock_tickers())

    manifest_path = CACHE_DIR / "_alpaca_fetched.json"
    done = set(json.loads(manifest_path.read_text())) if manifest_path.exists() else set()
    todo = [t for t in equities if t not in done]
    print(f"{len(done)} tickers already fetched, {len(todo)} remaining")

    buffer = defaultdict(dict)  # date -> {ticker: [o,h,l,c,v]}

    def _flush():
        for date, ticker_data in buffer.items():
            cache_file = CACHE_DIR / f"{date}.json"
            if cache_file.exists():
                existing = json.loads(cache_file.read_text())
                results = existing.get("results", {})
            else:
                results = {}
            results.update(ticker_data)
            cache_file.write_text(json.dumps({"status": "OK", "results": results}))
        buffer.clear()
        manifest_path.write_text(json.dumps(sorted(done)))

    for idx, ticker in enumerate(todo):
        try:
            bars = get_historical_bars(ticker, f"{start}T00:00:00Z", f"{end}T23:59:59Z", timeframe="1Day")
        except Exception as e:
            print(f"{ticker}: fetch error ({e}), skipping")
            done.add(ticker)
            continue
        for b in bars:
            date = datetime.datetime.fromisoformat(b["t"].replace("Z", "+00:00")).date().isoformat()
            buffer[date][ticker] = [b["o"], b["h"], b["l"], b["c"], b["v"]]
        done.add(ticker)
        if (idx + 1) % batch_size == 0 or idx == len(todo) - 1:
            _flush()
            print(f"...flushed after {idx + 1}/{len(todo)} tickers this run ({len(done)}/{len(equities)} total)")
        time.sleep(0.32)  # 200 req/min free tier, safety margin

    print(f"done: {len(done)}/{len(equities)} tickers fetched")


def _load_series(start, end):
    series = defaultdict(list)  # ticker -> [(date, o,h,l,c,v), ...] chronological
    for date in _trading_days(start, end):
        cache_file = CACHE_DIR / f"{date}.json"
        if not cache_file.exists():
            continue
        data = json.loads(cache_file.read_text())
        for ticker, ohlcv in data["results"].items():
            series[ticker].append((date, *ohlcv))
    return series


def _ema(prev_ema, price, n):
    k = 2 / (n + 1)
    return price * k + prev_ema * (1 - k) if prev_ema is not None else price


def _load_spy_bars(start, end):
    """Shared SPY daily-bar loader for both _fetch_spy_regime and
    _spy_closes -- sourced from Alpaca (not Massive's get_ticker_range_aggs
    as originally written), because Massive's 2-year cap can't reach the
    older portion of the extended 2020-08+ range fetch_range_alpaca()
    populates for everything else, added 2026-09-09. Alpaca's bars use an
    RFC3339 string "t" ("2021-06-02T04:00:00Z"), not Massive/Polygon's
    epoch-ms int -- normalized to epoch-ms here at fetch/cache time so the
    two callers' existing parsing (`b["t"] / 1000`) doesn't need to care
    which source built the cache. Caches to CACHE_DIR/SPY.json (one API
    call covers the whole range); delete that file to force a re-fetch
    with a wider range if a caller ever needs dates outside what's cached
    (confirmed live 2026-09-09: don't assume the old cached range covers
    a new, wider request -- check/refresh explicitly)."""
    cache_file = CACHE_DIR / "SPY.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    raw = get_historical_bars("SPY", f"{start}T00:00:00Z", f"{end}T23:59:59Z", timeframe="1Day")
    bars = [
        {"t": int(datetime.datetime.fromisoformat(b["t"].replace("Z", "+00:00")).timestamp() * 1000), "c": b["c"]}
        for b in raw
    ]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(bars))
    return bars


def _fetch_spy_regime(start, end, sma_window=REGIME_SMA_WINDOW):
    """Market-regime filter: {date: bool} -- True on days SPY's close is
    above its own `sma_window`-day SMA ("bullish regime"), False otherwise.
    Only take breakout/ema_cross LONG entries on True days -- the standard
    "don't fight the tape" filter for momentum-continuation systems, which
    tend to fail worst in choppy/downtrending markets. The first
    sma_window trading days of `start`..`end` have no regime value yet
    (not enough warmup) and are dropped by callers, not treated as
    bearish by default."""
    bars = _load_spy_bars(start, end)
    regime = {}
    closes = []
    for b in bars:
        date = datetime.datetime.fromtimestamp(b["t"] / 1000, tz=datetime.timezone.utc).date().isoformat()
        closes.append(b["c"])
        if len(closes) >= sma_window:
            sma = sum(closes[-sma_window:]) / sma_window
            regime[date] = closes[-1] > sma
    return regime


def _spy_closes(start, end):
    """{date: close} for SPY, via the shared _load_spy_bars() cache. Used
    by the relative_strength signal in iter_signals to compute a stock's
    return vs. SPY's return over the same window."""
    bars = _load_spy_bars(start, end)
    return {
        datetime.datetime.fromtimestamp(b["t"] / 1000, tz=datetime.timezone.utc).date().isoformat(): b["c"]
        for b in bars
    }


def _rsi_series(bars, period=RSI_PERIOD):
    """Wilder's RSI, standard incremental smoothing (same shape as _ema
    above). Returns a list aligned to `bars`, None until enough bars exist."""
    out = [None] * len(bars)
    if len(bars) <= period:
        return out
    gains = losses = 0.0
    for i in range(1, period + 1):
        delta = bars[i][4] - bars[i - 1][4]
        gains += max(delta, 0)
        losses += max(-delta, 0)
    avg_gain, avg_loss = gains / period, losses / period
    out[period] = 100 - 100 / (1 + avg_gain / avg_loss) if avg_loss else 100
    for i in range(period + 1, len(bars)):
        delta = bars[i][4] - bars[i - 1][4]
        gain, loss = max(delta, 0), max(-delta, 0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        out[i] = 100 - 100 / (1 + avg_gain / avg_loss) if avg_loss else 100
    return out


def _simulate_exit(bars, entry_idx):
    """bars: full chronological list for one ticker. entry_idx: index of the
    signal day. Enters at bars[entry_idx+1]'s open, exits per the stop/
    target/time-stop rule using subsequent bars. Returns pct_return or None
    if there aren't enough future bars to simulate (still open at data end)."""
    if entry_idx + 1 >= len(bars):
        return None
    entry_price = bars[entry_idx + 1][1]  # open
    stop_price = entry_price * (1 + STOP_PCT)
    target_price = entry_price * (1 + TARGET_PCT)
    for i in range(1, TIME_STOP_DAYS + 1):
        idx = entry_idx + i
        if idx >= len(bars):
            return None  # ran off the end of available data before resolving
        _, o, h, l, c, v = bars[idx]
        if l <= stop_price:
            return STOP_PCT
        if h >= target_price:
            return TARGET_PCT
        if i == TIME_STOP_DAYS:
            return (c - entry_price) / entry_price
    return None


def iter_signals(bars, spy_closes=None):
    """Shared signal logic -- yields (index, date, setup_name) for every bar
    in `bars` (one ticker's chronological [(date,o,h,l,c,v), ...]) where
    any setup fires. Used by both the historical backtest (run_backtest,
    below) and scripts/paper_trader.py's forward daily scan, so the two
    can never drift apart on what counts as a signal.

    Five setups:
    - "breakout" and "ema_cross": momentum-continuation (see module
      docstring).
    - "mean_reversion": the OPPOSITE regime bet, added 2026-09-07 to test
      whether momentum failing means the market's character right now
      favors reversion instead: RSI(14) crossing UP through 30 (an
      oversold bounce CONFIRMED by the cross, not "still falling and
      cheap").
    - "vcp_breakout" (added 2026-09-09): a tightened version of breakout
      requiring genuine volatility contraction first -- the last
      VCP_LOOKBACK days split in half, recent-half average daily range
      must be <= VCP_CONTRACTION_RATIO of the earlier half's, THEN the
      same close-above-prior-high + volume trigger as breakout. Targets
      breakout's specific failure mode (false breakouts from names that
      were never actually consolidating).
    - "relative_strength" (added 2026-09-09): stock's trailing RS_WINDOW-day
      return minus SPY's return over the same window crossing UP through
      RS_THRESHOLD (a real acceleration in outperformance, not "has been
      outperforming for a while already" -- same crossing-not-level design
      as ema_cross/mean_reversion). Only computed when `spy_closes` (a
      {date: close} dict from _spy_closes) is given -- callers without it
      (e.g. a quick scan that hasn't fetched SPY) simply don't get this
      setup, not an error."""
    ema9 = ema21 = None
    prev_ema9 = prev_ema21 = None
    rsi = _rsi_series(bars)
    for i, (date, o, h, l, c, v) in enumerate(bars):
        prev_ema9, prev_ema21 = ema9, ema21
        ema9 = _ema(ema9, c, 9)
        ema21 = _ema(ema21, c, 21)

        if i < 21:
            continue
        if not (PRICE_MIN <= c <= PRICE_MAX) or v < VOLUME_MIN:
            continue

        window = bars[i - 20:i]  # prior 20 days, excludes today
        prior_high = max(b[2] for b in window)
        prior_avg_vol = sum(b[5] for b in window) / 20
        breakout_trigger = c > prior_high and v >= 1.5 * prior_avg_vol
        if breakout_trigger:
            yield i, date, "breakout"

        if prev_ema9 is not None and prev_ema21 is not None:
            if prev_ema9 <= prev_ema21 and ema9 > ema21:
                yield i, date, "ema_cross"

        if rsi[i] is not None and rsi[i - 1] is not None:
            if rsi[i - 1] < RSI_OVERSOLD <= rsi[i]:
                yield i, date, "mean_reversion"

        if breakout_trigger and i >= VCP_LOOKBACK:
            vcp_window = bars[i - VCP_LOOKBACK:i]
            mid = VCP_LOOKBACK // 2
            earlier_half, recent_half = vcp_window[:mid], vcp_window[mid:]
            earlier_vol = sum((b[2] - b[3]) / b[4] for b in earlier_half) / len(earlier_half)
            recent_vol = sum((b[2] - b[3]) / b[4] for b in recent_half) / len(recent_half)
            if earlier_vol > 0 and recent_vol <= VCP_CONTRACTION_RATIO * earlier_vol:
                yield i, date, "vcp_breakout"

        if spy_closes is not None and i >= RS_WINDOW + 1:
            d_now, d_prev, d_base_now, d_base_prev = date, bars[i - 1][0], bars[i - RS_WINDOW][0], bars[i - 1 - RS_WINDOW][0]
            if all(d in spy_closes for d in (d_now, d_prev, d_base_now, d_base_prev)):
                stock_ret_now = (c - bars[i - RS_WINDOW][4]) / bars[i - RS_WINDOW][4]
                spy_ret_now = (spy_closes[d_now] - spy_closes[d_base_now]) / spy_closes[d_base_now]
                excess_now = stock_ret_now - spy_ret_now
                prev_close = bars[i - 1][4]
                stock_ret_prev = (prev_close - bars[i - 1 - RS_WINDOW][4]) / bars[i - 1 - RS_WINDOW][4]
                spy_ret_prev = (spy_closes[d_prev] - spy_closes[d_base_prev]) / spy_closes[d_base_prev]
                excess_prev = stock_ret_prev - spy_ret_prev
                if excess_prev < RS_THRESHOLD <= excess_now:
                    yield i, date, "relative_strength"


def _gap_pct(bars, i):
    """Overnight gap: bar i's open vs bar i-1's close, as a fraction (0.02
    = +2%). Returns None for i==0 (no prior bar)."""
    if i == 0:
        return None
    return (bars[i][1] - bars[i - 1][4]) / bars[i - 1][4]


def run_backtest(start, end, regime=None,
                  setups=("breakout", "ema_cross", "mean_reversion", "vcp_breakout", "relative_strength"),
                  require_gap_pct=None, cost_pct=0.0):
    """cost_pct: fraction (e.g. 0.001 = 0.10%) subtracted from every
    trade's raw return to represent round-trip cost (spread + slippage +
    commission combined). Applied as a flat per-trade haircut, not as a
    change to entry/exit prices, since cost doesn't change WHICH of
    stop/target/time-stop fires first, only the net P&L once it does --
    safe to apply post-hoc rather than re-simulating exits. Default 0.0
    reproduces every prior backtest's numbers unchanged (all of which were
    gross-of-costs). See cost_sensitivity() below for sweeping this to
    find the breakeven cost that erases a setup's edge.

    regime: optional {date: bool} from _fetch_spy_regime -- when given,
    breakout/ema_cross signals are only counted on bullish-regime days
    (mean_reversion is exempt -- it's deliberately the counter-trend bet,
    applying a "don't fight the tape" filter to it would defeat the point).
    A signal on a date with no regime value yet (not enough SMA warmup) is
    dropped rather than assumed bullish or bearish.

    require_gap_pct: optional float (e.g. 0.02) -- when given, breakout/
    ema_cross signals are only counted if that day's open gapped up from
    the PRIOR day's close by at least this much. This is a PROXY for "a
    real dated catalyst drove this, not just gradual drift" -- added
    2026-09-07 because FMP's free tier has no historical earnings-calendar
    lookback (confirmed live: 402 Payment Required on any date more than
    ~a few weeks in the past), so verifying an actual news catalyst for
    each of 30,000+ historical signals isn't feasible at this tier. A
    genuine overnight gap is a reasonable, fully data-derived stand-in
    (real catalysts -- earnings, M&A, FDA news -- usually gap; routine
    technical drift usually doesn't) but it is NOT the same claim as
    "verified this ticker had real news that day" -- be honest about that
    distinction when reporting results. mean_reversion is exempt (a gap
    DOWN would be the relevant direction for a bounce setup, a different
    question not tested here)."""
    series = _load_series(start, end)
    results = {s: [] for s in setups}
    spy_closes = _spy_closes(start, end) if "relative_strength" in setups else None

    for ticker, bars in series.items():
        if len(bars) < 25:
            continue
        for i, date, setup in iter_signals(bars, spy_closes=spy_closes):
            if setup not in results:
                continue
            if regime is not None and setup != "mean_reversion":
                if date not in regime or not regime[date]:
                    continue
            if require_gap_pct is not None and setup != "mean_reversion":
                gap = _gap_pct(bars, i)
                if gap is None or gap < require_gap_pct:
                    continue
            r = _simulate_exit(bars, i)
            if r is not None:
                results[setup].append({"ticker": ticker, "date": date, "return": r - cost_pct})

    return results


def cost_sensitivity(start, end, setups=("breakout", "ema_cross", "mean_reversion", "vcp_breakout", "relative_strength"),
                      cost_levels_bps=(0, 2, 4, 6, 8, 10, 15, 20, 30, 50), regime=None):
    """Answers the question raised alongside every 'no edge' verdict in
    this project so far: is that conclusion final, or just 'no edge under
    a zero-cost assumption'? Reuses run_backtest() (and therefore whatever
    is already cached under CACHE_DIR -- no new network calls) at a sweep
    of round-trip cost assumptions (in basis points, 1bps = 0.01%) and
    reports, per setup, the highest cost level in this sweep whose avg
    return/trade is still positive -- i.e. a lower bound on the breakeven
    cost. A setup whose edge disappears at 2-4bps is fragile (that's
    below typical real-world spread+slippage for a liquid large-cap, let
    alone a small/mid-cap); one that survives 20-30bps is more robust to
    being wrong about costs.

    For scale: T212 itself charges no per-trade commission on this
    project's target instrument (US equities), so 'cost' here is
    effectively bid/ask spread + slippage only, not commission -- a
    liquid large-cap's spread is often 1-5bps, a thinner small/mid-cap
    name can be 10-50bps+. Compare the breakeven this prints against that
    range rather than assuming any single number."""
    print(f"\n=== COST SENSITIVITY: {start}..{end} ===")
    print("(round-trip cost in bps subtracted flat from every trade's return; "
          "0bps reproduces this project's existing gross-of-costs numbers)\n")
    breakeven = {s: None for s in setups}
    for bps in cost_levels_bps:
        results = run_backtest(start, end, regime=regime, setups=setups, cost_pct=bps / 10_000)
        row = []
        for setup, trades in results.items():
            n = len(trades)
            if n == 0:
                row.append(f"{setup}: 0 trades")
                continue
            avg_return = sum(t["return"] for t in trades) / n * 100
            if avg_return > 0:
                breakeven[setup] = bps
            row.append(f"{setup}: {avg_return:+.3f}%/trade (n={n})")
        print(f"  {bps:>3}bps: " + " | ".join(row))
    print("\nBreakeven (highest cost level tested still net positive; "
          "'0' means already negative even at zero cost; '>=' the top "
          "tested level means still positive at every level tried):")
    top = cost_levels_bps[-1]
    for setup, bps in breakeven.items():
        if bps is None:
            print(f"  {setup}: negative/flat even at 0bps cost -- cost sensitivity is moot, there's no edge to erode")
        elif bps == top:
            print(f"  {setup}: still positive at >={top}bps, the highest level tested -- extend cost_levels_bps to pin this down further")
        else:
            print(f"  {setup}: ~{bps}bps (positive at {bps}bps, flips negative at the next level tested)")


def _summarize(label, results):
    print(f"\n=== {label} ===")
    for setup, trades in results.items():
        n = len(trades)
        if n == 0:
            print(f"  {setup}: 0 trades in range")
            continue
        wins = [t for t in trades if t["return"] > 0]
        win_rate = len(wins) / n * 100
        avg_return = sum(t["return"] for t in trades) / n * 100
        print(f"  {setup}: {n} trades, win rate {win_rate:.1f}%, avg return/trade {avg_return:.2f}%")


def compare(start, end):
    """Runs and prints, side by side: the original unfiltered baseline
    (all 3 setups), a market-regime-filtered version of the two momentum
    setups (SPY above its 50-day SMA), and mean_reversion again on its own
    for clarity (it's identical to the baseline row -- regime filtering
    doesn't apply to it -- repeated here just so all "final" numbers are
    in one place). Answers: does a regime filter rescue the momentum
    setups, and does mean-reversion look more promising than either,
    given the same 2-year window/universe/exit-rule for a fair comparison."""
    global VCP_CONTRACTION_RATIO, RS_THRESHOLD
    baseline = run_backtest(start, end)
    _summarize("BASELINE (unfiltered)", baseline)

    regime = _fetch_spy_regime(start, end)
    regime_filtered = run_backtest(start, end, regime=regime, setups=("breakout", "ema_cross"))
    _summarize(f"REGIME-FILTERED (SPY > its {REGIME_SMA_WINDOW}-day SMA)", regime_filtered)

    bullish_days = sum(1 for v in regime.values() if v)
    print(f"\n(regime filter: {bullish_days}/{len(regime)} days in dataset were bullish per this filter)")

    for gap in (0.02, 0.05):
        gap_filtered = run_backtest(start, end, setups=("breakout", "ema_cross"), require_gap_pct=gap)
        _summarize(f"GAP-CONFIRMED (open gapped up >= {gap*100:.0f}% vs prior close -- catalyst PROXY, not verified news)", gap_filtered)

    print(f"\n(baseline row above already includes vcp_breakout at the default "
          f"{VCP_CONTRACTION_RATIO*100:.0f}% contraction ratio and relative_strength at "
          f"the default {RS_THRESHOLD*100:.0f}pp threshold -- sensitivity checks at other "
          f"thresholds follow)")

    orig_vcp, orig_rs = VCP_CONTRACTION_RATIO, RS_THRESHOLD
    for ratio in (0.6, 0.8):
        VCP_CONTRACTION_RATIO = ratio
        vcp_variant = run_backtest(start, end, setups=("vcp_breakout",))
        _summarize(f"VCP_BREAKOUT (contraction ratio {ratio})", vcp_variant)
    VCP_CONTRACTION_RATIO = orig_vcp

    for threshold in (0.10, 0.20):
        RS_THRESHOLD = threshold
        rs_variant = run_backtest(start, end, setups=("relative_strength",))
        _summarize(f"RELATIVE_STRENGTH (threshold {threshold*100:.0f}pp)", rs_variant)
    RS_THRESHOLD = orig_rs

    out_path = CACHE_DIR / f"compare_{start}_{end}.json"
    out_path.write_text(json.dumps({"baseline": baseline, "regime_filtered": regime_filtered}, indent=2))
    print(f"full trade lists written to {out_path}")


if __name__ == "__main__":
    cmd, start, end = sys.argv[1], sys.argv[2], sys.argv[3]
    if cmd == "fetch":
        fetch_range(start, end)
    elif cmd == "fetch_alpaca":
        fetch_range_alpaca(start, end)
    elif cmd == "backtest":
        results = run_backtest(start, end)
        _summarize("BASELINE (unfiltered)", results)
        out_path = CACHE_DIR / f"results_{start}_{end}.json"
        out_path.write_text(json.dumps(results, indent=2))
        print(f"\nfull trade list written to {out_path}")
    elif cmd == "compare":
        compare(start, end)
    elif cmd == "cost_sensitivity":
        cost_sensitivity(start, end)
    else:
        print("usage: backtest_ta.py [fetch|fetch_alpaca|backtest|compare|cost_sensitivity] START END")
