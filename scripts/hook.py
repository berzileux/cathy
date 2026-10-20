"""Cathy rule loading. Reads the hook JSON from stdin. Writes only to stdout and the seen-flag folder.
Usage: hook.py session | prompt | tool | core (print the compact rules)
Mode "always": print the rules at session start.
Mode "on": load the rules once for each session, on the first of these:
  - a prompt that matches rules/triggers.txt
  - an edit of a code file (rules/code-extensions.txt), even if the prompt had no keyword
  After that, a matching prompt gets a one-line reminder.
Mode "off": print nothing.
This hook never blocks. It exits 0 on any failure. The guard is a separate script."""
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = os.path.join(ROOT, "rules", "FOUNDATIONS.md")
TRIGGERS = os.path.join(ROOT, "rules", "triggers.txt")
EXTENSIONS = os.path.join(ROOT, "rules", "code-extensions.txt")
STATE = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "cathy")
SEEN = os.path.join(STATE, "seen")
SAFE_ID = re.compile(r"[^A-Za-z0-9_-]")
EDIT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def mode():
    try:
        with open(os.path.join(STATE, "mode"), encoding="utf-8") as fh:
            m = fh.read().strip()
    except OSError:
        m = ""
    m = m or os.environ.get("CATHY_DEFAULT_MODE", "off")
    return m if m in ("on", "always") else "off"


def read_lines(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return [l.strip() for l in fh if l.strip() and not l.lstrip().startswith("#")]
    except OSError:
        return []


def read_rules():
    """Return the compact rules text for injection. Claude Code cuts hook output over
    about 10,000 characters, so inject only the title, how to use, the principles and the
    report block. The language notes and the pattern table stay in the full file."""
    with open(RULES, encoding="utf-8") as fh:
        text = fh.read()
    parts = re.split(r"(?m)^(?=## )", text)
    keep = [parts[0]] + [p for p in parts[1:] if re.match(r"## (1|2|5)\.", p)]
    out = "".join(keep).rstrip() + (
        "\n\n---\n\nLanguage notes, the pattern vocabulary and known limits are in the full file. "
        "Read it when you need them: " + RULES + "\n"
    )
    return out


def flag_path(session_id):
    return os.path.join(SEEN, SAFE_ID.sub("_", session_id or "unknown")[:80])


def prompt_matches(prompt):
    for pat in read_lines(TRIGGERS):
        try:
            if re.search(pat, prompt, re.I):
                return True
        except re.error:
            continue
    return False


def is_code_file(path):
    base = os.path.basename(path).lower()
    for entry in read_lines(EXTENSIONS):
        e = entry.lower()
        if e.startswith("."):
            if base.endswith(e):
                return True
        elif base == e:
            return True
    return False


def mark_seen(session_id):
    """Return True if this call set the flag, False if it was already set."""
    flag = flag_path(session_id)
    if os.path.exists(flag):
        return False
    try:
        os.makedirs(SEEN, exist_ok=True)
        open(flag, "w").close()
        cutoff = time.time() - 7 * 86400
        for name in os.listdir(SEEN):
            p = os.path.join(SEEN, name)
            if os.path.getmtime(p) < cutoff:
                os.remove(p)
    except OSError:
        pass
    return True


def main():
    event = sys.argv[1] if len(sys.argv) > 1 else ""
    if event == "core":
        print(read_rules())
        return
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    m = mode()
    sid = str(data.get("session_id", ""))
    if event == "session":
        # A new, resumed or compacted session may have lost the rules. Forget the flag.
        try:
            os.remove(flag_path(sid))
        except OSError:
            pass
        if m == "always":
            print("CATHY ALWAYS. Apply the foundation rules below for this session. WAR_ROOM specs and SOUL decisions override them. Turn off with /cathy:run off.\n")
            print(read_rules())
        return
    if m != "on":
        return
    if event == "prompt":
        prompt = str(data.get("prompt", ""))
        if prompt.lstrip().startswith("/cathy:") or not prompt_matches(prompt):
            return
        if mark_seen(sid):
            print("CATHY: this prompt matched a coding keyword. Apply the foundation rules below to this task. WAR_ROOM specs and SOUL decisions override them.\n")
            print(read_rules())
        else:
            print("CATHY: the foundation rules (P1 to P13) apply to this task. Follow them.")
        return
    if event == "tool":
        if data.get("tool_name") not in EDIT_TOOLS:
            return
        ti = data.get("tool_input") or {}
        path = str(ti.get("file_path") or ti.get("notebook_path") or "")
        if not path or not is_code_file(path):
            return
        if mark_seen(sid):
            text = ("CATHY: you are editing a code file. Apply the foundation rules below to this task and to "
                    "the edit you are about to make. WAR_ROOM specs and SOUL decisions override them.\n\n" + read_rules())
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": text}}))


try:
    main()
except Exception:
    pass
sys.exit(0)
