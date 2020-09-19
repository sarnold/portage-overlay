#!/bin/bash

USB_DIR="/dev/usb"

#VERBOSE="true"
DEV_NAME="lp"

if [[ -d ${USB_DIR} ]]; then
	DEV_NUM=$(find "${USB_DIR}" -name "${DEV_NAME}"\* | wc -l)
	if [[ -n ${VERBOSE} ]]; then
		DEV_LIST=$(find ${USB_DIR} -name ${DEV_NAME}\*)
		echo "${DEV_NUM} ${DEV_NAME} devices found:"
		echo "${DEV_LIST}"
	else
		echo "${DEV_NUM}"
	fi
else
	echo "0"
fi
