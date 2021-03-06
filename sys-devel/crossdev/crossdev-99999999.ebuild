# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI="6"

if [[ ${PV} == "99999999" ]] ; then
	inherit git-r3
	EGIT_REPO_URI="https://github.com/sarnold/crossdev.git"
else
	SRC_URI="mirror://gentoo/${P}.tar.xz
		https://dev.gentoo.org/~vapier/dist/${P}.tar.xz"
	KEYWORDS="~alpha ~amd64 ~arm ~arm64 ~hppa ~ia64 ~m68k ~mips ~ppc ~ppc64 ~s390 ~sh ~sparc ~x86 ~x86-fbsd"
fi

DESCRIPTION="Gentoo Cross-toolchain generator"
HOMEPAGE="https://www.gentoo.org/"

LICENSE="GPL-2"
SLOT="0"
IUSE=""

RDEPEND=">=sys-apps/portage-2.1
	>=app-portage/portage-utils-0.55
	app-shells/bash
	sys-apps/gentoo-functions
	!sys-devel/crossdev-wrappers"
DEPEND="app-arch/xz-utils"

src_install() {
	default
	if [[ "${PV}" == "99999999" ]] ; then
		sed -i "s:@CDEVPV@:${EGIT_VERSION}:" "${ED%/}"/usr/bin/crossdev || die
	fi
}
