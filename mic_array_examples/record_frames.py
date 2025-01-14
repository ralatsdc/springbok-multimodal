#!/usr/bin/env python3
"""Create a recording with arbitrary duration.
"""
import argparse
from pathlib import Path
import tempfile
import queue
import sys

import progressbar
import sounddevice as sd
import soundfile as sf
import numpy  # Make sure NumPy is loaded before it is used in the callback

assert numpy  # avoid "imported but unused" message (W0611)


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


def print_banner(text):
    """Helper function to print a banner."""
    print("#" * len(text))
    print(text)
    print("#" * len(text))


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    "-l",
    "--list-devices",
    action="store_true",
    help="show list of audio devices and exit",
)
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser],
)
parser.add_argument(
    "-d", "--device", type=int_or_str, help="input device (numeric ID or substring)"
)
parser.add_argument("-r", "--samplerate", type=int, help="sampling rate")
parser.add_argument(
    "-c", "--channels", type=int, default=1, help="number of input channels"
)
parser.add_argument(
    "-f", "--format", type=str, default="AIFF", help='sound file format (e.g. "AIFF")'
)
parser.add_argument(
    "-t",
    "--subtype",
    type=str,
    default="PCM_16",
    help='sound file subtype (e.g. "PCM_16")',
)
parser.add_argument(
    "-g", "--samplegain", type=float, default=0.0, help="sample gain [db]"
)
parser.add_argument(
    "-i", "--sampleinterval", type=int, default=10, help="sample interval [s]"
)
parser.add_argument("filename", nargs="?", metavar="FILENAME", help="output audio file")
args = parser.parse_args(remaining)

q = queue.Queue()
d = {}
d["inpdata"] = []  # List of ndarray
d["frames"] = 0  # Number of frames


def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    adata = indata.copy() * (10.0 ** (args.samplegain / 10.0))
    q.put(adata.copy())
    d["inpdata"].append(adata.copy())
    d["frames"] += frames


try:
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, "input")
        # soundfile expects an int, sounddevice provides a float:
        args.samplerate = int(device_info["default_samplerate"])
        args.channels = int(device_info["max_input_channels"])

    suffix = f".{args.format}".lower()
    if args.filename is None:
        args.filename = tempfile.mktemp(
            prefix="delme_rec_unlimited_", suffix=suffix, dir=""
        )
    elif Path(args.filename).suffix != suffix:
        args.filename = f"{Path(args.filename).stem}{suffix}"

    # Initialize a progress bar
    samples = args.samplerate * args.sampleinterval  # Number of samples
    widgets = [
        " [",
        progressbar.Timer(format="elapsed time: %(elapsed)s"),
        "] ",
        progressbar.Bar("*"),
        " (",
        progressbar.ETA(),
        ") ",
    ]

    # Make sure the file is opened before recording anything:
    with sf.SoundFile(
        Path("../recordings") / args.filename,
        mode="x",
        samplerate=args.samplerate,
        channels=args.channels,
        format=args.format,
        subtype=args.subtype,
    ) as file:
        with sd.InputStream(
            samplerate=args.samplerate,
            device=args.device,
            channels=args.channels,
            callback=callback,
        ):
            print_banner("Press Ctrl+C to stop the recording")
            bar = progressbar.ProgressBar(max_value=samples, widgets=widgets).start()
            while d["frames"] / args.samplerate < args.sampleinterval:
                bar.update(min(samples, d["frames"]))
                file.write(q.get())

except KeyboardInterrupt:
    print("\nRecording finished: " + repr(args.filename))
    parser.exit(0)

except Exception as e:
    parser.exit(type(e).__name__ + ": " + str(e))
