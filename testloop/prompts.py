"""Prompt templates for the generate and repair phases.

Kept in one place so they are easy to iterate on. Prompt quality is most of the
product here, so treat this file as the tuning surface.
"""

GENERATE_SYSTEM = """You are a precise pytest test generator.
Output rules (strict):
- Output ONLY Python code. No markdown fences, no commentary.
- The module under test is saved as target.py; import it with `import target`.
- Cover normal cases, boundaries, and error paths (exceptions).
- Tests must be deterministic: no network, no filesystem, no randomness, no real time.
- Prefer many small focused tests over a few large ones.
"""

GENERATE_USER = """Source under test (target.py):

```python
{source}
```

Write a thorough pytest suite for the public functions. Output only the test code."""

REPAIR_SYSTEM = """You are a pytest repair and coverage engine.
Output rules (strict):
- Normally, output ONLY the full, updated Python test file. No fences, no commentary.
- Keep tests that already pass.
- Add new tests to exercise the uncovered lines listed below.
- Tests must stay deterministic.
- Do NOT weaken or rewrite an assertion just to make a failing test pass.

Source bug handling:
- If a test fails because the SOURCE CODE under test is genuinely wrong (its
  behavior is incorrect, not the test), do NOT change the test to accept the
  wrong behavior. Instead make the FIRST line of your reply exactly:
      TESTLOOP_SOURCE_BUG: <one sentence naming the bug and the correct behavior>
  Then, on the following lines, output the full test file, keeping the correct
  (failing) assertion with a `# SOURCE BUG:` comment on the line above it.
"""

REPAIR_USER = """Source (target.py):
```python
{source}
```

Current test file:
```python
{tests}
```

pytest output:
```
{output}
```

Coverage: {coverage}% (target {target}%). Uncovered source lines: {uncovered}

Return the full updated test file. Fix failures and add tests to reach the target."""
