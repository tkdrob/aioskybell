"""Tests configuration."""
# pylint:disable=redefined-outer-name
import asyncio

import pytest
from aiohttp import ClientSession

from aioskybell import Skybell
from tests import EMAIL, PASSWORD


@pytest.fixture(autouse=True)
def loop_factory():
    """Create loop."""
    return asyncio.new_event_loop


@pytest.fixture()
async def apisession():
    """Create client session."""
    async with ClientSession() as sess:
        yield sess


@pytest.fixture()
async def client(apisession):
    """Create Client."""
    async with Skybell(
        EMAIL,
        PASSWORD,
        auto_login=True,
        get_devices=True,
        login_sleep=False,
        session=apisession,
    ) as obj:
        yield obj
