# Research notes

## Scope

These notes summarize a July 2026 review of Reddit discussions about AI-written copy, visible AI writing patterns, SaaS landing pages, and generic marketing language. Reddit comments are anecdotal evidence, not controlled research. The repeated patterns are still useful as editorial heuristics because the task is reader perception.

## Repeated complaints

### The product remains unclear

SaaS readers repeatedly object to landing pages that use broad claims and require several sections before explaining the product. They prefer an immediate statement of what the product is, who it is for, and what it does.

Source:
- https://www.reddit.com/r/SaaS/comments/1l7ydmz/your_landing_page_is_probably_too_polite/

### The prose feels polished but hollow

Users describe model output as complete, composed, safe, vague, and padded. The problem is not grammatical correctness. It is the sense that every sentence has been rounded into a presentable shape without adding information.

Sources:
- https://www.reddit.com/r/ChatGPT/comments/1ue7hg2/the_pain_of_using_chatgpt_lately/
- https://www.reddit.com/r/replika/comments/1unctkw/does_anyone_else_feel_like_the_replies_come_out/

### Repeated structures expose the generator

Commonly mentioned tells include em dashes, adjective triplets, repeated short sentences for emphasis, similar paragraph pacing, bold emphasis, single quoted words, and stock transitions.

Sources:
- https://www.reddit.com/r/galway/comments/1u6cyvr/avoid_mcswiggans_ruined_my_wifes_40th_birthday/
- https://www.reddit.com/r/Pennsylvania/comments/1rspw8p/pennsylvania_says_its_hiring_but_nobody_actually/
- https://www.reddit.com/r/antiai/comments/1u7ugzj/what_is_it_that_makes_ai_writing_so_bad/

### Specific details outperform synonym replacement

One copywriting discussion recommends writing toward one person, hunting generic lines, and replacing them with specific detail rather than a more impressive synonym.

Source:
- https://www.reddit.com/r/DigitalProductEmpir/comments/1owvn5p/my_secret_to_writing_copy_that_doesnt_sound_like/

### Customer complaints appear as stories

A marketing discussion about reviewing hundreds of Reddit threads argues that useful buying language often appears in stories about work, reporting, and approval rather than feature wish lists. The practical lesson is to extract situations and consequences, not just keywords.

Source:
- https://www.reddit.com/r/digital_marketing/comments/1rqu9vf/i_tagged_500_reddit_threads_to_find_where/

### Domain audiences reject vague emotional marketing

A SaaS copywriting discussion notes that technical audiences often respond better to exact descriptions of the problem and handling mechanism than to emotional labels such as "nightmare."

Source:
- https://www.reddit.com/user/saasB2Bcopywriter/

## Editorial conclusions used by this skill

1. Specificity is the main defense against median model output.
2. Structure must follow information, not a landing-page template.
3. A word blacklist helps, but structural and semantic checks matter more.
4. Good copy can be polished; the issue is polish without earned meaning.
5. Humanization filters that add slang, errors, or random sentence variation address detection rather than quality.
6. Deterministic linting catches visible habits, while a human semantic pass must catch empty claims.
