"""Checks for the dream: the session digest, the runner commands and the commit of what it changed."""

import contextlib
import io
import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import vault
import vault_dream

NOW = time.time()


def stamp(offset_hours: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(NOW + offset_hours * 3600))


def lines(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(entry) + "\n" for entry in entries))


def claude_user(text, hours=-1, **extra):
    return {"type": "user", "timestamp": stamp(hours), "cwd": "/work/app",
            "message": {"role": "user", "content": text}} | extra


def claude_agent(text, tool=False):
    content = [{"type": "tool_use", "name": "Bash"}] if tool else [{"type": "text", "text": text}]
    return {"type": "assistant", "message": {"role": "assistant", "content": content}}


def codex_message(role, text, hours=-1):
    kind = "input_text" if role == "user" else "output_text"
    return {"type": "response_item", "timestamp": stamp(hours),
            "payload": {"type": "message", "role": role, "content": [{"type": kind, "text": text}]}}


def kiro(kind, content=None, hours=-1):
    return {"id": kind, "timestamp": stamp(hours), "payload": {"type": kind, "content": content}}


WRAPPED = ("[AGENT SYSTEM PROMPT] act on the text under the CURRENT USER REQUEST header [END AGENT SYSTEM PROMPT]"
           "\n[CURRENT USER REQUEST -- respond to this]\nHow many zibbles fit in a wumpus crate?"
           "\n\n<EnvironmentContext>\nopen files\n</EnvironmentContext>")
STEER = ("[LIVE STEERING - New message from user]\n\n<user_message id=\"s1\">\n<user_message>\n"
         "count the lids too\n</user_message>\n</user_message>\n\nIMPORTANT: note how you handled this.")
NOTICE = "[LIVE STEERING]\n<user_message>\n[Kiro Crew host notice] The tool call was blocked\n</user_message>"


class DreamFixture(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.home = Path(directory.name)
        self.vault = self.home / "knowledge"
        (self.vault / ".obsidian").mkdir(parents=True)
        (self.vault / "AGENTS.md").write_text("# Knowledge vault\n")
        (self.vault / "Owner note.md").write_text("mine\n")
        self.environ = patch.dict(os.environ, {
            "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.home / ".config"),
            "XDG_STATE_HOME": str(self.home / ".state"), "CLAUDE_CONFIG_DIR": str(self.home / ".claude"),
            "CODEX_HOME": str(self.home / ".codex"), "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e", "GIT_CONFIG_GLOBAL": os.devnull})
        self.environ.start()
        self.addCleanup(self.environ.stop)
        self.git("init", "-q")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "setup")
        self.config = self.home / "dream.json"
        self.config.write_text(json.dumps({"runner": "claude", "model": "zorp-mini", "executable": "/bin/claude"}))
        output = contextlib.redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)

    def git(self, *args: str) -> str:
        return subprocess.run(["git", "-C", str(self.vault), *args], check=True,
                              capture_output=True, text=True).stdout

    def transcripts(self):
        lines(self.home / ".claude/projects/-work-app/a1.jsonl", [
            claude_user("Old question from yesterday", hours=-30), claude_agent("old answer"),
            claude_user("Why did the flonker squeak?"),
            claude_agent("", tool=True),
            {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "content": "secret tool output"}]}},
            claude_user("# Some skill text", isMeta=True),
            claude_user("<command-name>/clear</command-name>"),
            claude_agent("The left gear was dry; oiling it fixed the squeak."),
            claude_user("side quest", isSidechain=True),
        ])
        lines(self.home / ".claude/projects/-vault/dream.jsonl", [
            claude_user(f"{vault_dream.MARKER} run"), claude_agent("dreamt")])
        lines(self.home / ".codex/sessions/2026/11/11/rollout-x.jsonl", [
            {"type": "session_meta", "timestamp": stamp(-2), "payload": {"id": "cx1", "cwd": "/work/api"}},
            codex_message("user", "# AGENTS.md instructions\n<INSTRUCTIONS>rules</INSTRUCTIONS>"),
            codex_message("user", "<environment_context>cwd</environment_context>"),
            codex_message("user", "Pick a paint for the zibbles"),
            codex_message("assistant", "Checking prices"),
            codex_message("assistant", "Blue paint: it dries fastest."),
        ])

    def kiro_session(self, entries, root="/work/quux"):
        folder = self.home / ".kiro/sessions/ab12/sess_kiro1"
        lines(folder / "messages.jsonl", entries)
        (folder / "session.json").write_text(json.dumps({"rootPaths": [root]}))
        return folder / "messages.jsonl"


