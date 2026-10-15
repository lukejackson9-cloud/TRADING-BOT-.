"""
Discord alert bridge -> Trading 212 DEMO account.

WHY THIS SHAPE (2026-10-15): the user follows trade alerts in a plain text
channel of a Discord server they do not administer. A bot cannot be invited
without an admin, the channel is not an announcement channel (so it cannot be
"Followed" into a server the user owns), and logging in as the user with their
personal token ("self-bot") breaks Discord's terms and risks their account.
What the user DOES legitimately receive is the push notification on their
Android phone. A notification-forwarding app (Tasker + AutoNotification, or
any "notification to webhook" app) POSTs each Discord notification's text to
this server, which parses it and acts on the demo account.

This process runs on its own, with no Claude session in the loop -- it must
live on an always-on machine (a small VPS, or a PC left on). A Claude Code
cloud container is NOT suitable: it is reclaimed and has lost .env twice.

DEMO ONLY, ENFORCED IN CODE. Refuses to start unless T212_BASE_URL points at
demo.trading212.com. Live execution needs a separate explicit user decision
(CLAUDE.md "Trade execution & approval") and is deliberately not supported.

The four safeguards CLAUDE.md makes mandatory for ANY automatic execution are
implemented here, not just documented:
  1. Every fill (open or close) -> push notification (ntfy.sh) + data/trades.log.
  2. Daily-loss circuit breaker: account total down >= BRIDGE_DAILY_LOSS_PCT
     (default and maximum 5%) from the day's start -> pause new entries, notify.
     Never resumes itself: `python scripts/discord_alert_bridge.py resume`.
  3. Hard Risk Rules at order time: <=5% of account per position, <=50% total
     invested, long only (shorts/puts/options alerts are logged and skipped).
     Env overrides can only TIGHTEN these, never loosen them.
  4. Correlation check: one position per ticker, and at most
     BRIDGE_MAX_PER_SECTOR open bridge positions sharing an SIC industry
     (looked up via Massive when MASSIVE_API_KEY is set; if it is not, the
     check degrades to per-ticker only and says so in every entry log line).

BRIDGE_DRY_RUN defaults to ON. In dry-run every alert is parsed, sized and
logged exactly as it would be traded, but no order is sent. Leave it on until
the parser has been checked against real alerts from the channel.

Environment:
  T212_API_KEY, T212_API_SECRET, T212_BASE_URL (demo)    required to trade
  BRIDGE_SECRET            required; shared secret the phone sends
  BRIDGE_PORT              default 8787
  BRIDGE_DRY_RUN           default "1"; set "0" to place demo orders
  BRIDGE_CHANNEL_FILTER    optional; substring the notification title must
                           contain (e.g. "#alerts"), so other Discord
                           notifications are ignored
  NTFY_TOPIC               optional; ntfy.sh topic for push notifications
  BRIDGE_MAX_POSITION_PCT  default 0.05 (capped at 0.05)
  BRIDGE_MAX_EXPOSURE_PCT  default 0.50 (capped at 0.50)
  BRIDGE_DAILY_LOSS_PCT    default 0.05 (capped at 0.05)
  BRIDGE_DEFAULT_STOP_PCT  default 0.04  (used when an alert gives no stop)
  BRIDGE_DEFAULT_TARGET_PCT default 0.08 (used when an alert gives no target)
  BRIDGE_MAX_PER_SECTOR    default 2
  ALPACA_API_KEY/SECRET    optional; price source when an alert has no entry
  MASSIVE_API_KEY          optional; SIC industry for the correlation check
  BRIDGE_FX_GBP_USD        optional fallback FX rate if frankfurter.app is unreachable

Phone side: POST http://<server>:<port>/alert with header
  X-Bridge-Secret: <BRIDGE_SECRET>
and JSON body {"title": "<notification title>", "text": "<notification text>"}
(a raw text body is accepted too). GET /health returns "ok".

CLI:
  python scripts/discord_alert_bridge.py serve
  python scripts/discord_alert_bridge.py parse "Bought more IREN at 26.8 and CRWV at 59.9"
  python scripts/discord_alert_bridge.py status
  python scripts/discord_alert_bridge.py resume
"""

