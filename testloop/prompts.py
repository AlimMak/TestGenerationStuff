"""Prompt templates for the generate and repair phases.

Kept in one place so they are easy to iterate on. Prompt quality is most of the
product here, so treat this file as the tuning surface.

All templates that reference the module under test use ``str.format()`` with
named placeholders.  ``module_dotted`` carries the importable dotted name (e.g.
``"target"`` in single-file mode, ``"mypkg.utils"`` in package mode).

The import instruction is defined once in :func:`_import_contract` and injected
into both GENERATE_SYSTEM and REPAIR_SYSTEM via the ``{import_contract}``
placeholder.  This prevents the two prompts from drifting apart and giving the
model contradictory import rules.
"""


def _import_contract(module_dotted: str) -> str:
    """Return the canonical import instruction for both generate and repair prompts.

    Keeping this in one place means the rules are identical in both system
    prompts — a change here applies everywhere automatically.
    """
    return (
        f"- The module under test is `{module_dotted}`.\n"
        f"  Import it by its full dotted name — NEVER just the last component:\n"
        f"      import {module_dotted}                   # correct\n"
        f"      from {module_dotted} import func, Class  # correct\n"
        f"  A bare `import {module_dotted.rsplit('.', 1)[-1]}` causes ImportError;"
        f" `{module_dotted}` is not\n"
        f"  importable as a top-level name because it lives inside a package.\n"
        f"  If an existing test file uses only the last component, fix it first."
    )


GENERATE_SYSTEM = """\
You are a precise pytest test generator.
Output rules (strict):
- Output ONLY Python code. No markdown fences, no commentary.
{import_contract}
- Cover normal cases, boundaries, and error paths (exceptions).
- Tests must be deterministic: no network, no filesystem, no randomness, no real time.
- Prefer many small focused tests over a few large ones.
"""

GENERATE_USER = """\
Source under test ({module_dotted}):

```python
{source}
```

Write a thorough pytest suite for the public functions. Output only the test code."""

REPAIR_SYSTEM = """\
You are a pytest repair and coverage engine.
Output rules (strict):
- Normally, output ONLY the full, updated Python test file. No fences, no commentary.
{import_contract}
- Keep tests that already pass.
- Add new tests to exercise the uncovered lines listed below.
- Tests must stay deterministic.
- Do NOT weaken or rewrite an assertion just to make a failing test pass.
- NEVER delete a failing test. If a test fails because the SOURCE is wrong,
  keep it and use the TESTLOOP_SOURCE_BUG marker (see below).
  Deleting or skipping tests to reduce the failure count is not acceptable.

Source bug handling:
- If a failing test exists because the SOURCE CODE is genuinely wrong, do NOT
  weaken the assertion to match the wrong behavior.
- SIGNAL THE BUG: your reply MUST begin with this marker as its very first line
  — no blank lines or other text before it:
      TESTLOOP_SOURCE_BUG: <one sentence naming the exact bug, the incorrect behavior, and the correct behavior>
  Example: TESTLOOP_SOURCE_BUG: int(value * factor + 0.5) uses integer truncation instead of round(), returning 2 for 2.5
  A `# SOURCE BUG` comment inside the test file is NOT sufficient on its own —
  the TESTLOOP_SOURCE_BUG marker on line 1 is required to surface the diagnosis.
- After the marker, output the full updated test file with the failing assertion
  kept intact and annotated `# SOURCE BUG:` on the line above it.
"""

REPAIR_USER = """\
Source ({module_dotted}):
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
