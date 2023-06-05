#!/bin/sh

if [ -f /config/scsd.conf ]; then
    scsd -f /config/scsd.conf
elif [ -f /config/scsd.conf.default ]; then
    scsd -f /config/scsd.conf.default
else
    echo "No config. scsd not ran"
fi
