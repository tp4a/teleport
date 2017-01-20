#!/bin/bash

SRV=all
if [ x$1 != x ]; then
	SRV=$1
fi

APP_PATH=/usr/local/eom/teleport

cd "${APP_PATH}"

# start teleport core server...
if [ $SRV == all ] || [ $SRV == core ] ; then
	echo -n "starting teleport core server ... "
	result=$( ps ax | grep "${APP_PATH}/bin/tp_core start" | grep -v grep | wc -l )
	if [ $result -gt 0 ]; then
		echo "already running, skip."
	else
		${APP_PATH}/bin/tp_core start

		result=$( ps ax | grep "${APP_PATH}/bin/tp_core start" | grep -v grep | wc -l )
		if [ ! $result -gt 0 ]; then
			echo -e "\e[31m[FAILED]\033[0m"
		else
			echo -e "\e[32m[done]\033[0m"
		fi
	fi
fi


# start web
if [ $SRV == all ] || [ $SRV == web ] ; then
	echo -n "starting teleport web ... "
	result=$( ps ax | grep "${APP_PATH}/bin/tp_web start" | grep -v grep | wc -l )
	if [ $result -gt 0 ]; then
		echo "already running, skip."
	else
		${APP_PATH}/bin/tp_web start

		result=$( ps ax | grep "${APP_PATH}/bin/tp_web start" | grep -v grep | wc -l )
		if [ ! $result -gt 0 ]; then
			echo -e "\e[31m[FAILED]\033[0m"
		else
			echo -e "\e[32m[done]\033[0m"
		fi
	fi
fi
