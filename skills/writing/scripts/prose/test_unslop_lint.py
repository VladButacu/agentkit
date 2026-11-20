#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import unslop_lint
from unslop_data import FATAL_PHRASES, FATAL_WORDS, RULE_BY_ID, RULES

SLOP_PATTERNS = HERE.parents[1] / "references" / "prose" / "slop-patterns.md"

# (rule id, text that must trigger the rule, text that must not trigger it)
FIXTURES: list[tuple[str, str, str]] = [
    ("banned-word", "We will leverage the cache.", "The cache stores results."),
    ("generic-structural", "This structural improvement is large.", "The structural engineering review is complete."),
    ("banned-filler", "It is the kind of tool teams need.", "It is a tool teams need."),
    ("repeated-in-practice", "In practice the queue grew. In practice the retries grew.", "In practice, the queue stopped growing."),
    ("banned-phrase", "Let me be clear about the cost.", "The cost is clear from the table."),
    ("contrast-not-just", "Not just a tool, but a partner.", "The queue is bounded but shared."),
    ("from-to", "From notes to drafts in one step.", "The job runs on Mondays."),
    ("whether-you-are", "Whether you're a founder or a developer, start here.", "Check whether you are logged in before you retry."),
    ("where-meets", "Where search meets storage.", "The queue stops when the worker reaches the limit."),
    ("x-redefined", "Search, redefined.", "Search results, redefined by the team, are shown here."),
    ("say-goodbye-hello", "Say goodbye to manual sorting.", "The logs say nothing about the timeout."),
    ("make-a-breeze", "Make releases a breeze.", "The breeze moved the sensor."),
    ("next-level-slogan", "Take your workflow to the next level.", "Take the next step to reduce load."),
    ("designed-to", "The queue is designed to drop old jobs.", "The queue drops old jobs."),
    ("built-to", "The cache is built to survive restarts.", "The cache survives restarts."),
    ("analysis-unpack", "Unpacking this question takes time.", "The archive was unpacked by the script."),
    ("contrast-not-about", "This is not about speed. It is about trust.", "This is about speed. It is about trust."),
    ("negate-then-reveal", "This is not a chatbot. It is an agent.", "The retry queue had no upper bound. It was shared."),
    (
        "negate-then-restate",
        "That does not weaken the case. It makes the case more precise.",
        "That is a valid case. It makes sense.",
    ),
    ("empty-purpose-clause", "Use the export so you can share results.", "The export writes CSV files."),
    ("two-beat-inflation", "The API retries requests. It also logs them.", "The API retries requests, and it also logs them."),
    ("rule-of-three", "It is clear, fast, and reliable.", "The job ran once, then failed."),
    (
        "self-answering-question",
        "What makes a good API? Predictability.",
        "What makes a good API? The answer depends on the client's retry policy and the queue depth.",
    ),
    ("standalone-verdict", "That's critical.", "That's critical for the migration because it blocks the release."),
    ("meta-signposting", "The real problem was the queue.", "The queue had no upper bound."),
    ("mechanical-transition", "Additionally, the system failed.", "The system failed additionally."),
    ("repeated-opener", "The queue grows. The queue stalls. The queue fails.", "The queue grows. The worker stalls. A timer fails."),
    (
        "fragment-triplet",
        "It failed. It retried. It stopped.",
        "The queue failed on startup. It retried the job three times. The retry limit stopped it.",
    ),
    ("short-restatement", "It worked. It worked well enough.", "The plumbing worked. The content was garbage."),
    (
        "drumbeat-closers",
        (
            "The queue grew for an hour before anyone noticed. It stopped.\n\n"
            "The retries doubled the load on the database. It recovered."
        ),
        (
            "The queue grew for an hour before anyone noticed the retries doubling the load on the database.\n\n"
            "The fix capped the queue at one thousand jobs and added an alert for growth."
        ),
    ),
    ("vague-attribution", "Experts say the queue is unsafe.", "The vendor says the queue is unsafe."),
    ("absolute-claim", "Uptime is 100% over the quarter.", "Uptime was 99.9 percent over the quarter."),
    ("generic-emotion", "Get peace of mind.", "The report lists the open incidents."),
    ("fake-pain", "Stop the chaos in your inbox.", "The inbox lists unread mail."),
    ("abstract-density", "Growth, value, and impact drive our vision.", "The queue grew by ten jobs."),
    ("em-dash", "The queue\u2014not the worker\u2014failed.", "The queue failed; the worker did not."),
    ("spaced-en-dash", "The queue \u2013 not the worker \u2013 failed.", "Pages 10\u201320 hold the spec."),
    ("curly-quote", "It’s broken.", "It's broken."),
    ("bold-in-prose", "This is **critical** for the release.", "This is critical for the release."),
    ("inline-header-list", "- **Owner:** the platform team", "- Owner: the platform team"),
    ("emoji-heading", "## \U0001f680 Launch", "## Launch plan"),
    ("quoted-emphasis", 'This is a "game changer" for teams.', 'The log reads "the queue was empty at startup".'),
    ("generic-cta", "Get started", "Get started with the CLI by running the install command."),
    ("generic-heading", "## The challenge", "## The retry queue"),
    ("broad-opening", "In recent years, teams have struggled with alerts.", "The alert queue grew after the deploy."),
]

