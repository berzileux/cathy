---
description: Turn the Cathy foundation rules on or off (on, off, status)
argument-hint: "[on|off|status]"
allowed-tools: Bash(bash:*)
---

!`bash "${CLAUDE_PLUGIN_ROOT}/scripts/cathy.sh" "$ARGUMENTS"`

Read the output above. Confirm the Cathy state in one short sentence.
If the output starts with "CATHY ON", apply the rules it contains for the rest of this session.
If the output starts with "CATHY OFF", stop applying those rules for the rest of this session.
Do nothing else.
