# Adopt: bring an existing codebase under the workflow

Use this when the project already has working code but no document set, or only part of one. The rules already exist: they are in the code, in the schema and in people's heads. The job is to find them, have the user confirm them, and pin them with tests, without changing what the application does.

Two things make adoption safe, and every step below protects them:

- **Production code does not change during Adopt.** Adopt writes documents, tests, tool configuration and nothing else. Behaviour changes go through Change afterwards, behind the tests Adopt added. A user who asks to fix something mid-adoption gets the fix recorded as an open point and offered as the next Change.
- **Only the user turns a candidate into a rule.** Code shows what happens, not what was meant. A check in the code may be a bug, a leftover or a workaround, so `business-rules.md` only receives what the user confirmed. Until then a candidate lives in `docs/adoption.md`.

## Contents

1. Opening
2. Map the codebase (first run only)
3. Shared documents and tools (first run only)
4. Candidates for one area
5. Confirmation
6. Write the area's documents
7. Tests that pin behaviour
8. Architecture check with a baseline
9. Closing and the report
10. A project that is partly adopted

## 1. Opening

1. **Branch check**, as in Build. Adopt touches many files; a branch keeps them reviewable. Start the session task list with this file's sections; on a later run, put the area under "Now" in `docs/plan.md` (on the first run the plan is written in section 2).
2. Read what exists: `README`, any spec, ADR, wiki export or `CLAUDE.md`, the manifests, the migrations or schema, and the test folders. Detect the language and read its reference file.
3. If `docs/adoption.md` exists, this is a later run: read it and `docs/plan.md`, skip sections 2 and 3, and continue with the area the user names or the next one not ticked in the plan.
4. **Starting state.** Run the existing test suite once, as it is. Record the result (pass, fail, cannot run and why) with the commit in `docs/adoption.md`. Adopt must leave every test that passed still passing, and it must not try to fix the ones that already failed: they are findings for the report.

## 2. Map the codebase (first run only)

The goal is a list of areas small enough to adopt one at a time, not an understanding of every line.

