# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=2
inherit eutils fdo-mime flag-o-matic

DESCRIPTION="Gnome based ALSA Mixer"
HOMEPAGE="http://www.paw.za.org/projects/gnome-alsamixer"
SRC_URI="ftp://ftp.paw.za.org/pub/PAW/sources/${P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="amd64 ppc x86"
IUSE=""

RDEPEND="media-libs/alsa-lib
	 x11-libs/gtk+:2
	 >=gnome-base/libgnomeui-2"
DEPEND="${RDEPEND}
	virtual/pkgconfig"

src_prepare() {
	epatch "${FILESDIR}"/${P}-gtk24.patch \
		"${FILESDIR}"/${P}-fixpath.patch
}

src_compile() {
	append-ldflags -lm
	emake
}

src_install() {
	emake DESTDIR="${D}" install || die "emake install failed"

	make_desktop_entry gnome-alsamixer "Gnome Alsa Mixer" \
		/usr/share/pixmaps/${PN}/${PN}-icon.png

	dodoc AUTHORS ChangeLog
}

pkg_postinst() {
	fdo-mime_mime_database_update
	fdo-mime_desktop_database_update
}

pkg_postrm() {
	fdo-mime_mime_database_update
	fdo-mime_desktop_database_update
}
