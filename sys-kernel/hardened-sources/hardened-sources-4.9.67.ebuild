# Copyright 1999-2018 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI="6"
ETYPE="sources"
K_WANT_GENPATCHES="base extras experimental"
K_GENPATCHES_VER="69"

inherit kernel-2 eutils
detect_version
detect_arch

GRSEC_PATCH="${P}.grsec.patch.gz"
GRSEC_URI="https://dev.gentoo.org/~nerdboy/files"
G_PATCH_URI="${GRSEC_URI}/${GRSEC_PATCH}"

KEYWORDS="~alpha ~amd64 ~arm ~arm64 ~hppa ~ia64 ~mips ~ppc ~ppc64 ~s390 ~sh ~sparc ~x86"
HOMEPAGE="https://dev.gentoo.org/~mpagano/genpatches"
IUSE="experimental"

DESCRIPTION="Full sources including the Gentoo and GRSEC patchsets for the ${KV_MAJOR}.${KV_MINOR} kernel tree"
SRC_URI="${KERNEL_URI} ${GENPATCHES_URI} ${ARCH_URI} ${G_PATCH_URI}"

UNIPATCH_LIST="${UNIPATCH_LIST} ${DISTDIR}/${GRSEC_PATCH}"

pkg_postinst() {
	kernel-2_pkg_postinst
	einfo "For more info on this patchset, and how to report problems, see:"
	einfo "${HOMEPAGE}"
}

pkg_postrm() {
	kernel-2_pkg_postrm
}
