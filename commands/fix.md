---
description: Fix a bug against the documented rules - confirm the rule, failing test first, smallest change in the rule's home
argument-hint: "<the bug, a rule ID or an open point, e.g. \"LN-12\" or \"a second return charges the fee again\">"
---
Follow the skill at `${CLAUDE_PLUGIN_ROOT}/skills/ddd-hexagonal/SKILL.md` in **Fix** mode. Read its references from `${CLAUDE_PLUGIN_ROOT}/skills/ddd-hexagonal/references/`, not from any other installed copy of the skill. Its steps are in `references/fix.md`.

If the project has no `docs/business-rules.md`, stop: there is no rule to fix against. Suggest `/ddd-hexagonal:adopt` for working code without documents, or the built-in workflow for an ordinary fix. If the bug is not described below, list the open points marked as code that differs from a rule, and the tests marked as expected failures, and ask which one to fix.

Bug: $ARGUMENTS
