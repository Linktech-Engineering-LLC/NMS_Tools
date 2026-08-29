#!/usr/bin/env python3
"""
Universal header updater for Python projects.

Behavior:
- If --path/-p is provided, scan only that project.
- If no path is provided, treat the parent folder of this script as the
  project root and scan ALL Python files beneath it.
- Supports --preview mode.
"""

import os
import sys
import argparse
from datetime import date, datetime
from pathlib import Path

# PythonTools logging
from PythonTools.log_helpers.helpers import resolve_paths, initialize_universal_logging

# ------------------------------------------------------------
# Enhanced Argparse (consistent with check_html.py)
# ------------------------------------------------------------

class CustomFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter
):
    def _get_help_string(self, action):
        help_text = action.help or ""
        if "%(default)" in help_text:
            return help_text
        if action.default in (None, False):
            return help_text
        return f"{help_text} (default: {action.default})"


class CheckArgError(Exception):
    pass


class CheckArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(f"ERROR: {message}\n")
        self.print_help()
        sys.exit(1)   # UNKNOWN not needed here; this is not a Nagios plugin


def build_parser():
    parser = CheckArgumentParser(
        prog="update_modified",
        description=(
            "Universal Python header updater.\n\n"
            "Updates 'Modified:' headers in Python files modified today.\n"
            "If --path is omitted, the parent folder of this script is treated\n"
            "as the project root and ALL Python files beneath it are scanned."
        ),
        formatter_class=CustomFormatter,
        add_help=True
    )

    parser.add_argument(
        "-p", "--path",
        help="Path to a specific project. If omitted, scan the parent folder.",
    )

    parser.add_argument(
        "--preview",
        action="store_true",
        help="Show which files WOULD be updated, but do not modify anything.",
    )

    return parser

# ------------------------------------------------------------
# Helper Functions (no side effects)
# ------------------------------------------------------------

def build_summary(updated_files: list[str], preview: bool) -> str:
    mode = "PREVIEW" if preview else "UPDATE"
    today = date.today()
    lines = [f"{mode} summary for {today}"]
    if updated_files:
        lines.append("\n=== Files updated ===")
        lines.extend(f" - {f}" for f in updated_files)
    else:
        lines.append("\nNo files updated today")
    return "\n".join(lines)


def get_new_files_today(root_path: Path) -> list[Path]:
    """Return all .py files under root_path whose mtime is today."""
    today = date.today()
    new_files = []

    for root, _, files in os.walk(root_path):
        for f in files:
            if f.endswith(".py"):
                path = Path(root) / f
                mtime = datetime.fromtimestamp(path.stat().st_mtime).date()
                if mtime == today:
                    new_files.append(path)

    return new_files


def update_file(path: Path, project_root: Path) -> str | None:
    """
    Update the Modified header in a file.
    Return relative path if updated, else None.
    """
    updated = False
    today = date.today().isoformat()
    lines = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("Modified:"):
                lines.append(f" Modified: {today}\n")
                updated = True
            else:
                lines.append(line)

    if updated:
        with path.open("w", encoding="utf-8") as f:
            f.writelines(lines)
        return str(path.relative_to(project_root))

    return None


def walk_project(project_root: Path, preview: bool) -> list[str]:
    """Walk project and update headers, return list of updated files."""
    fs_files = get_new_files_today(project_root)
    updated_files: list[str] = []

    for path in fs_files:
        rel = str(path.relative_to(project_root))
        if preview:
            updated_files.append(rel)
        else:
            result = update_file(path, project_root)
            if result:
                updated_files.append(result)

    return updated_files


# ------------------------------------------------------------
# GLOBAL LOGGER INITIALIZATION
# ------------------------------------------------------------

def init_logging_for_universal_script():
    # Resolve paths for this script
    paths = resolve_paths(__file__)
     # Universal scripts usually have no CLI args
    args = argparse.Namespace()

    # Build the context expected by initialize_universal_logging()
    context = {
        "PROJECT_NAME": "update_modified",
        "args": args,
        "paths": paths,
        "secrets": {},
    }

    logging_ctx = initialize_universal_logging(context)
    return logging_ctx["logger"]


logger = init_logging_for_universal_script()


# ------------------------------------------------------------
# Main Orchestration
# ------------------------------------------------------------

def main():
    parser = build_parser()
    args = parser.parse_args()

    # Determine project root
    if args.path:
        project_root = Path(args.path).expanduser().resolve()
        if not project_root.exists():
            print(f"Error: path does not exist: {project_root}")
            sys.exit(1)
    else:
        # Default: parent folder of this script
        project_root = Path(__file__).resolve().parent.parent

    logger.info(f"Scanning project root: {project_root}")
    print(f"Scanning project root: {project_root}, {args.preview}")

    updated_files = walk_project(project_root, args.preview)
    summary = build_summary(updated_files, args.preview)
    print(summary)
    logger.info(summary)


if __name__ == "__main__":
    main()
