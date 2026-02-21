#subscribe.py for Web Application

import paho.mqtt.client as mqtt
import time

mqtt_broker = "test.mosquitto.org"
topic_temperature = "iotp/pe_03/sensor/temperature"
topic_hum = "iotp/pe_03/sensor/humidity"
topic_fire = "iotp/pe_03/sensor/fire"

# Global variables to store sensor data
temperature = 0
humidity = 0
fire_status = False

# MQTT callback to update sensor values
def on_message(client, userdata, message):
    global temperature, humidity,fire_status
    value = float(message.payload.decode())
    if message.topic == topic_temperature:
        temperature = value
    elif message.topic == topic_hum:
        humidity = value
    elif message.topic == topic_fire:
        fire_status = value

# Start MQTT client once
mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message
mqtt_client.connect(mqtt_broker, port=1883)
mqtt_client.subscribe(topic_temperature)
mqtt_client.subscribe(topic_hum)
mqtt_client.subscribe(topic_fire)
mqtt_client.loop_start()  # start background loop
print("MQTT client started and subscribed to topics")

# Function to get latest sensor data as dictionary
def get_sensor_data(wait_for_data=True, timeout=3):
    start_time = time.time()
    while wait_for_data and (temperature is None or humidity is None):
        if time.time() - start_time > timeout:
            return {'temperature': 0, 'humidity': 0,'fire_status': 0}
        time.sleep(0.1)

    return {
        'temperature': temperature if temperature is not None else 0,
        'humidity': humidity if humidity is not None else 0,
        'fire_status': fire_status
    }
