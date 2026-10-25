# Bootstrap interview

Goal: collect enough decisions to write the document set without inventing anything. Ask one decision at a time with `AskUserQuestion` (two to four options, the recommendation first and marked). Group two to four small related questions in one call. Skip anything the project files, existing documents or the conversation already answer. After each cluster, write that part of the documents so the user reviews real text.

When the answer is unknown or depends on someone else, record it as an open point in the functional spec and move on.

## Order

1. **Purpose and users.** What the system is for, who uses it, how many, on which devices, in which language. Output: functional spec "Purpose and context".
2. **Roles.** Who can see and do what. Is there an emergency or system account? Output: roles table; rules in the ID area (access).
3. **Core concepts and words.** The five to ten nouns the business uses, and the one sentence that explains how they relate. Challenge synonyms: pick one term. Output: functional "Core concepts", domain-model glossary with the interface terms in the user's language.
4. **Rules, area by area.** For each concept ask: what must always be true, what is forbidden, what is calculated and how, what happens at the edges (dates, rounding, empty, duplicates). Offer concrete examples as options to react to. Output: rule table, one ID per rule, error code where a check can fail. Typical areas: the core transaction, calculation or allocation, locking or closing periods, catalog or reference data, audit, access, reporting, privacy and retention.
5. **Lifecycle and history.** What can be deleted, deactivated, corrected after the fact, locked, audited? What must be kept, for how long, and what happens at the end? Output: rules in the audit and retention areas.
6. **Use cases.** For every actor, list what they do from login to logout. Each becomes a row with its rule IDs. Output: use-cases table.
7. **Scope.** What is explicitly out. Output: functional "Out of scope".
8. **Constraints.** Hosting, budget, who maintains it, existing systems, compliance (privacy law, accounting). Output: technical "Hosting constraints" and functional open points.
9. **Stack.** Language, framework, database, only where the user has a preference or a constraint forces it; otherwise propose with reasons. Check the language reference exists. Output: technical "Stack" table.
10. **Working rules.** The defaults list in SKILL.md: language of code, branch handling and naming, commit policy, test policy, dependency policy, report detail (concise or detailed). Output: `CLAUDE.md`.
    **Logging** is always its own explicit question, never assumed: summarise `references/logging.md` in three lines (one DEBUG on entry and one INFO on completion per adapter call and use case, a correlation ID, an allowlist that keeps personal data out of logs) and offer: adopt it (recommended), adopt it with changes (ask which), or leave logging out of scope for now. If adopted, also ask the log destination, retention period and the level per environment. Output: technical "Logging", the "Personal data" section of the domain model, a line in `CLAUDE.md`.
11. **Milestones.** Group the use cases into rollout steps; each step is a "slice group" for the deep review. Output: functional "Rollout".

## Interview habits

- Offer a recommendation and say why in one sentence.
- Use realistic examples from the user's domain instead of abstractions.
- When two answers conflict, stop and resolve it before writing.
- Never fill a gap with a guess; write it as an open point or ask.
- A value that depends on an open answer (the country, and with it VAT rates, retention periods, number formats, legal wording) stays out of the rules. Write the rule neutrally ("kept for the legal retention period") and put the value in configuration or an open point naming who decides.
- Keep a running list of terms to put in the glossary and ask when two words seem to mean the same thing.
