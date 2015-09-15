# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=5

PYTHON_COMPAT=( python2_7 )

inherit eutils python-single-r1

DESCRIPTION="Sound menu indicator plugin (adds MPRISv2 support) for XFCE Panel and Gnome Shell"
HOMEPAGE="https://github.com/sunng87/Exaile-Soundmenu-Indicator"

if [[ ${PV} = 9999* ]]; then
	EGIT_REPO_URI="https://github.com/sunng87/Exaile-Soundmenu-Indicator.git"
	inherit git-r3
else
	SRC_URI="mirror://gentoo/${P}.tar.gz"
fi

# this version is based on the following commit id for use with exaile 0.3.2.1-r1
#   7ad3c04c3df92f310e1e0ff2e0d018378aa52840
#   Merge pull request #9 from grawity/master

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~arm ~ppc ~ppc64 ~x86"
IUSE="gnome xfce"

RESTRICT="test"

RDEPEND="${PYTHON_DEPS}
	=media-sound/exaile-0.3*
	xfce? ( xfce-extra/xfce4-soundmenu-plugin )
	gnome? ( gnome-base/gnome-shell )"
DEPEND="${RDEPEND}"

S="${WORKDIR}/${PN}"

RESTRICT="test"

src_prepare() {
	python_setup
}

src_install() {
	insinto /usr/share/exaile/plugins
	doins -r ${S} || die
}

