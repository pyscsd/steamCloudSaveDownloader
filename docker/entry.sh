#!/bin/sh

PUID=${PUID:=1000}
PGID=${PGID:=1000}
CRON_VAR="${CRON_VAR:=39 */2 * * *}"
AUTO_UPDATE="${AUTO_UPDATE:=false}"

new_user () {
    id user > /dev/null 2> /dev/null
    USER_EXIST="$?"

    if [ "$USER_EXIST" -eq 0 ]; then
        echo "[entry.sh] User exist, skip creation"
        return
    fi

    addgroup -g "${PGID}" user
    adduser -h /user -g "" -s /bin/sh -G user -D -u "${PUID}" user
    echo "[entry.sh] Add user(${PUID}) and group(${PGID})"
}

set_permission () {
    echo "[entry.sh] Setting permission"
    chown user:user /data
    chown user:user /config
    chown user:user /opt/run.sh
}

set_cron () {
    echo "[entry.sh] Setting cron"

    if [ -f "/etc/crontabs/user" ]; then
        echo "[entry.sh] Crontab exist. Skipped"
        return
    fi

    echo "[entry.sh] Crontab schedule:  ${CRON_VAR}"
    echo "${CRON_VAR} /bin/sh /opt/run.sh" > /tmp/cron

    crontab -u user /tmp/cron
    rm /tmp/cron
}

setup_auto_update() {
    echo "[entry.sh] Setting up auto update"

    if [ "${AUTO_UPDATE}" = "false" ]; then
        crontab -r
        echo "[entry.sh] Auto update set to disabled"
        return
    fi

    cat /etc/crontabs/root | grep 'pip install -U scsd' > /dev/null 2> /dev/null
    retval=$?

    if [ $retval -eq 0 ]; then
        echo "[entry.sh] Auto update job exist->Skipped"
        return
    fi

    echo "27 */4 * * * pip install -U scsd" >> /etc/crontabs/root
    echo "[entry.sh] Auto update added to crontab"

}

gen_default_config () {
    if [ -f /config/scsd.conf ]; then
        echo "[entry.sh] Config exist. Skip default config creation"
        return
    fi

    if [ -f /config/scsd.conf.default ]; then
        echo "[entry.sh] Default config exist. Skip default config creation"
        return
    fi

    echo -e '[General]\nsave_dir = /data\n' > /config/scsd.conf.default
    chown user:user /config/scsd.conf.default
    echo "[entry.sh] Default config created"
}

create_scsd_dockerenv () {
    if [ -f "/.scsd_dockerenv" ]; then
        echo "[entry.sh] .scsd_dockerenv exist. Skipped"
        return
    fi
    echo "[entry.sh] Creating .scsd_dockerenv"
    touch "/.scsd_dockerenv"
}

new_user
set_permission
set_cron
setup_auto_update
gen_default_config
create_scsd_dockerenv

exec crond -f -d 8
