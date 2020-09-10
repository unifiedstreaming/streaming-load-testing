PROGRAM_FILES=./load_generator/*.py
TEST_FILES=./tests/*.py
VOD_CONTENT_FOLDER=content/vod-tos
LIVE_DOCKER_COMPOSE=content/live-demo/docker-compose.yml
UNIFIED_CAPTURE_FOLDER=./tests/unified_capture
OUTPUT_CAPTURE = urls_output.txt
ORIGIN_TAG=1.10.18

ifndef TAG
	TAG=latest
endif

all: test


.PHONY: init
init:
		pip3 install -r requirements.txt
		mkdir -p test-results


.PHONY: upload
upload: 
		python3 setup.py upload

# Coverage3 test
tests: $(TEST_FILES) $(PROGRAM_FILES)
		coverage3 run -m pytest

download_vod:
	wget "http://repository.unified-streaming.com/tears-of-steel.zip" -O tos.zip
	mkdir -p $(VOD_CONTENT_FOLDER)
	unzip tos.zip -d $(VOD_CONTENT_FOLDER)

vod_origin:
	docker run --rm -e USP_LICENSE_KEY=\${USP_LICENSE_KEY} \
	 -e DEBUG_LEVEL=warn -v ${PWD}/$(VOD_CONTENT_FOLDER):/var/www/unified-origin \
	 -p 80:80 unifiedstreaming/origin:${ORIGIN_TAG}

live_origin:
	docker-compose -f $(LIVE_DOCKER_COMPOSE) up


dry_run_unified_capture:
	rm -f $(UNIFIED_CAPTURE_FOLDER)/$(OUTPUT_CAPTURE)
	mkdir -p $(UNIFIED_CAPTURE_FOLDER)
	docker run --rm --entrypoint unified_capture -v ${PWD}:/data -w /data/  \
		unifiedstreaming/packager:$(ORIGIN_TAG) \
		--license-key=$(USP_LICENSE_KEY) -o $(UNIFIED_CAPTURE_FOLDER)/output.mp4 \
		https://demo.unified-streaming.com/video/ateam/ateam.ism/ateam.mpd \
		--dry_run >> $(UNIFIED_CAPTURE_FOLDER)/$(OUTPUT_CAPTURE)


.PHONY: env

env/bin/activate:
	test -d env || python3 -m venv env
	. env/bin/activate; \
	pip3 install wheel; \
	pip3 install -Ur requirements.txt

env: env/bin/activate

test: env
	. env/bin/activate; coverage run -m pytest -s

.PHONY: build

build:
	time docker build -t unified-streaming/streaming-load-testing:$(TAG) .


.PHONY: docker-stop

docker-stop:
	-docker stop unified-streaming/streaming-load-testing
	docker container prune -f


.PHONY: run

run:
ifneq ($(and $(ORIGIN), $(MANIFEST_FILE), $(LOCUST_FILE)}),)
	docker run \
		-e "HOST_URL=http://${ORIGIN}" \
		-e "MANIFEST_FILE=${MANIFEST_FILE}" \
		-e "mode=vod" \
		-e "play_mode=full_playback" \
		-e "bitrate=lowest_bitrate" \
		-p 8089:8089 \
		-v ${PWD}/test-results/:/test-results/ \
		unified-streaming/streaming-load-testing  \
		-f /load_generator/locustfiles/${LOCUST_FILE} \
		--no-web -c 1 -r 1 --run-time 10s --only-summary \
		--csv=../test-results/ouput_example 
else
	docker run  \
		-e "HOST_URL=https://demo.unified-streaming.com" \
		-e "MANIFEST_FILE=/video/ateam/ateam.ism/ateam.m3u8" \
		-e "mode=vod" \
		-e "play_mode=full_playback" \
		-e "bitrate=lowest_bitrate" \
		-p 8089:8089 \
		-v ${PWD}/test-results/:/test-results/ \
		unified-streaming/streaming-load-testing  \
    	-f /load_generator/locustfiles/vod_dash_hls_sequence.py \
		--no-web -c 1 -r 1 --run-time 10s --only-summary \
		--csv=../test-results/ouput_example 
endif



clean:
	rm -rf env
	rm -rf test-results
	find . -iname "*pycache*" -delete

