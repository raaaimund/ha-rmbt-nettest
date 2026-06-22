RMBT Speedtest — Home Assistant Integration
============================================

A [Home Assistant](https://www.home-assistant.io/) custom integration that runs RMBT network speed tests and exposes the results as sensors.

Uses the Python RMBT client from [raaaimund/open-rmbt-client-cli](https://github.com/raaaimund/open-rmbt-client-cli) (a fork of the original [rtr-nettest/open-rmbt-client-cli](https://github.com/rtr-nettest/open-rmbt-client-cli)). No third-party dependencies — pure Python stdlib.

Special thanks to [RTR-Netztest](https://www.netztest.at) for providing the measurement infrastructure.


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
2. Enter the control server URL (default: `https://c01.netztest.at`).
3. The integration registers a client UUID with the server and runs the first test in the background.

### Options

| Option | Default | Description |
|--------|---------|-------------|
| Test interval | 60 min | How often to run an automatic test (15–1440 min) |
| Threads | 0 (auto) | Force a specific thread count; 0 lets the pre-test decide |
| Duration | 0 (server) | Override the test duration in seconds |
| Skip TLS verify | off | Disable TLS certificate checks (useful for local test servers) |


## Triggering a speedtest

### Dashboard button

Add a **Button** card pointing at the `button.run_speedtest` entity to kick off a test on demand.

The button automatically becomes **unavailable (grayed out)** while a test is running, preventing double-presses. A companion `binary_sensor.rmbt_speedtest_test_running` entity turns `on` for the duration of the test and can be used in automations or custom dashboard cards.

### Dashboard button with spinner (custom:button-card)

Install [custom:button-card](https://github.com/custom-cards/button-card) via HACS, then use the following card configuration to show an animated spinner while the test is in progress:

```yaml
type: custom:button-card
entity: button.rmbt_speedtest_run_speedtest
name: Run Speedtest
icon: mdi:speedometer
state:
  - value: unavailable
    icon: mdi:loading
    spin: true
    name: Running...
    styles:
      icon:
        - color: var(--warning-color)
```

### Dashboard button with spinner (Mushroom)

Install [lovelace-mushroom](https://github.com/piitaya/lovelace-mushroom) via HACS.

**Basic — icon and color change, no spin (no extra plugins needed):**

```yaml
type: custom:mushroom-template-card
primary: >
  {% if is_state('binary_sensor.rmbt_speedtest_test_running', 'on') %}
    Running...
  {% else %}
    Run Speedtest
  {% endif %}
secondary: >
  {% if is_state('binary_sensor.rmbt_speedtest_test_running', 'on') %}
    Test in progress
  {% else %}
    Tap to start a speed test
  {% endif %}
icon: >
  {% if is_state('binary_sensor.rmbt_speedtest_test_running', 'on') %}
    mdi:loading
  {% else %}
    mdi:speedometer
  {% endif %}
color: >
  {% if is_state('binary_sensor.rmbt_speedtest_test_running', 'on') %}
    orange
  {% else %}
    blue
  {% endif %}
tap_action:
  action: perform-action
  perform_action: button.press
  target:
    entity_id: button.rmbt_speedtest_run_speedtest
```

**With animated spinner — requires [card_mod](https://github.com/thomasloven/lovelace-card-mod) (HACS) in addition to Mushroom:**

```yaml
type: custom:mushroom-template-card
primary: >
  {% if is_state('binary_sensor.rmbt_speedtest_test_running', 'on') %}
    Running...
  {% else %}
    Run Speedtest
  {% endif %}
icon: >
  {% if is_state('binary_sensor.rmbt_speedtest_test_running', 'on') %}
    mdi:loading
  {% else %}
    mdi:speedometer
  {% endif %}
color: >
  {% if is_state('binary_sensor.rmbt_speedtest_test_running', 'on') %}
    orange
  {% else %}
    blue
  {% endif %}
tap_action:
  action: perform-action
  perform_action: button.press
  target:
    entity_id: button.rmbt_speedtest_run_speedtest
card_mod:
  style: |
    {% if is_state('binary_sensor.rmbt_speedtest_test_running', 'on') %}
    mushroom-shape-icon {
      --icon-animation: spin 1s linear infinite;
    }
    {% endif %}
```

### Automation / script — button press

```yaml
- action: button.press
  target:
    entity_id: button.rmbt_speedtest_run_speedtest
```

### Automation / script — update entity

Calling `homeassistant.update_entity` on any of the sensors also triggers a full coordinator refresh:

```yaml
- action: homeassistant.update_entity
  target:
    entity_id: sensor.rmbt_speedtest_download_speed
```

### Example: notify when download drops below threshold

```yaml
automation:
  trigger:
    - platform: numeric_state
      entity_id: sensor.rmbt_speedtest_download_speed
      below: 50
  action:
    - action: notify.mobile_app
      data:
        message: >
          Speed test: download {{ states('sensor.rmbt_speedtest_download_speed') }} Mbit/s
          — {{ states('sensor.rmbt_speedtest_result_url') }}
```


## Python client dependency

This integration depends on the [`rmbt-client`](https://pypi.org/project/rmbt-client/) PyPI package, which originates from [raaaimund/open-rmbt-client-cli](https://github.com/raaaimund/open-rmbt-client-cli) (a fork of [rtr-nettest/open-rmbt-client-cli](https://github.com/rtr-nettest/open-rmbt-client-cli)). Home Assistant installs it automatically when the integration loads.


## License

The integration code is licensed under the **MIT License** — see [LICENSE](LICENSE).

The [`rmbt-client`](https://pypi.org/project/rmbt-client/) dependency originates from [rtr-nettest/open-rmbt-client-cli](https://github.com/rtr-nettest/open-rmbt-client-cli) and is licensed under the **Apache License 2.0**.
