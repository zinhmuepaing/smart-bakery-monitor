# Smart Bakery — IoT Environmental Monitoring

Suggested repository name: **smart-bakery-monitor**

## Overview

Smart Bakery is an end-to-end IoT system for continuous environmental monitoring of small and medium bakeries. It automates temperature, humidity, and fire monitoring using a Raspberry Pi and BME280 sensor, with remote control and visualization via a Flask web dashboard, Grafana, MySQL, and InfluxDB. The system adds safety alerts (buzzer and email) and historical traceability for quality control.

## Objectives

- Continuous sensing of temperature and humidity using BME280, and flame detection using a flame sensor.
- Real-time threshold-based alarm (buzzer) and manual overrides via a web dashboard.
- Remote control of a 5V fan through a relay.
- Bidirectional MQTT communication between Raspberry Pi and the web application.
- Persisting historical data in MySQL and time-series data in InfluxDB for Grafana visualization.
- Fire alert email notifications with cooldown to avoid spamming.
- Modular, threaded design for reliability and non-blocking operation.

## Features

- Real-time telemetry publishing every ~2 seconds from Raspberry Pi to MQTT.
- Web dashboard (Flask + Chart.js) for live values and historical data by date.
- Automatic buzzer activation when temperature exceeds configurable threshold or when flame is detected.
- Manual buzzer and fan control from dashboard.
- Historical storage in MySQL and time-series writes to InfluxDB for Grafana.
- Email alerting for fire events with cooldown (default 300s).
- Systemd service script to auto-start the Raspberry Pi program and Grafana integration.

## Hardware & I/O (summary)

- BME280: I2C (3.3V) — SDA: GPIO2 (Pin 3), SCL: GPIO3 (Pin 5), VCC: 3.3V (Pin 1), GND: Pin 9
- Buzzer: GPIO17 (Pin 11)
- Flame sensor DO: GPIO22 (Pin 15) — defaults High, goes Low on detection
- Relay IN1: GPIO23 (Pin 16) — controls 5V fan (fan power isolated from Pi)
- 5V supply for fan and relay: Pin 2 (5V), common ground required

Refer to your wiring diagrams and safety notes when connecting relays and mains-powered fans.

## MQTT Topics and Payloads

Broker used in project examples: `test.mosquitto.org:1883` (recommend replacing with private broker)

- Telemetry published by Raspberry Pi:
  - `iotp/pe_03/sensor/temperature` — payload: temperature string, e.g. `25.99`
  - `iotp/pe_03/sensor/humidity` — payload: humidity string, e.g. `60.09`
  - `iotp/pe_03/sensor/fire` — payload: `1` (fire) or `0` (no fire)

- Controls published by Web App:
  - `iotp/pe_03/buzzer` — `true` / `false` (manual buzzer command)
  - `iotp/pe_03/fun` — `true` / `false` (fan control)
  - `iotp/pe_03/threshold` — numeric string, e.g. `30` or `30.5`

Behavior summary on Raspberry Pi:
- Flame detection forces buzzer ON and triggers email alert.
- If no fire and any manual button is ON, manual mode applies.
- If no fire and both buttons OFF, auto mode compares temperature to the current threshold (default 30.0°C).

## Software Components (workspace mapping)

- Raspberry Pi / Edge code
  - [index.py](index.py) — main control loop, sensor reads, GPIO logic, publishes telemetry, writes to InfluxDB, calls email alert on flame detection.
  - [publishData.py](publishData.py) — (publisher) sends temperature, humidity, fire status to MQTT (used/integrated by `index.py`).
  - [subscribeUserInput.py](subscribeUserInput.py) — MQTT subscriber for user controls (`buzzer`, `fun`, `threshold`) with thread-safe storage.
  - [writeDB.py](writeDB.py) — writes aggregated records to MySQL for historical queries.
  - [fire_email.py](fire_email.py) — sends fire alert email with cooldown (e.g., 300s) to avoid repeated emails.

- Web Application (Flask)
  - `Flask Web API/control.py` — REST endpoints and handlers for control and threshold POST actions.
  - `Flask Web API/subscribe.py` — MQTT subscriber to receive sensor telemetry and expose latest values to Flask endpoints.
  - `Flask Web API/db.py` — MySQL access layer used for historical data endpoints.
  - `Flask Web API/templates/BuzzerFunBtn.html` — dashboard UI.
  - `Flask Web API/static/script.js` — client-side polling and Chart.js logic.
  - `Flask Web API/static/style.css` — dashboard styles.

Note: file names are referenced as present in the project workspace; adjust imports or paths if you reorganize directories.

## Databases & Schema

- MySQL (relational) — Database: `sensorReading` (or `iotpdb` depending on your MySQL schema in the project)
  - Table example: `datas`
  - Stored fields: timestamp (UTC), temperature (float), humidity (float), fire_status (int), nodeId

