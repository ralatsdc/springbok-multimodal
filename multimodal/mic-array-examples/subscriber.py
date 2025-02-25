import os

import paho.mqtt.client as mqtt

host = "localhost"
port = 1883
clientid = "one"
disable_clean_session = True
username = "mosquitto"
password = os.environ["MOSQUITTO_PASSWD"]
keepalive = 60
topic = "paho/test/opts"
qos = 0


def on_connect(mqttc, obj, flags, reason_code, properties):
    print(f"on_connect reason_code {str(reason_code)}")


def on_message(mqttc, obj, msg):
    print(f"on_message {msg.topic} - qos {str(msg.qos)} - payload {str(msg.payload)}")


def on_publish(mqttc, obj, mid):
    print(f"on_publish mid {str(mid)}")


def on_subscribe(mqttc, obj, mid, reason_code_list, properties):
    print(f"on_subscribe mid {str(mid)} - reason_code_list {str(reason_code_list)}")


def on_log(mqttc, obj, level, string):
    print(f"on_log string {string}")


mqttc = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2, clientid, clean_session=disable_clean_session
)

mqttc.username_pw_set(username, password)

mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
mqttc.on_log = on_log

print(f"Connecting to host {host} on port {str(port)}")
mqttc.connect(host, port, keepalive)
mqttc.subscribe(topic, qos)

mqttc.loop_forever()
