#!/usr/bin/env python3
# Copyright Advanced Micro Devices, Inc.
# SPDX-License-Identifier: MIT

"""
Parse CTest/GTest/Catch2 output and report failed tests.

This script reads a log file containing test output and extracts
the list of failed tests for reporting.

Usage:
    python report_failed_tests.py --log-file <path>

Supported formats:
- CTest: "The following tests FAILED: 1 - test_name (Failed)"
- GTest: "[  FAILED  ] TestSuite.TestName"
- Catch2: "FAILED:" followed by test details
"""

import argparse
import json
import re
import sys
from pathlib import Path


def parse_ctest_failures(content: str) -> list[str]:
    """Parse CTest output for failed tests.

    CTest outputs failures in the format:
        The following tests FAILED:
                  1 - test_name (Failed)
                  2 - another_test (Timeout)
    """
    failed_tests = []

    # Find the "The following tests FAILED:" section
    match = re.search(
        r"The following tests FAILED:\s*\n((?:\s+\d+\s+-\s+.+\n?)+)", content
    )
    if match:
        failures_block = match.group(1)
        # Parse each failure line: "  1 - test_name (Failed)"
        for line in failures_block.strip().split("\n"):
            test_match = re.match(r"\s*\d+\s+-\s+(.+?)\s+\(", line)
            if test_match:
                failed_tests.append(test_match.group(1).strip())

    return failed_tests


def parse_gtest_failures(content: str) -> list[str]:
    """Parse GTest output for failed tests.

    GTest outputs failures in the format:
        [  FAILED  ] TestSuite.TestName (X ms)
    Or in the summary:
        [  FAILED  ] TestSuite.TestName
    Or parameterized tests:
        [  FAILED  ] TestSuite/TestName/0 (X ms)
    """
    failed_tests = []

    # Find all "[  FAILED  ]" lines with test names
    # Match patterns like: TestSuite.TestName, TestSuite/TestName/0, etc.
    # Test names contain word chars, dots, slashes, and may end with timing info
    pattern = r"\[\s*FAILED\s*\]\s+([\w./]+)"
    matches = re.findall(pattern, content)

    # Deduplicate while preserving order
    seen = set()
    for match in matches:
        test_name = match.strip()
        # Skip numeric-only matches (these are summary counts like "2 tests")
        if test_name.isdigit():
            continue
        if test_name not in seen:
            seen.add(test_name)
            failed_tests.append(test_name)

    return failed_tests


def parse_catch2_failures(content: str) -> list[str]:
    """Parse Catch2 output for failed tests.

    Catch2 outputs failures like:
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        test case name
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        FAILED:
    """
    failed_tests = []

    # Look for FAILED: markers and try to find the test case name before it
    # Pattern: test name appears between ~~~ lines before FAILED:
    pattern = r"~{10,}\s*\n\s*(.+?)\s*\n~{10,}[^~]*?FAILED:"
    matches = re.findall(pattern, content, re.DOTALL)

    seen = set()
    for match in matches:
        test_name = match.strip()
        if test_name and test_name not in seen:
            seen.add(test_name)
            failed_tests.append(test_name)

    return failed_tests


def parse_failed_tests(log_file: Path) -> list[str]:
    """Parse a log file and extract failed tests from test output."""
    try:
        content = log_file.read_text(errors="replace")
    except Exception as e:
        print(f"Error reading {log_file}: {e}")
        return []

    failed_tests = []
    seen = set()

    def add_unique(tests: list[str]):
        for test in tests:
            if test not in seen:
                seen.add(test)
                failed_tests.append(test)

    # Parse GTest failures first (most specific)
    gtest_failures = parse_gtest_failures(content)
    add_unique(gtest_failures)

    # Parse Catch2 failures
    catch2_failures = parse_catch2_failures(content)
    add_unique(catch2_failures)

    # Parse CTest failures last
    # If we already have gtest/catch2 failures, ctest failures are just wrapper names
    ctest_failures = parse_ctest_failures(content)
    if not failed_tests:
        # Only add ctest failures if we didn't find more specific ones
        add_unique(ctest_failures)

    return failed_tests


def main():
    parser = argparse.ArgumentParser(
        description="Parse CTest/GTest/Catch2 output and report failed tests"
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        required=True,
        help="Path to log file containing test output",
    )

    args = parser.parse_args()

    if not args.log_file.exists():
        print(f"Log file not found: {args.log_file}")
        return 1

    failed_tests = parse_failed_tests(args.log_file)

    if failed_tests:
        print(f"\n{'='*60}")
        print(f"FAILED TESTS ({len(failed_tests)}):")
        print(f"{'='*60}")
        print(json.dumps(failed_tests, indent=2))
        return 0  # Don't fail the step, just report
    else:
        print("No failed tests found in log.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
