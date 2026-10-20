# cathy

Foundation engineering principles and a safety guard for Claude Code,
with one switch. Off by default.

One switch controls both parts:

- `/cathy:run on`: the guard enforces now. The rules load only when you do coding
  work: on a coding keyword in your prompt, or on the first edit of a code file.
- `/cathy:run always`: the guard enforces, and the rules load at every session start.
- `/cathy:run off`: no rules and no guard.

Off means no protection. Use it only when you are present and need an action
that the guard blocks.

The guard does not depend on keywords. It is active whenever the mode is `on` or `always`.
Only the rule loading is triggered by keywords, because only the rules cost context.

## Install

Run inside a Claude Code session, as two separate prompts:

    /plugin marketplace add berzileux/cathy
    /plugin install cathy@cathy

Restart the session after installing so the hooks load.

## Use

    /cathy:run on        guard on; rules load on a coding keyword or the first code edit
    /cathy:run always    guard on; rules load at every session start
    /cathy:run off       turn off the rules and the guard
    /cathy:run status    show the current mode

The command is `/cathy:run`. Plugin commands carry the plugin name as a prefix, and
autocomplete inserts it. Type the full name. Shorter forms such as `/cathy on` are not
resolved by Claude Code itself. A model may guess them, so do not rely on them.

## The two parts

### Rules (advisory)

`rules/FOUNDATIONS.md` holds 13 language-agnostic principles. Each has a rule,
a reason and a check. Notes cover C#/.NET, Go, Python, Perl, TypeScript/React
and SQL. P13 asks for comments that explain why, written in ASD-STE100 style:
short sentences, one idea each, plain text, no icons.

The rules are a prompt. Claude can ignore them.

Claude Code cuts hook output over about 10,000 characters, and the full file is more
than that. So the hooks inject a compact core of about 7.5 KB: the intro, how to use,
the 13 principles and the report block. The language notes, the pattern vocabulary and
the known limits stay in the full file. The injected text gives its path, so Claude
can read it when it needs it. The core is cut from `FOUNDATIONS.md` by heading, so the
two cannot drift apart.

#### When the rules load in mode `on`

1. A prompt matches a line in `rules/triggers.txt`. Examples: code, implement,
   refactor, function, endpoint, query, test, build, deploy, commit, fix, bug.
2. Claude edits a code file for the first time in the session. The file type comes
   from `rules/code-extensions.txt`. This covers a prompt with no keyword, such as
   "do what task.md says".
3. Later matching prompts add only a one-line reminder.
4. After a session is resumed or compacted, the next trigger loads the rules again.

A prompt with no keyword and no code edit loads nothing, so the rules cost nothing on
other work. The first-edit trigger fires before the edit runs. The rules reach Claude
with that tool call, so the first edit may already be written. Later edits follow them.
Edit `triggers.txt` and `code-extensions.txt` to fit your work.

### Guard (enforced)

A PreToolUse hook checks every Bash, Write, Edit, MultiEdit and NotebookEdit
call while mode is `on` or `always`. It blocks the action before it runs.

- Commands: `guard/blocklist.txt`. The default list blocks git add, commit,
  push, reset --hard, clean, config and rebase; npm publish, docker push and
  gh create/comment/merge; kubectl apply/delete, helm install/upgrade/uninstall,
  terraform apply/destroy and a few aws delete commands.
- Files: `guard/protected-paths.txt`. The default list protects .env files,
  .ssh, .aws, .kube, Claude settings and plugins, and Cathy's own state folder.
- Self-protection: while the guard is active, the agent cannot run the switch script,
  edit the mode file, or edit the guard, hook and rule files. Only you can switch it off,
  with `/cathy:run off`.
- Fail closed: if python3 is missing or the hook input cannot be read while
  the guard is active, the action is blocked.
- Rule loading fails open. If python3 is missing, the rules do not load, and you get
  no warning. The guard still blocks.

Edit the two guard files to fit your work. One line per entry. Lines that start
with # are comments.

## How it works

- `/cathy:run on`, `always` and `off` write the mode to `~/.config/cathy/mode`
  (or `$XDG_CONFIG_HOME/cathy/mode`). `always` also prints the compact rules at once.
  `on` prints only a confirmation.
- A SessionStart hook prints the compact rules when the mode is `always`. In every mode
  it clears the "rules already loaded" flag for that session.
- A UserPromptSubmit hook, in `on` mode, loads the rules when the prompt matches a keyword.
- A PreToolUse hook (`hook.py tool`), in `on` mode, loads the rules on the first edit of a
  code file. The flag files are in `~/.config/cathy/seen/` and are deleted after 7 days.
- A separate PreToolUse hook runs the guard. When the mode is `off`, it allows everything.
- `/cathy:run off` writes `off` and tells Claude to stop applying the rules.

Set `CATHY_DEFAULT_MODE=on` (or `always`) to change the default when no mode file exists.
The default is `off`.

Upgrade note: in versions before 0.4.0, `on` loaded the rules at every session start.
Now that is `always`. A saved `on` becomes keyword mode.

## Tested

Tested with the claude CLI, `--plugin-dir`, and permissions skipped:

- Mode off: `git add` runs.
- Mode on: `git add` is blocked and nothing is staged.
- `/cathy:run off` still works for the human while the guard is on.
- Mode on: the agent cannot run the switch script, cannot overwrite the mode
  file with the Write tool, cannot write `.env` with Write or with a shell
  redirect. A normal file write and `git status` still work.
