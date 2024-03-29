# Copyright 1999-2018 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI="6"

ETYPE="sources"
UNIPATCH_STRICTORDER="1"
K_WANT_GENPATCHES="base extras experimental"
K_GENPATCHES_VER="18"

inherit kernel-2 eutils
detect_version
detect_arch

K_BRANCH_ID="${KV_MAJOR}.${KV_MINOR}"
SPLASH_PATCH="linux-${K_BRANCH_ID}-bootsplash-patches-for-kernel-space-fbc.patch"
SPLASH_URI="mirror://gentoo/${SPLASH_PATCH}.gz"
LOGO_PATCH="linux-4.14-bootsplash-add-orchard-logo-build-script.patch"

KEYWORDS="~alpha ~amd64 ~arm ~arm64 ~hppa ~ia64 ~mips ~ppc ~ppc64 ~s390 ~sh ~sparc ~x86"
HOMEPAGE="https://dev.gentoo.org/~mpagano/genpatches"
IUSE="experimental"

DESCRIPTION="Full sources including the Gentoo patchset for the ${KV_MAJOR}.${KV_MINOR} kernel tree"
SRC_URI="${KERNEL_URI} ${GENPATCHES_URI} ${ARCH_URI} ${SPLASH_URI}"

RDEPEND=""
DEPEND="${RDEPEND}
	>=dev-vcs/git-1.8.2.1"

K_EXTRAELOG="This is the bleeding-edge mainline gentoo-sources kernel
with the linux bootsplash patches on top (see tools/bootsplash).  You
need to enable CONFIG_BOOTSPLASH and build the splash file using the
script in the above directory (a sample tux bootsplash is provided).
Then install the splash file as shown and add the cmdline parameter."

src_unpack() {
	# must unpack first manually and depend on git due to patch reqs below
	unpack ${SPLASH_PATCH}.gz

	kernel-2_src_unpack
}

src_prepare() {
	# We can't use unipatch or eapply here due to the git binary
	# diffs that always cause dry-run errors (even with --force).

	ebegin "Applying kernel bootsplash and makefile patches"
		EPATCH_OPTS="-F3 -b"
		epatch "${WORKDIR}"/${SPLASH_PATCH} || die "splash patch failed!"
		epatch "${FILESDIR}"/${LOGO_PATCH} || die "logo patch failed!"
		epatch "${FILESDIR}"/0001-tools-bootsplash-Makefile-fix-include-paths.patch
		cp "${FILESDIR}"/*.gif "${S}"/tools/bootsplash/

		eapply "${FILESDIR}"/${PN}-increase-max-arg-pages-to-64.patch
		if use arm64; then
			eapply "${FILESDIR}"/0001-Fix-build-error-in-arm64-VDSO-when-gold-linker-is-default.patch
		fi
	eend $? || return

	eapply_user

	# clean up workdir so we don't install patch cruft
	rm -f "${WORKDIR}"/*bootsplash-patches-for-kernel-space-fbc*
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
	einfo "  https://github.com/philmmanjaro/linux-bootsplash"
}

pkg_postrm() {
	kernel-2_pkg_postrm
}
