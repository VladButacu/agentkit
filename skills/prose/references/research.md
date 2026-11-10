# Research behind the voice pass

## Findings and scope

Human-sounding writing is not one measurable style. Three questions need separating: whether a text is easy to understand, whether it sounds like its intended author in its setting, and whether its authorship can be inferred. An authorship classifier does not answer the first two. The skill therefore aims at faithful, coherent communication and treats statistical style features as possible clues rather than a target distribution.

This synthesis combines empirical language research, writing-centre guidance, professional content guidance and editorial lessons from the cover-letter revisions that prompted the skill. Those kinds of evidence support different conclusions. Corpus comparisons describe the sampled texts. Writing guides recommend practices. Reader studies test responses in particular settings. The skill's workflow is an editorial synthesis, not a scientifically validated humanization algorithm.

Sources were checked on 9 September 2026. Model comparisons below concern the versions actually studied, primarily GPT-3, GPT-3.5, GPT-4, GPT-4o and Llama variants. They do not establish the behaviour of every current model or author. Most evidence concerns English. Cultural and language conventions require separate consideration.

## What empirical studies establish

### Genre and grammatical habits matter

Reinhart and colleagues compared parallel human and model continuations across multiple English genres. The models included GPT-4o, GPT-4o Mini and base and instruction-tuned Llama 3 variants. They found differences beyond word choice, including heavier use of nominalizations and participial clauses by instruction-tuned models. The results also varied by model and genre. One especially useful complication is that GPT-4o used agentless passive constructions less often than the human samples. A blanket ban on passive voice is therefore not a research-backed route to human authorship.[^1]

**Editorial consequence:** inspect dense noun phrases, trailing explanatory clauses and genre mismatch when they make a passage hard to follow. Do not mechanically eliminate grammatical structures or apply one conversational style to every artifact.

### Variation across writers is not a recipe for randomness

O'Sullivan's study analysed frequent-word patterns in prompted short stories by humans and GPT-3.5, GPT-4 and Llama 70b. Human texts formed more varied clusters, while outputs from each model clustered more tightly. This was a constrained creative-writing dataset, not a representative sample of cover letters. The analysis deliberately excluded explicit sentence-length and punctuation measures. The paper also cautions against applying stylometry as an academic-integrity verdict.[^2]

**Editorial consequence:** preserve the author's particular choices rather than smoothing everyone into the same voice. The findings do not imply that randomly varying sentence length, increasing repetition or injecting errors will improve a piece.

### Reader impressions can be misleading

Jakesch, Hancock and Naaman studied judgments of self-presentations in professional, hospitality and dating contexts. Across six experiments involving 4,600 participants, judgments were affected by unreliable cues such as first-person pronouns, contractions and family topics. These cues could make generated writing seem human without demonstrating its provenance.[^3]

**Editorial consequence:** personal pronouns and hobbies can be appropriate content, but they are not authenticity certificates. Include them because they express the author's relevant experience or motivation, not because they might influence a detector or an observer's guess.

### Detector errors complicate readability advice

Liang and colleagues found that the detectors they evaluated frequently misclassified English essays by non-native writers as AI-generated. Their paper also showed that detector judgments could shift with changes in linguistic expression. This is evidence about the evaluated tools and samples in 2023, not a current performance estimate for every detector.[^4]

**Editorial consequence:** do not tell a writer to make clear English more complicated to obtain a different authorship score. Do not equate predictable language with inauthentic language. Preserve the writer's multilingual voice without manufacturing errors or stereotypes.

## What makes a passage understandable and personal

### Coherence precedes transitions

UNC's Writing Center distinguishes good organization from the transitions that help readers follow it. If ideas are poorly arranged, inserting connective words cannot supply the missing argument. Its reverse-outline method asks what each paragraph contributes and how the parts relate.[^5]

Yale's coherence guide adds a useful sentence-level practice: introduce new information through a concept already available to the reader. It distinguishes logical coherence from the links that hold words, sentences and paragraphs together.[^6]

**Editorial synthesis:** inspect the actual relation between adjacent sentences. A statement about welcoming feedback does not automatically explain an example about slow builds. The writer needs either a developed claim that the example supports or a different paragraph. This is why replacing a few words failed repeatedly in the cover-letter case.

### Voice and tone serve different purposes

Mailchimp's guide distinguishes a relatively consistent voice from a tone that changes with the reader's situation. It favours clarity over forced entertainment and explicitly warns against making jokes merely to sound lively.[^7]

