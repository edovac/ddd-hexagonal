# <Project> — Adoption

<date> · <owner>

Working file while existing code is brought under the workflow (`references/adopt.md` in the ddd-hexagonal skill). It holds the map of areas and the candidates of the area in progress. Candidates are not rules: a rule exists only once the user confirms it and it moves to `business-rules.md`. Delete this file when every area is adopted.

## Starting state

| Item | Value |
| --- | --- |
| Commit | `<sha>` |
| Test suite | `<command>`: <n passed, n failed, or "cannot run: reason"> |
| Tests failing before adoption | <list; they are not fixed by Adopt> |
| Layering found | <e.g. "models/ services/ views/ (Django)", or "none"> |

## Areas

| Area | Entry points | Includes | Main tables | Status | Rules | Use cases |
| --- | --- | --- | --- | --- | --- | --- |
| <Name> | `<route or command>`, … | `<module>`, … (shared: `<module>`, also used by <area>) | `<table>`, … | not adopted · in progress · adopted | <IDs once adopted> | <IDs once adopted> |

## Candidates: <area in progress>

### Rules

| # | Candidate | Evidence | Today on failure | Tested by | Decision |
| --- | --- | --- | --- | --- | --- |
| C1 | <One testable sentence with the edge as the code has it.> | `<file:line>`, `<migration:line> (CHECK)` | <exception, message, HTTP status, or silent> | `<test>` or none | rule · code wrong: <intended> · not a rule · don't know |

### Use cases

| # | Action | Actor | Entry point | Candidates applied |
| --- | --- | --- | --- | --- |
| U1 | <Verb + object> | <Role, from the permission check> | `<route or command>` | C1, C2 |

### Terms

| In the code | In the interface or the user's words | Decision |
| --- | --- | --- |
| `<class / table / route>` | <word> | <business term> |

### Findings

- <Same check with different values: `a.py:12` allows 3, `b.py:40` allows 5.>
- <A rule enforced only in the interface: `templates/x.html:8`.>
