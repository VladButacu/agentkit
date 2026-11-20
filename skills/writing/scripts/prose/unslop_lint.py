#!/usr/bin/env python3
"""Advisory linter for generic AI and marketing-writing patterns.

The linter reports surface and structural signals and exits 0 whenever it can
read its input. It cannot decide whether a claim is true, specific or useful.
references/prose.md describes how to act on findings, and
references/prose/slop-patterns.md documents each rule.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from itertools import pairwise
from pathlib import Path

from unslop_data import (
    ABSTRACT_MARKETING_TERMS,
    EMOJI_RE,
    FATAL_PHRASES,
    FATAL_WORDS,
    GENERIC_CTA_LINES,
    GENERIC_HEADINGS,
    HEADING_RE,
    MECHANICAL_OPENERS,
    REGEX_RULES,
    RULE_BY_ID,
    STANDALONE_VERDICTS,
    STOPWORDS,
    WORD_RE,
)

SENTENCE_RE = re.compile(r"(?:e\.g\.|i\.e\.|[^.!?\n]|[.!?](?=\S))+(?:[.!?]+(?=\s|$))?")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
FENCE_RE = re.compile(r"^\s*(?:```|~~~)")
ALLOW_RE = re.compile(r"unslop:\s*allow\s+([\w-]+)")
QUOTED_EMPHASIS_RE = re.compile(r"['\"]([A-Za-z][A-Za-z -]{1,24})['\"]")
OPENER_EXEMPTIONS = frozenset({"the product", "the app"})
STRUCTURAL_QUALIFIERS_RE = re.compile(
    r"\s+(?:engineering|steel|beam|integrity|analysis|load|member|damage|component|change|problem|issue|constraint)\b"
)


@dataclass(frozen=True)
class Finding:
    severity: str
    rule: str
    line: int
    column: int
    match: str
    message: str


Sentence = tuple[str, int, int]


def mask_code(text: str) -> str:
    """Blank fenced and inline code, keeping length and line breaks so positions still line up."""
    out: list[str] = []
    in_fence = False
    for line in text.splitlines(keepends=True):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(_blank(line))
        elif in_fence:
            out.append(_blank(line))
        else:
            out.append(INLINE_CODE_RE.sub(lambda match: _blank(match.group(0)), line))
    return "".join(out)


def _blank(segment: str) -> str:
    return re.sub(r"[^\n]", " ", segment)


def _line_col(text: str, index: int) -> tuple[int, int]:
    line = text.count("\n", 0, index) + 1
    last_newline = text.rfind("\n", 0, index)
    column = index + 1 if last_newline < 0 else index - last_newline
    return line, column


def _emit(findings: list[Finding], text: str, rule_id: str, start: int, matched: str) -> None:
    rule = RULE_BY_ID[rule_id]
    line, column = _line_col(text, start)
    findings.append(Finding(rule.severity, rule.rule_id, line, column, matched.strip(), rule.message))


def sentence_spans(text: str) -> list[Sentence]:
    """Split on a full stop, question mark or exclamation mark that is followed by whitespace or the end of text."""
    spans: list[Sentence] = []
    for match in SENTENCE_RE.finditer(text):
        raw = match.group(0)
        sentence = raw.strip()
        if sentence:
            start = match.start() + (len(raw) - len(raw.lstrip()))
            spans.append((sentence, start, match.end()))
    return spans


def sentence_words(sentence: str) -> list[str]:
    return [word.lower() for word in WORD_RE.findall(sentence)]


def content_words(sentence: str) -> set[str]:
    return {word for word in sentence_words(sentence) if word not in STOPWORDS and len(word) > 2}


def find_words(prose: str, findings: list[Finding]) -> None:
    for word in sorted(FATAL_WORDS):
        for match in re.finditer(rf"(?<![\w-]){re.escape(word)}(?![\w-])", prose, re.IGNORECASE):
            _emit(findings, prose, "banned-word", match.start(), match.group(0))

    for match in re.finditer(r"\bstructural\b", prose, re.IGNORECASE):
        if not STRUCTURAL_QUALIFIERS_RE.match(prose, match.end()):
            _emit(findings, prose, "generic-structural", match.start(), match.group(0))

    for match in re.finditer(r"\bthe kind of\b", prose, re.IGNORECASE):
        _emit(findings, prose, "banned-filler", match.start(), match.group(0))

    in_practice = list(re.finditer(r"\bin practice\b", prose, re.IGNORECASE))
    for match in in_practice[1:]:
        _emit(findings, prose, "repeated-in-practice", match.start(), match.group(0))


def find_phrases(prose: str, findings: list[Finding]) -> None:
    for phrase in sorted(FATAL_PHRASES):
        for match in re.finditer(re.escape(phrase), prose, re.IGNORECASE):
            _emit(findings, prose, "banned-phrase", match.start(), match.group(0))


def find_regex_rules(prose: str, findings: list[Finding]) -> None:
    for rule_id, pattern in REGEX_RULES.items():
        for match in pattern.finditer(prose):
            _emit(findings, prose, rule_id, match.start(), match.group(0))


def find_line_rules(prose: str, findings: list[Finding]) -> None:
    offset = 0
    first_prose_line: tuple[str, int] | None = None
    for line in prose.splitlines(keepends=True):
        raw = line.strip()
        stripped = re.sub(r"^[#>*\-\s]+", "", line).strip().rstrip(".!?")
        if stripped.lower() in GENERIC_CTA_LINES:
            _emit(findings, prose, "generic-cta", offset + max(0, line.find(stripped)), raw)

        heading_match = HEADING_RE.match(line.rstrip("\n"))
        if heading_match:
            heading = heading_match.group(1).strip().rstrip(".!?").lower()
            if EMOJI_RE.search(heading_match.group(1)):
                _emit(findings, prose, "emoji-heading", offset, raw)
            if heading in GENERIC_HEADINGS:
                _emit(findings, prose, "generic-heading", offset, raw)
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
            _emit(findings, prose, "broad-opening", start, opening)


def find_quoted_emphasis(prose: str, findings: list[Finding]) -> None:
    for match in QUOTED_EMPHASIS_RE.finditer(prose):
        if len(match.group(1).split()) <= 3:
            _emit(findings, prose, "quoted-emphasis", match.start(), match.group(0))


def find_sentence_rules(prose: str, findings: list[Finding]) -> None:
    sentences = sentence_spans(prose)
    for index, (sentence, start, _) in enumerate(sentences):
        normalized = sentence.rstrip(".!?").lower()
        if normalized in STANDALONE_VERDICTS:
            _emit(findings, prose, "standalone-verdict", start, sentence)

        words = sentence_words(sentence)
        if words and words[0] in MECHANICAL_OPENERS:
            _emit(findings, prose, "mechanical-transition", start, words[0])

        if sentence.endswith("?") and index + 1 < len(sentences):
            answer = sentences[index + 1][0]
            if 1 <= len(sentence_words(answer)) <= 7:
                _emit(findings, prose, "self-answering-question", start, f"{sentence} {answer}")

        abstract_count = sum(word in ABSTRACT_MARKETING_TERMS for word in words)
        if len(words) >= 5 and abstract_count >= 3:
            _emit(findings, prose, "abstract-density", start, sentence)


def find_cadence(prose: str, findings: list[Finding]) -> None:
    sentences = sentence_spans(prose)

    for index in range(len(sentences) - 2):
        group = sentences[index : index + 3]
        if all(1 <= len(sentence_words(sentence)) <= 5 for sentence, _, _ in group):
            combined = " ".join(sentence for sentence, _, _ in group)
            _emit(findings, prose, "fragment-triplet", group[0][1], combined)

    for index in range(len(sentences) - 1):
        first, first_start, _ = sentences[index]
        second = sentences[index + 1][0]
        first_count = len(sentence_words(first))
        second_count = len(sentence_words(second))
        if 1 <= first_count <= 6 and 1 <= second_count <= 10 and content_words(first) & content_words(second):
            _emit(findings, prose, "short-restatement", first_start, f"{first} {second}")

    openers: dict[str, list[int]] = {}
    for sentence, start, _ in sentences:
        words = sentence_words(sentence)
        if words:
            opener = " ".join(words[:2]) if len(words) >= 2 else words[0]
            openers.setdefault(opener, []).append(start)
    for opener, starts in openers.items():
        if len(starts) >= 3 and opener not in OPENER_EXEMPTIONS:
            _emit(findings, prose, "repeated-opener", starts[0], opener)

    endings = _paragraph_endings(prose)
    for (first_start, first_last, first_count), (_, second_last, second_count) in pairwise(endings):
        if 1 <= first_count < 8 and 1 <= second_count < 8:
            _emit(findings, prose, "drumbeat-closers", first_start, f"{first_last} / {second_last}")


def _paragraph_endings(prose: str) -> list[tuple[int, str, int]]:
    endings: list[tuple[int, str, int]] = []
    for match in re.finditer(r"(?ms)(?:^|\n\s*\n)([^\n].*?)(?=\n\s*\n|\Z)", prose):
        paragraph = match.group(1).strip()
        if not paragraph or paragraph.startswith(("#", "```")):
            continue
        if all(line.lstrip().startswith(("- ", "* ", "+ ")) for line in paragraph.splitlines() if line.strip()):
            continue
        paragraph_sentences = sentence_spans(paragraph)
        if paragraph_sentences:
            last_sentence = paragraph_sentences[-1][0]
            endings.append((match.start(1), last_sentence, len(sentence_words(last_sentence))))
    return endings


def _allowed_rules(text: str) -> dict[int, set[str]]:
    allowed: dict[int, set[str]] = {}
    for number, line in enumerate(text.split("\n"), start=1):
        rules = set(ALLOW_RE.findall(line))
        if rules:
            allowed[number] = rules
    return allowed


def lint(text: str) -> list[Finding]:
    prose = mask_code(text)
    findings: list[Finding] = []
    find_words(prose, findings)
    find_phrases(prose, findings)
    find_regex_rules(prose, findings)
    find_quoted_emphasis(prose, findings)
    find_line_rules(prose, findings)
    find_sentence_rules(prose, findings)
    find_cadence(prose, findings)

    allowed = _allowed_rules(text)
    unique: dict[tuple[str, int, int, str], Finding] = {}
    for finding in findings:
        if finding.rule in allowed.get(finding.line, set()):
            continue
        unique[(finding.rule, finding.line, finding.column, finding.match)] = finding
    return sorted(unique.values(), key=lambda item: (item.line, item.column, item.severity, item.rule))


def render_text(findings: Sequence[Finding], source_name: str) -> str:
    lines = [f"Unslop lint: {source_name}"]
    if not findings:
        lines.append("No findings.")
        return "\n".join(lines)

    counts = {severity: sum(1 for finding in findings if finding.severity == severity) for severity in ("ERROR", "WARN")}
    lines.append(", ".join(f"{severity}={count}" for severity, count in counts.items() if count))
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
    parser = argparse.ArgumentParser(description="Report generic AI and marketing-writing patterns in prose.")
    parser.add_argument("file", nargs="?", help="UTF-8 text or Markdown file. Reads stdin when omitted or '-'.")
    parser.add_argument("--format", choices=("text", "json"), default="text", dest="output_format")
    return parser.parse_args(argv)


def read_input(file_arg: str | None) -> tuple[str, str]:
    if not file_arg or file_arg == "-":
        return sys.stdin.read(), "stdin"
    path = Path(file_arg)
    return path.read_text(encoding="utf-8"), str(path)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    try:
        text, source_name = read_input(args.file)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"unslop_lint: could not read {args.file or 'stdin'}: {exc}", file=sys.stderr)
        return 2

    findings = lint(text)
    if args.output_format == "json":
        payload = {
            "source": source_name,
            "counts": {severity: sum(1 for finding in findings if finding.severity == severity) for severity in ("ERROR", "WARN")},
            "findings": [asdict(finding) for finding in findings],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(render_text(findings, source_name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
