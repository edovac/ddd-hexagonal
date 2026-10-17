# <Project> — Domain Model

<date> · <owner>

Concepts, boundaries and ownership of rules. It does not restate the specs.

- **What and why:** `functional-spec.md` · **Rules:** `business-rules.md` · **Use cases:** `use-cases.md`
- **How it is built:** `technical-spec.md`

## 1. Core domain

<The one thing this system must get right.>

## 2. Ubiquitous language

One term, one meaning, in code, tests, tables and conversation. The interface shows the interface-language term; code uses the English one.

| Code | Interface term | Meaning |
| --- | --- | --- |
| `<Term>` | <Term> | <One sentence, or the rule ID that defines it> |

Avoid: <synonyms to ban, with the preferred term>.

## 3. Bounded contexts

| Context | Responsibility | Tables or stores |
| --- | --- | --- |
| **<Core>** (core) | <Responsibility> | <tables> |

Relationships: <who asks whom, by ID only>.

## 4. Aggregates

| Aggregate | Root and children | Guarantees (rule IDs) |
| --- | --- | --- |
| **<Name>** | <Root + children> | <IDs> |

## 5. Value objects

| Class | Rules |
| --- | --- |
| `<Name>` | <Validation, representation, rule IDs> |

## 6. Services and application layer

- Domain services and where they are specified.
- Application classes: one per use case in `use-cases.md`, shaped authorise → load → guard → apply → save → audit.

Dependency direction: driving adapters → application → domain ← driven adapters.

## 7. Ports

| Port | Why it exists (second implementation or test seam) | Adapter |
| --- | --- | --- |
| `<Port>` | <Reason> | <Adapter> |

## 8. Domain events

<Named facts; how they map to the audit record.>

## 9. Personal data

Fields that identify a person or are sensitive. They never appear in logs (`references/logging.md`), and value objects holding them mask their string form.

| Aggregate or value object | Field | Category (personal, special category, credential, payment) |
| --- | --- | --- |
| `<Name>` | `<field>` | <category> |

## 10. Testing the model

Extra expectations from the domain view; test types are in the technical spec.

## 11. How to use this file

- Before a feature, find its concept in section 2 and its home in section 3.
- A new rule is first added to `business-rules.md` with an ID, then goes into an aggregate or domain service with a unit test.
- When a term in code and in the glossary diverge, rename the code.
