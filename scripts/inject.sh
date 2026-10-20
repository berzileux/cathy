#!/usr/bin/env bash
# SessionStart hook: print the rules into context only when mode is "on".
# Reads the mode file and the rules file. Writes nothing. No network.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/cathy/mode"
RULES="$ROOT/rules/FOUNDATIONS.md"

mode="$(cat "$STATE_FILE" 2>/dev/null || true)"
[ -n "$mode" ] || mode="${CATHY_DEFAULT_MODE:-off}"

if [ "$mode" = "on" ] && [ -f "$RULES" ]; then
  echo "CATHY ON. Apply the foundation rules below for this session. WAR_ROOM specs and SOUL decisions override them. Turn off with /cathy:run off."
  echo
  cat "$RULES"
fi

exit 0
