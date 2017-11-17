# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI=6

inherit multiprocessing

MYP=${PN}-gpl-${PV}-src

DESCRIPTION="Ada unit testing framework"
HOMEPAGE="http://libre.adacore.com/tools/aunit/"
SRC_URI="http://mirrors.cdn.adacore.com/art/591c45e2c7a447af2deed000
	-> ${MYP}.tar.gz"

LICENSE="GPL-3"
SLOT="0"
KEYWORDS="~amd64"
IUSE="+system-gcc gnat_2017"

RDEPEND="system-gcc? ( >=sys-devel/gcc-6.3.0[ada] )
	gnat_2017? ( dev-lang/gnat-gpl:6.3.0 )"
DEPEND="${RDEPEND}
	dev-ada/gprbuild[system-gcc?,gnat_2017?]"

S="${WORKDIR}"/${MYP}

PATCHES=( "${FILESDIR}"/${P}-gentoo.patch )

src_compile() {
	emake GPRBUILD="gprbuild -j$(makeopts_jobs)"
}

src_install() {
	emake INSTALL="${ED}"usr install
	einstalldocs
	mv "${ED}"usr/share/doc/${PN}/* "${ED}"usr/share/doc/${PF}/ || die
	rmdir "${ED}"usr/share/doc/${PN} || die
	mv "${ED}"usr/share/examples/${PN} "${ED}"usr/share/doc/${PF}/examples || die
	rmdir "${ED}"usr/share/examples || die
}