import datetime as dt
import hashlib
import hmac
import json
import math
import os
import queue
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "data" / "discord_bridge"
STATE_PATH = STATE_DIR / "state.json"
ALERT_LOG = STATE_DIR / "alerts.jsonl"
TRADES_LOG = ROOT / "data" / "trades.log"

# Hard Risk Rules ceilings (CLAUDE.md). Env may tighten, never loosen.
HARD_MAX_POSITION_PCT = 0.05
HARD_MAX_EXPOSURE_PCT = 0.50
HARD_MAX_DAILY_LOSS_PCT = 0.05


def _env_pct(name, default, ceiling):
    try:
        val = float(os.environ.get(name, default))
    except ValueError:
        val = default
    return max(0.0, min(val, ceiling))


MAX_POSITION_PCT = _env_pct("BRIDGE_MAX_POSITION_PCT", 0.05, HARD_MAX_POSITION_PCT)
MAX_EXPOSURE_PCT = _env_pct("BRIDGE_MAX_EXPOSURE_PCT", 0.50, HARD_MAX_EXPOSURE_PCT)
DAILY_LOSS_PCT = _env_pct("BRIDGE_DAILY_LOSS_PCT", 0.05, HARD_MAX_DAILY_LOSS_PCT)
DEFAULT_STOP_PCT = _env_pct("BRIDGE_DEFAULT_STOP_PCT", 0.04, 0.50)
DEFAULT_TARGET_PCT = _env_pct("BRIDGE_DEFAULT_TARGET_PCT", 0.08, 5.0)
MAX_PER_SECTOR = int(os.environ.get("BRIDGE_MAX_PER_SECTOR", "2"))
DRY_RUN = os.environ.get("BRIDGE_DRY_RUN", "1") != "0"
CHANNEL_FILTER = os.environ.get("BRIDGE_CHANNEL_FILTER", "").strip().lower()
MONITOR_INTERVAL_S = 60
DEDUPE_WINDOW_S = 600

_state_lock = threading.Lock()


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------
# Written against the user's real "Saucy Stocks" channel (screenshots,
# 2026-10-15). Alerts are casual prose, not a fixed format:
#   "ASTS is a buy here if you don't have ..."                 -> buy ASTS
#   "Added into the rest of my WDC position, my new avg is 392" -> buy WDC
#   "Closed NBIL at 17.4 and FPSX 3.7, I'm planning to hold VSH for a while"
#                                       -> close NBIL, close FPSX, NOT VSH
#   "Bought more IREN at 26.8 lowering my avg to 33 and CRWV at 59.9 my avg
#    is 69 now"                                                 -> buy IREN, CRWV
#   "RKLB at 54 is a buy, my average is way lower so I won't be adding ..."
# Prices in them are often the author's AVERAGE, not today's price, so sizing
# always prefers a live quote; an "at <price>" is only a fallback.
# The same author runs an OPTIONS channel ("GOOGL 352.5c 1.53 10/16"). Trading
# 212 cannot trade options and the user chose the stocks channel instead, so
# any option-contract alert is ignored outright -- if its notifications ever
# get forwarded too, they must not turn into share trades.
_NUM = r"\$?\s*(\d+(?:\.\d+)?)"
_CONTRACT_RE = re.compile(r"(?<![\w.])\d+(?:\.\d+)?[cp]\b|\b(calls?|puts?|strike|expiry)\b", re.I)
_RECAP_RE = re.compile(r"\b(recap|summary|watchlist|positions? update)\b", re.I)
_SHORT_RE = re.compile(r"\b(short(?![\s-]term)|shorting|shorted)\b", re.I)
_NEGATED_BUY_RE = re.compile(
    r"\b(not a buy|wouldn'?t buy|don'?t buy|do not buy|avoid|stay away)\b", re.I)
_BUY_RE = re.compile(
    r"\b(buy|buying|bought|long|entry|entering|entered|add|added|adding|"
    r"starting a position|started a position|opened)\b", re.I)
_TRIM_RE = re.compile(
    r"\b(trim|trimmed|trimming|took (?:some )?profits?|sold (?:some|half|part)|"
    r"selling (?:some|half|part)|scal(?:ed|ing) out)\b", re.I)
