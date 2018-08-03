# Copyright 1999-2018 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI="6"
UNIPATCH_STRICTORDER="1"
ETYPE="sources"
K_WANT_GENPATCHES="base extras experimental"
K_GENPATCHES_VER="17"

SPLASH_PATCH="linux-4.15-bootsplash-patches-and-Makefile-fix.patch"
SPL_PATCH_URI="mirror://gentoo/${SPLASH_PATCH}.gz"

inherit kernel-2
detect_version
detect_arch

KEYWORDS="~alpha ~amd64 ~arm ~arm64 ~hppa ~ia64 ~mips ~ppc ~ppc64 ~s390 ~sh ~sparc ~x86"
HOMEPAGE="https://dev.gentoo.org/~mpagano/genpatches
	https://github.com/philmmanjaro/linux-bootsplash"
IUSE="experimental"

DESCRIPTION="Full sources including the Gentoo patchset for the ${KV_MAJOR}.${KV_MINOR} kernel tree"
SRC_URI="${KERNEL_URI} ${GENPATCHES_URI} ${ARCH_URI} ${SPL_PATCH_URI}"

K_EXTRAELOG="This is the bleeding-edge mainline gentoo-sources kernel
with the linux bootsplash patches on top (see tools/bootsplash).  You
need to enable CONFIG_BOOTSPLASH and build the splash file using the
script in the above directory (a sample tux bootsplash is provided).
Then install the splash file as shown and add the cmdline parameter."

src_unpack() {
	# need to unpack manually due to patch reqs below
	unpack ${SPLASH_PATCH}.gz

	kernel-2_src_unpack
}

src_prepare() {
	ebegin "Applying kernel bootsplash patches"
		EPATCH_OPTS="-F3"
		epatch "${WORKDIR}"/${SPLASH_PATCH} || die "splash patch failed!"
		cp "${FILESDIR}"/*.gif "${S}"/tools/bootsplash/
		epatch "${FILESDIR}"/4.15.14/*
	eend $? || return

	kernel-2_src_prepare
}

pkg_postinst() {
	kernel-2_pkg_postinst
	einfo ""
	einfo "To configure the bootsplash, copy the file and add cmdline:"
	einfo ""
	einfo "  Splash-file under /lib/firmware/mypath/myfile"
	einfo "  Cmdline: bootsplash.bootfile=mypath/myfile"
	einfo ""
	einfo "For more info on this patchset, and how to report problems, see:"
	einfo "${HOMEPAGE}"
}

pkg_postrm() {
	kernel-2_pkg_postrm
}
