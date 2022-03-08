"""Tests configuration."""
# pylint:disable=redefined-outer-name
import asyncio
from collections.abc import Callable
from typing import AsyncGenerator

import pytest_asyncio
from aiohttp import ClientSession

from aioskybell import Skybell
from tests import EMAIL, PASSWORD


@pytest_asyncio.fixture(autouse=True)
def loop_factory() -> Callable[..., asyncio.AbstractEventLoop]:
    """Create loop."""
    return asyncio.new_event_loop


@pytest_asyncio.fixture()
async def apisession() -> AsyncGenerator:
    """Create client session."""
    async with ClientSession() as sess:
        yield sess


@pytest_asyncio.fixture()
async def client(apisession) -> AsyncGenerator:
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
