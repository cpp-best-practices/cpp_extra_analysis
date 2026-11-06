#!/usr/bin/env python3
"""Unit tests for the GitHub Actions workflows."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

WORKFLOWS_DIR = Path(__file__).resolve().parent.parent / ".github" / "workflows"
WORKFLOW = WORKFLOWS_DIR / "ci.yml"
VALIDATOR_JOB = "project-validator"
CHECK_TESTS_JOB = "check-tests"
ACTION_REFERENCE = re.compile(r"^\s*(?:-\s*)?uses:\s*(?P<action>[^@\s]+)@(?P<ref>\S+)", re.MULTILINE)
COMMIT_SHA = re.compile(r"[0-9a-f]{40}")
JOB_HEADER = re.compile(r"^  (?P<name>[A-Za-z0-9_-]+):\s*$")


def workflow_jobs(text: str) -> dict[str, str]:
    """Each job under `jobs:`, keyed by name, with its indented body."""
    jobs: dict[str, list[str]] = {}
    current: list[str] | None = None
    in_jobs = False
    for line in text.splitlines():
        if not line.startswith(" ") and line.strip():
            in_jobs = line.rstrip() == "jobs:"
            current = None
            continue
        header = JOB_HEADER.match(line) if in_jobs else None
        if header is not None:
            current = jobs.setdefault(header.group("name"), [])
        elif current is not None:
            current.append(line)
    return {name: "\n".join(body) for name, body in jobs.items()}


class ProjectValidatorJobTest(unittest.TestCase):
    def setUp(self) -> None:
        self.jobs = workflow_jobs(WORKFLOW.read_text(encoding="utf-8"))

    def validator_job(self) -> str:
        self.assertIn(VALIDATOR_JOB, self.jobs, f"{WORKFLOW} has no {VALIDATOR_JOB} job")
        return self.jobs[VALIDATOR_JOB]

    def test_checks_out_the_validator_main_branch(self) -> None:
        job = self.validator_job()
        self.assertRegex(job, re.compile(r"^\s+repository:\s*cpp-best-practices/project_validator\s*$", re.M))
        self.assertRegex(job, re.compile(r"^\s+ref:\s*main\s*$", re.M))

    def test_runs_the_validator_on_this_project(self) -> None:
        self.assertRegex(self.validator_job(), r"-m project_validator\b.*\$\{\{\s*github\.workspace\s*\}\}")


class CheckTestsJobTest(unittest.TestCase):
    def setUp(self) -> None:
        jobs = workflow_jobs(WORKFLOW.read_text(encoding="utf-8"))
        self.assertIn(CHECK_TESTS_JOB, jobs, f"{WORKFLOW} has no {CHECK_TESTS_JOB} job")
        self.job = jobs[CHECK_TESTS_JOB]

    def test_builds_debug_and_release_with_and_without_sanitizers(self) -> None:
        self.assertRegex(self.job, re.compile(r"^\s+build_type:\s*\[Debug, Release\]\s*$", re.MULTILINE))
        self.assertRegex(self.job, re.compile(r'^\s+sanitizers:\s*\["ON", "OFF"\]\s*$', re.MULTILINE))

    def test_treats_warnings_as_errors(self) -> None:
        self.assertIn("-DCMAKE_COMPILE_WARNING_AS_ERROR=ON", self.job)


class ActionPinningTest(unittest.TestCase):
    def test_every_action_is_pinned_to_a_commit(self) -> None:
        for workflow in sorted(WORKFLOWS_DIR.glob("*.yml")):
            for reference in ACTION_REFERENCE.finditer(workflow.read_text(encoding="utf-8")):
                with self.subTest(workflow=workflow.name, action=reference["action"]):
                    self.assertRegex(reference["ref"], COMMIT_SHA)


class WorkflowJobsTest(unittest.TestCase):
    def test_splits_jobs_by_name(self) -> None:
        text = "name: ci\njobs:\n  first:\n    runs-on: a\n  second:\n    runs-on: b\nother:\n  third:\n"
        self.assertEqual(workflow_jobs(text), {"first": "    runs-on: a", "second": "    runs-on: b"})


if __name__ == "__main__":
    unittest.main()
