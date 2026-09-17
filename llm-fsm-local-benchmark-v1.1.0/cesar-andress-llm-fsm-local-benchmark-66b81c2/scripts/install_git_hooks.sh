#!/usr/bin/env bash
# Point Git at repository-managed hooks (includes Spanish language pre-commit check).
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

chmod +x .githooks/pre-commit
git config core.hooksPath .githooks

echo "Git hooks installed: core.hooksPath=.githooks"
echo "Pre-commit will reject commits when Spanish text is found in tracked files."
