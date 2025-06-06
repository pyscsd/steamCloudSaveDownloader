FROM alpine:3.20

ARG SCSD_VERSION

# TODO Use pypi add auto update env
# TODO: Dynamic tag version
RUN apk --no-cache add \
    tzdata \
    python3 \
    pipx && \
    pipx install scsd${SCSD_VERSION:+==}${SCSD_VERSION:-} --global && \
    mkdir /data && \
    mkdir /config

COPY docker/entry.sh /root/entry.sh
COPY docker/run.sh /opt/run.sh
COPY docker/scsd_auth /usr/local/bin/scsd_auth

VOLUME ["/data", "/config"]

ENTRYPOINT ["/bin/sh", "/root/entry.sh"]
