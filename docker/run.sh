#!/bin/sh

if [ -f /config/scsd.conf ]; then
    CONFIG="/config/scsd.conf"
elif [ -f /config/scsd.conf.default ]; then
    CONFIG="/config/scsd.conf.default"
else
    echo "[run.sh] No config. scsd not ran"
    exit 1
fi

echo "[run.sh] Config specified ${CONFIG}"
scsd -f "${CONFIG}" $@
