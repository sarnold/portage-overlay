# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

UNIPATCH_STRICTORDER="yes"
K_SECURITY_UNSUPPORTED="1"

ETYPE="sources"
inherit kernel-2
detect_version
detect_arch

VIA_TARGET="via-c7_chrome9-lm_sensor.patch"
VIA_URI="mirror://gentoo/${VIA_TARGET}.bz2"
UNIPATCH_LIST="${DISTDIR}/${VIA_TARGET}.bz2"

DESCRIPTION="Full (vanilla) sources for the kernel, with the VIA C7 chrome9 and lm_sensor module patches."
HOMEPAGE="http://www.kernel.org"
SRC_URI="${KERNEL_URI} ${VIA_URI} ${ARCH_URI}"

KEYWORDS="~amd64 ~arm ~ppc ~pp64 ~x86"
IUSE=""

K_EXTRAELOG="If there are issues with this kernel, please direct any
queries to http://lkml.org/"

pkg_postinst() {
	kernel-2_pkg_postinst
	elog ""
	elog "Patches provided by http://sturmartillerie.org/linux/patches/"
	elog ""
}