# Each formula in slop-patterns.md, with a concrete instance and the rule that must flag it.
FORMULA_CASES: dict[str, tuple[str, str]] = {
    "not just X, but Y": ("Not just a tool, but a partner.", "contrast-not-just"),
    "whether you're X or Y": ("Whether you're a founder or a developer, start here.", "whether-you-are"),
    "from X to Y": ("From notes to drafts in one step.", "from-to"),
    "where X meets Y": ("Where search meets storage.", "where-meets"),
    "X, redefined": ("Search, redefined.", "x-redefined"),
    "say goodbye to X": ("Say goodbye to manual sorting.", "say-goodbye-hello"),
    "say hello to Y": ("Say hello to faster reviews.", "say-goodbye-hello"),
    "make X a breeze": ("Make releases a breeze.", "make-a-breeze"),
    "take your X to the next level": ("Take your workflow to the next level.", "next-level-slogan"),
    "designed to": ("The queue is designed to drop old jobs.", "designed-to"),
    "built to": ("The cache is built to survive restarts.", "built-to"),
    "unpacking this question": ("Unpacking this question takes time.", "analysis-unpack"),
}

# Examples quoted in slop-patterns.md: (excerpt that must appear in the reference, text to lint, expected rule).
REFERENCE_EXAMPLES: list[tuple[str, str, str]] = [
    ("This is not a chatbot. It is an agent.", "This is not a chatbot. It is an agent.", "negate-then-reveal"),
    ("The issue is not speed. It is predictability.", "The issue is not speed. It is predictability.", "negate-then-reveal"),
    (
        "That does not weaken the case. It makes the case more precise.",
        "That does not weaken the case. It makes the case more precise.",
        "negate-then-restate",
    ),
    ("What makes a good API? Predictability.", "What makes a good API? Predictability.", "self-answering-question"),
    ("X does Y. It also does Z.", "X does Y. It also does Z.", "two-beat-inflation"),
    ("It worked. It worked well enough that we stopped checking it.", "It worked. It worked well enough that we stopped checking it.", "short-restatement"),
    ("The real problem was the queue.", "The real problem was the queue. The queue had no upper bound.", "meta-signposting"),
    ("- Additionally,", "Additionally, the queue grew.", "mechanical-transition"),
    ("- That's critical.", "That's critical.", "standalone-verdict"),
    ("- That distinction matters.", "That distinction matters.", "standalone-verdict"),
    ("- This is important.", "This is important.", "standalone-verdict"),
    ("- That changes everything.", "That changes everything.", "standalone-verdict"),
]


def rules(text: str) -> set[str]:
    return {finding.rule for finding in unslop_lint.lint(text)}


def normalized(text: str) -> str:
    return " ".join(text.lower().split())


def bullets(section: str) -> list[str]:
    items = []
    for line in section.splitlines():
        if line.startswith("- "):
            items.append(line[2:].strip().rstrip(":").removesuffix("..."))
    return items


def section_between(text: str, start: str, end: str) -> str:
    head = text.index(start)
    return text[head : text.index(end, head)]


