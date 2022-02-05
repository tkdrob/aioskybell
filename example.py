"""Example usage of aioskybell."""
import asyncio

from aioskybell import Skybell


async def async_example():
    """Example usage of aioskybell."""
    async with Skybell(username="user", password="password") as client:
        print(await client.async_initialize())


asyncio.get_event_loop().run_until_complete(async_example())
