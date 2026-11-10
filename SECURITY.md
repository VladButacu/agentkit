# Security

## Reporting a vulnerability

Report a vulnerability privately through a [GitHub security advisory](https://github.com/VladButacu/agentkit/security/advisories/new), or by email to vladbutacu@gmail.com. Do not open a public issue for it.

Include what you found, how to reproduce it, and what an attacker could do with it.

## What happens next

- You get an acknowledgement within 3 working days.
- Within 10 working days you get an assessment: whether it is a vulnerability, how severe it is, and the plan to fix it.
- The fix ships in a patch release. The advisory is published with the release, crediting you unless you ask not to be named.
- Please keep the report private until the fix is released, or for 90 days after your report, whichever comes first.

Only the latest release receives security fixes.

## What agentkit does on your machine

The installer writes skill links (symlinks, or directory junctions on Windows), a marked agentkit block in the Codex and Claude Code instruction files, and JSON config for the supported tools it detects. It fetches the plugins declared in `plugins/manifest.json` and registers an optional Claude Code session hook that runs `scripts/install.py --check-update` once a day.

Code from this repository runs when you run the installer or `make` targets, and through that hook. `make uninstall` removes the hook and everything else the installer created. The installer never disables an enabled plugin, never replaces files it does not own, asks before changing an instruction file you wrote, and backs up every file it rewrites to `~/.local/state/agentkit/backups/`.
