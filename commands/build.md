---
description: Implement one use case - test first, architecture check, verification against rule IDs
argument-hint: "<use case ID or name>"
---
Follow the skill at `${CLAUDE_PLUGIN_ROOT}/skills/ddd-hexagonal/SKILL.md` in **Build** mode. Read its references from `${CLAUDE_PLUGIN_ROOT}/skills/ddd-hexagonal/references/`, not from any other installed copy of the skill, for exactly one use case.

If the project has no `docs/business-rules.md` or `docs/use-cases.md`, stop and suggest `/ddd-hexagonal:bootstrap`. If no use case is named below, list the use cases not ticked in `docs/plan.md` (from `docs/use-cases.md` if there is no plan yet), next milestone first, and ask which one to build.

Use case: $ARGUMENTS
