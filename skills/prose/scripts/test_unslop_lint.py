#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import importlib.util
import pathlib
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name("unslop_lint.py")
spec = importlib.util.spec_from_file_location("unslop_lint", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def rules(text: str) -> set[str]:
    return {finding.rule for finding in module.lint(text)}


def assert_has(text: str, expected: set[str]) -> None:
    found = rules(text)
    missing = expected - found
    assert not missing, f"Missing expected rules: {sorted(missing)}; got {sorted(found)}"


def main() -> None:
    old_bad = (
        "In today's fast-paced landscape, unlock seamless, powerful, and secure collaboration — without the hassle. "
        "Not just a tool, but a transformative partner. Get started."
    )
    assert_has(
        old_bad,
        {"banned-word", "banned-phrase", "em-dash", "rule-of-three", "contrast-not-just"},
    )

    curated_bad = (
        "“Here's what happened.” Additionally, the system failed. That's critical. "
        "What makes a good API? Predictability. In practice, retries grew. In practice, latency followed. "
        "Industry observers note that this is important."
    )
    assert_has(
        curated_bad,
        {
            "curly-quote",
            "banned-phrase",
            "mechanical-transition",
            "standalone-verdict",
            "self-answering-question",
            "repeated-in-practice",
            "vague-attribution",
        },
    )

    contrast_bad = "This is not a chatbot. It is an agent. That does not weaken the case. It makes it more precise."
    assert_has(contrast_bad, {"negate-then-reveal", "negate-then-restate"})

    staccato_bad = "It worked. It worked well enough."
    assert_has(staccato_bad, {"short-restatement"})

    staccato_good = "The plumbing worked. The content was garbage."
    assert "short-restatement" not in rules(staccato_good)

    one_in_practice = "In practice, the queue stopped growing after the cap was added."
    assert "repeated-in-practice" not in rules(one_in_practice)

    good = (
        "The alerting system fired sixteen times during one incident. Fourteen alerts described the same database timeout. "
        "We kept the service-impact alert and moved the dependency alerts to the dashboard. The on-call engineer now gets one page."
    )
    errors = [finding for finding in module.lint(good) if finding.severity == "ERROR"]
    assert not errors, f"Unexpected errors for good fixture: {errors}"

    print("All Text Unslop linter tests passed.")



def test_case_folding_keeps_positions() -> None:
    findings = module.lint("\u0130n conclusion, this matters.")
    matches = [f.match for f in findings if f.rule == "banned-phrase"]
    assert matches == ["\u0130n conclusion"], findings


def test_cli_exit_codes_and_json() -> None:
    import json
    import tempfile

    with tempfile.TemporaryDirectory() as directory:
        clean = pathlib.Path(directory) / "clean.txt"
        clean.write_text("The retry queue had no upper bound.\n")
        slop = pathlib.Path(directory) / "slop.txt"
        slop.write_text("In conclusion, everything is seamless.\n")
        assert module.main([str(clean)]) == 0
        assert module.main([str(slop)]) > 0
        report = pathlib.Path(directory) / "report.json"
        with open(report, "w") as handle, contextlib.redirect_stdout(handle):
            module.main([str(slop), "--format", "json"])
        payload = json.loads(report.read_text())
        assert payload, "json report must not be empty"

if __name__ == "__main__":
    main()
    test_case_folding_keeps_positions()
    test_cli_exit_codes_and_json()
    print("All Text Unslop linter tests passed.")