**Editorial synthesis:** derive voice from the author's language and corrections, then adapt the degree of formality, warmth and directness to the recipient. A recruiter, a future teammate and a customer need different forms of address. Repeated second-person language can sound personal while referring to the wrong person.

### Warmth needs context

Nielsen Norman Group tested different tones in paired website samples. Perceptions of friendliness, trustworthiness and desirability changed, but a more playful insurance example was perceived as friendlier and less trustworthy. The report also describes benefits from conversational language in other contexts. These were website studies, not hiring experiments.[^8]

**Editorial consequence:** warmth is not identical to humour, informality or enthusiasm. A worried customer may need a clear acknowledgment and a practical next step. An enthusiastic applicant may need room to express excitement. Tone should answer the reader's situation without pretending to know their feelings.

### Plain language preserves precision

The UK Department for Education's guidance distinguishes general plain-English techniques from language adapted to users' needs. It accepts specialist terminology when justified by the audience and calls for explanation where needed.[^9]

**Editorial synthesis:** use the shortest familiar expression that preserves meaning, not the shortest word available. "Database" can be clearer than "system," and a named technical action can be easier to understand than a vague phrase about improvements. Length is not the same as difficulty: missing actors, vague references and compressed causal steps can make short sentences hard to read.

### Genre supplies a practical purpose

Yale's cover-letter guidance asks writers to establish interest, demonstrate relevant qualifications and connect them to the position, normally within a page. It recommends developing each middle paragraph around a relevant point rather than restating the CV.[^10] MIT similarly recommends explaining what experience taught the applicant and connecting it to the work, rather than listing accomplishments again.[^11]

**Editorial synthesis:** a personal cover letter still has to make a hiring case. Hobbies can explain sustained curiosity, but they cannot carry the entire argument. A work example earns space when it shows a relevant ability, choice or judgment. The connection to the employer should be stated plainly instead of left for the recruiter to infer.

## Assessment of the supplied humanizer feedback

The supplied feedback names neither its tool nor its dataset, model version, reference population or measurement method. Its claimed human average of 23.2 words per sentence could not be independently substantiated from that information or the sources examined. It should not become a target. Several quotes come from an older cover-letter draft, so even a valid measurement of that excerpt would not describe the latest text.

| Feedback claim | Assessment | Practical use |
|---|---|---|
| A sentence average near 23.2 is human-like | Unverified benchmark with no population or method | Read for comprehension and cadence. Do not aim at that number. |
| An informal sign-off is human-like | A conventional closing fits the genre but is easy for anyone to produce | Keep a suitable sign-off. Do not score it as evidence of authorship. |
| More function words indicate human writing | Such words are used in stylometry, but a corpus pattern is not a universal quota | Preserve grammatical connections instead of deleting articles or adding pronouns mechanically. |
| Shorter words sound approachable | Often useful for clarity, but technical precision and audience matter | Replace unnecessary formality, not necessary terminology. |
| Repetition indicates human recurrence | Repetition can connect ideas or simply waste space | Retain recurring key concepts. Remove duplicate claims. |
| Human-oriented connectives show natural discourse | Their usefulness depends on the relationship they express | Check the logic first, then choose a connective if needed. |
| Hobbies and motivation make the tone personal | Useful when they belong to the author and support the purpose | Keep truthful details. Do not add invented personal material. |
| Familiar openings indicate a human voice | Some cited openings were specifically rejected by the author | The author's corrections take precedence over generic approval. |
| Moderate complexity and few nominalizations are human-like | Some corpus evidence supports related tendencies, but they depend on genre and model | Inspect difficulty, not a ratio. Semicolons are an author preference, not an authorship test. |
| Technical context naturally progresses to values | This is an interpretation requiring examination of the actual argument | Make the relationship explicit and check it as continuous prose. |
| A concise forward-looking ending is human-like | Often useful in an application, but easy to make formulaic | End with a relevant next step instead of an obligatory personality summary. |
| Direct sentiment without hedging is human-like | Direct feeling can suit personal prose. Removing warranted uncertainty can distort facts | Preserve the supplied emotion and the warranted level of certainty. |

## Design decisions for the reusable skill

These are editorial decisions informed by the sources and the revision history, not independent experimental findings.

**Meaning before surface style.** The first question is what the author needs the reader to understand. A sequence of pleasant sentences can fail if none develops the main point. The skill checks paragraph purpose before shortening or replacing words.

**The author supplies the emotion.** An explicit statement of love, frustration or pride is valid material. Removing it merely because it sounds subjective loses information. Conversely, the editor must not invent emotional details to make a restrained author seem passionate.

