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
  python scripts/discord_alert_bridge.py parse "BUY $AAPL @ 182.5 SL 178 TP 190"
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
_NUM = r"\$?\s*(\d+(?:\.\d+)?)"
_SHORT_RE = re.compile(r"\b(short(?![\s-]term)|shorting|puts?)\b", re.I)
_OPTIONS_RE = re.compile(
    r"\b(calls?|puts?|strike|expiry|expiration|exp)\b|\b\d+(?:\.\d+)?[cp]\b", re.I)
_BUY_RE = re.compile(r"\b(buy|buying|bought|long|entry|entering|entered|adding)\b", re.I)
_CLOSE_RE = re.compile(
    r"\b(sell|selling|sold|close|closing|closed|exit|exiting|exited|stopped out|"
    r"cut|cutting)\b", re.I)
_ENTRY_RE = re.compile(r"(?:entry|buy|bought|long|price|@|\bat\b)\s*[:\-=]?\s*" + _NUM, re.I)
_STOP_RE = re.compile(r"(?:\bsl\b|stop[\s-]*loss|\bstop\b)\s*[:\-=@]?\s*(?:at\s*)?" + _NUM, re.I)
_TARGET_RE = re.compile(
    r"(?:\b(?:tp|pt|target)\d?\b|take[\s-]*profit)\s*[:\-=@]?\s*(?:at\s*)?" + _NUM,
    re.I)
_DOLLAR_TICKER_RE = re.compile(r"\$([A-Za-z]{1,5})\b")
_BARE_TICKER_RE = re.compile(r"\b([A-Z]{1,5})\b")
_NOT_TICKERS = {
    "BUY", "BUYING", "LONG", "SELL", "SL", "TP", "PT", "ENTRY", "STOP", "LOSS",
    "TARGET", "NOW", "AT", "USD", "ALERT", "NEW", "I", "A", "AM", "PM", "ET",
    "EST", "EDT", "UK", "US", "NYSE", "OTC", "ATH", "EOD", "HOD", "LOD", "DAY",
    "SWING", "CEO", "ER", "PR", "FDA", "IPO", "ETF", "RSI", "EMA", "SMA", "VWAP",
    "TP1", "TP2", "PT1", "PT2", "OR", "AND", "THE", "IN", "ON", "TO", "OF", "IT",
    "IS", "MY", "GO", "UP", "ALL", "OUT", "RISK", "SIZE", "HALF", "FULL", "NFA",
    "DYOR", "GL", "LFG", "IMO", "CLOSE", "EXIT", "HOLD", "WATCH", "NOTE",
}


def _first_num(rx, text):
    m = rx.search(text)
    return float(m.group(1)) if m else None


def _find_tickers(text):
    found = [t.upper() for t in _DOLLAR_TICKER_RE.findall(text)]
    if not found:
        found = [t for t in _BARE_TICKER_RE.findall(text) if t not in _NOT_TICKERS]
    seen, out = set(), []
    for t in found:
        if t not in seen and t not in _NOT_TICKERS:
            seen.add(t)
            out.append(t)
    return out


def parse_alert(text):
    """
    Turn one alert's text into an action. Conservative by design: anything
    ambiguous is "ignore" with a reason, because a missed alert costs nothing
    on a demo account and a misread one teaches the measurement something false.
    """
    raw = (text or "").strip()
    if not raw:
        return {"action": "ignore", "reason": "empty"}
    if _OPTIONS_RE.search(raw):
        return {"action": "ignore", "reason": "options alert (T212 API is shares only)"}
    if _SHORT_RE.search(raw):
        return {"action": "ignore", "reason": "short alert (long-only per Hard Risk Rules)"}

    buy_m, close_m = _BUY_RE.search(raw), _CLOSE_RE.search(raw)
    if not buy_m and not close_m:
        return {"action": "ignore", "reason": "no buy/close keyword"}
    # Whichever comes first decides, so "Buy X, sell at 200" stays a buy.
    if buy_m and (not close_m or buy_m.start() < close_m.start()):
        action = "buy"
    else:
        action = "close"

    tickers = _find_tickers(raw)
    if not tickers:
        return {"action": "ignore", "reason": f"{action} keyword but no ticker found"}
    if len(tickers) > 1:
        return {"action": "ignore",
                "reason": f"ambiguous: several tickers {tickers}", "tickers": tickers}

    out = {"action": action, "ticker": tickers[0]}
    if action == "buy":
        # Prices after a sell word ("buy X, sell at 450") are an exit level,
        # never the entry.
        head = raw[:close_m.start()] if close_m else raw
        entry = _first_num(_ENTRY_RE, head)
        stop = _first_num(_STOP_RE, raw)
        target = _first_num(_TARGET_RE, raw)
        if target is None and close_m:
            target = _first_num(re.compile(r"\bat\s*" + _NUM, re.I), raw[close_m.start():])
        # Reject levels that are inconsistent with a long; defaults apply later.
        if entry and stop and stop >= entry:
            stop = None
        if entry and target and target <= entry:
            target = None
        out.update({"entry": entry, "stop": stop, "target": target})
    return out


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
    if not os.environ.get("ALPACA_API_KEY"):
        return None
    sys.path.insert(0, str(ROOT / "scripts"))
    import alpaca_client
    return float(alpaca_client.get_latest_trade(symbol)["trade"]["p"])


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

    price = alert.get("entry") or latest_price(sym)
    if not price:
        return f"skipped {sym}: no entry price in alert and no price source configured"

    if DRY_RUN and not os.environ.get("T212_API_KEY"):
        total, free, invested, acct_ccy = 5000.0, 5000.0, 0.0, "USD"
        instr_ccy, t212_ticker = "USD", f"{sym}_US_EQ"
    else:
        t212 = _t212()
        inst = resolve_instrument(sym)
        if not inst:
            return f"skipped {sym}: no unique T212 instrument found"
        t212_ticker, instr_ccy = inst["ticker"], inst.get("currencyCode", "USD")
        cash = t212.get_account_cash()
        info = t212._get("/equity/account/info")
        total, free = float(cash["total"]), float(cash["free"])
        invested, acct_ccy = float(cash.get("invested", 0)), info.get("currencyCode", "USD")

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

        alert = parse_alert(text)
        try:
            if alert["action"] == "buy":
                result = handle_buy(alert, state, body)
            elif alert["action"] == "close":
                result = close_position(alert["ticker"], state, "close alert")
            else:
                result = f"ignored: {alert['reason']}"
        except Exception as e:  # noqa: BLE001
            # Per CLAUDE.md: if a T212 call errors, stop and log -- never retry blindly.
            result = f"ERROR, nothing retried: {e!r}"
            notify("Discord bridge error", f"{alert.get('ticker', '?')}: {e!r}")
        save_state(state)
    log_alert({"at": _now().isoformat(), "title": title, "text": text,
               "parsed": alert, "result": result, "dry_run": DRY_RUN})
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

            cash = t212.get_account_cash()
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
