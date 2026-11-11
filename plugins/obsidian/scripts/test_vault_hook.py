"""Checks for the vault library and the lifecycle hook, on an isolated fixture vault."""

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import vault
import vault_hook


def note(path: Path, description: str, body: str = "", **properties: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    extra = "".join(f"{key}: {value}\n" for key, value in properties.items())
    path.write_text(f"---\ndescription: {description}\n{extra}---\n{body}\n", encoding="utf-8")


class VaultFixture(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.home = Path(directory.name)
        self.vault = self.home / "knowledge"
        (self.vault / ".obsidian").mkdir(parents=True)
        (self.vault / "AGENTS.md").write_text("# Knowledge vault\n")
        note(self.vault / "Flonker assembly.md", "Gear order and oil ratio for the flonker.",
             aliases="[Flonker build]")
        note(self.vault / "Zibble paint.md", "When to repaint zibbles in the workshop.")
        note(self.vault / "Wumpus crate.md", "Steps and mistakes when stacking wumpus crates.")
        note(self.vault / "Clippings/Flonker review article.md", "Flonker assembly tips from a trade blog.")
        note(self.vault / "Templates/Note.md", "Flonker template that must never match.")
        (self.vault / "Home.md").write_text("---\ndescription: Index\n---\n# Home\n- [[Flonker assembly]]\n")
        (self.vault / "log.md").write_text(
            "---\ndescription: log\n---\n" + "".join(
                f"## [2026-11-0{day}] capture | Entry {day} | codex\n- Created [[Entry {day}]]\n"
                for day in range(1, 8)))
        self.environ = patch.dict(os.environ, {"HOME": str(self.home),
                                               "XDG_CONFIG_HOME": str(self.home / ".config"),
                                               "XDG_STATE_HOME": str(self.home / ".state")})
        self.environ.start()
        self.addCleanup(self.environ.stop)

    def hook(self, event: str, tool: str, payload: dict) -> str:
        with patch("sys.stdin", io.StringIO(json.dumps(payload))), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(vault_hook.main([event, "--tool", tool]), 0)
        return output.getvalue()


class VaultLocationChecks(VaultFixture):
    def test_named_vault_wins_over_the_default(self):
        other = self.home / "notes"
        (other / ".obsidian").mkdir(parents=True)
        (other / "AGENTS.md").write_text("x")
        notes = self.home / ".config/agentkit/AGENTS.local.md"
        notes.parent.mkdir(parents=True)
        notes.write_text(f"## Knowledge vault\n\nKnowledge vault: {other}\n")
        self.assertEqual(vault.locate(), other)

    def test_default_vault_and_missing_vault(self):
        self.assertEqual(vault.locate(), self.vault)
        (self.vault / "AGENTS.md").unlink()
        self.assertIsNone(vault.locate())

    def test_every_hook_is_silent_without_a_vault(self):
        (self.vault / "AGENTS.md").unlink()
        for tool in ("claude", "codex", "kiro"):
            self.assertEqual(self.hook("start", tool, {"session_id": "s"}), "")
            self.assertEqual(self.hook("prompt", tool, {"prompt": "flonker assembly"}), "")
        self.assertEqual(self.hook("stop", "claude", {"session_id": "s"}), "")
        self.assertEqual(json.loads(self.hook("stop", "codex", {"session_id": "s"})), {})


class RecallChecks(VaultFixture):
    def test_relevant_prompt_finds_the_note_and_skips_clippings_and_templates(self):
        found = [hit.title for hit in vault.search(self.vault, "What did we decide about the flonker assembly?")]
        self.assertEqual(found[0], "Flonker assembly")
        self.assertNotIn("Flonker review article", found)
        self.assertNotIn("Note", found)

    def test_aliases_and_plurals_match(self):
        self.assertEqual(vault.search(self.vault, "the build today")[0].title, "Flonker assembly")
        self.assertEqual(vault.search(self.vault, "where are the wumpus crates")[0].title, "Wumpus crate")

    def test_small_vault_matches_names_and_aliases_only(self):
        self.assertEqual(vault.search(self.vault, "gear oil ratio"), [])

    def test_common_words_in_any_language_match_nothing_once_the_vault_is_larger(self):
        for topic in ("alpha", "bravo", "charlie", "delta", "echo", "foxtrot",
                      "golf", "hotel", "india", "juliet", "kilo", "lima"):
            note(self.vault / f"English {topic}.md", f"How the {topic} widget works for the company")
            note(self.vault / f"Dutch {topic}.md", f"Hoe het {topic} werkt voor het bedrijf")
        self.assertEqual(vault.search(self.vault, "how does this work for the company"), [])
        self.assertEqual(vault.search(self.vault, "hoe werkt het voor het bedrijf"), [])
        self.assertEqual(vault.search(self.vault, "gear oil ratio")[0].title, "Flonker assembly")
        self.assertEqual({hit.title for hit in vault.search(self.vault, "the delta widget")},
                         {"Dutch delta", "English delta"})

    def test_unrelated_and_short_prompts_inject_nothing(self):
        self.assertEqual(vault.search(self.vault, "yes, go ahead"), [])
        self.assertEqual(vault.search(self.vault, "refactor the payment form validation"), [])
        self.assertEqual(self.hook("prompt", "claude", {"prompt": "ok"}), "")

    def test_prompt_output_shapes(self):
        claude = json.loads(self.hook("prompt", "claude", {"prompt": "flonker assembly order"}))
        context = claude["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(claude["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("[[Flonker assembly]]", context)
        self.assertIn(str(self.vault / "Flonker assembly.md"), context)
        codex = json.loads(self.hook("prompt", "codex", {"prompt": "flonker assembly order"}))
        self.assertEqual(codex["hookSpecificOutput"]["additionalContext"], context)
        self.assertEqual(self.hook("prompt", "kiro", {"prompt": "flonker assembly order"}).strip(), context.strip())


class StartChecks(VaultFixture):
    def test_brief_carries_path_rules_home_and_recent_log(self):
        brief = vault.brief(self.vault)
        self.assertIn(str(self.vault), brief)
        self.assertIn("vault-recall", brief)
        self.assertIn("- [[Flonker assembly]]", brief)
        self.assertIn("Entry 7", brief)
        self.assertNotIn("Entry 2 ", brief)
        self.assertLessEqual(len(brief), vault.BRIEF_LIMIT)

    def test_brief_stays_within_its_limit(self):
        (self.vault / "Home.md").write_text("# Home\n" + "- [[A very long index line]]\n" * 2000)
        self.assertLessEqual(len(vault.brief(self.vault)), vault.BRIEF_LIMIT)

    def test_start_output_shapes(self):
        claude = json.loads(self.hook("start", "claude", {"session_id": "s"}))
        self.assertEqual(claude["hookSpecificOutput"]["hookEventName"], "SessionStart")
        cursor = json.loads(self.hook("start", "cursor", {"conversation_id": "c"}))
        self.assertIn("vault-recall", cursor["additional_context"])
        self.assertIn("vault-recall", self.hook("start", "kiro", {}))


class StopChecks(VaultFixture):
    def setUp(self):
        super().setUp()
        self.transcript = self.home / "transcript.jsonl"
        self.transcript.write_text("x" * 100)
        self.clock = 1_000_000.0
        clock = patch.object(vault_hook.time, "time", side_effect=lambda: self.clock)
        clock.start()
        self.addCleanup(clock.stop)
        os.utime(self.vault / "log.md", (self.clock - 3600, self.clock - 3600))

    def stop(self, tool="claude", **extra) -> str:
        payload = {"session_id": "s1", "conversation_id": "s1", "transcript_path": str(self.transcript)}
        return self.hook("stop", tool, payload | extra)

    def work(self, minutes: float = 5) -> None:
        with self.transcript.open("a") as handle:
            handle.write("y" * vault_hook.WORK_BYTES)
        self.clock += minutes * 60

    def start(self, tool="claude") -> None:
        self.hook("start", tool, {"session_id": "s1", "conversation_id": "s1",
                                  "transcript_path": str(self.transcript)})

    def test_nudges_once_after_real_work(self):
        self.start()
        self.assertEqual(self.stop(), "")
        self.work()
        nudge = json.loads(self.stop())
        self.assertIn("vault-capture", nudge["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(nudge["hookSpecificOutput"]["hookEventName"], "Stop")
        self.work()
        self.assertEqual(self.stop(), "")
        self.work(minutes=vault_hook.NUDGE_GAP / 60)
        self.assertNotEqual(self.stop(), "")

    def test_quiet_when_continuing_or_after_a_vault_write(self):
        self.start()
        self.work()
        self.assertEqual(self.stop(stop_hook_active=True), "")
        os.utime(self.vault / "log.md", (self.clock, self.clock))
        self.assertEqual(self.stop(), "")
        self.work()
        self.assertNotEqual(self.stop(), "")

    def test_stop_output_shapes_for_codex_and_cursor(self):
        for tool in ("codex", "cursor"):
            self.start(tool)
            self.work()
        self.clock += 1
        codex = json.loads(self.stop("codex"))
        self.assertEqual(codex["decision"], "block")
        self.assertIn("vault-capture", codex["reason"])
        cursor = json.loads(self.stop("cursor", status="completed", loop_count=0))
        self.assertIn("vault-capture", cursor["followup_message"])

    def test_cursor_follow_ups_and_aborted_turns_stay_quiet(self):
        self.start("cursor")
        self.work()
        self.assertEqual(json.loads(self.stop("cursor", status="aborted", loop_count=0)), {})
        self.assertEqual(json.loads(self.stop("cursor", status="completed", loop_count=1)), {})

    def test_dream_sessions_are_left_alone(self):
        self.start()
        self.work()
        with patch.dict(os.environ, {vault.DREAM_ENV: "1"}):
            self.assertEqual(self.stop(), "")
            self.assertEqual(self.hook("start", "claude", {"session_id": "d"}), "")

    def test_unknown_session_starts_its_checkpoint_at_the_first_stop(self):
        self.work()
        self.assertEqual(self.stop(session_id="new", conversation_id="new"), "")


if __name__ == "__main__":
    unittest.main()
