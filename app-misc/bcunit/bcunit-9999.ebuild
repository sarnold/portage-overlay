# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI="5"

inherit autotools eutils libtool multilib multilib-minimal

DESCRIPTION="Lightweight system for writing, administering, and running unit tests in C"
HOMEPAGE="https://github.com/BelledonneCommunications/bcunit"

if [[ ${PV} = 9999* ]]; then
	EGIT_REPO_URI="https://github.com/BelledonneCommunications/bcunit.git"
	EGIT_EGIT_COMMIT="e255f062249b75bfeb6a1c02943b602709f1f10738144075b036b3231aa4d590"
	inherit git-r3
else
	# just one release - 3.0
	SRC_URI="https://github.com/BelledonneCommunications/${PN}/archive/${PV}.tar.gz -> ${P}.tar.gz"
fi

KEYWORDS="~amd64 ~x86"
SLOT="0"
LICENSE="LGPL-2"
IUSE=""

DEPEND=""

RESTRICT="test"

src_prepare() {
	eautoreconf

	multilib_copy_sources
}

multilib_src_configure() {
	econf --prefix="${EPREFIX}"/usr \
		--datarootdir="${EPREFIX}"/usr/share

	# fix doc path
	sed -i -e "s|doc/BCUnit|share/doc/BCUnit|" \
		"${S}"/doc/headers/Makefile \
		"${S}"/doc/Makefile
}
