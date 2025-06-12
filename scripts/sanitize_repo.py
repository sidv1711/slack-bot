#!/usr/bin/env python3
"""sanitize_repo.py

Automated helper for open-sourcing this repository safely.

Features
--------
1. Scans every text file (recursively) looking for:
   • Company-specific names/URLs (e.g. "your_company", "example.com").
   • Common secret patterns (Slack/OAuth tokens, API keys, AWS IDs, hex secrets, UUIDs, etc.).
2. Prints a color-coded report summarising potential issues.
3. Optional `--write` mode creates a sanitized copy of the repo (or edits in-place) by
   replacing sensitive matches with configurable placeholders.

Usage examples
--------------
# Dry-run scan only (default)
python scripts/sanitize_repo.py

# Scan starting from another directory
python scripts/sanitize_repo.py --root ../my_project

# Write a sanitized copy to ./sanitized_repo
python scripts/sanitize_repo.py --write --output sanitized_repo
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

# ---------------------------------------------------------------------------
# Configuration – edit these lists/placeholders to fit your organisation
# ---------------------------------------------------------------------------
COMPANY_PATTERNS: List[Tuple[re.Pattern[str], str]] = [
    # (pattern_to_find, replacement)
    (re.compile(r"your_company", re.IGNORECASE), "your_company"),
    (re.compile(r"your_company\.ai", re.IGNORECASE), "example.com"),
]

SECRET_PATTERNS: List[Tuple[re.Pattern[str], str]] = [
    # OpenAI keys  (sk- followed by 32+ base64 chars)
    (re.compile(r"sk-[A-Za-z0-9]{32,}"), "<OPENAI_KEY>"),
    # Slack tokens (xox[abprs]- style)
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]+"), "<SLACK_TOKEN>"),
    # AWS access key id
    (re.compile(r"AKIA[0-9A-Z]{16}"), "<AWS_ACCESS_KEY_ID>"),
    # 64-char hex strings – typical for PropelAuth & other API keys
    (re.compile(r"[0-9a-f]{64}"), "<HEX_SECRET>"),
    # Generic 32+ char hex secrets
    (re.compile(r"[0-9a-f]{32,}"), "<HEX_SECRET>"),
    # UUID (Cloudflare tunnel IDs, etc.)
    (re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"), "<UUID>")
]

AWS_ACCOUNT_RE = re.compile(r"\b\d{12}\b")
HOME_PATH_RE = re.compile(r"/Users/[\w-]+|C:\\Users\\[\w-]+|/home/[\w-]+", re.IGNORECASE)

TEXT_FILE_EXTS = {
    ".py", ".md", ".txt", ".yml", ".yaml", ".json", ".sql", ".env", ".toml", ".ini", ".sh", ".pl", ".cfg", ".bat", ".ps1", ".dockerfile", "Dockerfile",
}

ANSI_RED = "\033[91m"
ANSI_YELLOW = "\033[93m"
ANSI_GREEN = "\033[92m"
ANSI_RESET = "\033[0m"


def is_text_file(path: Path) -> bool:
    """Heuristic check – treat by extension or small binary read."""
    if path.suffix.lower() in TEXT_FILE_EXTS or path.name in TEXT_FILE_EXTS:
        return True
    try:
        with path.open("rb") as fh:
            chunk = fh.read(1024)
            if b"\0" in chunk:
                return False
    except Exception:
        return False
    return True


def gather_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file() and not p.match("*/.git/*"):
            if is_text_file(p):
                yield p


def apply_replacements(content: str) -> Tuple[str, List[str]]:
    """Return (new_content, list_of_issue_descriptions)."""
    issues: List[str] = []
    original = content

    # Company patterns first
    for pattern, repl in COMPANY_PATTERNS:
        if pattern.search(content):
            issues.append(f"Company reference ↦ {pattern.pattern}")
            content = pattern.sub(repl, content)

    # Secrets
    for pattern, repl in SECRET_PATTERNS:
        for _ in range(3):  # repeat to catch overlaps after substitution
            if pattern.search(content):
                issues.append(f"Secret pattern ↦ {pattern.pattern}")
                content = pattern.sub(repl, content)

    # AWS account IDs
    if AWS_ACCOUNT_RE.search(content):
        issues.append("AWS account ID detected")
        content = AWS_ACCOUNT_RE.sub("<AWS_ACCOUNT_ID>", content)

    # Home directories / user paths
    if HOME_PATH_RE.search(content):
        issues.append("User home path detected")
        content = HOME_PATH_RE.sub("<HOME>", content)

    return content, issues


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan and optionally sanitize the repository.")
    parser.add_argument("--root", default=".", help="Root directory to scan (default: .)")
    parser.add_argument("--write", action="store_true", help="Write sanitized files (in-place unless --output given)")
    parser.add_argument("--output", help="Directory to write sanitized copy (ignored if not using --write)")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        print(f"{ANSI_RED}Error: root path {root} does not exist{ANSI_RESET}")
        sys.exit(1)

    output_root = None
    if args.write:
        output_root = Path(args.output or root)
        if output_root == root:
            print(f"{ANSI_YELLOW}⚠️  In-place sanitization – make sure you have a backup or use git.{ANSI_RESET}")
        else:
            if output_root.exists():
                print(f"{ANSI_YELLOW}Output directory {output_root} exists. It will be overwritten.{ANSI_RESET}")
                shutil.rmtree(output_root)
            shutil.copytree(root, output_root, dirs_exist_ok=True)
            print(f"Created copy at {output_root}")
            root = output_root  # operate on the copy

    total_files = 0
    findings = []
    for file in gather_files(root):
        total_files += 1
        try:
            text = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # skip non-utf8

        new_text, issues = apply_replacements(text)
        if issues:
            findings.append((file, issues))
            if args.write and new_text != text:
                file.write_text(new_text, encoding="utf-8")

    # Summary
    if findings:
        print(f"\n{ANSI_RED if not args.write else ANSI_GREEN}» Found {len(findings)} file(s) with potential issues.{ANSI_RESET}\n")
        for fp, iss in findings:
            rel = relative_to_root(fp, root)
            print(f"{ANSI_YELLOW}- {rel}{ANSI_RESET}")
            for i in set(iss):
                print(f"    • {i}")
    else:
        print(f"{ANSI_GREEN}✓ No potential issues detected.{ANSI_RESET}")

    if args.write:
        print("\nSanitization completed.")
        if output_root and output_root != Path(args.root).resolve():
            print(f"Sanitized copy located at {output_root}")


if __name__ == "__main__":
    main() 