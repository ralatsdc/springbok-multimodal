#!/usr/bin/env python3
"""Convert AIFF file to HDF5 file."""
import argparse
from pathlib import Path

import h5py
import soundfile as sf

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "-r",
    "--rec-dir",
    metavar="REC_DIR",
    default="../recordings",
    help="directory containing audio recordings",
)
parser.add_argument("aiff_file", metavar="AIFF_FILE", help="input AIFF file")
args = parser.parse_args()

# Read AIFF file using soundfile
rec_path = Path(args.rec_dir)
data, samplerate = sf.read(rec_path / args.aiff_file)

# Create HDF5 file
hdf5_file = Path(args.aiff_file).stem + ".h5"
with h5py.File(rec_path / hdf5_file, "w") as hf:

    # Create a dataset for the audio data
    hf.create_dataset("audio_data", data=data)

    # Store the samplerate as an attribute
    hf.attrs["samplerate"] = samplerate
