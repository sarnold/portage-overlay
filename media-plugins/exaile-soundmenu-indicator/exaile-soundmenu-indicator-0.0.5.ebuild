# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=3

PYTHON_DEPEND="2:2.6"

inherit eutils python

DESCRIPTION="Gnome 3 sound menu indicator plugin (adds MPRISv2 support)"
HOMEPAGE="https://github.com/grawity/Exaile-Soundmenu-Indicator"
SRC_URI="mirror://gentoo/${P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~ppc ~ppc64 ~x86"
IUSE=""

DEPEND=""

RDEPEND="${DEPEND}
	>=gnome-base/gnome-shell-3.2
	media-sound/exaile"

pkg_setup() {
	python_set_active_version 2
}

src_install() {
	insinto /usr/share/exaile/plugins
	doins -r ${S} || die
}

pkg_postinst() {
	python_mod_optimize /usr/share/exaile/plugins/${P}
}

pkg_postrm() {
	python_mod_cleanup /usr/share/exaile/plugins/${P}
}
