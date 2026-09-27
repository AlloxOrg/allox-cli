"""Allox CLI — OpenSandbox + AIO Sandbox."""

from importlib import metadata


try:
    __version__ = metadata.version("allox-cli")
except metadata.PackageNotFoundError:
    __version__ = "0+unknown"
