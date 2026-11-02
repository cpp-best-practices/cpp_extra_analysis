#!/usr/bin/env python3
"""Test harness for the custom static analysis checks in ``checks/``.

Layout::

    checks/<tool>/<check-name>/<check-name>.<ext>   the check itself
    checks/<tool>/<check-name>/tests/pass/*.cpp     must produce no findings
    checks/<tool>/<check-name>/tests/fail/*.cpp     must produce exactly the
                                                    findings marked with
                                                    ``// expect-finding``

Each line of a ``fail`` case that carries the ``expect-finding`` marker must be
reported by the check, and no other line may be reported.
"""

from __future__ import annotations

import argparse
import dataclasses
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CHECKS_DIR = REPO_ROOT / "checks"

EXPECT_MARKER = "expect-finding"
CXX_STANDARD = "c++20"

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_SKIPPED = 77

CLANG_QUERY_BINDING = re.compile(
    r'^(?P<file>.+?):(?P<line>\d+):(?P<column>\d+): note: "root" binds here$'
)
CPPCHECK_FINDING = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+):(?P<column>\d+): (?P<severity>\w+): (?P<message>.*) \[(?P<id>[^\]]+)\]$"
)
CPPCHECK_TEMPLATE = "{file}:{line}:{column}: {severity}: {message} [{id}]"
CPPCHECK_FAILURE_IDS = frozenset({"internalError", "syntaxError", "addonError"})


class HarnessError(Exception):
    """The analysis tool could not be run or produced unusable output."""


class ToolNotFound(HarnessError):
    """The analysis tool required by a check is not installed."""


@dataclasses.dataclass(frozen=True)
class TestCase:
    tool: str
    check_name: str
    check_file: Path
    source: Path
    should_fail: bool

    @property
    def name(self) -> str:
        kind = "fail" if self.should_fail else "pass"
        return f"{self.tool}/{self.check_name}/{kind}/{self.source.name}"


@dataclasses.dataclass(frozen=True)
class Outcome:
    case: TestCase
    passed: bool
    detail: str


def expected_finding_lines(source_text: str) -> frozenset[int]:
    return frozenset(
        number
        for number, line in enumerate(source_text.splitlines(), start=1)
        if EXPECT_MARKER in line
    )


def is_same_file(reported: str, source: Path) -> bool:
    reported_path = Path(reported)
    if not reported_path.is_absolute():
        reported_path = source.parent / reported_path
    return reported_path.exists() and os.path.samefile(reported_path, source)


def parse_clang_query_output(output: str, source: Path) -> frozenset[int]:
    matches = (CLANG_QUERY_BINDING.match(line) for line in output.splitlines())
    return frozenset(
        int(match["line"]) for match in matches if match and is_same_file(match["file"], source)
    )


def parse_cppcheck_output(output: str, source: Path, check_name: str) -> frozenset[int]:
    findings = [match for match in map(CPPCHECK_FINDING.match, output.splitlines()) if match]
    failures = [match.group(0) for match in findings if match["id"] in CPPCHECK_FAILURE_IDS]
    if failures:
        raise HarnessError("cppcheck could not analyse the file:\n" + "\n".join(failures))
    return frozenset(
        int(match["line"])
        for match in findings
        if match["id"].startswith(f"{check_name}-") and is_same_file(match["file"], source)
    )


def find_executable(environment_variable: str, base_name: str) -> str:
    configured = os.environ.get(environment_variable)
    if configured:
        return configured
    versioned = (f"{base_name}-{version}" for version in range(30, 13, -1))
    for candidate in (base_name, *versioned):
        found = shutil.which(candidate)
        if found:
            return found
    raise ToolNotFound(f"{base_name} not found; set {environment_variable} to its path")


