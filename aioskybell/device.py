"""The device class used by AIOSkybell."""
from __future__ import annotations

import logging
from datetime import datetime as dt
from distutils.util import strtobool
from typing import TYPE_CHECKING, cast

from . import utils as UTILS
from .exceptions import SkybellException
from .helpers import const as CONST
from .helpers import errors as ERROR

if TYPE_CHECKING:
    from . import Skybell

_LOGGER = logging.getLogger(__name__)


class SkybellDevice:  # pylint:disable=too-many-public-methods, too-many-instance-attributes
    """Class to represent each Skybell device."""

    def __init__(self, device_json: dict[str, str], skybell: Skybell) -> None:
        """Set up Skybell device."""
        self._activities: list = []
        self._avatar_json: dict[str, str] = {}
        self._device_id = device_json.get(CONST.ID, "")
        self._device_json = device_json
        self._info_json: dict[str, str | dict[str, str]] = {}
        self._settings_json: dict[str, str | int] = {}
        self._skybell = skybell
        self._type = device_json.get(CONST.TYPE, "")

    async def _async_device_request(self) -> dict[str, str | dict[str, str]]:
        url = str.replace(CONST.DEVICE_URL, "$DEVID$", self.device_id)
        return await self._skybell.async_send_request(method="get", url=url)

    async def _async_avatar_request(self) -> dict[str, str]:
        url = str.replace(CONST.DEVICE_AVATAR_URL, "$DEVID$", self.device_id)
        return await self._skybell.async_send_request(method="get", url=url)

    async def _async_info_request(self) -> dict[str, str | dict[str, str]]:
        url = str.replace(CONST.DEVICE_INFO_URL, "$DEVID$", self.device_id)
        return await self._skybell.async_send_request(method="get", url=url)

    async def _async_settings_request(
        self, method: str = "get", json_data: dict[str, str | int] = None
    ) -> dict[str, str | int]:
        url = str.replace(CONST.DEVICE_SETTINGS_URL, "$DEVID$", self.device_id)
        return await self._skybell.async_send_request(
            method=method, url=url, json_data=json_data
        )

    async def _async_activities_request(self) -> list[dict[str, str]]:
        url = str.replace(CONST.DEVICE_ACTIVITIES_URL, "$DEVID$", self.device_id)
        return await self._skybell.async_send_request(method="get", url=url)

    async def async_update(  # pylint:disable=too-many-arguments
        self,
        device_json: dict[str, str | dict[str, str]] = None,
        info_json: dict[str, str | dict[str, str]] = None,
        settings_json: dict[str, str | int] = None,
        avatar_json: dict[str, str] = None,
        refresh: bool = True,
        get_devices: bool = False,
    ) -> None:
        """Update the internal device json data."""
        if refresh or device_json or len(self._device_json) == 0:
            if get_devices:
                device_json = await self._async_device_request()
            UTILS.update(self._device_json, device_json or {})

        if refresh or avatar_json or len(self._avatar_json) == 0:
            self._avatar_json = await self._async_avatar_request()
            UTILS.update(self._avatar_json, avatar_json or {})

        if refresh or info_json or len(self._info_json) == 0:
            self._info_json = await self._async_info_request()
            UTILS.update(self._info_json, info_json or {})

        if refresh or settings_json or len(self._settings_json) == 0:
            self._settings_json = await self._async_settings_request()
            UTILS.update(self._settings_json, settings_json or {})

        if refresh:
            await self._async_update_activities()

    async def _async_update_activities(self) -> None:
        """Update stored activities and update caches as required."""
        self._activities = await self._async_activities_request() or []
        _LOGGER.debug("Device Activities Response: %s", self._activities)

        await self._async_update_events()

    async def _async_update_events(self) -> None:
        """Update our cached list of latest activity events."""
        events = cast(CONST.EventType, self._skybell.dev_cache(self, CONST.EVENT)) or {}

        for activity in self._activities:
            event = activity.get(CONST.EVENT)
            created_at = activity.get(CONST.CREATED_AT)

            old_event = events.get(event)
            if old_event and created_at < old_event.get(CONST.CREATED_AT):
                continue

            events[event] = activity

        await self._skybell.async_update_dev_cache(self, {CONST.EVENT: events})

    def activities(self, limit: int = 1, event: str = None) -> list[dict[str, str]]:
        """Return device activity information."""
        activities = self._activities or []

        # Filter our activity array if requested
        if event:
            activities = list(filter(lambda act: act[CONST.EVENT] == event, activities))

        # Return the requested number
        return activities[:limit]

    def latest(self, event: str = None) -> dict[str, str]:
        """Return the latest event activity."""
        events = cast(CONST.EventType, self._skybell.dev_cache(self, CONST.EVENT)) or {}
        _LOGGER.debug(events)

        if event:
            return events.get(event, {})

        latest: dict[str, str] = {}
        latest_date = None
        for evt in events.values():
            date = dt.strptime(evt.get(CONST.CREATED_AT, ""), "%Y-%m-%dT%H:%M:%S.%fZ")
            if len(latest) == 0 or latest_date is None or latest_date < date:
                latest = evt
                latest_date = date
        return latest

    async def async_set_setting(
        self, key: str, value: bool | str | int | tuple[int, int, int]
    ) -> None:
        """Set attribute."""
        if key in [CONST.DO_NOT_DISTURB, CONST.DO_NOT_RING]:
            await self._async_set_setting({key: str(value)})
        if key == ("motion_sensor" or CONST.MOTION_POLICY):
            key = CONST.MOTION_POLICY
            value = bool(value)
            value = CONST.MOTION_POLICY_ON if value is True else CONST.MOTION_POLICY_OFF
            await self._async_set_setting({key: value})
        if key in [CONST.LED_COLOR, "hs_color"]:
            key = CONST.LED_COLOR
            if not isinstance(value, (list, tuple)) or not all(
                isinstance(item, int) for item in value
            ):
                raise SkybellException(self, value)

            await self._async_set_setting(
                {
                    CONST.LED_R: value[0],
                    CONST.LED_G: value[1],
                    CONST.LED_B: value[2],
                }
            )
        if key in [
            CONST.OUTDOOR_CHIME,
            CONST.MOTION_THRESHOLD,
            CONST.VIDEO_PROFILE,
            CONST.BRIGHTNESS,
            "brightness",
        ] and not isinstance(value, tuple):
            key = CONST.BRIGHTNESS if key == "brightness" else key
            await self._async_set_setting({key: int(value)})

    async def _async_set_setting(self, settings: dict[str, str | int]) -> None:
        """Validate the settings and then send the PATCH request."""
        for key, value in settings.items():
            _validate_setting(key, value)

        try:
            await self._async_settings_request(method="patch", json_data=settings)
        except SkybellException:
            _LOGGER.warning("Exception changing settings: %s", settings)

    @property
    def user_id(self) -> str:
        """Get user id that owns the device."""
        return self._device_json["user"]

    @property
    def mac(self) -> str:
        """Get device mac address."""
        return self._device_json["mac"]

    @property
    def serial_no(self) -> str:
        """Get device serial number."""
        return self._device_json["serialNo"]

    @property
    def firmware_ver(self) -> str:
        """Get device firmware version."""
        return self._device_json["firmwareVersion"]

    @property
    def name(self) -> str:
        """Get device name."""
        return self._device_json.get(CONST.NAME, "")

    @property
    def type(self) -> str:
        """Get device type."""
        return self._type

    @property
    def device_id(self) -> str:
        """Get the device id."""
        return self._device_id

    @property
    def status(self) -> str:
        """Get the generic status of a device (up/down)."""
        return self._device_json.get(CONST.STATUS, "")

    @property
    def is_up(self) -> bool:
        """Shortcut to get if the device status is up."""
        return self.status == CONST.STATUS_UP

    @property
    def location(self) -> tuple[str, str]:
        """Return lat and lng tuple."""
        location = cast(dict, self._device_json.get(CONST.LOCATION, {}))

        return (
            location.get(CONST.LOCATION_LAT, "0"),
            location.get(CONST.LOCATION_LNG, "0"),
        )

    @property
    def image(self) -> str:
        """Get the most recent 'avatar' image."""
        return self._avatar_json.get(CONST.AVATAR_URL, "")

    @property
    def activity_image(self) -> str:
        """Get the most recent activity image."""
        return self.latest().get(CONST.MEDIA_URL, "")

    @property
    def wifi_status(self) -> str:
        """Get the wifi status."""
        status = cast(dict, self._info_json.get(CONST.STATUS, {}))
        return status.get(CONST.WIFI_LINK, "")

    @property
    def wifi_ssid(self) -> str:
        """Get the wifi ssid."""
        return cast(str, self._info_json.get(CONST.WIFI_SSID, ""))

    @property
    def last_check_in(self) -> str:
        """Get last check in timestamp."""
        return cast(str, self._info_json.get(CONST.CHECK_IN, ""))

    @property
    def do_not_disturb(self) -> bool:
        """Get if do not disturb is enabled."""
        return bool(strtobool(str(self._settings_json.get(CONST.DO_NOT_DISTURB))))

    @property
    def do_not_ring(self) -> bool:
        """Get if do not ring is enabled."""
        return bool(strtobool(str(self._settings_json.get(CONST.DO_NOT_RING))))

    @property
    def outdoor_chime_level(self) -> int:
        """Get devices outdoor chime level."""
        return int(self._settings_json.get(CONST.OUTDOOR_CHIME, ""))

    @property
    def outdoor_chime(self) -> bool:
        """Get if the devices outdoor chime is enabled."""
        return self.outdoor_chime_level is not CONST.OUTDOOR_CHIME_OFF

    @property
    def motion_sensor(self) -> bool:
        """Get if the devices motion sensor is enabled."""
        return self._settings_json.get(CONST.MOTION_POLICY) == CONST.MOTION_POLICY_ON

    @property
    def motion_threshold(self) -> int:
        """Get devices motion threshold."""
        return int(self._settings_json.get(CONST.MOTION_THRESHOLD, ""))

    @property
    def video_profile(self) -> int:
        """Get devices video profile."""
        return int(self._settings_json.get(CONST.VIDEO_PROFILE, ""))

    @property
    def led_rgb(self) -> tuple[int, int, int]:
        """Get devices LED color."""
        return (
            int(self._settings_json.get(CONST.LED_R, "")),
            int(self._settings_json.get(CONST.LED_G, "")),
            int(self._settings_json.get(CONST.LED_B, "")),
        )

    @property
    def led_intensity(self) -> int:
        """Get devices LED intensity."""
        return int(self._settings_json.get(CONST.BRIGHTNESS, ""))

    @property
    def desc(self) -> str:
        """Get a short description of the device."""
        # Front Door (id: ) - skybell hd - status: up - wifi status: good
        string = f"{self.name} (id: {self.device_id}) - {self.type}"
        return f"{string} - status: {self.status} - wifi status: {self.wifi_status}"


