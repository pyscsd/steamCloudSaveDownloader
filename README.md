# steamCloudSaveDownloader
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![Check and Build](https://github.com/pyscsd/steamCloudSaveDownloader/actions/workflows/check-test-build.yml/badge.svg)](https://github.com/pyscsd/steamCloudSaveDownloader/actions/workflows/check-test-build.yml/) [![Publish](https://github.com/pyscsd/steamCloudSaveDownloader/actions/workflows/publish.yml/badge.svg)](https://github.com/pyscsd/steamCloudSaveDownloader/actions/workflows/publish.yml/) [![PyPi](https://img.shields.io/pypi/v/scsd)](https://pypi.org/project/scsd/) [![GitHub Release](https://img.shields.io/github/v/release/pyscsd/steamCloudSaveDownloader)](https://github.com/pyscsd/steamCloudSaveDownloader/releases) [![Docker Hub](https://img.shields.io/docker/v/hhhhojeihsu/scsd?logo=docker&color=328fa8)](https://hub.docker.com/r/hhhhojeihsu/scsd)

Download/Backup Saves on Steam Cloud

## :warning: DISCLAIMER
- This program is not affiliated with Valve or Steam. Steam is a trademark of Valve Corporation.
- Even though this program is thoroughly tested and theoretically does not violate EULA. This program does not come with warranty and use at your own risk. More of this on [Rate Limit Section](#Rate-Limit)

## Description
For supported games, Steam will automatically upload game saves to the cloud. This is intended for seamless playing across multiple devices but NOT as a form of backup. Assume your game save is corrupted by the game itself or you perform something cannot be undone. Once you close the game Steam will automatically uploads newest(corrupted) game saves to the cloud. That is basically game over if you haven't backup your save or unplug your Internet cord before you close the game. This is when steamCloudSaveDownloader(abbreviated as scsd) come to the rescue.

You can view and download your save files stored on Steam cloud [here](https://store.steampowered.com/account/remotestorage). This program automatically crawls the webpages and download if the files are outdated. A number of copies are kept locally in case something goes wrong. You can rollback your saves whenever anything goes wrong.

## :warning: Limitation
- If the game does not support Steam Cloud then the file cannot be backuped. You should look for alternatives like [GameSave Manager](https://www.gamesave-manager.com/)
- File will be uploaded to Steam Cloud **after** you close the game. If the game save modification happens between a long game session without closing the game. Your last save point would be the last save uploaded to Steam Cloud and downloaded by scsd.
- You might want to increase the frequency of scsd run if you have multiple short gaming session. Please be aware of [Rate Limit](#Rate-Limit) and set an acceptable frequency in this case.

## Installation
This program is available on [PyPI](https://pypi.org/project/scsd/). All you have to do is install [Python](https://www.python.org/downloads/) and run.

```sh
pip install scsd
```

Linux and Windows executable can also be found on the [release page](https://github.com/pyscsd/steamCloudSaveDownloader/releases)

## Usage
Simply run `scsd -a <username>` to [login to Steam](#Authentication). Then run `scsd` to start downloading saves. The saves for each game will be stored within the `data` directory with the corresponding [AppID](https://steamdb.info/apps/). If rotation is specified the old version of the file will have suffix `.scsd_<version_num>` to the corresponding file name.

Please refer to [Scheduled Run](#Scheduled-Run) if you want to run scsd automatically at given time.

For more detail usages please reference [Command Arguments](https://github.com/pyscsd/steamCloudSaveDownloader/wiki/Command-Arguments) and [Config File](https://github.com/pyscsd/steamCloudSaveDownloader/wiki/Config-File)

## Authentication
By running `scsd -a <username>` scsd save a session file with NO password within. This session last approximately about a month if your IP has not been changed. Once expired scsd will notify you if the notification options are given.

## Notification
Right now scsd supports the following notification system whenever scsd finishes the download process or encountered error. Please refer to [Config File](https://github.com/pyscsd/steamCloudSaveDownloader/wiki/Config-File) for setting options
- Discord
- Script

## Scheduled Run
The saves will be download and saved locally only if you execute scsd. scsd relies on external scheduler to run automatically.

- For Windows users you can run it with [Task Scheduler](https://github.com/pyscsd/steamCloudSaveDownloader/wiki/Windows-Task-Scheduler)
- For Linux/Mac users you can run it with [cron](https://wiki.archlinux.org/title/cron)

## Rate Limit
Even though this program does not use Steam API directly. This program still complies to Steam maximum API calls limit (100,000) per day. This program will limit itself to 85% of the usage (which is 85,000). Once exceed the aforementioned limit, the program will stop sending requests to Steam.

In addition to that, the program will wait for a random amount of time (a few seconds) between each request. This will significantly lower chance for the program to be identified as DDoS attack and potentially ban your account. As a trade off, it might took awhile for all your cloud saves to be downloaded.

## Docker
Docker image is available at [Docker Hub](https://hub.docker.com/r/hhhhojeihsu/scsd). It has built in scheduler and will run scsd automatically at given time (At minute 39 past every 2nd hour).

Below is the minimal example for running within docker. This will bind mount the `data` directory and run the authentication process.

```sh
mkdir data
docker run -d --name scsd -v ./data:/data -v /etc/localtime:/etc/localtime:ro hhhhojeihsu/scsd:latest
docker exec -it scsd scsd_auth <username>
```

### Volumes
- `/data`: Where the save files and program related files are located
- `/config`: Where the configuration file is stored.

### Environment Variables
|Name        |Purpose|Default|
|------------|-------|-------|
|PUID        |Effective UID for scsd to run with|1000|
|PGID        |Effective GID for scsd to run with|1000|
|CRON_VAR    |Cron syntax for scheduled run|39 */2 * * *|
|AUTO_UPDATE |Set to `true` to enable scsd auto update|false|

## Special Thanks
