"""Optional features agentkit owns. Unlike the third-party plugins in plugins/manifest.json, a feature's
skills and tool wiring ship with this repository and install only when the user selects them."""

FEATURES = {
    "obsidian": {
        "folder": "features/obsidian",
        "description": "an Obsidian knowledge vault agents share with you: agentkit's vault-setup, "
                       "vault-capture, vault-recall, vault-lint, vault-prune and vault-dream",
    },
}


def entries() -> dict[str, dict]:
    """Selectable entries in the manifest's shape, keyed by name. Features never have a checkout."""
    return {name: {"feature": spec["folder"], "description": spec["description"]}
            for name, spec in FEATURES.items()}
