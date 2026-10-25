# Fix: the documents are right and the code is not

Use this for a bug: the code does something a rule in `business-rules.md` says it must not, or fails to do what a rule says. It is the route for a bug report from users, a rule test that fails, and every "code differs from rule" open point that Adopt left with an expected-failure test.

A fix is small on purpose. It changes the code to match a rule that already exists, proves it with a test that cites the rule, and touches nothing else. Anything larger is a Change, and telling the two apart is the first step.

## Contents

1. Is it a fix?
2. Reproduce with a failing test
3. Existing data
4. Fix in the rule's home
5. Closing and the report

## 1. Is it a fix?

1. **Branch check**, as in Build. Put the fix under "Now" in `docs/plan.md` (build the plan first if the project has none) and start the session task list with the five steps below (`references/progress.md`): the closing step is the one long fixes skip.
2. **Find the rule** the bug breaks: the open point or expected-failure test that names it, `tools/rule_impact.py <ID>` for a known ID, or the rule text for a reported behaviour. Read the rule, its use cases and its line in the enforcement table.
3. Decide, and say which in one line before editing:
   - **A rule covers it and the code breaks it** → Fix, continue here.
   - **No rule covers the behaviour** (the documents say nothing about a second return) → not a fix yet. The behaviour is undefined, so the missing rule is a decision for the user: propose it with a recommendation, and add it through Change (`references/change.md` section 2) before fixing.
   - **The rule itself is wrong or unclear** (the user says the limit should be 4, not 3) → Change, not Fix.
   - **The area is not adopted yet** (`docs/adoption.md`) → offer to adopt it first (`references/adopt.md` section 10).

The reason for this gate: a fix that quietly decides what the code should do is a rule written outside `business-rules.md`, which is exactly what the document set exists to prevent.

## 2. Reproduce with a failing test

1. If an expected-failure test already exists for the rule (from Adopt), remove its marker; that test is the reproduction. Do not write a second one for the same case.
2. Otherwise write a test that cites the rule (`@rule XX-nn`) at the layer where the rule is enforced: a unit test for domain code, an integration test against the real database for a rule that lives in a service with SQL or in the schema.
3. Run it and watch it fail for the reason the bug describes. A test that fails for another reason (a fixture error, a wrong import) proves nothing about the bug.

## 3. Existing data

A bug that ran in production may have left data behind: the late fee charged twice, a member suspended who should not be, a booking that should have been refused. Before editing, check whether stored data can be affected and, if it can, ask the user how to treat it, with a recommendation:

- leave it and report the affected rows (recommended when the effect is small or a person must judge each case);
- correct it with a migration or a one-off script, reviewed by the user before it runs;
- nothing to do, with the reason (the bug could not store anything).

Give the query that finds the affected rows, so the user can size the problem. Never correct data without that answer.

## 4. Fix in the rule's home

1. Change the code where the enforcement table says the rule lives. If the rule is enforced in several places, fix each one or ask; a rule fixed in one of two places is still broken.
2. Make the smallest change that makes the test pass. When the bug is a repeated action (a double submit, a second scan), check whether two requests at the same moment can still get through, and if they can, cover that path with a test too: a check that holds for requests in sequence can still fail for requests at the same moment. Do not move code into the target layout, rename, or tidy on the way: that is a Change, and mixed into a fix it hides what the fix was. Note what you would have moved as a suggestion in the report.
3. Return the rule's error code from `business-rules.md`. If the rule has a code but the code base has no way to return one yet (Adopt's "no error code yet"), return it in the form the surrounding code uses and list the gap.
4. If the fix needs a new dependency, ask first, as always.

## 5. Closing and the report

1. Run all checks: unit and integration tests, static analysis, the architecture check (the baseline count must not grow) and `tools/check_traceability.py --docs docs --tests <tests dir>`. A test that failed before the fix and is unrelated to it stays as it was and is reported, not fixed.
2. Update the documents the fix makes stale, and only those: close the open point (mark it done with the date, or remove it as the functional spec's style has it), and update the rule's line in the enforcement table. The rule text does not change; if it would have to, this was a Change. In `docs/plan.md`, tick the fix with the date, add the follow-ups and clear "Now".
3. Light documentation review (`references/doc-review.md`) for the touched rule.
4. Report, then stop; commit only if asked. The block opens the final message; with "detailed" report detail in `CLAUDE.md`, explanations follow it.

```
Fix: <one sentence>   Rule: XX-nn (<open point, issue or test that reported it>)
Cause: <file:line> - <what the code did wrong>
Test: <file::name> - failed before (<failure>), passes now
Code: <files changed>
Existing data: <affected rows and the decision taken, or why none>
Checks: unit · integration · static analysis · architecture (baseline <n>) · traceability
Documents changed: <file: what>
Suggested next: <a Change the fix pointed to, or none>
```
