#!/bin/sh
set -eu

repo=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
for runtime in python3 python3.15 python3.14 python3.13 python3.12 python3.11; do
    if command -v "$runtime" >/dev/null 2>&1 && "$runtime" -c 'import tomllib' 2>/dev/null; then
        exec "$runtime" "$repo/scripts/install.py" "$@"
    fi
done
echo "Python 3.11 or later is required (including its standard-library TOML reader)." >&2
exit 1
