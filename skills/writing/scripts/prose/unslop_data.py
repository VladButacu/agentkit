"""Tables for unslop_lint.py.

references/prose/slop-patterns.md documents every entry here, and
test_unslop_lint.py fails when the two drift apart.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

ERROR = "ERROR"
WARN = "WARN"


@dataclass(frozen=True)
class Rule:
    rule_id: str
    severity: str
    message: str


RULES: tuple[Rule, ...] = (
    Rule("banned-word", ERROR, "Banned or high-signal word. Replace the claim, not only the word."),
    Rule("generic-structural", ERROR, "Use 'structural' only as a precise technical or organizational qualifier."),
    Rule("banned-filler", ERROR, "Banned filler phrase."),
    Rule("repeated-in-practice", ERROR, "'In practice' may appear at most once, for a real theory-versus-operation contrast."),
    Rule("banned-phrase", ERROR, "Banned phrase. Replace the sentence's function, not only its wording."),
    Rule("contrast-not-just", WARN, "Stock contrast formula. State the important claim directly."),
    Rule("from-to", WARN, "Common range slogan. Verify that the range conveys necessary information."),
    Rule("whether-you-are", WARN, "Broad audience setup. Name the actual audience or situation."),
    Rule("where-meets", WARN, "Generic positioning formula. State the combination directly."),
    Rule("x-redefined", WARN, "Generic headline formula."),
    Rule("say-goodbye-hello", WARN, "Slogan formula. Say what changes for the reader."),
    Rule("make-a-breeze", WARN, "Slogan formula. Name the task and what becomes easier."),
    Rule("next-level-slogan", WARN, "Slogan formula. Name the concrete improvement."),
    Rule("designed-to", WARN, "Often introduces intention instead of observable behavior."),
    Rule("built-to", WARN, "Often introduces intention instead of observable behavior."),
    Rule("analysis-unpack", WARN, "Use the analysis directly instead of announcing that the topic will be unpacked."),
    Rule("contrast-not-about", WARN, "Staged contrast formula. Keep only if it corrects a real misunderstanding."),
    Rule("negate-then-reveal", WARN, "Negate-then-reveal theater. State the positive claim directly."),
    Rule("negate-then-restate", WARN, "Two sentences appear to negate and restate one point. Compress the qualification."),
    Rule("empty-purpose-clause", WARN, "Purpose clause may contain a generic benefit. Replace it with an observable consequence."),
    Rule("two-beat-inflation", WARN, "Second-beat sentence may split one claim. Combine unless it develops a distinct point."),
    Rule("rule-of-three", WARN, "Three-part list. Confirm that the subject naturally has three relevant items."),
    Rule("self-answering-question", WARN, "Rhetorical question with a short answer. State the claim unless the question is investigated."),
    Rule("standalone-verdict", ERROR, "Standalone verdict announces importance instead of explaining the consequence."),
    Rule("meta-signposting", ERROR, "Meta-signposting announces structure instead of carrying information."),
    Rule("mechanical-transition", ERROR, "Mechanical transition opener. Express the actual logical relation or remove it."),
    Rule("repeated-opener", WARN, "Sentence opener repeats three or more times. Vary the logic, not only the wording."),
    Rule("fragment-triplet", WARN, "Three consecutive short sentences or fragments create staged advertising cadence."),
    Rule("short-restatement", WARN, "Adjacent short sentences repeat a content word. Check for restatement or fake emphasis."),
    Rule("drumbeat-closers", WARN, "Consecutive paragraphs end with short verdict sentences. Vary the ending."),
    Rule("vague-attribution", WARN, "Vague attribution. Name and cite the source or remove the attribution."),
    Rule("absolute-claim", WARN, "Absolute claim. Confirm that the evidence and scope support it."),
    Rule("generic-emotion", WARN, "Generic emotional benefit. Explain the mechanism that earns it."),
    Rule("fake-pain", WARN, "Dramatic pain language. Use only when grounded in source material or a precise situation."),
    Rule("abstract-density", WARN, "High density of abstract marketing nouns. Replace one with a concrete mechanism or consequence."),
    Rule("em-dash", ERROR, "Em dash is prohibited. Rewrite, or use ordinary punctuation where grammar requires it."),
    Rule("spaced-en-dash", ERROR, "Spaced en dash used as punctuation is prohibited. Rewrite the sentence."),
    Rule("curly-quote", ERROR, "Curly quotation mark or apostrophe is prohibited. Use straight ASCII quotes."),
    Rule("bold-in-prose", WARN, "Bold emphasis inside prose can read like generated formatting. Keep only when structure requires it."),
    Rule("inline-header-list", WARN, "Mechanical inline-header list. Use prose, a table, or a genuinely parallel list."),
    Rule("emoji-heading", WARN, "Emoji-decorated heading. Use an informative text heading."),
    Rule("quoted-emphasis", WARN, "Quoted word or short phrase used for emphasis. Check whether the quotation marks add meaning."),
    Rule("generic-cta", WARN, "Generic call to action. Name the action and its immediate result."),
    Rule("generic-heading", WARN, "Generic heading. Name the evidence, decision, result, or subject of the section."),
    Rule("broad-opening", WARN, "Broad industry opening. Start with a concrete problem, observation, result, or decision."),
)

RULE_BY_ID: dict[str, Rule] = {rule.rule_id: rule for rule in RULES}

FATAL_WORDS: frozenset[str] = frozenset(
    {
        "delve", "landscape", "leverage", "pivotal", "comprehensive", "multifaceted", "harness",
        "foster", "realm", "tapestry", "testament", "watershed", "underscore", "utilize",
        "facilitate", "cutting-edge", "game-changer", "revolutionize", "empower", "unlock",
        "elevate", "supercharge", "streamline", "seamless", "synergy", "effortlessly", "robust",
        "transformative", "unparalleled", "innovative", "next-generation", "world-class",
        "future-proof", "straightforward", "actually", "genuinely", "genuine", "fundamentally",
    }
)

FATAL_PHRASES: frozenset[str] = frozenset(
    {
        "at the end of the day",
        "when it comes to",
        "in a world where",
        "moving forward",
        "circle back",
        "deep dive",
        "double down",
        "take a step back",
        "on the same page",
        "make no mistake",
        "it turns out",
        "let me be clear",
        "lean into",
        "unpack the problem",
        "unpack the issue",
        "navigate the challenges",
        "navigate the complexities",
        "it is important to note",
        "it's important to note",
        "it is worth mentioning",
        "it's worth mentioning",
        "in today's world",
        "in an era of",
        "needless to say",
        "without further ado",
        "let's dive in",
        "let's explore",
        "let's take a closer look",
        "in conclusion",
        "to sum up",
        "as we all know",
        "the future of",
        "reimagine the way",
        "transform the way",
        "everything you need to",
        "all-in-one",
        "one-stop shop",
        "designed with you in mind",
        "built for the modern",
        "built to scale with you",
        "more than just",
        "your partner in",
        "we understand that",
        "in today's fast-paced",
        "now more than ever",
        "the possibilities are endless",
        "without the hassle",
        "focus on what matters most",
        "so you can focus on what matters",
        "work smarter, not harder",
        "simple, powerful, and secure",
        "fast, flexible, and reliable",
        "ready to get started",
        "let's build something great",
        "here's the thing",
        "here's what happened",
        "here's where it gets interesting",
        "this is where it gets interesting",
        "that's when we learned",
        "but that's not all",
    }
)

GENERIC_CTA_LINES: frozenset[str] = frozenset(
    {
        "get started",
        "learn more",
        "discover more",
        "explore more",
        "explore possibilities",
        "begin your journey",
        "unlock access",
        "contact us today",
        "book a call today",
    }
)

GENERIC_HEADINGS: frozenset[str] = frozenset(
    {
        "the challenge",
        "the solution",
        "why it matters",
        "key takeaways",
        "final thoughts",
        "conclusion",
        "the journey",
        "looking ahead",
        "what comes next",
    }
)

ABSTRACT_MARKETING_TERMS: frozenset[str] = frozenset(
    {
        "clarity", "confidence", "control", "efficiency", "growth", "impact", "insights",
        "intelligence", "journey", "mission", "opportunity", "possibilities", "potential",
        "productivity", "success", "transformation", "value", "vision",
    }
)

STANDALONE_VERDICTS: frozenset[str] = frozenset(
    {
        "that's critical",
        "that is critical",
        "that's important",
        "that is important",
        "this is important",
        "that distinction matters",
        "this distinction matters",
        "that matters",
        "this matters",
        "that changes everything",
        "this changes everything",
    }
)

MECHANICAL_OPENERS: frozenset[str] = frozenset({"additionally", "furthermore", "moreover"})

STOPWORDS: frozenset[str] = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "had", "has",
        "have", "he", "her", "his", "i", "in", "is", "it", "its", "of", "on", "or", "our",
        "she", "that", "the", "their", "they", "this", "to", "was", "we", "were", "with", "you",
        "your",
    }
)

# Each regex is applied to prose with fenced and inline code blanked out.
REGEX_RULES: dict[str, re.Pattern[str]] = {
    "contrast-not-just": re.compile(r"\bnot\s+just\b.{0,120}\bbut\b", re.IGNORECASE),
    "from-to": re.compile(r"\bfrom\s+[^\n.!?]{1,45}\s+to\s+[^\n.!?]{1,45}", re.IGNORECASE),
    # Only the audience formula ("whether you're a X or a Y"), not a plain conditional.
    "whether-you-are": re.compile(r"\bwhether\s+you(?:'re| are)\s+(?:a|an)\s+[^.!?\n]{1,60}?\s+or\s+(?:a|an)\b", re.IGNORECASE),
    "where-meets": re.compile(r"\bwhere\s+[^\n.!?]{1,50}\s+meets\s+[^\n.!?]{1,50}", re.IGNORECASE),
    "x-redefined": re.compile(r"^[^\n.!?]{1,60},\s*redefined\.?$", re.IGNORECASE | re.MULTILINE),
    "say-goodbye-hello": re.compile(r"\bsay\s+(?:goodbye|hello)\s+to\b", re.IGNORECASE),
    "make-a-breeze": re.compile(r"\bmake\s+\S+\s+a\s+breeze\b", re.IGNORECASE),
    "next-level-slogan": re.compile(r"\btake\s+your\s+[\w-]+(?:\s+[\w-]+)?\s+to\s+the\s+next\s+level\b", re.IGNORECASE),
    "designed-to": re.compile(r"\bdesigned\s+to\b", re.IGNORECASE),
    "built-to": re.compile(r"\bbuilt\s+to\b", re.IGNORECASE),
    "analysis-unpack": re.compile(
        r"\bunpack(?:ing)?\s+(?:the|this|that|a)\s+(?:problem|issue|topic|idea|question|concept|argument|challenge)\b",
        re.IGNORECASE,
    ),
    "contrast-not-about": re.compile(
        r"\b(?:this|it)\s+is(?:n't| not)\s+about\b.{0,160}\b(?:it is|it's)\s+about\b", re.IGNORECASE
    ),
    "negate-then-reveal": re.compile(
        r"\b(?:this|that|it|the\s+\w+(?:\s+\w+)?)\s+(?:is|was)(?:n't| not)\b[^.!?]{1,120}[.!?]\s*(?:this|that|it)\s+(?:is|was)\b",
        re.IGNORECASE,
    ),
    "negate-then-restate": re.compile(
        r"\bthat\s+(?:doesn't|does not|didn't|did not|isn't|is not)\b[^.!?]{1,100}[.!?]\s*it\s+(?:does|did|is|makes)\b",
        re.IGNORECASE,
    ),
    "empty-purpose-clause": re.compile(
        r"\bso\s+you\s+can\b|\bhelp(?:ing|s)?\s+you\b|\benabling\s+teams\s+to\b|\bgiving\s+you\s+the\s+freedom\s+to\b",
        re.IGNORECASE,
    ),
    # Sentence-initial only: "It also" after a full stop or at the start of a line.
    "two-beat-inflation": re.compile(r"(?:^|(?<=[.!?]\s))It\s+(?:(?:is|was|does|did|can|will)\s+)?also\b", re.MULTILINE),
    "rule-of-three": re.compile(
        r"\b([A-Za-z][\w'-]{1,24})\s*,\s*([A-Za-z][\w'-]{1,24})\s*,\s*(?:and|or)\s+([A-Za-z][\w'-]{1,24})\b",
        re.IGNORECASE,
    ),
    "meta-signposting": re.compile(
        r"\b(?:it(?:'s| is) worth being specific about why|the real problem was|"
        r"before we continue,? it helps to understand|the next section (?:shows|explains|covers)|"
        r"in practice,? this meant)\b",
        re.IGNORECASE,
    ),
    "vague-attribution": re.compile(
        r"\b(?:industry observers|experts|many teams|many companies|some argue|it is widely accepted|it is widely believed)"
        r"\s+(?:say|note|agree|believe|argue|suggest|that)\b",
        re.IGNORECASE,
    ),
    # "always", "never" and "guaranteed" are ordinary words; the rule asks for evidence, it does not ban them.
    "absolute-claim": re.compile(r"(?:\b(?:always|never|guaranteed|guarantee)\b|\b100%)", re.IGNORECASE),
    "generic-emotion": re.compile(r"\b(?:peace of mind|feel confident|complete confidence|total control)\b", re.IGNORECASE),
    "fake-pain": re.compile(r"\b(?:nightmare|chaos|drowning in|painful process|frustrating process)\b", re.IGNORECASE),
    "em-dash": re.compile("\u2014"),
    "spaced-en-dash": re.compile(r"(?<=\s)\u2013(?=\s)"),
    "curly-quote": re.compile("[‘’“”]"),
    "bold-in-prose": re.compile(r"\*\*[^*\n]{1,80}\*\*"),
    "inline-header-list": re.compile(r"(?m)^\s*[-*+]\s+\*\*[^*\n]{1,60}:\*\*"),
}

WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)
EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$")
