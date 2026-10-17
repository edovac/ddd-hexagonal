# Change procedures

Read the section for the kind of change you are making. All kinds share the opening and the closing steps; the middle differs.

## Contents

1. Opening (every change)
2. Rule change
3. Use case change (new feature, new use case, altered or removed use case)
4. Technical change (stack, schema, hosting, architecture)
5. Rename a term
6. Closing (every change) and the report

## 1. Opening (every change)

1. **Branch check**, as in Build.
2. **Name the kinds.** A request is often more than one kind: "add refunds" is a new use case and new rules, and may be a technical change if it needs a payment provider. Say in one line which kinds you see and in what order you will do them, and wait for a yes before editing. Doing this first prevents choosing the scope by yourself.
3. **Find the impact** with `scripts/rule_impact.py <IDs>` (or `tools/rule_impact.py`). For a rename or a technical change, also grep for the old word or technology name, because documents and code mention those without citing an ID. Read what the script lists before deciding anything.
4. **Existing data.** If the change can make stored data invalid (a stricter rule, a changed schema, a removed field), ask the user how to treat it (apply to new data only, migrate, or grandfather) with a recommendation, before editing.
5. **Large changes.** If the impact touches more than about five use cases, or includes a schema change, propose an order and a milestone for each step instead of doing everything at once, and update the rollout list in the functional spec.

## 2. Rule change

IDs are stable: a tightened or relaxed rule keeps its ID. A rule whose meaning changes, or that is split, gets a new ID and the old text is marked "(superseded by XX-nn)". A removed rule is marked "(removed)" and its ID is never reused; the traceability script fails when an ID disappears without a marker.

1. Edit `business-rules.md` first, including the error-code column; update the translation file if a code changes.
2. In use cases, domain model and technical spec, change only the IDs they cite or the enforcement they describe. If the old value (a number, a role) appears outside the rules file, replace it with the ID.
3. Tests first: change tests that encode the old behaviour on purpose (never delete a failing test to turn it green), add tests for the new boundary with `@rule`, watch them fail, then change the code. The value lives in one place in the domain.

## 3. Use case change

Order matters because each document refers to the one before it.

1. **Rules first.** Add the rules the use case needs to `business-rules.md` with new IDs and error codes. Reuse existing rules instead of copying their meaning.
2. **Use case row.** Add `UC-nn` (next free number, never renumber) with actor, main flow, rule IDs and the class that will implement it. For an altered use case, change the row; for a removed one, mark it "(removed)" and keep the number.
3. **Domain model.** New concepts go in the glossary; new aggregates, value objects or ports only when a rule needs them. Name the aggregate that guarantees each new rule.
4. **Technical spec.** Add routes, schema changes (as new migrations, never edits of applied ones) and the line saying which service enforces which new rule.
5. **Functional spec.** Add the behaviour in plain words with the rule IDs, update scope and the rollout milestone if the use case belongs to one.
6. **Implement** with the Build procedure for that use case (test first, adapters only as far as the technical spec calls for). Ask before inventing behaviour the documents do not define.

## 4. Technical change

Examples: swapping the database or a library, adding a queue, splitting a context, moving a port.

1. **Decision.** Write the choice in the technical spec's stack table and add a short "Decisions" entry: what, why, what was rejected. A new dependency needs the user's approval first.
2. **Impact on the architecture.** Name the port the change sits behind. A change that is confined to one adapter should leave the domain and application layers untouched; if it does not, say so and explain why before going on.
3. **Rules that depended on the old technology.** Check whether any rule was guaranteed by it (for example a database constraint that backs a uniqueness or overlap rule). Decide how the new technology guarantees the same rule, and add a test.
4. **Schema and data.** Add new migrations; do not edit a file that has been applied to any environment you cannot throw away. Changing the database engine is the one case where the first migration cannot run on the new engine: do not rewrite it silently. Ask the user whether any real environment has applied it; if one has, add new migrations and keep the old files, and if none has, a rewrite is acceptable once the user confirms and the decision is written in the Decisions entry. Include how existing data moves and how to roll back.
5. **Tooling.** Update the architecture-check configuration (forbidden modules), Docker or CI setup, the integration test setup and the hosting constraints.
6. **Verify** on the real new technology (start it in Docker), not on a substitute.

## 5. Rename a term

1. Update the glossary in the domain model first (code term, interface term, meaning, and the old term under "avoid").
2. Rename in documents, code, tests, translation keys, database names (through a migration) and error codes, using the grep for the old word as the checklist.
3. Do not change rule IDs for a rename; IDs identify rules, not words.
4. Finish with a grep that finds no old term outside the "avoid" entry.

## 6. Closing (every change) and the report

1. Run the traceability check (including the ID-stability comparison against the last commit), unit and integration tests, static analysis and the architecture check; then the light documentation review.
2. Report in this form, then stop; commit only if asked:

```
Change: <one sentence>   Kinds: rule | use case | technical | rename
Rules: changed XX-nn · new XX-nn · superseded/removed XX-nn
Use cases: new UC-nn · changed UC-nn · removed UC-nn
Documents changed: <file: what>
Tests: changed <list> · added <list>   Code: <files>   Migrations: <files>
Existing data: <effect and the decision taken or needed>
Checks: unit · integration · static analysis · architecture · traceability
Open questions: <list or none>
```
