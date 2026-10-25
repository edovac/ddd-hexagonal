# Evals

`evals.json` holds the test prompts and assertions. Evals that need an existing project name a fixture and a `setup` command.

| Fixture | State | Used by |
| --- | --- | --- |
| `fixtures/room-booking` | Python + PostgreSQL project after Bootstrap: documents, scaffold, migrations, no use case built | `build-book-room` |
| `fixtures/room-booking-uc01` | Overlay on `room-booking`: UC-01 implemented and tested, as a second commit | `change-booking-limits`, `change-new-use-case`, `change-db-swap` |
| `fixtures/returns-review` | Documents only, with planted contradictions, gaps and duplication (see the eval's assertions) | `review-returns-docs` |
| `fixtures/library-legacy` | Working Flask + PostgreSQL app with no documents and no `tools/` or branch guard. Planted: rules only in the schema (one open loan per book, at most 2 renewals), a loan limit of 3 in `loans.py` and 5 in `web.py`, late fees on floats, and a test that already fails (`test_fee_is_capped`) | `adopt-library-loans` |

Create a project for one run, from this folder's parent (the skill folder):

```
uv run evals/setup_fixture.py room-booking-uc01 /tmp/run-1
```

It makes a git repository on `main`, copies the skill's current scripts into `tools/` and installs the branch guard, so fixtures never carry stale copies. Integration tests in the room-booking fixtures need PostgreSQL 16: `docker compose up -d db` in the project.

## Running an eval

Each run is a subagent given the skill path (`SKILL.md` of this folder, or a snapshot of the previous version for the baseline), the project made by `setup_fixture.py`, a database of its own where the eval needs one, the eval's prompt, and these instructions:

- The user cannot answer. Every question (including `AskUserQuestion`) goes to `outputs/questions.md` with the options offered and the answer assumed (the run's own recommendation), and the run carries on with it. Anything shown to the user before or between questions (a recap, the map) goes there too, in order.
- Do not commit.
- `outputs/report.md` is the final message to the user, exactly.
- `outputs/log.md` is the ordered log of what the run did, in this form, so reviewers can scan it:

  ```
  1. [loading skill] Read SKILL.md and references/adopt.md
  2. [codebase inspection] Listed entry points in web.py: 6 routes
  3. [unit tests] uv run pytest: 2 passed, 1 failed (test_fee_is_capped)
  ```

  One step per line, numbered, each with a tag naming the kind of step: `[loading skill]`, `[git]`, `[codebase inspection]`, `[question]`, `[documents]`, `[unit tests]`, `[integration tests]`, `[architecture check]`, `[traceability]`, `[report]`. The command and its real result go on the same line.

The format of `log.md` belongs to the eval, not to the skill: the skill keeps no log in the user's project.

### Short runs

An eval with a `run_note` is a shortened run of another eval, for testing one step several times at a fraction of the cost. `adopt-confirmation` replays `adopt-library-loans` up to the confirmation questions of the first area. Add to the run instructions: "This is a shortened run. Follow the skill until the confirmation questions for the first area are written to outputs/questions.md, then stop. Do not write the shared documents, CLAUDE.md, tools/, tests or tool configuration; docs/adoption.md is allowed. outputs/report.md holds one line saying where you stopped." Run three samples rather than one: the step is about form, and two runs of the same instructions have produced one clear recap and one unclear one.

## Grading with less cost

An eval iteration is mostly agent tokens: the runs, then a grader agent per eval that re-runs the checks. `grade_mechanical.py` does the part of grading that is a fact about the project: it runs the tests and tools, reads git, greps the domain, compares documents with `HEAD`, runs the branch guard, and probes the cases that matter (a stored booking over the new limit still blocking its room; which write paths a MySQL guarantee covers). It decides about half of the assertions in about a second per run, the same way every time.

```
uv run evals/grade_mechanical.py change-booking-limits <project> --outputs <run outputs> \
    --env DATABASE_URL=postgresql://postgres:test@localhost:5433/<database> --out mechanical.json
```

The output has `decided` (pass or fail with evidence), `needs_judgment` (assertions that need reading, each with the numbers that help) and `tools` (unit, integration, mypy, ruff, import-linter, traceability). Give the grader agent `mechanical.json` and tell it to grade only `needs_judgment`; that is the part that needs reading questions.md, the report and test intent.

- Checks are tied to assertions by the start of their text. When you reword an assertion in `evals.json`, the script stops with an error naming the check to update.
- `DATABASE_URL` must follow the project's own convention. The change-db-swap runs refuse any database name that does not end in `_test`. A fixture that cannot set up is reported as needing judgment, not as a failure.
- `run_grading.py` runs the script over a whole iteration folder (`eval-*/<configuration>/run-*/`) and writes `mechanical.json` beside each run, creating one database per run:

  ```
  uv run evals/run_grading.py <iteration> --db-suffix _i2 \
      --pg-url 'postgresql://postgres:test@localhost:5433/{db}' --pg-container <postgres container> \
      --mysql-url 'mysql://root:test@127.0.0.1:3306/{db}' --mysql-container <mysql container>
  ```

  The twelve runs of an iteration take about 30 seconds.
- Validated against 12 iteration-2 runs: it decided 66 of 130 assertion-runs and agreed with the agent graders on all 66.
- To compare a new skill version with the 0.3.0 baseline, keep the baseline projects and grade them again with the script when assertions change, instead of re-running them.
