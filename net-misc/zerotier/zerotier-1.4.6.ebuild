# Copyright 1999-2019 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=6

inherit flag-o-matic llvm systemd toolchain-funcs

HOMEPAGE="https://www.zerotier.com/"
DESCRIPTION="A software-based managed Ethernet switch for planet Earth"
SRC_URI="https://github.com/zerotier/ZeroTierOne/archive/${PV}.tar.gz -> ${P}.tar.gz"

LICENSE="BSL-1.1"
SLOT="0"
KEYWORDS="~amd64 ~arm ~arm64 ~x86"
IUSE="clang -systemd"

S="${WORKDIR}/ZeroTierOne-${PV}"

RDEPEND="
	dev-libs/json-glib:=
	net-libs/http-parser:=
	net-libs/libnatpmp:=
	net-libs/miniupnpc:="

DEPEND="${RDEPEND}
	|| ( >=sys-devel/gcc-6.0 >=sys-devel/clang-3.4 )
	|| (
		(
			sys-devel/clang:8
			!clang? ( sys-devel/llvm:8 )
			clang? (
				=sys-devel/lld-8*
				sys-devel/llvm:8[gold]
				=sys-libs/compiler-rt-sanitizers-8*
			)
		)
		(
			sys-devel/clang:7
			!clang? ( sys-devel/llvm:7 )
			clang? (
				=sys-devel/lld-7*
				sys-devel/llvm:7[gold]
				=sys-libs/compiler-rt-sanitizers-7*
			)
		)
		(
			sys-devel/clang:6
			!clang? ( sys-devel/llvm:6 )
			clang? (
				=sys-devel/lld-6*
				sys-devel/llvm:6[gold]
				=sys-libs/compiler-rt-sanitizers-6*
			)
		)
	)
"

DOCS=( README.md AUTHORS.md )

pkg_setup() {
	llvm_pkg_setup
}

src_compile() {
	if use clang && ! tc-is-clang ; then
		export CC=${CHOST}-clang
		export CXX=${CHOST}-clang++
	else
		tc-export CXX CC
	fi

	use arm && append-cxxflags -fPIC
	append-ldflags -Wl,-z,noexecstack
	emake CXX="${CXX}" STRIP=: one
}

src_test() {
	emake selftest
	./zerotier-selftest || die
}

src_install() {
	default
	# remove pre-zipped man pages
	rm -f "${ED}"/usr/share/man/{man1,man8}/*

	if ! use systemd ; then
		newinitd "${FILESDIR}/${PN}".init "${PN}"
	else
		systemd_dounit "${FILESDIR}/${PN}".service
	fi

	doman doc/zerotier-{cli.1,idtool.1,one.8}
}
