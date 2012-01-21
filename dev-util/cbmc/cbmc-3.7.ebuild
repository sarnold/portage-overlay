# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="3"

MY_PV="${PV/./-}-src"
MY_P="${PN}-${MY_PV}"

inherit eutils multilib toolchain-funcs versionator

DESCRIPTION="CBMC is a Bounded Model Checker for ANSI-C and C++ programs."
HOMEPAGE="http://www.cprover.org/cbmc/"
SRC_URI="http://www.cprover.org/cbmc/download/${MY_P}.tgz
	doc? ( http://www.cprover.org/cbmc/doc/cbmc-slides.pdf )"

SLOT="0"
KEYWORDS="~amd64 ~x86 ~amd64-linux ~x86-linux"
LICENSE="ETH"

IUSE="debug doc"

DEPEND="sys-devel/bison
	sys-devel/flex
	sys-libs/zlib
	=sci-mathematics/minisat-2.1*[extended-solver]
	!=sci-mathematics/minisat-2.2*"

RDEPEND="${DEPEND}"

S="${WORKDIR}/${MY_P}"

pkg_setup() {
	if version_is_at_least "4.4" "$(gcc-version)"; then
		newer_gcc="true"
	fi
}

src_prepare() {
	epatch "${FILESDIR}"/${P}-make_fixes.patch

	sed -i -e "s|g++|$(tc-getCXX)|" \
		scripts/goto-cc-api/Makefile \
		src/cbmc/link

	sed -i -e "s|c++|$(tc-getCXX)|" \
		src/big-int/makefile

	sed -i -e "s|= gcc|= $(tc-getCC)|" \
		-e "s|= g++|= $(tc-getCXX)|" \
		-e "s|= ld|= $(tc-getLD)|" \
		-e "s|= ar|= $(tc-getAR)|" \
		-e "s|LINKFLAGS =|LINKFLAGS = ${LDFLAGS}|" \
		-e "s|/usr/lib|/usr/$(get_libdir)|" \
		"${S}"/src/config.inc

	sed -i -e "s|CPLUS|CXX|g" \
		src/config.inc \
		src/goto-programs/Makefile \
		scripts/goto-cc-api/Makefile \
		src/cbmc/Makefile \
		src/ansi-c/Makefile

	if [[ $newer_gcc = "true" ]]; then
		epatch "${FILESDIR}"/${P}-gcc-4.4.patch
	fi

	# the minisat-2.2 interface is not supported by
	# any current releases of cbmc through 3.9 (an
	# update is in the works according to the author)
#	epatch "${FILESDIR}"/${P}-minisat-2.2_include.patch
}

src_configure() {
	myconf=""

	if [[ $newer_gcc = "true" ]]; then
		myconf="-std=gnu++0x"
	fi

	sed -i \
		-e "s|-O2|${myconf}|" \
		"${S}"/src/config.inc
#		-e "s/#MODULE_BV_REFINEMENT/MODULE_BV_REFINEMENT/" \
}

src_compile() {
	make -j1 -C src/ all || die "make failed"
}

src_install() {
	dobin src/cbmc/cbmc || die "dobin failed"

	dodoc src/util/README || die
	if use doc; then
		dodoc "${DISTDIR}"/cbmc-slides.pdf || die
		dohtml -r doc/html-manual/* || die
	fi
}
