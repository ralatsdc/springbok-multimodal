from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

audio_samples_path = Path("../recordings")
plots_path = Path("../plots")

# Load example audio samples

audio_samples_base = "A10F41_1734652691_Reciprocating_1_1_698_22_audiomoth_manasas"
audio_samples_case = "_left_1s+35db.npy"
sample_data = np.load(audio_samples_path / (audio_samples_base + audio_samples_case))
sample_freq = 48000

# Compute power spectral density

n_ch = sample_data.shape[1]
PSD = np.array([0.0])
for i_ch in range(n_ch):
    f, _PSD = signal.welch(sample_data[:, i_ch], fs=sample_freq, nperseg=1024)
    PSD = PSD + _PSD
PSD /= n_ch

fig, axs = plt.subplots()
axs.semilogx(f, 10 * np.log10(PSD))
axs.set_title(f"{audio_samples_base}", fontsize=10)
axs.set_xlabel("Frequency [Hz]")
axs.set_ylabel("PSD [dB]")
plt.suptitle(f"{audio_samples_case[1:-4]}")
plot_path = plots_path / (audio_samples_base + "_PSD.png")
plt.savefig(plot_path, format="png")
plt.show()
