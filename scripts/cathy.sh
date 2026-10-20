#!/usr/bin/env bash
# Toggle Cathy: on | always | off | status. Writes only the mode file. No network.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/cathy"
STATE_FILE="$STATE_DIR/mode"
RULES="$ROOT/rules/FOUNDATIONS.md"

current_mode() {
  local m
  m="$(cat "$STATE_FILE" 2>/dev/null || true)"
  [ -n "$m" ] || m="${CATHY_DEFAULT_MODE:-off}"
  case "$m" in on|always) echo "$m" ;; *) echo off ;; esac
}

cmd="${1:-status}"
[ -n "$cmd" ] || cmd="status"

case "$cmd" in
  on)
    mkdir -p "$STATE_DIR"
    printf 'on\n' > "$STATE_FILE"
    echo "CATHY ON. Keyword mode. The guard is active now. The foundation rules load once, when a prompt mentions a coding keyword or when a code file is first edited. The keywords are in rules/triggers.txt. Turn off with /cathy:run off."
    ;;
  always)
    mkdir -p "$STATE_DIR"
    printf 'always\n' > "$STATE_FILE"
    echo "CATHY ALWAYS. The guard is active. Apply the foundation rules below for this session and at every session start. WAR_ROOM specs and SOUL decisions override them. Turn off with /cathy:run off."
    echo
    # Print the compact rules. Fall back to the full file if python3 is missing.
    python3 -I "$ROOT/scripts/hook.py" core 2>/dev/null || cat "$RULES"
    ;;
  off)
    mkdir -p "$STATE_DIR"
    printf 'off\n' > "$STATE_FILE"
    echo "CATHY OFF. Stop applying the foundation rules and the Foundations report block for the rest of this session. Turn on with /cathy:run on."
    ;;
  status)
    echo "Cathy mode: $(current_mode)"
    ;;
  *)
    echo "Usage: /cathy:run on|always|off|status" >&2
    exit 2
    ;;
esac
