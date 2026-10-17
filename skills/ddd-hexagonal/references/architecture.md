# Architecture rules: DDD + hexagonal-lite

Read this before planning the first use case in a project. The names of folders vary by language (see the language file); the dependency rule does not.

## Contents

1. The dependency rule
2. Layers and what lives in them
3. Ports: when to create one
4. DDD building blocks
5. Application services
6. Errors, messages and language
7. Read side
8. Anti-patterns

## 1. The dependency rule

```
driving adapters (HTTP controllers, CLI, cron)  ->  application  ->  domain  <-  driven adapters (database, mail, storage)
                                                          ^ ports (interfaces) are owned by application/domain
```

- The domain imports nothing from frameworks, the database driver, the template engine, the HTTP layer or the clock/randomness of the platform.
- The application layer imports the domain and its own ports, nothing from adapters.
- Adapters import the core and implement its ports. Adapters never import each other.
- Wiring (dependency injection, composition root) is the only place that knows every layer.

The architecture check in the language reference enforces exactly this and runs in CI. If it fails, fix the code, not the check.

## 2. Layers and what lives in them

| Layer | Contains | Never contains |
| --- | --- | --- |
| Domain | Entities, aggregates, value objects, domain services (pure rules), domain errors | I/O, framework types, SQL, serialisation |
| Application | One class per use case, ports, DTOs for input and output, transaction boundary | Business rules (move them into the domain), HTTP or SQL details |
| Driving adapters | Controllers, CLI commands, schedulers, request parsing, response rendering, authorisation wiring | Rules, SQL |
| Driven adapters | Repositories (SQL), mail, external identity, storage, system clock | Rules |

A rule has one implementation, in the domain, and the rule table names it. If two places need it, they call the same domain service.

## 3. Ports: when to create one

Create a port when at least one is true:

- There is, or plausibly will be, a second implementation (storage provider, identity provider).
- The use case must be tested without the real thing (clock, mail, random, external HTTP).
- It is persistence for an aggregate (repository), so use cases can be tested with an in-memory fake.

Do not wrap the web framework, the template engine, the dependency injection container, or report writers. A port per class is boilerplate that buys nothing.

Rules for ports:

- The interface lives with the core, in the vocabulary of the domain (`TimeEntryRepository.save(entry)`, not `insertRow`).
- Repositories return domain objects, not arrays or rows.
- Every in-memory fake gets the same contract tests as the real adapter, so the fake cannot drift.

## 4. DDD building blocks

- **Ubiquitous language:** one term, one meaning, in the code, tests, tables and conversation. The glossary lives in `domain-model.md`; when code and glossary diverge, rename the code.
- **Bounded contexts:** group concepts that share a model and change together; contexts refer to each other by ID only. In a small app they are folders and discipline, not services.
- **Aggregates:** a cluster saved in one transaction that guarantees its own invariants. Children never exist or change without the root. Keep aggregates small; reference other aggregates by ID.
- **Value objects:** immutable, validated on construction, compared by value, no identity (money, quantity of time, period, percentage). Never use raw floats for quantities that must add up exactly.
- **Domain services:** stateless rules that do not belong to one entity (a split calculation, an eligibility query result checker).
- **Domain events:** named facts. Introduce a dispatcher only when something must react; until then they are vocabulary for code, tests and the audit log.

## 5. Application services

Every use case class follows the same shape, so reviews are fast:

```
authorise actor -> load aggregates through ports -> guard (locks, state) -> apply domain behaviour / validate
-> save through ports -> record audit -> commit (one transaction)
```

If a use case grows an `if` that expresses a business rule, move that rule into the aggregate or a domain service and add its ID to the rule table. A rule that exists only in a use case is invisible to the other use cases that need it.

Authorisation is checked in the application layer in addition to any route-level check; the interface hides, the server enforces.

## 6. Errors, messages and language

- The domain raises typed errors or returns violation codes in English (`allocation_exceeds_total`). The code table is in `business-rules.md`.
- The text shown to users lives in translation files and templates, keyed by those codes. The domain never contains user-facing sentences.
- This keeps the core testable and lets a second language be added without touching rules.

## 7. Read side

Queries that only read and hold no rules (reports, lists, exports) may go straight to the database through query classes that return plain row objects. They do not load aggregates. If a figure needs a rule (for example "unfunded"), reuse the rule's single implementation or a shared SQL fragment documented next to it, and test that report totals equal the aggregate sums.

## 8. Anti-patterns to refuse

- Anemic domain: entities that are bags of fields while rules live in services and controllers.
- The domain importing a framework, an ORM annotation or a date/time call that cannot be controlled in tests.
- Business rules in SQL reports, templates, controllers or adapters.
- Repositories returning arrays or leaking query builders to callers.
- One interface per class "for hexagonal", with a single implementation and no test seam.
- A cross-aggregate check hidden inside an aggregate, such as "total per day across entries". Put it in the application layer.
- Mocking the database in integration tests.
