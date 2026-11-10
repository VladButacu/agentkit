# Blog and article writing rules

## Contents

1. Article contract
2. Openings
3. Information control
4. Paragraph logic
5. Section substance
6. Headings
7. Technical material
8. Narrative honesty
9. Closings
10. Final article audit

## 1. Article contract

Before drafting, write an internal one-sentence contract:

> By the end, the reader will understand [specific thing] because the article shows [evidence, mechanism, example, or decision].

Do not publish the contract. Use it to reject sections that merely decorate the topic.

An article needs a reason to exist beyond announcing a product, repeating common advice, or restating source material.

## 2. Openings

Open with one concrete source of tension:

- a failure mode;
- a surprising observation;
- an unresolved constraint;
- a specific decision;
- a result that needs explanation;
- a real question created by evidence.

Do not open with:

- a broad industry statement;
- a dictionary definition;
- "In today's...";
- a claim that technology is changing rapidly;
- a generic anecdote invented to create relatability;
- a full summary of the article.

An opening should create a reason to continue without hiding the subject. Suspense comes from an unresolved cause, tradeoff, or consequence, not from withholding basic context.

Weak:

> Modern engineering teams face an increasingly complex observability landscape.

Stronger:

> Our alerting system fired sixteen times during one incident. Fourteen alerts described the same failure.

## 3. Information control

Do not list every system, step, and outcome in the introduction. Introduce details when the reader needs them.

Do not manufacture mystery with phrases such as "what happened next" or "the answer surprised us." State the evidence and let its consequence create interest.

Reveal the article's subject early. Delay only the explanation, decision, or result that the body will establish.

## 4. Paragraph logic

A paragraph should develop one thought, not collect unrelated facts.

Each sentence should do one of four things relative to the previous sentence:

- extend it with detail;
- explain its cause or mechanism;
- qualify or limit it;
- pivot to a real contrast or consequence.

Do not add mechanical transitions such as "Additionally," "Furthermore," or "Moreover." Use a transition only when the logical relation is not already clear.

Avoid paragraphs made from interchangeable declarative sentences. Vary sentence structure because the logic varies, not to create cosmetic rhythm.

Delete section-ending paragraphs that only preview the next section.

## 5. Section substance

Every section must teach at least one concrete thing that the reader did not know from the heading or introduction.

Valid substance includes:

- a number with source, scope, or timeframe;
- a code path, architecture detail, or operational mechanism;
- a decision and the rejected alternative;
- a failure and the evidence that identified it;
- a limitation that changes how the result should be interpreted;
- a specific example;
- a repeatable procedure;
- a source-backed inference.

A story is not substance by itself. A section fails when its only content is setup, atmosphere, reaction, or a restatement of the heading.

## 6. Headings

Write headings that identify the subject, result, decision, or evidence in the section.

Prefer:

- "Sixteen alerts, two real incidents"
- "Why the retry queue kept growing"
- "We kept Postgres and removed Redis"
- "The 9B model was slower but missed fewer tool calls"

Avoid:

- generic headings such as "The challenge" or "Key takeaways";
- clever headings whose meaning appears only after reading the section;
- clickbait questions;
- vague metaphor;
- negative framing when the section describes a positive result;
- a heading followed by one line that merely repeats it.

Use sentence case unless the publication requires another style.

## 7. Technical material

Use prose for reasoning and narrative. Use the form that best carries technical information:

- code blocks for executable or exact code;
- tables for comparisons with stable dimensions;
- diagrams for flows, boundaries, and architecture;
- numbered steps for procedures;
- bullets for genuinely parallel items.

Do not force a long technical explanation into uninterrupted prose. Do not turn ordinary prose into repeated `- **Label:** description` rows when a paragraph reads better.

Explain what a diagram or code sample proves. Do not insert it as decoration.

## 8. Narrative honesty

Do not invent adversity, uncertainty, conflict, or failure to make a success story dramatic.

If the source describes a successful implementation, explain why it worked. Do not recast it as a disaster narrowly avoided.

Do not claim a lesson was learned unless the source shows a prior belief, new evidence, and a changed decision.

Avoid vague attribution:

- "industry observers note";
- "experts agree";
- "many teams believe";
- "it is widely accepted."

Name the source or remove the attribution.

Separate observation from inference. Use direct language such as "The logs show..." for evidence and "This suggests..." for interpretation.

## 9. Closings

Do not summarize the article or repeat each section.

End on the final useful implication:

- the decision the evidence supports;
- the constraint that remains;
- the next experiment;
- the practical action;
- the unanswered question that follows directly from the article.

The final sentence does not need to sound quotable. It needs to finish the thought.

Weak:

> In conclusion, observability is essential for modern engineering teams.

Stronger:

> We now page on service impact and keep the duplicate dependency alerts in the dashboard, where they still help diagnosis without waking anyone up.

## 10. Final article audit

Before delivery:

1. Search for every banned word, phrase, em dash, and curly quotation mark.
2. Delete sentences that only announce the next sentence.
3. Check that no failure, quote, metric, source, or emotional reaction was invented.
4. Identify one concrete takeaway per section.
5. Break repeated grammatical patterns and repeated sentence openings.
6. Check that adjacent short sentences carry different facts rather than restating one fact.
7. Confirm that the introduction creates a question without summarizing the whole article.
8. Confirm that the conclusion ends the argument without summarizing it.
9. Replace generic headings with headings that name the section's evidence or decision.
10. Ask: "What exact passage would make a careful reader suspect generated filler?" Rewrite or cut it.
