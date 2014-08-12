# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="3"

inherit eutils flag-o-matic multilib toolchain-funcs versionator

DESCRIPTION="CBMC is a Bounded Model Checker for ANSI-C and C++ programs."
HOMEPAGE="http://www.cprover.org/cbmc/"
SRC_URI="mirror://gentoo/${P}.tar.bz2
	doc? ( http://www.cprover.org/cbmc/doc/cbmc-slides.pdf )"

SLOT="0"
KEYWORDS="~amd64 ~arm ~x86 ~amd64-linux ~arm-linux ~x86-linux"
LICENSE="ETH"

IUSE="debug doc"

DEPEND="sys-devel/bison
	sys-devel/flex
	sys-libs/zlib
	>=sci-mathematics/minisat-2.2[extended-solver]"

RDEPEND="sys-devel/autoconf"

pkg_setup() {
	if version_is_at_least "4.4" "$(gcc-version)"; then
		newer_gcc="true"
	fi
}

src_prepare() {
	epatch "${FILESDIR}"/${P}-make_fixes.patch

	sed -i -e "s|= g++|= $(tc-getCXX)|" \
		-e "s|= gcc|= $(tc-getCC)|" \
		-e "s|= ld|= $(tc-getLD)|" \
		-e "s|= ar|= $(tc-getAR)|" \
		-e "s|#LINKFLAGS = -static|LINKFLAGS = ${LDFLAGS}|" \
		-e "s|/usr/lib|/usr/$(get_libdir)|" \
		src/config.inc

	# this is here because upstream specified -O2 
	if is-flagq "-O3" ; then
		echo
		ewarn "Compiling with -O3 is known to produce incorrectly"
		ewarn "optimized code which breaks certain applications."
		echo
		elog "Continuing with -O2 instead ..."
		echo
		replace-flags "-O3" "-O2"
	fi
}

src_configure() {
	myconf=""

	if [[ $newer_gcc = "true" ]]; then
		myconf="-std=gnu++0x"
	fi

	sed -i \
		-e "s|-MMD|-MMD ${myconf}|" \
		"${S}"/src/config.inc
}

src_compile() {
	make -j1 -C src || die "make failed"
}

src_install() {
	dobin src/cbmc/cbmc src/goto-cc/goto-cc \
		src/goto-instrument/goto-instrument \
		|| die "dobin failed"

	dodoc src/util/README || die
	if use doc; then
		dodoc "${DISTDIR}"/cbmc-slides.pdf || die
		dohtml -r doc/html-manual/* || die
	fi
}
