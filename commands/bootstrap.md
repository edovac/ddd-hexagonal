---
description: Start a DDD + hexagonal project - interview, then write the document set
argument-hint: "[short description of the application]"
---
Follow the skill at `${CLAUDE_PLUGIN_ROOT}/skills/ddd-hexagonal/SKILL.md` in **Bootstrap** mode. Read its references from `${CLAUDE_PLUGIN_ROOT}/skills/ddd-hexagonal/references/`, not from any other installed copy of the skill.

Look at the project first. If `docs/business-rules.md` or `docs/use-cases.md` already exists, stop and tell the user: a document set is already in place, and **Change** or **Review** is likely what they want. Do not overwrite existing documents unless the user confirms.

Application: $ARGUMENTS
