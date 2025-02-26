from pathlib import Path
import sys
import threading
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
        device,
        channels,
        samplerate,
        samplegain,
        filename,
        fileformat,
        subtype,
        sampleinterval,
        origin=numpy.array([0.0, 0.0, 0.0]),
        pointing=None,
        geometry_file="geometries/array_16.xml",
        block_size=128,
        window="Hanning",
        hw=1.0,
        increment=0.01,
        freq=4120,
        n_bands=3,
        do_form_beam=False,
    ):
        self.device = device
        self.channels = channels
        self.samplerate = samplerate  # Hz
        self.samplegain = samplegain  # dB
        self.filename = filename
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
        # TODO: Remove
        # audio_samples_file = Path("recordings") / (
        #     "A10F41_1734652691_Reciprocating_1_1_698_22_audiomoth_manasas"
        #     + "_right_1s+35db.npy"
        # )
        # sample_data = numpy.load(audio_samples_file)
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


def locate(p1, u1, p2, u2):
    v3 = numpy.linalg.cross(u2, u1)
    u3 = v3 / numpy.linalg.norm(v3)
    a = numpy.array([u1, -u2, u3]).T
    b = p2 - p1
    t1, t2, t3 = numpy.linalg.solve(a, b)
    q1 = p1 + t1 * u1
    q2 = p2 + t2 * u2
    return (q1 + q2) / 2


def main():

    device = "UMA16v2"
    channels = 16
    samplerate = 48000  # Hz
    samplegain = 0.0  # dB
    fileformat = "AIFF"
    filename = f"{device.replace(' ', '-')}-{int(time.time())}.{fileformat.lower()}"
    # TODO: Is this right?
    subtype = "PCM_16"
    sampleinterval = 1
    origin = numpy.array([-0.5, 0.0, 0.0])

    recorder_one = Recorder(
        device,
        channels,
        samplerate,
        samplegain,
        filename,
        fileformat,
        subtype,
        sampleinterval,
        origin=origin,
        do_form_beam=True,
    )

    device = "UMA16v2"
    channels = 16
    samplerate = 48000  # Hz
    samplegain = 0.0  # dB
    fileformat = "AIFF"
    filename = f"{device.replace(' ', '-')}-{int(time.time())}.{fileformat.lower()}"
    # TODO: Is this right?
    subtype = "PCM_16"
    sampleinterval = 1
    origin = numpy.array([+0.5, 0.0, 0.0])

    recorder_two = Recorder(
        device,
        channels,
        samplerate,
        samplegain,
        filename,
        fileformat,
        subtype,
        sampleinterval,
        origin=origin,
        do_form_beam=True,
    )

    thread_one = threading.Thread(target=recorder_one.record)
    thread_two = threading.Thread(target=recorder_two.record)

    thread_one.daemon = True
    thread_two.daemon = True

    thread_one.start()
    thread_two.start()

    try:
        print("Hit Ctrl-C to terminate program")
        while thread_one.is_alive() or thread_two.is_alive():

            # Periodically form beam one
            if (
                recorder_one.d["frames"] / recorder_one.samplerate
                > recorder_one.sampleinterval
            ):
                if recorder_one.do_form_beam:
                    recorder_one.form_beam()
                    recorder_one.plot_beam()
                recorder_one.d["inpdata"] = numpy.empty((0, recorder_one.channels))
                recorder_one.d["frames"] = 0

            # Periodically form beam two
            if (
                recorder_two.d["frames"] / recorder_two.samplerate
                > recorder_two.sampleinterval
            ):
                if recorder_two.do_form_beam:
                    recorder_two.form_beam()
                    recorder_two.plot_beam()
                recorder_two.d["inpdata"] = numpy.empty((0, recorder_two.channels))
                recorder_two.d["frames"] = 0

            # Locate whenever able
            if recorder_one.pointing is not None and recorder_two.pointing is not None:
                locate(
                    recorder_one.origin,
                    recorder_one.pointing,
                    recorder_two.origin,
                    recorder_two.pointing,
                )
                recorder_one.pointing = None
                recorder_two.pointing = None

    except KeyboardInterrupt:
        print("Program terminated by user.")


if __name__ == "__main__":
    # main()
    p1 = numpy.array([-0.5, 0.0, 0.0])
    p2 = numpy.array([+0.5, 0.0, 0.0])

    v1 = numpy.array([0.5, -0.5, 1.0])
    v2 = numpy.array([-0.5, -0.5, 1.0])

    u1 = v1 / numpy.linalg.norm(v1)
    u2 = v2 / numpy.linalg.norm(v2)

    q = locate(p1, u1, p2, u2)

    print(f"q: {q}")
