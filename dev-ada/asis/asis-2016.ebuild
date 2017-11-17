# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI=6

inherit flag-o-matic multiprocessing
MYP=${PN}-gpl-${PV}-src

DESCRIPTION="To develop tools for Ada software"
HOMEPAGE="http://libre.adacore.com/"
SRC_URI="http://mirrors.cdn.adacore.com/art/57399029c7a447658e0aff71
	-> ${MYP}.tar.gz"

LICENSE="GPL-3"
SLOT="0"
KEYWORDS="~amd64"
IUSE="system-gcc gnat_2017"

DEPEND="dev-ada/gnat_util[system-gcc?,gnat_2017?]
	dev-ada/gnatcoll[system-gcc?,gnat_2017?,projects,shared]
	dev-ada/gprbuild[system-gcc?,gnat_2017?]
	dev-ada/xmlada[system-gcc?,gnat_2017?]
	system-gcc? ( =sys-devel/gcc-6.4.0[ada]
		=dev-ada/gnat_util-2016[system-gcc] )
	gnat_2017? ( dev-lang/gnat-gpl:6.3.0 )"
RDEPEND="${RDEPEND}"
REQUIRED_USE="^^ ( system-gcc gnat_2017 )"

S="${WORKDIR}"/${MYP}

PATCHES=( "${FILESDIR}"/${P}-gentoo.patch
	"${FILESDIR}"/compilation_options-2016.diff
	"${FILESDIR}"/link_tools_with_shared_asis.diff
	"${FILESDIR}"/typos.diff )

src_compile() {
	# need ADAFLAGS in flag-o-matic for this to work
	# needed for 6.4.0 "LTO streams not supported" bug
	if is-flagq -flto* ; then
		filter-flags -flto* -fuse-linker-plugin
	fi
	emake PROCESSORS=$(makeopts_jobs)
	emake tools PROCESSORS=$(makeopts_jobs)
}

src_install() {
	emake prefix="${D}"/usr install
	emake prefix="${D}"/usr install-tools
}
