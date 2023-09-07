"""The exceptions used by AIOSkybell."""
from __future__ import annotations


class SkybellException(Exception):
    """Class to throw general skybell exception."""


class SkybellAuthenticationException(SkybellException):
    """Class to throw authentication exception."""
