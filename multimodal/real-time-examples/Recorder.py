import threading
from pathlib import Path
import sys
import time

import acoular as ac
import matplotlib.pyplot as plt
import numpy  # Make sure NumPy is loaded before it is used in the callback
import sounddevice as sd
import soundfile as sf

assert numpy  # avoid "imported but unused" message (W0611)
plt.ion()  # enable interactive mode


class Recorder:

    def __init__(
        self,
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
    ):
        self.device = device
        self.channels = channels
        self.samplerate = samplerate  # Hz
        self.samplegain = samplegain  # dB
        self.fileformat = fileformat
        self.subtype = subtype
        self.sampleinterval = sampleinterval
        self.origin = origin
        self.pointing = pointing
        self.geometry_file = geometry_file
        self.block_size = block_size
        self.window = window
        self.hw = hw  # m
        self.increment = increment
        self.freq = freq  # Hz
        self.n_bands = n_bands
        self.do_form_beam = do_form_beam
        self.do_plot_beam = do_plot_beam

        self.mg = ac.MicGeom(from_file=geometry_file)
        self.rg = ac.RectGrid(
            x_min=-self.hw,
            x_max=self.hw,
            y_min=-self.hw,
            y_max=self.hw,
            z=1.0,
            increment=self.increment,
        )
        self.st = ac.SteeringVector(grid=self.rg, mics=self.mg)

        self.d = {}
        self.d["inpdata"] = numpy.empty((0, self.channels))
        self.d["frames"] = 0

        self.Lm = None

        if self.do_plot_beam:
            fig, axs = plt.subplots()
            self.fig = fig
            self.axs = axs
            self.fignum = plt.gcf().number
            self.init_plot()

    def init_plot(self):
        plt.figure(self.fignum)
        plt.imshow(
            numpy.empty((0, 0)),
            origin="lower",
            vmin=-10.0,
            extent=self.rg.extend(),
            interpolation="bicubic",
        )
        self.axs.set_title(f"{self.device}", fontsize=10)
        self.axs.set_xlabel("x [m]")
        self.axs.set_ylabel("y [m]")
        plt.colorbar()
        plt.draw()
        plt.pause(1.0e-1)

    def plot_beam(self):
        plt.figure(self.fignum)
        plt.imshow(
            self.Lm.T,
            origin="lower",
            vmin=self.Lm.max() - 10.0,
            extent=self.rg.extend(),
            interpolation="bicubic",
        )
        plt.draw()
        plt.pause(1.0e-1)

    def form_beam(self):
        sample_data = self.d["inpdata"]
        ts = ac.TimeSamples(data=sample_data, sample_freq=self.samplerate)
        ps = ac.PowerSpectra(source=ts, block_size=self.block_size, window=self.window)
        bb = ac.BeamformerBase(freq_data=ps, steer=self.st)
        pm = bb.synthetic(self.freq, self.n_bands)
        self.Lm = ac.L_p(pm)
        # TODO: Explain why Fortran?
        i_max, j_max = numpy.unravel_index(
            numpy.argmax(self.Lm.T, axis=None), self.Lm.T.shape, order="F"
        )
        print(f"i_max: {i_max}, j_max: {j_max}")

        x_max = self.rg.x_min + self.rg.increment * i_max
        y_max = self.rg.y_min + self.rg.increment * j_max
        z_max = self.rg.z
        print(f"x_max: {x_max}, y_max: {y_max}, z_max: {z_max}")

        azm = numpy.atan2(x_max, z_max)
        elv = numpy.atan2(-y_max, (x_max**2 + z_max**2) ** (1 / 2))
        print(f"azm: {azm * 180.0 / numpy.pi}")
        print(f"alv: {elv * 180.0 / numpy.pi}")

        v = numpy.array([x_max, y_max, z_max])
        self.pointing = v / numpy.linalg.norm(v)

    def callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        adata = indata.copy() * (10.0 ** (self.samplegain / 10.0))
        self.d["inpdata"] = numpy.append(self.d["inpdata"], adata, axis=0)
        self.d["frames"] += frames

    def record(self):
        with sd.InputStream(
            samplerate=self.samplerate,
            device=self.device,
            channels=self.channels,
            callback=self.callback,
        ):
            while True:
                time.sleep(1.0e-3)


if __name__ == "__main__":
    recorder = Recorder(
        device="MacBook Pro Microphone",
        channels=1,
        samplerate=44100,  # Hz
    )
    thread = threading.Thread(target=recorder.record)
    thread.daemon = True
    thread.start()
    try:
        print("Hit Ctrl-C to terminate recorder")
        while thread.is_alive():

            # Periodically clear recording
            if recorder.d["frames"] / recorder.samplerate > recorder.sampleinterval:
                print(
                    f"Writing then clearing accumulated {recorder.d['frames']} frames"
                )
                filename = f"{recorder.device.replace(' ', '-')}-{int(time.time())}.{recorder.fileformat.lower()}"
                with sf.SoundFile(
                    Path("recordings") / filename,
                    mode="x",
                    samplerate=recorder.samplerate,
                    channels=recorder.channels,
                    format=recorder.fileformat,
                    subtype=recorder.subtype,
                ) as file:
                    file.write(recorder.d["inpdata"])
                recorder.d["inpdata"] = numpy.empty((0, recorder.channels))
                recorder.d["frames"] = 0

    except KeyboardInterrupt:
        print("\n")
        print("Program terminated by user.")
