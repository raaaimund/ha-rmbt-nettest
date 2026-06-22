RMBT Speedtest — Home Assistant Integration
============================================

A [Home Assistant](https://www.home-assistant.io/) custom integration that runs RMBT network speed tests and exposes the results as sensors.

Uses the Python RMBT client from [open-rmbt-client-cli](https://github.com/rtr-nettest/open-rmbt-client-cli). No third-party dependencies — pure Python stdlib.


## Sensors

| Entity | Unit | Description |
|--------|------|-------------|
| Download Speed | Mbit/s | Aggregate download throughput |
| Upload Speed | Mbit/s | Aggregate upload throughput |
| Ping (Min) | ms | Minimum round-trip time |
| Ping (Median) | ms | Median round-trip time |
| Result URL | — | Link to the detailed test result on netztest.at |

The **Result URL** sensor also carries `test_uuid`, `open_test_uuid`, and `ping_count` as extra attributes.

A **Run Speedtest** button entity triggers an immediate test outside of the scheduled interval.


## Installation

### Via HACS (recommended)

1. Add this repository as a custom HACS repository (Category: Integration).
2. Install "RMBT Speedtest" from HACS.
3. Restart Home Assistant.

### Manual

Copy `custom_components/rmbt_speedtest/` into your HA `config/custom_components/` directory and restart.


## Configuration

1. Go to **Settings → Devices & Services → Add Integration** and search for "RMBT Speedtest".
2. Enter the control server URL (default: `https://controlserver.netztest.at`).
3. The integration registers a client UUID with the server and runs the first test in the background.

### Options

| Option | Default | Description |
|--------|---------|-------------|
| Test interval | 60 min | How often to run an automatic test (15–1440 min) |
| Threads | 0 (auto) | Force a specific thread count; 0 lets the pre-test decide |
| Duration | 0 (server) | Override the test duration in seconds |
| Skip TLS verify | off | Disable TLS certificate checks (useful for local test servers) |


## License

Apache 2.0 — see [LICENSE](LICENSE).
