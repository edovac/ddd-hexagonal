# Evals

`evals.json` holds the test prompts and assertions. Evals that need an existing project name a fixture and a `setup` command.

| Fixture | State | Used by |
| --- | --- | --- |
| `fixtures/room-booking` | Python + PostgreSQL project after Bootstrap: documents, scaffold, migrations, no use case built | `build-book-room` |
| `fixtures/room-booking-uc01` | Overlay on `room-booking`: UC-01 implemented and tested, as a second commit | `change-booking-limits`, `change-new-use-case`, `change-db-swap` |
| `fixtures/returns-review` | Documents only, with planted contradictions, gaps and duplication (see the eval's assertions) | `review-returns-docs` |

Create a project for one run, from this folder's parent (the skill folder):

```
uv run evals/setup_fixture.py room-booking-uc01 /tmp/run-1
```

It makes a git repository on `main`, copies the skill's current scripts into `tools/` and installs the branch guard, so fixtures never carry stale copies. Integration tests in the room-booking fixtures need PostgreSQL 16: `docker compose up -d db` in the project.

## Grading with less cost

An eval iteration is mostly agent tokens: the runs, then a grader agent per eval that re-runs the checks. `grade_mechanical.py` does the part of grading that is a fact about the project: it runs the tests and tools, reads git, greps the domain, compares documents with `HEAD`, runs the branch guard, and probes the cases that matter (a stored booking over the new limit still blocking its room; which write paths a MySQL guarantee covers). It decides about half of the assertions in about a second per run, the same way every time.

```
uv run evals/grade_mechanical.py change-booking-limits <project> --outputs <run outputs> \
    --env DATABASE_URL=postgresql://postgres:test@localhost:5433/<database> --out mechanical.json
```

The output has `decided` (pass or fail with evidence), `needs_judgment` (assertions that need reading, each with the numbers that help) and `tools` (unit, integration, mypy, ruff, import-linter, traceability). Give the grader agent `mechanical.json` and tell it to grade only `needs_judgment`; that is the part that needs reading questions.md, the report and test intent.

- Checks are tied to assertions by the start of their text. When you reword an assertion in `evals.json`, the script stops with an error naming the check to update.
- `DATABASE_URL` must follow the project's own convention. The change-db-swap runs refuse any database name that does not end in `_test`. A fixture that cannot set up is reported as needing judgment, not as a failure.
- Validated against 12 iteration-2 runs: it decided 66 of 130 assertion-runs and agreed with the agent graders on all 66.
- To compare a new skill version with the 0.3.0 baseline, keep the baseline projects and grade them again with the script when assertions change, instead of re-running them.
