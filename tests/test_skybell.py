# pylint:disable=line-too-long, protected-access, too-many-statements
"""
Test Skybell device functionality.

Tests the device initialization and attributes of the Skybell device class.
"""
import asyncio
import os
from unittest.mock import patch

import aiofiles
import pytest
from aresponses import ResponsesMockServer

from aioskybell import Skybell, exceptions
from aioskybell import utils as UTILS
from aioskybell.device import SkybellDevice
from aioskybell.helpers import const as CONST
from tests import EMAIL, PASSWORD, load_fixture


def login_response(aresponses: ResponsesMockServer) -> None:
    """Generate login response."""
    aresponses.add(
        "cloud.myskybell.com",
        "/api/v3/login/",
        "post",
        aresponses.Response(
            status=201,
            headers={"Content-Type": "application/json"},
            text=load_fixture("login.json"),
        ),
    )


def users_me(aresponses: ResponsesMockServer) -> None:
    """Generate login response."""
    aresponses.add(
        "cloud.myskybell.com",
        "/api/v3/users/me/",
        "get",
        aresponses.Response(
            status=201,
            headers={"Content-Type": "application/json"},
            text=load_fixture("me.json"),
        ),
    )


def failed_login_response(aresponses: ResponsesMockServer) -> None:
    """Generate failed login response."""
    aresponses.add(
        "cloud.myskybell.com",
        "/api/v3/login/",
        "post",
        aresponses.Response(
            status=401,
            headers={"Content-Type": "application/json"},
            text=load_fixture("403.json"),
        ),
    )


def devices_response(aresponses: ResponsesMockServer) -> None:
    """Generate devices response."""
    aresponses.add(
        "cloud.myskybell.com",
        "/api/v3/devices/",
        "get",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("devices.json"),
        ),
    )


def _device(aresponses: ResponsesMockServer) -> None:
    aresponses.add(
        "cloud.myskybell.com",
        "/api/v3/devices/012345670123456789abcdef/",
        "get",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("device-info.json"),
        ),
    )


def new_activity(aresponses: ResponsesMockServer, device: str) -> None:
    """Generate old event response."""
    aresponses.add(
        "cloud.myskybell.com",
        f"/api/v3/devices/{device}/activities/",
        "get",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("new-activity.json"),
        ),
    )


def device_info(aresponses: ResponsesMockServer) -> None:
    """Generate device info response."""
    aresponses.add(
        "cloud.myskybell.com",
        "/api/v3/devices/012345670123456789abcdef/info/",
        "get",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("device-info.json"),
        ),
    )


def device_info_forbidden(aresponses: ResponsesMockServer) -> None:
    """Generate device info response."""
    aresponses.add(
        "cloud.myskybell.com",
        "/api/v3/devices/012345670123456789abcdef/info/",
        "get",
        aresponses.Response(
            status=401,
            headers={"Content-Type": "application/json"},
            text=load_fixture("device-info-forbidden.json"),
        ),
    )


def device_avatar(aresponses: ResponsesMockServer, device: str) -> None:
    """Generate device avatar response."""
    aresponses.add(
        "cloud.myskybell.com",
        f"/api/v3/devices/{device}/avatar/",
        "get",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("device-avatar.json"),
        ),
    )


# Forbidden returns None
def device_settings(aresponses: ResponsesMockServer, device: str) -> None:
    """Generate device settings response."""
    aresponses.add(
        "cloud.myskybell.com",
        f"/api/v3/devices/{device}/settings/",
        "get",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("device-settings.json"),
        ),
    )


def device_activities(aresponses: ResponsesMockServer, device: str) -> None:
    """Generate device activities response."""
    aresponses.add(
        "cloud.myskybell.com",
        f"/api/v3/devices/{device}/activities/",
        "get",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("activities.json"),
        ),
    )


def avatar_camera_image(aresponses: ResponsesMockServer, device: str) -> None:
    """Generate avatar camera image response."""
    aresponses.add(
        "v3-production-devices-avatar.s3-us-west-2.amazonaws.com",
        f"/{device}.jpg",
        "get",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "image/jpeg"},
            body=bytes(1),
        ),
    )


