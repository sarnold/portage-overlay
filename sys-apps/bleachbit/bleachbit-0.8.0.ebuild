# Copyright 1999-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="2"

inherit eutils gnome2 python toolchain-funcs fdo-mime

DESCRIPTION="GTK+ and Python GUI app for cleaning junk off your hard disk."

SRC_URI="mirror://sourceforge/${PN}/${P}.tar.bz2"
HOMEPAGE="http://bleachbit.sourceforge.net/"

IUSE=""
SLOT="0"
KEYWORDS="~amd64 ~x86 ~ppc"
LICENSE="GPL-2"

COMMON_DEP=">=dev-lang/python-2.5
	dev-util/desktop-file-utils
	dev-python/gnome-python
	media-plugins/gst-plugins-gnomevfs
	>=dev-python/pygtk-2.6
	x11-misc/xdg-utils
	dev-python/pyxdg"

DEPEND="${COMMON_DEP}
	sys-devel/gettext"

RDEPEND="${COMMON_DEP}
	dev-python/py-xmlrpc"

src_prepare() {
	epatch "${FILESDIR}"/${P}-makefile.patch
}

src_configure() {
	elog "Nothing to configure, continuing..."
}

src_compile() {
	make -C po local || die "make failed"
}

src_test() {
	make tests || die "make tests failed"
}

src_install() {
	# remove Windows-specific cleaners
	grep -l os=.windows. cleaners/*xml | xargs rm -f
	# remove Windows-specific modules
	rm -f ${PN}/Windows.py

	make DESTDIR="${D}" install prefix=/usr \
		|| die "make install failed"

	# disabled by makefile patch, so must do manually
	insinto "$(python_get_sitedir)/${PN}"
	doins "${PN}"/*.py

#	doicon "${S}/${PN}.png"
#	make_desktop_entry ${PN} "BleachBit ${PV}" \
#		"${PN}" "GTK;System;"

	dodoc README
}

pkg_postinst() {
	python_mod_optimize "$(python_get_sitedir)/${PN}"
	fdo-mime_desktop_database_update

	elog
	elog ""
	elog
}

pkg_postrm() {
	fdo-mime_desktop_database_update
}
