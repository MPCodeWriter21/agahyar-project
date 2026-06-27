AGENTS.md
=========

This file captures the development patterns and preferences. It is intended
for AI agents to maintain consistent behavior across sessions.

Instructions
------------

- Task implementation and closing must be in the same commit. Only separate
  them in rare cases (e.g. when a hotfix is needed before the task is fully
  done).

- Do not commit anything without asking the user for confirmation first.
  Always verify that the user is ready for the changes to be committed.

- When the user says "note this" or "note that", they mean write it to
  AGENTS.md so the instruction persists across sessions.

- Always use the latest stable version for all packages across all
  configuration files.

Documentation
-------------

- All code changes include documentation
- README is the main source of truth for build/install/usage but it is not alone!
- Use GitHub-flavored Markdown fenced code blocks (triple backticks + lang) instead of reStructuredText `.. code::` directives in Markdown files.

- Never revert/override changes made by the user without asking for confirmation.
- Always ask for clarification if the user request is ambiguous.
- Do not commit anything without running the tests first.
- Do not commit empty files or files that do not provide any value to the project.
- Every new thing needs new tests to be added and run. If you add a new feature,
  add a test for it. If you fix a bug, add a test that reproduces the bug and
  passes after the fix.

Build system
------------

- use `uv` and `pyproject.toml`
- **Python support**: 3.12+

Commit convention
------------------

When a commit is related to a task, the task ID must appear in the commit
message: `type(Task YYYYMMDD-HHmmss): message`. Commits that are not
related to any task (e.g. chore-only or trivial fixes) do not need to
reference one.

Task management (Tigo)
----------------------

Tasks are managed using [Tigo](https://github.com/MPCodeWriter21/Tigo) and
stored as `TASK.md` files under `.tigo/YYYYMMDD-HHmmss/`. Each task has:

- A title (`# title`)
- STATUS, PRIORITY, TAGS, DUE metadata
- A description with checkpoints

Changes that are significant enough to warrant a new task should be added as
a new `TASK.md` file.

Code conventions
----------------

- Tests use `pytest`
- CI runs on GitHub Actions on Python 3.12
- Docstrings use reStructuredText (Sphinx) format
- Avoid non-trivial characters (e.g. em-dash `—`, curly quotes, non-ASCII
  punctuation) in source code files — stick to ASCII
- Do not use emojis anywhere
- Stage files one by one with explicit paths (`git add file1 file2`); do NOT
  use `git add -A` or `git add .` to avoid committing unintended files

Debugging with Python code
--------------------------

Do not directly use "python -c ...". Instead, write a temporary script and name
it `_debug_{REASON_FOR_CREATION}.py`, and run it using uv:
`uv run _debug_{REASON_FOR_CREATION}.py`

One general rule to keep in mind is to avoid directly using `python` and
instead running everything python related via uv or docker.
