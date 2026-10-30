#!/usr/bin/env bash
# Run the Hog syntax tests and syntax compatibility checks headless, using the
# Docker/podman runner of https://github.com/SublimeText/UnitTesting.
#
# Usage: tests/run_syntax_tests.sh [UNITTESTING_DIR]
#   UNITTESTING_DIR  local clone of SublimeText/UnitTesting
#                    (default: $UNITTESTING_DIR)
set -euo pipefail

ut="${1:-${UNITTESTING_DIR:-}}"
if [[ -z "$ut" || ! -f "$ut/docker/run_tests.py" ]]; then
    echo "usage: $0 UNITTESTING_DIR  (or set UNITTESTING_DIR)" >&2
    echo "  clone it with: git clone https://github.com/SublimeText/UnitTesting" >&2
    exit 2
fi

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

# The checkout may not be named "Hog", but test headers use Packages/Hog/...
exec python3 -I "$ut/docker/run_tests.py" "$repo" --package-name Hog --no-unit-tests
