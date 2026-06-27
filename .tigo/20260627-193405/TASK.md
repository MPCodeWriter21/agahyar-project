# Fix workflow

- STATUS: OPEN
- PRIORITY: 90
- TAGS: github, workflow

Error:
```
Run uv venv
  uv venv
  uv pip install -r requirements.txt
  uv pip install -e ".[dev]"
  shell: /usr/bin/bash -e {0}
  env:
    UV_PYTHON: 3.12
    VIRTUAL_ENV: /home/runner/work/agahyar-project/agahyar-project/.venv
    UV_CACHE_DIR: /home/runner/work/_temp/setup-uv-cache
Using CPython 3.12.3 interpreter at: /usr/bin/python3.12
Creating virtual environment at: .venv
error: Failed to create virtual environment
  Caused by: A virtual environment already exists at: .venv

hint: Use the `--clear` flag or set `UV_VENV_CLEAR=1` to replace the existing virtual environment
Error: Process completed with exit code 2.
```
