# Copyright 1999-2013 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=4

PYTHON_COMPAT=( python{2_6,2_7} )

inherit eutils multilib multilib-build toolchain-funcs python-any-r1

DESCRIPTION="Pseudo gives fake root capabilities to a normal user"
HOMEPAGE="http://git.yoctoproject.org/cgit/cgit.cgi/pseudo"
SRC_URI="http://www.yoctoproject.org/downloads/${PN}/${P}.tar.bz2"

LICENSE=""
SLOT="0"
KEYWORDS="~amd64 ~x86"
IUSE=""

RDEPEND=">=dev-db/sqlite-3.7"
DEPEND="${RDEPEND}
	${PYTHON_DEPS}"

src_prepare() {
	epatch "${FILESDIR}"/${P}-has_unload-add-function.patch \
		"${FILESDIR}"/${P}-shutdownping.patch \
		"${FILESDIR}"/${P}-symver.patch
	multilib_copy_sources
}

my_configure() {
	cd "${BUILD_DIR}" || die

	local abiflags=$(get_abi_CFLAGS)
	local bits=$(echo $abiflags | cut -c3-)
	local configopts=(
		--prefix=/usr
		--libdir=/usr/$(get_abi_LIBDIR)
		--without-rpath
		--cflags="${CFLAGS}"
		--bits=${bits}
		--enable-force-async
	)

	elog "config opts: ${configopts[@]} $@"

	./configure "${configopts[@]}" "$@"
}

src_configure() {
	multilib_foreach_abi my_configure
}

mymake() {
	cd "${BUILD_DIR}" || die
	local makeopts=(
		AR="$(tc-getAR)"
		CXX="$(tc-getCXX)"
		CXXFLAGS="${CXXFLAGS} -pthread"
		LDFLAGS="${LDFLAGS} -pthread"
		NM="$(tc-getNM)"
	)
	emake "${makeopts[@]}" "$@"
}

src_compile() {
	multilib_foreach_abi mymake
}

src_test() {
	multilib_foreach_abi mymake static-test
}

src_install() {
	myinstall() {
		cd "${BUILD_DIR}" || die
		emake DESTDIR="${ED}" prefix=usr libdir=usr/$(get_libdir) install
		multilib_check_headers
	}
	multilib_foreach_abi myinstall
	dodoc doc/*
}
