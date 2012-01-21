# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

inherit eutils toolchain-funcs

DESCRIPTION="Computes cyclomatic complexity metric on source code."
SRC_URI="http://www.maultech.com/chrislott/resources/cmetrics/${P}.tar.gz"
HOMEPAGE="http://www.maultech.com/chrislott/resources/cmetrics/"

KEYWORDS="~alpha ~amd64 ~hppa ~ia64 ~mips ~ppc ~ppc64 ~sparc ~x86 ~x86-fbsd"
SLOT="0"
LICENSE="GPL-2"
IUSE="debug"

DEPEND="sys-devel/flex"

src_unpack() {
	unpack ${A}
	cd "${S}"

	epatch "${FILESDIR}"/${P}-gcc-update.patch

	sed -i -e "s|= gcc|= $(tc-getCC)|" \
		-i -e "s|= g++|= $(tc-getCXX)|" \
		-i -e "s|= -ll|= -lstdc++ -lfl|" Makefile

	if ! use debug ; then
		sed -i -e "s|LDFLAGS = \$(DEBUG)|LDFLAGS = ${LDFLAGS}|" \
			-i -e "s|\$(OPTIM) \$(DEBUG) #-Wall|${CFLAGS}|" Makefile
	else
		sed -i -e  "s|LDFLAGS = \$(DEBUG)|= -Wl,-g ${LDFLAGS}|" \
			-i -e "s|\$(OPTIM) \$(DEBUG) #-Wall|${CFLAGS}|" Makefile
	fi
}

src_compile() {
		make all || die "make failed"
}

src_install() {
	dobin cyclo mcstrip

	doman cyclo.0 mcstrip.1 cyclo.1
	dodoc README mccabe.example || die "dodoc failed"
}
