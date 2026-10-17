# TypeScript / Node

Use `"strict": true` in `tsconfig.json`. Config snippets are starting points; check them against the current documentation of each tool.

## Layout

```
src/
├── domain/            entities, value objects, domain services, errors (no imports from outside domain)
├── application/       one class or function per use case, DTOs
│   └── ports/         interfaces owned by the core
├── adapters/
│   ├── http/          driving: routes, controllers, request validation
│   ├── persistence/   driven: repositories (SQL) implementing ports
│   └── ...            mail, storage, identity provider
├── queries/           read side: plain row queries for reports
└── main.ts            composition root: wires everything
tests/
├── unit/
└── integration/
```

## Tools

| Purpose | Tool |
| --- | --- |
| Tests | Vitest (or Jest) |
| Type checking | `tsc --noEmit` with strict mode |
| Lint | ESLint |
| Architecture check | dependency-cruiser |

Commands for `CLAUDE.md`: `npx vitest run tests/unit`, `npx vitest run tests/integration`, `npx tsc --noEmit`, `npx eslint .`, `npx depcruise src --config .dependency-cruiser.cjs`.

## Architecture check (dependency-cruiser)

```js
// .dependency-cruiser.cjs
module.exports = {
  forbidden: [
    { name: 'domain-is-isolated', severity: 'error',
      from: { path: '^src/domain' }, to: { pathNot: '^src/domain' } },
    { name: 'application-not-on-adapters', severity: 'error',
      from: { path: '^src/application' }, to: { path: '^src/adapters' } },
    { name: 'no-adapter-to-adapter', severity: 'error',
      from: { path: '^src/adapters/([^/]+)/' },
      to: { path: '^src/adapters/', pathNot: '^src/adapters/$1/' } },
  ],
  options: { tsConfig: { fileName: 'tsconfig.json' } },
};
```

The first rule also blocks Node built-ins and npm packages inside the domain, which is the intent: no I/O and no framework there. Allow a specific pure library explicitly if truly needed, and note it in the technical spec.

Verified with dependency-cruiser 18 and TypeScript 6: a planted `import fs` in `domain/`, an application import of an adapter, and an adapter importing another adapter were each reported (the `$1` capture in the third rule works).

**False-pass trap:** dependency-cruiser supports TypeScript below version 7. With TypeScript 7 installed it prints "no dependency violations found (0 modules, 0 dependencies cruised)" and exits 0, so the check silently passes. Pin `typescript@^6` (or whatever range the installed dependency-cruiser supports), and make CI fail if the output reports 0 modules. After setting the check up, plant one violation and confirm it is reported.

## Conventions

- Exact quantities: integer value objects (cents, hundredths), never `number` arithmetic on decimals.
- Time and randomness through injected ports; no `Date.now()` or `new Date()` in the domain.
- Parse and validate input at the adapter edge into DTOs; the domain receives typed values.
- Test tagging: a comment `// @rule AL-06` (and `// @usecase UC-01`) in each test or `describe` block, or the ID in the test title.
- Errors: domain errors carry an English `code`; messages come from translation files.

## Logging

Only when the project adopted a logging policy (`references/logging.md`). Starting points, to check against current documentation.

- Facade: pino (JSON by default; has `trace`). Pass a child logger into application classes and adapters.
- Correlation ID: `AsyncLocalStorage` set by the driving adapter, read by a pino `mixin` so every entry carries it.
- Masking: personal-data value objects override `toString()` and `toJSON()` to return the masked form. pino's `redact` option is a safety net, not the control.
- Architecture check: a dependency-cruiser `forbidden` rule from the domain folder to `pino`.

## Integration tests

Real database through Docker Compose or Testcontainers, schema from the migration files, each test in a rolled-back transaction or a freshly truncated schema. No in-memory database as a stand-in for the production engine.
