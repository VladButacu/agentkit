"""Rendered Makefile checks: every target dry-runs, git auth follows the chosen host, and the frontend test target reports failures."""

import os
import re
import shutil
import subprocess
import tempfile
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

RULE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?!=)", re.MULTILINE)
PHONY = re.compile(r"^\.PHONY:((?:.*\\\n)*.*)", re.MULTILINE)
VENV_TYPES = ("python-service", "python-library", "python-service-db", "mcp-server")
HOST_NAMES = {"gitlab": "GitLab", "github": "GitHub", "bitbucket": "Bitbucket"}
TOKEN_VARS = {"gitlab": "GITLAB_TOKEN", "github": "GITHUB_TOKEN", "bitbucket": "BITBUCKET_TOKEN"}
GITLAB_ONLY_TEXT = ("GitLab", "GITLAB_TOKEN", "/-/issues")


def dummy_settings(text, git_host):
    values = {key: f"value-{key.lower()}" for key in required(text) - HOST_KEYS}
    if "GIT_HOST" in values:
        values["GIT_HOST"] = git_host
    return values


def settings_for(text, git_host):
    return with_git_host(text, dummy_settings(text, git_host))


def render_makefile(name, folder, git_host="gitlab"):
    text = template_path(name).read_text(encoding="utf-8")
    path = Path(folder) / "Makefile"
    path.write_text(render(text, settings_for(text, git_host)), encoding="utf-8")
    return path


def targets(makefile):
    return RULE.findall(makefile.read_text(encoding="utf-8"))


def without(variable):
    return {key: value for key, value in os.environ.items() if key != variable}


def run_make(folder, *args, env=None):
    return subprocess.run(
        ["make", "-s", "-f", "Makefile", *args],
        cwd=folder,
        env=env or os.environ,
        capture_output=True,
        text=True,
        check=False,
    )


def dry_run(folder, target):
    return subprocess.run(
        ["make", "-n", "-f", "Makefile", target],
        cwd=folder,
        capture_output=True,
        text=True,
        check=False,
    )


class RenderedTargets(unittest.TestCase):
    def test_every_target_of_every_template_dry_runs(self):
        for path in sorted(TEMPLATES.iterdir()):
            with self.subTest(template=path.stem), tempfile.TemporaryDirectory() as folder:
                makefile = render_makefile(path.stem, folder)
                (Path(folder) / "uv.lock").touch()
                for target in targets(makefile):
                    with self.subTest(target=target):
                        result = dry_run(folder, target)
                        self.assertEqual(result.returncode, 0, result.stderr)

    def test_every_phony_name_is_a_defined_target(self):
        for path in sorted(TEMPLATES.iterdir()):
            with self.subTest(template=path.stem), tempfile.TemporaryDirectory() as folder:
                makefile = render_makefile(path.stem, folder)
                match = PHONY.search(makefile.read_text(encoding="utf-8"))
                if match is None:
                    self.fail("template has no .PHONY line")
                phony = match.group(1).replace("\\\n", " ").split()
                self.assertLessEqual(set(phony), set(targets(makefile)))

    def test_venv_path_is_an_overridable_variable_not_a_ci_branch(self):
        for path in sorted(TEMPLATES.iterdir()):
            with self.subTest(template=path.stem):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("/app/.venv", text)
                self.assertNotIn("ifeq ($(CI)", text)
        for name in VENV_TYPES:
            with self.subTest(template=name):
                text = template_path(name).read_text(encoding="utf-8")
                self.assertIn("VENV ?= .venv", text)


class GitAuth(unittest.TestCase):
    def test_check_fails_without_the_host_token_and_names_it(self):
        for host, variable in TOKEN_VARS.items():
            with self.subTest(host=host), tempfile.TemporaryDirectory() as folder:
                render_makefile("mcp-server", folder, host)
                result = run_make(folder, "check-git-auth", env=without(variable))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(variable, result.stdout + result.stderr)
                self.assertIn(HOST_NAMES[host], result.stdout)

    def test_check_passes_with_the_host_token(self):
        for host, variable in TOKEN_VARS.items():
            with self.subTest(host=host), tempfile.TemporaryDirectory() as folder:
                render_makefile("mcp-server", folder, host)
                result = run_make(folder, "check-git-auth", env={**without(variable), variable: "x"})
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_docker_build_waits_for_the_host_check_and_passes_its_token_as_a_secret(self):
        for host, variable in TOKEN_VARS.items():
            with self.subTest(host=host), tempfile.TemporaryDirectory() as folder:
                render_makefile("mcp-server", folder, host)
                self.assertIn("docker-build: check-git-auth", (Path(folder) / "Makefile").read_text())
                result = dry_run(folder, "docker-build")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"--secret id=git_token,env={variable}", result.stdout)

    def test_dev_install_and_update_deps_need_the_index_token_not_the_host_token(self):
        with tempfile.TemporaryDirectory() as folder:
            makefile = render_makefile("mcp-server", folder).read_text(encoding="utf-8")
        self.assertIn("dev-install: check-index-auth", makefile)
        self.assertIn("update-deps: check-index-auth", makefile)
        self.assertNotIn("check-gitlab-auth", makefile)


class OtherHostText(unittest.TestCase):
    def test_github_and_bitbucket_output_has_no_gitlab_text(self):
        for host in ("github", "bitbucket"):
            for path in sorted(TEMPLATES.iterdir()):
                with self.subTest(host=host, template=path.stem), tempfile.TemporaryDirectory() as folder:
                    makefile = render_makefile(path.stem, folder, host).read_text(encoding="utf-8")
                    for text in GITLAB_ONLY_TEXT:
                        self.assertNotIn(text, makefile)


@unittest.skipUnless(shutil.which("node"), "electron-frontend test target calls node")
class FrontendTestTarget(unittest.TestCase):
    def run_target(self, package_json, npm_exit_status):
        with tempfile.TemporaryDirectory() as folder:
            render_makefile("electron-frontend", folder)
            Path(folder, "package.json").write_text(package_json, encoding="utf-8")
            bin_folder = Path(folder, "fake-bin")
            bin_folder.mkdir()
            npm = bin_folder / "npm"
            npm.write_text(f"#!/bin/sh\nexit {npm_exit_status}\n", encoding="utf-8")
            npm.chmod(0o755)
            env = {**os.environ, "PATH": f"{bin_folder}{os.pathsep}{os.environ['PATH']}"}
            return run_make(folder, "test", env=env)

    def test_failing_test_script_fails_the_target(self):
        result = self.run_target('{"scripts": {"test": "exit 1"}}', npm_exit_status=1)
        self.assertNotEqual(result.returncode, 0)

    def test_passing_test_script_passes_the_target(self):
        result = self.run_target('{"scripts": {"test": "true"}}', npm_exit_status=0)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_test_script_is_reported_and_not_an_error(self):
        result = self.run_target('{"scripts": {"build": "true"}}', npm_exit_status=1)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No test script", result.stdout)


if __name__ == "__main__":
    unittest.main()
