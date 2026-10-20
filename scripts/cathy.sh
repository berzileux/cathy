#!/usr/bin/env bash
# Toggle Cathy: on | off | status. Writes only the mode file. No network.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/cathy"
STATE_FILE="$STATE_DIR/mode"
RULES="$ROOT/rules/FOUNDATIONS.md"

current_mode() {
  local m
  m="$(cat "$STATE_FILE" 2>/dev/null || true)"
  [ -n "$m" ] || m="${CATHY_DEFAULT_MODE:-off}"
  [ "$m" = "on" ] && echo on || echo off
}

cmd="${1:-status}"
[ -n "$cmd" ] || cmd="status"

case "$cmd" in
  on)
    mkdir -p "$STATE_DIR"
    printf 'on\n' > "$STATE_FILE"
    echo "CATHY ON. Apply the foundation rules below for this session. WAR_ROOM specs and SOUL decisions override them. Turn off with /cathy off."
    echo
    cat "$RULES"
    ;;
  off)
    mkdir -p "$STATE_DIR"
    printf 'off\n' > "$STATE_FILE"
    echo "CATHY OFF. Stop applying the foundation rules and the Foundations report block for the rest of this session. Turn on with /cathy on."
    ;;
  status)
    echo "Cathy mode: $(current_mode)"
    ;;
  *)
    echo "Usage: /cathy on|off|status" >&2
    exit 2
    ;;
esac
