---
name: ddd-hexagonal
description: Spec-driven development with Domain-Driven Design and hexagonal (ports and adapters) architecture, in any language. Bootstraps a project's document set (functional spec, business rules with IDs, use cases, domain model, technical spec) through an interview, then drives every task one use case at a time - test first, architecture check, verification against rule IDs, documentation review. Use this whenever the user starts a new application, service or module that has business rules; adds a feature or use case, changes, adds or removes a rule or requirement, renames a concept or term across a project, or swaps or replaces a framework, library, database or other technology in a project that has these documents; mentions DDD, domain model, aggregates, bounded contexts, hexagonal, ports and adapters, clean architecture, business rules, use cases, or "write the specs before the code"; asks to implement a use case or rule in a project that has docs/business-rules.md or docs/use-cases.md; wants to review project docs for contradictions or duplication; or asks for a code review in a project with these documents - even if they never name DDD or hexagonal.
---

# DDD + hexagonal, driven by documents

This skill keeps three things aligned: what the business needs (documents), how the code is shaped (domain at the centre, adapters at the edge), and proof that the two match (tests that cite rule IDs). The reason for the strict process is that business rules are the part of an application that costs the most when they are wrong or scattered, and a document set with one home per fact lets both people and Claude find the truth without guessing.

## Pick the mode

Look at the project first, then choose:

| Situation | Mode |
| --- | --- |
| No business rules document, or a new project | **Bootstrap**: interview, then write the documents |
| Documents exist and the user asks for a feature, rule or use case | **Build**: one use case at a time |
| A new feature or use case, a changed or dropped rule ("it's 4 hours now"), a technology swap, or a rename | **Change**: name the kinds, impact analysis, then documents, tests, code |
| A use case or milestone is finished, or the user asks for a check | **Review**: documentation and traceability |
| The user asks to review code, a diff, a branch or a PR in a project with these documents | **Code review**: architecture, traceability, code against the documents |

If the project has some documents but not the set below, say what is missing and offer to Bootstrap the missing parts only. Detect the language from manifests (`composer.json`, `package.json` or `tsconfig.json`, `pyproject.toml` or `requirements.txt`, `pom.xml` or `build.gradle*`) and read the matching file in `references/` (`php.md`, `typescript.md`, `python.md`, `java-kotlin.md`). For any other language read `references/new-language.md` and offer to create the reference file.

## Non-negotiable practices

These hold in every project. The reason is given so you can apply them with judgement in cases they do not literally cover.

1. **Rule IDs and traceability.** Every business rule has a stable ID (`AL-06`) in one table. Tests cite the IDs they cover (`@rule AL-06`), and a rule with no test is reported as a gap. IDs let a test, a use case and a conversation point at the same sentence without breaking when headings change.
2. **One fact, one home.** Each fact is stated in exactly one document; the others link to it. Duplicates drift apart and then contradict each other. Before writing anything down, check whether another document already holds it.
3. **Test first for domain code.** In the domain and service layers write the failing unit test, then the code. Adapters get integration tests against the real technology (the real database, not a lookalike), because mocks and substitutes hide the differences that cause production bugs.
4. **Ask before adding a dependency.** Anything not in the technical spec's stack table needs the user's approval; once approved it goes into the table. Dependencies are long-term commitments the user must own.
5. **Review the documentation after every slice.** After each use case run the light review, and after a milestone (a group of use cases) the deep review. Both are in `references/doc-review.md`. Documents rot silently if nobody looks.

## Defaults the user may override

Ask once at Bootstrap and record the answers in the project's `CLAUDE.md`:

- Code, comments, identifiers, database names, routes and commit messages in English, even when the interface is in another language. User-visible text lives in templates and translation files, and failed checks return English codes mapped to messages there.
- Before changing code, check the branch. On the main branch, propose a new branch and ask before creating it. Commit only when asked.
- Tests: unit tests for rules, integration tests against the real database, no coverage percentage, deploy or CI stops on a failing test, static analysis or architecture check.
- Hexagonal-lite: ports only at real seams (see `references/architecture.md`).
- Logging: never assume it. Ask the developer explicitly whether to adopt `references/logging.md` (one DEBUG on entry and one INFO on completion per adapter call and use case, no personal data in logs), adapt it, or leave logging out.

## The document set

Fixed layout, so every project reads the same. Templates are in `assets/templates/`. A small project may merge `business-rules.md` and `use-cases.md` into one file, as long as the IDs stay unique and each use case still lists its rules.

| Document | Holds | Does not hold |
| --- | --- | --- |
| `functional-spec.md` | Purpose, users and roles, core concepts, screens and behaviour in plain words, scope, open points, rollout | Rules (link to IDs), implementation |
| `business-rules.md` | Every rule with an ID, grouped by area, with the error code a failed check returns | Flows, implementation |
| `use-cases.md` | Actor, trigger, main flow, rule IDs, the class that implements it | Rules themselves |
| `domain-model.md` | Ubiquitous language, bounded contexts, aggregates, value objects, ports, events | What the specs already say |
| `technical-spec.md` | Stack, hosting limits, architecture and folder layout, schema, routes, which service enforces which rule, security, deploy, testing, conventions | Rule text |
| `CLAUDE.md` | Pointers to the above, documentation rules, coding rules, git and dependency rules | Anything duplicated from them |

## Bootstrap

