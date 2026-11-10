#!/usr/bin/env python3
"""Deterministic linter for generic AI and marketing-writing patterns.

The linter catches surface and structural signals. It cannot determine whether a
claim is true, specific, useful, or well sourced. Pair it with the semantic and
substance checks in SKILL.md.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

FATAL_WORDS = {
    "delve",
    "landscape",
    "leverage",
    "pivotal",
    "comprehensive",
    "multifaceted",
    "harness",
    "foster",
    "realm",
    "tapestry",
    "testament",
    "watershed",
    "underscore",
    "utilize",
    "facilitate",
    "cutting-edge",
    "game-changer",
    "revolutionize",
    "empower",
    "unlock",
    "elevate",
    "supercharge",
    "streamline",
    "seamless",
    "synergy",
    "effortlessly",
    "robust",
    "transformative",
    "unparalleled",
    "innovative",
    "next-generation",
    "world-class",
    "future-proof",
    "straightforward",
    "actually",
    "genuinely",
    "genuine",
    "fundamentally",
}

FATAL_PHRASES = {
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
    "take your business to the next level",
    "take your workflow to the next level",
    "everything you need to",
    "all-in-one",
    "one-stop shop",
    "designed with you in mind",
    "built for the modern",
    "built to scale with you",
    "more than just",
    "say goodbye to",
    "say hello to",
    "your partner in",
    "we understand that",
    "in today's fast-paced",
    "now more than ever",
    "the possibilities are endless",
    "make it a breeze",
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
    "in practice, this meant",
}

GENERIC_CTA_LINES = {
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

GENERIC_HEADINGS = {
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

ABSTRACT_MARKETING_TERMS = {
    "clarity",
    "confidence",
    "control",
    "efficiency",
    "growth",
    "impact",
    "insights",
    "intelligence",
    "journey",
    "mission",
    "opportunity",
    "possibilities",
    "potential",
    "productivity",
    "success",
    "transformation",
    "value",
    "vision",
}

STANDALONE_VERDICTS = {
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

MECHANICAL_OPENERS = {"additionally", "furthermore", "moreover"}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "his",
    "i",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "our",
    "she",
    "that",
    "the",
    "their",
    "they",
    "this",
    "to",
    "was",
    "we",
    "were",
    "with",
    "you",
    "your",
}

PATTERNS: list[tuple[str, str, re.Pattern[str], str]] = [
    (
        "WARN",
        "contrast-not-just",
        re.compile(r"\bnot\s+just\b.{0,120}\bbut\b", re.IGNORECASE),
        "Stock contrast formula. State the important claim directly.",
    ),
    (
        "WARN",
        "contrast-not-about",
        re.compile(r"\b(?:this|it)\s+is(?:n't| not)\s+about\b.{0,160}\b(?:it is|it's)\s+about\b", re.IGNORECASE),
        "Staged contrast formula. Keep only if it corrects a real misunderstanding.",
    ),
    (
        "WARN",
        "negate-then-reveal",
        re.compile(
            r"\b(?:this|that|it)\s+(?:is|was)(?:n't| not)\b[^.!?]{1,120}[.!?]\s*(?:this|that|it)\s+(?:is|was)\b",
            re.IGNORECASE,
        ),
        "Negate-then-reveal theater. State the positive claim directly.",
    ),
    (
        "WARN",
        "negate-then-restate",
        re.compile(
            r"\bthat\s+(?:doesn't|does not|didn't|did not|isn't|is not)\b[^.!?]{1,100}[.!?]\s*it\s+(?:does|did|is|makes)\b",
            re.IGNORECASE,
        ),
        "Two sentences appear to negate and restate one point. Compress the qualification.",
    ),
    (
        "WARN",
        "whether-you-are",
        re.compile(r"\bwhether\s+you(?:'re| are)\b", re.IGNORECASE),
        "Broad audience setup. Name the actual audience or situation.",
    ),
    (
        "WARN",
        "from-to",
        re.compile(r"\bfrom\s+[^\n.!?]{1,45}\s+to\s+[^\n.!?]{1,45}", re.IGNORECASE),
        "Common range slogan. Verify that the range conveys necessary information.",
    ),
    (
        "WARN",
        "empty-purpose-so-you-can",
        re.compile(r"\bso\s+you\s+can\b", re.IGNORECASE),
        "Purpose clause may contain a generic benefit. Replace it with an observable consequence.",
    ),
    (
        "WARN",
        "empty-purpose-helping-you",
        re.compile(r"\bhelp(?:ing|s)?\s+you\b", re.IGNORECASE),
        "Potentially generic benefit framing. Prefer the product action when possible.",
    ),
    (
        "WARN",
        "designed-to",
        re.compile(r"\bdesigned\s+to\b", re.IGNORECASE),
        "Often introduces intention instead of observable behavior.",
    ),
    (
        "WARN",
        "built-to",
        re.compile(r"\bbuilt\s+to\b", re.IGNORECASE),
        "Often introduces intention instead of observable behavior.",
    ),
    (
        "WARN",
        "absolute-claim",
        re.compile(r"\b(?:always|never|guaranteed|guarantee|100%)\b", re.IGNORECASE),
        "Absolute claim. Confirm that the evidence and scope support it.",
    ),
    (
        "WARN",
        "generic-emotion",
        re.compile(r"\b(?:peace of mind|feel confident|complete confidence|total control)\b", re.IGNORECASE),
        "Generic emotional benefit. Explain the mechanism that earns it.",
    ),
    (
        "WARN",
        "fake-pain",
        re.compile(r"\b(?:nightmare|chaos|drowning in|painful process|frustrating process)\b", re.IGNORECASE),
        "Dramatic pain language. Use only when grounded in source material or a precise situation.",
    ),
    (
        "WARN",
        "x-redefined",
        re.compile(r"^[^\n.!?]{1,60},\s*redefined\.?$", re.IGNORECASE | re.MULTILINE),
        "Generic headline formula.",
    ),
    (
        "WARN",
        "where-meets",
        re.compile(r"\bwhere\s+[^\n.!?]{1,50}\s+meets\s+[^\n.!?]{1,50}", re.IGNORECASE),
        "Generic positioning formula. State the combination directly.",
    ),
    (
        "ERROR",
        "meta-signposting",
        re.compile(
            r"\b(?:it(?:'s| is) worth being specific about why|the real problem was|before we continue,? it helps to understand|the next section (?:shows|explains|covers))\b",
            re.IGNORECASE,
        ),
        "Meta-signposting announces structure instead of carrying information.",
    ),
    (
        "WARN",
        "two-beat-inflation",
        re.compile(r"\bIt\s+(?:is|was|does|did|can|will)\s+also\b", re.IGNORECASE),
        "Second-beat sentence may artificially split one claim. Combine unless it develops a distinct point.",
    ),
    (
        "WARN",
        "vague-attribution",
        re.compile(
            r"\b(?:industry observers|experts|many teams|many companies|some argue|it is widely accepted|it is widely believed)\s+(?:say|note|agree|believe|argue|suggest|that)\b",
            re.IGNORECASE,
        ),
        "Vague attribution. Name and cite the source or remove the attribution.",
    ),
    (
        "WARN",
        "analysis-unpack",
        re.compile(r"\bunpack(?:ing)?\s+(?:the|this|that|a)\s+(?:problem|issue|topic|idea|question|concept|argument|challenge)\b", re.IGNORECASE),
        "Use the analysis directly instead of announcing that the topic will be unpacked.",
    ),
]

SENTENCE_RE = re.compile(r"[^.!?\n]+(?:[.!?]+|$)")
WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$")
EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")


@dataclass(frozen=True)
class Finding:
    severity: str
    rule: str
    line: int
    column: int
    match: str
    message: str


def _line_col(text: str, index: int) -> tuple[int, int]:
    line = text.count("\n", 0, index) + 1
    last_newline = text.rfind("\n", 0, index)
    column = index + 1 if last_newline < 0 else index - last_newline
    return line, column


def _add_match(
    findings: list[Finding],
    text: str,
    severity: str,
    rule: str,
    start: int,
    match: str,
    message: str,
) -> None:
    line, column = _line_col(text, start)
    findings.append(Finding(severity, rule, line, column, match.strip(), message))


def sentence_spans(text: str) -> list[tuple[str, int, int]]:
    spans: list[tuple[str, int, int]] = []
    for match in SENTENCE_RE.finditer(text):
        sentence = match.group(0).strip()
        if sentence:
            start = match.start() + (len(match.group(0)) - len(match.group(0).lstrip()))
            spans.append((sentence, start, match.end()))
    return spans


def sentence_words(sentence: str) -> list[str]:
    return [word.lower() for word in WORD_RE.findall(sentence)]


def content_words(sentence: str) -> set[str]:
    return {word for word in sentence_words(sentence) if word not in STOPWORDS and len(word) > 2}


def find_fatal_words(text: str, findings: list[Finding]) -> None:
    for word in sorted(FATAL_WORDS, key=len, reverse=True):
        pattern = re.compile(rf"(?<![\w-]){re.escape(word)}(?![\w-])", re.IGNORECASE)
        for match in pattern.finditer(text):
            _add_match(
                findings,
                text,
                "ERROR",
                "banned-word",
                match.start(),
                match.group(0),
                f"Banned or high-signal word: {word!r}. Replace the claim, not only the word.",
            )

    structural_pattern = re.compile(r"\bstructural\b", re.IGNORECASE)
    for match in structural_pattern.finditer(text):
        tail = text[match.end() : match.end() + 50].lower()
        if not re.match(
            r"\s+(?:engineering|steel|beam|integrity|analysis|load|member|damage|component|change|problem|issue|constraint)\b",
            tail,
        ):
            _add_match(
                findings,
                text,
                "ERROR",
                "generic-structural",
                match.start(),
                match.group(0),
                "Use 'structural' only as a precise technical or organizational qualifier.",
            )

    for match in re.finditer(r"\bthe kind of\b", text, re.IGNORECASE):
        _add_match(
            findings,
            text,
            "ERROR",
            "banned-filler",
            match.start(),
            match.group(0),
            "Banned filler phrase: 'the kind of'.",
        )

    in_practice = list(re.finditer(r"\bin practice\b", text, re.IGNORECASE))
    for match in in_practice[1:]:
        _add_match(
            findings,
            text,
            "ERROR",
            "repeated-in-practice",
            match.start(),
            match.group(0),
            "'In practice' may appear at most once, and only for a real theory-versus-operation contrast.",
        )


def find_fatal_phrases(text: str, findings: list[Finding]) -> None:
    for phrase in sorted(FATAL_PHRASES, key=len, reverse=True):
        # Match on the original text: lowercasing can change length (U+0130)
        # and shift every later index into the source.
        for match in re.compile(re.escape(phrase), re.IGNORECASE).finditer(text):
            _add_match(
                findings,
                text,
                "ERROR",
                "banned-phrase",
                match.start(),
                match.group(0),
                f"Banned phrase: {phrase!r}.",
            )


def find_punctuation_and_formatting(text: str, findings: list[Finding]) -> None:
    for match in re.finditer("—", text):
        _add_match(
            findings,
            text,
            "ERROR",
            "em-dash",
            match.start(),
            match.group(0),
            "Em dash is prohibited. Rewrite or use ordinary punctuation where grammar requires it.",
        )

    for match in re.finditer("[\u2018\u2019\u201c\u201d]", text):
        _add_match(
            findings,
            text,
            "ERROR",
            "curly-quote",
            match.start(),
            match.group(0),
            "Curly quotation mark or apostrophe is prohibited. Use straight ASCII quotes.",
        )

    for match in re.finditer(r"\*\*[^*\n]{1,80}\*\*", text):
        _add_match(
            findings,
            text,
            "WARN",
            "bold-in-prose",
            match.start(),
            match.group(0),
            "Bold emphasis inside prose can read like generated formatting. Keep only when structure requires it.",
        )

    for match in re.finditer(r"(?m)^\s*[-*+]\s+\*\*[^*\n]{1,60}:\*\*", text):
        _add_match(
            findings,
            text,
            "WARN",
            "inline-header-list",
            match.start(),
            match.group(0),
            "Mechanical inline-header list. Use prose, a table, or a genuinely parallel list.",
        )

    offset = 0
    for line in text.splitlines(keepends=True):
        heading_match = HEADING_RE.match(line.rstrip("\n"))
        if heading_match and EMOJI_RE.search(heading_match.group(1)):
            _add_match(
                findings,
                text,
                "WARN",
                "emoji-heading",
                offset,
                line.strip(),
                "Emoji-decorated heading. Use an informative text heading.",
            )
        offset += len(line)

    for match in re.finditer(r"['\"]([A-Za-z][A-Za-z -]{1,24})['\"]", text):
        content = match.group(1)
        if len(content.split()) <= 3:
            _add_match(
                findings,
                text,
                "WARN",
                "quoted-emphasis",
                match.start(),
                match.group(0),
                "Quoted word or short phrase used for emphasis. Check whether the quotation marks add meaning.",
            )


def find_rhetorical_patterns(text: str, findings: list[Finding]) -> None:
    for severity, rule, pattern, message in PATTERNS:
        for match in pattern.finditer(text):
            _add_match(findings, text, severity, rule, match.start(), match.group(0), message)

    triplet = re.compile(
        r"\b([A-Za-z][\w'-]{1,24})\s*,\s*([A-Za-z][\w'-]{1,24})\s*,\s*(?:and|or)\s+([A-Za-z][\w'-]{1,24})\b",
        re.IGNORECASE,
    )
    for match in triplet.finditer(text):
        _add_match(
            findings,
            text,
            "WARN",
            "rule-of-three",
            match.start(),
            match.group(0),
            "Three-part list. Confirm that the subject naturally has three relevant items.",
        )

    sentences = sentence_spans(text)
    for index, (sentence, start, _) in enumerate(sentences):
        normalized = sentence.strip().rstrip(".!?").lower()
        if normalized in STANDALONE_VERDICTS:
            _add_match(
                findings,
                text,
                "ERROR",
                "standalone-verdict",
                start,
                sentence,
                "Standalone verdict announces importance instead of explaining the consequence.",
            )

        words = sentence_words(sentence)
        if words and words[0] in MECHANICAL_OPENERS:
            _add_match(
                findings,
                text,
                "ERROR",
                "mechanical-transition",
                start,
                words[0],
                "Mechanical transition opener. Express the actual logical relation or remove it.",
            )

        if sentence.rstrip().endswith("?") and index + 1 < len(sentences):
            answer, _answer_start, _ = sentences[index + 1]
            answer_count = len(sentence_words(answer))
            if 1 <= answer_count <= 7:
                _add_match(
                    findings,
                    text,
                    "WARN",
                    "self-answering-question",
                    start,
                    f"{sentence} {answer}",
                    "Rhetorical question followed by a short answer. State the claim directly unless the question is genuinely investigated.",
                )


def find_cadence_patterns(text: str, findings: list[Finding]) -> None:
    sentences = sentence_spans(text)
    word_counts = [len(sentence_words(sentence)) for sentence, _, _ in sentences]

    for index in range(len(sentences) - 2):
        group = sentences[index : index + 3]
        counts = [len(sentence_words(sentence)) for sentence, _, _ in group]
        if all(1 <= count <= 5 for count in counts):
            combined = " ".join(sentence for sentence, _, _ in group)
            _add_match(
                findings,
                text,
                "WARN",
                "fragment-triplet",
                group[0][1],
                combined,
                "Three consecutive short sentences or fragments create staged advertising cadence.",
            )

    for index in range(len(sentences) - 1):
        first, first_start, _ = sentences[index]
        second, _, _ = sentences[index + 1]
        first_count = len(sentence_words(first))
        second_count = len(sentence_words(second))
        first_content = content_words(first)
        second_content = content_words(second)
        overlap = first_content & second_content
        if 1 <= first_count <= 6 and 1 <= second_count <= 10 and overlap:
            _add_match(
                findings,
                text,
                "WARN",
                "short-restatement",
                first_start,
                f"{first} {second}",
                "Adjacent short sentences repeat the same content word. Check for staccato restatement or fake emphasis.",
            )

    openers: dict[str, list[tuple[int, str]]] = {}
    for sentence, start, _ in sentences:
        words = sentence_words(sentence)
        if not words:
            continue
        opener = " ".join(words[:2]) if len(words) >= 2 else words[0]
        openers.setdefault(opener, []).append((start, sentence))

    for opener, occurrences in openers.items():
        if len(occurrences) >= 3 and opener not in {"the product", "the app"}:
            start, _ = occurrences[0]
            _add_match(
                findings,
                text,
                "WARN",
                "repeated-opener",
                start,
                opener,
                f"Sentence opener {opener!r} appears {len(occurrences)} times. Vary the logic, not only the wording.",
            )

    if len(word_counts) >= 6:
        mean = statistics.mean(word_counts)
        if mean > 0:
            coefficient = statistics.pstdev(word_counts) / mean
            if 6 <= mean <= 25 and coefficient < 0.18:
                _add_match(
                    findings,
                    text,
                    "WARN",
                    "uniform-cadence",
                    sentences[0][1],
                    f"{len(word_counts)} sentences",
                    "Sentence lengths are unusually uniform. Check for template cadence and repeated syntax.",
                )

    paragraph_matches = list(re.finditer(r"(?ms)(?:^|\n\s*\n)([^\n].*?)(?=\n\s*\n|\Z)", text))
    paragraph_endings: list[tuple[int, str, int]] = []
    for match in paragraph_matches:
        paragraph = match.group(1).strip()
        if not paragraph or paragraph.startswith(("#", "```")):
            continue
        if all(line.lstrip().startswith(("- ", "* ", "+ ")) for line in paragraph.splitlines() if line.strip()):
            continue
        p_sentences = sentence_spans(paragraph)
        if not p_sentences:
            continue
        last_sentence = p_sentences[-1][0]
        count = len(sentence_words(last_sentence))
        paragraph_endings.append((match.start(1), last_sentence, count))

    for index in range(len(paragraph_endings) - 1):
        first_start, first_last, first_count = paragraph_endings[index]
        _, second_last, second_count = paragraph_endings[index + 1]
        if 1 <= first_count < 8 and 1 <= second_count < 8:
            _add_match(
                findings,
                text,
                "WARN",
                "drumbeat-closers",
                first_start,
                f"{first_last} / {second_last}",
                "Consecutive paragraphs end with short verdict sentences. Vary the ending or remove staged emphasis.",
            )


def find_generic_lines_and_opening(text: str, findings: list[Finding]) -> None:
    offset = 0
    first_prose_line: tuple[str, int] | None = None

    for line in text.splitlines(keepends=True):
        raw = line.strip()
        stripped = re.sub(r"^[#>*\-\s]+", "", line).strip().rstrip(".!?")
        if stripped.lower() in GENERIC_CTA_LINES:
            _add_match(
                findings,
                text,
                "WARN",
                "generic-cta",
                offset + max(0, line.find(stripped)),
                line.strip(),
                "Generic CTA. Name the action and immediate result.",
            )

        heading_match = HEADING_RE.match(line.rstrip("\n"))
        if heading_match:
            heading = heading_match.group(1).strip().rstrip(".!?").lower()
            if heading in GENERIC_HEADINGS:
                _add_match(
                    findings,
                    text,
                    "WARN",
                    "generic-heading",
                    offset,
                    line.strip(),
                    "Generic heading. Name the evidence, decision, result, or subject of the section.",
                )
        elif first_prose_line is None and raw and not raw.startswith(("```", "- ", "* ", "+ ", ">")):
            first_prose_line = (raw, offset)

        offset += len(line)

    if first_prose_line:
        opening, start = first_prose_line
        if re.search(
            r"^(?:in recent years|today,? |the world of |as technology continues|modern (?:businesses|teams|companies)|businesses today)",
            opening,
            re.IGNORECASE,
        ):
            _add_match(
                findings,
                text,
                "WARN",
                "broad-opening",
                start,
                opening,
                "Broad industry opening. Start with a concrete problem, observation, result, or decision.",
            )

    for sentence, start, _ in sentence_spans(text):
        words = sentence_words(sentence)
        abstract_count = sum(word in ABSTRACT_MARKETING_TERMS for word in words)
        if len(words) >= 5 and abstract_count >= 3:
            _add_match(
                findings,
                text,
                "WARN",
                "abstract-density",
                start,
                sentence,
                "High density of abstract marketing nouns. Replace at least one with a concrete action, mechanism, or consequence.",
            )


def lint(text: str) -> list[Finding]:
    findings: list[Finding] = []
    find_fatal_words(text, findings)
    find_fatal_phrases(text, findings)
    find_punctuation_and_formatting(text, findings)
    find_rhetorical_patterns(text, findings)
    find_cadence_patterns(text, findings)
    find_generic_lines_and_opening(text, findings)

    unique: dict[tuple[str, str, int, int, str], Finding] = {}
    for finding in findings:
        key = (finding.severity, finding.rule, finding.line, finding.column, finding.match)
        unique[key] = finding
    return sorted(unique.values(), key=lambda item: (item.line, item.column, item.severity, item.rule))


def score(findings: Iterable[Finding]) -> int:
    penalties = {"ERROR": 12, "WARN": 4, "INFO": 1}
    return max(0, 100 - sum(penalties.get(finding.severity, 0) for finding in findings))


def render_text(findings: Sequence[Finding], source_name: str) -> str:
    lines = [f"Text Unslop lint: {source_name}", f"Score: {score(findings)}/100"]
    if not findings:
        lines.append("PASS: no deterministic slop patterns found.")
        lines.append("Run the semantic, honesty, and section-substance checks before delivery.")
        return "\n".join(lines)

    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    summary = ", ".join(
        f"{severity}={counts[severity]}" for severity in ("ERROR", "WARN", "INFO") if severity in counts
    )
    lines.append(summary)
    lines.append("")

    for finding in findings:
        snippet = re.sub(r"\s+", " ", finding.match)
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        lines.append(
            f"{finding.severity} {finding.line}:{finding.column} [{finding.rule}] {finding.message} Match: {snippet!r}"
        )
    return "\n".join(lines)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint public-facing prose for generic AI and marketing patterns.")
    parser.add_argument("file", nargs="?", help="UTF-8 text or Markdown file. Reads stdin when omitted or '-'.")
    parser.add_argument("--format", choices=("text", "json"), default="text", dest="output_format")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when warnings are present.")
    return parser.parse_args(argv)


def read_input(file_arg: str | None) -> tuple[str, str]:
    if not file_arg or file_arg == "-":
        return sys.stdin.read(), "stdin"
    path = Path(file_arg)
    try:
        return path.read_text(encoding="utf-8"), str(path)
    except OSError as exc:
        raise SystemExit(f"Could not read {path}: {exc}") from exc


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    text, source_name = read_input(args.file)
    findings = lint(text)

    if args.output_format == "json":
        payload = {
            "source": source_name,
            "score": score(findings),
            "counts": {
                severity: sum(1 for finding in findings if finding.severity == severity)
                for severity in ("ERROR", "WARN", "INFO")
            },
            "findings": [asdict(finding) for finding in findings],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(render_text(findings, source_name))

    has_error = any(finding.severity == "ERROR" for finding in findings)
    has_warning = any(finding.severity == "WARN" for finding in findings)
    if has_error or (args.strict and has_warning):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
