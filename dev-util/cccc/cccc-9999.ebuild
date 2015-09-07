# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=5

inherit eutils toolchain-funcs flag-o-matic

DESCRIPTION="Source metrics (line counts, complexity, etc) for Java and C++"
HOMEPAGE="http://cccc.sourceforge.net/"
if [[ ${PV} = 9999* ]]; then
	EGIT_REPO_URI="https://github.com/sarnold/cccc.git"
	EGIT_BRANCH="master"
	inherit git-r3
else
	SRC_URI="mirror://sourceforge/${PN}/${P}.tar.gz"
fi

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="amd64 ~arm ~ppc x86 ~amd64-linux ~x86-linux ~ppc-macos"
IUSE="doc apidoc"

RDEPEND=""
DEPEND="${RDEPEND}
	apidoc? ( app-doc/doxygen[dot] )
	"

MAKEOPTS="-j1"

src_prepare() {
	sed -i -e "/^CFLAGS/s|=|+=|" pccts/antlr/makefile
	sed -i -e "/^CFLAGS/s|=|+=|" pccts/dlg/makefile
	sed -i -e "/^CFLAGS/s|=|+=|" \
			-e "/^LD_OFLAG/s|-o|-o |" \
			-e "/^LDFLAGS/s|=|+=|" cccc/posixgcc.mak
	#LD_OFLAG: ld on Darwin needs a space after -o

	if ! [[ ${PV} = 9999* ]]; then
		epatch "${FILESDIR}"/${P}-whitespace-and-unqualified-lookup.patch
	fi

	epatch "${FILESDIR}"/${PN}-bug602904.patch \
		"${FILESDIR}"/${PN}-c_dialect.patch
}

src_compile() {
	emake CCC=$(tc-getCXX) LD=$(tc-getCXX) cccc

	use apidoc && emake CCC=$(tc-getCXX) LD=$(tc-getCXX) metrics docs
}

src_test() {
	emake CCC=$(tc-getCXX) LD=$(tc-getCXX) test
}

src_install() {
	dobin cccc/cccc
	dodoc README.rst changes.txt
	dodoc "${FILESDIR}"/cccc-dialect.opt
	docompress -x "/usr/share/doc/${PF}/cccc-dialect.opt"
	if use doc ; then
		dohtml cccc/*.html || die "html docs failed"
		if use apidoc ; then
			docinto api
			dohtml -A svg -r doxygen/html || die "dox failed"
			docompress -x "/usr/share/doc/${PF}/api"
			docinto metrics
			dohtml ccccout/* || die "metrics failed"
		fi
	fi
}
