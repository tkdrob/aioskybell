"""The exceptions used by AIOSkybell."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Skybell
    from .device import SkybellDevice


class SkybellException(Exception):
    """Class to throw general skybell exception."""

    def __init__(
        self,
        msg: Skybell | SkybellDevice | tuple,
        message: bool | str | int | tuple = "",
    ) -> None:
        """Initialize SkybellException."""
        # Call the base class constructor with the parameters it needs
        super().__init__(str(message) if msg is not None else message)


class SkybellAuthenticationException(SkybellException):
    """Class to throw authentication exception."""
