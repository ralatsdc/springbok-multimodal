import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal
import soundfile as sf


SPEED_OF_SOUND = 343  # [m/s] - See: https://en.wikipedia.org/wiki/Speed_of_sound

AUDIOMOTH_SENSITIVITY = -38.0  # [dB re V/Pa]
AUDIOMOTH_GAIN = 15.0  # [dB]

ARCHIVE_DIR = Path("2025-01-6-dataset-archive")
DATASET_DIR = "dataset"
DATASET_CSV = "dataset.csv"

ENGINE_TYPES = [
    "4-Cycle",
    "Reciprocating",
    "Turbo-fan",
    "Turbo-prop",
    "Turbo-shaft",
]


def compute_PL(r, c):
    """Compute propagation loss assuming spherical spreading.

    Parameters
    ----------
    r : float
        Range [m]
    c : float
        Speed of sound [m/s]

    Returns
    -------
    PL : float
        Propagation loss [dB re m²]

    """
    # Assume spherical spreading
    PL = 20 * math.log10(r)  #  dB re m²

    return PL


def compute_MSP(samples, S_dB_re_V_per_Pa, gain_dB):
    """Use samples produced by a microphone to compute mean square
    pressure.

    Parameters
    ----------
    samples : numpy.ndarray
        The audio samples
    S_dB_re_V_per_Pa : float
        Microphone sensitivity [dB re V/Pa]
    gain_dB : float
        Gain applied prior to analog to digital conversion [dB]

    Returns
    -------
    MSP : float
        Mean square pressure [Pa²]
    SPL : float
        Sound pressure level [dB re Pa²]
    pressure : numpy.ndarray
        Pressure samples [Pa]

    """
    # Compute voltage at microphone
    gain = 10 ** (gain_dB / 20)
    voltage = samples / gain  # [V]

    # Compute pressure at microphone
    S_V_per_Pa = 10 ** (S_dB_re_V_per_Pa / 20)  # [V/Pa]
    pressure = voltage / S_V_per_Pa  # [Pa]

    # Compute mean square pressure and sound pressure level
    MSP = np.mean(np.power(pressure, 2))  # [Pa²]
    SPL = 10 * math.log10(MSP)  # [dB re Pa²]

    return MSP, SPL, pressure


def compute_SL(samples, S_dB_re_V_per_Pa, gain_dB, r, c):
    """Use samples produced by a microphone to compute source level.

    Parameters
    ----------
    samples : numpy.ndarray
        The audio samples
    S_dB_re_V_per_Pa : float
        Microphone sensitivity [dB re V/Pa]
    gain_dB : float
        Gain applied prior to analog to digital conversion [dB]
    r : float
        Range [m]
    c : float
        Sound speed [m/s]

    Returns
    -------
    SL : float
        Source level [dB re Pa²m²]
    PL : float
        Propagation loss [dB re m²]
    MSP : float
        Mean square pressure [Pa²]
    SPL : float
        Sound pressure level [dB re Pa²]
    pressure : numpy.ndarray
        Pressure samples [Pa]

    """
    MSP, SPL, pressure = compute_MSP(samples, S_dB_re_V_per_Pa, gain_dB)
    PL = compute_PL(r, c)
    SL = SPL + PL  # [dB re Pa²m²]

    return SL, PL, MSP, SPL, pressure


def use_audio_samples_to_compute_SL_and_PSD(
    audio_dir,
    dataset,
    S_dB_re_V_per_μPa,
    gain_dB,
    c,
):
    """Use audio samples to compute source level and power spectral
    density for each recording in the dataset.

    Parameters
    ----------
    audio_dir : pathlib.Path()
        Path to directory containing audio files
    S_dB_re_V_per_μPa : float
        Hydrophone sensitivity [dB re V/Pa]
    gain_dB : float
        Gain applied prior to analog to digital conversion [dB]
    c : float
        Speed of sound [m/s]

    Returns
    -------
    results : dict
        Source levels, and power spectral densities by engine type,
        with intermediate values

    """
    results = {}
    for idx, row in dataset.iterrows():

        engine_type = row["engine_type"]
        if engine_type not in ENGINE_TYPES:
            continue

        distance = row["distance"]
        if distance == 0:
            continue

        # Compute source level, propagation loss, mean square pressure,
        # sound pressure level, and power spectral densitry
        audio_file = row["filename"]
        samples, sample_rate = sf.read(audio_dir / audio_file)
        SL, PL, MSP, SPL, pressure = compute_SL(
            samples, S_dB_re_V_per_μPa, gain_dB, distance, SPEED_OF_SOUND
        )
        f, PSD = signal.welch(pressure, fs=sample_rate, nperseg=sample_rate)
        # TODO: Move up to samples?
        if f.size == 0:
            # TODO: Remove
            breakpoint()
            continue

        # Assign and accumulate samples
        q = 100  # Downsample
        sample = {
            "audio_file": audio_file,
            "hex_id": row["hex_id"],
            "distance": distance,
            "sample_rate": sample_rate / q,
            "pressure": pressure[::q],
            "SL": SL,
            "PL": PL,
            "MSP": MSP,
            "SPL": SPL,
            "f": f,
            "PSD": PSD,
        }
        if engine_type not in results:
            results[engine_type] = {}
            results[engine_type]["f"] = f.copy()
            results[engine_type]["SL"] = SL
            results[engine_type]["PSD"] = PSD.copy()
            results[engine_type]["samples"] = [sample]

        else:
            results[engine_type]["SL"] += SL
            results[engine_type]["PSD"] += PSD
            results[engine_type]["samples"].append(sample)

    # Compute source level and power spectral density averages
    for engine_type in ENGINE_TYPES:
        n_samples = len(results[engine_type]["samples"])
        results[engine_type]["SL"] /= n_samples
        results[engine_type]["PSD"] /= n_samples

    return results


