from datetime import datetime
import os
import time
import uuid

import paho.mqtt.client as mqtt


class Publisher:

    def __init__(
        self,
        host="localhost",
        port=1883,
        clientid=str(uuid.uuid1()),
        disable_clean_session=True,
        username="mosquitto",
        password=os.environ["MOSQUITTO_PASSWD"],
        keepalive=60,
        topic="paho/test/opts",
        qos=0,
        delay=1.0,
    ):
        self.host = host
        self.port = port
        self.clientid = clientid
        self.disable_clean_session = disable_clean_session
        self.username = username
        self.password = password
        self.keepalive = keepalive
        self.topic = topic
        self.qos = qos
        self.delay = delay

        self.mqttc = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            self.clientid,
            clean_session=self.disable_clean_session,
        )
        self.mqttc.username_pw_set(self.username, self.password)
        self.mqttc.on_message = self.on_message
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_publish = self.on_publish
        self.mqttc.on_log = self.on_log

    def on_connect(self, mqttc, obj, flags, reason_code, properties):
        print(f"on_onnect reason_code {str(reason_code)}")

    def on_message(self, mqttc, obj, msg):
        print(
            f"on_message topic {msg.topic} - qos {str(msg.qos)} - payload {str(msg.payload)}"
        )

    def on_publish(self, mqttc, obj, mid, reason_code, properties):
        print(f"on_publish mid {str(mid)}")

    def on_log(self, mqttc, obj, level, string):
        print(f"on_log string {string}")

    def connect(self):
        print(f"Connecting to host {self.host} on port {self.port}")
        self.mqttc.connect(self.host, self.port, self.keepalive)
        self.mqttc.loop_start()

    def publish(self, message):
        print(f"Publishing message {message}")
        infot = self.mqttc.publish(self.topic, message, qos=self.qos)
        infot.wait_for_publish()

    def disconnect(self):
        print(f"Disconnecting from host {self.host} on port {self.port}")
        self.mqttc.disconnect()


if __name__ == "__main__":
    publisher = Publisher()
    try:
        publisher.connect()
        while True:
            message = str(datetime.now())
            print(f"Publishing message {message}")
            publisher.publish(message)
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n")
        publisher.disconnect()

    except Exception as e:
        print(f"Exiting due to exception {e}")
