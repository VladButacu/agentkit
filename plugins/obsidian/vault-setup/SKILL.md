---
name: vault-setup
description: Use when creating or adopting the Obsidian knowledge vault that agents share with the user, or when another vault skill cannot locate the vault.
disable-model-invocation: false
metadata:
  opencode/autoinvoke: true
---

# Vault setup

## Locate the vault

The vault is the path on the `Knowledge vault:` line of `~/.config/agentkit/AGENTS.local.md` (under `$XDG_CONFIG_HOME` when it is set). Without that line it is `~/knowledge`. A folder counts as the vault when it holds both `.obsidian/` and `AGENTS.md`. When neither location qualifies, offer to create or adopt one below.

The other vault skills follow this section.

## Create a vault

1. Agree the path with the user. Keep it outside `~/Documents`, `~/Desktop` and iCloud Drive: macOS privacy protection blocks sandboxed agents there. A non-empty folder that is not a vault calls for adoption instead.
2. Copy the contents of this skill's `vault/` folder, dotfiles included, to the path. Rename `gitignore` to `.gitignore` and create the empty folders `00 Inbox/`, `10 Notes/`, `20 Categories/`, `30 Clippings/`, `40 Daily/` and `90 System/Attachments/`.
3. Run `git init` in the vault and commit everything as `setup: create vault`.
4. Record the path in `~/.config/agentkit/AGENTS.local.md` under a `## Knowledge vault` heading as `Knowledge vault: <absolute path>`, creating the file when it is missing.
5. Hand the user the steps only they can do:
   - In Obsidian, choose **Open folder as vault** and pick the path.
   - Turn on **Settings → General → Command line interface** if `obsidian version` fails.
   - Point the Obsidian Web Clipper's note location at `30 Clippings`.
   - Open `Home.md`, also bookmarked in the Bookmarks tab. Its **Needs you** table lists what agents filed for approval.
   - Optionally install the community plugin **Homepage** (Settings → Community plugins → Browse). It opens the note named `Home` at every launch with no further setup.
   - Optionally add a private git remote. Agents push to it once it exists.

Done when `git -C <path> log --oneline` shows the setup commit and `AGENTS.local.md` names the path.

## Adopt an existing vault

1. Read the vault before changing it: its folders, `.obsidian/app.json`, and the frontmatter of a sample of notes.
2. Draft its `AGENTS.md` from `vault/AGENTS.md`, rewritten to the conventions the vault already uses. Existing notes stay where and as they are.
3. With the user's approval, write that `AGENTS.md`, add whatever of `CLAUDE.md`, `Home.md`, `00 Inbox/`, `90 System/` and `.gitignore` is missing, run `git init` if the vault has no repository, and record the path as in step 4 above.
