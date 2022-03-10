"""AIOSkybell constants."""
from enum import Enum

CACHE_PATH = "./skybell.pickle"

# URLS
BASE_URL = "https://cloud.myskybell.com/api/v3/"
BASE_URL_V4 = "https://cloud.myskybell.com/api/v4/"

LOGIN_URL = BASE_URL + "login/"
LOGOUT_URL = BASE_URL + "logout/"

USERS_ME_URL = BASE_URL + "users/me/"

DEVICES_URL = BASE_URL + "devices/"
DEVICE_URL = DEVICES_URL + "$DEVID$/"
DEVICE_ACTIVITIES_URL = DEVICE_URL + "activities/"
DEVICE_AVATAR_URL = DEVICE_URL + "avatar/"
DEVICE_INFO_URL = DEVICE_URL + "info/"
DEVICE_SETTINGS_URL = DEVICE_URL + "settings/"

SUBSCRIPTIONS_URL = BASE_URL + "subscriptions?include=device,owner"
SUBSCRIPTION_URL = BASE_URL + "subscriptions/$SUBSCRIPTIONID$"
SUBSCRIPTION_INFO_URL = SUBSCRIPTION_URL + "/info/"
SUBSCRIPTION_SETTINGS_URL = SUBSCRIPTION_URL + "/settings/"


# ACLs
class ACLType(str, Enum):
    """ACL types."""

    BASIC = "device:basic"
    OWNER = "owner"
    READ = "device:read"


# GENERAL
ACCESS_TOKEN = "access_token"
APP_ID = "app_id"
CLIENT_ID = "client_id"
DEVICES = "devices"
TOKEN = "token"

# DEVICE
ACL = "acl"
ACTIVITY = "activity"
AVATAR = "avatar"
ID = "id"
LOCATION = "location"
LOCATION_LAT = "lat"
LOCATION_LNG = "lng"
MEDIA_URL = "media"
NAME = "name"
STATUS = "status"
STATUS_UP = "up"
TYPE = "type"
URL = "url"

# DEVICE INFO
CHECK_IN = "checkedInAt"
WIFI_LINK = "wifiLink"
WIFI_SSID = "essid"

# DEVICE ACTIVITIES
CREATED_AT = "createdAt"
EVENT = "event"
EVENT_BUTTON = "device:sensor:button"
EVENT_MOTION = "device:sensor:motion"
EVENT_ON_DEMAND = "application:on-demand"

STATE = "state"
STATE_READY = "ready"

VIDEO_STATE = "videoState"
VIDEO_STATE_READY = "download:ready"

# DEVICE SETTINGS
BRIGHTNESS = "led_intensity"
DO_NOT_DISTURB = "do_not_disturb"
DO_NOT_RING = "do_not_ring"
LED_B = "green_b"
LED_G = "green_g"
LED_R = "green_r"
LED_COLORS = [LED_R, LED_G, LED_B]
MOTION_POLICY = "motion_policy"
MOTION_THRESHOLD = "motion_threshold"
OUTDOOR_CHIME = "chime_level"
RGB_COLOR = "rgb_color"
VIDEO_PROFILE = "video_profile"

# SETTINGS Values
BOOL_STRINGS = ["True", "False"]

OUTDOOR_CHIME_OFF = 0
OUTDOOR_CHIME_LOW = 1
OUTDOOR_CHIME_MEDIUM = 2
OUTDOOR_CHIME_HIGH = 3
OUTDOOR_CHIME_VALUES = [
    OUTDOOR_CHIME_OFF,
    OUTDOOR_CHIME_LOW,
    OUTDOOR_CHIME_MEDIUM,
    OUTDOOR_CHIME_HIGH,
]

MOTION_POLICY_OFF = "disabled"
MOTION_POLICY_ON = "call"
MOTION_POLICY_VALUES = [MOTION_POLICY_OFF, MOTION_POLICY_ON]

MOTION_THRESHOLD_LOW = 100
MOTION_THRESHOLD_MEDIUM = 50
MOTION_THRESHOLD_HIGH = 32
MOTION_THRESHOLD_VALUES = [
    MOTION_THRESHOLD_LOW,
    MOTION_THRESHOLD_MEDIUM,
    MOTION_THRESHOLD_HIGH,
]

VIDEO_PROFILE_1080P = 0
VIDEO_PROFILE_720P_BETTER = 1
VIDEO_PROFILE_720P_GOOD = 2
VIDEO_PROFILE_480P = 3
VIDEO_PROFILE_VALUES = [
    VIDEO_PROFILE_1080P,
    VIDEO_PROFILE_720P_BETTER,
    VIDEO_PROFILE_720P_GOOD,
    VIDEO_PROFILE_480P,
]

LED_VALUES = [0, 255]

BRIGHTNESS_VALUES = [0, 100]

EventType = dict[str, dict[str, str]]
DeviceType = dict[str, dict[str, dict[str, str]]]
