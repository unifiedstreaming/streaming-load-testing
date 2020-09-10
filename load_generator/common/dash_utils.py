import requests
import time
import logging
import random

logger = logging.getLogger(__name__)


HIGHEST_BITRATE = "highest_bitrate"
LOWEST_BITRATE = "lowest_bitrate"

LOGGER_SEGMENTS = True


def get_segment_url(ism_url, base_url, media_segment):
    return(
        f"{ism_url}/{base_url}{media_segment}"
    )


def create_segment_timeline(
        ism_url, base_url, media_segment, time, segment_duration):
    url = get_segment_url(ism_url, base_url, media_segment)
    segment = {}
    segment["time"] = time
    segment["url"] = url
    segment["duration"] = segment_duration
    return segment


def create_segment(
    media_segment, ism_url, protocol, time, segment_duration,
        segment_timeline):

    segment = create_segment_timeline(
        ism_url,
        protocol,
        media_segment,
        time,
        segment_duration
    )
    segment_timeline.append(segment)
    time = time + segment_duration
    return time, segment_timeline


def create_segments_timeline(
        ism_url, protocol, media, representation, timeline):
    """
    host: string
    ism_file: string
    base_url: string
    representation: string
    timeline: SegmentTimeline object from MPEGDASHParser
    """
    segment_timeline = []
    time = 0
    media_repr = media.replace("$RepresentationID$", representation)
    for segment in timeline.Ss:
        segment_duration = segment.d
        if segment.t is not None and segment.r is not None:
            time = segment.t
            media_segment = media_repr.replace("$Time$", str(time))
            r = segment.r + 1
            for i in range(0, r):
                time, segment_timeline = create_segment(
                    media_segment, ism_url,
                    protocol,
                    time,
                    segment_duration,
                    segment_timeline
                )
                media_segment = media_repr.replace("$Time$", str(time))
        elif segment.t is None and segment.r is None:
            media_segment = media_repr.replace("$Time$", str(time))
            time, segment_timeline = create_segment(
                media_segment, ism_url,
                protocol,
                time,
                segment_duration,
                segment_timeline
            )
        elif segment.t is not None and segment.r is None:
            time = segment.t
            media_segment = media_repr.replace("$Time$", str(time))
            time, segment_timeline = create_segment(
                media_segment, ism_url,
                protocol,
                time,
                segment_duration,
                segment_timeline
            )
        else:
            r = segment.r + 1
            for i in range(0, r):
                media_segment = media_repr.replace("$Time$", str(time))
                time, segment_timeline = create_segment(
                    media_segment, ism_url,
                    protocol,
                    time,
                    segment_duration,
                    segment_timeline
                )
    return segment_timeline


def prepare_playlist(ism_url, mpd):
    """
    mpd: MPEGDASHParser object
    Returns
    all_reprs: all available representation from MPD manifest
    period_s: dict of timelines for each representation and dict of bitrates
    available
    """
    logger.info("Preparing timeline...")
    all_reprs = []
    period_s = {}
    dir_mpd = dir(mpd)
    if "periods" in dir_mpd:
        for period in mpd.periods:
            base_urls = (period.base_urls)
            protocol = base_urls[0].base_url_value  # only dash/ is in index 0
            period_s["repr"] = {}
            period_s["abr"] = {}

            for adapt_set in period.adaptation_sets:
                timeline = []
                content_type = adapt_set.content_type
                period_s["abr"][content_type] = {}
                period_s["abr"][content_type]["representation"] = []
                period_s["abr"][content_type]["bandwidth"] = []
                media = adapt_set.segment_templates[0].media
                timeline = adapt_set.segment_templates[0].segment_timelines[0]
                timescale = adapt_set.segment_templates[0].timescale
                for repr in adapt_set.representations:
                    all_reprs.append(repr)
                    respresentation = repr.id
                    bandwidth = repr.bandwidth
                    content_type = adapt_set.content_type
                    segments_urls = create_segments_timeline(
                        ism_url, protocol, media, respresentation, timeline
                    )
                    number_segments = len(segments_urls)
                    period_s["repr"][respresentation] = {}
                    period_s["repr"][respresentation]["timeline"] = segments_urls
                    period_s["repr"][respresentation]["bandwidth"] = bandwidth
                    period_s["repr"][respresentation]["contentType"] = content_type
                    period_s["repr"][respresentation]["timescale"] = timescale
                    period_s["repr"][respresentation]["size"] = number_segments
                    period_s["abr"][content_type]["representation"].append(respresentation)
                    period_s["abr"][content_type]["bandwidth"].append(bandwidth)

        return all_reprs, period_s
    else:
        return 0, 0


