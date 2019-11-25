# Copyright 1999-2019 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=6

inherit flag-o-matic llvm systemd toolchain-funcs

HOMEPAGE="https://www.zerotier.com/"
DESCRIPTION="A software-based managed Ethernet switch for planet Earth"

if [[ ${PV} = 9999* ]]; then
	EGIT_REPO_URI="https://github.com/zerotier/ZeroTierOne.git"
	EGIT_COMMIT="088dab4f04d7ec662b83299a32d7183d5d48a5dc"
	inherit git-r3
	KEYWORDS=""
else
	SRC_URI="https://github.com/zerotier/ZeroTierOne/archive/${PV}.tar.gz -> ${P}.tar.gz"
	KEYWORDS="~amd64 ~arm ~arm64 ~x86"
	S="${WORKDIR}/ZeroTierOne-${PV}"
fi

LICENSE="BSL-1.1"
SLOT="0"
IUSE="clang debug doc neon -ztnc"

RDEPEND="
	dev-libs/json-glib:=
	net-libs/libnatpmp:=
	net-libs/miniupnpc:=
	clang? ( >=sys-devel/clang-6:=
		doc? ( app-doc/doxygen[dot,clang] )
	)
	!clang? (
		doc? ( app-doc/doxygen[dot] )
	)"

DEPEND="${RDEPEND}"

PATCHES=( "${FILESDIR}/${PN}-1.4.6-respect-ldflags.patch"
	"${FILESDIR}/${PN}-1.4.6-add-armv7a-support.patch"
	"${FILESDIR}/${PN}-1.4.6-fixup-neon-support.patch"
	"${FILESDIR}/${PN}-1.4.6-Add-make-src-docs-target.patch"
	"${FILESDIR}/${PN}-1.4.6-add-mk-ctlr-node-target.patch" )

DOCS=( README.md AUTHORS.md )

LLVM_MAX_SLOT=9

llvm_check_deps() {
	if use clang ; then
		if ! has_version --host-root "sys-devel/clang:${LLVM_SLOT}" ; then
			ewarn "sys-devel/clang:${LLVM_SLOT} is missing! Cannot use LLVM slot ${LLVM_SLOT} ..."
			return 1
		fi

		if ! has_version --host-root "=sys-devel/lld-${LLVM_SLOT}*" ; then
			ewarn "=sys-devel/lld-${LLVM_SLOT}* is missing! Cannot use LLVM slot ${LLVM_SLOT} ..."
			return 1
		fi

		einfo "Will use LLVM slot ${LLVM_SLOT}!"
	fi
}

src_compile() {
	if use clang && ! tc-is-clang ; then
		export CC=${CHOST}-clang
		export CXX=${CHOST}-clang++
		strip-unsupported-flags
		replace-flags -ftree-vectorize -fvectorize
		replace-flags -flto* -flto=thin
		append-ldflags -fuse-ld=lld
	else
		tc-export CXX CC
		append-flags -fPIC
		append-ldflags -fuse-ld=gold
	fi

	use debug && export ZT_DEBUG=1
	use neon || export ZT_DISABLE_NEON=1
	use ztnc && export ZT_CONTROLLER=1
	append-ldflags -Wl,-z,noexecstack

	if use ztnc; then
		emake CXX="${CXX}" STRIP=: controller-node
	else
		emake CXX="${CXX}" STRIP=: one
	fi

	use doc && make src-docs
}

src_test() {
	emake selftest
	./zerotier-selftest || die
}

src_install() {
	default
	# remove pre-zipped man pages
	rm -f "${ED}"/usr/share/man/{man1,man8}/*

	newinitd "${FILESDIR}/${PN}".init "${PN}"
	systemd_dounit "${FILESDIR}/${PN}".service

	doman doc/zerotier-{cli.1,idtool.1,one.8}

	use doc && dohtml -r -A svg src-docs/html/*
}
