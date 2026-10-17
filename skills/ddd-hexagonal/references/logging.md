# Logging

A default the developer chooses at Bootstrap (`references/interview.md`, step 10): adopt this policy, adapt it, or keep logging out of scope. Record the choice in `technical-spec.md` ("Logging") and a pointer in `CLAUDE.md`. Apply this file only when the policy, or an adapted version, was adopted.

Technical logs are not the audit record. The audit record is business data with its own rules and retention (`business-rules.md`); logs are for operating and debugging the system.

## Contents

1. Where logging happens
2. Entry format
3. Levels
4. Sensitive data
5. Testing
6. Review checklist

## 1. Where logging happens

| Layer | Logs | Why |
| --- | --- | --- |
| Domain | Never | It stays pure and testable. Outcomes leave it as violation codes and domain events, which the application layer logs |
| Application (use case classes) | DEBUG, INFO, WARN, ERROR | The use case owns its outcome |
| Driving adapters (HTTP, CLI, scheduler, consumer) | All levels | The edge where work enters |
| Driven adapters (repositories, mail, external APIs, storage) | All levels | The edge where work leaves |

Use the language's standard logging facade (see the language reference) in the application and adapter layers. It is not a port: there is no second implementation and tests capture it through the facade. Add the logging library to the domain's forbidden imports in the architecture check.

## 2. Entry format

- Structured: JSON in production, `key=value` is acceptable locally. One event per line.
- A fixed English event name per entry (`usecase.completed`), never a sentence built from values. A free-text message is where data leaks.
- Every entry carries `correlation_id`. The driving adapter accepts it from an allowlisted upstream header or creates one, and passes it to the use case and on to driven adapters (context variable, MDC or an explicit parameter, per language).

## 3. Levels

### Per unit: one DEBUG on entry, one INFO on completion

Each unit of work writes exactly one DEBUG entry when it starts and exactly one INFO entry when it ends, whatever the outcome.

| Unit | DEBUG on entry | INFO on completion |
| --- | --- | --- |
| Driving adapter, per request or command | `event=http.in.started` route template (`POST /bookings/{id}`, never the actual path), method | `event=http.in.completed` route template, status, `duration_ms` |
| Use case, per execution | `event=usecase.started` `use_case=UC-01`, actor role | `event=usecase.completed` `use_case=UC-01`, `outcome=ok\|rejected\|failed`, violation code when rejected, `duration_ms` |
| Driven adapter, per port call | `event=adapter.out.started` port and operation (`BookingRepository.save`) | `event=adapter.out.completed` port and operation, `outcome=ok\|failed`, `duration_ms` |

A driven adapter logs per port call, not per SQL statement or HTTP request it makes internally; those are TRACE.

### Other DEBUG (off in production, switched on to investigate)

- **Use case steps:** authorisation decision (`allowed`/`denied`, role), each aggregate loaded (ID, version), each rule check (`rule=BK-01 result=pass|fail`), each domain event raised (name only). Rule IDs in the log connect a production behaviour to `business-rules.md`.
- **Transactions:** begin, commit, rollback with the reason code.
- **Adapter decisions:** cache hit or miss, retry attempt `n/m` and backoff, which implementation is wired to each port at startup.
- **Startup:** effective configuration with secrets removed (log the key and `set|unset`, never the value).

### TRACE (local and test environments only, never production)

- Shapes, not values: field names, counts and sizes (`body.fields=[start,end,room_id] size=212`).
- SQL statements with placeholders, never bound parameters.
- Entry and exit of internal (non-port) methods in adapters, and aggregate state transitions with values masked.
- HTTP headers from an allowlist; `Authorization`, `Cookie` and `Set-Cookie` never.

Where the library has no TRACE level, the language reference says how to map it.

### WARN and ERROR

- A rejected business rule is an expected outcome: INFO with `outcome=rejected` and the violation code, never WARN or ERROR.
- WARN: degraded behaviour the system recovered from (a retry that succeeded, a fallback used, a slow call over its threshold).
- ERROR: an unexpected failure, once, where it is handled (normally the driving adapter), with the exception type and stack trace. Never log the raw exception message from a driver or client: it often contains values. Do not log and rethrow at every layer.

## 4. Sensitive data

The rule is an allowlist: an entry may contain only these kinds of values.

| Allowed | Examples |
| --- | --- |
| Surrogate IDs (random UUIDs or sequence numbers with no meaning) | `booking_id`, `actor_id` |
| Identifiers of the documents | use case ID, rule ID, violation code, event name |
| Technical values | route template, status, duration, count, size, enum value, port and operation |
| Correlation ID | `correlation_id` |

Never logged, at any level:

- Personal data: names, email addresses, phone numbers, postal addresses, IP addresses, dates of birth, national or tax IDs, any natural key that identifies a person.
- Free text a person typed.
- Credentials, tokens, session IDs, API keys, secrets.
- Payment data.
- Special-category data (health, beliefs, and the other GDPR Article 9 categories).
- Request and response bodies, bound SQL parameters, raw driver or client exception messages.

Surrogate IDs are still pseudonymous personal data under GDPR when they can be linked to a person, so the log retention in `technical-spec.md` applies to every log.

How the code enforces it:

- `domain-model.md` marks each field that holds personal data (section "Personal data"). Those fields never appear in a log entry.
- A value object that holds personal data (`Email`, `PhoneNumber`, `Iban`) returns a masked form from its string conversion (`toString`, `__str__`, `__repr__`), so logging one by mistake leaks nothing.
- Log entries are built from named fields, never by dumping an object, a DTO, a request or an exception.

## 5. Testing

- **Canary test:** an integration test runs one use case per driving adapter with recognisable fake values (`canary.person@example.test`, `Canary Surname`, `+00 000 CANARY`), captures every log entry at TRACE, and fails if any canary value appears. Tag it with the privacy rule ID when the project has one.
- **Shape test:** for one use case, assert that exactly one `usecase.started` and one `usecase.completed` entry were written, with the expected `outcome` and the same `correlation_id` as the adapter entries.
- **Masking test:** each personal-data value object's string conversion returns the masked form.

## 6. Review checklist

Used by `references/code-review.md` when the project adopted this policy.

- No logging import in the domain.
- Each changed driving adapter, use case and port method writes one DEBUG on entry and one INFO on completion, with the fields above.
- Every entry carries `correlation_id`, and a fixed event name, not a sentence.
- No value outside the allowlist; no object, DTO, request, response or exception message dumped; no field marked as personal data in `domain-model.md`.
- Rejections are INFO with a violation code; errors are logged once, without the raw message.
- New personal-data value objects mask their string form; the canary test covers new driving adapters.
