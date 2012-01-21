# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /var/cvsroot/gentoo-x86/games-board/xgammon/xgammon-0.98.ebuild,v 1.13 2009/09/24 20:46:30 mr_bones_ Exp $

EAPI=2
inherit eutils

MY_SRC_P="sndcrd-test.15"

DESCRIPTION="A program for testing and finding the optimum settings for your sound card."
HOMEPAGE="http://www.theory.physics.ubc.ca/soundcard/soundcard.html"
SRC_URI="http://www.theory.physics.ubc.ca/soundcard/${MY_SRC_P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~ppc ~ppc64 ~x86"
IUSE=""

RDEPEND="x11-libs/xforms
	x11-libs/libXext
	x11-libs/libX11"

DEPEND="${RDEPEND}"

S=${WORKDIR}/${MY_SRC_P}

src_prepare() {
	# need to update the static makefile
	sed -i -e "s|-g -Wall|${CFLAGS}|" \
		-i -e "s|/usr/X11R6/lib|/usr/$(get_libdir)|" \
		-i -e "s|/usr/X11R6/include|/usr/include|" \
		-i -e "s|/usr/local/bin|/usr/bin|" \
		Makefile || die "sed failed"
}

src_configure() {
	elog "Nothing to see here... Move along."
}

src_compile() {
#	env PATH=".:${PATH}" 
	emake || die "emake failed"
}

src_install() {
	emake DESTDIR="${D}" install || die "emake install failed"
}