def activity_camera_image(aresponses: ResponsesMockServer, device: str) -> None:
    """Generate activity camera image response."""
    aresponses.add(
        "skybell-thumbnails-stage.s3.amazonaws.com",
        f"/{device}/1646859244793-951{device}_{device}.jpeg",
        "get",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "image/jpeg"},
            body=bytes(1),
        ),
    )


def new_activity_camera_image(aresponses: ResponsesMockServer, device: str) -> None:
    """Generate activity camera image response."""
    aresponses.add(
        "skybell-thumbnails-stage.s3.amazonaws.com",
        f"/{device}/1646859244794-951{device}_{device}.jpeg",
        "get",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "image/jpeg"},
            body=bytes(2),
        ),
        match_querystring=True,
    )


@pytest.mark.asyncio
async def test_loop() -> None:
    """Test loop usage is handled correctly."""
    async with Skybell(EMAIL, PASSWORD) as skybell:
        assert isinstance(skybell, Skybell)


@pytest.mark.asyncio
async def test_async_initialize_and_logout(aresponses: ResponsesMockServer) -> None:
    """Test initializing and logout."""
    client = Skybell(
        EMAIL, PASSWORD, auto_login=True, get_devices=True, login_sleep=False
    )
    login_response(aresponses)
    devices_response(aresponses)
    users_me(aresponses)
    data = await client.async_initialize()
    assert client._cache_path == "skybell_test@testcom.pickle"
    assert client.user_id == "1234567890abcdef12345678"
    assert client.user_first_name == "First"
    assert client.user_last_name == "Last"
    assert isinstance(data[0], SkybellDevice)
    assert client._cache["access_token"] == "superlongkey"
    assert client._cache["app_id"] is not None
    assert client._cache["client_id"] is not None
    assert not client._cache["devices"]
    assert client._cache["token"] is not None

    device = client._devices["012345670123456789abcdef"]
    assert isinstance(device, SkybellDevice)

    assert await client.async_logout() is True
    assert not client._devices

    with pytest.raises(RuntimeError):
        await client.async_login()

    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, os.remove(client._cache_path))

    assert not aresponses.assert_no_unused_routes()


