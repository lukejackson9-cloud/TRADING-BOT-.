"""
Reads TradingView webhook alerts relayed through a Zapier bridge into a
published Google Sheet (TradingView has no way to receive webhooks
itself in this project, and this session's own webhook mechanism only
accepts signed requests from Anthropic's artifact service -- see
HANDOFF.md's 2026-09-07 entry for why this bridge exists at all).

Flow: TradingView alert --webhook--> Zapier "Catch Hook" --> Zapier
"Google Sheets: Create Spreadsheet Row" --> a Sheet published to the web
as CSV --> this script polls that CSV over plain HTTP (no Google auth
needed -- "publish to web" makes it a public, unauthenticated URL, so
there's no credential to manage here at all).

Requires env var: TRADINGVIEW_ALERTS_CSV_URL (the published-CSV URL from
the Google Sheet -- see skills/ or HANDOFF.md for the full setup steps on
the user's side: Sheet -> Zapier -> TradingView alert webhook).

Sheet is expected to have a header row: Timestamp, Ticker, Message (the
exact columns Zapier's Google Sheets action was configured to write --
if the user's Zap maps different column names, update HEADER below to
match, don't assume).

Cursor file (data/reference/tradingview_alerts_cursor.json, gitignored --
regenerable state, not project memory) tracks how many rows have already
been processed, so repeated polls only return genuinely NEW alerts
instead of replaying the whole sheet every time.
"""

import os
import csv
import json
import io
from pathlib import Path

import requests

CSV_URL = os.environ.get("TRADINGVIEW_ALERTS_CSV_URL")
CURSOR_PATH = Path("data/reference/tradingview_alerts_cursor.json")
HEADER = ["Timestamp", "Ticker", "Message"]


def _load_cursor():
    if CURSOR_PATH.exists():
        return json.loads(CURSOR_PATH.read_text()).get("rows_seen", 0)
    return 0


def _save_cursor(rows_seen):
    CURSOR_PATH.parent.mkdir(parents=True, exist_ok=True)
    CURSOR_PATH.write_text(json.dumps({"rows_seen": rows_seen}))


def get_new_alerts():
    """
    Fetches the published CSV and returns only rows appended since the
    last call (as a list of dicts keyed by HEADER). Raises RuntimeError
    if TRADINGVIEW_ALERTS_CSV_URL isn't set -- this integration is opt-in,
    callers (e.g. a routine) should catch that and skip quietly rather
    than erroring a whole pipeline run if the user hasn't finished setup
    yet.

    NOTE: if a row is ever deleted/reordered in the Sheet, this simple
    row-count cursor will misbehave (skip or replay rows) -- fine for an
    append-only alert log (the expected use), not safe if the user starts
    manually editing the sheet's existing rows.
    """
    if not CSV_URL:
        raise RuntimeError("TRADINGVIEW_ALERTS_CSV_URL not set -- alert bridge not configured yet")

    resp = requests.get(CSV_URL, timeout=15)
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.text))
    rows = list(reader)

    rows_seen = _load_cursor()
    new_rows = rows[rows_seen:]
    _save_cursor(len(rows))
    return new_rows


if __name__ == "__main__":
    # quick manual sanity check -- does NOT reset the cursor, so running
    # this twice in a row will correctly show 0 new alerts the second time
    try:
        alerts = get_new_alerts()
        print(f"{len(alerts)} new alert(s)")
        for a in alerts:
            print(a)
    except RuntimeError as e:
        print(e)
