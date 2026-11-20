"""Template rendering checks."""
# Twin in skills/repo-ops/scripts/pyproject-generator; fix both or neither.

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from render_template import (
    HOST_KEYS,
    TEMPLATES,
    main,
    parse_settings,
    render,
    required,
    template_path,
    with_git_host,
)


def dummy_settings(text, git_host):
    values = {key: f"value-{key.lower()}" for key in required(text) - HOST_KEYS}
    if "GIT_HOST" in values:
        values["GIT_HOST"] = git_host
    return values


def run_render(name, values, folder):
    argv = ["render", name, "--out", str(Path(folder) / "out")]
    for key, value in values.items():
        argv += ["--set", f"{key}={value}"]
    with contextlib.redirect_stderr(io.StringIO()) as errors:
        status = main(argv)
    return status, errors.getvalue()


class RenderChecks(unittest.TestCase):
    def test_every_template_renders_from_its_own_placeholders(self):
        for path in sorted(TEMPLATES.iterdir()):
            with self.subTest(template=path.name):
                text = path.read_text(encoding="utf-8")
                values = with_git_host(text, dummy_settings(text, "gitlab"))
                self.assertNotIn("{{", render(text, values))

    def test_missing_value_is_rejected(self):
        with self.assertRaisesRegex(ValueError, r"missing: \['PROJECT_NAME'\]"):
            render("name = {{PROJECT_NAME}}", {})

    def test_unused_value_is_rejected(self):
        with self.assertRaisesRegex(ValueError, r"unused: \['TYPO'\]"):
            render("name = {{PROJECT_NAME}}", {"PROJECT_NAME": "a", "TYPO": "b"})

    def test_value_is_substituted_verbatim(self):
        self.assertEqual(render("a {{X}} b", {"X": "y $(z) {{Q}}"}), "a y $(z) {{Q}} b")

    def test_setting_needs_key_and_value(self):
        with self.assertRaises(ValueError):
            parse_settings(["NO_EQUALS"])
        with self.assertRaises(ValueError):
            parse_settings(["=value"])

    def test_setting_value_may_contain_equals(self):
        self.assertEqual(parse_settings(["URL=https://x.test/?a=b"]), {"URL": "https://x.test/?a=b"})

    def test_duplicate_setting_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_settings(["A=1", "A=2"])

    def test_service_name_does_not_match_its_db_variant(self):
        self.assertEqual(template_path("python-service").stem, "python-service")

    def test_unknown_template_is_rejected(self):
        with self.assertRaises(ValueError):
            template_path("no-such-type")

    def test_list_prints_the_placeholders_a_template_needs(self):
        text = template_path("python-service").read_text(encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["list", "python-service"]), 0)
        self.assertEqual(output.getvalue().split(), sorted(required(text)))

    def test_list_asks_for_the_git_host_when_the_template_uses_it(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["list", "mcp-server"]), 0)
        self.assertIn("GIT_HOST", output.getvalue().split())


class GitHost(unittest.TestCase):
    def test_known_host_fills_only_the_host_values_the_template_uses(self):
        text = template_path("mcp-server").read_text(encoding="utf-8")
        values = with_git_host(text, {"GIT_HOST": "github"})
        self.assertEqual(values["GIT_TOKEN_VAR"], "GITHUB_TOKEN")
        self.assertEqual(values["GIT_HOST_NAME"], "GitHub")
        self.assertNotIn("ISSUES_SUFFIX", values)

    def test_known_host_renders_without_the_host_values_being_given(self):
        text = template_path("mcp-server").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as folder:
            status, errors = run_render("mcp-server", dummy_settings(text, "bitbucket"), folder)
            self.assertEqual(status, 0, errors)
            self.assertIn("BITBUCKET_TOKEN", (Path(folder) / "out").read_text(encoding="utf-8"))

    def test_other_host_fails_without_its_values_and_renders_with_them(self):
        text = template_path("mcp-server").read_text(encoding="utf-8")
        values = dummy_settings(text, "other")
        with tempfile.TemporaryDirectory() as folder:
            status, errors = run_render("mcp-server", values, folder)
            self.assertEqual(status, 1)
            self.assertIn("missing:", errors)
            values.update(GIT_HOST_NAME="Acme", GIT_TOKEN_VAR="ACME_TOKEN", GIT_TOKEN_HINT="an Acme token")
            status, errors = run_render("mcp-server", values, folder)
            self.assertEqual(status, 0, errors)
            self.assertIn("ACME_TOKEN", (Path(folder) / "out").read_text(encoding="utf-8"))

    def test_git_host_is_unused_when_the_template_has_no_git_values(self):
        text = template_path("python-service").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as folder:
            values = {**dummy_settings(text, "gitlab"), "GIT_HOST": "gitlab"}
            status, errors = run_render("python-service", values, folder)
            self.assertEqual(status, 1)
            self.assertIn("unused: ['GIT_HOST']", errors)

    def test_unknown_host_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown GIT_HOST: sourcehut"):
            with_git_host("{{GIT_TOKEN_VAR}}", {"GIT_HOST": "sourcehut"})


if __name__ == "__main__":
    unittest.main()
