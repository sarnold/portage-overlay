# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="3"

K_WANT_GENPATCHES="base extras"
K_GENPATCHES_VER="6"
UNIPATCH_STRICTORDER="yes"
K_SECURITY_UNSUPPORTED="1"
K_DEBLOB_AVAILABLE="1"

ETYPE="sources"
inherit kernel-2
detect_version
detect_arch

ASPM_TARGET="aspm-main"
ASPM_URI="mirror://gentoo/linux-${PV}-${ASPM_TARGET}.tar.gz"
UNIPATCH_LIST="${DISTDIR}/linux-${PV}-${ASPM_TARGET}.tar.gz"

DESCRIPTION="Full (gentoo-ish) sources for the kernel, with the main ASPM and atl1c patches."
HOMEPAGE="http://www.kernel.org"
SRC_URI="${KERNEL_URI} ${GENPATCHES_URI} ${ARCH_URI} ${ASPM_URI}"

KEYWORDS="~amd64 ~arm ~ppc ~pp64 ~x86"
IUSE=""

K_EXTRAELOG="If there are issues with this kernel, please direct any
queries to http://lkml.org/"

pkg_postinst() {
	kernel-2_pkg_postinst
	elog ""
	elog ""
}
