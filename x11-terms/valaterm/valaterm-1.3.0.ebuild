# Copyright 1999-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI=6
VALA_MIN_API_VERSION="0.32"
VALA_USE_DEPEND=vapigen

MY_PN="vala-terminal"

inherit autotools vala xdg-utils

DESCRIPTION="A lightweight vala based terminal"
HOMEPAGE="https://github.com/freesmartphone/vala-terminal"
SRC_URI="https://github.com/freesmartphone/${MY_PN}/archive/${PV}.tar.gz -> ${P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~arm ~arm64 ~ppc ~ppc64 ~x86"
IUSE="nls"

RDEPEND=$(vala_depend)"
	dev-libs/glib:2
	x11-libs/gtk+:3
	x11-libs/vte:0"

DEPEND="${RDEPEND}
	virtual/pkgconfig
	nls? (
		dev-util/intltool
		sys-devel/gettext
		)"

DOCS="AUTHORS ChangeLog README TODO"

S="${WORKDIR}/${MY_PN}-${PV}"

src_prepare() {
	eapply_user
	eautoreconf
	default
}

src_configure() {
	local my_econf=(
		$(use_enable nls)
	)
	vala_src_prepare
	econf "${my_econf[@]}"
}

pkg_postinst() {
	xdg_desktop_database_update
}

pkg_postrm() {
	xdg_desktop_database_update
}
