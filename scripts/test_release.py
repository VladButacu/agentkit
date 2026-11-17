"""Release-tag helpers and the tag-aware update notice."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import actions
import release


class ReleaseFixture(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.repo = Path(self.directory.name) / "repo"
        self.repo.mkdir()
        self.state = Path(self.directory.name) / "state"
        for key, value in {"REPO": self.repo, "STATE": self.state}.items():
            replacement = patch.object(actions, key, value)
            replacement.start()
            self.addCleanup(replacement.stop)

    def fake_run(self, answers: dict, default=""):
        """answers maps an exact argument to git stdout, or an Exception to a failing command."""
        def run(args):
            for key, value in answers.items():
                if key in args:
                    if isinstance(value, Exception):
                        raise value
                    return value
            if isinstance(default, Exception):
                raise default
            return default
        return run

    def marker(self) -> dict:
        return json.loads((self.state / "update-check.json").read_text())


class TagHelperChecks(ReleaseFixture):
    def test_tag_helpers_return_none_on_git_failure(self):
        with patch.object(actions, "run", side_effect=RuntimeError("git failed")):
            self.assertIsNone(release.exact_tag(self.repo))
            self.assertIsNone(release.latest_tag(self.repo))
            self.assertFalse(release.contains(self.repo, "v0.4.0"))
            self.assertFalse(release.at_release(self.repo))

    def test_tag_helpers_read_git_output(self):
        answers = self.fake_run({"--exact-match": "v0.4.1", "--abbrev=0": "v0.5.0",
                                 "--is-ancestor": ""})
        with patch.object(actions, "run", side_effect=answers):
            self.assertEqual(release.exact_tag(self.repo), "v0.4.1")
            self.assertEqual(release.latest_tag(self.repo), "v0.5.0")
            self.assertTrue(release.contains(self.repo, "v0.5.0"))
            self.assertTrue(release.at_release(self.repo))


class UpdateNoticeChecks(ReleaseFixture):
    def notice(self, answers):
        with patch.object(release, "notify", return_value=True) as notify, \
             contextlib.redirect_stdout(io.StringIO()) as output:
            release.check_update()
        return output.getvalue(), notify

    def test_check_update_reports_new_tag_and_notifies_once(self):
        answers = self.fake_run({"--exact-match": "v0.4.1", "--abbrev=0": "v0.5.0",
                                 "--is-ancestor": RuntimeError("exit 1")})
        with patch.object(actions, "run", side_effect=answers):
            output, notify = self.notice(answers)
        self.assertIn("v0.5.0 available (running v0.4.1)", output)
        notify.assert_called_once()
        self.assertEqual(self.marker()["current"], "v0.4.1")
        self.assertEqual(self.marker()["latest"], "v0.5.0")
        with patch.object(actions, "run", side_effect=answers):
            output, notify = self.notice(answers)
        self.assertIn("v0.5.0 available", output)
        notify.assert_not_called()

    def test_check_update_silent_when_tree_already_contains_latest(self):
        answers = self.fake_run({"--exact-match": RuntimeError("untagged"),
                                 "--abbrev=0": "v0.5.0", "--is-ancestor": ""})
        with patch.object(actions, "run", side_effect=answers):
            output, _ = self.notice(answers)
        self.assertEqual(output, "")
        self.assertEqual(self.marker()["message"], "")

    def test_check_update_silent_on_any_git_failure(self):
        with patch.object(actions, "run", side_effect=RuntimeError("no git")), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(release.check_update(), 0)
        self.assertEqual(output.getvalue(), "")
        self.assertFalse((self.state / "update-check.json").exists())

    def test_notify_absence_still_writes_the_marker(self):
        answers = self.fake_run({"--exact-match": "v0.4.1", "--abbrev=0": "v0.5.0",
                                 "--is-ancestor": RuntimeError("exit 1")})
        with patch.object(actions, "run", side_effect=answers), \
             patch.object(release, "notify", return_value=False), \
             contextlib.redirect_stdout(io.StringIO()):
            release.check_update()
        self.assertTrue(self.marker()["message"])
        self.assertEqual(self.marker()["notified"], 0)


class NotifierChecks(ReleaseFixture):
    def test_notify_commands_per_platform(self):
        calls = []
        with patch.object(actions, "run", side_effect=lambda args: calls.append(args) or ""), \
             patch.object(release.shutil, "which", side_effect=lambda name: f"/usr/bin/{name}"):
            with patch.object(release.sys, "platform", "darwin"):
                self.assertTrue(release.notify("agentkit", "v0.5.0 available"))
            self.assertEqual(calls[-1], ["osascript", "-e",
                                         ('display notification "v0.5.0 available" '
                                          'with title "agentkit"')])
            with patch.object(release.sys, "platform", "linux"):
                self.assertTrue(release.notify("agentkit", "v0.5.0 available"))
            self.assertEqual(calls[-1], ["notify-send", "agentkit", "v0.5.0 available"])
            with patch.object(release.sys, "platform", "win32"):
                self.assertFalse(release.notify("agentkit", "v0.5.0 available"))
            self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
