# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI=5

PYTHON_COMPAT=( python2_7 )

inherit eutils git-r3 python-single-r1

DESCRIPTION="Sound menu indicator plugin (adds MPRISv2 support) for XFCE Panel and Gnome Shell"
HOMEPAGE="https://github.com/sarnold/Exaile-Soundmenu-Indicator"

EGIT_REPO_URI="https://github.com/sarnold/Exaile-Soundmenu-Indicator.git"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~arm ~ppc ~ppc64 ~x86"
IUSE="gnome xfce"

RESTRICT="test"

RDEPEND="${PYTHON_DEPS}
	>=media-sound/exaile-3.0[${PYTHON_USEDEP}]
	xfce? ( xfce-extra/xfce4-soundmenu-plugin )
	gnome? ( gnome-base/gnome-shell )"
DEPEND="${RDEPEND}"

REQUIRED_USE="|| ( xfce gnome ) ${PYTHON_REQUIRED_USE}"

#S="${WORKDIR}/${P}"

RESTRICT="test"

pkg_setup() {
	python-single-r1_pkg_setup
}

src_install() {
	insinto /usr/share/exaile/plugins/${PN}
	doins __init__.py  mpris2.py  PLUGININFO || die

	dodoc README.md
}

