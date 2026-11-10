# The evidence pass

Write like a person who knows the subject and has something specific to say. Do not imitate casual speech mechanically. Remove formulaic language by grounding every sentence in a fact, action, mechanism, constraint, consequence, decision, or observed result.

## Operating principle

Treat weak writing as an information problem before treating it as a wording problem.

Never compensate for missing facts with adjectives, emotional claims, metaphors, narrative tension, or broad promises. If a required fact is absent, ask one precise question or use a visible placeholder such as `[deployment detail needed]`. Do not invent proof, customers, metrics, guarantees, certifications, failures, adversity, or outcomes.

## Workflow

### 1. Build the fact sheet

Extract or request only the facts needed for the artifact:

- what the product, service, event, or argument is;
- what happened or what the user can do;
- who it is for and who it is not for;
- how it works differently from the current alternative;
- what remains local, manual, private, slow, limited, uncertain, or dependent on another system;
- what proof exists: screenshots, measured results, customer quotes, implementation details, pricing, guarantees, named experience, logs, code, or source material;
- what the reader should understand or do next.

Keep the user's exact domain language when it is clear. Do not translate precise terms into softer marketing vocabulary.

### 2. Choose the claim hierarchy

Rank available material in this order:

1. Observable behavior or event.
2. Verifiable mechanism, decision, or constraint.
3. Concrete consequence.
4. Supported comparison or interpretation.
5. Emotional or aspirational benefit.

Build mainly from levels 1 to 3. Use levels 4 and 5 only when the evidence supports them.

### 3. Choose the artifact rules

- For websites, landing pages, product pages, and service pages, read `website-copy.md`.
- For blog posts, technical articles, case studies, and essays, read `blog-writing.md`.
- For mixed artifacts, apply both but let the artifact's main purpose decide structure.

Do not apply landing-page suspense to a product hero. Do not apply landing-page repetition to an article. Do not turn a technical article into sales copy.

### 4. Draft by sentence job

Each sentence must perform one identifiable job:

- identify the thing;
- describe an action or event;
- explain a mechanism;
- state a constraint or tradeoff;
- show a consequence;
- provide proof or an example;
- qualify a claim;
- answer an objection;
- connect the current fact to the next one;
- request an action.

Delete sentences whose only job is to frame, tease, editorialize, sound confident, announce importance, or preview the next sentence.

### 5. Remove meta-signposting

Delete any sentence that announces what the text is about to say instead of saying it.

Bad:

> This is where the problem becomes interesting. The retry queue had no upper bound.

Better:

> The retry queue had no upper bound.

Bad:

> It is worth being specific about why the migration failed.

Better:

> The migration copied user records before their encryption keys.

A transition survives only when it carries information or explains a logical relation.

### 6. Apply the substitution test

For every sentence, ask:

> Could this sentence appear unchanged on 100 unrelated websites or articles?

If yes, delete it or replace the abstract claim with a subject-specific fact.

Bad:

> A smarter way to transform how your team works.

Better:

> Record a meeting, transcribe it on your computer, and search the notes later without uploading the audio.

### 7. Apply the consequence test

Do not stop at a feature or broad benefit. State the visible change when useful.

Bad:

> Keep everything organized and accessible.

Better:

> Search past meeting notes by topic instead of opening recordings one by one.

Do not force a consequence sentence when the action already explains itself.

### 8. Run the section substance audit

For each section, name the concrete thing the reader learns that was not already known from the heading or previous section.

A section passes when it contains at least one of these:

- a specific fact, event, or observation;
- a mechanism or implementation detail;
- a decision and its reason;
- a measured result with scope;
- a limitation or tradeoff;
- an example that changes understanding;
- a practical instruction the reader can use.

If the section can be reduced to one sentence without losing information, either add real detail or cut the section. Do not pad it with a story, list, or conclusion.

### 9. Remove performance language and staged rhetoric

Read `slop-patterns.md`. Remove every fatal pattern and review every high-risk pattern. In particular:

- no grand framing or broad industry openings;
- no fake urgency or fabricated adversity;
- no abstract transformation claims;
- no generic reassurance;
- no negate-then-reveal theater;
- no self-answering rhetorical questions;
- no standalone verdict fragments;
- no repeated dramatic short sentences;
- no automatic rule-of-three phrasing;
- no inflated adjectives;
- no em dashes or curly quotation marks;
- no headings that sound like conference talks;
- no conclusions that summarize what the reader just read.

### 10. Run the linter

Run the lint step from the skill root (`scripts/unslop_lint.py`) on the saved draft.

Resolve every `ERROR`. Review every `WARN` in context. Do not evade a warning by swapping in a synonym while preserving the same empty sentence.

Run the linter again after revisions. A passing lint result is necessary but not sufficient.

### 11. Perform the human edit

Read the text aloud once. Revise when any of these are true:

- adjacent sentences have the same length or grammatical shape;
- sentences sit beside one another as disconnected facts;
- every paragraph ends with a neat payoff;
- two consecutive paragraphs end with short verdict sentences;
- the prose sounds more certain than the facts allow;
- the writer appears to be selling before explaining;
- a second short sentence merely restates the first;
- a phrase sounds written to impress another copywriter;
- a sentence is clear but not something a domain expert would naturally say;
- an opening gives away every system, step, and result before the article earns them;
- a closing repeats the article instead of ending on its final implication.

Prefer one plain sentence over a staged sequence of fragments. Add connective tissue only when it expresses cause, contrast, sequence, scope, or qualification.

### 12. Deliver one committed version

Return one best version unless the user asks for options. Do not surround the writing with praise, a sales rationale, or claims that it is "human." If assumptions were required, list them briefly outside the artifact.

## Editing existing text

When rewriting supplied text:

1. Preserve every supported factual claim.
2. Identify the intended point of each section.
3. Remove empty setup, previews, and repeated conclusions.
4. Replace generic benefits with available mechanisms or consequences.
5. Keep distinctive user phrasing unless it is unclear or inaccurate.
6. Do not make the text more polished than the author or brand should sound.
7. Do not invent a failure arc around a successful event.
8. Run the linter, substitution test, and section substance audit.

Do not rewrite merely to change words. Keep a sentence unchanged when it is already clear, specific, and natural.

## Drafting from sparse input

When only a name and category are provided, do not fabricate a full website or article. Ask for the missing facts with the highest claim value:

1. What happened or what can the user do?
2. What makes this different from the current method?
3. Which claim can be proved today?
4. For an article, what evidence, example, or source should teach the reader something new?

Ask no more than necessary. If interruption is undesirable, draft a factual skeleton with placeholders.

## Required references

- Read `slop-patterns.md` for prohibited language, rhetorical structures, formatting tells, and repair methods.
- Read `website-copy.md` for website and landing-page work.
- Read `blog-writing.md` for articles, blog posts, case studies, and technical prose.
- Read `examples.md` when the requested tone remains ambiguous after applying the rules.
- Read `research-notes.md` only when explaining the rationale or updating the skill.
