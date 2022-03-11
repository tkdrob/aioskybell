"""An asynchronous client for Skybell API.

Async spinoff of: https://github.com/MisterWil/skybellpy

Published under the MIT license - See LICENSE file for more details.

"Skybell" is a trademark owned by SkyBell Technologies, Inc, see
www.skybell.com for more information. I am in no way affiliated with Skybell.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, cast

from aiohttp import ClientConnectorError
from aiohttp.client import ClientError, ClientSession, ClientTimeout

from . import utils as UTILS
from .device import SkybellDevice
from .exceptions import SkybellAuthenticationException, SkybellException
from .helpers import const as CONST
from .helpers import errors as ERROR

_LOGGER = logging.getLogger(__name__)


class Skybell:  # pylint:disable=too-many-instance-attributes
    """Main Skybell class."""

    _close_session = False

    def __init__(  # pylint:disable=too-many-arguments
        self,
        username: str = None,
        password: str = None,
        auto_login: bool = False,
        get_devices: bool = False,
        cache_path: str = CONST.CACHE_PATH,
        disable_cache: bool = False,
        login_sleep: bool = True,
        session: ClientSession = None,
    ) -> None:
        """Initialize Skybell object."""
        self._auto_login = auto_login
        self._cache_path = cache_path
        self._devices: dict[str, SkybellDevice] = {}
        self._disable_cache = disable_cache
        self._get_devices = get_devices
        self._password = password
        if username is not None and self._cache_path == CONST.CACHE_PATH:
            self._cache_path = f"skybell_{username.replace('.', '')}.pickle"
        self._username = username
        if session is None:
            session = ClientSession()
            self._close_session = True
        self._session = session
        self._login_sleep = login_sleep
        self._user: dict[str, str] = {}

        # Create a new cache template
        self._cache: dict[str, str | dict[str, CONST.DeviceType]] = {
            CONST.APP_ID: UTILS.gen_id(),
            CONST.CLIENT_ID: UTILS.gen_id(),
            CONST.TOKEN: UTILS.gen_token(),
            CONST.ACCESS_TOKEN: "",
            CONST.DEVICES: {},
        }

    async def __aenter__(self) -> Skybell:
        """Async enter."""
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        """Async exit."""
        if self._session and self._close_session:
            await self._session.close()

    async def async_initialize(self) -> list[SkybellDevice]:
        """Initialize."""
        if not self._disable_cache:
            await self._async_load_cache()
        if (
            self._username is not None
            and self._password is not None
            and self._auto_login
        ):
            await self.async_login()
        self._user = await self.async_send_request(method="get", url=CONST.USERS_ME_URL)
        return await self.async_get_devices()

    async def async_login(self, username: str = None, password: str = None) -> bool:
        """Execute Skybell login."""
        if username is not None:
            self._username = username
        if password is not None:
            self._password = password

        if self._username is None or self._password is None:
            raise SkybellAuthenticationException(
                self, f"{ERROR.USERNAME}: {ERROR.PASSWORD}"
            )

        await self.async_update_cache({CONST.ACCESS_TOKEN: ""})

        login_data: dict[str, str | int] = {
            "username": self._username,
            "password": self._password,
            "appId": cast(str, self.cache(CONST.APP_ID)),
            CONST.TOKEN: cast(str, self.cache(CONST.TOKEN)),
        }

        response = await self.async_send_request(
            "post", CONST.LOGIN_URL, json_data=login_data, retry=False
        )

        _LOGGER.debug("Login Response: %s", response)

        await self.async_update_cache(
            {CONST.ACCESS_TOKEN: response[CONST.ACCESS_TOKEN]}
        )

        if self._login_sleep:
            _LOGGER.info("Login successful, waiting 5 seconds...")
            await asyncio.sleep(5)
        else:
            _LOGGER.info("Login successful")

        return True

    async def async_logout(self) -> bool:
        """Explicit Skybell logout."""
        if len(self.cache(CONST.ACCESS_TOKEN)) > 0:
            # No explicit logout call as it doesn't seem to matter
            # if a logout happens without registering the app which
            # we aren't currently doing.
            if self._session and self._close_session:
                await self._session.close()
            self._devices = {}

            await self.async_update_cache({CONST.ACCESS_TOKEN: ""})

        return True

    async def async_get_devices(self, refresh: bool = False) -> list[SkybellDevice]:
        """Get all devices from Skybell."""
        if refresh or len(self._devices) == 0:

            _LOGGER.info("Updating all devices...")
            response = await self.async_send_request("get", CONST.DEVICES_URL)

            _LOGGER.debug("Get Devices Response: %s", response)

            for device_json in response:
                # Attempt to reuse an existing device
                device = self._devices.get(device_json[CONST.ID])

                # No existing device, create a new one
                if device:
                    await device.async_update({device_json[CONST.ID]: device_json})
                else:
                    device = SkybellDevice(device_json, self)
                    self._devices[device.device_id] = device

        return list(self._devices.values())

    async def async_get_device(
        self, device_id: str, refresh: bool = False
    ) -> SkybellDevice:
        """Get a single device."""
        if len(self._devices) == 0:
            await self.async_get_devices()
            refresh = False

        device = self._devices.get(device_id)

        if not device:
            raise SkybellException(self, "Device not found")
        if refresh:
            await device.async_update()

        return device

    @property
    def user_id(self) -> str:
        """Return logged in user id."""
        return self._user[CONST.ID]

    @property
    def user_first_name(self) -> str:
        """Return logged in user first name."""
        return self._user["firstName"]

    @property
    def user_last_name(self) -> str:
        """Return logged in user last name."""
        return self._user["lastName"]

    async def async_send_request(  # pylint:disable=too-many-arguments
        self,
        method: str,
        url: str,
        headers: dict[str, str] = None,
        json_data: dict[str, str | int] = None,
        retry: bool = True,
    ) -> Any:
        """Send requests to Skybell."""
        if len(self.cache(CONST.ACCESS_TOKEN)) == 0 and url != CONST.LOGIN_URL:
            await self.async_login()

        headers = headers if headers else {}
        if "cloud.myskybell.com" in url:
            if len(self.cache(CONST.ACCESS_TOKEN)) > 0:
                headers["Authorization"] = f"Bearer {self.cache(CONST.ACCESS_TOKEN)}"
            headers["content-type"] = "application/json"
            headers["accept"] = "*/*"
            headers["x-skybell-app-id"] = cast(str, self.cache(CONST.APP_ID))
            headers["x-skybell-client-id"] = cast(str, self.cache(CONST.CLIENT_ID))

        _LOGGER.debug("HTTP %s %s Request with headers: %s", method, url, headers)

        try:
            response = await self._session.request(
                method=method,
                url=url,
                json=json_data,
                headers=headers,
                timeout=ClientTimeout(30),
            )
        except (ClientConnectorError, ClientError) as exc:
            _LOGGER.warning("Skybell request exception: %s", exc)

            if retry:
                await self.async_login()

                return await self.async_send_request(
                    method, url, headers, json_data, False
                )
            if "cloud.myskybell.com" in url:
                raise SkybellException(
                    self,
                    f"Request exception for '{url}' with - {exc}",
                ) from exc
            raise SkybellException(self, ("Failed getting image: %s", exc)) from exc
        if "cloud.myskybell.com" in url:
            _result = await response.json()
        else:
            _result = await response.read()
        if response.status < 400:
            return _result
        if response.status == 401:
            raise SkybellAuthenticationException(self, _result)
        raise SkybellException(self, _result)

    def cache(self, key: str) -> str | dict[str, CONST.DeviceType]:
        """Get a cached value."""
        return self._cache.get(key, "")

    async def async_update_cache(
        self, data: dict[str, str] | dict[str, dict[str, CONST.DeviceType]]
    ) -> None:
        """Update a cached value."""
        UTILS.update(self._cache, data)
        await self._async_save_cache()

    def dev_cache(
        self, device: SkybellDevice, key: str = None
    ) -> CONST.DeviceType | CONST.EventType | dict[str, str] | str | None:
        """Get a cached value for a device."""
        cache = cast(dict[str, CONST.DeviceType], self._cache.get(CONST.DEVICES, {}))
        device_cache = cache.get(device.device_id)

        if device_cache and key:
            return device_cache.get(key)

        return device_cache

    async def async_update_dev_cache(
        self, device: SkybellDevice, data: CONST.DeviceType
    ) -> None:
        """Update cached values for a device."""
        await self.async_update_cache({CONST.DEVICES: {device.device_id: data}})

    async def _async_load_cache(self) -> None:
        """Load existing cache and merge for updating if required."""
        if not self._disable_cache:
            if os.path.exists(self._cache_path):
                _LOGGER.debug("Cache found at: %s", self._cache_path)
                if os.path.getsize(self._cache_path) > 0:
                    loaded_cache = await UTILS.async_load_cache(self._cache_path)
                    UTILS.update(self._cache, loaded_cache)
                else:
                    _LOGGER.debug("Cache file is empty.  Removing it.")
                    os.remove(self._cache_path)

        await self._async_save_cache()

    async def _async_save_cache(self) -> None:
        """Trigger a cache save."""
        if not self._disable_cache:
            await UTILS.async_save_cache(self._cache, self._cache_path)
