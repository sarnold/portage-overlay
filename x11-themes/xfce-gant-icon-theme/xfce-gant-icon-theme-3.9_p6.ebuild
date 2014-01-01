# Copyright 1999-2013 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="3"

MY_PDIR="Gant.Xfce"

inherit gnome2-utils

DESCRIPTION="Xfce Gant Icon Theme"
HOMEPAGE="http://www.xfce-look.org/content/show.php/GANT?content=23297"
SRC_URI="http://overlay.uberpenguin.net/icons-xfce-gant-${PV/_p/-}.tar.bz2"

LICENSE="public-domain"
SLOT="0"
KEYWORDS="amd64 x86"
IUSE=""

RDEPEND="x11-themes/hicolor-icon-theme"
DEPEND="${RDEPEND}"

RESTRICT="binchecks strip"

S=${WORKDIR}/${MY_PDIR}

src_install() {
	dodoc README || die
	rm -f icons/iconrc~ README || die

	# note: previous doins -r is horribly slow with some build envs
	dodir /usr/share/icons/${MY_PDIR}
	cp -aR * "${ED}"/usr/share/icons/${MY_PDIR}/ || die
}

pkg_preinst() { gnome2_icon_savelist; }
pkg_postinst() { gnome2_icon_cache_update; }
pkg_postrm() { gnome2_icon_cache_update; }
