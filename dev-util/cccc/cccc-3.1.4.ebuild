# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=5

inherit eutils toolchain-funcs flag-o-matic

DESCRIPTION="Source metrics (line counts, complexity, etc) for Java and C++"
HOMEPAGE="http://cccc.sourceforge.net/"
if [[ ${PV} = 9999* ]]; then
	EGIT_REPO_URI="https://github.com/sarnold/cccc.git"
	inherit git-r3
else
	SRC_URI="mirror://sourceforge/${PN}/${P}.tar.gz"
	MAKEOPTS="-j1"
fi

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="amd64 ~arm ~ppc x86 ~amd64-linux ~x86-linux ~ppc-macos"
IUSE=""

RDEPEND=""
DEPEND="${RDEPEND}"

src_prepare() {
	sed -i -e "/^CFLAGS/s|=|+=|" pccts/antlr/makefile
	sed -i -e "/^CFLAGS/s|=|+=|" pccts/dlg/makefile
	sed -i -e "/^CFLAGS/s|=|+=|" \
			-e "/^LD_OFLAG/s|-o|-o |" \
			-e "/^LDFLAGS/s|=|+=|" cccc/posixgcc.mak
	#LD_OFLAG: ld on Darwin needs a space after -o

	epatch "${FILESDIR}"/${P}-whitespace-and-unqualified-lookup.patch
}

src_compile() {
	emake CCC=$(tc-getCXX) LD=$(tc-getCXX) pccts

	append-flags "-std=gnu++11"
	emake CCC=$(tc-getCXX) LD=$(tc-getCXX) cccc
}

src_install() {
	dodoc readme.txt changes.txt
	dohtml cccc/*.html
	cd install || die
	dodir /usr
	emake -f install.mak INSTDIR="${ED}"/usr/bin
}
