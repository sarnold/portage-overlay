# Copyright 1999-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI=5

# TODO: Use python-r1 instead and support Python 3.x?

PYTHON_COMPAT=( python2_7 )

inherit autotools eutils python-single-r1 udev

if [[ ${PV} = 9999* ]]; then
	EGIT_REPO_URI="https://github.com/VCTLabs/libgpod.git"
	inherit git-r3
	KEYWORDS=""
else
	SRC_URI="https://github.com/VCTLabs/${PN}/archive/${PV}.tar.gz -> ${P}.tar.gz"
	KEYWORDS="amd64 arm x86"
fi

DESCRIPTION="Shared library to access the contents of an iPod and other Apple stuff"
HOMEPAGE="http://www.gtkpod.org/libgpod/"

LICENSE="LGPL-2"
SLOT="0"
IUSE="doc +gtk python +udev ios static-libs"

RDEPEND=">=app-pda/libplist-1.0:=
	>=dev-db/sqlite-3
	>=dev-libs/glib-2.16:2
	dev-libs/libxml2
	sys-apps/sg3_utils
	gtk? ( x11-libs/gdk-pixbuf:2 )
	ios? ( app-pda/libimobiledevice:= )
	python? (
		${PYTHON_DEPS}
		>=media-libs/mutagen-1.8[${PYTHON_USEDEP}]
		>=dev-python/pygobject-2.8:2[${PYTHON_USEDEP}]
		)
	udev? ( virtual/udev )"

DEPEND="${RDEPEND}
	python? ( >=dev-lang/swig-3.0.5 )
	dev-libs/libxslt
	dev-util/intltool
	sys-devel/gettext
	virtual/pkgconfig"

REQUIRED_USE="python? ( ${PYTHON_REQUIRED_USE} )
	doc? ( python )"

DOCS="AUTHORS NEWS README* TROUBLESHOOTING"

pkg_setup() {
	use python && python-single-r1_pkg_setup
}

src_prepare() {
	epatch "${FILESDIR}"/${P}-allow_disable_werror.patch

	eautoreconf
}

src_configure() {
	econf \
		$(use_enable static-libs static) \
		$(use_enable udev) \
		$(use_enable gtk gdk-pixbuf) \
		$(use_enable python pygobject) \
		--without-hal \
		--without-mono \
		$(use_with ios libimobiledevice) \
		--with-udev-dir="$(get_udevdir)" \
		--with-html-dir=/usr/share/doc/${PF}/html \
		$(use_with python) \
		$(use_enable doc gtk-doc) \
		--enable-more-warnings=no
}

src_install() {
	default
	rmdir "${ED}"/tmp
	prune_libtool_files --all
}
