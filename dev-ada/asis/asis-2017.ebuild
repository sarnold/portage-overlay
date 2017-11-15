# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI=6

inherit multiprocessing
MYP=${PN}-gpl-${PV}-src

DESCRIPTION="To develop tools for Ada software"
HOMEPAGE="http://libre.adacore.com/"
SRC_URI="http://mirrors.cdn.adacore.com/art/591c45e2c7a447af2deecffb
	-> ${MYP}.tar.gz"

LICENSE="GPL-3"
SLOT="0"
KEYWORDS="~amd64"
IUSE="gnat_2017 +system-gcc"

DEPEND="dev-ada/gnat_util[system-gcc?,gnat_2017?]
	dev-ada/gnatcoll[system-gcc?,gnat_2017?,projects,shared]
	dev-ada/gprbuild[system-gcc?,gnat_2017?]
	dev-ada/xmlada[system-gcc?,gnat_2017?]
	system-gcc? ( >=sys-devel/gcc-6.3.0[ada] )
	gnat_2017? ( dev-lang/gnat-gpl:6.3.0 )"
RDEPEND="${RDEPEND}"
REQUIRED_USE="^^ ( gnat_2017 system-gcc )"

S="${WORKDIR}"/${MYP}

PATCHES=( "${FILESDIR}"/${P}-gentoo.patch
	"${FILESDIR}"/gnatgcc.patch
	"${FILESDIR}"/compilation_options.diff
	"${FILESDIR}"/link_tools_with_shared_asis.diff
	"${FILESDIR}"/typos.diff
	"${FILESDIR}"/xmlada-split.diff
	"${FILESDIR}"/gcc-7.diff
)

src_compile() {
	emake PROCESSORS=$(makeopts_jobs)
	emake tools PROCESSORS=$(makeopts_jobs)
}

src_install() {
	emake prefix="${ED}"/usr install
	emake prefix="${ED}"/usr install-tools
}
