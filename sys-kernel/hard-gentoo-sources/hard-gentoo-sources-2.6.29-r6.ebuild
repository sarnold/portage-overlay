# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

ETYPE="sources"
K_WANT_GENPATCHES="base extras"
K_GENPATCHES_VER="8"
inherit kernel-2
detect_version
detect_arch

KEYWORDS="~alpha ~amd64 ~arm ~hppa ~ia64 ~ppc ~ppc64 ~sh ~sparc ~x86"
IUSE=""
HOMEPAGE="http://dev.gentoo.org/~dsd/genpatches"

HGPV="${KV_MAJOR}.${KV_MINOR}.${KV_PATCH}-1"
HGPV_URI="http://dev.gentoo.org/~gengor/distfiles/${CATEGORY}/hardened-sources/hardened-patches-${HGPV}.extras.tar.bz2"
SRC_URI="${KERNEL_URI} ${HGPV_URI} ${GENPATCHES_URI} ${ARCH_URI}"

UNIPATCH_LIST="${DISTDIR}/hardened-patches-${HGPV}.extras.tar.bz2"
UNIPATCH_EXCLUDE="4201_fbcondecor-0.9.6.patch"

DESCRIPTION="Hardened version of the Gentoo patchset for the ${KV_MAJOR}.${KV_MINOR} kernel tree"
#SRC_URI="${KERNEL_URI} ${GENPATCHES_URI} ${ARCH_URI}"

pkg_postinst() {
	kernel-2_pkg_postinst
	einfo "For more info on this patchset, and how to report problems, see:"
	einfo "${HOMEPAGE}"
}
