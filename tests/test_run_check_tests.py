#!/usr/bin/env python3
"""Unit tests for tools/run_check_tests.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import run_check_tests as harness  # noqa: E402


def make_case(source: Path, should_fail: bool) -> harness.TestCase:
    return harness.TestCase("cppcheck", "demo", source.parent / "demo.py", source, should_fail)


class ExpectedFindingLinesTest(unittest.TestCase):
    def test_collects_marked_lines(self) -> None:
        source = "int a;\nint b = (int)1.0;// expect-finding\nint c;\n// expect-finding\n"
        self.assertEqual(harness.expected_finding_lines(source), frozenset({2, 4}))

    def test_unmarked_source_has_no_expectations(self) -> None:
        self.assertEqual(harness.expected_finding_lines("int a;\n"), frozenset())


class ParserTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.source = Path(self.directory.name) / "case.cpp"
        self.source.write_text("int a;\n", encoding="utf-8")
        self.other = Path(self.directory.name) / "header.hpp"
        self.other.write_text("int b;\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_clang_query_reports_root_bindings_in_source_only(self) -> None:
        output = "\n".join(
            [
                "Match #1:",
                f'{self.source}:3:10: note: "root" binds here',
                f'{self.source}:4:2: note: "other" binds here',
                f'{self.other}:7:1: note: "root" binds here',
                "2 matches.",
            ]
        )
        self.assertEqual(harness.parse_clang_query_output(output, self.source), frozenset({3}))

    def test_cppcheck_reports_only_findings_from_the_check(self) -> None:
        output = "\n".join(
            [
                f"{self.source}:3:29: performance: from the check [demo-rule]",
                f"{self.source}:5:1: style: built in finding [unusedFunction]",
                f"{self.other}:2:1: performance: other file [demo-rule]",
                f"{self.source}:8:1: performance: similarly named check [demo2-rule]",
            ]
        )
        self.assertEqual(harness.parse_cppcheck_output(output, self.source, "demo"), frozenset({3}))

    def test_cppcheck_addon_failure_is_an_error(self) -> None:
        output = f"{self.source}:0:0: error: Failed to execute addon 'demo' [internalError]"
        with self.assertRaises(harness.HarnessError):
            harness.parse_cppcheck_output(output, self.source, "demo")


class CompareFindingsTest(unittest.TestCase):
    source = Path("case.cpp")

    def test_pass_case_without_findings_passes(self) -> None:
        outcome = harness.compare_findings(make_case(self.source, False), frozenset(), frozenset())
        self.assertTrue(outcome.passed)

    def test_pass_case_with_findings_fails(self) -> None:
        outcome = harness.compare_findings(make_case(self.source, False), frozenset(), frozenset({2}))
        self.assertFalse(outcome.passed)

    def test_pass_case_with_markers_fails(self) -> None:
        outcome = harness.compare_findings(make_case(self.source, False), frozenset({2}), frozenset({2}))
        self.assertFalse(outcome.passed)

    def test_fail_case_with_matching_findings_passes(self) -> None:
        outcome = harness.compare_findings(make_case(self.source, True), frozenset({2, 5}), frozenset({2, 5}))
        self.assertTrue(outcome.passed)

    def test_fail_case_with_missing_finding_fails(self) -> None:
        outcome = harness.compare_findings(make_case(self.source, True), frozenset({2, 5}), frozenset({2}))
        self.assertFalse(outcome.passed)
        self.assertIn("missing findings on lines: 5", outcome.detail)

    def test_fail_case_with_unexpected_finding_fails(self) -> None:
        outcome = harness.compare_findings(make_case(self.source, True), frozenset({2}), frozenset({2, 7}))
        self.assertFalse(outcome.passed)
        self.assertIn("unexpected findings on lines: 7", outcome.detail)

    def test_fail_case_without_markers_fails(self) -> None:
        outcome = harness.compare_findings(make_case(self.source, True), frozenset(), frozenset())
        self.assertFalse(outcome.passed)


class DiscoveryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.checks_dir = Path(self.directory.name)
        self.check_dir = self.checks_dir / "clang-query" / "demo"

    def tearDown(self) -> None:
        self.directory.cleanup()

    def add_case(self, kind: str, name: str) -> Path:
        source = self.check_dir / "tests" / kind / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("int a;\n", encoding="utf-8")
        return source

    def test_discovers_multiple_pass_and_fail_cases(self) -> None:
        for kind, name in (("pass", "a.cpp"), ("pass", "b.cpp"), ("fail", "c.cpp"), ("fail", "d.cpp")):
            self.add_case(kind, name)
        cases = harness.discover_cases(self.checks_dir)
        self.assertEqual(
            [(case.source.name, case.should_fail) for case in cases],
            [("a.cpp", False), ("b.cpp", False), ("c.cpp", True), ("d.cpp", True)],
        )
        self.assertTrue(all(case.check_file == self.check_dir / "demo.query" for case in cases))

    def test_check_without_fail_case_is_rejected(self) -> None:
        self.add_case("pass", "a.cpp")
        with self.assertRaises(harness.HarnessError):
            harness.discover_cases(self.checks_dir)

    def test_check_without_pass_case_is_rejected(self) -> None:
        self.add_case("fail", "a.cpp")
        with self.assertRaises(harness.HarnessError):
            harness.discover_cases(self.checks_dir)

    def test_case_for_source_infers_tool_and_check(self) -> None:
        case = harness.case_for_source(self.add_case("fail", "a.cpp"))
        self.assertEqual((case.tool, case.check_name, case.should_fail), ("clang-query", "demo", True))

    def test_case_for_source_rejects_files_outside_the_layout(self) -> None:
        stray = self.checks_dir / "stray.cpp"
        stray.write_text("int a;\n", encoding="utf-8")
        with self.assertRaises(harness.HarnessError):
            harness.case_for_source(stray)

    def test_missing_check_implementation_fails_the_case(self) -> None:
        case = harness.case_for_source(self.add_case("pass", "a.cpp"))
        self.assertFalse(harness.run_case(case).passed)


if __name__ == "__main__":
    unittest.main()
