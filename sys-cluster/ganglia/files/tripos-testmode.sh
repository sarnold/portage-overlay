#!/bin/bash

TRI_CFG=$(find /opt/tripos* -name triPOS.config)
MODE=$(grep -m1 testMode "${TRI_CFG}" | grep -o -e true -e false)

if [[ $MODE = "true" ]]; then
	echo "TRUE"
elif [[ $MODE = "false" ]]; then
	echo "FALSE"
else
	echo "Unknown mode found!! Check that ${TRI_CFG} is valid!"
	exit 1
fi
