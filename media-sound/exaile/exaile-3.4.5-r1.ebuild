# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI=5

PYTHON_COMPAT=( python2_7 )
PYTHON_REQ_USE="sqlite"

inherit fdo-mime multilib python-r1

DESCRIPTION="A media player aiming to be better than AmaroK, but for GTK+"
HOMEPAGE="http://www.exaile.org/"
SRC_URI="https://github.com/${PN}/${PN}/archive/${PV}.tar.gz -> ${P}.tar.gz"

LICENSE="GPL-2 GPL-3"
SLOT="0"
KEYWORDS="~amd64 ~arm ~ppc ~sparc ~x86"
IUSE="cddb extra-plugins libnotify mpris2 nls"

RDEPEND="dev-python/dbus-python
	dev-python/gst-python:1.0
	>=dev-python/pygtk-2.17
	>=dev-python/pygobject-2.18:2
	media-libs/gst-plugins-good:1.0
	>=media-libs/mutagen-1.10
	media-plugins/gst-plugins-meta:1.0
	virtual/python-imaging
	cddb? ( dev-python/cddb-py )
	libnotify? ( dev-python/notify-python )
	dev-python/egg-python
        media-plugins/gst-plugins-libav:1.0
	dev-python/pymtp
	dev-python/pywebkitgtk
        mpris2? ( media-plugins/exaile-soundmenu-indicator )"

DEPEND="nls? ( dev-util/intltool
		sys-devel/gettext )"

RESTRICT="test" #315589

src_prepare() {
	python_setup

	epatch "${FILESDIR}"/${PN}-0.3.2.1-amazoncover-lxml.patch \
		"${FILESDIR}"/${P}-missing_dbus_import.patch \
		"${FILESDIR}"/${P}-externals_install_fix.patch
}
src_compile() {
	emake compile manpage

	if use nls; then
		emake locale
	fi
}

src_install() {
	emake \
		PREFIX=/usr \
		LIBINSTALLDIR=/$(get_libdir) \
		DESTDIR="${D}" \
		install$(use nls || echo _no_locale)

	if use extra-plugins ; then
		PREFIX=/usr LIBINSTALLDIR=/$(get_libdir) DESTDIR="${D}" \
			emake -C plugins extra_install \
			|| die "install extra plugins failed"
	fi

	dodoc FUTURE
}

pkg_postinst() {
	fdo-mime_desktop_database_update
	fdo-mime_mime_database_update
}

pkg_postrm() {
	fdo-mime_desktop_database_update
	fdo-mime_mime_database_update
}
