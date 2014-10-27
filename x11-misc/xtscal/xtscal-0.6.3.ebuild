# Copyright 1999-2014 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=4

inherit autotools eutils flag-o-matic

DESCRIPTION="Touchscreen calibration utility"
HOMEPAGE="http://gpe.linuxtogo.org/"
SRC_URI="http://gpe.linuxtogo.org/download/source/${P}.tar.bz2 mirror://gentoo/xtscal-0.6.3-patches-0.1.tar.bz2"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="alpha amd64 arm hppa ~ia64 ~m68k ~mips ppc ppc64 ~s390 ~sh ~sparc x86 ~x86-fbsd"
IUSE=""

DEPEND="x11-libs/libX11
	x11-proto/xcalibrateproto
	x11-libs/libXCalibrate
	x11-libs/libXrender
"
RDEPEND="x11-libs/libX11"

src_prepare() {
	epatch "${WORKDIR}"/patch/*.patch
	eautoreconf
}

src_configure() {
	append-libs "-lXrender"
	econf
}

src_install() {
	dobin xtscal || die
}