def _validate_setting(  # pylint:disable=too-many-branches
    setting: str, value: str | int
) -> None:
    """Validate the setting and value."""
    if setting == CONST.DO_NOT_DISTURB:
        if value not in CONST.DO_NOT_DISTURB_VALUES:
            raise SkybellException(ERROR.INVALID_SETTING_VALUE, (setting, value))

    if setting == CONST.DO_NOT_RING:
        if value not in CONST.DO_NOT_RING_VALUES:
            raise SkybellException(ERROR.INVALID_SETTING_VALUE, (setting, value))

    if setting == CONST.OUTDOOR_CHIME:
        if value not in CONST.OUTDOOR_CHIME_VALUES:
            raise SkybellException(ERROR.INVALID_SETTING_VALUE, (setting, value))

    if setting == CONST.MOTION_THRESHOLD:
        if value not in CONST.MOTION_THRESHOLD_VALUES:
            raise SkybellException(ERROR.INVALID_SETTING_VALUE, (setting, value))

    if setting == CONST.VIDEO_PROFILE:
        if value not in CONST.VIDEO_PROFILE_VALUES:
            raise SkybellException(ERROR.INVALID_SETTING_VALUE, (setting, value))

    if setting in CONST.LED_COLORS:
        if not CONST.LED_VALUES[0] <= int(value) <= CONST.LED_VALUES[1]:
            raise SkybellException(ERROR.INVALID_SETTING_VALUE, (setting, value))

    if setting == CONST.BRIGHTNESS:
        if not CONST.BRIGHTNESS_VALUES[0] <= int(value) <= CONST.BRIGHTNESS_VALUES[1]:
            raise SkybellException(ERROR.INVALID_SETTING_VALUE, (setting, value))
