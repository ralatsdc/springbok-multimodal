import json
import os
import time
import uuid

import numpy  # Make sure NumPy is loaded before it is used in the callback

from Subscriber import Subscriber

assert numpy  # avoid "imported but unused" message (W0611)


class Locater:

    @staticmethod
    def locate(p1, u1, p2, u2):
        v3 = numpy.linalg.cross(u2, u1)
        u3 = v3 / numpy.linalg.norm(v3)
        a = numpy.array([u1, -u2, u3]).T
        b = p2 - p1
        t1, t2, t3 = numpy.linalg.solve(a, b)
        q1 = p1 + t1 * u1
        q2 = p2 + t2 * u2
        return (q1 + q2) / 2

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

        self.subscriber = Subscriber(
            host=self.host,
            port=self.port,
            clientid=self.clientid,
            disable_clean_session=self.disable_clean_session,
            username=self.username,
            password=self.password,
            keepalive=self.keepalive,
            topic=self.topic,
            qos=self.qos,
        )

        self.subscriber.mqttc.on_message = self.on_message

        self.pointing = {}

    # TODO: Call locate() after receiving messages from two publishers
    def on_message(self, mqttc, obj, msg):
        message = json.loads(msg.payload.decode('utf-8'))
        clientid = message["clientid"]
        origin = numpy.array(message["origin"])
        pointing = numpy.array(message["pointing"])
        if clientid not in self.pointing:
            self.pointing[clientid] = {}
        self.pointing[clientid]["origin"] = origin
        self.pointing[clientid]["pointing"] = pointing
        if len(self.pointing) == 2:
            clientids = list(self.pointing.keys())
            p1 = self.pointing[clientids[0]]["origin"]
            u1 = self.pointing[clientids[0]]["pointing"]
            p2 = self.pointing[clientids[1]]["origin"]
            u2 = self.pointing[clientids[1]]["pointing"]
            location = Locater.locate(p1, u1, p2, u2)
            print(f"Locator finds location {location}")

        elif len(self.pointing) > 2:
            raise Exception("Locate expects two, and only two listeners")
            
        print(
            f"on_message {msg.topic} - qos {str(msg.qos)} - clientid {clientid} - pointing {pointing}"
        )


if __name__ == "__main__":
    locater = Locater(host="44.220.217.88")
    try:
        locater.subscriber.connect()
        locater.subscriber.subscribe()
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n")
        locater.subscriber.disconnect()

    except Exception as e:
        print(f"Exiting due to exception {e}")
