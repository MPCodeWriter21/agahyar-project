"""Pytest plugin loaded early to override DB and cache settings for tests."""

import os

os.environ.setdefault("REDIS_URL", "")
