from pathlib import Path
import queue
import sys
import threading
import time

import numpy  # Make sure NumPy is loaded before it is used in the callback
import sounddevice as sd
import soundfile as sf

assert numpy  # avoid "imported but unused" message (W0611)


class Recorder:

    def __init__(
        self,
        device,
        channels,
        samplerate,
        samplegain,
        filename,
        fileformat,
        subtype,
        sampleinterval,
    ):
        self.device = device
        self.channels = channels
        self.samplerate = samplerate
        self.samplegain = samplegain
        self.filename = filename
        self.fileformat = fileformat
        self.subtype = subtype
        self.sampleinterval = sampleinterval
        self.q = queue.Queue()
        self.d = {}
        self.d["inpdata"] = None
        self.d["frames"] = 0

    def callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        adata = indata.copy() * (10.0 ** (self.samplegain / 10.0))
        self.q.put(adata.copy())
        self.d["inpdata"] = numpy.append(self.d["inpdata"], adata.copy(), axis=0)
        self.d["frames"] += frames

    def record(self):
        self.d["inpdata"] = numpy.empty((0, self.channels))
        with sf.SoundFile(
            Path("recordings") / self.filename,
            mode="x",
            samplerate=self.samplerate,
            channels=self.channels,
            format=self.fileformat,
            subtype=self.subtype,
        ) as file:
            with sd.InputStream(
                samplerate=self.samplerate,
                device=self.device,
                channels=self.channels,
                callback=self.callback,
            ):
                while self.d["frames"] / self.samplerate < self.sampleinterval:
                    file.write(self.q.get())

            # Save the audio samples
            numpy.save(
                Path("recordings") / (Path(self.filename).stem + ".npy"),
                self.d["inpdata"],
            )


def main():

    device = "UMA16v2"
    channels = 16
    samplerate = 48000
    samplegain = 0.0
    fileformat = "AIFF"
    filename = f"{device.replace(' ', '-')}-{int(time.time())}.{fileformat.lower()}"
    # TODO: Is this right?
    subtype = "PCM_16"
    sampleinterval = 1

    recorder_one = Recorder(
        device,
        channels,
        samplerate,
        samplegain,
        filename,
        fileformat,
        subtype,
        sampleinterval,
    )

    device = "MacBook Pro Microphone"
    channels = 1
    samplerate = 44100
    samplegain = 0.0
    fileformat = "AIFF"
    filename = f"{device.replace(' ', '-')}-{int(time.time())}.{fileformat.lower()}"
    # TODO: Is this right?
    subtype = "PCM_16"
    sampleinterval = 1

    recorder_two = Recorder(
        device,
        channels,
        samplerate,
        samplegain,
        filename,
        fileformat,
        subtype,
        sampleinterval,
    )

    thread_one = threading.Thread(target=recorder_one.record)
    thread_two = threading.Thread(target=recorder_two.record)

    thread_one.daemon = True
    thread_two.daemon = True

    thread_one.start()
    thread_two.start()

    try:
        while thread_one.is_alive() or thread_two.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Program terminated by user.")


if __name__ == "__main__":
    main()
