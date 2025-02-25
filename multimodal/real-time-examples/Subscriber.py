import os
import uuid

import paho.mqtt.client as mqtt


class Subscriber:

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
        print(f"on_connect reason_code {str(reason_code)}")

    def on_message(self, mqttc, obj, msg):
        print(
            f"on_message {msg.topic} - qos {str(msg.qos)} - payload {str(msg.payload)}"
        )

    def on_publish(self, mqttc, obj, mid):
        print(f"on_publish mid {str(mid)}")

    def on_subscribe(self, mqttc, obj, mid, reason_code_list, properties):
        print(f"on_subscribe mid {str(mid)} - reason_code_list {str(reason_code_list)}")

    def on_log(self, mqttc, obj, level, string):
        print(f"on_log string {string}")

    def connect(self):
        print(f"Connecting to host {self.host} on port {self.port}")
        self.mqttc.connect(self.host, self.port, self.keepalive)

    def subscribe(self):
        self.mqttc.subscribe(self.topic, self.qos)
        self.mqttc.loop_forever()

    def disconnet(self):
        print(f"Disconnecting from host {self.host} on port {self.port}")
        self.mqttc.disconnect()
