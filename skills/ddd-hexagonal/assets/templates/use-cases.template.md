# <Project> — Use Cases

<date> · <owner>

Who does what, in which order. A use case holds no rule of its own: it names the rules it applies by ID, and `business-rules.md` states them. A build task is one use case.

**Home** is where the code lives: a class in the application layer unless another folder is named. Every use case that changes data runs in one transaction and writes the audit record.

## <Area>

| ID | Use case | Actor | Main flow | Rules | Home |
| --- | --- | --- | --- | --- | --- |
| UC-01 | <Verb + object> | <Role> | <Step → step → result> | <IDs, or none> | `<ClassName>` |

Alternative flows: <only the important ones, referencing rule IDs>.
