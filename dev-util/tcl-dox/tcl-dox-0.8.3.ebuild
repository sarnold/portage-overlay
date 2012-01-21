# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="2"

inherit eutils toolchain-funcs

DESCRIPTION="A Tcl input filter for doxygen."
HOMEPAGE="http://therowes.net/~greg/software/#tcldox"
SRC_URI="http://therowes.net/%7Egreg/download/tcl-doxygen-filter/${P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~ppc ~ppc64 ~sparc ~x86"
IUSE=""

DEPEND="sys-devel/flex"

RDEPEND="app-doc/doxygen"

src_prepare() {
	cd "${S}"/src
	sed -i -e "s|CFLAGS=|CFLAGS=${CFLAGS} |" \
		-e "s|gcc|$(tc-getCC)|" \
		Makefile || die
}

src_compile() {
	cd "${S}"/src
	make || die
}

src_install() {
	dobin src/tcl-dox
	dodoc README
	insinto /usr/share/doc/${P}/exmaples
	doins example/*
}
