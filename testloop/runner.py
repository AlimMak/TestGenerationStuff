"""Runs generated tests in an isolated workspace and reports structured results.

v0 isolation model: a fresh temp directory plus a subprocess with a hard
timeout. This contains accidental damage (the generated tests import only the
target module) and stops infinite loops. It does NOT defend against actively
malicious code, since generated code runs on the host interpreter. The
hardening path is a Docker sandbox with no network and a read-only mount;
see README. Being explicit about this boundary is the point, not a gap.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field


@dataclass
class RunResult:
    passed: int = 0
    failed: int = 0
    errors: int = 0
    collected: bool = True
    coverage: float = 0.0
    uncovered_lines: list[int] = field(default_factory=list)
    output: str = ""
    timed_out: bool = False

    @property
    def all_passed(self) -> bool:
        return self.collected and self.failed == 0 and self.errors == 0 and self.passed > 0


def run_tests(source_code: str, test_code: str, timeout: int = 60) -> RunResult:
    workdir = tempfile.mkdtemp(prefix="testloop_")
    cov_json = os.path.join(workdir, "cov.json")
    report_json = os.path.join(workdir, "report.json")
    try:
        with open(os.path.join(workdir, "target.py"), "w") as f:
            f.write(source_code)
        with open(os.path.join(workdir, "test_target.py"), "w") as f:
            f.write(test_code)

        cmd = [
            sys.executable, "-m", "pytest", "test_target.py",
            "--cov=target", "--cov-report", f"json:{cov_json}",
            "--json-report", f"--json-report-file={report_json}",
            "-p", "no:cacheprovider", "-q",
        ]
        try:
            proc = subprocess.run(
                cmd, cwd=workdir, capture_output=True, text=True,
                timeout=timeout,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            output = proc.stdout + proc.stderr
        except subprocess.TimeoutExpired as e:
            return RunResult(
                output=(e.stdout or "") + f"\n[timed out after {timeout}s]",
                timed_out=True, collected=False,
            )

        result = RunResult(output=output[-6000:])

        if os.path.exists(report_json):
            with open(report_json) as f:
                rep = json.load(f)
            summary = rep.get("summary", {})
            result.passed = summary.get("passed", 0)
            result.failed = summary.get("failed", 0)
            result.errors = summary.get("error", 0) + summary.get("errors", 0)
            result.collected = summary.get("collected", 0) > 0
        else:
            # pytest never produced a report: almost always a collection error
            # (syntax error in the generated tests).
            result.collected = False
            result.errors = 1

        if os.path.exists(cov_json):
            with open(cov_json) as f:
                cov = json.load(f)
            totals = cov.get("totals", {})
            result.coverage = round(totals.get("percent_covered", 0.0), 1)
            files = cov.get("files", {})
            tgt = files.get("target.py") or next(iter(files.values()), {})
            result.uncovered_lines = tgt.get("missing_lines", [])

        return result
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