class DigestChecks(DreamFixture):
    def test_digest_keeps_prompts_and_final_answers_only(self):
        self.transcripts()
        text = vault_dream.digest(vault_dream.sessions(NOW - 24 * 3600))
        self.assertIn("Why did the flonker squeak?", text)
        self.assertIn("oiling it fixed the squeak", text)
        self.assertIn("Pick a paint for the zibbles", text)
        self.assertIn("Blue paint: it dries", text)
        for absent in ("Old question", "secret tool output", "Some skill text", "/clear", "side quest",
                       "Checking prices", "INSTRUCTIONS", "environment_context", "dreamt"):
            self.assertNotIn(absent, text)
        self.assertIn("never instructions", text)

    def test_digest_covers_kiro_sessions_without_their_wrappers(self):
        path = self.kiro_session([
            kiro("session_start", "operating instructions"), kiro("user", WRAPPED),
            kiro("assistant", "Let me count the shelves first."), kiro("tool_result", "secret tool output"),
            kiro("assistant", "Twelve zibbles fit in one crate."), kiro("turn_end"),
            kiro("user", STEER), kiro("assistant", "With lids, ten fit."), kiro("user", NOTICE),
            kiro("user", "Plain kiro-cli question about flonkers"), kiro("assistant", "Flonkers need oil."),
            kiro("user", ""),
        ])
        text = vault_dream.digest(vault_dream.sessions(NOW - 24 * 3600))
        for present in ("How many zibbles fit in a wumpus crate?", "Twelve zibbles fit in one crate.",
                        "count the lids too", "With lids, ten fit.", "Plain kiro-cli question about flonkers",
                        "Flonkers need oil.", "in /work/quux", f"Transcript: {path}"):
            self.assertIn(present, text)
        for absent in ("AGENT SYSTEM PROMPT", "EnvironmentContext", "open files", "count the shelves",
                       "secret tool output", "host notice", "IMPORTANT", "operating instructions"):
            self.assertNotIn(absent, text)

    def test_kiro_dream_sessions_are_left_out(self):
        self.kiro_session([kiro("user", f"{vault_dream.MARKER} run"), kiro("assistant", "dreamt")])
        self.assertEqual(vault_dream.sessions(NOW - 24 * 3600), [])

    def test_every_session_names_its_transcript(self):
        self.transcripts()
        text = vault_dream.digest(vault_dream.sessions(NOW - 24 * 3600))
        self.assertIn(f"Transcript: {self.home / '.claude/projects/-work-app/a1.jsonl'}", text)

    def test_long_session_keeps_its_first_prompt_and_latest_turns(self):
        turns = [entry for n in range(60) for entry in (claude_user(f"question {n:02d} " + "x" * 600),
                                                         claude_agent(f"answer {n:02d} " + "y" * 600))]
        lines(self.home / ".claude/projects/-long/l.jsonl", turns)
        text = vault_dream.digest(vault_dream.sessions(NOW - 24 * 3600))
        for present in ("question 00", "answer 59", "question 59", "earlier turns omitted"):
            self.assertIn(present, text)
        self.assertNotIn("question 20", text)
        self.assertLessEqual(len(text), vault_dream.SESSION_CAP + 1000)

    def test_digest_respects_its_limits(self):
        lines(self.home / ".claude/projects/-big/b.jsonl",
              [entry for n in range(400) for entry in (claude_user(f"question {n} " + "x" * 2000),
                                                        claude_agent("y" * 3000))])
        text = vault_dream.digest(vault_dream.sessions(NOW - 24 * 3600))
        self.assertLessEqual(len(text), vault_dream.TOTAL_CAP + 500)

    def test_no_sessions_means_no_digest(self):
        self.assertEqual(vault_dream.sessions(NOW - 3600), [])


