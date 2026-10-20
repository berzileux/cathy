# FOUNDATIONS.md

Language-agnostic engineering principles for agentic_session.
Principles first. Pattern names are vocabulary only, never a requirement.

Authority order (highest first):
1. SOUL decisions
2. WAR_ROOM MD specs
3. Project instructions file
4. This file

If two principles conflict, the lower number wins. Security and correctness
come before speed and elegance.

Loaded by the cathy plugin when mode is on. Switch with /cathy:run on or /cathy:run off.
Without the plugin, import with @FOUNDATIONS.md.

Style: rules follow OUTPUT_STYLE.md. Reasons and risk notes use normal precise prose.

---

## 1. How to use this file

- These are defaults, not laws. A spec may override any principle.
- To break a principle, record the reason in the session report under
  "deviations". An unrecorded deviation is a defect.
- Each principle has: the rule, the reason, and a check. If you cannot
  state how you checked it, say "unchecked" in the report.
- Keep this file short. Every line loads into context. Move per-language
  notes into separate files when a project needs only one of them.

---

## 2. Principles

### P1. Treat every boundary as hostile

Rule: Validate and authorize all data that crosses a trust boundary.
Deny by default. Never put secrets or personal data in code, logs, URLs
or error messages.

Reason: Data from outside the process is the only data you cannot reason
about. One missing check at a boundary outweighs careful code everywhere else.

Check: List each entry point. For each, name the validation and the
authorization step, or write "missing".

### P2. Fail loudly

Rule: Return or raise an explicit error. Do not swallow errors. Do not
log and continue when the caller needs to know.

Reason: Silent failure turns a small bug into corrupted data found weeks
later. A crash with context is cheaper than a wrong answer.

Check: Search for empty catch blocks, ignored error returns, and
log-only handlers. Justify each one or fix it.

### P3. Make invalid states hard to represent

Rule: Use types, enums, constraints and constructors so a wrong state
cannot be built. Replace magic strings and numbers with named values.

Reason: A state the code cannot express is a state the code cannot get
wrong. Magic values hide business meaning and break when the data changes.

Check: Search for string or number literals in conditionals. Name them
or document why they stay.

### P4. Protect data integrity

Rule: Make writes atomic. Make retried operations idempotent. Prefer one
conditional update over read-then-write. Wrap multi-step changes in a
transaction or a compensating step.

Reason: Retries, crashes and concurrent requests happen in production.
Code that is correct only in the single-request case is not correct.

Check: For each write path, state what happens on a retry, on a crash
halfway, and on two concurrent requests.

### P5. Bound everything, then measure

Rule: Put a limit on every loop over external data, every queue, every
retry, every timeout, every page size. Measure before you optimize.
Do not optimize without a number.

Reason: Unbounded work fails at scale and under attack. Unmeasured
optimization adds complexity and often misses the real cost.

Check: Find each unbounded collection, call or retry. State its limit
or mark it "unbounded, accepted by SOUL".

### P6. Keep logic pure and I/O at the edges

Rule: Put business decisions in functions that do no I/O. Put network,
disk, database and clock access in thin outer layers.

Reason: Pure logic is easy to test and reason about. Mixed code forces
slow, fragile tests and hides where failures come from.

Check: For each changed function, mark it pure, impure or mixed.
Explain any mixed function.

### P7. Prefer small interfaces and composition

Rule: Define small contracts where they are used. Combine behavior by
composition. Use inheritance only when the language and the domain
clearly call for it.

Reason: Small contracts are easy to fake, replace and understand.
Deep hierarchies couple unrelated changes.

Check: Count the methods in each new interface. Justify more than a few.

### P8. Fix the root cause once

Rule: Reproduce the bug first. Find every caller of the faulty code.
Fix the shared function, not each symptom.

Reason: A patch on one path leaves sibling paths broken. The ticket
names a symptom, not the cause.

Check: List the callers you reviewed. Confirm a test fails before the
fix and passes after it.

### P9. Leave one check behind for risky logic

Rule: Any logic with a branch, a loop, a parser, money or security gets
at least one runnable test. Test behavior at the boundary, not internals.

Reason: Untested risky logic is a guess. One small test is the cheapest
proof that it still works after the next change.

Check: For each risky change, name the test and show it fails when the
logic breaks.

### P10. Log decisions with context

Rule: Log failures and key decisions with an identifier, the inputs that
matter and the outcome. Keep secrets and personal data out of logs.

Reason: You cannot debug what you cannot see. Logs that leak data
create a second incident.

Check: Read each new log line. Confirm it names the context and holds
no sensitive value.

### P11. Change surgically, reuse first

Rule: Touch only what the task needs. Reuse existing code before you
write new code. Add a dependency only when it earns its place, and pin
its version.

Reason: Every extra changed line is extra review and extra risk. Every
dependency is code you did not write and must trust.

