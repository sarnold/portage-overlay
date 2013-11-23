# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=3

PYTHON_DEPEND="2:2.6"
PYTHON_USE_WITH="berkdb sqlite"

inherit eutils fdo-mime multilib python

DESCRIPTION="A media player aiming to be similar to AmaroK, but for GTK+"
HOMEPAGE="http://www.exaile.org/"
SRC_URI="http://launchpad.net/${PN}/0.3.2/${PV}/+download/${P}.tar.gz"

LICENSE="GPL-2 GPL-3"
SLOT="0"
KEYWORDS="~amd64 ~ppc ~sparc ~x86"
IUSE="cddb context-info ffmpeg gnome libnotify mtp nls"

RDEPEND="dev-python/dbus-python
	>=media-libs/mutagen-1.10
	>=dev-python/pygtk-2.17
	>=dev-python/pygobject-2.18
	dev-python/gst-python:0.10
	media-libs/gst-plugins-good:0.10
	media-plugins/gst-plugins-meta:0.10
	dev-python/beautifulsoup
	libnotify? ( dev-python/notify-python )
	cddb? ( dev-python/cddb-py )
	ffmpeg? ( media-plugins/gst-plugins-ffmpeg )
	mtp? ( dev-python/pymtp )
	gnome? ( media-plugins/exaile-soundmenu-indicator )
	context-info? ( dev-python/imaging
			dev-python/pywebkitgtk )"

DEPEND="nls? ( dev-util/intltool
	sys-devel/gettext )"

RESTRICT="test" #315589

pkg_setup() {
	python_set_active_version 2
	python_pkg_setup
}

src_prepare() {
	sed -i \
		-e "s:exec python:exec $(PYTHON):" \
		exaile tools/generate-launcher || die

	# fix import of python imaging
	sed -i -e "s|import Image|import PIL|" \
		plugins/contextinfo/__init__.py || die
}

src_compile() {
	if use nls; then
		emake locale || die
	fi
}

src_install() {
	emake \
		PREFIX=/usr \
		LIBINSTALLDIR=/$(get_libdir) \
		DESTDIR="${D}" \
		install$(use nls || echo _no_locale) || die

	dodoc FUTURE || die
}

pkg_postinst() {
	python_need_rebuild
	python_mod_optimize -- /usr/$(get_libdir)/${PN}
	fdo-mime_desktop_database_update
	fdo-mime_mime_database_update
}

pkg_postrm() {
	python_mod_cleanup  -- /usr/$(get_libdir)/${PN}
	fdo-mime_desktop_database_update
	fdo-mime_mime_database_update
}
