# <Project> — Business Rules

<date> · <owner>

The single home of every business rule. Other documents refer to a rule by its ID and never restate it. Tests cite the ID (`@rule AL-06`). The Code column is the English code a failed check returns; the user-facing message for each code lives in the translation files.

## <Area name> (<PREFIX>)

| ID | Rule | Code |
| --- | --- | --- |
| XX-01 | <One testable sentence: what is always true, forbidden or calculated, with the edge included.> | `error_code` or – |

<!--
Guidance for writing rules
- One rule, one sentence, one reason to fail. Split "and" rules.
- Include the edge in the sentence (inclusive dates, rounding, zero, duplicates).
- Give the rule an error code only if a check can reject input because of it.
- Keep values that depend on an open decision (country, tax rates, retention periods) out of the rule text; refer to the configuration or the open point instead.
- IDs are stable: never renumber; mark a removed rule "(removed)" instead of reusing its ID.
- Typical areas: core transaction, calculation or allocation, locking or closing, catalog or reference data, audit, access, reporting, privacy and retention.
-->
