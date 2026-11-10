---
name: grill-me
description: Use when a plan or design has consequential unresolved assumptions, requirements or trade-offs, or the user asks to be grilled. Skip settled designs and trivial changes.
license: MIT
disable-model-invocation: false
metadata:
  opencode/autoinvoke: true
---

# Grill Me

Use `superpowers:brainstorming` for from-scratch discovery of what to build; this skill pressure-tests a plan or design that already exists.

Reach a shared, evidence-backed understanding of the decisions that matter. Challenge assumptions and ambiguous language, expose consequential trade-offs, and preserve useful conclusions without turning every discussion into a documentation project.

## Interview

Read the supplied context and relevant existing code, glossary and architectural decisions before asking questions. Carry forward answers already given. Separate established facts, user preferences and your proposals.

Map the unresolved decisions and their dependencies. Ask a short round of independent questions whose prerequisites are settled. Defer questions that depend on an unanswered choice. Number each question and give your recommendation, its reason and the main trade-off. Make disagreement easy; do not phrase questions to steer the user toward agreement.

Wait for answers before advancing dependent decisions. Use concrete scenarios and counterexamples to expose hidden constraints, failure modes and unclear terms. When terminology or stated behavior conflicts with the project's glossary or code, show the discrepancy and resolve it with the user.

Look up facts yourself using the available tools. Delegate bounded research only when it helps and is permitted. If evidence is unavailable, state the uncertainty instead of asking the user to ratify a guess.

After each round, carry forward the resolved choices and focus the next round on what they unlock. Stop when consequential uncertainties are resolved or explicitly deferred. Do not prolong the interview with speculative choices that would not affect the outcome.

## Preserve useful decisions

For project design work, capture resolved terminology and significant decisions when documentation is in scope. Respect requests for discussion only and repository approval rules. With no relevant project or durable conclusion, keep the result in the conversation.

- Follow the existing documentation layout. If `GLOSSARY-MAP.md` exists, use it to find the relevant context. Challenge inconsistent vocabulary before recording it.
- Add or refine a glossary entry only after its meaning is agreed. Keep definitions about the domain, without implementation details. Follow the existing format; for a new glossary, use a context heading and bold terms with one- or two-sentence definitions and any misleading synonyms to avoid.
- Record an ADR only for a consequential decision that is costly to reverse, surprising without context, and the result of a real trade-off. Follow the existing format; otherwise use the next sequential `docs/adr/NNNN-slug.md`, a descriptive title and a short paragraph explaining context, decision and reason. Distinguish proposals from accepted decisions.
- Create files lazily. Do not produce an ADR for every answer, rewrite global rules, publish tickets, or start implementation as a side effect of the interview.

## Finish

Give the settled decisions, unresolved or deliberately deferred points, and any documentation changed. Ask the user to confirm that the shared understanding is accurate before proceeding to implementation. Confirmation of the design does not grant unrelated external actions or permissions.