@pytest.mark.asyncio
async def test_get_devices(aresponses: ResponsesMockServer, client: Skybell) -> None:
    """Test getting devices."""
    login_response(aresponses)
    devices_response(aresponses)
    users_me(aresponses)

    data = await client.async_get_device("012345670123456789abcdef", refresh=True)
    assert isinstance(data, SkybellDevice)
    device = client._devices["012345670123456789abcdef"]
    assert isinstance(device, SkybellDevice)
    assert device._device_json["acl"] == "owner"
    assert device._device_json["createdAt"] == "2020-10-20T14:35:00.745Z"
    assert (
        device._device_json["deviceInviteToken"]
        == "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    )
    assert device._device_json["id"] == "012345670123456789abcdef"
    assert device._device_json["location"] == {"lat": "-1.0", "lng": "1.0"}
    assert device._device_json["name"] == "Front Door"
    assert device._device_json["resourceId"] == "012345670123456789abcdef"
    assert device._device_json["status"] == "up"
    assert device._device_json["type"] == "skybell hd"
    assert device._device_json["updatedAt"] == "2020-10-20T14:35:00.745Z"
    assert device._device_json["user"] == "0123456789abcdef01234567"
    assert device._device_json["uuid"] == "0123456789"

    login_response(aresponses)
    data = await client.async_initialize()
    device_avatar(aresponses, device.device_id)
    device_info(aresponses)
    device_settings(aresponses, device.device_id)
    device_avatar(aresponses, device.device_id)
    device_info(aresponses)
    device_settings(aresponses, device.device_id)
    device_activities(aresponses, device.device_id)
    avatar_camera_image(aresponses, device.device_id)
    activity_camera_image(aresponses, device.device_id)
    await client.async_get_device("012345670123456789abcdef", refresh=True)

    devices_response(aresponses)
    device_activities(aresponses, device.device_id)
    avatar_camera_image(aresponses, device.device_id)
    avatar_camera_image(aresponses, device.device_id)
    activity_camera_image(aresponses, device.device_id)
    activity_camera_image(aresponses, device.device_id)
    device = client._devices["012345670123456789abcdee"]
    device_avatar(aresponses, device.device_id)
    device_activities(aresponses, device.device_id)
    assert not device._settings_json
    assert not device._info_json
    assert device.mac is None
    device = client._devices["012345670123456789abcded"]
    device_avatar(aresponses, device.device_id)
    device_settings(aresponses, device.device_id)
    device_activities(aresponses, device.device_id)
    assert not device._info_json
    assert device.images == {}
    for dev in await client.async_get_devices(refresh=True):
        assert isinstance(dev, SkybellDevice)
    new_activity(aresponses, device.device_id)
    assert device._activities[0][CONST.ID] == "1234567890ab1234567890ab"
    assert (
        device._activities[0][CONST.MEDIA_URL]
        == "https://skybell-thumbnails-stage.s3.amazonaws.com/012345670123456789abcdef/1646859244793-951012345670123456789abcdef_012345670123456789abcdef.jpeg"
    )
    assert device.images == {"activity": b"\x00", "avatar": b"\x00"}
    assert (
        device.image_url
        == "https://v3-production-devices-avatar.s3-us-west-2.amazonaws.com/012345670123456789abcdef.jpg"
    )
    new_activity_camera_image(aresponses, "012345670123456789abcdef")
    await device._async_update_activities()
    assert device.images == {"activity": b"\x00\x00", "avatar": b"\x00"}
    assert device._activities[0][CONST.ID] == "1234567890ab1234567890ac"
    assert (
        device._activities[0][CONST.MEDIA_URL]
        == "https://skybell-thumbnails-stage.s3.amazonaws.com/012345670123456789abcdef/1646859244794-951012345670123456789abcdef_012345670123456789abcdef.jpeg"
    )

    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, os.remove(client._cache_path))

    assert not aresponses.assert_no_unused_routes()


@pytest.mark.asyncio
async def test_errors(aresponses: ResponsesMockServer, client: Skybell) -> None:
    """Test errors."""
    with pytest.raises(exceptions.SkybellException):
        await client.async_get_devices()

    aresponses.add(
        "cloud.myskybell.com",
        "/api/v3/login/",
        "post",
        aresponses.Response(
            status=403,
            headers={"Content-Type": "application/json"},
        ),
    )
    with pytest.raises(exceptions.SkybellException):
        await client.async_login()

    with patch("aioskybell.asyncio.sleep"), patch(
        "aioskybell.Skybell.async_send_request"
    ), patch("aioskybell.Skybell.async_update_cache"):
        client = Skybell(
            EMAIL, PASSWORD, auto_login=True, get_devices=True, login_sleep=True
        )
        await client.async_login()

    failed_login_response(aresponses)
    with pytest.raises(exceptions.SkybellAuthenticationException):
        await client.async_login(username="test")

    failed_login_response(aresponses)
    with pytest.raises(exceptions.SkybellAuthenticationException):
        await client.async_login(password="test")

    with pytest.raises(exceptions.SkybellAuthenticationException):
        await Skybell().async_login()

    login_response(aresponses)
    login_response(aresponses)
    with patch("aioskybell.asyncio.sleep"), pytest.raises(exceptions.SkybellException):
        await client.async_get_devices()

    login_response(aresponses)
    with patch("aioskybell.asyncio.sleep"), pytest.raises(exceptions.SkybellException):
        await client.async_send_request(
            "get", "https://skybell-thumbnails-stage.s3.amazonaws.com"
        )

    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, os.remove(client._cache_path))

    assert not aresponses.assert_no_unused_routes()