**Enough space to connect ideas.** The budget is spent on context, the reason for an action and the significance of an example. Filler is removed, but the explanation that makes an example understandable stays. A longer revision can be the clearer one.

**Personal defaults stay personal.** An author's recorded preferences (punctuation, vocabulary, warmth) belong to that author alone; they are not claims about how humans write, and other authors keep their own conventions.

**No numerical human score.** A new linter would duplicate surface checks while implying precision about an editorial judgment. The skill uses review questions and realistic examples instead. Existing lint tools may flag a passage for inspection, but a passing score does not prove that it communicates well.

**Preserve factual boundaries.** An edit must retain who did the work, what is measured, what remains uncertain and which outcomes are only hoped for. In a technical example, improved pipeline time cannot silently become improved customer satisfaction or safer releases.

**Assess the delivered artifact.** When the task includes editing a website, the result must reach the source and any relevant saved copy. Generating a better paragraph in chat does not update a persisted draft. This is a delivery lesson from the case, not a linguistic finding.

## Limits and validation

There is no identified universal threshold for human-sounding prose, and the evidence does not establish that this skill improves hiring outcomes or defeats authorship detection. It supports a workflow whose results must be judged in context. The author's feedback and the intended reader's understanding are essential evidence, but neither alone proves factual accuracy.

Evaluation should examine whether facts and feeling survive, whether the reader can explain the argument, whether pronouns point to the correct people, and whether the text fulfils its purpose. A reviewer should test more than one genre. A technically accurate incident note should not become an enthusiastic personal essay just because the same skill helped a cover letter.

## Sources

[^1]: Alex Reinhart et al. (2025). [Do LLMs write like humans? Variation in grammatical and rhetorical styles](https://arxiv.org/html/2410.16107v2). PNAS 122, e2422455122. Full author manuscript accessed. Corpus comparison, not a writing-quality intervention.
[^2]: James O'Sullivan (11 November 2025). [Stylometric comparisons of human versus AI-generated creative writing](https://www.nature.com/articles/s41599-025-05986-3). Humanities and Social Sciences Communications 12, 1708. Full article accessed. Prompted short-story corpus.
[^3]: Maurice Jakesch, Jeffrey Hancock and Mor Naaman (2023). [Human heuristics for AI-generated language are flawed](https://arxiv.org/pdf/2206.07271). PNAS 120, e2208839120. Author manuscript and abstract accessed. Self-presentation experiments with the models available at the time.
[^4]: Weixin Liang et al. (2023). [GPT detectors are biased against non-native English writers](https://arxiv.org/html/2304.02819v3). Patterns 4, 100779. Author manuscript accessed after the PMC page presented an access challenge. Do not generalize its detector performance to all later tools.
[^5]: University of North Carolina Writing Center (undated). [Transitions](https://writingcenter.unc.edu/tips-and-tools/transitions/). Professional writing instruction, not a controlled trial of humanization.
[^6]: Malena Rice, Elizabeth White and Josie Bircher, Yale Poorvu Center (undated). [Coherence and Flow: From Old to New Information](https://poorvucenter.yale.edu/sites/default/files/2024-12/Coherence%20and%20Flow%20From%20Old%20to%20New%20Information%20GWL%20Handout.pdf). Seven-page teaching handout.
[^7]: Mailchimp (undated). [Voice and Tone](https://styleguide.mailchimp.com/voice-and-tone/). Professional brand guidance. Its particular humour and brand personality are not universal prescriptions.
[^8]: Kate Moran, Nielsen Norman Group (7 August 2016, reviewed 30 January 2024). [The Impact of Tone of Voice on Users' Brand Perception](https://www.nngroup.com/articles/tone-voice-users/). Reader research on paired website samples, not a cover-letter experiment.
[^9]: UK Department for Education (undated). [Guidance to meet the Plain Language standard](https://design.education.gov.uk/content-design/plain-language). Practical service-content guidance.
[^10]: Yale Office of Career Strategy (undated). [Cover Letters & Correspondence](https://ocs.yale.edu/channels/cover-letters-correspondence/). Career guidance, not an experimental estimate of recruitment outcomes.
[^11]: MIT Career Advising & Professional Development (undated on retrieved page). [Career toolkit: Writing a cover letter](https://capd.mit.edu/resources/career-toolkit-writing-a-cover-letter/). Full transcript retrieved during the preceding cover-letter research in this conversation. A later request returned HTTP 429. Only previously retrieved content is used here.
