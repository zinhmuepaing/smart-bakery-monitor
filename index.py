# index.py
# Reads BME280 + flame sensor and controls buzzer/fan.
# Also starts:
# - MQTT publish loop
# - InfluxDB write loop

import time
import threading
import smbus2
import bme280
import RPi.GPIO as GPIO

import subscribeUserInput
import fire_email
import writeDB
import publishData

# I2C config
port = 1
address = 0x76

# GPIO config (BCM numbering)
Buzzer_GPIO = 17
Relay_GPIO = 23
Fire_GPIO = 22


def read_bme280():
    bus = smbus2.SMBus(port)
    try:
        calib = bme280.load_calibration_params(bus, address)
        data = bme280.sample(bus, address, calib)

        return {
            "timestamp": data.timestamp,
            "temperature": float(data.temperature),
            "humidity": float(data.humidity),
            "pressure": float(data.pressure),
        }
    finally:
        bus.close()


def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(Buzzer_GPIO, GPIO.OUT)
    GPIO.setup(Relay_GPIO, GPIO.OUT)

    GPIO.setup(Fire_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.output(Buzzer_GPIO, GPIO.LOW)
    GPIO.output(Relay_GPIO, GPIO.LOW)


def check_fire_alert():
    fire_state = GPIO.input(Fire_GPIO)
    if fire_state == GPIO.LOW:
        return True
    return False


def set_buzzer(on):
    GPIO.output(Buzzer_GPIO, GPIO.HIGH if on else GPIO.LOW)


def set_fan(on):
    GPIO.output(Relay_GPIO, GPIO.HIGH if on else GPIO.LOW)


def control_manual(buzzer_value, fun_value):
    set_buzzer(buzzer_value == "true")
    set_fan(fun_value == "true")
    return "MANUAL"


def control_auto(temp, threshold):
    if temp > threshold:
        set_buzzer(True)
        set_fan(True)
        return "AUTO ALARM ON"
    else:
        set_buzzer(False)
        set_fan(False)
        return "AUTO NORMAL"



def main():
    print("Monitoring Started.")
    print("Fire sensor (GPIO22) has highest priority.")
    print("If any button is ON, system uses MANUAL mode.")
    print("If both buttons are OFF, system uses AUTO threshold mode.\n")
    print("Threshold is read from MQTT topic: iotp/pe_03/threshold\n")

    setup_gpio()


    # Start MQTT subscribe listener (buttons + threshold)
    subscribeUserInput.start_listener()

    stop_event = threading.Event()

    db_thread = threading.Thread(
        target=writeDB.start_writer,
        args=(read_bme280, stop_event, 2),
        daemon=True
    )
    db_thread.start()

    pub_thread = threading.Thread(
        target=publishData.start_publisher,
        args=(read_bme280, check_fire_alert, stop_event, 2),
        daemon=True
    )
    pub_thread.start()

    prev_fire_status = False

    try:
        while True:
            sensor_data = read_bme280()

            temp = sensor_data["temperature"]
            hum = sensor_data["humidity"]
            ts = sensor_data["timestamp"]

            buzzer_value = subscribeUserInput.get_buzzer_value()
            fun_value = subscribeUserInput.get_fun_value()

            threshold_str = subscribeUserInput.get_threshold_value()
            try:
                threshold = float(threshold_str)
            except:
                threshold = 30.0

            fire_status = check_fire_alert()

            if fire_status and not prev_fire_status:
                fire_email.send_fire_email(ts, temp, hum)

            prev_fire_status = fire_status

            if fire_status:
                set_buzzer(True)
                set_fan(fun_value == "true")
                mode = "FIRE ALERT"
            else:
                if buzzer_value == "false" and fun_value == "false":
                    mode = control_auto(temp, threshold)
                else:
                    mode = control_manual(buzzer_value, fun_value)

            print("Time:", ts)
            print("Temperature:", round(temp, 2), "degC")
            print("Humidity:", round(hum, 2), "%")
            print("Threshold:", threshold)
            print("Fire:", fire_status,
                  "| Buttons -> Buzzer:", buzzer_value,
                  "Fan:", fun_value)
            print("Mode:", mode)
            print("")

            time.sleep(2)

    except KeyboardInterrupt:
        print("Program stopped by user.")

    finally:
        stop_event.set()
        subscribeUserInput.stop_listener()
        set_buzzer(False)
        set_fan(False)
        GPIO.cleanup()


if __name__ == "__main__":
    main()