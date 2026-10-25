---
description: Bring an existing codebase under DDD + hexagonal - map areas, confirm rules found in the code, pin them with tests, one area at a time
argument-hint: "[area to adopt, e.g. \"billing\"]"
---
Follow the skill at `${CLAUDE_PLUGIN_ROOT}/skills/ddd-hexagonal/SKILL.md` in **Adopt** mode. Read its references from `${CLAUDE_PLUGIN_ROOT}/skills/ddd-hexagonal/references/`, not from any other installed copy of the skill. Its steps are in `references/adopt.md`.

Look at the project first. If there is no application source code, stop and suggest `/ddd-hexagonal:bootstrap`. If `docs/business-rules.md` exists and there is no `docs/adoption.md`, the project already follows the workflow: stop and suggest **Change** or **Review**, unless the user confirms that parts of the code are still undocumented.

If `docs/adoption.md` exists, continue with the area named below, or the next area not ticked in `docs/plan.md`. If it does not exist, start by mapping the codebase; an area named below is the user's choice for the first area.

Area: $ARGUMENTS