- 69 unit cases for the guard script pass.
- Guard modes, through `guard.sh`: `on` blocks `git add`, `always` blocks it, `off` and
  no mode file allow it.
- Keyword mode (`on`), live: a plain prompt loaded nothing. A prompt with a coding keyword
  loaded the rules, and the model answered a question about P13, the last principle.
  The guard blocked `git add` in a session where no keyword had loaded the rules.
- First-edit trigger, live: with the prompt "do what task.md says" (no keyword), the first
  `Write` of `hello.py` loaded the rules, and the model then answered a question about P13.
- `always`, live: the rules were in context at session start, with no keyword.
- Hook unit tests: no match, first match, later match, a skipped `/cathy:` prompt, a
  `.md` edit that loads nothing, a `Dockerfile` edit that loads, a Read that loads nothing,
  a session event that clears the flag, and bad input failing open.
- Found in testing: the first version injected the full 11 KB file, and Claude Code cut it
  after P2. Injection now uses the compact core (about 7.5 KB). Every injected text was
  measured under 9,500 characters.

Not tested: install through `/plugin marketplace add`, refresh from a GitHub
marketplace, Windows, and any shell other than bash.

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
- Claude Code cuts hook output over about 10,000 characters. [Likely] If you add
  principles to `FOUNDATIONS.md`, keep sections 1, 2 and 5 under about 9,000 characters
  in total, or the rules will be cut again.
- Keyword matching is a regular expression on your prompt, not meaning. It can miss a
  prompt with no keyword. The first-edit trigger catches most such cases. It cannot catch
  a task that never edits a code file. In that case use `always`.
- A prompt can match by accident. The rules then load once for that session.
- Text already loaded into a conversation cannot be removed. `/cathy:run off` stops
  the rules by instruction. The text is gone in the next session.
- The mode file is per machine and shared by all sessions on that machine.
- The scripts need bash and python3. Windows needs WSL or Git Bash.
- The guard reads and blocks. It does not read-protect files: `cat .env` or a Read of a
  protected path is not blocked. Keep secrets out of reach of the session.
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

## Testing a local copy

If you installed the live market source, remove it first to avoid issues:

    /plugin uninstall cathy@cathy
    /plugin marketplace remove cathy

Then add the local folder and install it. Use the absolute path of the folder that
contains `.claude-plugin`:

    /plugin marketplace add /abs/path/to/cathy
    /plugin install cathy@cathy

Restart the session after installing so the hooks load.

`marketplace add` only registers the folder. You must still run the install command.

While you develop from the local folder, you do not need to update, reinstall or
raise the version. Edit the files, then start a new session, or run `/reload-plugins`
in an open one.

To go back to the GitHub copy, remove the local one with the two commands above,
then follow the Install section. If you move or rename the folder, remove the
local copy and add it again from the new path.

When a release removes or renames a file, delete the old plugin folder before you
unzip the new one. Unzipping over the old folder keeps the removed files. For
example, an old `commands/cathy.md` keeps a second command `/cathy:cathy` alive, and
an old `scripts/inject.sh` stays on disk.

### Check that it works

Run these in a scratch folder that is a git repo, not in a project you care about.

1. Type `/ca`. Autocomplete should show `cathy:run` and no `cathy:cathy`.
2. `/cathy:run status` should say the mode is off.
3. `/cathy:run on`, then ask: "Run git add a.txt, then git status --short."
   The guard should block `git add`, and `a.txt` should stay untracked.
   The block message says "CATHY GUARD blocked this action".
4. Keyword trigger. Start a new session and run `/cathy:run status` (it should say on).
   Ask: "I need to implement a function. From your current instructions only, with no
   file reads, what does rule P13 say?" The answer should describe the comment rule.
   Then ask the same question without the keywords. In a new session, ask: "From your
   current instructions only, with no file reads, what does rule P13 say? If you
   do not have it, say: not loaded." The answer should be "not loaded".
5. First-edit trigger. In a new session, write a file `task.md` that says "Create hello.py
   that prints hello". Ask only: "Do what task.md says." Then ask the P13 question in
   the same session. The answer should describe the comment rule.
6. `/cathy:run off`, then `git add a.txt` should work.

Steps 4 and 5 need a new session each time, because the rules load once per session.
If a step fails, run `claude plugin list` and check the `Read from:` path, then
`ls <that path>/commands` for stale files.

## Layout

    .claude-plugin/
      marketplace.json
      plugin.json
    commands/
      run.md
    hooks/
      hooks.json
    scripts/
      cathy.sh        switch
      hook.py         rule loading: SessionStart, UserPromptSubmit, PreToolUse
      guard.sh        PreToolUse entry point, checks the mode
      guard.py        PreToolUse checks
    guard/
      blocklist.txt
      protected-paths.txt
    rules/
      FOUNDATIONS.md      full reference
      triggers.txt        coding keywords for mode on
      code-extensions.txt code file types for the first-edit trigger

## Uninstall

    /plugin uninstall cathy@cathy
    /plugin marketplace remove cathy

Then delete the saved mode: `rm -r ~/.config/cathy`.

## Credit

The on/off command idea is inspired by the DietrichGebert/ponytail plugin.
No ponytail text or code is included here.
