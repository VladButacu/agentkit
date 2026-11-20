# Prose

Two passes, always both, in this order: the evidence pass decides what each sentence may claim, the voice pass decides how it sounds. Read [evidence.md](prose/evidence.md) before the first pass and [voice.md](prose/voice.md) before the second.

## Inputs before drafting

From the request and the supplied material, establish both:

- The author, the actual recipient, their relationship, the decision or understanding the text should support, and the author's expressed feelings, intensity and characteristic words.
- The facts: what happened or what the reader can do, how it differs from the alternative, what proof exists, and what stays local, manual, uncertain or limited.

Ask one precise question only when a missing fact or choice would materially change the message. Do not invent experience, feelings, customers, metrics or outcomes to fill a gap.

## Pass 1: evidence

Work through [evidence.md](prose/evidence.md): the fact sheet, the claim hierarchy, sentence jobs, the substitution and consequence tests, the section substance audit, and the artifact rules. For websites, landing pages and product pages also read [website-copy.md](prose/website-copy.md); for articles, blog posts and case studies also read [blog-writing.md](prose/blog-writing.md). [slop-patterns.md](prose/slop-patterns.md) holds the prohibited patterns and repairs.

## Lint

Save the draft to a UTF-8 text file and run from this skill's directory:

```bash
python scripts/prose/unslop_lint.py <file>
```

The linter is advisory. It prints findings and exits 0 whenever it can read the file. It exits 2 only for unreadable input or bad arguments. Each finding carries a label:

- `ERROR`: a pattern the prose rules prohibit outright.
- `WARN`: a pattern that needs judgement in context.

Review every finding in context. Fix one that describes a real problem. Keep one that is correct as written, and mark its line with `unslop: allow <rule-id>` (in an HTML comment in Markdown). The marker suppresses that rule on that line only. Fenced and inline code is not checked. Rule ids are listed in [slop-patterns.md](prose/slop-patterns.md#10-linter-rules). Do not evade a finding by swapping a synonym into the same empty sentence. Run the linter again after revisions. A clean run is necessary but not sufficient.

## Pass 2: voice

Work through [voice.md](prose/voice.md): establish the voice, repair the thought and the paragraph relationships, preserve the person, make the language easy to follow, then run its final review checklist. The voice pass comes after linting, never before.

## Review

For text that will be published, such as documentation, website copy or an article, dispatch the `blind-reviewer` subagent after the voice pass. Give it the final text and the [review rubric](prose/examples-and-checks.md#review-rubric), revise what it finds, and lint again. When the subagent is not installed, skip the review and say so.

## When the passes collide

Evidence constrains what may be claimed; voice constrains how it may sound. An explicit feeling is source material, not an unsupported claim: keep it at the strength the author gave it. A fact that hurts the tone stays; a wording that betrays the author goes. A lint finding never overrides the author's stated feeling, a necessary connective sentence, an ordinary sign-off or a precise technical word. Voice never licenses an unsupported claim, an invented anecdote or a fabricated metric.

## Deliver

Return one committed version unless alternatives were requested. Keep any explanation brief and outside the artifact. Do not claim a literal read-aloud test or an independent review unless it happened. Stop when the text works; do not rewrite merely to produce another version.
