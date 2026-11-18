"""Lifecycle hook for the knowledge vault, run by Claude Code, Codex, Cursor and Kiro.

Usage: vault_hook.py start|prompt|stop --tool claude|codex|cursor|kiro

Reads the tool's hook JSON on stdin and prints the response shape that tool expects:
- start: the vault brief, so every session knows the vault and its index.
- prompt: pointers to notes that match the prompt.
- stop: one reminder to file what the work taught, when real work happened since the last
  checkpoint and nothing reached the vault meanwhile.
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import vault

WORK_BYTES = 60_000
WORK_SECONDS = 20 * 60
NUDGE_GAP = 30 * 60
SESSION_TTL = 7 * 24 * 3600
NUDGE = ("Vault checkpoint: if this work produced something a future session should know, such as "
         "a decision and its reason, how something works, or a verified gotcha, file it now with the "
         "vault-capture skill. If nothing qualifies, reply only: Vault: nothing to file.")
EVENTS = {"start": "SessionStart", "prompt": "UserPromptSubmit", "stop": "Stop"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event", choices=EVENTS)
    parser.add_argument("--tool", required=True, choices=("claude", "codex", "cursor", "kiro"))
    args = parser.parse_args(argv)
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        text = respond(args.event, args.tool, payload if isinstance(payload, dict) else {})
    except Exception:  # noqa: BLE001 - a broken hook must never block or break a session
        text = None
    sys.stdout.write(render(args.event, args.tool, text))
    return 0


def respond(event: str, tool: str, payload: dict) -> str | None:
    if os.environ.get(vault.DREAM_ENV):
        return None
    path = vault.locate()
    if path is None:
        return None
    if event == "start":
        record(session_file(tool, payload), transcript_size(payload), nudged=0)
        return vault.brief(path)
    if event == "prompt":
        hits = vault.search(path, str(payload.get("prompt", "")))
        return vault.recall_context(hits) if hits else None
    return NUDGE if should_nudge(path, tool, payload) else None


def render(event: str, tool: str, text: str | None) -> str:
    if text is None:
        # Codex and Cursor read a stop hook's stdout as JSON, so a quiet stop is an empty object.
        return "{}" if event == "stop" and tool in ("codex", "cursor") else ""
    if tool == "kiro":
        return text + "\n"
    if tool == "cursor":
        return json.dumps({"followup_message" if event == "stop" else "additional_context": text})
    if tool == "codex" and event == "stop":
        return json.dumps({"decision": "block", "reason": text})
    return json.dumps({"hookSpecificOutput": {"hookEventName": EVENTS[event], "additionalContext": text}})


def session_file(tool: str, payload: dict) -> Path | None:
    session = payload.get("session_id") or payload.get("conversation_id")
    if not session:
        return None
    name = hashlib.sha256(f"{tool}:{session}".encode()).hexdigest()[:24]
    return vault.state_dir() / "sessions" / f"{name}.json"


def transcript_size(payload: dict) -> int | None:
    try:
        return Path(payload["transcript_path"]).stat().st_size if payload.get("transcript_path") else None
    except OSError:
        return None


def record(path: Path | None, size: int | None, nudged: float) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    for old in path.parent.glob("*.json"):
        if old.stat().st_mtime < now - SESSION_TTL:
            old.unlink(missing_ok=True)
    path.write_text(json.dumps({"checkpoint": now, "bytes": size or 0, "nudged": nudged}))


def should_nudge(path: Path, tool: str, payload: dict) -> bool:
    if payload.get("stop_hook_active") or payload.get("loop_count"):
        return False
    if payload.get("status", "completed") != "completed":
        return False
    state_path = session_file(tool, payload)
    if state_path is None:
        return False
    size = transcript_size(payload)
    if not state_path.is_file():
        record(state_path, size, nudged=0)
        return False
    state = json.loads(state_path.read_text())
    now = time.time()
    log = path / vault.LOG
    if log.is_file() and log.stat().st_mtime > state["checkpoint"]:
        record(state_path, size, nudged=state["nudged"])
        return False
    if now - state["nudged"] < NUDGE_GAP:
        return False
    if size is not None:
        worked = size - state["bytes"] >= WORK_BYTES
    else:
        worked = now - state["checkpoint"] >= WORK_SECONDS
    if worked:
        record(state_path, size, nudged=now)
    return worked


if __name__ == "__main__":
    raise SystemExit(main())
