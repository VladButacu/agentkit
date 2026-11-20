# Slop patterns

## Contents

1. Fatal vocabulary
2. Fatal phrases
3. Banned punctuation and formatting
4. Banned rhetorical structures
5. Meta-signposting
6. Cadence and robotic prose
7. Structural tells
8. Semantic and honesty failures
9. Repair methods

## 1. Fatal vocabulary

Do not use these words in delivered public-facing prose unless the user is quoting them or explicitly requires one as a precise technical term:

- delve
- landscape
- leverage
- pivotal
- comprehensive
- multifaceted
- harness
- foster
- realm
- tapestry
- testament
- watershed
- underscore
- utilize
- facilitate
- cutting-edge
- game-changer
- revolutionize
- empower
- unlock
- elevate
- supercharge
- streamline
- seamless
- synergy
- effortlessly
- robust
- transformative
- unparalleled
- innovative
- next-generation
- world-class
- future-proof
- straightforward

Treat these as fatal when used as filler or generic emphasis:

- actually
- genuinely
- genuine
- fundamentally
- structural
- the kind of

`Structural` may survive only as a precise engineering or organizational term. `In practice` may appear once when it marks a real contrast between theory and observed operation. A second use in the same piece fails the lint check.

## 2. Fatal phrases

Do not use:

- at the end of the day
- when it comes to
- in a world where
- moving forward
- circle back
- deep dive
- double down
- take a step back
- on the same page
- make no mistake
- it turns out
- let me be clear
- lean into
- unpack the problem
- unpack the issue
- navigate the challenges
- navigate the complexities
- it is important to note
- it's important to note
- it is worth mentioning
- it's worth mentioning
- in today's world
- in an era of
- needless to say
- without further ado
- let's dive in
- let's explore
- let's take a closer look
- in conclusion
- to sum up
- as we all know
- the future of
- reimagine the way
- transform the way
- take your X to the next level
- everything you need to
- all-in-one
- one-stop shop
- designed with you in mind
- built for the modern
- built to scale with you
- more than just
- not just X, but Y
- whether you're X or Y
- from X to Y
- say goodbye to X
- say hello to Y
- X, redefined
- where X meets Y
- your partner in
- we understand that
- in today's fast-paced
- now more than ever
- the possibilities are endless
- make X a breeze
- without the hassle
- focus on what matters most
- so you can focus on what matters
- work smarter, not harder
- simple, powerful, and secure
- fast, flexible, and reliable
- ready to get started
- let's build something great
- here's the thing
- here's what happened
- here's where it gets interesting
- this is where it gets interesting
- that's when we learned
- but that's not all

Do not repair these phrases with close synonyms. Replace the sentence's function or remove it.

## 3. Banned punctuation and formatting

### Em dashes

Do not use em dashes. Use a comma, full stop, colon, semicolon, or parentheses only when the grammar requires one. Often the sentence should simply be rewritten.

### Curly quotation marks

Use straight ASCII quotation marks and apostrophes in delivered text:

- use `"` instead of curly double quotation marks;
- use `'` instead of curly single quotation marks.

### Mechanical emphasis

Avoid:

- boldface used to manufacture importance inside ordinary prose;
- quoted single words used for drama;
- emoji-decorated headings or bullet labels;
- repeated `- **Header:** description` rows when prose, a table, or a real list would communicate better.

## 4. Banned rhetorical structures

### Negate-then-reveal

Examples:

> This is not a chatbot. It is an agent.

> The issue is not speed. It is predictability.

This structure stages a reveal instead of stating the claim. Write the positive claim directly unless the contrast corrects a documented misunderstanding.

### Negate-then-restate

Example:

> That does not weaken the case. It makes the case more precise.

Two sentences perform one job. State the qualification once.

### Standalone verdict fragments

Delete sentences such as:

- That's critical.
- That distinction matters.
- This is important.
- That changes everything.

Explain the consequence instead of announcing importance.

### Two-beat inflation

Avoid:

> X does Y. It also does Z.

Combine the facts when they belong together. Keep two sentences only when the second develops a distinct consequence or mechanism.

### Self-answering rhetorical questions

Avoid:

> What makes a good API? Predictability.

State the claim directly. A question is useful only when the answer is genuinely uncertain and the article investigates it.

### Automatic triplets

AI copy often stacks three adjectives, verbs, benefits, or fragments because three sounds complete:

- clear, fast, and reliable;
- plan, build, and grow;
- no setup, no friction, no compromise.

Use three items only when the subject naturally has exactly three relevant parts.

### Empty purpose clauses

Flag clauses beginning with:

- so you can;
- helping you;
- enabling teams to;
- giving you the freedom to.

Keep them only when the consequence is concrete and not already implied.

## 5. Meta-signposting

