---
name: prose
description: Use when drafting or revising any prose a person will read, including documentation, website copy, blog posts, articles, case studies, emails, letters and applications. Always applies both passes: evidence discipline and voice fidelity.
disable-model-invocation: false
metadata:
  opencode/autoinvoke: true
---

# Prose

Two passes, always both, in this order: the evidence pass decides what each sentence may claim, the voice pass decides how it sounds. Read [references/evidence.md](references/evidence.md) before the first pass and [references/voice.md](references/voice.md) before the second.

## Inputs before drafting

From the request and the supplied material, establish both:

- The author, the actual recipient, their relationship, the decision or understanding the text should support, and the author's expressed feelings, intensity and characteristic words.
- The facts: what happened or what the reader can do, how it differs from the alternative, what proof exists, and what stays local, manual, uncertain or limited.

Ask one precise question only when a missing fact or choice would materially change the message. Do not invent experience, feelings, customers, metrics or outcomes to fill a gap.

## Pass 1: evidence

Work through [references/evidence.md](references/evidence.md): the fact sheet, the claim hierarchy, sentence jobs, the substitution and consequence tests, the section substance audit, and the artifact rules. For websites, landing pages and product pages also read [references/website-copy.md](references/website-copy.md); for articles, blog posts and case studies also read [references/blog-writing.md](references/blog-writing.md). [references/slop-patterns.md](references/slop-patterns.md) holds the prohibited patterns and repairs.

## Lint

Save the draft to a UTF-8 text file and run from this skill's directory:

```bash
python scripts/unslop_lint.py <file>
```

Resolve every `ERROR`. Review every `WARN` in context; do not evade a warning by swapping a synonym into the same empty sentence. Run it again after revisions. A passing lint result is necessary but not sufficient.

## Pass 2: voice

Work through [references/voice.md](references/voice.md): establish the voice, repair the thought and the paragraph relationships, preserve the person, make the language easy to follow, then run its final review checklist. The voice pass comes after linting, never before.

## When the passes collide

Evidence constrains what may be claimed; voice constrains how it may sound. An explicit feeling is source material, not an unsupported claim: keep it at the strength the author gave it. A fact that hurts the tone stays; a wording that betrays the author goes. A lint score never overrides the author's stated feeling, a necessary connective sentence, an ordinary sign-off or a precise technical word. Voice never licenses an unsupported claim, an invented anecdote or a fabricated metric.

## Deliver

Return one committed version unless alternatives were requested. Keep any explanation brief and outside the artifact. Do not claim a literal read-aloud test or an independent review unless it happened. Stop when the text works; do not rewrite merely to produce another version.