_CLOSE_RE = re.compile(
    r"\b(sell|selling|sold|close|closing|closed|exit|exiting|exited|stopped out|"
    r"cut|cutting|out of)\b", re.I)
_HOLD_RE = re.compile(r"\b(hold|holding|keep|keeping|still in|watching|watch)\b", re.I)
_AT_PRICE_RE = re.compile(r"\bat\s*" + _NUM, re.I)
_STOP_RE = re.compile(r"(?:\bsl\b|stop[\s-]*loss|\bstop\b)\s*[:\-=@]?\s*(?:at\s*)?" + _NUM, re.I)
_TARGET_RE = re.compile(
    r"(?:\b(?:tp|pt|target)\d?\b|take[\s-]*profit)\s*[:\-=@]?\s*(?:at\s*)?" + _NUM, re.I)
_TICKER_RE = re.compile(r"\$([A-Za-z]{1,5})\b|\b([A-Z]{1,5})\b")
_CLAUSE_SPLIT_RE = re.compile(r"\n+|[;,.!?](?!\d)\s*|\s+\band\b\s+", re.I)
_NOT_TICKERS = {
    "I", "A", "AM", "PM", "ET", "EST", "EDT", "UK", "US", "USA", "SL", "TP", "PT",
    "NFA", "DYOR", "IMO", "IMHO", "ATH", "ATL", "EOD", "HOD", "LOD", "DCA", "AI",
    "EV", "CPI", "PPI", "FOMC", "FED", "GDP", "NFP", "ER", "PR", "FDA", "IPO", "ETF",
    "CEO", "CFO", "RSI", "EMA", "SMA", "MA", "VWAP", "OTC", "NYSE", "LFG", "GL",
    "OK", "TBH", "BTW", "FYI", "LOL", "ALL", "NEW", "BUY", "SELL", "LONG", "STOP",
    "AND", "THE", "OR", "IT", "IS", "ON", "IN", "AT", "TO", "MY", "UP", "NOW",
}


def _tickers(clause):
    out = []
    for m in _TICKER_RE.finditer(clause):
        t = (m.group(1) or m.group(2)).upper()
        if t not in _NOT_TICKERS and t not in out:
            out.append(t)
    return out


def _clause_action(clause):
    """buy / trim / close / hold / None, by whichever keyword comes first."""
    if _NEGATED_BUY_RE.search(clause):
        return "hold"
    hits = []
    for kind, rx in (("trim", _TRIM_RE), ("close", _CLOSE_RE), ("buy", _BUY_RE),
                     ("hold", _HOLD_RE)):
        m = rx.search(clause)
        if m:
            hits.append((m.start(), kind))
    # A trim phrase ("sold some") also matches the close word "sold"; same start
    # position, so the sort keeps trim because it was appended first.
    return sorted(hits, key=lambda h: h[0])[0][1] if hits else None


def _first_num(rx, text):
    m = rx.search(text)
    return float(m.group(1)) if m else None


def parse_alert(text):
    """
    Turn one alert into a LIST of actions (one message can close two names).
    Conservative: anything unclear is "ignore" with a reason, because a missed
    alert costs nothing on a demo account and a misread one records a trade
    the author never made.
    """
    raw = (text or "").strip()
    if not raw:
        return [{"action": "ignore", "reason": "empty"}]
    if _RECAP_RE.search(raw):
        return [{"action": "ignore", "reason": "recap/summary message, never traded"}]
    if _CONTRACT_RE.search(raw):
        return [{"action": "ignore", "reason": "options alert (T212 is shares only)"}]
    if _SHORT_RE.search(raw):
        return [{"action": "ignore", "reason": "short alert (long-only per Hard Risk Rules)"}]

    actions, seen, prev = [], set(), None
    for clause in filter(None, (c.strip() for c in _CLAUSE_SPLIT_RE.split(raw))):
        tickers = _tickers(clause)
        kind = _clause_action(clause)
        if kind is None and tickers and prev in ("buy", "close", "trim") \
                and _tickers(clause.split()[0]) == tickers[:1]:
            # "Closed NBIL at 17.4 and FPSX 3.7": a verbless clause that STARTS
            # with a ticker continues the previous verb. "I'm planning to hold
            # VSH" does not start with one, and says hold anyway.
            kind = prev
        if kind:
            prev = kind
        if kind not in ("buy", "close", "trim") or not tickers:
            continue
        if len(tickers) > 1:
            actions.append({"action": "ignore",
                            "reason": f"ambiguous clause, several tickers {tickers}: {clause!r}"})
            continue
        t = tickers[0]
        if t in seen:
            continue
        seen.add(t)
        a = {"action": kind, "ticker": t}
        if kind == "buy":
            a.update({"entry": _first_num(_AT_PRICE_RE, clause),
                      "stop": _first_num(_STOP_RE, clause),
                      "target": _first_num(_TARGET_RE, clause)})
            e = a["entry"]
            if e and a["stop"] and a["stop"] >= e:
                a["stop"] = None
            if e and a["target"] and a["target"] <= e:
                a["target"] = None
        actions.append(a)
    return actions or [{"action": "ignore", "reason": "no buy/close/trim with a ticker"}]


