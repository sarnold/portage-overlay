# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="3"

inherit eutils toolchain-funcs

# unless there's an actual versioned release from upstream, this svn
# package is *.1 until something big changes or 1260 rolls over 2000
MY_P="${PN}-r1260"

DESCRIPTION="A fast STP solver with reference papers."
HOMEPAGE="http://sites.google.com/site/stpfastprover/"
SRC_URI="mirror://gentoo/${MY_P}.tar.gz"

SLOT="0"
KEYWORDS="~amd64 ~x86 ~amd64-linux ~x86-linux"
LICENSE="MIT"

IUSE="debug doc"

DEPEND="sys-devel/bison
	sys-devel/flex
	sys-libs/zlib"

RDEPEND="${DEPEND}"

S=${WORKDIR}/${MY_P}

pkg_setup() {
	if use debug; then
		myconf="-g"
	else
		myconf="-DNDEBUG"
	fi
}

src_prepare() {
	tc-export CC CXX

	echo "PREFIX=\$(DESTDIR)/usr" > scripts/config.info
	echo "CC=${CC}" >> scripts/config.info
	echo "CXX=${CXX}" >> scripts/config.info
	echo "CFLAGS_FPIC=-fpic" >> scripts/config.info

	cp scripts/Makefile.in Makefile || die "Could not create Makefile!"

	sed -i -e "s|-O3  -g|${CFLAGS} ${LDFLAGS} ${myconf}|" \
		scripts/Makefile.common

	sed -i -e "s|-O3|${CFLAGS} ${LDFLAGS} ${myconf}|" \
		src/sat/Makefile
}

src_compile() {
	emake || die "emake failed"
}

src_install() {
	# somewhat brute-force, but so is the build setup...

	dobin bin/${PN} || die
	dolib.a lib/lib${PN}.a || die

	insinto /usr/include/${PN}
	doins src/c_interface/*.h

	dodoc README CODING_GUIDLINES LICENSE LICENSE_COMPONENTS || die
	if use doc; then
		dodoc papers/*.pdf || die
	fi
}
