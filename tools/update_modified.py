#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: update_modified.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-05-06
Modified: 2026-05-06
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: 
    Standalone header updater for Python scripts.

    - Self-contained logger (no external imports)
    - Recursively scans directories
    - Updates the 'Modified:' header line
    - Defaults to scanning the parent folder

"""

import os
import sys
import shutil
import zipfile
import platform
import argparse
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Global Constants
# ---------------------------------------------------------------------------
SUITE_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_VERSION = "1.0.0"
SCRIPT_NAME = Path(sys.argv[0]).stem

# Default scan directory (alias for suite root)
SCAN_DIR = SUITE_ROOT
AUTO_EXCLUDES = {".venv", "venv", "__pycache__", "site-packages"}

# Logging
DEFAULT_LOG_DIR = Path.home() / "logs"

# ---------------------------------------------------------------------------
# Status Codes
# ---------------------------------------------------------------------------
STATUS_OK = 0
STATUS_WARNING = 1
STATUS_CRITICAL = 2
STATUS_UNKNOWN = 3

# ---------------------------------------------------------------------------
# Python Version
# ---------------------------------------------------------------------------
def load_version() -> str:
    version_file = SUITE_ROOT / "VERSION"
    try:
        return version_file.read_text(encoding="utf-8").strip()
    except Exception:
        return "External to NMS_TOOLS Suite"

VERSION = load_version()
MIN_MAJOR = 3
MIN_MINOR = 8

# ---------------------------------------------------------------------------
# Custom Formatter
# ---------------------------------------------------------------------------
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
        sys.exit(STATUS_UNKNOWN)

# ---------------------------------------------------------------------------
# Logger Class
# ---------------------------------------------------------------------------
class Logger:
    def __init__(self, log_dir, script_path=None, max_mb=50, verbose=False):
        self.log_dir = Path(log_dir)
        self.verbose = verbose
        self.max_bytes = max_mb * 1024 * 1024
        self._warn_emitted = False

        # Determine script name automatically
        if script_path is None:
            script_path = __file__
        self.script_name = Path(script_path).stem

        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logfile = self.log_dir / f"{self.script_name}.log"

    def ts(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def write(self, message):
        try:
            with open(self.logfile, "a", encoding="utf-8") as f:
                f.write(f"{self.ts()}; {message}\n")
        except Exception as e:
            if not self._warn_emitted:
                self._warn_emitted = True
                warn = f"[WARN] Unable to write to log directory: {self.log_dir} — {e}"
                if self.verbose:
                    print(warn)

    def rotate_if_needed(self):
        if not self.logfile.exists():
            return

        if self.logfile.stat().st_size < self.max_bytes:
            return

        archive_path = self._build_archive_path()
        shutil.move(self.logfile, archive_path)
        self._compress_file(archive_path)

        with open(self.logfile, "w", encoding="utf-8") as f:
            f.write(f"{self.ts()}; [INFO] log rotated to {archive_path.name}.zip\n")

    def _build_archive_path(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.log_dir / f"{self.script_name}_{ts}.log"

    def _compress_file(self, path):
        zip_path = str(path) + ".zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(path, arcname=path.name)
        os.remove(path)

    def start_banner(self):
        self.write(f"[START] {self.script_name}.py")

    def end_banner(self):
        self.write("[END]")

# ---------------------------------------------------------------------------
# Header Update Logic
# ---------------------------------------------------------------------------
def update_header(path: Path, logger: Logger, dry_run: bool) -> bool:
    """
    Update the Modified: header only if the date is different.
    If dry_run=True, do not write changes.
    Returns True if an update *would* occur.
    """
    if path.suffix != ".py":
        return False
    try:
        text = path.read_text(encoding="utf-8").splitlines(keepends=True)
    except Exception as e:
        logger.write(f"[ERROR] Unable to read {path}: {e}")
        return False

    today = datetime.now().strftime("%Y-%m-%d")
    updated = False
    new_lines = []

    for line in text:
        if line.strip().startswith("Modified:"):
            old_date = line.split(":", 1)[1].strip()

            # Only update if the date actually changed
            if old_date != today:
                new_lines.append(f"Modified: {today}\n")
                updated = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # If nothing changed, skip
    if not updated:
        logger.write(f"[SKIP] Skipping {path}")
        return False

    # Dry-run: report but do not write
    if dry_run:
        logger.write(f"[DRYRUN] Would update: {path}")
        return True

    # Write updated file
    try:
        path.write_text("".join(new_lines), encoding="utf-8")
        logger.write(f"[INFO] Updated header: {path}")
        return True
    except Exception as e:
        logger.write(f"[ERROR] Unable to write {path}: {e}")
        return False

# ---------------------------------------------------------------------------
# Directory Walker
# ---------------------------------------------------------------------------
def scan_directory(root: Path, logger: Logger, dry_run: bool = False, excludes=None):
    if excludes is None:
        excludes = set()
    updated_count = 0
    skipped_count = 0

    for dirpath, dirs, files in os.walk(root):
        # Remove excluded directories from traversal
        dirs[:] = [d for d in dirs if d not in excludes]
        for name in files:
            if not name.endswith(".py"):
                continue

            full_path = Path(dirpath) / name
            if update_header(full_path, logger, dry_run):
                updated_count += 1
            else:
                skipped_count += 1

    return updated_count, skipped_count

# ---------------------------------------------------------------------------
# Argument Parser
# ---------------------------------------------------------------------------
def build_parser() -> argparse.Namespace:
    parser = CheckArgumentParser(
        prog=SCRIPT_NAME,
        description=(
            "Update Modified Header Tool\n\n"
            "Recursively scans Python files and updates the 'Modified:' header line."
        ),
        formatter_class=CustomFormatter,
        add_help=True,
    )

    core = parser.add_argument_group("Core Options")
    core.add_argument(
        "paths",
        nargs="*",
        help=f"Folders to scan default: {str(SCAN_DIR)}",
    )
    core.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which files would be updated without modifying them",
    )
    core.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="DIR",
        help="Directory names to exclude from scanning (can be used multiple times)",
    )

    log = parser.add_argument_group("Logging Options")
    log.add_argument(
        "-l", "--log-dir",
        dest="log_dir",
        default=str(DEFAULT_LOG_DIR),
        help="Directory to store logs",
    )
    log.add_argument(
        "--log-max-mb",
        type=int,
        default=50,
        dest="log_max_mb",
        help="Maximum log size in MB before rotation",
    )

    out = parser.add_argument_group("Output Options")
    out.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Detailed output",
    )
    out.add_argument(
        "-V", "--version",
        action="version",
        version=(
            f"NMS_TOOLS Suite Version: {VERSION}\n"
            f"{SCRIPT_NAME}: {SCRIPT_VERSION}\n"
            f"Python: {platform.python_version()}"
        ),
        help="Show script and Python version",
    )

    return parser.parse_args()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    args = build_parser()

    roots = [Path(p).resolve() for p in args.paths] if args.paths else [SCAN_DIR]
    dry_run = args.dry_run
    excludes = set(args.exclude)
    # Always exclude virtual environments
    excludes.update(AUTO_EXCLUDES)
    
    logger = Logger(
        log_dir=args.log_dir,
        max_mb=args.log_max_mb,
        verbose=args.verbose,
    )

    logger.start_banner()

    total_updated = 0
    total_skipped = 0

    for root in roots:
        logger.write(f"[INFO] Scanning: {root}")
        updated, skipped = scan_directory(root, logger, dry_run=dry_run, excludes=excludes)
        total_updated += updated
        total_skipped += skipped

    logger.write(f"[RESULT] updated={total_updated} skipped={total_skipped}")
    logger.end_banner()

    sys.exit(STATUS_OK)

if __name__ == "__main__":
    if sys.version_info < (MIN_MAJOR, MIN_MINOR):
        print(f"ERROR: Python {MIN_MAJOR}.{MIN_MINOR}+ required")
        sys.exit(STATUS_UNKNOWN)
    main()