1. List the entry points: HTTP routes, CLI commands, scheduled jobs, queue consumers, event handlers. Each one an actor can trigger is a likely use case.
2. List where data lives: tables, columns, constraints, triggers, ORM models.
3. List the external systems: mail, payment, identity, file storage, other services.
4. Note the existing layering, if any (`models/`, `services/`, `controllers/`, a framework's conventions), and where business decisions seem to sit.
5. Group the entry points and tables into **areas**: sets that share the same nouns and change together. They are candidate bounded contexts, but an area only needs to be a sensible unit of work. For each give the entry points, the modules it includes, the main tables and a rough size. A module goes with the area whose use cases call it; one that several areas call goes with the first area adopted and is named in the others' rows.
6. Recommend the first area. A good first area is small, holds real rules, and matters to the user; an area with some existing tests is easier.

On a large codebase, run the mapping in parallel: one Explore agent per group of entry points (or per top-level package), each told to return entry points, tables touched and file:line references, not file dumps. Merge their lists yourself.

Write the map into `docs/adoption.md` from `assets/templates/adoption.template.md`, then ask the user to pick the area, with the recommendation first. In the same question, name each module whose place is not obvious (a calculation the area's use cases call that could stand as its own concept, a module another area also uses) with a recommendation: "`fees.py` is used by the return: include it in Lending (recommended), or leave it for a later area". The user fixes the boundary once, before anything is traced, so the candidates, the recap and the questions all follow from the same area. Then write `docs/plan.md` (`references/progress.md`): the areas in the agreed order under "Adoption", the first one under "Now".

## 3. Shared documents and tools (first run only)

Write the parts of the document set that do not belong to one area, from what the code shows. Interview the user (`references/interview.md` habits: one decision at a time, a recommendation in front) only for what the code cannot answer.

- **Functional spec:** purpose, users and roles as the code and the user describe them. Areas not yet adopted go under "Scope" as "not adopted yet; see `adoption.md`", so nobody reads the spec as complete.
- **Technical spec:** the stack **as found**: every dependency in the manifests goes into the stack table, since the user already owns them. The architecture section describes the code as it is and, separately, the target layout from the language reference that new and moved code will use. The enforcement table starts empty and grows per area.
- **Domain model:** the glossary starts here and grows per area.
- **`CLAUDE.md`, `tools/` and the branch guard:** as in `references/bootstrap.md`. Record the working rules from SKILL.md's defaults; the logging question is asked as in the interview, never assumed.

A tool the project does not have yet (the architecture check, a test container library) is a new dependency: ask before adding it.

## 4. Candidates for one area

Trace each entry point of the area from the request to the database and back, and write down every place where the code **decides** something:

- a check that rejects input or a state (a validation, an `if` that raises or returns an error, an HTTP 4xx);
- a calculation (prices, totals, dates, rounding, limits);
- a state transition (what can follow what, what can be undone);
- a permission check (who may do it);
- a database guarantee (unique, check, foreign key, not null, a trigger), because it is a rule even when no code mentions it;
- a configuration value that changes behaviour (a limit read from settings).

For each one, add a row to the area's candidate table in `docs/adoption.md`:

| Column | What goes in it |
| --- | --- |
| Candidate | One testable sentence, written like a rule in `business-rules.md`, with the edge included as the code has it (`<` or `<=`) |
| Evidence | Every place it is enforced, as `file:line`. Two places is worth noting; two places with different values is a finding |
| Today on failure | What the code does: the exception, message, status code or silent behaviour |
| Tested by | The existing test that covers it, or none |

Also add, per entry point, a use case candidate (actor, action, entry point, the candidates it applies), and a terms list: the nouns the code uses (class, table and route names) next to the words the user's interface uses.

Candidates and findings cite `file:line`, because the user confirms them now and the section is deleted when the area closes. What moves into the lasting documents and into the map's notes cites `path::symbol` instead (section 6).

Record **findings** separately: the same check with different values in two places, a check on one path and not on another that should share it, a rule enforced only in the interface, a calculation on floats for money, dead code that still enforces something. These are questions, not fixes.

Read every evidence line yourself before writing it down. If Explore agents traced the entry points, treat their output as leads to verify: a wrong line reference turns into a wrong rule.

**Stay inside the area.** The area is what the user picked, including the modules listed in its row. Tracing an entry point can lead into code outside it (a call into the catalog, a module the user left for a later area). Record what that code decides as a note for that area in the map, not as a candidate here, unless the user widens the area. An area that grows while it is traced is no longer the unit the user picked, and its review gets harder in the same proportion.

## 5. Confirmation

Confirmation costs the user attention, and a long run of questions wears it out before the questions that matter. So spend it where the answers change something.

1. **One recap, on top.** Before the first confirmation question, and only there, give one short summary. The codebase map of section 2 is shown as the map, not as another recap, so the user meets a single summary right before the questions it introduces.
   - How many candidates the area has, split into groups: plain data integrity, rules that look settled, rules that need a decision. Each candidate is in exactly one group, and a finding that needs a decision is listed under the decisions, not again on its own.
   - The decisions that matter most, three to five, each written as the choice the user will make, with what the code does today: "Loan limit: 3 (what the code enforces) or 5 (the constant in `web.py` that never takes effect)". A statement of fact ("a second return charges the fee again") leaves the user guessing what is being asked.
   - The number of decisions here matches the questions that follow, so the recap reads as their table of contents. The user sees the whole before the parts and can say "accept the settled ones" at once.
2. **Settled candidates in one batch.** What the code settles beyond doubt (a not-null column on an ID, a foreign key, a check the code and the schema agree on) is confirmed in a single question: "these N are recorded as rules as coded; anything to take out?"
3. **Then the decisions, grouped and in order of impact.** One `AskUserQuestion` call per concept (lending limits, due dates, fees), two to four questions in it, the decision with the most consequences first. For each candidate offer:
   - **It is a rule, as the code has it** — the candidate becomes a rule.
   - **It is a rule, but the code is wrong** — ask for the intended rule. The rule records the intended behaviour, and the difference becomes an open point (see section 7).
   - **Not a business rule** — an implementation detail; it stays out of `business-rules.md`.
   - **Don't know** — it becomes an open point in the functional spec, with the evidence, and stays out of the rules for now.

A finding is asked in the group of the concept it touches, with the evidence and a recommendation, not in a separate round at the end.

**Rules only the database enforces.** For a candidate that only a constraint, index or trigger guarantees, also ask where the rule should be enforced once the code is restructured: in the domain as well as the database (recommended: in hexagonal architecture the storage is an adapter, and the next one may not validate the same way), or by the database alone. Record the answer in the enforcement table; making the domain enforce it is a later Change, never part of Adopt.

**Terms.** Ask which word is the business term only where the code and the interface disagree; the glossary records the code term and the business term, and any rename in code is a later Change.

## 6. Write the area's documents

With the answers in hand:

1. **`business-rules.md`:** one area section with its prefix; each confirmed rule gets an ID. The Code column holds the code the check returns today if it returns one. If it returns only a sentence or an exception class, propose an English code and list "no error code yet" under the area's gaps; changing what the code returns is a Change.
2. **`use-cases.md`:** one row per confirmed use case, with its rule IDs. Home is where the code lives today (`app/views/bookings.py::create_booking`), even when that is a controller; it moves when the code moves.
3. **`domain-model.md`:** the area's glossary terms, its aggregates as the user describes the business (not as the tables happen to be grouped), and for each aggregate where its rules live today.
4. **`technical-spec.md`:** the enforcement table gets a row per rule naming every place it is enforced today, by `path::symbol` (the `file:line` evidence of the candidates does not carry over, since the next edit would shift it), so a rule enforced in a controller and in SQL is visible as such.
5. **Functional spec:** behaviour of the area in plain words with rule IDs; each "code is wrong" answer and each "don't know" as an open point with the rule ID or the evidence.
6. **`docs/adoption.md`:** remove the area's candidate section; everything in it has now moved to its home or been rejected. Fill the area's rule and use case IDs in the map.
7. **`docs/plan.md`:** tick the area with the date, add a Fixes item for each rule the code gets wrong and for each "not testable without changing code", add the report's follow-ups, clear "Now". Status lives here only, so the map in `adoption.md` keeps no status of its own.

## 7. Tests that pin behaviour

Every confirmed rule ends with a test that cites its ID, so the later Change that restructures the area has a net.

1. **Tag what exists.** Where an existing test already covers a rule, add the `@rule` tag in the language's convention and change nothing else in that test.
2. **Add characterization tests** for the rules without one. Test through the most stable seam the code already has: a pure function or class, then the service, then the HTTP route or CLI command against the real database. Do not change production code to create a seam. If a rule cannot be reached without changing code, list it as "not testable without changing code" in the report; it becomes the first step of a Change.
3. **Rules where the code is wrong.** Write the test for the intended rule and mark it as an expected failure that cites the rule ID and the open point (`pytest.mark.xfail(strict=True, reason="BK-04: code allows 8 h, see open point")`; the language reference gives the marker). The suite stays green, the gap is visible, and the test flips to an unexpected pass the day the fix lands. Where the test framework has no such marker, the language reference says how to keep the test in a separate run instead.
4. **Integration tests** run against the real database, as everywhere in this skill. If the project's tests used a substitute (SQLite for PostgreSQL), keep the old tests running and put the new ones on the real engine; replacing the old setup is a Change.

Run the full suite. Every test that passed at the starting state still passes; the new ones pass or are expected failures.

## 8. Architecture check with a baseline

Existing code will break the dependency rule. Turning the check on with every existing violation failing would make it useless on day one, and switching it off would let new violations in. So record the current violations as a **baseline**: the check passes on them and fails on any new one.

1. Map the existing folders to layers where the code has them (models or entities → domain, services → application, views, controllers and repositories → adapters). Where the code has no layering, map nothing and check only the target folders that new code will use.
2. Configure the language's tool as its reference says, then record the baseline with the tool's own mechanism ("Existing code: baseline" in the language reference). With `check_imports.py`, use `--write-baseline`.
3. Write the baseline count and the command in the technical spec. The number only goes down: each Change that moves code removes its entries, and adding an entry needs the user's approval like a new dependency.

On later runs, re-record the baseline only if the area's mapping changed, and say how the count moved.

## 9. Closing and the report

1. Run all checks: the test suite (against the starting state), static analysis as the project had it, the architecture check, and `tools/check_traceability.py --docs docs --tests <tests dir>`. It should report no undefined IDs; rules without a test are only the ones listed as not testable.
2. Light documentation review (`references/doc-review.md`) for the area's documents.
3. Report, then stop; commit only if asked. The block below opens the final message, so the user and anyone comparing runs find the same facts in the same place; explanations, if the report detail in `CLAUDE.md` is "detailed", follow it, one short paragraph per finding or decision.

```
Area: <name>   Areas adopted: <n> of <m> (see docs/plan.md)
Rules: confirmed XX-01..XX-nn · code differs from rule: XX-nn (open point) · rejected <n> · unknown <n> (open points)
Use cases: UC-nn … (Home as found)
Tests: starting state <pass/fail> → now <pass/fail> · existing tests tagged <n> · added <n> · expected failures XX-nn …
Not testable without changing code: <rules or none>
Architecture: <tool> · baseline <n> known violations · new violations <n>
Findings: <same check with different values, rules only in the interface, … or none>
Documents changed: <file: what>
Next: <the most valuable Fix or Change, and the next area to adopt>
```

## 10. A project that is partly adopted

`docs/plan.md` shows which areas are adopted and `docs/adoption.md` what each holds. Until all are adopted, the other modes apply only to adopted areas:

- A Build or Change request in an area that is not adopted yet: say so, and offer to adopt that area first (recommended) or to make the change without the workflow's guarantees, recorded as a finding for that area's adoption.
- A Change that moves adopted code into the target layout is a technical change (`references/change.md` section 4): the area's tests stay green throughout, the moved code's entries leave the baseline, and Home in `use-cases.md` follows the code.
- A "code differs from rule" open point is fixed with Fix (`references/fix.md`): its expected-failure test, with the marker removed, is the reproduction.
- Review and Code review read `adoption.md` and skip areas that are not adopted, reporting them as such instead of as gaps.

When the last area is adopted, delete `docs/adoption.md`, after moving its starting state and baseline notes into the technical spec if they still matter, and remove the "Adoption" section of the plan, keeping its ticked lines under a milestone or as history if the team wants them.
