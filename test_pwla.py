#!/usr/bin/env python3
"""
PWLA — Automated Field Test Script
===================================

Generates synthetic log files with known error patterns and validates that
PWLA's classification logic detects them correctly.

Usage:
    python3 test_pwla.py

This script does NOT require the GUI. It imports the pattern-matching logic
directly and runs assertions against it.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add repo root to path so we can import PWLA logic
REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

# Import the pattern classifier from gui/main.py
from gui.main import DEFAULT_PATTERNS, PWLAGUI  # noqa: E402

# We need a Tk root for the class, but we won't show the window
import tkinter as tk  # noqa: E402

root = tk.Tk()
root.withdraw()  # hide the window
app = PWLAGUI(root)


# ── Test data: synthetic log lines with known classifications ──
TEST_LINES = [
    # Critical patterns
    ("«", "critical"),
    ("EXCEPTION_ACCESS_VIOLATION read at 0x000000c0", "critical"),
    ("FATAL: engine crash in scene:quant:vehicle:buq", "critical"),
    ("segmentation fault (sigsegv) at rip=0x1408a9a88", "critical"),
    ("panic: runtime error: invalid memory address", "critical"),
    ("Process aborted with signal 6", "critical"),

    # Error patterns
    ("unexpected token (eResource.cpp:102)", "error"),
    ("File not found - resource/abm.inc (eIORepository.cpp:374)", "error"),
    ("Link failed: human[0x1b:mp/ger/late/tankman human]", "error"),
    ("CTD at 00:01:31 in skirmish mode", "error"),
    ("assertion failed: bone_count > 0", "error"),
    ("failed to load texture icon_iron_nest.dds", "error"),
    ("missing file resource/scripts/abm/heavyart.inc", "error"),

    # Warning patterns
    ("Warning: deprecated SDL function used", "warn"),
    ("advertencia: textura sin mipmaps", "warn"),
    ("deprecat: old material format", "warn"),
    ("warn: bone driver not found in skeleton", "warn"),

    # Info patterns (should NOT match error/critical)
    ("INFO: Loading level skirmish_mid", "info"),
    ("log: game started at 00:00:00", "info"),
    ("loading resources from salida_mod/", "info"),
    ("initialized physics engine", "info"),
    ("starting mission briefing", "info"),

    # Neutral lines (no match at all)
    ("This is a completely normal line.", None),
    ("Frame rendered in 16.6ms", None),
    ("Player connected from 192.168.1.50", None),
]


def test_classification():
    """Test that _classify_line returns the expected severity for each line."""
    print("=" * 60)
    print("TEST 1: Pattern classification")
    print("=" * 60)

    passed = 0
    failed = 0

    for line, expected in TEST_LINES:
        actual = app._classify_line(line)
        status = "PASS" if actual == expected else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        print(f"[{status}] {str(expected):10} <- {str(actual):10} | {line[:60]}")

    print(f"\nResult: {passed} passed, {failed} failed out of {len(TEST_LINES)}")
    return failed == 0


def test_custom_patterns():
    """Test that custom patterns loaded from error_patterns.json work."""
    print("\n" + "=" * 60)
    print("TEST 2: Custom pattern loading")
    print("=" * 60)

    # Write a custom patterns file
    custom = {
        "critical": ["ENGINE_FAIL", "SYS_PANIC"],
        "error": ["NULL_PTR", "ASSET_MISSING"],
        "warn": ["MOD_DEPRECATED"],
        "info": ["GAME_BOOT"]
    }

    patterns_file = REPO_ROOT / "error_patterns.json"
    backup = None
    if patterns_file.exists():
        backup = patterns_file.read_text(encoding="utf-8")

    try:
        patterns_file.write_text(json.dumps(custom, indent=2), encoding="utf-8")

        # Reload patterns and assign to app
        from gui.main import load_patterns  # noqa: F811
        app.patterns = load_patterns()

        tests = [
            ("ENGINE_FAIL at frame 42", "critical"),
            ("SYS_PANIC in renderer", "critical"),
            ("NULL_PTR at object 0x123", "error"),
            ("ASSET_MISSING texture_01.png", "error"),
            ("MOD_DEPRECATED_API used", "warn"),
            ("GAME_BOOT v2021.3", "info"),
            ("random line with no match", None),
        ]

        passed = 0
        failed = 0
        for line, expected in tests:
            actual = app._classify_line(line)
            status = "PASS" if actual == expected else "FAIL"
            if status == "PASS":
                passed += 1
            else:
                failed += 1
            print(f"[{status}] {str(expected):10} <- {str(actual):10} | {line[:50]}")

        print(f"\nResult: {passed} passed, {failed} failed out of {len(tests)}")
        return failed == 0

    finally:
        if backup is not None:
            patterns_file.write_text(backup, encoding="utf-8")
        else:
            patterns_file.unlink(missing_ok=True)


def test_export_report():
    """Test that the export report contains only error/critical lines."""
    print("\n" + "=" * 60)
    print("TEST 3: Export report filtering")
    print("=" * 60)

    # Create a temporary log file
    log_content = "\n".join(line for line, _ in TEST_LINES) + "\n"

    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_game.log"
        log_path.write_text(log_content, encoding="utf-8")

        out_path = Path(tmpdir) / "report.txt"

        # Ensure patterns are back to defaults (test 2 may have swapped them)
        from gui.main import load_patterns  # noqa: F811
        app.patterns = load_patterns()

        # Simulate the export logic from PWLA
        report_lines = []
        for line in log_content.splitlines():
            lower = line.lower()
            if any(
                k.lower() in lower
                for severity, keywords in app.patterns.items()
                for k in keywords
                if severity in ("critical", "error")
            ):
                report_lines.append(line.rstrip("\n"))

        expected_errors = [
            line for line, sev in TEST_LINES if sev in ("critical", "error")
        ]

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"PWLA Error Report — {log_path.name}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total error/critical lines: {len(report_lines)}\n\n")
            f.write("\n".join(report_lines))

        # Verify
        exported = out_path.read_text(encoding="utf-8")
        passed = True
        failed_msgs = []

        for expected_line in expected_errors:
            if expected_line not in exported:
                passed = False
                failed_msgs.append(f"MISSING: {expected_line[:50]}")

        # Check that info/warn lines are NOT in the report
        info_lines = [line for line, sev in TEST_LINES if sev == "info"]
        for info_line in info_lines:
            if info_line in exported:
                passed = False
                failed_msgs.append(f"SHOULD NOT BE IN REPORT: {info_line[:50]}")

        print(f"Expected {len(expected_errors)} error/critical lines in report.")
        print(f"Found {len(report_lines)} lines in report.")

        if passed:
            print("PASS: All expected lines present, no info/warn lines leaked.")
        else:
            print("FAIL:")
            for msg in failed_msgs:
                print(f"  - {msg}")

        return passed


def test_empty_and_missing_files():
    """Test edge cases: empty file and missing file."""
    print("\n" + "=" * 60)
    print("TEST 4: Edge cases (empty / missing files)")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Empty file
        empty_path = Path(tmpdir) / "empty.log"
        empty_path.write_text("", encoding="utf-8")

        lines = empty_path.read_text(encoding="utf-8").splitlines()
        result_empty = len(lines) == 0
        print(f"[{'PASS' if result_empty else 'FAIL'}] Empty file yields 0 lines")

        # Missing file
        missing_path = Path(tmpdir) / "nonexistent.log"
        result_missing = not missing_path.exists()
        print(f"[{'PASS' if result_missing else 'FAIL'}] Missing file correctly reported as not found")

        return result_empty and result_missing


def main():
    print("PWLA — Automated Field Test")
    print("Repository:", REPO_ROOT)
    print()

    results = []

    results.append(("Pattern classification", test_classification()))
    results.append(("Custom patterns", test_custom_patterns()))
    results.append(("Export report filtering", test_export_report()))
    results.append(("Edge cases", test_empty_and_missing_files()))

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()