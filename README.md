# testloop

[![CI](https://github.com/AlimMak/testloop/actions/workflows/ci.yml/badge.svg)](https://github.com/AlimMak/testloop/actions)

![demo](assets/demo/.gif)

A closed-loop test generation agent. Point it at a Python file; it writes a
pytest suite, runs it in an isolated sandbox, reads the failures and coverage
gaps, repairs itself, and loops until the tests pass and hit your coverage
target (or it runs out of iterations).

## How it works

Each iteration has four steps:

1. **Generate** — the LLM writes a pytest suite for the module under test.
2. **Run** — pytest runs in a fresh temp dir subprocess with a hard timeout.
   `runner.py` parses the JUnit XML and coverage.py JSON into a `RunResult`:
   pass/fail counts, coverage percent, exact uncovered line numbers, and whether
   the module even imported successfully.
3. **Observe** — that structured data, not raw output text, is what goes back
   into the next prompt. The repair prompt receives the current tests, the pytest
   output, the coverage percentage, and the specific line numbers that were not
   hit. Each iteration is grounded in what actually executed, not in the model
   guessing what might be wrong.
4. **Repair** — the LLM returns an updated test file. The loop repeats until the
   coverage target is met, a source bug is found, or iterations are exhausted.

**Safeguards built into the loop:**

- **Best-suite tracking** — the result reported is the highest-scoring iteration
  (by coverage, then passing count), not the last one. A repair that makes things
  worse does not overwrite a good prior result.
- **Regression guard** — if a repair reduces the test count (deleting failing
  tests instead of fixing them), the loop reverts to the previous suite and
  re-prompts with an explicit rejection note. Two consecutive regressions halt
  with outcome `regressed`.
- **Collection-error handling** — "pytest could not import the module" is
  distinguished from "tests ran and failed." Import errors are flagged separately
  and fed back with a specific prefix so the model fixes the import, not the
  logic.
- **Truncation retry** — if the LLM response is cut off because it hit the token
  cap, the loop retries the same call once at twice the cap before giving up.

## Results

**Against [natsort](https://github.com/SethMMorton/natsort)** — a library the
model had not seen during training at that granularity:

- 3/3 modules processed successfully
- ~104 tests generated in total
- 95.1% average coverage across all three modules
- One module recovered from 68% to 100% coverage in a single repair round

**On testloop's own source** — two of its most complex modules:

- 80 tests generated
- ~99.7% average coverage

**Bug detection** — when a test fails because the source is wrong, testloop
reports it as a finding rather than modifying the test to accept wrong behavior.
On a rounding utility it flagged:

> "round_half_up adds 0.5 then truncates with int(), which works for positive
> values but breaks for negatives (e.g. -25.0 becomes -24.99) because int()
> truncates toward zero instead of rounding away from zero."

## Why this is not a wrapper

The interesting part is not "call a model to write tests." It is the feedback
loop: the agent acts, observes real execution results, and uses those
observations to decide what to do next. Structured `RunResult` data (pass/fail
counts, exact uncovered line numbers, timeouts) is fed back into the repair
prompt, so each iteration is grounded in what actually happened rather than in
the model guessing.

## Install

```bash
pip install -e .          # or: pipx install -e .
```

## Usage

```bash
export ANTHROPIC_API_KEY=sk-...

# Single file
testloop path/to/module.py

# Package directory (processes each public module)
testloop path/to/package/
```

Key flags:

| Flag | Default | Description |
|---|---|---|
| `--coverage N` | 80 | Minimum coverage % to consider a module done |
| `--max-iters N` | 5 | Repair iterations per module before giving up |
| `--max-files N` | — | Stop after N files in directory mode |
| `--budget-tokens N` | — | Halt the whole run after N total output tokens |
| `--max-tokens N` | 16384 | Per-call output token cap (raise if responses truncate) |
| `--out-dir DIR` | — | Write generated test files to this directory |

Offline demo with no API key (uses scripted responses):

```bash
testloop examples/example_target.py --mock
```

`python -m testloop` also works if you prefer.

## Architecture

- `runner.py` runs generated tests in a fresh temp dir inside a subprocess with
  a hard timeout, then parses structured results from pytest's built-in JUnit XML
  and coverage.py. Returns pass/fail counts, coverage percent, and the exact
  uncovered line numbers.
- `agent.py` is the loop: generate, run, observe, repair, stop on success. It
  also distinguishes "the test is wrong" from "the source has a bug": when the
  model signals a genuine defect with a `TESTLOOP_SOURCE_BUG` marker, the loop
  stops and surfaces it as a finding instead of contorting the tests to pass.
- `llm.py` wraps the Anthropic SDK, tracks token usage, and has a mock mode.
- `prompts.py` holds the generate and repair prompts (the main tuning surface).
- `cli.py` is the entry point.

## Sandboxing

Running model-generated code is the real risk in a tool like this, so isolation
is a first-class feature rather than an afterthought.

**local (default)** — a fresh temp dir plus a subprocess with a hard timeout.
That contains accidents and kills infinite loops, but the code still runs on the
host interpreter with your permissions. Fine for code you trust.

**docker (`--docker`)** — the same tests run in a throwaway container:

- `--network=none` so generated code cannot phone home or pull anything
- `--memory=512m` and `--pids-limit=128` so it cannot exhaust or fork-bomb the host
- the only host path it can see is one throwaway temp dir mounted at `/work`
- the container is named, so a timeout kills it by name; a runaway test cannot
  outlive the run
- `--rm` so nothing is left behind

Build the image once:

```bash
docker build -t testloop-sandbox .
testloop billing.py --docker --coverage 95
```

Where it still stops: the container runs as root and shares the host kernel, so
this is isolation against runaway and misbehaving code, not against a determined
attacker with a kernel exploit. Knowing exactly where your isolation ends is the
point.

## Roadmap / stretch

- Non-root container user and a read-only source mount
- Coverage-guided repair that targets specific uncovered branches, not just lines
- Multi-file / whole-repo mode
- Cost estimation from token counts
- A GitHub Action that runs the loop on new PRs
