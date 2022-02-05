"""Tests for AIOSkybell."""
import pathlib

EMAIL = "test@test.com"
PASSWORD = "securepass"


def load_fixture(filename) -> str:
    """Load a fixture."""
    return (
        pathlib.Path(__file__)
        .parent.joinpath("fixtures", filename)
        .read_text(encoding="utf8")
    )
