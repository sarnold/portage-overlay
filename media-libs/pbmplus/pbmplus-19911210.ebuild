# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=5

inherit eutils toolchain-funcs

DESCRIPTION="A toolkit for converting various image formats"
HOMEPAGE="http://acme.com/software/pbmplus/"
SRC_URI="http://acme.com/software/pbmplus/${PN}_10dec1991.tar.gz -> ${P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="amd64 ~arm ~ppc x86 ~amd64-linux ~x86-linux ~ppc-macos"
IUSE="apidoc"

RDEPEND=""
DEPEND="${RDEPEND}
	apidoc? ( app-doc/doxygen[dot] )
	"

S="${WORKDIR}"/${PN}

src_prepare() {
	sed -i -e "s|10dec91|19911210|" version.h || die "sed version failed"

	DEFS="-DSVR4 -D__STDC__"

	sed -i -e "s|CC =		cc|CC ?= gcc|" \
		-e "s|CFLAGS =	-O|CFLAGS ?= -O2 -std=gnu99|" \
		-e "s|LDFLAGS =	-s|LDFLAGS ?= -Wl,-O1|" \
		-e "s|usr/lib/X11/rgb|usr/share/X11|" \
		-e "s|TIFFINC =	-I../libtiff|TIFFINC = -I/usr/include|" \
		-e "s|TIFFLIB =	../libtiff/libtiff.a|TIFFLIB = -ltiff|" \
		-e "s|/usr/new/pbmplus|${EPREFIX}/usr|" \
		-e "s|/usr/man/|/usr/share/man/|g" \
		Makefile || die "sed makefile failed!"

	sed -i -e "s|#define BSD|/* #define BSD */|" \
		-e "s|/* #define SYSV	*/|#define SYSV|" \
		pbmplus.h || die "sed header failed!"
}

src_compile() {
	CC=$(tc-getCC) LD=$(tc-getCC) emake || die "emake failed"
}

src_install() {
	elog "Install here..."
}