Check: Trace each changed line to the task. List each new dependency
with its reason and version.

### P12. One term for one concept

Rule: Pick one name for each concept and use it everywhere. Write
contracts between components down: formats, fields, units, limits.

Reason: Synonyms create bugs and slow review. Unwritten contracts break
silently when one side changes.

Check: Search for two names for the same thing. List each cross-component
contract you relied on.

### P13. Comment the why, in short plain sentences

Rule: Add a comment where the reason, a limit or a contract is not clear from
the code. Write it in ASD-STE100 style: short sentences, one idea per
sentence, active voice, one term per concept, no filler. Say why, not what.
Use plain text only. Use no emoji and no icons. Update a comment when you
change the code. Delete a comment that is no longer true.

Reason: Code shows what happens. Only a comment can show why. Short plain
sentences stay readable and get kept up to date. Long comments go stale.

Check: Read each new comment. Confirm it states a reason, a limit or a
contract. Confirm each sentence holds one idea. Confirm no condition was
dropped to save words. For a security or concurrency condition, use several
short sentences. Do not cut a condition to stay short.

---

## 3. Language notes

Defaults from general practice. Adjust to the project. If a note conflicts
with a spec, the spec wins.

### C# / .NET
- P3: Use records, enums and value objects. Enable nullable reference types.
- P6: Keep domain logic in plain classes. Put I/O behind interfaces.
- P7: Define interfaces in the consuming layer. Avoid base classes for reuse.
- P4: Use transactions and unique constraints. Use idempotency keys on retried endpoints.
- P5: Pass a CancellationToken. Set HttpClient timeouts. Page every query.
- P13: Use XML doc comments on public members. Keep the summary to one sentence.

### Go
- P2: Check every returned error. Wrap with context. Do not ignore.
- P7: Define small interfaces where they are consumed. Compose with embedding.
- P5: Pass context with deadlines. Bound goroutines and channels.
- P9: Use table-driven tests.
- P3: Use defined types and constants. Use iota for enums.
- P13: Start each doc comment with the name of the thing it describes.

### Python
- P3: Use type hints, enums and dataclasses. Check with a type checker.
- P1: Validate input with a schema at the boundary.
- P2: Catch specific exceptions. Never use a bare except.
- P11: Pin dependencies with a lock file.
- P5: Stream large data. Do not load it all into memory.
- P13: Make the first docstring line one sentence. Use comments for the why.

### Perl
- P1: Enable strict and warnings. Treat all external input as tainted.
- P1: Use placeholders for SQL. Never interpolate input into queries or commands.
- P2: Check return values of open, close and system calls.
- P11: Prefer core modules and pin CPAN versions.
- P9: Use Test::More for at least one check per risky function.
- P13: Use POD for public subs. Use # comments for the why.

### TypeScript / React
- P3: Turn on strict mode. Use discriminated unions for state.
- P1: Validate data from the network at runtime. Types do not check it.
- P6: Keep logic in plain functions or hooks. Keep components thin.
- P5: Debounce and paginate. Clean up effects and subscriptions.
- P10: Keep secrets out of client bundles and logs.
- P13: Use TSDoc on exported functions and hooks. Keep each one short.

### SQL / PostgreSQL
- P3: Use constraints, foreign keys and check clauses. Use proper types.
- P4: Use transactions and unique indexes. Use conditional updates for races.
- P5: Add LIMIT or pagination. Check plans with EXPLAIN before you add indexes.
- P1: Use parameters. Grant the least privilege to each role.
- P13: Use COMMENT ON for tables and columns whose meaning is not obvious.

---

## 4. Pattern names as vocabulary

Use names for discussion. Do not force a class structure on a language
that does not need it.

| Name      | Class-based languages        | Go, Python, functional style         |
| --------- | ---------------------------- | ------------------------------------ |
| Strategy  | Interface with implementations | Function passed as a parameter     |
| Factory   | Factory class or method      | Constructor function                 |
| Observer  | Event and listener types     | Callback, channel or event stream    |
| Decorator | Wrapper class                | Wrapper function or middleware       |
| Command   | Command object               | Function or closure plus data        |
| Singleton | Avoid. Use dependency injection | Module-level value, passed explicitly |

If the spec names a pattern, follow the spec. If it does not, choose the
simplest structure that satisfies P1 to P13.

---

## 5. Report block

Append to each agentic_session report:

    ### Foundations
    - principles checked: <P-numbers>
    - unchecked: <P-numbers and why>
    - deviations: <P-number, reason, or none>
    - unbounded or untested items left: <list or none>
    - quirks unknown to WAR_ROOM: <list or none>

---

## 6. Known limits

- This file is a prompt. The agent can ignore it. It is not enforced.
- Checks in section 2 are only as good as the review of the report.
  SOUL spot-checks the claims against the code.
- Language notes were written from general practice, not verified
  against a specific project. Treat them as a starting point.
