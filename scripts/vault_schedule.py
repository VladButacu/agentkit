"""Schedules the nightly vault dream with the operating system's own scheduler: a launchd agent on
macOS, a systemd user timer on Linux and a Task Scheduler task on Windows. The scheduler starts
vault_dream.py, which runs whichever agent CLI and model the user chose."""

import json
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

import actions

PLUGIN = Path("plugins/obsidian")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / PLUGIN / "scripts"))
import vault_dream

LABEL = "io.github.vladbutacu.agentkit.vault-dream"
UNIT = "agentkit-vault-dream"
TASK = "agentkit vault dream"


def available() -> dict[str, str]:
    """Each supported agent CLI found on this machine, with its executable."""
    return {name: path for name, runner in vault_dream.RUNNERS.items()
            if (path := shutil.which(runner.binary))}


def runner_config(dream: dict) -> dict:
    if dream["runner"] == "command":
        return {"runner": "command", "command": dream["command"]}
    return {"runner": dream["runner"], "model": dream.get("model"),
            "executable": available()[dream["runner"]]}


def program(config: Path) -> list[str]:
    return [str(actions.python_launcher()), str(actions.REPO / PLUGIN / "scripts/vault_dream.py"), "run", "--config", str(config)]


def search_path(config: dict) -> str:
    # Schedulers start jobs with a bare PATH; agent CLIs often need node or a version manager on it.
    first = [str(Path(config["executable"]).parent)] if config.get("executable") else []
    return os.pathsep.join(dict.fromkeys(first + os.environ.get("PATH", "").split(os.pathsep)))


def ignore_failure(argv: list[str]) -> None:
    """Unregister something that may already be gone."""
    try:
        actions.run(argv)
    except RuntimeError:
        pass


def launchd(installer: actions.Installer, config: dict, hour: int, minute: int) -> None:
    plist = actions.HOME / f"Library/LaunchAgents/{LABEL}.plist"
    logs = actions.STATE / "dream-scheduler.log"
    installer.write_text(plist, plistlib.dumps({
        "Label": LABEL, "ProgramArguments": program(actions.STATE / "dream-runner.json"),
        "StartCalendarInterval": {"Hour": hour, "Minute": minute},
        "EnvironmentVariables": {"PATH": search_path(config)},
        "StandardOutPath": str(logs), "StandardErrorPath": str(logs)}).decode())
    actions.run(["launchctl", "bootstrap", f"gui/{getattr(os, 'getuid', lambda: 0)()}", str(plist)])


def systemd(installer: actions.Installer, config: dict, hour: int, minute: int) -> None:
    units = actions.CONFIG / "systemd/user"
    command = " ".join(f'"{part}"' for part in program(actions.STATE / "dream-runner.json"))
    installer.write_text(units / f"{UNIT}.service",
                         "[Unit]\nDescription=agentkit vault dream\n\n[Service]\nType=oneshot\n"
                         f'Environment="PATH={search_path(config)}"\nExecStart={command}\n')
    installer.write_text(units / f"{UNIT}.timer",
                         "[Unit]\nDescription=Nightly agentkit vault dream\n\n[Timer]\n"
                         f"OnCalendar=*-*-* {hour:02d}:{minute:02d}:00\nPersistent=true\n\n"
                         "[Install]\nWantedBy=timers.target\n")
    actions.run(["systemctl", "--user", "daemon-reload"])
    actions.run(["systemctl", "--user", "enable", "--now", f"{UNIT}.timer"])


def task_scheduler(installer: actions.Installer, config: dict, hour: int, minute: int) -> None:
    command = subprocess.list2cmdline(program(actions.STATE / "dream-runner.json"))
    actions.run(["schtasks", "/Create", "/F", "/SC", "DAILY", "/ST", f"{hour:02d}:{minute:02d}",
                 "/TN", TASK, "/TR", command])


def unschedule(installer: actions.Installer, platform: str) -> None:
    if platform == "darwin":
        plist = actions.HOME / f"Library/LaunchAgents/{LABEL}.plist"
        ignore_failure(["launchctl", "bootout", f"gui/{getattr(os, 'getuid', lambda: 0)()}/{LABEL}"])
        if plist.exists():
            installer.remove_file(plist)
    elif platform.startswith("win"):
        ignore_failure(["schtasks", "/Delete", "/F", "/TN", TASK])
    else:
        ignore_failure(["systemctl", "--user", "disable", "--now", f"{UNIT}.timer"])
        for suffix in ("timer", "service"):
            unit = actions.CONFIG / f"systemd/user/{UNIT}.{suffix}"
            if unit.exists():
                installer.remove_file(unit)
        ignore_failure(["systemctl", "--user", "daemon-reload"])


def sync(installer: actions.Installer, dream: dict, platform: str = sys.platform) -> None:
    """Make the scheduled dream match the user's answer: installed, changed or removed."""
    record_path = actions.STATE / "dream-schedule.json"
    previous = actions.read_json(record_path) or None
    wanted = None
    if dream["runner"] != "none":
        config = runner_config(dream)
        wanted = {"platform": platform, "time": dream["time"], "config": config,
                  "program": program(actions.STATE / "dream-runner.json")}
    if wanted == previous:
        return
    if installer.dry_run:
        print(f"Schedule the vault dream: {json.dumps(wanted) if wanted else 'none'}")
        return
    if previous:
        unschedule(installer, previous["platform"])
    runner = actions.STATE / "dream-runner.json"
    if wanted is None:
        for path in (runner, record_path):
            if path.exists():
                installer.remove_file(path)
        return
    hour, minute = (int(part) for part in dream["time"].split(":"))
    installer.write_json(runner, wanted["config"])
    scheduler = launchd if platform == "darwin" else task_scheduler if platform.startswith("win") else systemd
    scheduler(installer, wanted["config"], hour, minute)
    installer.write_json(record_path, wanted)
    print(f"Scheduled the vault dream daily at {dream['time']} with {dream['runner']}")
