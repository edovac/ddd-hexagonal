# Documentation review

Run it after every use case (light) and after every milestone (deep). Start with the script, then read.

```
uv run tools/check_traceability.py --docs docs --tests <tests dir>   # or the runner in CLAUDE.md; <skill-dir>/scripts/ if the project has no tools/ copy
```

It reports: rule IDs used but not defined, rules nobody references, rules cited in no test, use cases that list no rules. Fix or explain every line before reading on.

In the deep review, also compare each script in `tools/` with the one in `<skill-dir>/scripts/` (`diff -q`). If they differ, the project has an older copy or a local edit: show the diff, and ask before replacing it, since a local edit may be deliberate.

## Light review (after a use case)

Scope: the use case just finished and the documents it touched.

- Its rule IDs exist, are cited by tests, and the end-of-task report matches the code.
- If the work changed behaviour, the rule text, error code table and use case flow were updated in their single home, and no other document repeats the old wording.
- New terms are in the glossary; code names match the glossary.
- The technical spec's "which service enforces which rule" matches the code.
- No new decision lives only in code or only in the conversation.

## Deep review (after a milestone)

Read every document in full, in this order, and write down findings before fixing.

1. **Contradictions.** Same fact stated differently (limits, formats, which roles may do what, which rule applies when). Cross-check the routes/permissions table against the roles and rule IDs, the schema against the rules (constraints, nullable fields), exports and report formats against the functional text, and open points against decisions already made elsewhere.
2. **Gaps.** Behaviour the rules do not define: what happens at the edges of dates and limits, when referenced data changes after use, on deletion or deactivation, with concurrent edits, after unlock or correction, on retention or erasure, when a calculation names something not eligible.
3. **Duplication.** A fact with two homes. Replace the copy with a pointer to the home, but only when both say the same thing. If they differ in any detail (a value, a condition, where or whether a check happens), it is a contradiction: report it and ask which is right, because merging would silently pick one meaning.
4. **Stale text.** Removed features still mentioned, renamed things under their old name, references to sections that moved, dates, table counts.
5. **Traceability.** Every use case lists rules; every rule that can fail has a code; the language file has a message for each code.
6. **Architecture drift.** Folder layout in the technical spec matches the code; the architecture check passes; no rule lives outside the domain.

## Reporting and fixing

Report findings in three groups: contradictions, gaps, duplication or stale text. Fix what is unambiguous straight away and say what changed. For every real decision (which of two statements is right, how an edge case behaves) ask the user, with options and a recommendation, then apply the answer to every document it touches and recheck for repeats. Never change a rule silently to fit the code; ask which is right.