# --------------------------------------------------------------------------
# State, logging, notifications
# --------------------------------------------------------------------------
def _now():
    return dt.datetime.now(dt.timezone.utc)


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"paused": False, "pause_reason": None, "day": None,
            "day_start_total": None, "positions": {}, "recent_hashes": {}}


def save_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_PATH)


def log_alert(record):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with ALERT_LOG.open("a") as f:
        f.write(json.dumps(record) + "\n")


def log_trade(line):
    TRADES_LOG.parent.mkdir(parents=True, exist_ok=True)
    with TRADES_LOG.open("a") as f:
        f.write(f"{_now().isoformat()} [discord_bridge{' DRY-RUN' if DRY_RUN else ''}] {line}\n")


def notify(title, message):
    """Push to the user's phone via ntfy.sh. Never raises: a failed push is
    logged, and must not stop a stop-loss from executing."""
    print(f"[notify] {title}: {message}", flush=True)
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        return
    try:
        requests.post(f"https://ntfy.sh/{topic}", data=message.encode(),
                      headers={"Title": title}, timeout=10)
    except Exception as e:  # noqa: BLE001
        print(f"[notify] push failed: {e}", flush=True)


# --------------------------------------------------------------------------
# Broker / data access (imported lazily so `parse` works without credentials)
# --------------------------------------------------------------------------
def _t212():
    base = os.environ.get("T212_BASE_URL", "https://demo.trading212.com/api/v0")
    if "demo.trading212.com" not in base:
        raise RuntimeError(f"REFUSING: T212_BASE_URL is not the demo endpoint ({base})")
    sys.path.insert(0, str(ROOT / "scripts"))
    import trading212_client as t212
    return t212


_instrument_cache = {"at": 0, "data": None}
_acct = {"ccy": None, "cash_at": 0.0}
# T212 rate-limits account endpoints (measured 2026-10-15: a second /cash call
# right after the first returned 429). Pacing, not retrying: one alert can name
# two tickers, and each needs a fresh balance.
CASH_MIN_INTERVAL_S = 5.0


def account_currency():
    if not _acct["ccy"]:
        _acct["ccy"] = _t212()._get("/equity/account/info").get("currencyCode", "USD")
    return _acct["ccy"]


def account_cash():
    wait = CASH_MIN_INTERVAL_S - (time.time() - _acct["cash_at"])
    if wait > 0:
        time.sleep(wait)
    try:
        return _t212().get_account_cash()
    finally:
        _acct["cash_at"] = time.time()


def resolve_instrument(symbol):
    """Exact T212 instrument for a US ticker, never a guessed suffix."""
    t212 = _t212()
    if not _instrument_cache["data"] or time.time() - _instrument_cache["at"] > 86400:
        _instrument_cache["data"] = t212._get("/equity/metadata/instruments")
        _instrument_cache["at"] = time.time()
    insts = _instrument_cache["data"]
    for i in insts:
        if i.get("ticker") == f"{symbol}_US_EQ":
            return i
    matches = [i for i in insts if (i.get("shortName") or "").upper() == symbol
               and i.get("type") == "STOCK"]
    return matches[0] if len(matches) == 1 else None