@pytest.mark.asyncio
async def test_async_refresh_device(
    aresponses: ResponsesMockServer, client: Skybell
) -> None:
    """Test refreshing device."""
    login_response(aresponses)
    devices_response(aresponses)
    _device(aresponses)
    device_info(aresponses)
    device_info(aresponses)

    data = await client.async_get_devices()
    device = data[0]
    device_activities(aresponses, device.device_id)
    device_settings(aresponses, device.device_id)
    device_avatar(aresponses, device.device_id)
    device_settings(aresponses, device.device_id)
    device_avatar(aresponses, device.device_id)
    avatar_camera_image(aresponses, device.device_id)
    activity_camera_image(aresponses, device.device_id)
    await device.async_update(get_devices=True)
    assert device._info_json["address"] == "1.2.3.4"
    assert (
        device._info_json["clientId"]
        == "1234567890abcdef1234567890abcdef1234567890abcdef"
    )
    assert device._info_json["deviceId"] == "01234567890abcdef1234567"
    assert device._info_json["firmwareVersion"] == "7082"
    assert device._info_json["hardwareRevision"] == "SKYBELL_TRIMPLUS_1000030-F"
    assert (
        device._info_json["localHostname"] == "ip-10-0-0-67.us-west-2.compute.internal"
    )
    assert device._info_json["mac"] == "ff:ff:ff:ff:ff:ff"
    assert device._info_json["port"] == "5683"
    assert device._info_json["proxy_address"] == "34.209.204.201"
    assert device._info_json["proxy_port"] == "5683"
    assert device._info_json["region"] == "us-west-2"
    assert device._info_json["serialNo"] == "0123456789"
    assert device._info_json["status"] == {"wifiLink": "poor"}
    assert device._info_json["timestamp"] == "60000000000"
    assert device._info_json["wifiBitrate"] == "39"
    assert device._info_json["wifiLinkQuality"] == "43"
    assert device._info_json["wifiNoise"] == "0"
    assert device._info_json["wifiSignalLevel"] == "-67"
    assert device._info_json["wifiTxPwrEeprom"] == "12"
    assert device._settings_json["ring_tone"] == "0"
    assert device._settings_json["digital_doorbell"] == "false"
    assert device._settings_json["video_profile"] == "1"
    assert device._settings_json["mic_volume"] == "63"
    assert device._settings_json["speaker_volume"] == "96"
    assert device._settings_json["low_lux_threshold"] == "50"
    assert device._settings_json["med_lux_threshold"] == "150"
    assert device._settings_json["high_lux_threshold"] == "400"
    assert device._settings_json["low_front_led_dac"] == "10"
    assert device._settings_json["med_front_led_dac"] == "10"
    assert device._settings_json["high_front_led_dac"] == "10"

    data = device.activities()[0]

    assert data["_id"] == "1234567890ab1234567890ab"
    assert data["callId"] == "1234567890123-1234567890abcd1234567890abcd"
    assert data["createdAt"] == "2020-03-30T12:35:02.204Z"
    assert data["device"] == "0123456789abcdef01234567"
    assert data["event"] == "device:sensor:motion"
    assert data["id"] == "1234567890ab1234567890ab"
    assert data["state"] == "ready"
    assert data["ttlStartDate"] == "2020-03-30T12:35:02.204Z"
    assert data["updatedAt"] == "2020-03-30T12:35:02.566Z"
    assert data["videoState"] == "download:ready"

    assert device.acl == CONST.ACLType.OWNER.value
    assert device.owner is True
    assert device.user_id == "0123456789abcdef01234567"
    assert device.mac == "ff:ff:ff:ff:ff:ff"
    assert device.serial_no == "0123456789"
    assert device.firmware_ver == "7082"
    assert device.name == "Front Door"
    assert device.type == "skybell hd"
    assert device.device_id == "012345670123456789abcdef"
    assert device.status == {"wifiLink": "poor"}
    assert device.is_up is False
    assert device.location == ("-1.0", "1.0")
    assert device.wifi_ssid == "wifi"
    assert device.last_check_in == "2020-03-31T04:13:37.000Z"
    assert device.do_not_disturb is False
    assert device.do_not_ring is False
    assert device.outdoor_chime_level == 1
    assert device.outdoor_chime is True
    assert device.motion_sensor is False
    assert device.motion_threshold == 32
    assert device.video_profile == 1
    assert device.led_rgb == (0, 0, 255)
    assert device.led_intensity == 0
    assert (
        device.desc
        == "Front Door (id: 012345670123456789abcdef) - skybell hd - status: {'wifiLink': 'poor'} - wifi status: poor"
    )

    assert isinstance(device.activities(event="device:sensor:motion"), list)
    assert isinstance(device.latest(event="device:sensor:motion"), dict)

    device_activities(aresponses, device.device_id)
    await device.async_update()

    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, os.remove(client._cache_path))

    assert aresponses.assert_no_unused_routes() is None


