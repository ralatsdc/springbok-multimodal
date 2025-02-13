from pathlib import Path

import acoular as ac
import matplotlib.pyplot as plt
import numpy

geometry_path = Path("geometries")
audio_samples_path = Path("recordings")
plots_path = Path("plots")

# Load and plot mic geometry

geometry_file = geometry_path / "array_16.xml"
mg = ac.MicGeom(from_file=geometry_file)

fig, axs = plt.subplots()
axs.plot(mg.mpos[0], mg.mpos[1], "o")
for i_pos in range(mg.mpos.shape[1]):
    axs.text(mg.mpos[0][i_pos] + 0.005, mg.mpos[1][i_pos], str(i_pos + 1))
axs.set_title("mic geometry")
axs.set_xlabel("x [cm]")
axs.set_ylabel("y [cm]")
axs.axis("equal")
plot_path = plots_path / "UMA-16-MicGeom.png"
plt.savefig(plot_path, format="png")
plt.show()

# Use Acoular's basic beamforming example

hw = 1.0
sample_freq = 48000
block_size = 128
window = "Hanning"
increment = 0.01
freq = 4120
n_bands = 3

def form_beam(audio_samples_file):

    sample_data = numpy.load(audio_samples_file)
    ts = ac.TimeSamples(data=sample_data, sample_freq=sample_freq)
    ps = ac.PowerSpectra(source=ts, block_size=block_size, window=window)
    rg = ac.RectGrid(
        x_min=-hw, x_max=hw, y_min=-hw, y_max=hw, z=1.0, increment=increment
    )
    st = ac.SteeringVector(grid=rg, mics=mg)
    bb = ac.BeamformerBase(freq_data=ps, steer=st)
    pm = bb.synthetic(freq, n_bands)
    Lm = ac.L_p(pm)

    return Lm, rg, ps

# Process specified audio samples

audio_samples_base = "A10F41_1734652691_Reciprocating_1_1_698_22_audiomoth_manasas"
audio_samples_cases = [
    "_left_1s+35db.npy",
    "_right_1s+35db.npy",
    # "_demo.npy",
]

for audio_samples_case in audio_samples_cases:

    Lm, rg, ps = form_beam(
        audio_samples_path / (audio_samples_base + audio_samples_case)
    )

    fig, axs = plt.subplots()
    plt.imshow(
        Lm.T,
        origin="lower",
        vmin=Lm.max() - 10,
        extent=rg.extend(),
        interpolation="bicubic",
    )
    axs.set_title(f"{audio_samples_base}", fontsize=10)
    axs.set_xlabel("x [m]")
    axs.set_ylabel("y [m]")
    plt.suptitle(f"{audio_samples_case[1:-4]}")
    plt.colorbar()
    plot_path = plots_path / (audio_samples_base + "_" + audio_samples_case[1:-4] + ".png")
    plt.savefig(plot_path, format="png")
    plt.show()