def latest_price(symbol):
    """Live share price: Alpaca when keyed, else Yahoo's keyless chart endpoint
    (unofficial -- see yahoo_screener_client.py; needs a User-Agent)."""
    if os.environ.get("ALPACA_API_KEY"):
        sys.path.insert(0, str(ROOT / "scripts"))
        import alpaca_client
        return float(alpaca_client.get_latest_trade(symbol)["trade"]["p"])
    r = requests.get(f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}",
                     params={"interval": "1m", "range": "1d"},
                     headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    r.raise_for_status()
    px = r.json()["chart"]["result"][0]["meta"].get("regularMarketPrice")
    return float(px) if px else None


def fx_rate(from_ccy, to_ccy):
    """Units of to_ccy per 1 from_ccy."""
    if from_ccy == to_ccy:
        return 1.0
    try:
        r = requests.get("https://api.frankfurter.app/latest",
                         params={"from": from_ccy, "to": to_ccy}, timeout=10)
        r.raise_for_status()
        return float(r.json()["rates"][to_ccy])
    except Exception:  # noqa: BLE001
        # Manual fallback, e.g. BRIDGE_FX_GBP_USD=1.27. With neither source the
        # trade errors out (logged + pushed) rather than sizing on a guess.
        override = os.environ.get(f"BRIDGE_FX_{from_ccy}_{to_ccy}")
        if override:
            return float(override)
        raise


def sector_of(symbol):
    if not os.environ.get("MASSIVE_API_KEY"):
        return None
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        import massive_client
        res = massive_client._get(f"/v3/reference/tickers/{symbol}").get("results", {})
        return res.get("sic_description")
    except Exception:  # noqa: BLE001
        return None


# --------------------------------------------------------------------------
# Actions
# --------------------------------------------------------------------------
def handle_buy(alert, state, source_text):
    sym = alert["ticker"]
    if state["paused"]:
        return f"skipped {sym}: auto-trading PAUSED ({state['pause_reason']})"
    if sym in state["positions"]:
        return f"skipped {sym}: already holding a bridge position"

    sector = sector_of(sym)
    sector_note = sector or "sector unknown (per-ticker check only)"
    if sector:
        same = [p for p in state["positions"].values() if p.get("sector") == sector]
        if len(same) >= MAX_PER_SECTOR:
            return (f"skipped {sym}: correlation cap, already {len(same)} open in "
                    f"'{sector}' ({', '.join(p['ticker'] for p in same)})")

    # Live quote first: alert prices are often the author's average, not today's.
    try:
        price = latest_price(sym)
    except Exception:  # noqa: BLE001
        price = None
    price = price or alert.get("entry")
    if not price:
        return f"skipped {sym}: no live price and no price in the alert"

    if DRY_RUN and not os.environ.get("T212_API_KEY"):
        total, free, invested, acct_ccy = 5000.0, 5000.0, 0.0, "USD"
        instr_ccy, t212_ticker = "USD", f"{sym}_US_EQ"
    else:
        t212 = _t212()
        inst = resolve_instrument(sym)
        if not inst:
            return f"skipped {sym}: no unique T212 instrument found"
        t212_ticker, instr_ccy = inst["ticker"], inst.get("currencyCode", "USD")
        cash = account_cash()
        total, free = float(cash["total"]), float(cash["free"])
        invested, acct_ccy = float(cash.get("invested", 0)), account_currency()

    if DRY_RUN:
        # No real fills in dry-run, so count the simulated book against the caps.
        sim = sum(p.get("cost_acct", 0) for p in state["positions"].values())
        invested, free = invested + sim, free - sim
    budget = min(total * MAX_POSITION_PCT, free)
    if invested + budget > total * MAX_EXPOSURE_PCT:
        budget = total * MAX_EXPOSURE_PCT - invested
    if budget <= 0:
        return f"skipped {sym}: total exposure cap ({MAX_EXPOSURE_PCT:.0%}) reached"

    budget_instr = budget * fx_rate(acct_ccy, instr_ccy)
    qty = math.floor(budget_instr / price * 1000) / 1000
    if qty <= 0:
        return f"skipped {sym}: position too small to size"

    stop = alert.get("stop") or round(price * (1 - DEFAULT_STOP_PCT), 4)
    target = alert.get("target") or round(price * (1 + DEFAULT_TARGET_PCT), 4)

    order_id = None
    if not DRY_RUN:
        resp = _t212().place_market_order(t212_ticker, qty)
        order_id = resp.get("id")

    state["positions"][sym] = {
        "ticker": sym, "t212_ticker": t212_ticker, "qty": qty, "entry_ref": price,
        "stop": stop, "target": target, "sector": sector, "order_id": order_id,
        "cost_acct": round(budget, 2),
        "opened_at": _now().isoformat(), "source": source_text[:500],
        "dry_run": DRY_RUN,
    }
    msg = (f"BUY {qty} {sym} ~{price} ({budget:.2f} {acct_ccy}, "
           f"{budget / total:.1%} of account) stop {stop} target {target}; {sector_note}")
    log_trade(msg)
    notify(f"{'[DRY RUN] ' if DRY_RUN else ''}Demo BUY {sym}", msg)
    return msg


