"""AIOSkybell utility methods."""
from __future__ import annotations

import pickle
import random
import string
import uuid
from typing import Any

import aiofiles


async def async_save_cache(
    data: dict[str, str | dict[str, dict[str, dict[str, dict[str, str]]]]],
    filename: str,
) -> None:
    """Save cache from file."""
    async with aiofiles.open(filename, "wb") as file:
        pickled_foo = pickle.dumps(data)
        await file.write(pickled_foo)


async def async_load_cache(
    filename: str,
) -> dict[str, str | dict[str, dict[str, dict[str, dict[str, str]]]]]:
    """Load cache from file."""
    async with aiofiles.open(filename, "rb") as file:
        pickled_foo = await file.read()

    return pickle.loads(pickled_foo)


def gen_id() -> str:
    """Generate new Skybell IDs."""
    return str(uuid.uuid4())


def gen_token() -> str:
    """Generate a new Skybell token."""
    return "".join(
        random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
        for _ in range(32)
    )


def update(
    dct: dict[str, Any],
    dct_merge: dict[str, Any],
) -> dict[str, Any]:
    """Recursively merge dicts."""
    if not isinstance(dct, dict):
        return dct
    for key, value in dct_merge.items():
        if key in dct and isinstance(dct[key], dict):
            dct[key] = update(dct[key], value)
        else:
            dct[key] = value
    return dct
