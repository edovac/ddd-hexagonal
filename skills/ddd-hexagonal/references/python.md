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

## Existing code: baseline (Adopt)

Only when adopting existing code (`references/adopt.md` section 8). import-linter has no baseline file: list each known violation as an `ignore_imports` entry on the contract it breaks, copied from the `a -> b` lines that `uv run lint-imports` prints.

```toml
[[tool.importlinter.contracts]]
name = "Core uses no driver"
type = "forbidden"
source_modules = ["myapp.models", "myapp.services"]
forbidden_modules = ["requests"]
# Adopt baseline: known violations; the list only shrinks.
ignore_imports = ["myapp.services.pricing -> requests"]
```

Use exact module names, never wildcards (`myapp.services.**`): a wildcard also hides the next violation. Verified with import-linter 2.15: the listed import passes, a new one in another module breaks the contract, and an entry that no longer matches fails the run with "No matches for ignored import", so a fixed violation must leave the list.

Expected failure for a rule the code gets wrong: `@pytest.mark.xfail(strict=True, reason="BK-04: code allows 8 h; see open point")`. `strict=True` turns the day the fix lands into a failure, which reminds the Change to remove the marker.

## Conventions

- Exact quantities: `Decimal` or integer value objects, never `float`. Use frozen dataclasses for value objects.
- Time and randomness through injected ports; no `datetime.now()` in the domain.
- Test tagging: `# @rule AL-06` (and `# @usecase UC-01`) in the test's docstring or on the line above.
- Domain errors carry an English `code`; messages come from translation files.

## Logging

Only when the project adopted a logging policy (`references/logging.md`). Starting points, to check against current documentation.

- Facade: the standard library `logging` (`logger = logging.getLogger(__name__)`) with a JSON formatter configured once in the composition root; a formatter library is a dependency to approve like any other.
- TRACE: register a custom level once: `logging.addLevelName(5, "TRACE")`, and log with `logger.log(5, ...)`.
- Correlation ID: a `contextvars.ContextVar` set by the driving adapter and added to every record by a `logging.Filter`.
- Masking: personal-data value objects (frozen dataclasses) define `__str__` and `__repr__` returning the masked form, with `field(repr=False)` on the raw value.
- Architecture check: add `"logging"` (and any logging library) to a `forbidden` contract whose `source_modules` is only the domain. Verified: `import logging` in `domain/` breaks the contract while the application layer may still import it.

## Integration tests

Real database (Docker Compose or testcontainers), schema from the migration files, a fixture that wraps each test in a rolled-back transaction. No SQLite stand-in for another engine.
