"""Django project configuration package for the Agahyar application."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("agahyar")
except PackageNotFoundError:
    __version__ = "unknown"
