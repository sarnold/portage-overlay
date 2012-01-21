# Copyright 1999-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=1

inherit eutils toolchain-funcs qt4

DESCRIPTION="The QAMix utility from the alsamodular project."
HOMEPAGE="http://alsamodular.sourceforge.net/"
SRC_URI="mirror://sourceforge/alsamodular/${P}.tar.bz2"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~x86"
IUSE=""

DEPEND="x11-libs/qt-gui:4
	>=media-libs/alsa-lib-0.9.0
	x11-libs/libX11"

src_unpack() {
	unpack ${A}
	cd "${S}"

	epatch "${FILESDIR}"/${P}-fixqtbasedir.patch
}

src_compile() {
	export CC="${QMAKE_CC}"
	export CXX="${QMAKE_CXX}"
	export LINK="${QMAKE_LINK}"
	export LINK_SHLIB="${QMAKE_CXX}"
	einfo "using QTDIR: '$QTDIR'."
	make -f make_qamix || die "make QAMix failed"
}

src_install() {
	dobin qamix || die "install binaries failed"
	dodoc README || die "install doc failed"
	insinto /usr/share/${PN}
	#doins aeolus01.qmr
}

pkg_postinst() {
	elog "You will find an example of MIDI filter configuration for use"
	elog "with aeolus in /usr/share/${PN}"
}
