# cathy

Foundation engineering principles and a safety guard for Claude Code,
with one switch. Off by default.

One switch controls both parts:

- `/cathy on`: the rules apply and the guard enforces.
- `/cathy off`: no rules and no guard.

Off means no protection. Use it only when you are present and need an action
that the guard blocks.

## Install

Run inside a Claude Code session, as two separate prompts:

    /plugin marketplace add berzileux/cathy
    /plugin install cathy@cathy

Restart the session after installing so the hooks load.

## Use

    /cathy on        turn on the rules and the guard
    /cathy off       turn off the rules and the guard
    /cathy status    show the current mode

The full name `/cathy:cathy on` is tested and works. The short form
`/cathy on` did not resolve in a headless test, so confirm it in an
interactive session. If it fails, use the full name.

## The two parts

### Rules (advisory)

`rules/FOUNDATIONS.md` holds 13 language-agnostic principles. Each has a rule,
a reason and a check. Notes cover C#/.NET, Go, Python, Perl, TypeScript/React
and SQL. P13 asks for comments that explain why, written in ASD-STE100 style:
short sentences, one idea each, plain text, no icons.

The rules are a prompt. Claude can ignore them.

### Guard (enforced)

A PreToolUse hook checks every Bash, Write, Edit, MultiEdit and NotebookEdit
call while mode is on. It blocks the action before it runs.

- Commands: `guard/blocklist.txt`. The default list blocks git add, commit,
  push, reset --hard, clean, config and rebase; npm publish, docker push and
  gh create/comment/merge; kubectl apply/delete, helm install/upgrade/uninstall,
  terraform apply/destroy and a few aws delete commands.
- Files: `guard/protected-paths.txt`. The default list protects .env files,
  .ssh, .aws, .kube, Claude settings and plugins, and Cathy's own state folder.
- Self-protection: while mode is on, the agent cannot run the switch script,
  edit the mode file, or edit the guard files. Only you can switch it off,
  with `/cathy off`.
- Fail closed: if python3 is missing or the hook input cannot be read while
  mode is on, the action is blocked.

Edit the two guard files to fit your work. One line per entry. Lines that start
with # are comments.

## How it works

- `/cathy on` writes `on` to `~/.config/cathy/mode` (or `$XDG_CONFIG_HOME/cathy/mode`)
  and prints the rules into the conversation.
- A SessionStart hook prints the rules at the start of each session
  (also after resume and compaction) when the mode is `on`.
- A PreToolUse hook runs the guard. When the mode is `off`, it allows everything.
- `/cathy off` writes `off` and tells Claude to stop applying the rules.

Set `CATHY_DEFAULT_MODE=on` to change the default when no mode file exists.
The default is `off`.

## Tested

Tested with the claude CLI, `--plugin-dir`, and permissions skipped:

- Mode off: `git add` runs.
- Mode on: `git add` is blocked and nothing is staged.
- `/cathy:cathy off` still works for the human while the guard is on.
- Mode on: the agent cannot run the switch script, cannot overwrite the mode
  file with the Write tool, cannot write `.env` with Write or with a shell
  redirect. A normal file write and `git status` still work.
- 69 unit cases for the guard script pass.

Not tested: install through `/plugin marketplace add`, refresh from a GitHub
marketplace, the short form `/cathy on`, Windows, and any shell other than bash.

## Limits

- The guard reads command text. It does not run or trace the command.
  A command built at run time, such as `g=git; $g push`, can pass.
  Redirect checks cover `>`, `>>` and `tee`. They do not cover `cp`, `mv`,
  `sed -i` or a script that writes a file.
- The strongest control is to keep push credentials, SSH keys and tokens out of
  the session. Run sessions with permissions skipped only in a sandbox with no
  production credentials.
- `.env.*` is protected, so `.env.example` is blocked too. Edit
  `guard/protected-paths.txt` if you want to allow it.
- Text already loaded into a conversation cannot be removed. `/cathy off` stops
  the rules by instruction. The text is gone in the next session.
- The mode file is per machine and shared by all sessions on that machine.
- The scripts need bash and python3. Windows needs WSL or Git Bash.
- Plugin hooks run with your user rights at session start and before each
  tool call. Read the scripts before you install. Pin the commit you installed.

## Update

After you change files in this repo, do these steps.

1. Edit the files.
2. Raise `version` in `.claude-plugin/plugin.json`, for example 0.2.0 to 0.2.1.
3. Commit and push to GitHub.
4. On each machine, run these two commands in a Claude Code session:

       /plugin marketplace update cathy
       /plugin update cathy@cathy

5. Restart the session. The update does not apply until you restart.

The same commands work in a terminal as `claude plugin marketplace update cathy`
and `claude plugin update cathy@cathy`.

Raise the version on every change. If an update seems stuck, uninstall and
install again:

    /plugin uninstall cathy@cathy
    /plugin install cathy@cathy

While you develop, add the folder as a marketplace by its local path:

    /plugin marketplace add ./cathy

A plugin from a local path is read live from its folder. Edits apply at the next
session start or after `/reload-plugins`. You do not need the update commands.

Before you pull a change onto another machine, read the diff. The hooks run
scripts with your user rights at every session start and tool call.

## Layout

    .claude-plugin/
      marketplace.json
      plugin.json
    commands/
      cathy.md
    hooks/
      hooks.json
    scripts/
      cathy.sh        switch
      inject.sh       SessionStart: print the rules when on
      guard.sh        PreToolUse entry point, checks the mode
      guard.py        PreToolUse checks
    guard/
      blocklist.txt
      protected-paths.txt
    rules/
      FOUNDATIONS.md

## Uninstall

    /plugin uninstall cathy@cathy
    /plugin marketplace remove cathy

Then delete the saved mode: `rm -r ~/.config/cathy`.

## Credit

The on/off command idea is inspired by the DietrichGebert/ponytail plugin.
No ponytail text or code is included here.
