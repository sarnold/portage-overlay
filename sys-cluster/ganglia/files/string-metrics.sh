#!/bin/bash
. /etc/profile

GMETRIC="/usr/bin/gmetric --tmax=660 --dmax=660"
ZT_DEV_NAME=$(ip link show | grep mode | sed 's/://g' | awk '{print $2}' | grep ^zt)

$GMETRIC --name="rc_crashed" --title="Number of crashed services" --type=string --value=$(rc-status | grep -o -q "crashed" | wc -l)
$GMETRIC --name="rc_stopped" --title="Number of stopped services" --type=string --value=$(rc-status | grep -o -q "stopped" | wc -l)
$GMETRIC --name="gitops_status" --title="Gitops daemon PPID" --type=string --value=$([[ -e /run/confd.pid ]] && pgrep -ai -F /run/confd.pid | cut -f1 -d" " || echo "NONE")
$GMETRIC --name="host_name" --title="Hostname" --type=string --value=$(uname -n)
$GMETRIC --name="device_id" --type=string --value=$(grep DEVICE_ID /etc/env.d/00device-id | cut -d'"' -f2)
$GMETRIC --name="lp_devices" --title="Local print devices" --type=string --value=$(/usr/bin/lp-device-check.sh)
$GMETRIC --name="zt_host_id" --type=string --value=$(zerotier-cli info | cut -d" " -f3)
$GMETRIC --name="zt_network_id" --type=string --value=$(zerotier-cli listnetworks | grep zt | cut -d" " -f3)
$GMETRIC --name="zt_ipv6_addr" --type=string --value=$(ip address show "${ZT_DEV_NAME}" 2>&1 | awk '/link / {print $2}'  | cut -d/ -f1)
$GMETRIC --name="default_root" --type=string --value=$(grep DEFAULT_ROOT /etc/profile.env | cut -d"'" -f2)
$GMETRIC --name="os_version" --title="Gentoo Release" --type=string --value=$(cat /etc/gentoo-release | cut -d" " -f5)
$GMETRIC --name="orchard_build" --title="OrchardOS Release" --type=string --value=$(cat /etc/orchard-release | cut -d" " -f3)
$GMETRIC --name="tripos_version" --title="TriPOS Version" --type=string --value=$(qlist -ICv tripos)
$GMETRIC --name="tripos_test_mode" --title="TriPOS Test Mode" --type=string --value=$(/usr/bin/tripos-testmode.sh)
$GMETRIC --name="selinux_policy" --type=string --value=$(grep SELINUXTYPE= /etc/selinux/config)
$GMETRIC --name="selinux_mode" --type=string --value=$(grep SELINUX= /etc/selinux/config)
