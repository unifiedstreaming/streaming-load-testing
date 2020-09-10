import os
import sys
import logging
from locust import TaskSequence, seq_task, TaskSet, task
from mpegdash.parser import MPEGDASHParser
from load_generator.common import dash_utils
from load_generator.config import default
import random
from locust.exception import StopLocust

logger = logging.getLogger(__name__)

MANIFEST_FILE = os.getenv('MANIFEST_FILE')
PLAY_MODE = os.getenv("play_mode")
BUFFER_SIZE = os.getenv("buffer_size")
BUFFER_SIZE = int(BUFFER_SIZE)  # Cast os.environ str to int
BITRATE = os.getenv("bitrate")

LOGGER = True


class class_dash_player(TaskSet):
    """
    Simple MPEG-DASH emulation of a player
    Receives an MPEG-DASH /.mpd manifest
    """
    base_url = None
    mpd_body = None
    mpd_object = None
    print("started task")

    @seq_task(1)
    def get_manifest(self):
        print("MPEG-DASH child player running ...")
        base_url = f"{self.locust.host}/{MANIFEST_FILE}"
        if LOGGER:
            print(base_url)
        self.base_url = f"{base_url}"  # It should already be a /.mpd
        logger.info(f"Requesting manifest: {base_url}")
        response_mpd = self.client.get(f"{base_url}", name="merged")
        self.mpd_body = response_mpd.text
        if response_mpd.status_code == 0 or response_mpd.status_code == 404:
            logger.info("Make sure your Manifest URI is reachable")
            try:
                sys.exit(1)
            except SystemExit:
                os._exit(1)
        else:
            pass

    @seq_task(2)
    def dash_parse(self, reschedule=True):
        """
        Parse Manifest file to MPEGDASHParser
        """
        logger.info("Obtained MPD body ")
        if self.mpd_body is not None:
            self.mpd_object = MPEGDASHParser.parse(self.mpd_body)
            print(f"self.mpd_object: {self.mpd_object}")
        else:
            # self.interrupt()
            pass

    @seq_task(3)
    def dash_playback(self):
        """
        Create a list of the avaialble segment URIs with
        its specific media representation
        """
        logger.info("Dash playback")
        all_reprs, period_segments = dash_utils.prepare_playlist(
            self.base_url, self.mpd_object
        )
        if all_reprs != 0 and period_segments != 0:
            selected_representation = dash_utils.select_representation(
                period_segments["abr"],
                BITRATE  # highest_bitrate, lowest_bitrate, random_bitrate
            )
            chosen_video = selected_representation[1]
            chosen_audio = selected_representation[0]
            if PLAY_MODE == "full_playback":
                if BUFFER_SIZE == 0:
                    dash_utils.simple_playback(
                        self,
                        period_segments,
                        chosen_video,
                        chosen_audio,
                        False  # Delay in between every segment request
                    )
                else:
                    dash_utils.playback_w_buffer(
                        self,
                        period_segments,
                        chosen_video,
                        chosen_audio,
                        BUFFER_SIZE
                    )
            elif PLAY_MODE == "only_manifest":
                self.get_manifest()
            else:
                # select random segments: one for audio content and second for
                # video
                video_timeline = period_segments["repr"][chosen_video]["timeline"]
                audio_timeline = period_segments["repr"][chosen_audio]["timeline"]
                video_segment = random.choice(video_timeline)
                audio_segment = random.choice(audio_timeline)
                logger.info(video_segment["url"])
                self.client.get(video_segment["url"])
                logger.info(audio_segment["url"])
                self.client.get(audio_segment["url"])
        else:
            print("Peridos not found in the MPD body")
