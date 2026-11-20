"""Rendered pyproject checks: every template parses, URLs follow the chosen host, and the reference agrees with the templates."""

import re
import tomllib
import unittest
from pathlib import Path

from render_template import (
    HOST_KEYS,
    TEMPLATES,
    render,
    required,
    template_path,
    with_git_host,
)

REFERENCE = Path(__file__).resolve().parents[2] / "references" / "pyproject-generator.md"
ASYNCIO_RULE = re.compile(r"`asyncio_mode` is `(\w+)`")
ASYNCIO_SETTING = re.compile(r'^asyncio_mode = "(\w+)"', re.MULTILINE)
HOMEPAGE = "https://example.test/acme/tool"
ISSUES_SUFFIXES = {"gitlab": "/-/issues", "github": "/issues", "bitbucket": "/issues"}
BUG_TRACKER_TEMPLATES = ("mcp-server", "python-library", "python-service", "python-service-db")
GITLAB_ONLY_TEXT = ("GitLab", "GITLAB_TOKEN", "/-/issues")


def settings_for(text, git_host, **overrides):
    values = {key: f"value-{key.lower()}" for key in required(text) - HOST_KEYS}
    if "GIT_HOST" in values:
        values["GIT_HOST"] = git_host
    values.update(overrides)
    return with_git_host(text, values)


def render_text(name, git_host="gitlab", **overrides):
    text = template_path(name).read_text(encoding="utf-8")
    return render(text, settings_for(text, git_host, **overrides))


def render_template(name, git_host="gitlab", **overrides):
    return tomllib.loads(render_text(name, git_host, **overrides))


class RenderedTemplates(unittest.TestCase):
    def test_every_template_renders_to_valid_toml(self):
        for path in sorted(TEMPLATES.iterdir()):
            with self.subTest(template=path.stem):
                render_template(path.stem)

    def test_no_author_specific_values_remain(self):
        for path in sorted(TEMPLATES.iterdir()):
            with self.subTest(template=path.stem):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("omni-forge", text)
                self.assertNotIn("Proprietary", text)

    def test_python_library_minimum_and_classifier_follow_one_value(self):
        project = render_template("python-library", PYTHON_VERSION="3.13")["project"]
        self.assertEqual(project["requires-python"], ">=3.13")
        self.assertIn("Programming Language :: Python :: 3.13", project["classifiers"])

    def test_electron_backend_python_constraint_is_supplied(self):
        project = render_template("electron-backend", PYTHON_CONSTRAINT=">=3.12,<3.13")["project"]
        self.assertEqual(project["requires-python"], ">=3.12,<3.13")

    def test_asyncio_mode_in_every_template_matches_the_reference(self):
        rule = ASYNCIO_RULE.search(REFERENCE.read_text(encoding="utf-8"))
        if rule is None:
            self.fail("reference does not state the asyncio_mode rule")
        for path in sorted(TEMPLATES.iterdir()):
            with self.subTest(template=path.stem):
                modes = ASYNCIO_SETTING.findall(path.read_text(encoding="utf-8"))
                self.assertEqual(modes, [rule.group(1)])


class ProjectUrls(unittest.TestCase):
    def test_bug_tracker_is_the_homepage_plus_the_host_suffix(self):
        for host, suffix in ISSUES_SUFFIXES.items():
            for name in BUG_TRACKER_TEMPLATES:
                with self.subTest(host=host, template=name):
                    urls = render_template(name, host, HOMEPAGE_URL=HOMEPAGE)["project"]["urls"]
                    self.assertEqual(urls["Bug Tracker"], HOMEPAGE + suffix)

    def test_library_repository_is_the_homepage_with_git_suffix_for_every_host(self):
        for host in ISSUES_SUFFIXES:
            with self.subTest(host=host):
                urls = render_template("python-library", host, HOMEPAGE_URL=HOMEPAGE)["project"]["urls"]
                self.assertEqual(urls["Repository"], HOMEPAGE + ".git")

    def test_github_and_bitbucket_output_has_no_gitlab_text(self):
        for host in ("github", "bitbucket"):
            for path in sorted(TEMPLATES.iterdir()):
                with self.subTest(host=host, template=path.stem):
                    text = render_text(path.stem, host)
                    for forbidden in GITLAB_ONLY_TEXT:
                        self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
