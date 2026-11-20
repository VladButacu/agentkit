#!/usr/bin/env python3
"""Fill a template's {{PLACEHOLDER}} values, failing on any missing or unused value.

    render_template.py list NAME                      print the placeholders NAME needs
    render_template.py render NAME --set KEY=VALUE ... --out PATH
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[2] / "templates" / "makefile-generator"
PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")


def template_path(name: str) -> Path:
    matches = sorted(TEMPLATES.glob(f"{name}.*"))
    if len(matches) != 1:
        raise ValueError(f"unknown template: {name}")
    return matches[0]


def placeholders(text: str) -> set[str]:
    return set(PLACEHOLDER.findall(text))


def render(text: str, values: dict[str, str]) -> str:
    needed = placeholders(text)
    missing = needed - values.keys()
    unused = values.keys() - needed
    if missing or unused:
        raise ValueError(f"missing: {sorted(missing)}; unused: {sorted(unused)}")
    return PLACEHOLDER.sub(lambda match: values[match.group(1)], text)


def parse_settings(pairs: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for pair in pairs:
        key, separator, value = pair.partition("=")
        if not separator or not key:
            raise ValueError(f"expected KEY=VALUE, got: {pair}")
        if key in values:
            raise ValueError(f"duplicate setting: {key}")
        values[key] = value
    return values


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    list_command = commands.add_parser("list")
    list_command.add_argument("name")
    render_command = commands.add_parser("render")
    render_command.add_argument("name")
    render_command.add_argument("--set", dest="settings", action="append", default=[], metavar="KEY=VALUE")
    render_command.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        text = template_path(args.name).read_text(encoding="utf-8")
        if args.command == "list":
            print("\n".join(sorted(placeholders(text))))
            return 0
        args.out.write_text(render(text, parse_settings(args.settings)), encoding="utf-8")
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
