---
description: Cathy foundations and guard. on (keyword-triggered rules), always, off, status
argument-hint: "[on|always|off|status]"
allowed-tools: Bash(bash:*)
---

!`bash "${CLAUDE_PLUGIN_ROOT}/scripts/cathy.sh" "$ARGUMENTS"`

Read the output above. Confirm the Cathy state in one short sentence.
If the output starts with "CATHY ON", confirm the state in one short sentence and do nothing else.
If the output starts with "CATHY ALWAYS", confirm the state in one short sentence, then apply the rules it contains for the rest of this session.
If the output starts with "CATHY OFF", stop applying those rules for the rest of this session.
Do nothing else.
