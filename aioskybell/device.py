"""The device class used by AIOSkybell."""
from __future__ import annotations

import logging
from datetime import datetime as dt
from distutils.util import strtobool
from typing import TYPE_CHECKING, cast

from . import utils as UTILS
from .exceptions import SkybellAuthenticationException, SkybellException
from .helpers import const as CONST
from .helpers import errors as ERROR

if TYPE_CHECKING:
    from . import Skybell

_LOGGER = logging.getLogger(__name__)


class SkybellDevice:  # pylint:disable=too-many-public-methods, too-many-instance-attributes
    """Class to represent each Skybell device."""

    _skybell: Skybell

    def __init__(self, device_json: dict[str, str], skybell: Skybell) -> None:
        """Set up Skybell device."""
        self._activities: list[dict[str, str]] = []
        self._avatar_json: dict[str, str] = {}
        self._device_id = device_json.get(CONST.ID, "")
        self._device_json = device_json
        self._info_json: dict[str, str | dict[str, str]] = {}
        self._settings_json: dict[str, str | int] = {}
        self._skybell = skybell
        self._type = device_json.get(CONST.TYPE, "")
        self.images: dict[str, bytes] = {}

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
        return await self._skybell.async_send_request(method="get", url=url) or []

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
            result = await self._async_avatar_request()
            if result[CONST.CREATED_AT] != self._avatar_json.get(CONST.CREATED_AT):
                self.images[CONST.AVATAR] = await self._skybell.async_send_request(
                    "get", result[CONST.URL]
                )
            self._avatar_json = result
            UTILS.update(self._avatar_json, avatar_json or {})

        if self.acl == CONST.ACLType.OWNER.value:
            if refresh or info_json or len(self._info_json) == 0:
                self._info_json = await self._async_info_request()
                UTILS.update(self._info_json, info_json or {})

        if self.acl != CONST.ACLType.READ.value:
            if refresh or settings_json or len(self._settings_json) == 0:
                self._settings_json = await self._async_settings_request()
                UTILS.update(self._settings_json, settings_json or {})

        if refresh:
            await self._async_update_activities()

    async def _async_update_activities(self) -> None:
        """Update stored activities and update caches as required."""
        activities = await self._async_activities_request()
        if self._activities:
            for act in activities:
                if act[CONST.ID] not in [x[CONST.ID] for x in self._activities]:
                    self.images[
                        CONST.ACTIVITY
                    ] = await self._skybell.async_send_request(
                        "get", act[CONST.MEDIA_URL]
                    )
        else:
            await self._async_update_events(activities=activities)
            latest = self.latest()[CONST.MEDIA_URL]
            self.images[CONST.ACTIVITY] = await self._skybell.async_send_request(
                "get", latest
            )
        self._activities = activities
        _LOGGER.debug("Device Activities Response: %s", self._activities)

        await self._async_update_events()

    async def _async_update_events(
        self, activities: list[dict[str, str]] | None = None
    ) -> None:
        """Update our cached list of latest activity events."""
        events = cast(CONST.EventType, self._skybell.dev_cache(self, CONST.EVENT)) or {}

        activities = activities or self._activities
        for activity in activities:
            event = activity[CONST.EVENT]
            created_at = activity[CONST.CREATED_AT]

            if (old := events.get(event)) and created_at < old[CONST.CREATED_AT]:
                continue

            events[event] = activity

        await self._skybell.async_update_dev_cache(self, {CONST.EVENT: events})

    def activities(self, limit: int = 1, event: str = None) -> list[dict[str, str]]:
        """Return device activity information."""
        activities = self._activities

        # Filter our activity array if requested
        if event:
            activities = list(filter(lambda act: act[CONST.EVENT] == event, activities))

        # Return the requested number
        return activities[:limit]

    def latest(self, event: str = None) -> dict[str, str]:
        """Return the latest event activity (motion or button)."""
        events = cast(CONST.EventType, self._skybell.dev_cache(self, CONST.EVENT)) or {}
        _LOGGER.debug(events)

        if event:
            return events.get(f"device:sensor:{event}", {})

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
        if key == CONST.RGB_COLOR:
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
        if self.acl == CONST.ACLType.READ.value:
            raise SkybellAuthenticationException(
                self, "Attempted setting with invalid scope"
            )
        for key, value in settings.items():
            _validate_setting(key, value)

        try:
            await self._async_settings_request(method="patch", json_data=settings)
        except SkybellException:
            _LOGGER.warning("Exception changing settings: %s", settings)

    @property
    def acl(self) -> str:
        """Get access level to device."""
        return self._device_json.get(CONST.ACL, "")

    @property
    def owner(self) -> bool:
        """Return if user has admin rights to device."""
        return self.acl == CONST.ACLType.OWNER.value

    @property
    def user_id(self) -> str:
        """Get user id that owns the device."""
        return self._device_json["user"]

    @property
    def mac(self) -> str | None:
        """Get device mac address."""
        if mac := self._info_json.get("mac"):
            return cast(str, mac)
        return None

    @property
    def serial_no(self) -> str:
        """Get device serial number."""
        return cast(str, self._info_json.get("serialNo", ""))

    @property
    def firmware_ver(self) -> str:
        """Get device firmware version."""
        return cast(str, self._info_json.get("firmwareVersion", ""))

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
    def image_url(self) -> str:
        """Get the most recent 'avatar' image."""
        return self._avatar_json.get(CONST.URL, "")

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
        return bool(
            strtobool(str(self._settings_json.get(CONST.DO_NOT_DISTURB, "false")))
        )

    @property
    def do_not_ring(self) -> bool:
        """Get if do not ring is enabled."""
        return bool(strtobool(str(self._settings_json.get(CONST.DO_NOT_RING))))

    @property
    def outdoor_chime_level(self) -> int:
        """Get devices outdoor chime level."""
        return int(self._settings_json.get(CONST.OUTDOOR_CHIME, "0"))

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
        return int(self._settings_json.get(CONST.MOTION_THRESHOLD, "0"))

    @property
    def video_profile(self) -> int:
        """Get devices video profile."""
        return int(self._settings_json.get(CONST.VIDEO_PROFILE, "0"))

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
        return int(self._settings_json.get(CONST.BRIGHTNESS, "0"))

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
        if value not in CONST.BOOL_STRINGS:
            raise SkybellException(ERROR.INVALID_SETTING_VALUE, (setting, value))

    if setting == CONST.DO_NOT_RING:
        if value not in CONST.BOOL_STRINGS:
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
