#!/usr/bin/env bash
# PreToolUse entry point for the Cathy guard.
# It enforces only when Cathy mode is "on". When mode is off, it allows everything.
# It fails closed: if the guard cannot run while mode is on, it blocks the action.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/cathy/mode"

mode="$(cat "$STATE_FILE" 2>/dev/null || true)"
[ -n "$mode" ] || mode="${CATHY_DEFAULT_MODE:-off}"

# Mode off: allow.
[ "$mode" = "on" ] || exit 0

# Mode on: python3 does the checks. Without it, block. Exit code 2 means block.
if ! command -v python3 >/dev/null 2>&1; then
  echo "CATHY GUARD blocked this action: python3 is missing, so the guard cannot check it. Ask the human to install python3 or run /cathy off." >&2
  exit 2
fi

exec python3 -I "$ROOT/scripts/guard.py"