def get_segment_duration(period_segments, chosen_quality, index):
    duration = period_segments["repr"][chosen_quality]["timeline"][index]["duration"]
    timescale = period_segments["repr"][chosen_quality]["timescale"]
    segment_duration = duration/timescale
    return segment_duration


def simple_playback(self, period_segments, chosen_video, chosen_audio, delay):
    number_video_segments = period_segments["repr"][chosen_video]["size"]
    for i in range(0, number_video_segments - 1):
        video_segment = period_segments["repr"][chosen_video]["timeline"][i]["url"]
        self.client.get(video_segment, name="merged")
        if LOGGER_SEGMENTS:
            print(video_segment)
        segment_duration = get_segment_duration(
            period_segments, chosen_video, i
        )
        if delay:
            logger.info(f"Sleeping client for: {segment_duration} seconds")
            self._sleep(segment_duration)
        else:
            pass
        for j in range(0, 2):
            audio_segment = period_segments["repr"][chosen_audio]["timeline"][i + j]["url"]
            self.client.get(audio_segment, name="merged")
            if LOGGER_SEGMENTS:
                print(audio_segment)

            segment_duration = get_segment_duration(
                period_segments, chosen_video, i
            )
    logger.info("******* Finished playing the whole timeline *******")


def simple_live_playback(self, period_segments, chosen_video, chosen_audio, delay):
    number_video_segments = period_segments["repr"][chosen_video]["size"]
    for i in range(0, int(number_video_segments/2) - 1):
        video_segment = period_segments["repr"][chosen_video]["timeline"][i]["url"]
        response = self.client.get(video_segment)
        period_segments["repr"][chosen_video]["timeline"].pop(i)
        if LOGGER_SEGMENTS:
            print(video_segment)
            print(response.status_code)
        segment_duration = get_segment_duration(
            period_segments, chosen_video, i
        )
        if delay:
            logger.info(f"Sleeping client for: {segment_duration} seconds")
            self._sleep(segment_duration)
        else:
            pass
        for j in range(0, 2):
            audio_segment = period_segments["repr"][chosen_audio]["timeline"][i + j]["url"]
            self.client.get(audio_segment)
            if LOGGER_SEGMENTS:
                print(audio_segment)
            segment_duration = get_segment_duration(
                period_segments, chosen_video, i
            )
    return period_segments
    logger.info("******* Finished playing the whole timeline *******")


def simple_buffer(self, segment_count, buffer_size, segment_duration):
    min_buffer = buffer_size/2
    if segment_count >= min_buffer:
        # wait for the last segment duration
        logger.info(f"Buffering for {segment_duration} seconds ")
        time.sleep(segment_duration)
        self._sleep(segment_duration)
        segment_count = 0
    return segment_count


def get_channel_rate(http_response):
    """
    Calculate channel_rate based on HTTP request
    http_response: requests.response object
    return:
    chnnel_rate [kbps]
    download_duration of segment:  [seconds]
    """
    channel_rate = None
    download_duration = None
    content_length = None
    code = http_response.status_code
    if code == 200:
        content_length = http_response.headers['Content-Length']
        content_length = int(content_length)
        elapsed = http_response.elapsed
        if elapsed.seconds is not None:
            microseconds = elapsed.microseconds
            seconds = elapsed.seconds
            microseconds = microseconds / 1000000  # microseconds to seconds
            download_duration = microseconds + seconds  # [seconds]
            content_length = content_length * 8  # KB to kilobits
            channel_rate = content_length / (download_duration * 1000)  # [kbps]
    else:
        logger.error(f"Error request with code: {code} ")
        channel_rate = 0
        content_length = None
        download_duration = None

    return channel_rate, download_duration


