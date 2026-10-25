# Progress: the plan file and the task list

Two kinds of progress, kept in two places because they live for different times.

| | `docs/plan.md` | Session task list |
| --- | --- | --- |
| Tracks | The project: milestones and use cases, adoption areas, fixes, follow-ups, reviews | The steps of the task in hand |
| Lives | In the repository, across sessions and people | In this session only (the task tool, e.g. TodoWrite) |
| Answers | "What is done and what is next?" | "Which step am I on, and did I skip one?" |

## The plan file

`docs/plan.md` is part of the document set, made from `assets/templates/plan.template.md`. It follows the rule every document follows: one fact, one home. It holds status and order, by ID, and nothing else; the content of each item stays in its own document.

### Creating it

- **Bootstrap** writes it with the milestones from the interview (each with its use cases) and the deep review per milestone.
- **Adopt** writes it on the first run if it is missing: the areas from the map, in the order the user agreed, plus a Fixes item for each "code differs from rule" answer as the area closes.
- **A project without one** (made before the plan existed): when any mode starts and `docs/plan.md` is missing, build it from what is there. Milestones from the functional spec's "Rollout", a use case ticked when its Home exists in the code and its rules have passing tests, areas from `adoption.md`, fixes from the open points and expected-failure tests. Say that you made it, and list anything you could not place.

### Updating it

Each mode updates the plan in its closing step, before the report, so the report and the plan never disagree.

| Mode | At the start | At the end |
| --- | --- | --- |
| Build | Put the use case under "Now" | Tick the use case; add the report's follow-ups |
| Change | Put the change under "Now" | Add new use cases under their milestone, mark removed ones "(removed)", tick a fix the change closed, add follow-ups |
| Adopt | Put the area under "Now" | Tick the area; add a Fixes item per rule the code gets wrong; add follow-ups |
| Fix | Put the fix under "Now" | Tick the fix; add follow-ups |
| Review | — | Tick the milestone's deep review |
| Code review | — | Add each finding the user chose to fix later as a follow-up |

Clear "Now" when the task ends. A ticked item stays, with its date: the plan is also the history of what was done.

The traceability check reads the plan too: it warns when a live use case is in no milestone, and fails when the plan cites an ID that does not exist.

## The session task list

At the start of Adopt, Build, Change and Fix, create a task list with the mode's steps, using the session's task tool. Build's ten steps, Change's opening, per-kind and closing steps, Adopt's sections, Fix's five steps. Tick each as it is done.

The steps that get skipped in long tasks are the last ones: the light review, the plan update, the report. A visible list catches that before the user does. Keep it to the mode's steps; it is not a place for notes, which belong in the documents or the report.
