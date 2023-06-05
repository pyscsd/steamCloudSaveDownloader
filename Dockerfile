FROM alpine:3.17

# TODO Use pypi add auto update env
# TODO: Dynamic tag version
RUN apk --no-cache add \
    python3 \
    py3-pip && \
    pip install --no-cache-dir scsd && \
    mkdir /data && \
    mkdir /config

COPY docker/entry.sh /root/entry.sh
COPY docker/run.sh /opt/run.sh

VOLUME ["/data", "/config"]

ENTRYPOINT ["/bin/sh", "/root/entry.sh"]
