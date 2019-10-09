# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI=7
#EAUTORECONF=1
inherit xdg-utils

DESCRIPTION="A panel plug-in to control MPRIS2 compatible players like Pragha (from the same authors)"
HOMEPAGE="https://github.com/matiasdelellis/xfce4-soundmenu-plugin"
IUSE="debug +glyr lastfm +keybinder -mixer"

if [[ ${PV} = 9999* ]]; then
	EGIT_REPO_URI="https://github.com/matiasdelellis/${PN}"
	EGIT_COMMIT="c32cf7ff057f04e2685b0a85a3be49d8be303a8c"
	EGIT_HAS_SUBMODULES=y
	EGIT_NONBARE=y
	KEYWORDS=""
else
	SRC_URI="https://github.com/matiasdelellis/${PN}/releases/download/v${PV}/${P}.tar.bz2"
	KEYWORDS="amd64 arm x86"
fi

LICENSE="GPL-2 LGPL-2"
SLOT="0"

RDEPEND=">=dev-libs/glib-2.28
	>=media-libs/libmpris2client-0.1
	>=media-sound/pulseaudio-2[glib]
	>=x11-libs/gtk+-2.20:2
	x11-libs/libX11
	>=xfce-base/libxfce4ui-4.10
	>=xfce-base/libxfce4util-4.10
	>=xfce-base/xfce4-panel-4.10
	glyr? ( >=media-libs/glyr-1.0.0 )
	lastfm? ( >=media-libs/libclastfm-0.5 )
	keybinder? ( >=dev-libs/keybinder-0.2.2:0 )"
DEPEND="${RDEPEND}
	dev-util/intltool
	sys-devel/gettext
	virtual/pkgconfig"

DOCS=( AUTHORS ChangeLog NEWS README THANKS TODO )

src_configure() {
	local myconf=(
		$(use_enable keybinder)
		$(use_enable lastfm libclastfm)
		$(use_enable glyr libglyr)
		$(xfconf_use_debug)
		$(use_enable mixer)
		)

	econf "${myconf[@]}"
}

src_install() {
	default

	find "${D}" -name '*.la' -delete || die
}
