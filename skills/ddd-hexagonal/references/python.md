# Python

Use type hints everywhere and run a strict type checker. Use **uv** as the build and dependency manager. Snippets below were run with uv 0.9 and import-linter in Docker; still check them against the current documentation of each tool.

## Project and dependencies (uv)

- Create with `uv init --package <name>` (src layout, installable project) and set `requires-python` in `pyproject.toml`.
- Add a runtime dependency with `uv add <pkg>` and a development tool with `uv add --dev <pkg>` (stored in `[dependency-groups] dev`). `uv add` is the point where the "ask before adding a dependency" rule applies: ask first, run it after approval, then add the library to the technical spec's stack table.
- `uv.lock` is committed. Install with `uv sync` locally and `uv sync --frozen` in CI so the lock file decides versions.
- Run everything through `uv run` (`uv run pytest`), so the commands in `CLAUDE.md` work without activating a virtual environment and without setting `PYTHONPATH`.
- The project must be installable for the architecture check to find its package. With hatchling:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/myapp"]
```

(`uv init --package` generates an equivalent build system; keep whichever it created.)

## Layout

```
src/myapp/
├── domain/            entities, value objects, domain services, errors (standard library only)
├── application/       one class per use case, DTOs
│   └── ports.py       Protocols or ABCs owned by the core
├── adapters/
│   ├── web/           driving: routes, controllers
│   ├── persistence/   driven: repositories implementing ports
│   └── ...            mail, storage, identity provider
├── queries/           read side: plain row queries
└── bootstrap.py       composition root
tests/
├── unit/
└── integration/
```

## Tools

| Purpose | Tool |
| --- | --- |
| Project and dependencies | uv |
| Tests | pytest |
| Type checking | mypy (`strict = true`) or pyright |
| Lint and format | ruff |
| Architecture check | import-linter |

Commands for `CLAUDE.md`: `uv run pytest tests/unit`, `uv run pytest tests/integration`, `uv run mypy src`, `uv run ruff check .`, `uv run lint-imports`.

## Architecture check (import-linter)

```toml
# pyproject.toml
[tool.importlinter]
root_package = "myapp"
include_external_packages = true   # required for forbidden contracts on third-party modules

[[tool.importlinter.contracts]]
name = "Layers point inward"
type = "layers"
layers = ["myapp.adapters", "myapp.application", "myapp.domain"]

[[tool.importlinter.contracts]]
name = "Domain uses no framework or driver"
type = "forbidden"
source_modules = ["myapp.domain", "myapp.application"]
forbidden_modules = ["sqlalchemy", "django", "flask", "fastapi", "psycopg", "requests"]
```

Extend `forbidden_modules` with each library of the stack table. Add an `independence` contract so adapter packages cannot import each other. Verified behaviour: with `import requests` in `domain/` and an application module importing an adapter, `uv run lint-imports` reports both contracts as broken and names the import lines. Indirect chains (application → domain → requests) are reported too, which is usually what you want.

## Conventions

- Exact quantities: `Decimal` or integer value objects, never `float`. Use frozen dataclasses for value objects.
- Time and randomness through injected ports; no `datetime.now()` in the domain.
- Test tagging: `# @rule AL-06` (and `# @usecase UC-01`) in the test's docstring or on the line above.
- Domain errors carry an English `code`; messages come from translation files.

## Integration tests

Real database (Docker Compose or testcontainers), schema from the migration files, a fixture that wraps each test in a rolled-back transaction. No SQLite stand-in for another engine.