def close_position(sym, state, why):
    pos = state["positions"].get(sym)
    if not pos:
        return f"no bridge position in {sym} to close"
    if not DRY_RUN:
        _t212().place_market_order(pos["t212_ticker"], -pos["qty"])
    del state["positions"][sym]
    msg = f"SELL {pos['qty']} {sym} ({why})"
    log_trade(msg)
    notify(f"{'[DRY RUN] ' if DRY_RUN else ''}Demo SELL {sym}", msg)
    return msg


def trim_position(sym, state, why):
    """Their trims never state a size, so sell half (the whole thing if tiny)."""
    pos = state["positions"].get(sym)
    if not pos:
        return f"no bridge position in {sym} to trim"
    half = math.floor(pos["qty"] / 2 * 1000) / 1000
    if half <= 0 or pos["qty"] - half <= 0:
        return close_position(sym, state, why)
    if not DRY_RUN:
        _t212().place_market_order(pos["t212_ticker"], -half)
    pos["qty"] = round(pos["qty"] - half, 3)
    msg = f"SELL {half} {sym} (half, {why}); {pos['qty']} left"
    log_trade(msg)
    notify(f"{'[DRY RUN] ' if DRY_RUN else ''}Demo TRIM {sym}", msg)
    return msg


def process_notification(title, text):
    """Entry point for one forwarded notification. Returns a result string."""
    if CHANNEL_FILTER and CHANNEL_FILTER not in (title or "").lower():
        return "ignored: not from the configured channel"
    body = f"{title or ''}\n{text or ''}".strip()
    digest = hashlib.sha256(body.encode()).hexdigest()
    with _state_lock:
        state = load_state()
        now = time.time()
        state["recent_hashes"] = {h: t for h, t in state["recent_hashes"].items()
                                  if now - t < DEDUPE_WINDOW_S}
        if digest in state["recent_hashes"]:
            return "ignored: duplicate notification"
        state["recent_hashes"][digest] = now

        alerts = parse_alert(text)
        results = []
        for alert in alerts:
            try:
                if alert["action"] == "buy":
                    results.append(handle_buy(alert, state, body))
                elif alert["action"] == "close":
                    results.append(close_position(alert["ticker"], state, "close alert"))
                elif alert["action"] == "trim":
                    results.append(trim_position(alert["ticker"], state, "trim alert"))
                else:
                    results.append(f"ignored: {alert['reason']}")
            except Exception as e:  # noqa: BLE001
                # Per CLAUDE.md: if a T212 call errors, stop and log -- never retry blindly.
                results.append(f"ERROR, nothing retried: {e!r}")
                notify("Discord bridge error", f"{alert.get('ticker', '?')}: {e!r}")
        result = " | ".join(results)
        save_state(state)
    log_alert({"at": _now().isoformat(), "title": title, "text": text,
               "parsed": alerts, "result": result, "dry_run": DRY_RUN})
    print(f"[alert] {result}", flush=True)
    return result