class RuleFixtureTests(unittest.TestCase):
    def test_every_rule_has_one_positive_and_one_negative_fixture(self) -> None:
        ids = [rule_id for rule_id, _, _ in FIXTURES]
        self.assertEqual(len(ids), len(set(ids)), "a rule has more than one fixture row")
        self.assertEqual(set(ids), set(RULE_BY_ID), "fixture rows and registered rules differ")

    def test_positive_fixtures_trigger_their_rule_with_matching_text(self) -> None:
        for rule_id, positive, _ in FIXTURES:
            with self.subTest(rule=rule_id):
                matches = [finding.match for finding in unslop_lint.lint(positive) if finding.rule == rule_id]
                self.assertTrue(matches, f"{rule_id} did not fire on {positive!r}")
                source = normalized(positive)
                for match in matches:
                    for part in match.split(" / "):
                        self.assertIn(normalized(part), source, f"{rule_id} reported {part!r}, not in the input")

    def test_negative_fixtures_do_not_trigger_their_rule(self) -> None:
        for rule_id, _, negative in FIXTURES:
            with self.subTest(rule=rule_id):
                self.assertNotIn(rule_id, rules(negative), f"{rule_id} fired on {negative!r}")

    def test_registry_severities_are_error_or_warn(self) -> None:
        self.assertTrue(all(rule.severity in {"ERROR", "WARN"} for rule in RULES))


class DetectionRegressionTests(unittest.TestCase):
    def test_hundred_percent_is_an_absolute_claim(self) -> None:
        self.assertIn("absolute-claim", rules("Uptime is 100% over the quarter."))

    def test_whether_you_are_passes_a_plain_conditional(self) -> None:
        self.assertNotIn("whether-you-are", rules("Check whether you are logged in before you retry."))

    def test_spaced_en_dash_is_flagged_and_range_is_not(self) -> None:
        self.assertIn("spaced-en-dash", rules("Ship it \u2013 then measure."))
        self.assertNotIn("spaced-en-dash", rules("Pages 10\u201320 hold the spec."))

    def test_md_example_with_leading_subject_is_flagged(self) -> None:
        self.assertIn("negate-then-reveal", rules("The issue is not speed. It is predictability."))


class SentenceSplitTests(unittest.TestCase):
    def test_decimal_point_does_not_end_a_sentence(self) -> None:
        sentences = [sentence for sentence, _, _ in unslop_lint.sentence_spans("Use Python 3.11 for this. It works.")]
        self.assertEqual(sentences, ["Use Python 3.11 for this.", "It works."])

    def test_e_g_does_not_end_a_sentence(self) -> None:
        sentences = [sentence for sentence, _, _ in unslop_lint.sentence_spans("Use tools, e.g. a linter. Then stop.")]
        self.assertEqual(sentences, ["Use tools, e.g. a linter.", "Then stop."])

    def test_terminator_at_end_of_text_ends_a_sentence(self) -> None:
        self.assertEqual([s for s, _, _ in unslop_lint.sentence_spans("Done.")], ["Done."])


class CodeAndSuppressionTests(unittest.TestCase):
    def test_inline_code_is_not_checked(self) -> None:
        self.assertNotIn("banned-word", rules("Run `leverage` to test the cache."))

    def test_fenced_code_is_not_checked(self) -> None:
        text = "Example:\n\n```\nWe will leverage the cache. It is a \u2014 test.\n```\n"
        found = rules(text)
        self.assertNotIn("banned-word", found)
        self.assertNotIn("em-dash", found)

    def test_allow_marker_suppresses_only_its_rule_on_its_line(self) -> None:
        text = "This is the kind of leverage we need. <!-- unslop: allow banned-word -->\nWe will leverage the queue."
        findings = unslop_lint.lint(text)
        banned = [(finding.rule, finding.line) for finding in findings if finding.rule == "banned-word"]
        self.assertEqual(banned, [("banned-word", 2)])
        self.assertIn("banned-filler", {finding.rule for finding in findings})

    def test_positions_survive_lowercasing_of_unicode(self) -> None:
        findings = unslop_lint.lint("İn conclusion, this matters.")
        self.assertEqual([f.match for f in findings if f.rule == "banned-phrase"], ["İn conclusion"])


