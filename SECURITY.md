# Security

Report vulnerabilities through a private GitHub security advisory for this
repository. Low-severity issues can go into a regular issue.

What this repository does on your machine: `install.sh` writes symlinks and
JSON config for the supported tools, fetches the plugins declared in
`plugins/manifest.json`, and registers an optional Claude Code session hook
that runs `scripts/install.py --check-update` once a day. Code from this
repository runs when you execute the installer or `make` targets, and through
that hook; `make uninstall` removes the hook and everything else the installer
created. The installer never disables an enabled plugin, never replaces files
it does not own, and backs up every JSON file it rewrites to
`~/.local/state/agentkit/backups/`.
