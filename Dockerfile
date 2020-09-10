FROM python:3.8-alpine
LABEL maintainer "Roberto Ramos <roberto@unified-streaming.com>"

# Install packages
RUN apk --no-cache add g++ zeromq-dev libffi-dev file make gcc musl-dev \
 && rm -f /var/cache/apk/*

# Copy locust and load emulation requirements
COPY requirements.txt /
COPY setup.py /
COPY README.rst /
COPY load_generator /load_generator


RUN apk add --no-cache -U --virtual build-deps \
      g++ \
    && python -m pip install --upgrade pip \
    && pip3 install -r /requirements.txt \
    && apk del build-deps \
    && rm -f /var/cache/apk/*

WORKDIR /load_generator

EXPOSE 8089 5557


ENTRYPOINT ["locust"]
