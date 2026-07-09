"""Command line entry point.

    python -m testloop path/to/module.py --coverage 85 --max-iters 5
"""

from __future__ import annotations

import argparse
import os
import sys

from .agent import generate_tests
from .llm import LLM


def _print_event(kind: str, i: int, msg: str) -> None:
    tag = {"act": "->", "observe": "..", "done": "**"}.get(kind, "  ")
    print(f"  [iter {i}] {tag} {msg}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="testloop",
                                description="Closed-loop pytest generator.")
    p.add_argument("target", help="Python file to generate tests for")
    p.add_argument("--coverage", type=float, default=80.0,
                   help="coverage target percent (default 80)")
    p.add_argument("--max-iters", type=int, default=5,
                   help="max generate/repair iterations (default 5)")
    p.add_argument("--timeout", type=int, default=60,
                   help="per-run test timeout in seconds (default 60)")
    p.add_argument("-o", "--out", default=None,
                   help="where to write tests (default test_<name>.py)")
    p.add_argument("--model", default="claude-sonnet-5")
    p.add_argument("--mock", action="store_true",
                   help="run without the API using scripted responses")
    args = p.parse_args(argv)

    if not os.path.isfile(args.target):
        print(f"error: no such file: {args.target}", file=sys.stderr)
        return 2

    with open(args.target) as f:
        source = f.read()

    out = args.out or f"test_{os.path.basename(args.target)}"

    print(f"testloop: {args.target}  (target {args.coverage}% cov, "
          f"max {args.max_iters} iters)")
    llm = LLM(mock=args.mock, model=args.model)
    loop = generate_tests(
        source, llm,
        coverage_target=args.coverage,
        max_iterations=args.max_iters,
        timeout=args.timeout,
        on_event=_print_event,
    )

    with open(out, "w") as f:
        f.write(loop.tests)

    status = "SUCCESS" if loop.succeeded else "INCOMPLETE"
    print(f"\n{status} after {loop.iterations} iteration(s)")
    print(f"  {loop.result.passed} passed, {loop.result.failed} failed, "
          f"{loop.result.coverage}% coverage")
    print(f"  tokens: {llm.input_tokens} in / {llm.output_tokens} out")
    print(f"  tests written to {out}")
    return 0 if loop.succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
