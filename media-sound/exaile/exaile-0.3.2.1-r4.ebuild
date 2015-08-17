# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=5

PYTHON_COMPAT=( python2_7 )
PYTHON_REQ_USE="sqlite"

inherit eutils fdo-mime multilib python-single-r1

DESCRIPTION="A media player aiming to be similar to AmaroK, but for GTK+"
HOMEPAGE="http://www.exaile.org/"
SRC_URI="http://launchpad.net/${PN}/0.3.2/${PV}/+download/${P}.tar.gz"

LICENSE="GPL-2 GPL-3"
SLOT="0"
KEYWORDS="~amd64 ~arm ~ppc ~sparc ~x86"
IUSE="-aws cddb context-info droptray -ffmpeg libnotify mpris2 mtp nls"

RDEPEND=${PYTHON_DEPS}"
	dev-python/dbus-python
	>=media-libs/mutagen-1.10
	>=dev-python/pygtk-2.17
	>=dev-python/pygobject-2.18
	dev-python/gst-python:0.10
	media-libs/gst-plugins-good:0.10
	media-plugins/gst-plugins-meta:0.10
	dev-python/beautifulsoup
	aws? ( dev-python/lxml )
	libnotify? ( dev-python/notify-python )
	cddb? ( dev-python/cddb-py )
	droptray? ( dev-python/egg-python )
	ffmpeg? ( media-plugins/gst-plugins-ffmpeg:0.10[libav] )
	mpris2? ( media-plugins/exaile-soundmenu-indicator )
	mtp? ( dev-python/pymtp )
	context-info? ( virtual/python-imaging
			dev-python/pywebkitgtk )"

DEPEND="${RDEPEND}
	nls? ( dev-util/intltool
	sys-devel/gettext )"

REQUIRED_USE="${PYTHON_REQUIRED_USE}"

RESTRICT="test" #315589

src_prepare() {
	python_setup

	sed -i \
		-e "s:exec python:exec ${EPYTHON}:" \
		exaile tools/generate-launcher || die

	# fix import of python imaging
	sed -i -e "s|import Image|import PIL|" \
		plugins/contextinfo/__init__.py || die

	epatch "${FILESDIR}"/${P}-amazoncover-lxml.patch
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
	fdo-mime_desktop_database_update
}

pkg_postrm() {
	fdo-mime_desktop_database_update
}
