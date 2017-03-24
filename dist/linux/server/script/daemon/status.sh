#!/bin/bash

APP_PATH=/usr/local/eom/teleport

result=$( ps ax | grep "${APP_PATH}/bin/tp_core start" | grep -v grep | wc -l )
if [ $result -gt 0 ]; then
	# echo "teleport core server is running."
	echo -e "teleport core server is \e[32mrunning\033[0m."
else
	# echo "teleport core server is not running."
	echo -e "teleport core server is \e[31mnot running\033[0m."
fi

result=$( ps ax | grep "${APP_PATH}/bin/tp_web start" | grep -v grep | wc -l )
if [ $result -gt 0 ]; then
	# echo "teleport web is running."
	echo -e "teleport web server is \e[32mrunning\033[0m."
else
	# echo "teleport web is not running."
	echo -e "teleport web server is \e[31mnot running\033[0m."
fi
