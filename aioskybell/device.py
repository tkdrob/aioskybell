"""The device class used by AIOSkybell."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, cast

import aiofiles

from . import utils as UTILS
from .exceptions import SkybellAuthenticationException, SkybellException
from .helpers import const as CONST
from .helpers import errors as ERROR

from .helpers.models import (  # isort:skip
    AvatarDict,
    DeviceDict,
    EventDict,
    EventTypeDict,
    InfoDict,
    SettingsDict,
)

if TYPE_CHECKING:
    from . import Skybell

_LOGGER = logging.getLogger(__name__)


class SkybellDevice:  # pylint:disable=too-many-public-methods, too-many-instance-attributes
    """Class to represent each Skybell device."""

    _skybell: Skybell

    def __init__(self, device_json: DeviceDict, skybell: Skybell) -> None:
        """Set up Skybell device."""
        self._activities: list[EventDict] = []
        self._avatar_json = AvatarDict()
        self._device_id = device_json.get(CONST.ID, "")
        self._device_json = device_json
        self._info_json = InfoDict()
        self._settings_json = SettingsDict()
        self._skybell = skybell
        self._type = device_json.get(CONST.TYPE, "")
        self.images: dict[str, bytes | None] = {CONST.ACTIVITY: None}

    async def _async_device_request(self) -> DeviceDict:
        url = str.replace(CONST.DEVICE_URL, "$DEVID$", self.device_id)
        return await self._skybell.async_send_request(method="get", url=url)

    async def _async_avatar_request(self) -> AvatarDict:
        url = str.replace(CONST.DEVICE_AVATAR_URL, "$DEVID$", self.device_id)
        return await self._skybell.async_send_request(method="get", url=url)

    async def _async_info_request(self) -> InfoDict:
        url = str.replace(CONST.DEVICE_INFO_URL, "$DEVID$", self.device_id)
        if data := await self._skybell.async_send_request(method="get", url=url):
            data[CONST.CHECK_IN] = convert_date(data.get(CONST.CHECK_IN, ""))
        return data

    async def _async_settings_request(
        self, method: str = "get", json_data: dict[str, str | int] = None
    ) -> SettingsDict:
        url = str.replace(CONST.DEVICE_SETTINGS_URL, "$DEVID$", self.device_id)
        return await self._skybell.async_send_request(
            method=method, url=url, json_data=json_data
        )

    async def _async_activities_request(self) -> list[EventDict]:
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

        self._activities = activities
        _LOGGER.debug("Device Activities Response: %s", self._activities)

        await self._async_update_events()

        if url := self.latest().get(CONST.MEDIA_URL):
            self.images[CONST.ACTIVITY] = await self._skybell.async_send_request(
                "get", url
            )

    async def _async_update_events(
        self, activities: list[EventDict] | None = None
    ) -> None:
        """Update our cached list of latest activity events."""
        events = cast(EventTypeDict, self._skybell.dev_cache(self, CONST.EVENT)) or {}

        activities = activities or self._activities
        for activity in activities:
            event = activity[CONST.EVENT]
            created_at = activity[CONST.CREATED_AT]

            if not (old := events.get(event)) or created_at >= old[CONST.CREATED_AT]:
                events[event] = activity

        await self._skybell.async_update_dev_cache(self, {CONST.EVENT: events})

    def activities(self, limit: int = 1, event: str = None) -> list[EventDict]:
        """Return device activity information."""
        activities = self._activities

        # Filter our activity array if requested
        if event:
            activities = list(filter(lambda act: act[CONST.EVENT] == event, activities))

        # Return the requested number
        return activities[:limit]

    def latest(self, event: str = None) -> EventDict:
        """Return the latest event activity (motion or button)."""
        events = cast(EventTypeDict, self._skybell.dev_cache(self, CONST.EVENT)) or {}
        _LOGGER.debug(events)

        if event:
            if (_evt := cast(EventDict, events.get(f"device:sensor:{event}"))) is None:
                _default = {CONST.CREATED_AT: "1970-01-01T00:00:00.000Z"}
                _evt = events.get(f"application:on-{event}", _default)
            _entry = {CONST.CREATED_AT: convert_date(_evt[CONST.CREATED_AT])}
            return cast(EventDict, _evt | _entry)

        latest: EventDict = EventDict()
        latest_date = None
        for evt in events.values():
            date = convert_date(evt[CONST.CREATED_AT])
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

    async def async_get_activity_video_url(self, video: str | None = None) -> str:
        """Get activity video. Return latest if no video specified."""
        durl = str.replace(CONST.DEVICE_ACTIVITY_VIDEO_URL, "$DEVID$", self._device_id)
        act_url = str.replace(durl, "$ACTID$", video or self.latest()[CONST.ID])
        return (await self._skybell.async_send_request("get", act_url))[CONST.URL]

    async def async_download_videos(
        self,
        path: str = None,
        video: str = None,
        limit: int = 1,
        delete: bool = False,
    ) -> None:
        """Download videos to specified path."""
        _path = self._skybell._cache_path[:-7]  # pylint:disable=protected-access
        if video and (_id := [ev for ev in self._activities if video == ev[CONST.ID]]):
            return await self._async_save_video(path or _path, _id[0], delete)
        for event in self.activities(limit=limit):
            await self._async_save_video(path or _path, event, delete)

    async def _async_save_video(
        self, path: str, event: EventDict, delete: bool
    ) -> None:
        """Write video from S3 to file."""
        async with aiofiles.open(f"{path}_{event[CONST.CREATED_AT]}.mp4", "wb") as file:
            url = await self.async_get_activity_video_url(event[CONST.ID])
            await file.write(await self._skybell.async_send_request("get", url))
        if delete:
            await self.async_delete_video(event[CONST.ID])

    async def async_delete_video(self, video: str) -> None:
        """Delete video with specified activity id."""
        durl = str.replace(CONST.DEVICE_ACTIVITY_URL, "$DEVID$", self._device_id)
        act_url = str.replace(durl, "$ACTID$", video)
        await self._skybell.async_send_request("delete", act_url)

    @property
    def acl(self) -> str:
        """Get access level to device."""
        return self._device_json[CONST.ACL]

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
        return self._info_json.get("mac")

    @property
    def serial_no(self) -> str:
        """Get device serial number."""
        return self._info_json.get("serialNo", "")

    @property
    def firmware_ver(self) -> str:
        """Get device firmware version."""
        return self._info_json.get("firmwareVersion", "")

    @property
    def name(self) -> str:
        """Get device name."""
        return self._device_json[CONST.NAME]

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
        return self._device_json[CONST.STATUS]

    @property
    def is_up(self) -> bool:
        """Shortcut to get if the device status is up."""
        return self.status == CONST.STATUS_UP

    @property
    def location(self) -> tuple[str, str]:
        """Return lat and lng tuple."""
        location = self._device_json.get(CONST.LOCATION, {})

        return (
            location.get(CONST.LOCATION_LAT, "0"),
            location.get(CONST.LOCATION_LNG, "0"),
        )

    @property
    def image_url(self) -> str:
        """Get the most recent 'avatar' image."""
        return self._avatar_json[CONST.URL]

    @property
    def wifi_status(self) -> str:
        """Get the wifi status."""
        status = self._info_json.get(CONST.STATUS, {})
        return status.get(CONST.WIFI_LINK, "")

    @property
    def wifi_ssid(self) -> str:
        """Get the wifi ssid."""
        return self._info_json.get(CONST.WIFI_SSID, "")

    @property
    def last_check_in(self) -> datetime:
        """Get last check in timestamp."""
        return self._info_json.get(CONST.CHECK_IN, "")

    @property
    def do_not_disturb(self) -> bool:
        """Get if do not disturb is enabled."""
        return self._settings_json.get(CONST.DO_NOT_DISTURB) == "true"

    @property
    def do_not_ring(self) -> bool:
        """Get if do not ring is enabled."""
        return self._settings_json.get(CONST.DO_NOT_RING) == "true"

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


def convert_date(string: str) -> datetime:
    """Convert string to datetime."""
    return datetime.strptime(f"{string}+00:00", "%Y-%m-%dT%H:%M:%S.%fZ%z")