def buffer_model(
        self, buffer_level, segment_duration, download_duration, max_buffer):
    """
    self: locust TaskSequence object
    buffer_level at epoch t: float [seconds]
    segment_duration: float [seconds]
    download_duration of segment t [seconds]
    max_buffer: int [seconds]
    Returns:
    updated buffer_level
    """
    logger.info(f"Buffer level: {buffer_level} seconds")
    delta_t = buffer_level - download_duration + segment_duration - max_buffer
    delta_t = abs(delta_t)
    diff = buffer_level - download_duration + segment_duration
    # Update buffer level
    buffer_level = buffer_level + segment_duration - download_duration

    if (diff < max_buffer):
        # Request (t + 1)-th segment
        return buffer_level
    else:
        buffer_level -= delta_t  # Creates playback
        logger.info(f"Buffering for {delta_t} seconds")
        self._sleep(delta_t)
        time.sleep(delta_t)  # Wait before (t + 1)-th segment is requested
        return buffer_level


def playback_w_buffer(
        self, period_segments, chosen_video, chosen_audio, max_buffer=10):
    """
    Apply buffer by max_buffer parameter
    """
    if isinstance(max_buffer, int):
        if LOGGER_SEGMENTS:
            logger.info(f"Buffer size: {max_buffer}")
        segment_count = 1  # empty buffer initialized
        buffer_level = 0  # buffer starts empty
        number_video_segments = period_segments["repr"][chosen_video]["size"]
        segments = period_segments["repr"]

        for i in range(0, number_video_segments - 1):
            video_segment = segments[chosen_video]["timeline"][i]["url"]
            logger.info(video_segment)
            response = self.client.get(video_segment, name="merged")
            channel_rate, download_duration = get_channel_rate(response)
            segment_duration = get_segment_duration(
                period_segments, chosen_video, i
            )
            if LOGGER_SEGMENTS:
                logger.info(f"Video segment duration: {segment_duration} seconds")
            buffer_level = buffer_model(
                self,
                buffer_level, segment_duration, download_duration, max_buffer
            )
            segment_count += i
            if LOGGER_SEGMENTS:
                logger.info(f"Number of segments in buffer: {segment_count}")
            for j in range(0, 2):
                audio_segment = segments[chosen_audio]["timeline"][i+j]["url"]
                logger.info(audio_segment)
                self.client.get(audio_segment, name="merged")
                segment_duration = get_segment_duration(
                    period_segments, chosen_audio, i+j
                )
                if LOGGER_SEGMENTS:
                    logger.info(
                        f"Audio segment duration : {segment_duration} seconds"
                    )

    else:
        logger.error("Your buffer size needs to be an integer")
        return


def select_representation(abr, option):
    """
    Select AdaptationSet with minimum or maximum bitrate
    abr: dictionary with represenation[] and bandwidths[]
    option: int 0-> lowest bitrate, 1-> highest bitrate
    """
    selected_audio = None
    selected_video = None
    slected_type = ["audio", "video"]
    selected_representation = []
    for type_content, content in abr.items():
        if type_content in slected_type:

            if option == HIGHEST_BITRATE:
                bitrate = max(content["bandwidth"])
            elif option == LOWEST_BITRATE:
                bitrate = min(content["bandwidth"])
            else:
                bitrate = random.choice(content["bandwidth"])

            index = content["bandwidth"].index(bitrate)
            representation = content["representation"][index]
            if type_content == "video":
                selected_video = representation
                selected_representation.append(selected_video)
            elif type_content == "audio":
                selected_audio = representation
                selected_representation.append(selected_audio)
            else:
                pass
    return selected_representation