- InfluxDB (time-series) — Database: `sensorReading`
  - Measurement: `reading`
  - Tags: `nodeId`
  - Fields: `Temperature` (float), `Humidity` (float)
  - Timestamp: write time from Raspberry Pi in UTC (format `YYYY-MM-DD HH:MM:SS`)

This split allows easy web-based historical queries (MySQL) and high-performance time-series visualization (Grafana + InfluxDB).

## Deployment & Setup (high level)

Prerequisites:
- Raspberry Pi with Python 3 and I2C enabled.
- Python packages: `paho-mqtt`, `Flask`, `mysql-connector-python` (or `PyMySQL`), `influxdb-client` (or `influxdb`), sensor libraries for BME280 (e.g., `smbus2`, `Adafruit_BME280`), and `RPi.GPIO` or `gpiozero`.
- MySQL (XAMPP or native) for web historical storage.
- InfluxDB and Grafana for time-series and dashboards.
- An SMTP-capable account or SMTP server for email alerts.

Quick steps:
1. Install Python dependencies on Raspberry Pi and server hosting Flask.

```bash
pip3 install paho-mqtt Flask mysql-connector-python influxdb-client smbus2 RPi.GPIO
```

2. Configure MQTT broker settings in `index.py` and Flask `subscribe.py`.
3. Set MySQL connection credentials in `Flask Web API/db.py` and `writeDB.py`.
4. Configure InfluxDB URL, token, and org in `index.py` (or `writeDB.py`) if using InfluxDB v2.
5. On the Pi, enable I2C: `raspi-config` -> Interfacing Options -> I2C.
6. Setup systemd service for auto-start: create `/etc/systemd/system/smartbakery.service` with `ExecStart=/usr/bin/python3 /path/to/index.py` and enable with `sudo systemctl enable smartbakery.service`.
7. Enable Grafana to start on boot with `sudo systemctl enable grafana-server`.

Run locally for testing:
```bash
# Start Flask app (from Flask Web API directory)
export FLASK_APP=control.py
flask run --host=0.0.0.0 --port=5000
```

## Usage

- Open the Flask dashboard in a browser to see real-time values and charts. The dashboard polls `/api/sensor-data` every ~5s and updates Chart.js graphs.
- Use controls on the dashboard to set buzzer/fan and publish a threshold. The web app publishes these values to MQTT topics consumed by the Raspberry Pi.
- View longer trends in Grafana connected to InfluxDB.
- Query per-day historical records via the dashboard's historical-data endpoint which reads MySQL.

## Logging, Threading & Reliability

- MQTT publishing and DB writes are performed in background threads to keep the control loop responsive.
- The flame sensor check runs each loop; when fire is detected `fire_email.py` is called to send an alert (with cooldown).
- Consider adding structured logging and log rotation for production use.

## Security & Recommendations

- Replace the public MQTT broker with a private, authenticated broker (e.g., Mosquitto with TLS and password auth).
- Protect the Flask dashboard with authentication and HTTPS for remote access.
- Add input validation and rate-limiting on REST endpoints.
- Add DB indexing on timestamp and nodeId for faster historical queries.
- Consider circuit protections (flyback diodes, transistors/MOSFETs for buzzer drives, opto-isolated relays for mains loads).
- Add role-based controls to restrict who can change thresholds or send manual commands.

## Troubleshooting

- If BME280 readings are missing, verify I2C is enabled and `i2cdetect -y 1` shows the device address.
- If MQTT messages are not seen, check broker connectivity and topic names in both publisher and subscriber.
- For email failures, verify SMTP credentials and network connectivity.

## Evidence & Screenshots

(Insert circuit photos, terminal outputs, Grafana panels, and dashboard screenshots in the repo's `docs/` folder.)

## Files of Interest

- [index.py](index.py) — main Raspberry Pi control program
- [publishData.py](publishData.py) — telemetry publisher
- [subscribeUserInput.py](subscribeUserInput.py) — subscriber for web controls
- [writeDB.py](writeDB.py) — MySQL writer for historical data
- [fire_email.py](fire_email.py) — email alerting logic
- Flask Web App directory: `Flask Web API/` (control, subscribe, db, templates, static files)

## Future Improvements

- Private, secured MQTT broker and TLS connections.
- User accounts and RBAC for dashboard controls.
- ML-based anomaly detection for predictive maintenance and anomaly alerts.
- Over-the-air updates for Raspberry Pi software.
- Cloud backup of historical data and multi-node support.

## Team

- Zin Hmue Paing
- Ye Min Htet
- Suu Suu Phyoe

---

If you'd like, I can:
- Commit this README to git and create a suggested repository layout.
- Add a `requirements.txt` and a short `README-setup.md` with exact config variables.

