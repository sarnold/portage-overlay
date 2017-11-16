# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI="5"

inherit eutils toolchain-funcs

DESCRIPTION="This tool is designed to aid in the creation of Ada bindings to C"
SRC_URI="https://dev.gentoo.org/~george/src/${P}.tar.bz2"
HOMEPAGE="http://archive.adaic.com/tools/bindings/bindings95/html/section4.html#cbind"
LICENSE="GMGPL"

DEPEND="virtual/ada"
RDEPEND="${DEPEND}"

SLOT="0"
KEYWORDS="~amd64 ~arm ~arm64 ~x86"
IUSE=""

MAKEOPTS="-j1"

src_prepare() {
	epatch "${FILESDIR}"/${P}-makefile.patch
}

src_compile() {
	make touch
	emake all
}

src_install () {
	make PREFIX=/usr DESTDIR="${ED}" install || die
	dodoc README DOCS
}
