# Copyright 1999-2019 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI="6"

ETYPE="sources"
#K_DEFCONFIG="gentoo-arm_defconfig"
UNIPATCH_STRICTORDER="1"
K_WANT_GENPATCHES="base extras experimental"
K_GENPATCHES_VER="9"

inherit kernel-2 eutils
detect_version
detect_arch

K_BRANCH_ID="${KV_MAJOR}.${KV_MINOR}"
SPLASH_PATCH="linux-5.1-bootsplash-patches-for-kernel-space-fbc.patch"
SPLASH_URI="https://dev.gentoo.org/~nerdboy/files/${SPLASH_PATCH}.gz"
LOGO_PATCH="linux-4.14-bootsplash-add-gentoo-logo-build-script.patch"

KEYWORDS="~alpha ~amd64 ~arm ~arm64 ~hppa ~ia64 ~mips ~ppc ~ppc64 ~s390 ~sh ~sparc ~x86"
HOMEPAGE="https://dev.gentoo.org/~mpagano/genpatches"

DESCRIPTION="Full sources for ${OKV} kernel plus gentoo, splash, and ARM64 device patches"
SRC_URI="
	${KERNEL_URI}
	${ARCH_URI}
	${GENPATCHES_URI}
	${SPLASH_URI}"

IUSE="experimental"

K_EXTRAELOG="This is mainline kernel splash and device/dts patches on the
full gentoo-sources kernel (intended for Allwinner boards like pine64
although it should work pretty much anywhere, eg, X1 Carbon).  A copy of
the latest config has been installed as ${K_DEFCONFIG}.
If you are reading this, you know what to do..."

RDEPEND=""
DEPEND="${RDEPEND}
	>=sys-devel/patch-2.7.4"

PATCHES=( "${FILESDIR}/${KV_MAJOR}.${KV_MINOR}/" )

src_unpack() {
	unpack ${SPLASH_PATCH}.gz
	kernel-2_src_unpack
}

src_prepare() {
	handle_genpatches
	eapply "${PATCHES[@]}"

	ebegin "Applying kernel bootsplash and makefile patches"
		EPATCH_OPTS="-F3 -b"
		epatch "${WORKDIR}"/${SPLASH_PATCH} || die "splash patch failed!"
		epatch "${FILESDIR}"/${LOGO_PATCH} || die "logo patch failed!"
		epatch "${FILESDIR}"/0001-tools-bootsplash-Makefile-fix-include-paths.patch
		cp "${FILESDIR}"/*.gif "${S}"/tools/bootsplash/
		eapply "${FILESDIR}"/${PN}-increase-max-arg-pages-to-64.patch
	eend $? || return

	# cleanup...
	rm -f "${WORKDIR}"/*bootsplash-patches-for-kernel-space-fbc*

	eapply_user

	[[ -n "${K_DEFCONFIG}" ]] && update_config
	kernel-2_src_prepare
}

pkg_postinst() {
	kernel-2_pkg_postinst
	einfo "For more info on this patchset, and how to report problems, see:"
	einfo "${HOMEPAGE}"
}

pkg_postrm() {
	kernel-2_pkg_postrm
}

update_config() {
	cp -f "${FILESDIR}"/${KV_MAJOR}.${KV_MINOR}/${K_DEFCONFIG} \
		"${S}"/arch/arm64/configs/ \
		|| die "failed to install ${K_DEFCONFIG}!"
}
