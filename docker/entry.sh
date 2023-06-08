#!/bin/sh

PUID=${PUID:=1000}
PGID=${PGID:=1000}
CRON_VAR="${CRON_VAR:=39 */2 * * *}"
AUTO_UPDATE="${AUTO_UPDATE:=false}"

new_user () {
    id user > /dev/null 2> /dev/null
    USER_EXIST="$?"

    if [ "$USER_EXIST" -eq 0 ]; then
        echo "User exist, skip creation"
        return
    fi

    addgroup -g "${PGID}" user
    adduser -h /user -g "" -s /bin/sh -G user -D -u "${PUID}" user
    echo "Add user(${PUID}) and group(${PGID})"
}

set_permission () {
    echo "Setting permission"
    chown user:user /data
    chown user:user /config
    chown user:user /opt/run.sh
}

set_cron () {
    echo "Setting cron"

    if [ -f "/etc/crontabs/user" ]; then
        echo "Crontab exist. Skipped"
        return
    fi

    if [ -f /config/scsd.conf ]; then
        CONFIG="/config/scsd.conf"
    else
        CONFIG="/config/scsd.conf.default"
    fi
    echo "Crontab schedule:  ${CRON_VAR}"
    echo "${CRON_VAR} /bin/sh /opt/run.sh" > /tmp/cron

    crontab -u user /tmp/cron
    rm /tmp/cron
}

setup_auto_update() {
    echo "[Auto update] starting"

    if [ "${AUTO_UPDATE}" = "false" ]; then
        crontab -r
        echo "[Auto udpate] False->disabled"
        return
    fi

    cat /etc/crontabs/root | grep 'pip install -U scsd' > /dev/null 2> /dev/null
    retval=$?

    if [ $retval -eq 0 ]; then
        echo "[Auto udpate] Exist->Skipped"
        return
    fi

    echo "27 */4 * * * pip install -U scsd" >> /etc/crontabs/root
    echo "[Auto udpate] Added"

}

gen_default_config () {
    if [ -f /config/scsd.conf ]; then
        echo "Config exist skipped"
        return
    fi

    if [ -f /config/scsd.conf.default ]; then
        echo "Default config exist skipped"
        return
    fi

    echo -e '[Required]\nsave_dir = /data\n' > /config/scsd.conf.default
    chown user:user /config/scsd.conf.default
    echo "Default config created"
}

new_user
set_permission
set_cron
setup_auto_update
gen_default_config

exec crond -f -d 8