1. Read what exists. Then run the interview in `references/interview.md`: one decision at a time, with `AskUserQuestion` offering two to four options and a recommendation in front. Never ask something the project files already answer.
2. After each cluster of answers, write that part of the documents from the templates, so the user reviews real text and not a plan. Keep rules in `business-rules.md` only; flows reference IDs.
3. Collect doubts as open points in the functional spec instead of inventing answers.
4. Copy `scripts/check_traceability.py`, `scripts/check_imports.py` and `scripts/rule_impact.py` into the project's `tools/` folder so the project is self-contained and CI can run them. Install the branch guard: copy `assets/hooks/block_commit_on_main.py` to `.claude/hooks/` and merge `assets/hooks/settings.snippet.json` into `.claude/settings.json` (read the file first and merge the `PreToolUse` array; never replace existing settings; if a hook on `Bash` already exists, ask whether to add alongside). It refuses `git commit` while the branch is `main` or `master`. Tell the user it needs `/hooks` opened once or a restart if `.claude/` did not exist when the session began, and that it only guards Claude, so a git `pre-commit` hook is the option for guarding people too. Create `CLAUDE.md` from `assets/templates/claude-md.template.md`, with the commands filled from the language reference and the script paths pointing at `tools/`.
5. Set up the architecture check for the language (the reference file says how) and run `tools/check_traceability.py` once the rules exist. Finish with the deep review.
6. Stop before building. The user starts the first use case.

## Build: one use case at a time

A task is one use case from `use-cases.md`. For each:

1. **Branch.** Check the current branch; follow the git default above.
2. **Read** the use case, every rule ID it lists, and the matching parts of the domain model and technical spec. If something is missing or contradictory, ask before coding.
3. **Plan** the files per layer in two or three lines: domain objects, services, application class, ports, adapters, tests. Say where each rule will be enforced.
4. **Test first** for the domain and service code: write the failing unit test with its `@rule` tags, watch it fail, make it pass.
5. **Implement** the application class and the ports it needs. Dependencies point inward only (`references/architecture.md`). Business rules never go into controllers, templates, SQL reports or adapters. Build only what the use case and the technical spec call for: a driven adapter (for example the database repository) when the use case must persist, a driving adapter (HTTP route) only when the technical spec lists one for this use case. Do not invent endpoints, authentication placeholders or other behaviour the documents do not define; record each such gap as an open point or a question. If the project adopted a logging policy, each new adapter call and use case logs as `references/logging.md` says, and never with personal data.
6. **Integration tests** for each new adapter and for the use case end to end, against the real database.
7. **Run** the unit tests, integration tests, static analysis and the architecture check. Report real results, including failures; never mark a task done on a red run. If a check cannot run here, say which and why; a real database can usually be started in Docker.
8. **Verify against the specs** and write the report below.
9. **Light documentation review** (`references/doc-review.md`).
10. Stop. Commit only if asked.

If code and documents disagree at any point, ask which is right before changing either, because the documents are the source of truth until the user says otherwise. The only document edits you make on your own are adding an open point, adding the stack-table row for an approved dependency, and updating the folder layout or enforcement table to match code you just wrote; list them under "Documents changed". Anything that alters a rule, an aggregate's guarantees or a decision is a question first.

### End-of-task report

```
Use case: UC-xx <name>
Rules touched: AL-02, AL-03 …
Coverage: rule -> test (file::name) for each; rules without a test: <list or none>
Checks: unit <n pass/fail> · integration <n pass/fail> · static analysis <result> · architecture <result>
Gaps or mismatches with the documents: <list or none>
Documents changed: <list or none>
Decisions needed from you: <list or none>
```

## Change: a requirement, use case or technology is added, altered or removed

Use this when the user asks for a new feature or use case, says a rule, limit or role is different now, wants to swap or add technology, or wants to rename a concept. A change is often several kinds at once, and the risk is a half-applied change: one document updated while a use case, a test, a constant or the schema still holds the old version. So work from facts, in this order, following `references/change.md`:

1. Branch check, then **name the kinds** of change you see (rule, use case, technical, rename) and wait for the user's yes before editing, so the scope is the user's and not yours.
2. **Find the impact** with `scripts/rule_impact.py` (and a grep for the old word or technology), and decide what happens to existing data before editing.
3. Apply the procedure for each kind, always editing the single home first and updating the other documents only by ID.
4. Tests first, then code; run all checks, including the traceability check, which also fails when a rule or use case ID disappears without a "(removed)" or "(superseded by ...)" marker.
5. End with the change report from `references/change.md` and stop; commit only if asked.

## Review

Light review after each use case, deep review after a milestone: follow `references/doc-review.md`. Run `scripts/check_traceability.py --docs docs --tests <tests dir>` first; it finds unknown IDs, rules nobody references and rules without a test, so your reading time goes to the contradictions a script cannot see. Report findings as contradictions (the documents disagree), gaps (nothing says), and duplication (two homes), and fix only what is unambiguous; decisions go to the user as questions with a recommendation.

## Code review

Review changed code against the rules of this skill, following `references/code-review.md`: the dependency rule and rules kept in the domain, `@rule` tests for changed rule logic, names and logic that match the glossary and `business-rules.md`, integration tests on the real technology, and no dependency outside the stack table. Scripts run first. Generic bug finding belongs to the built-in `code-review` skill; chain it before the DDD pass when the user asks for a full review. Report findings ranked by severity; fix only when asked and only what is unambiguous. Code that disagrees with the documents is a question, not a fix.

## Architecture in brief

Domain at the centre, then application services, then adapters; dependencies point inward. Ports (interfaces owned by the core) exist only where a second implementation or a test seam is real: persistence, clock, mail, external identity, file or backup storage. Read-only reports may query the database directly because they hold no rules. The full rules, folder mapping and anti-patterns are in `references/architecture.md`; read it before planning a use case in a new project.

## Style of work

- Keep documents short: tables and bullets over prose, a pointer over a copy.
- Ask decisions as questions with a recommendation, one topic at a time; apply the answer to every document it touches, then check that no other document repeats it.
- Use the user's language for conversation and the ubiquitous language for names in code.
