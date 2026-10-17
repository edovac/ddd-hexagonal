# Java / Kotlin

Config snippets are starting points; check them against the current documentation of each tool and library version.

## Layout

```
com.example.app
├── domain            entities, value objects, domain services, errors (no framework annotations)
├── application       one class per use case, DTOs
│   └── port          interfaces owned by the core
└── adapter
    ├── web           driving: controllers
    ├── persistence   driven: repositories implementing ports
    └── ...           mail, storage, identity provider
src/test/.../unit
src/test/.../integration
```

The composition root (Spring configuration, Guice module or manual wiring) is the only place that sees every package. Keep framework annotations out of `domain` and `application`; map persistence entities in the adapter.

## Tools

| Purpose | Tool |
| --- | --- |
| Tests | JUnit 5 |
| Integration database | Testcontainers |
| Static analysis | Error Prone or SpotBugs (Java); detekt and ktlint (Kotlin) |
| Architecture check | ArchUnit, run as ordinary tests |

Commands for `CLAUDE.md`: the Gradle or Maven test tasks for unit and integration suites, plus the static analysis task.

## Architecture check (ArchUnit)

```java
@AnalyzeClasses(packages = "com.example.app", importOptions = ImportOption.DoNotIncludeTests.class)
class ArchitectureTest {
  @ArchTest
  static final ArchRule layers = Architectures.onionArchitecture()
      .withOptionalLayers(true)
      .domainModels("..domain..")
      .applicationServices("..application..")
      .adapter("web", "..adapter.web..")
      .adapter("persistence", "..adapter.persistence..");

  @ArchTest
  static final ArchRule domainHasNoFramework =
      noClasses().that().resideInAPackage("..domain..")
          .should().dependOnClassesThat().resideInAnyPackage(
              "org.springframework..", "jakarta..", "javax.persistence..");
}
```

`onionArchitecture` also forbids adapters from depending on each other. Add each framework of the stack table to the second rule.

Verified with ArchUnit 1.4.1 and JUnit 5.11 on JDK 21 (Maven, in Docker): a planted application → adapter import and an adapter → adapter import fail `layers`, and a `@jakarta.persistence.Entity` in `domain` fails `domainHasNoFramework`.

**Trap:** without `.withOptionalLayers(true)`, `onionArchitecture()` fails a correct codebase with "Layer 'domain service' is empty" unless you also declare `.domainServices(...)` and have classes there. Keep the option, or declare every layer you really use. Imports needed: `ImportOption`, `AnalyzeClasses`, `ArchTest`, `ArchRule`, `Architectures`, and a static import of `ArchRuleDefinition.noClasses`. ArchUnit's JUnit 5 engine runs the `@ArchTest` fields as ordinary tests, so the normal test task is the gate.

## Conventions

- Exact quantities: `BigDecimal` with a fixed scale, or integer value objects; Kotlin `data class` or Java `record` for value objects.
- Time through an injected `Clock`; never `Instant.now()` in the domain.
- Test tagging: a comment `// @rule AL-06` or `@Tag("AL-06")` on each test, plus `@usecase` for use cases.
- Domain errors carry an English `code`; messages come from resource bundles.

## Logging

Only when the project adopted a logging policy (`references/logging.md`). Starting points, to check against current documentation.

- Facade: SLF4J (has `trace`), Logback with a JSON encoder behind it; one `Logger` per class in application and adapter code.
- Correlation ID: SLF4J `MDC`, set by the driving adapter (servlet filter or interceptor) and cleared at the end of the request; the encoder writes MDC fields on every entry.
- Masking: personal-data value objects override `toString()` to return the masked form (a Java `record` or Kotlin `data class` prints every field by default, so override it).
- Architecture check: an ArchUnit rule `noClasses().that().resideInAPackage("..domain..").should().dependOnClassesThat().resideInAPackage("org.slf4j..")`.

## Integration tests

Testcontainers with the production database engine and version, schema from the migration tool (Flyway or Liquibase), each test in a rolled-back transaction or against a clean schema. No H2 or other embedded substitute for the production engine.
