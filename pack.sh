#!/bin/sh
mkdir -p dist
pyinstaller --collect-all steamCloudSaveDownloader --onefile ./scsd --name scsd_x86_64
