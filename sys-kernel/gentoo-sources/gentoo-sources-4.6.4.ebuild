# Copyright 1999-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI="5"
ETYPE="sources"
K_WANT_GENPATCHES="base extras experimental"
K_GENPATCHES_VER="5"

inherit eutils kernel-2
detect_version
detect_arch

KEYWORDS="~alpha ~amd64 ~arm ~arm64 ~hppa ~ia64 ~mips ~ppc ~ppc64 ~s390 ~sh ~sparc ~x86"
HOMEPAGE="https://dev.gentoo.org/~mpagano/genpatches"
IUSE="experimental"
DESCRIPTION="Full sources including the Gentoo patchset for the ${KV_MAJOR}.${KV_MINOR} kernel tree"

PATCHES=(
	"${FILESDIR}"/0001-PATCH-v1-ARM-dtsi-sun4i-Add-clocks-and-hardware-defs.patch
	"${FILESDIR}"/0002-PATCH-v1-ARM-dts-mk802-Switch-OTG-to-host-mode.patch
)

SRC_URI="${KERNEL_URI} ${GENPATCHES_URI} ${ARCH_URI}"

src_prepare() {
	[[ ${ARCH} == arm ]] && epatch "${PATCHES[@]}"
}

pkg_postinst() {
	kernel-2_pkg_postinst
	einfo "For more info on this patchset, and how to report problems, see:"
	einfo "${HOMEPAGE}"
}

pkg_postrm() {
	kernel-2_pkg_postrm
}
