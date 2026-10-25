# Adding a language

When the project's language has no reference file, create one with the same sections as `php.md` before building anything. Tell the user you are doing it and ask them to confirm the tool choices.

Save it in the project as `.claude/ddd-hexagonal/<language>.md`, commit it with the project, and point to it from `CLAUDE.md`. Do not save it in the skill folder: in a plugin install that folder is a cache that each update replaces, so the file would be lost. If the language is likely to come up again, suggest the user contribute the file to the plugin as `references/<language>.md`.

## What the file must answer

1. **Layout:** folder or package names for domain, application (with ports), driving adapters, driven adapters, queries (read side), composition root, and the two test folders.
2. **Tools:** test runner, static analysis or type checker, style tool, architecture check, with the exact commands for `CLAUDE.md`.
3. **Architecture check:** a configuration that fails the build when the domain imports a framework, driver or adapter, when the application imports an adapter, or when adapters import each other. Prefer an established tool for the language. If none exists, use `scripts/check_imports.py`:

   ```
   uv run tools/check_imports.py --dir src/domain --forbid "^(use|import|require)\b.*(Framework|Driver)"
   ```

   It scans files for import-style lines matching a pattern and exits non-zero on any match. Run it in CI like any other test.
4. **Exact quantities:** how to represent money, time and other values that must add up exactly.
5. **Time and randomness:** how to inject them as ports.
6. **Test tagging:** the convention for citing `@rule` and `@usecase` IDs (any text containing the ID in a test file counts for `check_traceability.py`).
7. **Integration database:** how to run the real engine locally and in CI and roll back between tests.
8. **Error codes:** how domain errors carry an English code and where messages live.
9. **Logging:** the facade and JSON output, how TRACE maps if the library lacks it, how the correlation ID travels (context variable, MDC), how a value object masks its string form, and how the architecture check forbids the logging library in the domain (`references/logging.md`).
10. **Existing code (Adopt):** how the architecture check records a baseline of known violations so only new ones fail (the tool's own mechanism, or `check_imports.py --write-baseline` and `--baseline`), and the marker for a test expected to fail (a strict expected failure, or a tag excluded from the normal run).

Keep the file short and mark every configuration snippet as a starting point to be checked against current documentation.
