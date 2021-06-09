#!/bin/bash

TP_VER=3.5.6-rc6

if [ ! -d /usr/local/teleport/data/etc ]; then
    cp -R /root/teleport-server-linux-x64-${TP_VER}/data/tmp/etc /usr/local/teleport/data/etc
fi

if [ ! -d /usr/local/teleport/data/log ]; then
    mkdir /usr/local/teleport/data/log
fi

nohup /usr/local/teleport/bin/tp_core -d start 2>/dev/null 1>/dev/null &
/usr/local/teleport/bin/tp_web -d start 2>/dev/null 1>/dev/null
