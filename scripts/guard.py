#!/usr/bin/env python3
"""Cathy guard. Runs as a PreToolUse hook while Cathy mode is on.

Exit 0 allows the action. Exit 2 blocks it and sends the reason to Claude.
The guard fails closed: if it cannot read its input, it blocks.

Limit: this reads command text. It does not run or trace the command.
A command built at run time (for example g=git; $g push) can pass.
The strongest control is to keep push credentials out of the session.
"""
import fnmatch
import json
import os
import re
import shlex
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_DEPTH = 4

# Tokens that only wrap another command. The guard skips them.
WRAPPERS = {"sudo", "env", "command", "nohup", "time", "exec", "xargs", "nice", "builtin"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}
SEPARATORS = {";", "&&", "||", "|", "&", "(", ")", ";;", "|&"}

# A Bash command that mentions these text fragments is blocked.
# They protect Cathy's own switch and files from an agent edit.
SELF_PROTECT = [".config/cathy", "cathy/mode", "cathy.sh", "inject.sh",
                "guard.sh", "guard.py", "cathy/guard", "cathy/rules"]


def block(why):
    sys.stderr.write(
        "CATHY GUARD blocked this action: %s\n"
        "Do not look for a way around this. Ask the human to run /cathy off "
        "if the action is really needed.\n" % why
    )
    sys.exit(2)


def load_lines(name):
    # One entry per line. Empty lines and lines that start with # are ignored.
    path = os.path.join(ROOT, "guard", name)
    try:
        with open(path, encoding="utf-8") as fh:
            lines = [ln.strip() for ln in fh]
    except OSError:
        block("the guard file %s is missing" % name)
    return [ln for ln in lines if ln and not ln.startswith("#")]


def tokenize(cmd):
    # Split into tokens. Operators such as ; && | become separate tokens.
    cmd = cmd.replace("\n", " ; ")
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        return list(lex)
    except ValueError:
        # Unbalanced quotes. Fall back to a plain split. This favors blocking.
        return cmd.split()


def segments(tokens):
    seg = []
    for tok in tokens:
        if tok in SEPARATORS:
            if seg:
                yield seg
            seg = []
        else:
            seg.append(tok)
    if seg:
        yield seg


def strip_prefix(seg):
    # Drop VAR=value assignments and wrapper commands from the front.
    i = 0
    while i < len(seg):
        tok = seg[i]
        base = os.path.basename(tok)
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tok) or base in WRAPPERS:
            i += 1
            continue
        break
    return seg[i:]


GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace",
                       "--exec-path", "--super-prefix", "--config-env"}


def git_parts(seg):
    # Return (subcommand, remaining tokens) for a git command, or None.
    if not seg or os.path.basename(seg[0]) != "git":
        return None
    i = 1
    while i < len(seg) and seg[i].startswith("-"):
        takes_value = seg[i] in GIT_OPTS_WITH_VALUE
        i += 2 if takes_value else 1
    if i >= len(seg):
        return None
    return seg[i], seg[i + 1:]


def matches(seg, prefix):
    seg = strip_prefix(seg)
    if not seg:
        return False
    want = prefix.split()
    if want[0] == "git":
        parts = git_parts(seg)
        if parts is None:
            return False
        sub, rest = parts
        return sub == want[1] and all(w in rest for w in want[2:])
    if os.path.basename(seg[0]) != want[0]:
        return False
    # The words must appear in order. Other words may sit between them.
    pos = 1
    for w in want[1:]:
        try:
            pos = seg.index(w, pos) + 1
        except ValueError:
            return False
    return True


def inner_commands(seg):
    # Find command text inside sh -c "...", eval "...", $(...) and backticks.
    found = []
    seg2 = strip_prefix(seg)
    if seg2:
        base = os.path.basename(seg2[0])
        if base in SHELLS:
            for i, tok in enumerate(seg2[:-1]):
                if tok.startswith("-") and "c" in tok[1:] and not tok.startswith("--"):
                    found.append(seg2[i + 1])
        elif base == "eval":
            found.append(" ".join(seg2[1:]))
    for tok in seg:
        found += re.findall(r"\$\(([^)]*)\)", tok)
        found += re.findall(r"`([^`]*)`", tok)
    return found


def check_command(cmd, blocklist, depth=0):
    if depth > MAX_DEPTH:
        return
    for seg in segments(tokenize(cmd)):
        for prefix in blocklist:
            if matches(seg, prefix):
                block("the command matches the blocked pattern '%s'" % prefix)
        for inner in inner_commands(seg):
            check_command(inner, blocklist, depth + 1)


def state_dir():
    # The folder that holds the Cathy mode file. It follows XDG_CONFIG_HOME.
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "cathy")


def redirect_targets(tokens):
    # Yield file names that a command writes to with > or >> or tee.
    for i, tok in enumerate(tokens[:-1]):
        if tok in (">", ">>", ">|"):
            yield tokens[i + 1]
        elif os.path.basename(tok) == "tee":
            for nxt in tokens[i + 1:]:
                if nxt in SEPARATORS:
                    break
                if not nxt.startswith("-"):
                    yield nxt


def check_bash(cmd):
    for frag in SELF_PROTECT + [state_dir()]:
        if frag in cmd:
            block("the command touches Cathy's own switch or files ('%s')" % frag)
    for target in redirect_targets(tokenize(cmd)):
        check_path(target)
    check_command(cmd, load_lines("blocklist.txt"))


def check_path(path):
    if not path:
        return
    candidates = {os.path.abspath(os.path.expanduser(path)),
                  os.path.realpath(os.path.expanduser(path))}
    own = state_dir()
    for cand in candidates:
        if cand == own or cand.startswith(own + os.sep):
            block("the path '%s' is inside Cathy's state folder" % path)
    for pattern in load_lines("protected-paths.txt"):
        for cand in candidates:
            if fnmatch.fnmatch(cand, pattern):
                block("the path '%s' is protected by '%s'" % (path, pattern))


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        block("the guard could not read the hook input")
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    if tool == "Bash":
        check_bash(tool_input.get("command", "") or "")
    elif tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        check_path(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
    sys.exit(0)


if __name__ == "__main__":
    main()
