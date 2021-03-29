import pytest
import os
os.environ["GEVENT_SUPPORT"] = "True"
os.environ["PYDEVD_USE_FRAME_EVAL"] = "NO"  # Set to remove GEVENT_SUPPORT support warning
# *** Import requirements for gevent warnings: https://github.com/gevent/gevent/issues/1016#issuecomment-328529454
import gevent.monkey
gevent.monkey.patch_all()
from requests.packages.urllib3.util.ssl_ import create_urllib3_context
create_urllib3_context()
# *** Ends import requirements for gevent
import requests
import subprocess
import json
from mpegdash.parser import MPEGDASHParser
from load_generator.common import dash_utils
from locust import HttpLocust, Locust, TaskSet, between
print(f"__file__{__file__}")
from locust.exception import InterruptTaskSet
os.environ["mode"] = "vod"
os.environ["MANIFEST_FILE"] = "video/ateam/ateam.ism/.m3u8"
from load_generator.common.dash_emulation import class_dash_player
from load_generator.common.hls_emulation import class_hls_player


@pytest.mark.parametrize("hostname,ism_path", [(
        'http://demo.unified-streaming.com',
        'video/ateam/ateam.ism'
    )
])
@pytest.mark.parametrize("streaming_output", ["m3u8", "mpd"])
@pytest.mark.parametrize("play_mode", [
    "only_manifest", "full_playback", "random_segments"
])
@pytest.mark.parametrize("bitrate", [
    "highest_bitrate", "lowest_bitrate", "random_bitrate"
])
@pytest.mark.parametrize("buffer_size", ["0"])  # ["0", "1", "2"])
def test_vod_dash_hls_sequence(
        hostname, ism_path, streaming_output, play_mode, bitrate, buffer_size):
    current_directory = os.getcwd()
    print(f"Current directory: {current_directory}")
    locust_str_cmd = (
        f"locust "
        f"-f {current_directory}/load_generator/locustfiles/vod_dash_hls_sequence.py"
        f" --no-web"
        f" -c 1"
        f" -r 1"
        f" --run-time 1s"
        f" --only-summary")
    locust_list_cmd = locust_str_cmd.split(' ')
    print(f"Locust command:\n {locust_list_cmd}")
    my_env = os.environ.copy()
    my_env["HOST_URL"] = hostname
    my_env["MANIFEST_FILE"] = f"{ism_path}/.{streaming_output}"
    my_env["mode"] = "vod"
    my_env["play_mode"] = play_mode
    my_env["bitrate"] = bitrate
    my_env["buffer_size"] = buffer_size  # os.environ requires a str

    print(
        f"my_env: HOST_URL={my_env['HOST_URL']}, "
        f"mode={my_env['mode']}, "
        f"MANIFEST_FILE={my_env['MANIFEST_FILE']}")
    process = subprocess.Popen(
        locust_list_cmd,
        env=my_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()
    print(f"stdout={stdout}")
    exit_code = process.returncode
    print(f"Return code: {exit_code}")
    json_error = stderr.decode('utf8').replace("'", '"')
    print(json_error)
    assert 0 == exit_code
