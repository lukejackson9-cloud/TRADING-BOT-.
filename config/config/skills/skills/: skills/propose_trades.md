# Skill: Propose Trades

Goal: turn CANDIDATE research notes into a fully-specified, human-readable
trade proposal — WITHOUT sending any order. This is as far as any automated
routine is allowed to go.

## Preconditions
- /data/research/{today}/{TICKER}.md exists and Verdict == CANDIDATE

## Steps
1. Pull account cash/value via `scripts/trading212_client.py get_account_cash()`.
2. Pull current positions via `get_portfolio()` to check existing exposure.
3. Look up the exact T212 ticker via `lookup_instrument()` — never guess the
   ticker suffix.
4. Compute a proposed position size = min(5% of account value, available
   cash) at current price. Round to a sensible quantity (T212 supports
   fractional shares).
5. Compute a suggested stop-loss (-4%) and take-profit (+8%) level. Note:
   these are informational only — T212's live order types are currently
   limited (see scripts/trading212_client.py notes), so stops/targets may
   need to be monitored manually via skills/monitor.md rather than attached
   to the order automatically. Check current T212 docs before assuming
   otherwise.
6. Append the proposal to /data/pending_trades.json as a new entry:
   ```json
   {
     "id": "2026-09-02-NVDA-01",
     "ticker": "NVDA_US_EQ",
     "action": "BUY",
     "quantity": 3.2,
     "est_price": 187.40,
     "suggested_stop": 179.90,
     "suggested_target": 202.40,
     "research_file": "/data/research/2026-09-02/NVDA.md",
     "status": "PENDING_APPROVAL",
     "proposed_at": "2026-09-02T14:03:00Z"
   }
scripts/clickup_client.py post_report()
Hard rule
This skill NEVER calls place_market_order() or place_limit_order().
It only ever writes to /data/pending_trades.json and notifies via ClickUp.
