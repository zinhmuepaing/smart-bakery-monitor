#control.py for Web Application

from collections import deque
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import time
import paho.mqtt.client as mqtt
import subscribe
import db
import mysql.connector

app = Flask(__name__)

mqtt_broker = "test.mosquitto.org"
topic_buzzer = "iotp/pe_03/buzzer"
topic_fun = "iotp/pe_03/fun"
topic_thresh = "iotp/pe_03/thresh"

temperatures = []
humidities = []
fires = []
timecount = 0

data_history = deque(maxlen=50)

def publish(b_value,f_value,t_value):
    # Publish to MQTT when values change
    my_mqtt = mqtt.Client()
    print("\nCreated client object at " + time.strftime("%H:%M:%S"))
    try:
        my_mqtt.connect(mqtt_broker, port=1883)
        print("--connected to broker")

        my_mqtt.publish(topic_buzzer, b_value)
        print("BUZZER published: " + b_value)
        my_mqtt.publish(topic_fun, f_value)
        print("FUN published: " + f_value)
        my_mqtt.publish(topic_thresh,t_value)
        print("THRESH published: " + t_value)
        my_mqtt.disconnect()
        print("--disconnected from broker")
    except Exception as e:
        print(f"--error publishing! {e}")


@app.route("/", methods=['POST', 'GET'])
def home():
    buzzer_value = "false"
    fun_value = "false"
    thresh_value = 0

    if request.method == "POST":
        buzzer_value = request.form.get("buzzer", "false")
        fun_value = request.form.get("fun", "false")
        thresh_value = request.form.get("thresh",0)
        print(f"Buzzer: {buzzer_value}, Fun: {fun_value}")
        publish(buzzer_value,fun_value,thresh_value)

    return render_template("BuzzerFunBtn.html",
                           buzzer=buzzer_value,
                           fun=fun_value,
                           thresh = thresh_value
                        )

@app.route("/api/sensor-data", methods=["GET"])
def api_sensor_data():
    global temperatures,humidities,fires,timecount

    data_raw = subscribe.get_sensor_data()
    temperature = data_raw['temperature']
    humidity = data_raw['humidity']
    fire = data_raw['fire_status']
    timecount += 1

    if timecount % 12 == 0:
        temperatures.append(temperature)
        humidities.append(humidity)
        fires.append(fire)

    if len(temperatures) == 60 or len(humidities) == 60 or len(fires) == 60:
        tempToWrite = sum(temperatures) / len(temperatures)
        humidToWrite = sum(humidities) / len(humidities)
        fToWrite = any(fires)
        db.write_database(tempToWrite, humidToWrite, fToWrite)

        temperatures = []
        humidities = []
        fires = []

    data = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "temperature": temperature,
        "humidity": humidity,
        "fire_status": fire,
    }
    return jsonify(data)


@app.route("/api/historical-data", methods=["GET"])
def get_historical_data():
    date = request.args.get('date')

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='iotpdb'
    )

    cursor = conn.cursor()
    cursor.execute("SELECT Date, Temperature, Humidity, FireStatus FROM datas WHERE Date LIKE %s ORDER BY Date",
                   (f"{date}%",))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    data = []
    for row in results:
        hour = row[0].split()[-1] if ' ' in row[0] else '00'
        data.append({
            'hour': f"{hour}:00",
            'temperature': round(float(row[1]), 1),
            'humidity': round(float(row[2]), 1),
            'fire_status': row[3]
        })

    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True,port=5001)