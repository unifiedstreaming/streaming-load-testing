import os
import sys
import logging

logger = logging.getLogger(__name__)

MANIFEST_FILE = None

if "mode" in os.environ:
    if os.environ["mode"] not in ["vod", "live"]:
        logger.error("That is an incorrect input variable for 'mode'")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    else:
        mode = os.environ.get("mode")
        print(f"The selected 'mode' variable is: {mode}")

else:
    print("You should specify the mode: 'vod' or 'live'")
    try:
        sys.exit(1)
    except SystemExit:
        os._exit(1)

if "play_mode" in os.environ:
    if os.environ["play_mode"] not in ["only_manifest", "full_playback", "random_segments"]:
        print(
            "You should specify a correct variable for 'play_mode' ENV"
            " variable: 'only_manifest', 'full_playback', 'random_segments'"
        )
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    else:
        play_mode = os.environ.get("play_mode")
        print(f"The selected 'play_mode' variable is: {play_mode}")

else:
    # Default behaviour if play_mode is not set
    os.environ["play_mode"] = "full_playback"
    print("Default play_mode is set to:  'full_playback'")

if "bitrate" in os.environ:
    if os.environ["bitrate"] not in ["highest_bitrate", "lowest_bitrate", "random_bitrate"]:
        print(
            "You should specify a correct variable for 'bitrate' ENV"
            " variable: highest_birtate, lowest_bitrate, random_bitrate"
        )
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    else:
        bitrate = os.environ.get("bitrate")
        print(f"The selected 'bitrate' variable is: {bitrate}")

else:
    # Default behaviour if bitrate is not set
    os.environ["bitrate"] = "highest_bitrate"
    print(
        "'bitrate' ENV variable is not set. Default 'bitrate' is set to:  "
        "'highest_bitrate'"
    )

# Create list of possible buffer_size
list_input = str(list(range(0, 10)))
if "buffer_size" in os.environ:
    if os.environ["buffer_size"] not in list_input:
        print(
            "You should specify a correct variable for 'buffer_size' ENV"
            " variable: integers from 0 to 10"
        )
        try:
            sys.exit(1)
        except SystemExit:
            os._exit(1)
    else:
        buffer_size = os.environ.get("buffer_size")
        print(f"The selected 'buffer_size' variable is: {buffer_size}")
else:
    os.environ["buffer_size"] = "0"
    print(
        "'buffer_size' ENV variable is not set. Default 'buffer_size'"
        "is set to: 0"
    )

if ("time_shift" in os.environ) and (os.environ.get("mode") == "live"):
    if os.environ["time_shift"] not in ["-4", "-3", "-2", "-1", "0", "1"]:
        print(
            "You should specify a correct variable for 'time_shift' ENV"
            " int variable: -4, -3, 2, 1, 0, 1"
        )
        try:
            sys.exit(1)
        except SystemExit:
            os._exit(1)
    else:
        mode = os.environ.get("mode")
        print(f"Mode before starting time_shift is : {mode}")
        time_shift = os.environ.get("time_shift")
        print(f"The selected 'time_shift' variable is: {time_shift} with type: {type(time_shift)}")

elif ("time_shift" in os.environ) and (os.environ.get("mode") == "vod"):
    print(
        "'time_shift' ENV can only be used with mode=live"
    )
    try:
        sys.exit(1)
    except SystemExit:
        os._exit(1)
else:
    print("'time_shift' ENV variable is not set")


if "MANIFEST_FILE" not in os.environ:
    print("You are required to set MANIFEST_FILE ENV variable ")
    try:
        sys.exit(1)
    except SystemExit:
        os._exit(1)
else:
    MANIFEST_FILE = os.getenv('MANIFEST_FILE')
    print(f"**** The manifest file is: {MANIFEST_FILE} ****")
