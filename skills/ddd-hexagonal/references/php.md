# PHP

Use PHP 8.x with `declare(strict_types=1)` in every file. Config snippets are starting points; check them against the current documentation of each tool before relying on them.

## Layout

```
src/
├── Domain/            entities, value objects, domain services, domain errors (no framework, no PDO)
├── Application/       one class per use case, DTOs
│   └── Port/          interfaces owned by the core (repositories, Clock, Mailer ...)
├── Repository/        PDO adapters implementing the repository ports (or Infrastructure/Persistence)
├── Controller/        driving adapters: HTTP handlers
├── Middleware/        driving adapters: session, CSRF, auth
└── Report/            read side: query classes returning plain rows
tests/
├── Unit/              domain and application with in-memory fakes
└── Integration/       adapters and use cases against the real database
```

Use a DI container (for example PHP-DI) as the only place that wires layers.

## Tools

| Purpose | Tool |
| --- | --- |
| Tests | PHPUnit |
| Static analysis | PHPStan at level 8 or higher |
| Style | PHP_CodeSniffer with PSR-12 |
| Architecture check | Deptrac |

Commands to put in `CLAUDE.md`: `vendor/bin/phpunit --testsuite Unit`, `vendor/bin/phpunit --testsuite Integration`, `vendor/bin/phpstan analyse`, `vendor/bin/phpcs`, `vendor/bin/deptrac analyse`.

## Architecture check (Deptrac)

```yaml
deptrac:
  paths: [./src]
  layers:
    - name: Domain
      collectors: [{ type: directory, value: src/Domain/.* }]
    - name: Application
      collectors: [{ type: directory, value: src/Application/.* }]
    - name: Adapters
      collectors:
        - { type: directory, value: src/Repository/.* }
        - { type: directory, value: src/Controller/.* }
        - { type: directory, value: src/Middleware/.* }
    - name: Vendor
      collectors:
        - { type: classNameRegex, value: '#^(PDO|Slim|Twig|Psr|PHPMailer)#' }
  ruleset:
    Domain: ~
    Application: [Domain]
    Adapters: [Application, Domain, Vendor]
```

Domain and Application are not allowed to reach `Vendor`. Extend the regex with each framework or driver in the stack table; avoid backslashes in it, because YAML and Deptrac escape them differently and the check then fails with "Invalid regex pattern". (Verified with Deptrac 2.0: a `use PDO;` in `Domain/` is reported as `DependsOnDisallowedLayer`.) Adapters must not import each other; if a split between driving and driven adapters matters, make them separate layers.

## Existing code: baseline (Adopt)

Only when adopting existing code (`references/adopt.md` section 8). Deptrac writes its own baseline:

```
vendor/bin/deptrac analyse --formatter=baseline --output=deptrac.baseline.yaml
```

and `deptrac.yaml` imports it with a top-level `imports: [deptrac.baseline.yaml]`. The file holds `skip_violations` (class → classes it may still depend on). Verified with Deptrac 2.0.6: the listed violation is reported as skipped, a new one fails. The imported file must exist before the first run (write `deptrac: {}` into it), or Deptrac stops. Re-run the formatter after a Change removes violations, and check that the file only shrank.

Expected failure for a rule the code gets wrong: PHPUnit has none. Put the test for the intended rule in a group, `#[Group('known-mismatch')]` with the rule ID in the test name, exclude the group in `phpunit.xml` (`<groups><exclude><group>known-mismatch</group></exclude></groups>`), and run it with `--group known-mismatch` for the report: it should fail until the fix lands.

## Conventions

- Hours, money and other exact quantities: value objects over integers (hundredths, cents), never floats.
- Dates: inject a `Clock` port; do not call `new DateTimeImmutable()` in the domain.
- Prepared statements only, `PDO::ATTR_EMULATE_PREPARES` off; repositories return domain objects.
- Test tagging: a docblock line `@rule AL-06` (and `@usecase UC-01`) on each test method or class.
- Test names read as rules: `test_full_each_allows_allocations_above_entry_total`.

## Logging

Only when the project adopted a logging policy (`references/logging.md`). Starting points, to check against current documentation.

- Facade: PSR-3 `Psr\Log\LoggerInterface` injected into application classes and adapters; Monolog with `JsonFormatter` behind it.
- TRACE: PSR-3 has nothing below `debug`. Log TRACE entries at `debug` with `'trace' => true` in the context, and filter them out outside local and test.
- Correlation ID: a Monolog processor adds it to every record; the driving adapter sets it per request.
- Masking: personal-data value objects implement `__toString()` returning the masked form and keep the raw value behind an explicit getter.
- Architecture check: add `Psr\Log` and `Monolog` to the collectors the Domain layer must not depend on.

## Integration tests

Run against the same database engine and version as production (Docker locally, a service container in CI). Build the schema from the migration files, wrap each test in a transaction that is rolled back, and load fixtures per test. Do not use SQLite as a stand-in for MySQL or PostgreSQL.

## Shared-hosting note

If production has no shell or Composer, build `vendor/` locally or in CI and upload it, and keep every runtime feature in pure PHP. Record such limits in the technical spec's hosting section, because they decide which libraries are allowed.
