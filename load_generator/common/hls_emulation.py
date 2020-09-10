import os
import m3u8
from locust import TaskSet, task
from load_generator.config import default
import logging
import random

logger = logging.getLogger(__name__)


MANIFEST_FILE = os.getenv('MANIFEST_FILE')
PLAY_MODE = os.getenv("play_mode")
BUFFER_SIZE = os.getenv("buffer_size")
BUFFER_SIZE = int(BUFFER_SIZE)  # Cast os.environ str to int
BITRATE = os.getenv("bitrate")


LOGGER_SEGMENTS = True


class class_hls_player(TaskSet):
    """
    Simple HLS emulation of a player
    Receives an M3U8 manifest (/.m3u8)
    """
    @task(1)
    def hls_player_child(self):
        print("HLS child player running ...")
        base_url = (f"{self.locust.host}/{MANIFEST_FILE}")

        # get master HLS manifest
        master_url = f"{base_url}"  # It must be a /.m3u8 Master playlist
        if LOGGER_SEGMENTS:
            print(master_url)

        if PLAY_MODE == "only_manifest":
            master_m3u8 = self.client.get(master_url, name="merged")
            m3u8.M3U8(content=master_m3u8.text, base_uri=base_url)

        elif PLAY_MODE == "full_playback":
            # Retrieve segments with an specific buffer size
            master_m3u8 = self.client.get(master_url, name="merged")
            parsed_master_m3u8 = m3u8.M3U8(content=master_m3u8.text, base_uri=base_url)

            variant = self.select_bitrate(parsed_master_m3u8)

            variant_url = "{base_url}/{variant}".format(base_url=base_url, variant=variant.uri)
            variant_m3u8 = self.client.get(variant_url, name="merged")
            parsed_variant_m3u8 = m3u8.M3U8(content=variant_m3u8.text, base_uri=base_url)

            # get all the segments
            for segment in parsed_variant_m3u8.segments:
                if LOGGER_SEGMENTS:
                    print(segment.absolute_uri)
                self.client.get(segment.absolute_uri, name="merged")
                if BUFFER_SIZE != 0:
                    self._sleep(BUFFER_SIZE)
        else:
            # Select random segments
            master_m3u8 = self.client.get(master_url, name="merged")
            parsed_master_m3u8 = m3u8.M3U8(content=master_m3u8.text, base_uri=base_url)

            variant = self.select_bitrate(parsed_master_m3u8)

            variant_url = "{base_url}/{variant}".format(base_url=base_url, variant=variant.uri)
            variant_m3u8 = self.client.get(variant_url, name="merged")
            parsed_variant_m3u8 = m3u8.M3U8(content=variant_m3u8.text, base_uri=base_url)

            # get random segments
            for segment in parsed_variant_m3u8.segments:
                segment = random.choice(parsed_variant_m3u8.segments)
                if LOGGER_SEGMENTS:
                    print(segment.absolute_uri)
                self.client.get(segment.absolute_uri, name="merged")
                if BUFFER_SIZE != 0 and isinstance(BUFFER_SIZE, int):
                    self._sleep(BUFFER_SIZE)

    def select_bitrate(self, parsed_master_m3u8):
        bandwidth_list = []
        for playlist in parsed_master_m3u8.playlists:
            bandwidth = playlist.stream_info.bandwidth
            bandwidth_list.append(bandwidth)

        if BITRATE == "highest_bitrate":
            max_bandwidth = bandwidth_list.index(max(bandwidth_list))
            variant = parsed_master_m3u8.playlists[max_bandwidth]
        elif BITRATE == "lowest_bitrate":
            min_bandwidth = bandwidth_list.index(min(bandwidth_list))
            variant = parsed_master_m3u8.playlists[min_bandwidth]
        else:
            # Select a random bitrate
            variant = random.choice(parsed_master_m3u8.playlists)

        return variant

    def simple_buffer(self, segment):
        seg_get = self.client.get(segment.absolute_uri, name="merged")
        sleep = segment.duration - seg_get.elapsed.total_seconds()
        self._sleep(sleep)
