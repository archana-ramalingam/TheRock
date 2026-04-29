#!/usr/bin/env python3
# Copyright Advanced Micro Devices, Inc.
# SPDX-License-Identifier: MIT

"""
Parse test results and report failed tests.

This script reads structured test output (JUnit XML, GTest JSON) and extracts
the list of failed tests for reporting.

Usage:
    python report_failed_tests.py --results-dir <path>

Supported formats:
- CTest JUnit XML: ctest-*.xml files (from --output-junit)
- GTest JSON: gtest-*.json files (from --gtest_output=json:)
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_junit_xml(xml_file: Path) -> list[str]:
    """Parse a JUnit XML file and extract failed test names.

    Args:
        xml_file: Path to the JUnit XML file

    Returns:
        List of failed test names
    """
    failed_tests = []

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Handle both <testsuites> and <testsuite> as root
        if root.tag == "testsuites":
            testsuites = root.findall("testsuite")
        elif root.tag == "testsuite":
            testsuites = [root]
        else:
            return failed_tests

        for testsuite in testsuites:
            suite_name = testsuite.get("name", "")
            for testcase in testsuite.findall("testcase"):
                failure = testcase.find("failure")
                error = testcase.find("error")

                if failure is not None or error is not None:
                    test_name = testcase.get("name", "unknown")
                    classname = testcase.get("classname", "")

                    # Build full test name
                    if classname and classname != suite_name:
                        full_name = f"{classname}.{test_name}"
                    elif suite_name:
                        full_name = f"{suite_name}.{test_name}"
                    else:
                        full_name = test_name

                    failed_tests.append(full_name)

    except ET.ParseError as e:
        print(f"Warning: Failed to parse {xml_file}: {e}")
    except Exception as e:
        print(f"Warning: Error reading {xml_file}: {e}")

    return failed_tests


def parse_gtest_json(json_file: Path) -> list[str]:
    """Parse a GTest JSON file and extract failed test names.

    Args:
        json_file: Path to the GTest JSON file

    Returns:
        List of failed test names
    """
    failed_tests = []

    try:
        with open(json_file) as f:
            data = json.load(f)

        # GTest JSON structure:
        # { "testsuites": [ { "name": "...", "testsuite": [ { "name": "...", "failures": [...] } ] } ] }
        for testsuite in data.get("testsuites", []):
            suite_name = testsuite.get("name", "")
            for test in testsuite.get("testsuite", []):
                # Check if test has failures
                failures = test.get("failures", [])
                if failures:
                    test_name = test.get("name", "unknown")
                    full_name = f"{suite_name}.{test_name}" if suite_name else test_name
                    failed_tests.append(full_name)

    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse {json_file}: {e}")
    except Exception as e:
        print(f"Warning: Error reading {json_file}: {e}")

    return failed_tests


def find_and_parse_results(results_dir: Path) -> list[str]:
    """Find and parse all test result files in the directory.

    Args:
        results_dir: Directory containing test result files

    Returns:
        List of all failed test names
    """
    all_failed_tests = []
    seen = set()

    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}")
        return all_failed_tests

    # Parse JUnit XML files (from ctest)
    for xml_file in results_dir.glob("ctest-*.xml"):
        print(f"Parsing: {xml_file.name}")
        failed = parse_junit_xml(xml_file)
        for test in failed:
            if test not in seen:
                seen.add(test)
                all_failed_tests.append(test)

    # Parse GTest JSON files
    for json_file in results_dir.glob("gtest-*.json"):
        print(f"Parsing: {json_file.name}")
        failed = parse_gtest_json(json_file)
        for test in failed:
            if test not in seen:
                seen.add(test)
                all_failed_tests.append(test)

    return all_failed_tests


def main():
    parser = argparse.ArgumentParser(
        description="Parse test results and report failed tests"
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        required=True,
        help="Directory containing test result files (JUnit XML, GTest JSON)",
    )

    args = parser.parse_args()

    failed_tests = find_and_parse_results(args.results_dir)

    if failed_tests:
        print(f"\n{'='*60}")
        print(f"FAILED TESTS ({len(failed_tests)}):")
        print(f"{'='*60}")
        print(json.dumps(failed_tests, indent=2))
    else:
        print("\nNo failed tests found.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