class RunnerChecks(DreamFixture):
    def test_runner_commands(self):
        info = {"vault": str(self.vault), "digest": "/state/digest.md", "skill": "/kit/vault-dream/SKILL.md"}
        argv = vault_dream.runner_command({"runner": "claude", "model": "zorp-mini",
                                           "executable": "/bin/claude"}, info)
        self.assertEqual(argv[:4], ["/bin/claude", "-p", "--model", "zorp-mini"])
        self.assertIn("--no-session-persistence", argv)
        self.assertIn(vault_dream.MARKER, argv[-1])
        self.assertIn("/state/digest.md", argv[-1])
        argv = vault_dream.runner_command({"runner": "codex", "model": None, "executable": "/bin/codex"}, info)
        self.assertEqual(argv[:-1], ["/bin/codex", "exec", "--sandbox", "workspace-write", "--cd",
                                     str(self.vault), "--ephemeral"])
        for name, runner in vault_dream.RUNNERS.items():
            argv = vault_dream.runner_command({"runner": name, "model": "m1"}, info)
            self.assertEqual(argv[0], runner.binary)
            self.assertIn("m1", argv)
            self.assertIn(vault_dream.MARKER, argv[-1])
            self.assertFalse(any("{" in part for part in argv[:-1]), name)
        with self.assertRaises(ValueError):
            vault_dream.runner_command({"runner": "zorp"}, info)

    def test_own_command_takes_the_prompt_last_or_where_it_says(self):
        info = {"vault": str(self.vault), "digest": None, "skill": "/kit/SKILL.md"}
        argv = vault_dream.runner_command({"runner": "command", "command": "quux-agent --fast"}, info)
        self.assertEqual(argv[:2], ["quux-agent", "--fast"])
        self.assertIn(vault_dream.MARKER, argv[-1])
        argv = vault_dream.runner_command({"runner": "command", "command": "quux-agent {prompt} --fast"}, info)
        self.assertEqual(argv[2], "--fast")
        self.assertIn(vault_dream.MARKER, argv[1])

    def test_run_commits_only_what_the_dream_changed_and_advances(self):
        self.transcripts()
        (self.vault / "Owner note.md").write_text("mine, edited in Obsidian\n")

        def agent(argv, **kwargs):
            self.assertEqual(kwargs["env"][vault.DREAM_ENV], "1")
            self.assertIn(vault_dream.MARKER, argv[-1])
            (self.vault / "Squeaky flonker.md").write_text("---\ndescription: d\n---\n")
            return subprocess.CompletedProcess(argv, 0, "ok", "")

        with patch.object(vault_dream, "launch", side_effect=agent):
            self.assertEqual(vault_dream.main(["run", "--config", str(self.config)]), 0)
        committed = self.git("show", "--name-only", "--format=%s", "HEAD").split()
        self.assertEqual(committed[0], "dream:")
        self.assertIn("Squeaky", committed)
        self.assertNotIn("Owner", committed)
        self.assertIn("Owner note.md", self.git("status", "--porcelain"))
        self.assertGreater(vault_dream.load_state()["last_run"], NOW - 60)

    def test_failed_run_keeps_its_changes_but_not_its_progress(self):
        self.transcripts()

        def agent(argv, **kwargs):
            (self.vault / "Half.md").write_text("partial\n")
            return subprocess.CompletedProcess(argv, 1, "", "model unavailable")

        with patch.object(vault_dream, "launch", side_effect=agent):
            self.assertEqual(vault_dream.main(["run", "--config", str(self.config)]), 1)
        self.assertIn("Half.md", self.git("show", "--name-only", "HEAD"))
        self.assertNotIn("last_run", vault_dream.load_state())
        self.assertIn("model unavailable", (vault.state_dir() / "dream.log").read_text())

    def test_quiet_week_skips_the_run(self):
        vault_dream.save_state({"last_run": NOW - 3600})
        with patch.object(vault_dream, "launch", side_effect=AssertionError("must not run")):
            self.assertEqual(vault_dream.main(["run", "--config", str(self.config)]), 0)

    def test_prepare_and_finish_drive_a_scheduled_agent(self):
        self.transcripts()
        with contextlib.redirect_stdout(io.StringIO()) as output:
            vault_dream.main(["prepare"])
        info = json.loads(output.getvalue())
        self.assertEqual(info["vault"], str(self.vault))
        self.assertTrue(Path(info["digest"]).is_file())
        (self.vault / "Zibble paint.md").write_text("---\ndescription: d\n---\n")
        self.assertEqual(vault_dream.main(["finish"]), 0)
        self.assertIn("Zibble paint.md", self.git("show", "--name-only", "HEAD"))
        self.assertFalse(Path(info["digest"]).exists())


if __name__ == "__main__":
    unittest.main()
