#publishData.py

import time
import threading
import paho.mqtt.client as mqtt

mqtt_broker = "test.mosquitto.org"

topic_temp = "iotp/pe_03/sensor/temperature"
topic_hum = "iotp/pe_03/sensor/humidity"
topic_fire = "iotp/pe_03/sensor/fire"


def start_publisher(get_sensor_data_func, get_fire_status_func, stop_event: threading.Event, interval_sec: int = 2):
    """
    get_sensor_data_func() must return a dict with keys: temperature, humidity
    get_fire_status_func() must return True/False
    stop_event is used to stop the loop cleanly
    """
    while not stop_event.is_set():
        data = get_sensor_data_func()
        temp = float(data["temperature"])
        hum = float(data["humidity"])

        payload_temp = str(round(temp, 2))
        payload_hum = str(round(hum, 2))
        payload_fire = "1" if get_fire_status_func() else "0"

        my_mqtt = mqtt.Client()
        print("\nCreated client object at " + time.strftime("%H:%M:%S"))

        my_mqtt.connect(mqtt_broker, port=1883)
        print("--connected to broker")

        try:
            my_mqtt.publish(topic_temp, payload_temp)
            print("--published:", topic_temp, payload_temp)

            my_mqtt.publish(topic_hum, payload_hum)
            print("--published:", topic_hum, payload_hum)

            my_mqtt.publish(topic_fire, payload_fire)
            print("--published:", topic_fire, payload_fire)

        except Exception as e:
            print("--error publishing!", e)

        else:
            my_mqtt.disconnect()
            print("--disconnected from broker")

        stop_event.wait(interval_sec)