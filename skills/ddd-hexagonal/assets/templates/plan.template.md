# <Project> — Plan

<date> · <owner>

The single home of progress: what is done, what is in progress, what comes next. Other documents say what things are (a milestone's content is in `functional-spec.md` "Rollout", a use case in `use-cases.md`, an area in `adoption.md`, an open question in the functional spec's open points); this file only says how far each has got, by ID. Every mode updates it when it ends.

## Now

- [ ] <Mode: what, on branch `<branch>`, started <date>>

## Milestones

### M1 <name>

- [ ] UC-01 <name>
- [ ] Deep review of M1

## Adoption

<Only while `docs/adoption.md` exists; remove the section when the last area is adopted.>

- [ ] <Area> (see `adoption.md`)

## Fixes

<Rules the code breaks: open points marked "code differs from rule", failing rule tests, bug reports.>

- [ ] XX-nn <what the code does wrong> (<open point · expected-failure test · reported by>)

## Follow-ups

<Work a report suggested that is not a use case, an area or a fix yet: a Change, a technical move, a dependency to evaluate.>

- [ ] <What> (from <mode> on <date>)

<!--
How to tick
- A use case is ticked when it is built, its checks are green and its light review is done.
- A milestone's deep review is ticked when the review ran and its findings are fixed or asked.
- An area is ticked when its adoption report is given; a fix when its test passes without a marker.
- Ticked items stay, with the date: "- [x] UC-01 Book a room (2026-10-25)". The list is the history.
- Nothing here restates a rule, a flow or an open point: write the ID and a few words, and the home has the rest.
-->