def write_SLs(results, engine_types, archive_dir, tex_file):
    """Write source levels for the specified engine types as a LaTeX
    table to specified file in the specified archive directory.

    Parameters
    ----------
    results : dict
        Source levels, and power spectral densities by engine type,
        with intermediate values
    engine_types : list(str)
        Engine types to write
    archive_dir : pathlib.Path()
        Path to archive directory
    tex_file : str
        Name of LaTeX file

    Returns
    -------
    None

    """
    with open(archive_dir / tex_file, "w") as f:

        # ̱Open environment
        line = "\\begin{tabular}{"
        for engine_type in engine_types:
            line += "c"
        line += "}\n"
        f.write(line)

        # ̱Label table
        f.write("  \\hline\n")
        line = "  "
        for engine_type in engine_types:
            if line != "  ":
                line += " & "
            line += f"\\textbf{{{engine_type[0:min(len(engine_type), 7)]}}}"
        line += " \\\\\n"
        f.write(line)
        f.write("  \\hline\n")
        f.write("  \\hline\n")

        # ̱Write at most ten samples for each engine type
        for iSmp in range(10):
            line = "  "
            for engine_type in engine_types:
                if line != "  ":
                    line += " & "
                samples = results[engine_type]["samples"]
                if iSmp < len(samples):
                    line += f"{samples[iSmp]['SL']:.1f}"
            line += " \\\\\n"
            f.write(line)
        f.write("  \\hline\n")

        # Write the average and number of samples for each engine type
        line = "  "
        for engine_type in engine_types:
            if line != "  ":
                line += " & "
            line += f"{results[engine_type]['SL']:.1f} ({len(results[engine_type]['samples'])})"
        line += " \\\\\n"
        f.write(line)
        f.write("  \\hline\n")

        # Close environment
        f.write("\\end{tabular}\n")


