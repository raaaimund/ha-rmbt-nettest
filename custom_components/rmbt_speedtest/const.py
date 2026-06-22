"""Constants for rmbt_speedtest."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "rmbt_speedtest"
ATTRIBUTION = "Data provided by RTR RMBT measurement server"

CONF_HOST = "host"
CONF_UUID = "uuid"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_THREADS = "threads"
CONF_DURATION = "duration"
CONF_NO_TLS_VERIFY = "no_tls_verify"

DEFAULT_HOST = "https://c01.netztest.at"
NETZTEST_URL = "https://www.netztest.at"
DEFAULT_SCAN_INTERVAL = 60  # minutes
DEFAULT_THREADS = 0  # 0 = determined by pre-test
DEFAULT_DURATION = 0  # 0 = use server default

CLIENT_VERSION = "1.0.0"
