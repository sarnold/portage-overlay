# Copyright 1999-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

# !NOTE!
# this is a utility, no libs generated, no reason to do the gnat.eclass dance
# so, "inherit gnat" should not appear here!

DESCRIPTION="This tool is designed to aid in the creation of Ada bindings to C"
SRC_URI="https://dev.gentoo.org/~george/src/${P}.tar.bz2"
HOMEPAGE="http://archive.adaic.com/tools/bindings/bindings95/html/section4.html#cbind"
LICENSE="GMGPL"

DEPEND="virtual/ada"
RDEPEND="${DEPEND}"

SLOT="0"
KEYWORDS="~amd64 ~arm ~x86"
IUSE=""

src_compile() {
	MAKEOPTS="${MAKEOPTS} -j1" emake || die
}

src_install () {
	make PREFIX="${D}"/usr/ install || die
	dodoc README DOCS
}