def plot_PSDs(results, plot_type, engine_types, archive_dir, plot_file):
    """Plot example pressure time series, or example or average power
    spectral densities for the specified engine types, and save the
    figure to the specified file in the specified archive directory.

    Parameters
    ----------
    results : dict
        Source levels, and power spectral densities by engine type,
        with intermediate values
    plot_type : str
        Type of plot: "example_p_ts" (example pressure time series),
        "example_psd" (examples PSDs), or "average_psd" (averages
        PSDs)
    engine_types : list(str)
        Engine types to plot
    archive_dir : pathlib.Path()
        Path to archive directory
    plot_file : str
        Name of plot file

    Returns
    -------
    None

    """
    # Configure figure for subplots
    nRow = 2
    nCol = 3
    fig, axs = plt.subplots(nRow, nCol, figsize=(10, 5), layout="constrained")

    # Initialize common x and y axis limits
    if plot_type in ["example_psd", "average_psd"]:
        x0 = 2.0
        x1 = 2000.0
    y0 = float("inf")
    y1 = float("-inf")

    # Plot each engine type
    if plot_type in ["example_p_ts", "example_psd"]:
        hex_id = []
        SPL = []
    SL = []
    iTyp = -1
    for iRow in range(nRow):
        for iCol in range(nCol):
            iTyp += 1
            if iTyp == len(engine_types):
                axs[iRow, iCol].set_axis_off()
                continue

            if plot_type in ["example_p_ts", "example_psd"]:
                item = results[engine_types[iTyp]]["samples"][0]
                hex_id.append(item["hex_id"])  # Accumulate for labeling
            else:
                item = results[engine_types[iTyp]]

            if plot_type == "example_p_ts":

                # Plot pressure over the full sample time
                SPL.append(item["SPL"])  # Accumulate for labeling
                pressure = item["pressure"]
                t = np.arange(pressure.size) / item["sample_rate"]
                axs[iRow, iCol].plot(t, pressure / 1.0e6)
                axs[iRow, iCol].set_title(
                    f"{engine_types[iTyp][0:min(len(engine_types[iTyp]), 13)]} ({hex_id[iTyp]})",
                    loc="left",
                )
                xlim = axs[iRow, iCol].get_xlim()
                x0 = xlim[0]
                x1 = xlim[1]

            else:

                # Plot spectrum over the x (frequency) limits
                SL.append(item["SL"])  # Accumulate for labeling
                f = item["f"]
                PSD = item["PSD"]
                idx = np.logical_and(x0 <= f, f <= x1)
                axs[iRow, iCol].loglog(f[idx], PSD[idx])
                if plot_type == "example_psd":
                    axs[iRow, iCol].set_title(
                        f"{engine_types[iTyp][0:min(len(engine_types[iTyp]), 12)]} ({hex_id[iTyp]})",
                        loc="left",
                    )
                else:
                    axs[iRow, iCol].set_title(f"{engine_types[iTyp]}", loc="left")

            # Find common y limits
            ylim = axs[iRow, iCol].get_ylim()
            y0 = min(y0, ylim[0])
            y1 = max(y1, ylim[1])

    # Set common y limits, and annotate each subplot ...
    iTyp = -1
    for iRow in range(nRow):
        for iCol in range(nCol):
            iTyp += 1
            if iTyp == len(engine_types):
                continue

            if plot_type == "example_p_ts":
                axs[iRow, iCol].set_ylim(y0, y1)
                xW = x1 - x0
                yW = y1 - y0
                aT = axs[iRow, iCol].text(
                    x0 + 0.05 * xW, y0 + 0.05 * yW, f"{SPL[iTyp]:.1f} dB re µPa²"
                )

            else:
                axs[iRow, iCol].set_ylim(y0, y1)
                aT = axs[iRow, iCol].text(x0, 2 * y0, f"{SL[iTyp]:.1f} dB re µPa²m²")

    # Label the axes of the figures of subplots
    if plot_type == "example_p_ts":
        xL = fig.supxlabel("Time [s]", fontweight="semibold")
        yL = fig.supylabel("Pressure [Pa]", fontweight="semibold")

    else:
        xL = fig.supxlabel("Frequency [Hz]", fontweight="semibold")
        yL = fig.supylabel("Pressure Spectral Density [µPa²/Hz]", fontweight="semibold")

    # Save the figure, then block for user input
    plot_path = archive_dir / plot_file
    plt.savefig(plot_path, format=plot_path.suffix.replace(".", ""))
    plt.show()


def main():

    # TODO: Create a command line interface

    # Read the dataset and append the engine type
    csv_path = ARCHIVE_DIR / DATASET_CSV
    dataset = pd.read_csv(csv_path)
    dataset["engine_type"] = dataset["filename"].apply(lambda fn: fn.split("_")[2])

    # Use audio samples to compute source level and power spectral
    # density for each recording in the dataset
    audio_dir = (ARCHIVE_DIR / DATASET_DIR,)
    S_dB_re_V_per_μPa = AUDIOMOTH_SENSITIVITY
    gain_dB = AUDIOMOTH_GAIN
    c = SPEED_OF_SOUND
    results = use_audio_samples_to_compute_SL_and_PSD(
        audio_dir,
        dataset,
        S_dB_re_V_per_μPa,
        gain_dB,
        c,
    )

    # Write source levels for the specified engine types as a LaTeX
    # table
    tex_file = DATASET_CSV.replace(".csv", "_SLs.tex")
    write_SLs(results, ENGINE_TYPES, ARCHIVE_DIR, tex_file)

    # Plot example pressure time series for all engine types
    plot_type = "example_p_ts"
    plot_file = DATASET_CSV.replace(".csv", f"_{plot_type}.pdf")
    plot_PSDs(results, plot_type, ENGINE_TYPES, ARCHIVE_DIR, plot_file)

    # Plot example power spectral densities for all engine types
    plot_type = "example_psd"
    plot_file = DATASET_CSV.replace(".csv", f"_{plot_type}.pdf")
    plot_PSDs(results, plot_type, ENGINE_TYPES, ARCHIVE_DIR, plot_file)

    # Plot average power spectral densities for all engine types
    plot_type = "average_psd"
    plot_file = DATASET_CSV.replace(".csv", f"_{plot_type}.pdf")
    plot_PSDs(results, plot_type, ENGINE_TYPES, ARCHIVE_DIR, plot_file)

    return dataset, results


if __name__ == "__main__":
    dataset, results = main()
