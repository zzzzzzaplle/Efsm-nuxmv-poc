#!/usr/bin/env bash
# Mandatory pre-release gate: repository-wide English language audit.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
  echo "Usage: $0 <version>" >&2
  echo "Example: $0 v0.2.0" >&2
  exit 2
fi

if command -v python3.12 >/dev/null 2>&1; then
  PYTHON=python3.12
elif command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
else
  echo "audit_release_language: python3.12 or python3 is required" >&2
  exit 1
fi

REPORT="docs/release_language_audit_${VERSION}.md"

echo "==> Repository-wide language audit (scope=workspace)"
"$PYTHON" scripts/validate_language.py \
  --scope workspace \
  --write-report "$REPORT" \
  --release-version "$VERSION"

echo "==> Dataset and benchmark integrity"
"$PYTHON" scripts/validate_integrity.py

echo "==> Release language audit passed"
echo "    Report: $REPORT"
echo "    Commit the report before tagging $VERSION."
