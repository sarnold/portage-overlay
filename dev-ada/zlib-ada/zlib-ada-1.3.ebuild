# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=5
inherit eutils

DESCRIPTION="ZLib.Ada is a thick binding to the popular compression/decompression library ZLib."
HOMEPAGE="http://zlib-ada.sourceforge.net"
SRC_URI="mirror://sourceforge/zlib-ada/${P}.tar.gz"

LICENSE="GPL-2+"
SLOT="0"
KEYWORDS="~amd64 ~arm ~arm64 ~x86"
IUSE="examples"

RDEPEND="sys-libs/zlib"
DEPEND="${RDEPEND}
	virtual/ada"

S="${WORKDIR}"

src_compile() {
	gnatmake -Pzlib.gpr -L/usr/$(get_libdir)
}

src_install() {
	pkg_libs="zlib*.ali"
	pkg_src="zlib*.ad*"
	examples="buffer_demo.adb mtest.adb read.adb test.adb"

	insinto "${ADA_OBJECTS_PATH}/${PN}"
	doins "${pkg_libs}"

	insinto "${ADA_INCLUDE_PATH}/${PN}"
	doins "${pkg_src}"

	if use esamples ; then
		insinto /usr/share/${P}/examples
		doins "${examples}"
	fi

	dodoc readme.txt
}
