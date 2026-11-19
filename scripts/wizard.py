"""The first-install wizard as data. `install.py --status` prints the next unanswered question, given the
answers so far, so the agent asks the user one step at a time and finishes with the flags to install with."""

from pathlib import Path

import actions
import choices


def option(value: str, label: str) -> dict:
    return {"value": value, "label": label}


def ask(step: str, question: str, options: list[dict], flag: str, free_text: bool = False,
        multiple: bool = False) -> dict:
    return {"step": step, "question": question, "options": options, "flag": flag,
            "free_text": free_text, "multiple": multiple}


def plugin_options(manifest: dict, names: set[str]) -> list[dict]:
    return [option(name, manifest[name].get("description", "")) for name in sorted(names)]


def dream_steps(dream: dict, available: dict[str, str]) -> tuple[dict | None, list[str]]:
    """The first unanswered dream question, or None with the dream flags once all are answered."""
    runner = dream.get("runner")
    if runner is None:
        found = [option(name, f"the {name} CLI") for name in sorted(available)]
        return ask("dream_tool", "Which agent should run the nightly vault dream?",
                   [*found, option("none", "no nightly dream")], "--dream"), []
    flags = ["--dream", runner]
    if runner != "none":
        if runner == "command":
            if not dream.get("command"):
                raise ValueError("--dream command needs the command itself: pass --dream-command '<command>'")
            flags += ["--dream-command", dream["command"]]
        else:
            if dream.get("model") is None:
                return ask("dream_model", "Which model should the dream use? Answer default for the CLI's own.",
                           [option("default", "the CLI's own default model")], "--dream-model", free_text=True), []
            flags += ["--dream-model", dream["model"]]
        if not dream.get("time"):
            return ask("dream_time", "At what time of day should the dream run, as 24-hour HH:MM?",
                       [option(choices.DREAM_TIME, "the default, while you sleep")], "--dream-time",
                       free_text=True), []
        flags += ["--dream-time", dream["time"]]
    choices.validate_dream(dream, available)
    return None, flags


def next_step(manifest: dict, answers: dict, foreign: list[Path], available: dict[str, str]) -> dict:
    """The next question, or {"step": "done", "run_with": flags} once every answer is known."""
    required = {name for name, entry in manifest.items() if entry.get("required")}
    names = set(manifest) - required
    flags: list[str] = []
    if answers.get("plugins"):
        selected = choices.select_plugins(manifest, answers["plugins"], persist=False) - required
        flags += ["--plugins", answers["plugins"]]
    else:
        saved = choices.stored_selection()
        selected, offered = (set(), set()) if saved is None else (saved[0] & names, saved[1])
        if unasked := names - offered:
            return ask("plugins", "Which optional plugins and features should agentkit install?",
                       plugin_options(manifest, unasked), "--plugins", multiple=True)
    if "obsidian" in selected and not (actions.STATE / "dream.json").exists():
        question, dream_flags = dream_steps(answers.get("dream") or {}, available)
        if question:
            return question
        flags += dream_flags
    unresolved = set(map(str, foreign)) - choices.kept_instruction_files(actions.STATE / "instructions.json")
    if unresolved and not answers.get("instructions"):
        return ask("instructions", "Some instruction files already hold your own text. What should agentkit do?",
                   [option("keep", "leave them as they are, without agentkit's instructions"),
                    option("append", "add agentkit's instructions below yours"),
                    option("replace", "use only agentkit's; yours are backed up first")], "--instructions")
    if unresolved:
        flags += ["--instructions", answers["instructions"]]
    return {"step": "done", "run_with": flags}