Delete sentences that announce what follows instead of carrying information.

Common failures:

- It's worth being specific about why...
- This is where it gets interesting...
- That's when we learned...
- The real problem was...
- Here's what happened:
- Here's the thing:
- In practice, this meant...
- Before we continue, it helps to understand...
- The next section explains...

Repair by deleting the frame and stating the fact.

Bad:

> The real problem was the queue. The queue had no upper bound.

Better:

> The queue had no upper bound.

A transition is useful when it expresses cause, contrast, sequence, scope, or qualification. It is not useful when it comments on the writer's structure.

## 6. Cadence and robotic prose

### Staccato dramatic fragmentation

Do not use two or more adjacent short sentences to restate or escalate one fact.

Acceptable:

> The plumbing worked. The content was garbage.

The sentences report different facts.

Reject:

> It worked. It worked well enough that we stopped checking it.

The second sentence embellishes the first. Combine or add the missing evidence.

### Drumbeat closers

Do not end two or more consecutive paragraphs with short declarative verdicts. This creates a repeated motivational cadence.

### Uniform syntax

Review three or more consecutive sentences with the same grammatical shape. Vary structure because the logic changes, not as cosmetic noise.

### Repetitive openers

Do not repeatedly begin sentences with the same subject or mechanical transition. Never start sentences with:

- Additionally,
- Furthermore,
- Moreover.

### Missing connective tissue

A paragraph should not be a list of standalone facts. Each sentence should extend, explain, qualify, or pivot from the previous sentence.

Do not add empty transitions to simulate flow. Express the actual relation.

## 7. Structural tells

Review and revise when several occur together:

- paragraphs of nearly identical length;
- every heading followed by a one-sentence explanation and three bullets;
- repeated "you can" or "we help" constructions;
- a neat summary sentence at the end of every section;
- a headline followed by a subtitle that says the same thing;
- feature cards with interchangeable titles and equal-length descriptions;
- a page built entirely from problem, promise, three benefits, testimonial, CTA;
- a CTA repeated without new information;
- overuse of colons to introduce dramatic claims;
- excessive title case;
- generic or clever headings that conceal the section's subject;
- a heading followed by one line that restates it;
- section-ending paragraphs that only preview the next section;
- a conclusion that summarizes the article;
- uninterrupted walls of prose for code, architecture, procedures, or comparisons that need another format.

Do not create artificial roughness to hide AI use. The goal is natural specificity, not random punctuation, slang, typos, or lower-case text.

## 8. Semantic and honesty failures

### Category camouflage

The reader cannot tell what the company sells after reading the hero.

Repair: name the category and main action.

### Benefit fog

The text promises productivity, growth, control, or better work without showing what changes.

Repair: name the task, mechanism, or avoided step.

### Adjective substitution

The draft lacks evidence, so it adds words such as private, powerful, intelligent, flexible, or premium.

Repair: replace the adjective with the fact that earns it.

Bad:

> Private meeting intelligence.

Better:

> Audio, transcripts, and summaries stay on your computer.

### Universal applicability

The sentence could sell software, consulting, insurance, or a coffee machine.

Repair: use the substitution test and add a subject-specific noun and verb.

### Unpaid certainty

The text claims results that depend on adoption, implementation, customer behavior, or missing evidence.

Repair: narrow the claim to what the product or evidence supports directly.

### Fabricated adversity

The draft invents struggle, failure, conflict, or surprise because a story seems too positive.

Repair: preserve the event's real shape. Explain why success occurred rather than manufacturing a failure arc.

### Vague attribution

The draft says "experts agree," "industry observers note," or "many teams believe" without naming a source.

Repair: name and cite the source or remove the attribution.

### Substance deficit

A section passes all surface checks but teaches nothing concrete.

Repair: add a fact, mechanism, decision, example, result, limitation, or usable instruction. If none exists, cut the section.

### Copywriter showing off

A line is memorable mainly because of wordplay, alliteration, symmetry, or metaphor.

Repair: keep it only if it makes the subject easier to understand.

### Manufactured authority

The text tries to sound senior through abstractions, passive voice, or inflated nouns.

Repair: state the decision, action, evidence, or tradeoff directly.

## 9. Repair methods

Use these in order:

1. Delete the sentence and check whether meaning is lost.
2. Replace the claim with a fact.
3. Replace an adjective with a mechanism.
4. Replace an emotional benefit with an observable consequence.
5. Replace a broad audience with one recognizable situation.
6. Replace a slogan with a normal sentence.
7. Combine staged fragments into one sentence.
8. Add a real logical connection between adjacent facts.
9. Restore the user's own phrasing when it is more specific than the rewrite.
10. Cut the section when no concrete substance exists.

Never repair slop with a thesaurus. A synonym preserves the same empty idea.
