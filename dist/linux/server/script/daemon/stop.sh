#!/bin/bash

SRV=all
if [ x$1 != x ]; then
	SRV=$1
fi

APP_PATH=/usr/local/eom/teleport

# start teleport core server...
if [ $SRV == all ] || [ $SRV == core ] ; then
	echo -n "stoping teleport core server ... "
	result=$( ps ax | grep "${APP_PATH}/bin/tp_core start" | grep -v grep | wc -l )
	if [ $result -gt 0 ]; then
		ps ax | grep "${APP_PATH}/bin/tp_core start" | grep -v grep | kill `awk '{print $1}'`
		echo 'done.'
	else
		echo "not running, skip."
	fi
fi

# stop web
if [ $SRV == all ] || [ $SRV == web ] ; then
	echo -n "stoping teleport web ... "
	result=$( ps ax | grep "${APP_PATH}/bin/tp_web start" | grep -v grep | wc -l )
	if [ $result -gt 0 ]; then
		ps ax | grep "${APP_PATH}/bin/tp_web start" | grep -v grep | kill `awk '{print $1}'`
		echo 'done.'
	else
		echo "not running, skip."
	fi
fi
