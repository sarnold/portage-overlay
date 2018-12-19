# Copyright 1999-2018 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI=6

inherit gnome2-utils l10n qmake-utils xdg-utils

if [[ ${PV} == *9999 ]]; then
	inherit git-r3
	EGIT_REPO_URI="https://github.com/sergey-dryabzhinsky/qt-webkit-kiosk.git"
else
	SRC_URI="https://github.com/sergey-dryabzhinsky/${PN}/archive/${PV}.tar.gz -> ${PN}-${PV}.tar.gz"
	KEYWORDS="~amd64 ~arm ~arm64 ~x86"
fi

DESCRIPTION="A simple browser application written on Qt & QtWebkit."
HOMEPAGE="https://github.com/sergey-dryabzhinsky/qt-webkit-kiosk"

LICENSE="LGPL-3"
SLOT="0"
IUSE="debug"

COMMON_DEPEND="
	dev-qt/qtcore:5
	dev-qt/qtgui:5
	dev-qt/qtmultimedia:5[widgets]
	dev-qt/qtnetwork:5[ssl]
	dev-qt/qtwebkit:5[printsupport,multimedia,opengl]
	dev-qt/qtwidgets:5
	x11-libs/libxcb:=
"
DEPEND="${COMMON_DEPEND}
	dev-db/sqlite
	virtual/pkgconfig
"
RDEPEND="${COMMON_DEPEND}
	dev-qt/qtsvg:5
"

DOCS=( doc/README.md doc/README.ru.md )

src_unpack() {
	if [[ ${PV} == *9999 ]]; then
		git-r3_src_unpack
	fi
	default
}

src_configure() {
	# see BUILDING document for explanation of options
	eqmake5 PREFIX="${EPREFIX}"/usr DEBUG_BUILD=$(usex debug true '') setup.pro
}

src_install() {
	emake INSTALL_ROOT="${D}" install
	einstalldocs
}

pkg_postinst() {
	xdg_desktop_database_update
	gnome2_icon_cache_update
}

pkg_postrm() {
	xdg_desktop_database_update
	gnome2_icon_cache_update
}