def run_tool(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as error:
        raise ToolNotFound(f"could not run {command[0]}: {error}") from error


def run_clang_query(case: TestCase) -> frozenset[int]:
    executable = find_executable("CLANG_QUERY", "clang-query")
    result = run_tool(
        [executable, "-f", str(case.check_file), str(case.source), "--", f"-std={CXX_STANDARD}"]
    )
    if result.returncode != 0 or "error:" in result.stderr:
        raise HarnessError(f"clang-query failed ({result.returncode}):\n{result.stdout}{result.stderr}")
    return parse_clang_query_output(result.stdout, case.source)


def run_cppcheck(case: TestCase) -> frozenset[int]:
    executable = find_executable("CPPCHECK", "cppcheck")
    result = run_tool(
        [
            executable,
            f"--addon={case.check_file}",
            "--enable=warning,style,performance,portability",
            "--language=c++",
            f"--std={CXX_STANDARD}",
            "--quiet",
            f"--template={CPPCHECK_TEMPLATE}",
            str(case.source),
        ]
    )
    if result.returncode != 0:
        raise HarnessError(f"cppcheck failed ({result.returncode}):\n{result.stdout}{result.stderr}")
    return parse_cppcheck_output(result.stderr, case.source, case.check_name)


@dataclasses.dataclass(frozen=True)
class Tool:
    check_extension: str
    run: Callable[[TestCase], frozenset[int]]


TOOLS: dict[str, Tool] = {
    "clang-query": Tool(".query", run_clang_query),
    "cppcheck": Tool(".py", run_cppcheck),
}


def describe_lines(lines: Iterable[int]) -> str:
    return ", ".join(map(str, sorted(lines))) or "none"


def compare_findings(case: TestCase, expected: frozenset[int], reported: frozenset[int]) -> Outcome:
    if case.should_fail and not expected:
        return Outcome(case, False, f"fail case has no '{EXPECT_MARKER}' markers")
    if not case.should_fail and expected:
        return Outcome(case, False, f"pass case must not contain '{EXPECT_MARKER}' markers")
    if expected == reported:
        return Outcome(case, True, f"findings on lines: {describe_lines(reported)}")
    return Outcome(
        case,
        False,
        f"missing findings on lines: {describe_lines(expected - reported)}; "
        f"unexpected findings on lines: {describe_lines(reported - expected)}",
    )


def run_case(case: TestCase) -> Outcome:
    if not case.check_file.is_file():
        return Outcome(case, False, f"check implementation {case.check_file} does not exist")
    reported = TOOLS[case.tool].run(case)
    expected = expected_finding_lines(case.source.read_text(encoding="utf-8"))
    return compare_findings(case, expected, reported)


def cases_for_check(tool: str, check_dir: Path) -> list[TestCase]:
    check_file = check_dir / f"{check_dir.name}{TOOLS[tool].check_extension}"
    return [
        TestCase(tool, check_dir.name, check_file, source, should_fail)
        for should_fail, kind in ((False, "pass"), (True, "fail"))
        for source in sorted((check_dir / "tests" / kind).glob("*.cpp"))
    ]


def check_directories(checks_dir: Path) -> list[tuple[str, Path]]:
    return [
        (tool, check_dir)
        for tool in sorted(TOOLS)
        for check_dir in sorted(path for path in (checks_dir / tool).glob("*") if path.is_dir())
    ]


def require_pass_and_fail_cases(check_dir: Path, cases: Sequence[TestCase]) -> None:
    if not all(any(case.should_fail == kind for case in cases) for kind in (False, True)):
        raise HarnessError(f"{check_dir} needs at least one tests/pass and one tests/fail case")


def discover_cases(checks_dir: Path) -> list[TestCase]:
    discovered: list[TestCase] = []
    for tool, check_dir in check_directories(checks_dir):
        cases = cases_for_check(tool, check_dir)
        require_pass_and_fail_cases(check_dir, cases)
        discovered.extend(cases)
    return discovered


def case_for_source(source: Path) -> TestCase:
    resolved = source.resolve()
    kind_dir = resolved.parent
    check_dir = kind_dir.parent.parent
    tool = check_dir.parent.name
    if kind_dir.name not in ("pass", "fail") or kind_dir.parent.name != "tests" or tool not in TOOLS:
        raise HarnessError(f"{source} is not inside checks/<tool>/<check>/tests/<pass|fail>/")
    check_file = check_dir / f"{check_dir.name}{TOOLS[tool].check_extension}"
    return TestCase(tool, check_dir.name, check_file, resolved, kind_dir.name == "fail")


def run_cases(cases: Sequence[TestCase]) -> int:
    failures = 0
    skipped = 0
    for case in cases:
        try:
            outcome = run_case(case)
        except ToolNotFound as error:
            skipped += 1
            print(f"SKIP {case.name}: {error}")
            continue
        except HarnessError as error:
            outcome = Outcome(case, False, str(error))
        failures += 0 if outcome.passed else 1
        print(f"{'PASS' if outcome.passed else 'FAIL'} {case.name}: {outcome.detail}")

    print(f"\n{len(cases)} cases: {len(cases) - failures - skipped} passed, {failures} failed, {skipped} skipped")
    if failures:
        return EXIT_FAILURE
    return EXIT_SKIPPED if skipped else EXIT_SUCCESS


def parse_arguments(arguments: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--checks-dir", type=Path, default=DEFAULT_CHECKS_DIR, help="root of the checks tree")
    parser.add_argument("--tool", choices=sorted(TOOLS), help="only run checks for this tool")
    parser.add_argument("--check", help="only run the check with this name")
    parser.add_argument("--list", action="store_true", help="list the test cases instead of running them")
    parser.add_argument("cases", nargs="*", type=Path, help="individual test case sources to run")
    return parser.parse_args(arguments)


def select_cases(options: argparse.Namespace) -> list[TestCase]:
    cases = [case_for_source(source) for source in options.cases] or discover_cases(options.checks_dir)
    return [
        case
        for case in cases
        if options.tool in (None, case.tool) and options.check in (None, case.check_name)
    ]


def main(arguments: Sequence[str]) -> int:
    options = parse_arguments(arguments)
    try:
        cases = select_cases(options)
    except HarnessError as error:
        print(error, file=sys.stderr)
        return EXIT_FAILURE

    if options.list:
        print("\n".join(str(case.source) for case in cases))
        return EXIT_SUCCESS
    if not cases:
        print("no test cases found", file=sys.stderr)
        return EXIT_FAILURE
    return run_cases(cases)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
