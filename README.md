# aioskybell

[![codecov](https://codecov.io/gh/tkdrob/aioskybell/branch/master/graph/badge.svg)](https://codecov.io/gh/tkdrob/aioskybell)
![python version](https://img.shields.io/badge/Python-3.9=><=3.12-blue.svg)
[![PyPI](https://img.shields.io/pypi/v/aioskybell)](https://pypi.org/project/aioskybell)
![Actions](https://github.com/tkdrob/aioskybell/workflows/Actions/badge.svg?branch=master)

_Python API client for Skybell Doorbells._

## Installation

```bash
python3 -m pip install aioskybell
```

## Example usage

More examples can be found in the `tests` directory.

```python
"""Example usage of aioskybell."""
import asyncio
from aioskybell import Skybell


async def async_example():
    """Example usage of aioskybell."""
    async with Skybell(username="user", password="password") as client:
        print(await client.async_initialize())

asyncio.get_event_loop().run_until_complete(async_example())
```

## Contribute

**All** contributions are welcome!

1. Fork the repository
2. Clone the repository locally and open the devcontainer or use GitHub codespaces
3. Do your changes
4. Lint the files with `make lint`
5. Ensure all tests passes with `make test`
6. Ensure 100% coverage with `make coverage`
7. Commit your work, and push it to GitHub
8. Create a PR against the `master` branch
