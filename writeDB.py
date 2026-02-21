#writeDB.py

import time
import threading
from influxdb import InfluxDBClient

USER = "root"
PASSWORD = "root"
DBNAME = "sensorReading"
HOST = "localhost"
PORT = 8086


def _build_point(temp: float, hum: float):
    now = time.gmtime()
    return [
        {
            "time": time.strftime("%Y-%m-%d %H:%M:%S", now),
            "measurement": "reading",
            "tags": {
                "nodeId": "node_1",
            },
            "fields": {
                "Temperature": round(temp, 2),
                "Humidity": round(hum, 2),
            },
        }
    ]


def start_writer(get_sensor_data_func, stop_event: threading.Event, interval_sec: int = 2):
    """
    get_sensor_data_func() must return a dict with keys: temperature, humidity
    stop_event is used to stop the loop cleanly
    """
    client = InfluxDBClient(HOST, PORT, USER, PASSWORD, DBNAME)

    while not stop_event.is_set():
        data = get_sensor_data_func()
        temp = float(data["temperature"])
        hum = float(data["humidity"])

        point = _build_point(temp, hum)
        client.write_points(point)
        print("Written data")

        stop_event.wait(interval_sec)