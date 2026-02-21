# subscribeUserInput.py
import time
import threading
import paho.mqtt.client as mqtt

broker = "test.mosquitto.org"
topic_buzzer = "iotp/pe_03/buzzer"
topic_fun = "iotp/pe_03/fun"
topic_threshold = "iotp/pe_03/threshold"

buzzer_value = "false"
fun_value = "false"
threshold_value = "30.0"  # default as string

lock = threading.Lock()
client = None


def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker, rc =", rc)
    client.subscribe(topic_buzzer)
    client.subscribe(topic_fun)
    client.subscribe(topic_threshold)
    print("Subscribed to:", topic_buzzer)
    print("Subscribed to:", topic_fun)
    print("Subscribed to:", topic_threshold)


def on_message(client, userdata, msg):
    global buzzer_value, fun_value, threshold_value

    payload_raw = msg.payload.decode().strip()

    with lock:
        if msg.topic == topic_buzzer:
            payload = payload_raw.lower()
            if payload != "true" and payload != "false":
                return
            buzzer_value = payload
            print("MQTT buzzer_value =", buzzer_value)

        elif msg.topic == topic_fun:
            payload = payload_raw.lower()
            if payload != "true" and payload != "false":
                return
            fun_value = payload
            print("MQTT fun_value =", fun_value)

        elif msg.topic == topic_threshold:
            # accept numbers like: 30, 30.5, " 31 "
            try:
                float(payload_raw)
            except:
                return
            threshold_value = payload_raw
            print("MQTT threshold_value =", threshold_value)


def start_listener():
    global client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker, 1883, 60)

    t = threading.Thread(target=client.loop_forever, daemon=True)
    t.start()

    time.sleep(1)


def get_buzzer_value():
    with lock:
        return buzzer_value


def get_fun_value():
    with lock:
        return fun_value


def get_threshold_value():
    with lock:
        return threshold_value


def stop_listener():
    global client
    try:
        if client is not None:
            client.disconnect()
    except:
        pass