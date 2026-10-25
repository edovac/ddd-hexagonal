# <Project> — Technical Specification

<date> · <owner>

How the system in `functional-spec.md` is built. It says which service enforces which rule by ID; rule text is in `business-rules.md`.

## Architecture

<Layer diagram: driving adapters → application → domain ← driven adapters, plus external systems.>

## Stack

| Layer | Choice |
| --- | --- |
| Language | <language and version> |
| Framework | <name> |
| Database | <engine and version> |
| Tests | <runner, static analysis, architecture check> |

A dependency not listed here needs the user's approval before use.

## Hosting constraints

- <Limits that decide which libraries and techniques are allowed.>

## Project structure

<Folder tree from the language reference, with the role of each folder.>

## Database schema

<Schema or link to the migrations; constraints that mirror rules cite the rule ID in a comment.>

## Routes and permissions

| Method | Path | Purpose | Role |
| --- | --- | --- | --- |
| <GET> | `<path>` | <purpose> | <role> |

## Business logic

Which component enforces which rules and how, citing code as `path::symbol`, never by line number. No rule text.

### <Service>

Enforces <IDs>. <Algorithm, inputs, outputs, transaction notes.>

## Authentication and security

<Mechanisms and the table of threats and controls.>

## Logging

<Adopted, adapted or out of scope, as decided at Bootstrap. If adopted: "Follows the skill's logging policy" plus only the differences.>

| Item | Choice |
| --- | --- |
| Library and format | <facade, JSON in production> |
| Destination | <stdout collected by …, file, service> |
| Level per environment | production INFO · staging DEBUG · local and test TRACE |
| Retention | <days; applies to all logs, which hold pseudonymous IDs> |
| Correlation ID header | <`X-Correlation-Id`> |

## Operations

<Backup, jobs, migrations, deploy.>

## Decisions

One entry per decision that changed the stack, a guarantee or a rule's value: what, why, what was rejected, and the evidence for any claim that an alternative cannot work.

- **D-1 <Title>.** <What and why.> Rejected: <alternative and reason>.

## Testing

- **Unit:** every business rule in the domain and service layers; no database, no framework.
- **Integration:** adapters and use cases against the real database engine, schema from migrations, each test rolled back.
- **Logging (if adopted):** canary test that no personal data reaches the logs, shape test of the DEBUG/INFO entries per use case.
- **Manual before release:** <list>.

Rules:

- **Test first** for the domain and service layers.
- **Rule reference:** each test names the rules it covers, `@rule XX-01`, and the use case, `@usecase UC-01`. A rule ID without a test is reported as a gap.
- **Gate:** the pipeline stops on a failing test, static analysis error or architecture check failure.

## Conventions

- Everything in code is English: identifiers, database names, routes, config keys, comments, tests, error codes, commits. User-visible text lives in templates and translation files.
- <Style tool, strictness, migration policy, time zone.>
