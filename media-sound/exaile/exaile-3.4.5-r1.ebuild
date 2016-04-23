# Copyright 1999-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI=5

PYTHON_COMPAT=( python2_7 )
PYTHON_REQ_USE="sqlite"

inherit eutils fdo-mime multilib python-r1

DESCRIPTION="A media player aiming to be better than AmaroK, but for GTK+"
HOMEPAGE="http://www.exaile.org/"

if [[ ${PV} = 9999* ]]; then
	inherit git-r3
	EGIT_REPO_URI="https://github.com/exaile/exaile.git"
	EGIT_BRANCH="master"
	KEYWORDS=""
else
	SRC_URI="https://github.com/${PN}/${PN}/archive/${PV}.tar.gz -> ${P}.tar.gz"
	KEYWORDS="~amd64 ~arm ~ppc ~sparc ~x86"
fi

LICENSE="GPL-2 GPL-3"
SLOT="0"
IUSE="cddb droptray extra-plugins libnotify mp4 mpris2 mtp nls wikipedia"

RDEPEND="${PYTHON_DEPS}
	dev-python/dbus-python
	dev-python/gst-python:1.0
	dev-python/pygtk:2[${PYTHON_USEDEP}]
	dev-python/pygobject:2[${PYTHON_USEDEP}]
	media-libs/gst-plugins-good:1.0
	>=media-libs/mutagen-1.10
	media-plugins/gst-plugins-meta:1.0
	dev-python/pillow
	cddb? ( dev-python/cddb-py )
	droptray? ( dev-python/egg-python )
	libnotify? ( dev-python/notify-python )
	mp4? ( media-plugins/gst-plugins-libav:1.0 )
	mpris2? ( media-plugins/exaile-soundmenu-indicator )
	mtp? ( dev-python/pymtp )
	wikipedia? ( dev-python/pywebkitgtk )"

DEPEND="nls? ( dev-util/intltool
		sys-devel/gettext )"

RESTRICT="test" #315589

EPATCH_OPTS="-F 3"

src_prepare() {
	python_setup

	epatch "${FILESDIR}"/${PN}-0.3.2.1-amazoncover-lxml.patch \
		"${FILESDIR}"/${P}-missing_dbus_import.patch \
		"${FILESDIR}"/${P}-manprefix-makefile.patch
}
src_compile() {
	emake all_no_locale

	if use nls; then
		emake locale
	fi
}

src_install() {
	# MANPREFIX now defaults to PREFIX/share - set path for *BSDs
	INSTALL_OPTS='PREFIX=/usr LIBINSTALLDIR=/usr/$(get_libdir) DESTDIR="${ED}"'

	emake ${INSTALL_OPTS} install$(use nls || echo _no_locale)

	if use extra-plugins ; then
		emake ${INSTALL_OPTS} -C plugins extra_install \
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
