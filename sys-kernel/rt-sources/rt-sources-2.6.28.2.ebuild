# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /var/cvsroot/gentoo-x86/sys-kernel/tuxonice-sources/tuxonice-sources-2.6.26.ebuild,v 1.2 2008/07/25 13:52:53 nelchael Exp $

K_NOUSENAME="yes"
K_NOSETEXTRAVERSION="yes"
K_SECURITY_UNSUPPORTED="1"
ETYPE="sources"
inherit kernel-2
detect_version

DESCRIPTION="Full (vanilla) sources for the kernel, with rt_user_sched patch."
HOMEPAGE="http://www.kernel.org"
SRC_URI="${KERNEL_URI}"

KEYWORDS="-alpha ~amd64 ~arm ~hppa ~ia64 ~ppc ~ppc64 ~sh ~sparc ~x86"
IUSE=""

RT_TARGET="2.6.28.2"
UNIPATCH_LIST="${FILESDIR}/${PN}-rt_user_sched.patch"
SRC_URI="${KERNEL_URI}"

K_EXTRAELOG="If there are issues with this kernel, please direct any
queries to http://lkml.org/"

pkg_postinst() {
	kernel-2_pkg_postinst
	elog ""
	elog "Note that the pam limits.conf method for allowing normal users"
	elog "to set realtime (SCHED_FIFO) priorities is no longer enough."
	elog "In order to enable realtime scheduling in newer kernels, you"
	elog "need to decrease the value in:"
	elog "    /sys/kernel/uids/0/cpu_rt_runtime"
	elog "and increase the value for your own UID.  Something like 450000"
	elog "for each one should suffice to get started.  You will also need"
	elog "the following kernel options enabled:"
	elog "    CONFIG_GROUP_SCHED=y"
	elog "    CONFIG_FAIR_GROUP_SCHED=y"
	elog "    CONFIG_RT_GROUP_SCHED=y"
	elog "    CONFIG_USER_SCHED=y"
	elog "For more info on realtime scheduling in the kernel, see:"
	elog "    /usr/src/linux/Documentation/scheduler/sched-rt-group.txt"
	elog ""
}