class CliTests(unittest.TestCase):
    def run_cli(self, argv: list[str]) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = unslop_lint.main(argv)
        return code, output.getvalue()

    def test_findings_are_advisory_and_exit_zero(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            slop = Path(directory) / "slop.txt"
            slop.write_text("In conclusion, everything is seamless.\n", encoding="utf-8")
            code, output = self.run_cli([str(slop)])
        self.assertEqual(code, 0)
        self.assertIn("[banned-phrase]", output)
        for gate_word in ("Score", "PASS", "FAIL"):
            self.assertNotIn(gate_word, output)

    def test_clean_file_reports_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            clean = Path(directory) / "clean.txt"
            clean.write_text("The retry queue had no upper bound.\n", encoding="utf-8")
            code, output = self.run_cli([str(clean)])
        self.assertEqual(code, 0)
        self.assertIn("No findings.", output)

    def test_unreadable_file_exits_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                code = unslop_lint.main([str(Path(directory) / "missing.txt")])
        self.assertEqual(code, 2)
        self.assertIn("could not read", error.getvalue())

    def test_bad_arguments_exit_two(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            unslop_lint.main(["--no-such-option"])
        self.assertEqual(raised.exception.code, 2)

    def test_json_report_has_findings_and_counts_without_score(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            slop = Path(directory) / "slop.txt"
            slop.write_text("We will leverage the cache.\n", encoding="utf-8")
            _, output = self.run_cli([str(slop), "--format", "json"])
        payload = json.loads(output)
        self.assertNotIn("score", payload)
        self.assertEqual(payload["counts"]["ERROR"], 1)
        self.assertEqual([finding["rule"] for finding in payload["findings"]], ["banned-word"])


class ReferenceAgreementTests(unittest.TestCase):
    """Keeps slop-patterns.md and the linter tables from drifting apart."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = SLOP_PATTERNS.read_text(encoding="utf-8")

    def test_fatal_words_match_the_reference(self) -> None:
        section = section_between(self.reference, "## 1. Fatal vocabulary", "## 2. Fatal phrases")
        self.assertEqual(set(bullets(section)), set(FATAL_WORDS) | {"structural", "the kind of"})

    def test_literal_phrases_match_the_reference(self) -> None:
        section = section_between(self.reference, "## 2. Fatal phrases", "## 3. Banned punctuation")
        literal, _, formulas = section.partition("Avoid these formulas")
        self.assertEqual(set(bullets(literal)), set(FATAL_PHRASES))
        self.assertEqual(set(bullets(formulas)), set(FORMULA_CASES))

    def test_every_formula_is_flagged_by_its_warn_rule(self) -> None:
        for formula, (example, rule_id) in FORMULA_CASES.items():
            with self.subTest(formula=formula):
                self.assertEqual(RULE_BY_ID[rule_id].severity, "WARN")
                self.assertIn(rule_id, rules(example))

    def test_every_literal_phrase_is_flagged_as_an_error(self) -> None:
        for phrase in sorted(FATAL_PHRASES):
            with self.subTest(phrase=phrase):
                self.assertIn("banned-phrase", rules(phrase.capitalize() + "."))

    def test_meta_signposting_examples_are_flagged_as_errors(self) -> None:
        section = section_between(self.reference, "Common failures:", "Repair by deleting")
        for phrase in bullets(section):
            with self.subTest(phrase=phrase):
                severities = {finding.severity for finding in unslop_lint.lint(phrase + ".")}
                self.assertIn("ERROR", severities)

    def test_examples_quoted_in_the_reference_are_flagged(self) -> None:
        for excerpt, text, rule_id in REFERENCE_EXAMPLES:
            with self.subTest(example=excerpt):
                self.assertIn(excerpt, self.reference)
                self.assertIn(rule_id, rules(text))

    def test_rule_table_matches_the_registry(self) -> None:
        section = self.reference[self.reference.index("## 10. Linter rules") :]
        table = {
            match.group(1): match.group(2)
            for match in re.finditer(r"^\|\s*`([\w-]+)`\s*\|\s*(ERROR|WARN)\s*\|\s*[1-9]\s*\|", section, re.MULTILINE)
        }
        self.assertEqual(table, {rule.rule_id: rule.severity for rule in RULES})


if __name__ == "__main__":
    unittest.main()
