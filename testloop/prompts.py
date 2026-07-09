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
- Output ONLY the full, updated Python test file. No fences, no commentary.
- Keep tests that already pass.
- If a test fails because the SOURCE is buggy (not the test), keep the correct
  assertion and put a comment `# SOURCE BUG:` on the line above it.
- Add new tests to exercise the uncovered lines listed below.
- Tests must stay deterministic.
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
