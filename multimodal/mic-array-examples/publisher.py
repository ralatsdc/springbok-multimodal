from datetime import datetime
import os
import time

import paho.mqtt.client as mqtt


def on_connect(mqttc, obj, flags, reason_code, properties):
    print(f"on_onnect reason_code {str(reason_code)}")


def on_message(mqttc, obj, msg):
    print(
        f"on_message topic {msg.topic}, qos {str(msg.qos)}, payload {str(msg.payload)}"
    )


def on_publish(mqttc, obj, mid, reason_code, properties):
    print(f"on_publish mid {str(mid)}")


def on_log(mqttc, obj, level, string):
    print(f"on_log string {string}")


host = "localhost"
port = 1883
clientid = "two"
disable_clean_session = True
username = "mosquitto"
password = os.environ["MOSQUITTO_PASSWD"]
keepalive = 60
topic = "paho/test/opts"
qos = 0
delay = 1.0

mqttc = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2, clientid, clean_session=disable_clean_session
)

mqttc.username_pw_set(username, password)

mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_log = on_log

print(f"Connecting to {host} on port {port}")
mqttc.connect(host, port, keepalive)

mqttc.loop_start()

try:
    while True:
        message = str(datetime.now())
        print(f"Publishing message {message}")
        infot = mqttc.publish(topic, message, qos=qos)
        infot.wait_for_publish()
        time.sleep(delay)

except KeyboardInterrupt:
    print(f"Disconnecting from {host} on port {port}")
    mqttc.disconnect()

except Exception as e:
    print(f"Exiting due to exception {e}")
