#!/usr/bin/env python3
"""Audit repository text files for Spanish user-facing content."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = REPO_ROOT.parent

SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules"}
SKIP_FILES = {"validate_language.py"}
TEXT_EXTENSIONS = {
    ".md", ".txt", ".py", ".json", ".yml", ".yaml", ".sh", ".cff", ".csv", ".tex", ".bib", ".svg", ".mdc"
}

# Spanish diacritics and inverted punctuation (Unicode escapes — not Spanish prose)
SPANISH_DIACRITICS = re.compile(r"[\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1\u00bf\u00a1]", re.IGNORECASE)

SPANISH_KEYWORDS = re.compile(
    r"\b("
    r"requisito|requisitos|ejecutar|documento|metrica|experimento|"
    r"reproducibilidad|configuracion|instalacion|ejecucion|graficos|"
    r"repositorio|archivo|traducir|descripcion|verificacion|validacion|"
    r"generacion|maquina|ningun|ninguna|tambien|ademas|contiene|incluye|informe"
    r")\b",
    re.IGNORECASE,
)

ALLOWLIST_SUBSTRINGS = (
    "Spanish diacritics",
    "Spanish text",
    "Spanish natural-language",
    "Spanish findings",
    "word \"Spanish\"",
    "translation requirement",
    "non-English",
    "Remaining Spanish content",
)

# Canonical scholarly identity (see papers/promts/author_identity_standardization.md).
# Diacritics in these forms are author-name spelling, not Spanish prose.
AUTHOR_IDENTITY_ALLOWLIST = (
    "César Andrés",
    "Andrés, César",
    "Andrés, C.",
    "Andrés, C.A.",
)


def is_allowed_line(line: str) -> bool:
    if any(token in line for token in ALLOWLIST_SUBSTRINGS):
        return True
    lowered = line.lower()
    # CITATION.cff splits the canonical name across given/family fields.
    if ("family-names:" in lowered or "given-names:" in lowered) and any(
        token in line for token in ("Andrés", "César")
    ):
        return True
    if any(token in line for token in AUTHOR_IDENTITY_ALLOWLIST):
        # Allow only when the line is an author-metadata / citation identity line.
        return any(
            key in lowered
            for key in (
                "author",
                "creator",
                "family-names",
                "given-names",
                "name",
                "copyright",
                "orcid",
                "pdfauthor",
                "signature",
            )
        ) or line.strip().startswith(("César Andrés", "Andrés,"))
    return False


def should_scan(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.name in SKIP_FILES:
        return False
    if any(part in SKIP_DIRS for part in path.parts):
        return False
    return path.suffix.lower() in TEXT_EXTENSIONS


def list_tracked_files(repo_root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    paths: list[Path] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        path = repo_root / raw.decode("utf-8", errors="replace")
        if should_scan(path):
            paths.append(path)
    return sorted(paths)


def scan_paths(paths: list[Path]) -> tuple[list[str], list[tuple[str, int, str, str]]]:
    scanned: list[str] = []
    findings: list[tuple[str, int, str, str]] = []

    for path in paths:
        path_str = str(path.resolve())
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        scanned.append(path_str)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if is_allowed_line(line):
                continue
            if SPANISH_DIACRITICS.search(line):
                findings.append((path_str, lineno, "diacritic", line.strip()[:160]))
            elif SPANISH_KEYWORDS.search(line):
                findings.append((path_str, lineno, "keyword", line.strip()[:160]))
    return scanned, findings


def scan_roots(roots: list[Path]) -> tuple[list[str], list[tuple[str, int, str, str]]]:
    paths: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if should_scan(path):
                paths.append(path)
    return scan_paths(paths)


def write_report(
    report_path: Path,
    *,
    scope_label: str,
    release_version: str | None,
    scanned: list[str],
    findings: list[tuple[str, int, str, str]],
) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    version_line = f"**Release version:** `{release_version}`  \n" if release_version else ""
    verdict = "PASS" if not findings else "FAIL"

    lines = [
        "# Release Language Audit",
        "",
        f"**Date:** {timestamp}  ",
        version_line.rstrip(),
        f"**Scope:** `{scope_label}` (repository-wide)  ",
        f"**Auditor:** `scripts/validate_language.py`",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Files scanned | {len(scanned)} |",
        f"| Remaining Spanish content | {len(findings)} |",
        f"| Verdict | **{verdict}** |",
        "",
    ]

    if findings:
        lines.extend(
            [
                "## Findings",
                "",
                "| File | Line | Kind | Snippet |",
                "|------|------|------|---------|",
            ]
        )
        for path, lineno, kind, snippet in findings:
            snippet = snippet.replace("|", "\\|")
            rel = path
            try:
                rel = str(Path(path).resolve().relative_to(WORKSPACE_ROOT))
            except ValueError:
                pass
            lines.append(f"| `{rel}` | {lineno} | {kind} | {snippet} |")
        lines.append("")
    else:
        lines.extend(["## Findings", "", "No Spanish user-facing text detected.", ""])

    lines.extend(
        [
            "## Reproduce",
            "",
            "```bash",
            "python3.12 scripts/audit_release_language.sh <version>",
            "# or",
            f"python3.12 scripts/validate_language.py --scope workspace --write-report {report_path.as_posix()}",
            "```",
            "",
            "---",
            "",
            "*Generated before release. Do not publish if verdict is FAIL.*",
            "",
        ]
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scope",
        choices=("tracked", "workspace"),
        default="tracked",
        help="tracked: Git-indexed files only (default, used by pre-commit); "
        "workspace: repository plus sibling workspace paths (used before release)",
    )
    parser.add_argument(
        "--write-report",
        type=Path,
        metavar="PATH",
        help="Write a Markdown audit report to PATH (typical for release audits)",
    )
    parser.add_argument(
        "--release-version",
        metavar="VERSION",
        help="Release tag or version label recorded in the audit report",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.scope == "tracked":
        scanned, findings = scan_paths(list_tracked_files(REPO_ROOT))
        scope_label = "tracked"
    else:
        scanned, findings = scan_roots([REPO_ROOT, WORKSPACE_ROOT])
        scope_label = "workspace"

    print(f"Scope: {scope_label}")
    print(f"Scanned files: {len(scanned)}")
    print(f"Spanish findings: {len(findings)}")
    for path, lineno, kind, snippet in findings:
        print(f"{path}:{lineno} [{kind}] {snippet}")

    if args.write_report:
        report_path = args.write_report if args.write_report.is_absolute() else REPO_ROOT / args.write_report
        write_report(
            report_path,
            scope_label=scope_label,
            release_version=args.release_version,
            scanned=scanned,
            findings=findings,
        )
        print(f"Report written: {report_path}")

    if findings:
        if args.scope == "tracked":
            print("\nCommit rejected: Spanish text found in tracked files.", file=sys.stderr)
        else:
            print("\nRelease audit failed: Spanish text found in repository-wide scan.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
