# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI=6

inherit flag-o-matic toolchain-funcs multiprocessing

MYP=${PN}-gpl-${PV}

DESCRIPTION="Provides access to GNAT compiler internals for AdaCore utilities"
HOMEPAGE="http://libre.adacore.com"
SRC_URI="http://mirrors.cdn.adacore.com/art/57399637c7a447658e0affa6 -> ${MYP}-src.tar.gz"

LICENSE="GPL-3"
SLOT="0"
KEYWORDS="~amd64"
IUSE="system-gcc gnat_2017 +shared static static-pic"

RDEPEND="system-gcc? ( sys-devel/gcc:6.4.0[ada] )
	gnat_2017? ( dev-lang/gnat-gpl:6.3.0 )"
DEPEND="${RDEPEND}
	dev-ada/gprbuild[system-gcc?,gnat_2017?]"
REQUIRED_USE="^^ ( system-gcc gnat_2017 )"

S="${WORKDIR}"/${MYP}-src

PATCHES=( "${FILESDIR}"/${P}-gentoo.patch )

src_compile() {
	if use system-gcc ; then
		GCC_PV=$(gcc -dumpversion)
		# build uses -Wl,-r for partial linking
		append-ldflags -no-pie
		tc-export CC LD AS AR NM RANLIB STRIP OBJCOPY
		GCC=${CC}
		GNATMAKE=$(which gnatmake)
	else
		GCC_PV=6.3.0
		GCC=${CHOST}-gcc-${GCC_PV}
		GNATMAKE=${CHOST}-gnatmake-${GCC_PV}
	fi

	emake GNATMAKE="${GNATMAKE} ${ADAFLAGS}" \
		BUILDER="gprbuild -j$(makeopts_jobs)" generate_sources

	for kind in shared static static-pic; do
		if use ${kind}; then
			emake CC="${GCC}" BUILDER="gprbuild -v -j$(makeopts_jobs)" \
				build-${kind}
		fi
	done
}

src_install() {
	for kind in shared static static-pic; do
		if use ${kind}; then
			emake prefix="${D}"/usr install-${kind}
		fi
	done
	einstalldocs
}
