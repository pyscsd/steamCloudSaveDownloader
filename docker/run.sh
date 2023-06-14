#!/bin/sh

if [ -f /config/scsd.conf ]; then
    CONFIG="/config/scsd.conf"
elif [ -f /config/scsd.conf.default ]; then
    CONFIG="/config/scsd.conf.default"
else
    echo "No config. scsd not ran"
fi

scsd -f "${CONFIG}" $@
