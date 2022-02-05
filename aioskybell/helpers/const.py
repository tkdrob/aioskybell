"""AIOSkybell constants."""
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

# GENERAL
APP_ID = "app_id"
CLIENT_ID = "client_id"
TOKEN = "token"
ACCESS_TOKEN = "access_token"
DEVICES = "devices"

# DEVICE
NAME = "name"
ID = "id"
TYPE = "type"
STATUS = "status"
STATUS_UP = "up"
LOCATION = "location"
LOCATION_LAT = "lat"
LOCATION_LNG = "lng"
AVATAR = "avatar"
AVATAR_URL = "url"
MEDIA_URL = "media"

# DEVICE INFO
WIFI_LINK = "wifiLink"
WIFI_SSID = "essid"
CHECK_IN = "checkedInAt"

# DEVICE ACTIVITIES
EVENT = "event"
EVENT_ON_DEMAND = "application:on-demand"
EVENT_BUTTON = "device:sensor:button"
EVENT_MOTION = "device:sensor:motion"
CREATED_AT = "createdAt"

STATE = "state"
STATE_READY = "ready"

VIDEO_STATE = "videoState"
VIDEO_STATE_READY = "download:ready"

# DEVICE SETTINGS
DO_NOT_DISTURB = "do_not_disturb"
DO_NOT_RING = "do_not_ring"
OUTDOOR_CHIME = "chime_level"
MOTION = "motion_sensor"
MOTION_POLICY = "motion_policy"
MOTION_THRESHOLD = "motion_threshold"
VIDEO_PROFILE = "video_profile"
LED_R = "green_r"
LED_G = "green_g"
LED_B = "green_b"
LED_COLOR = "hs_color"
LED_COLORS = [LED_R, LED_G, LED_B]
BRIGHTNESS = "led_intensity"

ALL_SETTINGS = [
    DO_NOT_DISTURB,
    DO_NOT_RING,
    OUTDOOR_CHIME,
    MOTION_POLICY,
    MOTION_THRESHOLD,
    VIDEO_PROFILE,
    LED_R,
    LED_G,
    LED_B,
    BRIGHTNESS,
]

# SETTINGS Values
DO_NOT_DISTURB_VALUES = ["True", "False"]
DO_NOT_RING_VALUES = ["True", "False"]

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