# --------------------------------------------------------------------------
# Monitor: stops, targets, daily-loss circuit breaker
# --------------------------------------------------------------------------
def monitor_once():
    with _state_lock:
        state = load_state()
        if not state["positions"] and DRY_RUN:
            return
        prices = {}
        if DRY_RUN:
            for sym in state["positions"]:
                try:
                    prices[sym] = latest_price(sym)
                except Exception:  # noqa: BLE001
                    prices[sym] = None
        else:
            t212 = _t212()
            for p in t212.get_portfolio():
                prices[p["ticker"]] = float(p["currentPrice"])
            prices = {sym: prices.get(pos["t212_ticker"])
                      for sym, pos in state["positions"].items()}

            cash = account_cash()
            total = float(cash["total"])
            today = _now().date().isoformat()
            if state["day"] != today:
                state["day"], state["day_start_total"] = today, total
            start = state["day_start_total"]
            if (not state["paused"] and start
                    and total <= start * (1 - DAILY_LOSS_PCT)):
                state["paused"] = True
                state["pause_reason"] = (f"daily loss {total / start - 1:.2%} on {today} "
                                         f"(limit -{DAILY_LOSS_PCT:.0%})")
                log_trade(f"CIRCUIT BREAKER: {state['pause_reason']}")
                notify("Auto-trading PAUSED", state["pause_reason"] +
                       ". Open positions still exit on stop/target. "
                       "Run `discord_alert_bridge.py resume` to re-enable.")

        for sym, pos in list(state["positions"].items()):
            px = prices.get(sym)
            if px is None:
                continue
            if px <= pos["stop"]:
                close_position(sym, state, f"stop hit at {px}")
            elif px >= pos["target"]:
                close_position(sym, state, f"target hit at {px}")
        save_state(state)


def _monitor_loop():
    while True:
        try:
            monitor_once()
        except Exception as e:  # noqa: BLE001
            print(f"[monitor] error: {e!r}", flush=True)
        time.sleep(MONITOR_INTERVAL_S)


# --------------------------------------------------------------------------
# HTTP server
# --------------------------------------------------------------------------
_work = queue.Queue()


def _worker():
    while True:
        title, text = _work.get()
        try:
            process_notification(title, text)
        except Exception as e:  # noqa: BLE001
            print(f"[worker] error: {e!r}", flush=True)


class Handler(BaseHTTPRequestHandler):
    def _reply(self, code, body):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        self._reply(200, "ok") if self.path == "/health" else self._reply(404, "not found")

    def do_POST(self):
        if not self.path.startswith("/alert"):
            return self._reply(404, "not found")
        secret = os.environ["BRIDGE_SECRET"]
        given = self.headers.get("X-Bridge-Secret", "")
        if not hmac.compare_digest(given.encode(), secret.encode()):
            return self._reply(403, "forbidden")
        length = min(int(self.headers.get("Content-Length", 0)), 20000)
        raw = self.rfile.read(length).decode("utf-8", "replace")
        try:
            body = json.loads(raw)
            title, text = body.get("title", ""), body.get("text", "")
        except (json.JSONDecodeError, AttributeError):
            title, text = "", raw
        _work.put((title, text))
        self._reply(200, "queued")

    def log_message(self, *args):
        pass


def serve():
    if not os.environ.get("BRIDGE_SECRET"):
        sys.exit("BRIDGE_SECRET is not set; refusing to expose an order-placing endpoint without it.")
    if not DRY_RUN:
        _t212()  # raises unless the demo endpoint is configured
        for k in ("T212_API_KEY", "T212_API_SECRET"):
            if not os.environ.get(k):
                sys.exit(f"{k} is not set; cannot trade. Set BRIDGE_DRY_RUN=1 to test parsing.")
    port = int(os.environ.get("BRIDGE_PORT", "8787"))
    threading.Thread(target=_worker, daemon=True).start()
    threading.Thread(target=_monitor_loop, daemon=True).start()
    print(f"Discord alert bridge on :{port}  dry_run={DRY_RUN}  "
          f"pos<={MAX_POSITION_PCT:.0%} exposure<={MAX_EXPOSURE_PCT:.0%} "
          f"daily_loss<={DAILY_LOSS_PCT:.0%}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "serve"
    if cmd == "serve":
        serve()
    elif cmd == "parse":
        print(json.dumps(parse_alert(" ".join(argv[2:])), indent=2))
    elif cmd == "status":
        print(json.dumps({k: v for k, v in load_state().items() if k != "recent_hashes"},
                         indent=2))
    elif cmd == "resume":
        with _state_lock:
            state = load_state()
            state["paused"], state["pause_reason"] = False, None
            save_state(state)
        log_trade("RESUMED by user")
        print("Auto-trading resumed.")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
