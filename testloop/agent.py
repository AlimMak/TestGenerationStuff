"""The closed loop: generate -> run -> observe -> repair, until green + covered.

This is the perceive/decide/act/observe loop applied to test writing. Each turn
the agent acts (writes or repairs tests), observes (runs them, reads failures
and coverage), and decides whether to stop or feed the observation back in.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import prompts
from .llm import LLM
from .runner import RunResult, run_tests


@dataclass
class LoopResult:
    tests: str
    result: RunResult
    iterations: int
    succeeded: bool
    input_tokens: int
    output_tokens: int


def generate_tests(
    source: str,
    llm: LLM,
    coverage_target: float = 80.0,
    max_iterations: int = 5,
    timeout: int = 60,
    on_event=lambda *_: None,
) -> LoopResult:
    tests = ""
    result = RunResult()

    for i in range(1, max_iterations + 1):
        if i == 1:
            on_event("act", i, "generating initial tests")
            tests = llm.complete(
                prompts.GENERATE_SYSTEM,
                prompts.GENERATE_USER.format(source=source),
            )
        else:
            on_event("act", i, "repairing tests")
            tests = llm.complete(
                prompts.REPAIR_SYSTEM,
                prompts.REPAIR_USER.format(
                    source=source,
                    tests=tests,
                    output=result.output,
                    coverage=result.coverage,
                    target=coverage_target,
                    uncovered=result.uncovered_lines,
                ),
            )

        result = run_tests(source, tests, timeout=timeout)
        on_event(
            "observe", i,
            f"{result.passed} passed, {result.failed} failed, "
            f"{result.coverage}% coverage",
        )

        done = result.all_passed and result.coverage >= coverage_target
        if done:
            on_event("done", i, "target reached")
            return LoopResult(tests, result, i, True,
                              llm.input_tokens, llm.output_tokens)

    return LoopResult(tests, result, max_iterations, False,
                      llm.input_tokens, llm.output_tokens)
