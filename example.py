"""Example usage of aioskybell."""
import asyncio

from aioskybell import Skybell


async def async_example():
    """Example usage of aioskybell."""
    async with Skybell(username="user", password="password") as client:
        devices = await client.async_initialize()
        for device in devices:
            await device.async_update()
            print(device.status)


asyncio.get_event_loop().run_until_complete(async_example())
