---
description: Review code changes against the DDD + hexagonal rules - architecture, rule-ID traceability, agreement with the documents, tests and dependencies
argument-hint: "[PR number | branch | path] [--full] [--fix] [low|medium|high|xhigh|max]"
---
Use the ddd-hexagonal skill in **Code review** mode, following `references/code-review.md`.

If the project has no `docs/business-rules.md`, stop and suggest `/ddd-hexagonal:bootstrap`, or the built-in `/code-review` for a generic review.

Read these from the arguments below:
- **Target:** a PR number, branch or path; with none, the uncommitted changes, or the current branch if there are none.
- **`--full`:** first run the built-in `code-review` skill on the same target (passing the effort level, if one is given), then the DDD pass, and merge the findings.
- **`--fix`:** apply the unambiguous fixes after the report. Without it, report only.

Arguments: $ARGUMENTS
