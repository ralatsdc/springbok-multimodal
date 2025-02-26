import json
import os
import threading
import uuid

import numpy  # Make sure NumPy is loaded before it is used in the callback

from Publisher import Publisher
from Recorder import Recorder

assert numpy  # avoid "imported but unused" message (W0611)


class Listener:

    def __init__(
        self,
        # Recorder
        device="UMA16v2",
        channels=16,
        samplerate=48000,  # Hz
        samplegain=0.0,  # dB
        fileformat="AIFF",
        subtype="PCM_16",  # TODO: Is this right?
        sampleinterval=1,
        origin=numpy.array([-0.5, 0.0, 0.0]),
        pointing=None,
        geometry_file="geometries/array_16.xml",
        block_size=128,
        window="Hanning",
        hw=1.0,
        increment=0.01,
        freq=4120,
        n_bands=3,
        do_form_beam=False,
        do_plot_beam=False,
        # Publisher
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

        # Recorder
        self.device = device
        self.channels = channels
        self.samplerate = samplerate
        self.samplegain = samplegain
        self.fileformat = fileformat
        self.subtype = subtype
        self.sampleinterval = sampleinterval
        self.origin = origin
        self.pointing = pointing
        self.geometry_file = geometry_file
        self.block_size = block_size
        self.window = window
        self.hw = hw
        self.increment = increment
        self.freq = freq
        self.n_bands = n_bands
        self.do_form_beam = do_form_beam
        self.do_plot_beam = do_plot_beam
        self.recorder = Recorder(
            device=self.device,
            channels=self.channels,
            samplerate=self.samplerate,
            samplegain=self.samplegain,
            fileformat=self.fileformat,
            subtype=self.subtype,
            sampleinterval=self.sampleinterval,
            origin=self.origin,
            pointing=self.pointing,
            geometry_file=self.geometry_file,
            block_size=self.block_size,
            window=self.window,
            hw=self.hw,
            increment=self.increment,
            freq=self.freq,
            n_bands=self.n_bands,
            do_form_beam=self.do_form_beam,
            do_plot_beam=self.do_plot_beam,
        )

        # Publisher
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
        self.publisher = Publisher(
            host=self.host,
            port=self.port,
            clientid=self.clientid,
            disable_clean_session=self.disable_clean_session,
            username=self.username,
            password=self.password,
            keepalive=self.keepalive,
            topic=self.topic,
            qos=self.qos,
            delay=self.delay,
        )

    def listen(self):
        try:
            self.publisher.connect()
            thread = threading.Thread(target=self.recorder.record)
            thread.daemon = True
            thread.start()
            print("Hit Ctrl-C to terminate listener")
            while thread.is_alive():

                # Periodically form and plot beam, if required,
                # publish pointing, then clear accumulated samples
                if (
                    self.recorder.d["frames"] / self.recorder.samplerate
                    > self.recorder.sampleinterval
                ):
                    if self.recorder.do_form_beam:
                        self.recorder.form_beam()
                        if self.recorder.do_plot_beam:
                            self.recorder.plot_beam()
                    self.publisher.publish(json.dumps(self.recorder.pointing.tolist()))
                    self.recorder.d["inpdata"] = numpy.empty(
                        (0, self.recorder.channels)
                    )
                    self.recorder.d["frames"] = 0

        except KeyboardInterrupt:
            print("\n")
            self.publisher.disconnect()


if __name__ == "__main__":
    listener = Listener(
        do_form_beam=True,
        host="44.220.217.88",
    )
    listener.listen()
