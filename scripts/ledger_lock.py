"""
Shared file-locking for the JSON paper-trade ledgers (data/paper_trades.json,
data/ict_paper_trades.json) that scripts/paper_trader.py,
scripts/ict_paper_trader.py, and scripts/tag_catalyst.py all
read-modify-write independently, as separate process invocations.

Without locking, two callers running around the same time -- confirmed
live 2026-09-16, when 8 parallel catalyst-tagging subagents each ran
`tag_catalyst.py tag ...` concurrently against the same file -- both
read the pre-write state, then whichever saves last silently overwrites
the other's change. This cost one ticker's tag (MPC) that day; it was
only caught by a manual post-hoc audit comparing every agent's reported
determination against the actual file, not by the script itself.

`locked_ledger(path)` fixes this by wrapping a read-modify-write cycle in
an OS-level advisory lock (fcntl.flock) held on a companion `.lock` file,
so a second concurrent caller blocks until the first finishes instead of
racing it. The write itself goes through a temp file + os.replace() (an
atomic rename on POSIX), so any caller reading the ledger WITHOUT taking
the lock (e.g. tag_catalyst.py's `pending`/`report`, which only read)
still never observes a half-written file.

Usage:
    with locked_ledger(LEDGER_PATH) as ledger:
        ledger.append(...)   # or mutate existing dicts in place
    # written back automatically on exit, while still holding the lock

Mutate the yielded list/dicts in place -- don't rebind the variable to a
new list -- since what gets written back is that same object.
"""

import fcntl
import json
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def locked_ledger(path: Path):
    lock_path = path.with_name(path.name + ".lock")
    lock_path.touch(exist_ok=True)
    with open(lock_path, "r+") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            data = json.loads(path.read_text()) if path.exists() else []
            yield data
            tmp_path = path.with_name(path.name + ".tmp")
            tmp_path.write_text(json.dumps(data, indent=2))
            tmp_path.replace(path)  # atomic on POSIX -- unlocked readers never see a partial file
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