@pytest.mark.asyncio
async def test_async_change_setting(
    aresponses: ResponsesMockServer, client: Skybell
) -> None:
    """Test changing settings on device."""

    login_response(aresponses)
    devices_response(aresponses)

    data = await client.async_get_devices()
    device = data[0]
    with patch("aioskybell.device.SkybellDevice._async_settings_request"):
        await device.async_set_setting(CONST.DO_NOT_DISTURB, True)
    assert device._settings_json is not None
    await device.async_set_setting(CONST.DO_NOT_RING, True)
    await device.async_set_setting(CONST.MOTION_POLICY, True)
    await device.async_set_setting("motion_sensor", True)
    await device.async_set_setting(CONST.MOTION_POLICY, True)
    await device.async_set_setting(CONST.LED_COLOR, (0, 0, 0))
    await device.async_set_setting("hs_color", (0, 0, 0))
    await device.async_set_setting(CONST.OUTDOOR_CHIME, 1)
    await device.async_set_setting(CONST.MOTION_THRESHOLD, 32)
    await device.async_set_setting(CONST.VIDEO_PROFILE, 1)
    await device.async_set_setting(CONST.BRIGHTNESS, 33)
    await device.async_set_setting("brightness", 33)

    with pytest.raises(exceptions.SkybellException):
        await client.async_get_device("foo")

    with pytest.raises(exceptions.SkybellException):
        await device.async_set_setting(CONST.DO_NOT_DISTURB, 4)

    with pytest.raises(exceptions.SkybellException):
        await device.async_set_setting(CONST.DO_NOT_RING, 4)

    with pytest.raises(exceptions.SkybellException):
        await device.async_set_setting(CONST.OUTDOOR_CHIME, 4)

    with pytest.raises(exceptions.SkybellException):
        await device.async_set_setting(CONST.MOTION_THRESHOLD, 33)

    with pytest.raises(exceptions.SkybellException):
        await device.async_set_setting(CONST.VIDEO_PROFILE, 5)

    with pytest.raises(exceptions.SkybellException):
        await device.async_set_setting(CONST.LED_COLOR, [-1, 0, 0])

    with pytest.raises(exceptions.SkybellException):
        await device.async_set_setting("hs_color", True)

    with pytest.raises(exceptions.SkybellException):
        await device.async_set_setting(CONST.BRIGHTNESS, 101)

    with pytest.raises(exceptions.SkybellAuthenticationException):
        await data[1].async_set_setting(CONST.BRIGHTNESS, 101)

    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, os.remove(client._cache_path))

    assert aresponses.assert_no_unused_routes() is None


@pytest.mark.asyncio
async def test_cache(client: Skybell) -> None:
    """Test cache."""

    async with aiofiles.open(client._cache_path, "wb"):
        pass

    with patch("aioskybell.Skybell._async_save_cache"), patch(
        "aioskybell.Skybell.async_send_request"
    ):
        await client.async_initialize()

    assert os.path.exists(client._cache_path) is False

    assert UTILS.update("", "") == ""
