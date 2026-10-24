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
