"""Models for Skybell."""
from __future__ import annotations

from datetime import datetime


class InfoDict(dict):
    """Class for info."""

    address: str
    checkedInAt: str
    clientId: str
    deviceId: str
    essid: str
    firmwareVersion: str
    hardwareRevision: str
    localHostname: str
    mac: str
    port: str
    proxy_address: str
    proxy_port: str
    region: str
    serialNo: str
    status: dict[str, str]
    timestamp: str
    wifiBitrate: str
    wifiLinkQuality: str
    wifiNoise: str
    wifiSignalLevel: str
    wifiTxPwrEeprom: str


class DeviceDict(dict):
    """Class for device."""

    acl: str
    createdAt: str
    deviceInviteToken: str
    id: str
    location: dict[str, str]
    name: str
    resourceId: str
    status: str
    type: str
    updatedAt: str
    user: str
    uuid: str


class AvatarDict(dict):
    """Class for avatar."""

    createdAt: str
    url: str


class SettingsDict(dict):
    """Class for settings."""

    chime_level: str | None
    digital_doorbell: str | None
    do_not_disturb: str | None
    do_not_ring: str | None
    green_b: str | None
    green_g: str | None
    green_r: str | None
    high_front_led_dac: str | None
    high_lux_threshold: str | None
    led_intensity: str | None
    low_front_led_dac: str | None
    low_lux_threshold: str | None
    med_front_led_dac: str | None
    med_lux_threshold: str | None
    mic_volume: str | None
    motion_policy: str | None
    motion_threshold: str | None
    ring_tone: str | None
    speaker_volume: str | None
    video_profile: str | None


class EventDict(dict):
    """Class for an event."""

    _id: str
    callId: str
    createdAt: datetime
    device: str
    event: str
    id: str
    media: str
    mediaSmall: str
    state: str
    ttlStartDate: str
    updatedAt: str
    videoState: str


EventTypeDict = dict[str, EventDict]
DeviceTypeDict = dict[str, dict[str, EventTypeDict]]
DevicesDict = dict[str, DeviceTypeDict]
