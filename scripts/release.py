"""Release-tag awareness: what the clone runs, what upstream released, and the session notice.

Other modules read the paths as `actions.NAME` at call time, so tests can redirect them."""

import json
import shutil
import sys
import time
from pathlib import Path

import actions

UPDATE_CHECK_PERIOD = 24 * 3600


def exact_tag(repo: Path) -> str | None:
    """The release tag HEAD sits on, or None when untagged or git is unavailable."""
    try:
        return actions.run(["git", "-C", str(repo), "describe", "--tags", "--exact-match", "HEAD"])
    except RuntimeError:
        return None


def latest_tag(repo: Path) -> str | None:
    """The newest release tag reachable from origin/main."""
    try:
        return actions.run(["git", "-C", str(repo), "describe", "--tags", "--abbrev=0", "origin/main"])
    except RuntimeError:
        return None


def contains(repo: Path, tag: str) -> bool:
    """Whether HEAD already includes the tag, so a dev tree ahead of it is not 'behind'."""
    try:
        actions.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", tag, "HEAD"])
        return True
    except RuntimeError:
        return False


def at_release(repo: Path) -> bool:
    """True only when git works and HEAD sits exactly on a release tag."""
    try:
        actions.run(["git", "-C", str(repo), "rev-parse", "-q", "--verify", "HEAD"])
    except RuntimeError:
        return False
    return exact_tag(repo) is not None


def notify(title: str, body: str) -> bool:
    """A best-effort user notification; False when this platform has no notifier."""
    if sys.platform == "darwin" and shutil.which("osascript"):
        actions.run(["osascript", "-e",
                     f"display notification {json.dumps(body)} with title {json.dumps(title)}"])
        return True
    if sys.platform.startswith("linux") and shutil.which("notify-send"):
        actions.run(["notify-send", title, body])
        return True
    return False


def check_update() -> int:
    """One notice line for the session, and one user notification a day, when a newer release exists."""
    marker = actions.STATE / "update-check.json"
    now = time.time()
    try:
        cached = {}
        if marker.exists():
            cached = json.loads(marker.read_text())
            if now - cached.get("checked", 0) < UPDATE_CHECK_PERIOD:
                if cached.get("message"):
                    print(cached["message"])
                return 0
        actions.run(["git", "-C", str(actions.REPO), "fetch", "-q", "--tags", "origin"])
        current = exact_tag(actions.REPO)
        latest = latest_tag(actions.REPO)
        message = ""
        if latest and current != latest and not contains(actions.REPO, latest):
            message = (f"agentkit {latest} available (running {current or 'an unreleased tree'}). "
                       f"Run: make -C {actions.REPO} update")
            if now - cached.get("notified", 0) > UPDATE_CHECK_PERIOD and notify(
                    "agentkit update available", message):
                cached["notified"] = now
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({"checked": now, "current": current, "latest": latest,
                                      "message": message,
                                      "notified": cached.get("notified", 0)}))
        if message:
            print(message)
    except (TypeError, ValueError, RuntimeError, OSError):
        # A session hook must stay silent when git, the network or the clone is missing.
        return 0
    return 0
