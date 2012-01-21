# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /var/cvsroot/gentoo-x86/media-sound/dvda-author/dvda-author-20050703.ebuild,v 1.1 2008/01/06 02:46:01 sbriesen Exp $

inherit eutils toolchain-funcs

DESCRIPTION="Converts ATS audio to wave, a DVD-Audio Tools utility."
HOMEPAGE="http://dvd-audio.sourceforge.net/"
SRC_URI="mirror://sourceforge/dvd-audio/${P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~x86"
IUSE=""

RDEPEND=">=media-libs/flac-1.1.3"

DEPEND="${RDEPEND}
	dev-util/pkgconfig"

src_unpack() {
	unpack ${A}
	#epatch "${FILESDIR}/${P}-flac113.diff"
}

src_compile() {
	econf --libdir=/usr/$(get_libdir)
	emake CC="$(tc-getCC)" || die "emake failed"
}

src_install() {
	dobin ats2wav || die "install failed"
	#dodoc CHANGES README sort.txt
}
