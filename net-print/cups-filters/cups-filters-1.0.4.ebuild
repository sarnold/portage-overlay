# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=4

inherit autotools eutils base

DESCRIPTION="A modern set of CUPS PDF filters."
HOMEPAGE="http://www.linuxfoundation.org/collaborate/workgroups/openprinting/pdfasstandardprintjobformat"
SRC_URI="http://www.openprinting.org/download/cups-filters/${P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~alpha ~amd64 ~arm ~ppc ~ppc64 ~sparc ~x86"
IUSE="+jpeg"

RDEPEND=">=app-text/poppler-0.18.1[utils]
	media-libs/lcms:2
	media-libs/fontconfig
	media-libs/freetype:2
	>=net-print/cups-1.5
	media-libs/libpng
	media-libs/tiff
	sys-libs/zlib
	jpeg? ( media-libs/jpeg )
	"

DEPEND="${RDEPEND}"

WANT_AUTOCONF=2.5

RESTRICT="strip test"

src_configure() {
	local my_conf="--enable-zlib --with-php=no"
	econf ${my_conf} || die
}

src_compile() {
	emake || die "make failed"
}

src_install() {
	emake DSTROOT="${D}" install || die "einstall failed"
}

pkg_postinst() {
	elog "These filters are largely untested on Gentoo, but have been"
	elog "the default set of print filters on Debian/Ubuntu for a while"
	elog "now. They are optional for cups-1.5 but will be standard on 1.6"
}
