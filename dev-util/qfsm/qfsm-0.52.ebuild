# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="4"
inherit cmake-utils qt4-r2 fdo-mime

MY_P="${PN}-${PV}.0-Source"

DESCRIPTION="Qfsm is a graphical editor for finite state machines (also useful for analyzing Verilog code)"
HOMEPAGE="http://qfsm.sourceforge.net/"
SRC_URI="mirror://sourceforge/${PN}/${MY_P}.tar.bz2"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="amd64 x86"
IUSE="debug"

RDEPEND="x11-libs/qt-gui:4"

DEPEND="${RDEPEND}
	app-arch/unzip"

S="${WORKDIR}/${MY_P}"

src_configure(){
	cmake .
}

src_install(){
	cmake-utils_src_install
	dodoc README INSTALL || die "dodoc failed"
}

pkg_postinst() {
        fdo-mime_desktop_database_update
        elog "See the docs and examples for more info..."
}

pkg_postrm() {
	fdo-mime_desktop_database_update
}
