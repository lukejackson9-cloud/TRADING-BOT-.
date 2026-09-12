#!/bin/bash
# Keep this session on the current code before it does anything.
#
# WHY: the daily routines fire into a long-lived session that works from its
# own checkout. On 2026-09-12 that meant a merged bug fix (the IEX volume
# floor) and a rewritten CLAUDE.md were sitting in the repo while the session
# that actually trades kept running the old copy. A stale checkout is not a
# visible failure -- it silently produces wrong paper trades and reads an
# out-of-date brain file, which is worse than an error.
#
# SAFETY: this NEVER merges, rebases, resets or discards anything. The daily
# routines write to data/*.json, so an unclean tree is normal and expected --
# in that case (or on any non-fast-forward) it prints a loud warning and
# changes nothing, leaving the decision to the agent. Fast-forward only.
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0
command -v git >/dev/null 2>&1 || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0

if ! git fetch origin main --quiet 2>/dev/null; then
  echo "startup: could not reach origin — continuing on the local checkout."
  exit 0
fi

LOCAL=$(git rev-parse HEAD 2>/dev/null)
REMOTE=$(git rev-parse origin/main 2>/dev/null)
BEHIND=$(git rev-list --count "HEAD..origin/main" 2>/dev/null || echo 0)

if [ "$LOCAL" = "$REMOTE" ] || [ "$BEHIND" = "0" ]; then
  echo "startup: code is current with origin/main."
  exit 0
fi

echo "startup: this checkout is $BEHIND commit(s) behind origin/main."

# --untracked-files=no on purpose: only TRACKED modifications can conflict with
# a fast-forward, and git refuses on its own if an incoming file would clobber an
# untracked one. Counting untracked files here would let a stray scratch file
# silently leave this session on stale code -- the exact failure being prevented.
if [ -n "$(git status --porcelain --untracked-files=no 2>/dev/null)" ]; then
  echo "!! NOT updating: tracked files have uncommitted changes (normal if a"
  echo "!! daily routine just wrote a ledger). Commit or push those first, then"
  echo "!! pull. DO NOT read results from this run as final — the code may be stale."
  exit 0
fi

if git merge --ff-only origin/main --quiet 2>/dev/null; then
  echo "startup: fast-forwarded to $(git rev-parse --short HEAD). Code and CLAUDE.md are current."
else
  echo "!! NOT updating: cannot fast-forward (local commits diverge from main)."
  echo "!! Reconcile manually. DO NOT read results from this run as final."
fi
exit 0
