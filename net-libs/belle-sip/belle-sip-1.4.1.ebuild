# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="5"

inherit eutils autotools versionator

DESCRIPTION="Yet Another implementation of the Session Initiation Protocol"
HOMEPAGE="http://www.linphone.org/technical-corner/belle-sip/overview"
SRC_URI="http://download.savannah.gnu.org/releases/linphone/${PN}/${P}.tar.gz"

LICENSE="GPL-2"
KEYWORDS="~amd64 ~arm ~ppc ~sparc ~x86"

IUSE="+antlr pic -polarssl -server -static tls -tunnel"
SLOT="0"

RDEPEND="antlr? ( >=dev-libs/antlr-c-3.2 )
	=dev-java/antlr-3*
	!polarssl? ( >=dev-libs/openssl-0.9.7 ) polarssl? ( >=net-libs/polarssl-1.2.10 )
"

DEPEND="${RDEPEND}
	dev-util/intltool
	virtual/pkgconfig"


src_prepare() {
	AT_M4DIR="m4" eautoreconf
}

src_configure() {
	local my_conf="--disable-tests"
	econf ${my_conf} \
		--disable-strict \
		$(use_enable server server-sockets) \
		$(use_enable static) \
		$(use_enable tls) \
		$(use_enable tunnel) \
		$(use_with pic) \
		$(use_with antlr antlr=${EPREFIX}/usr) \
		$(use_with polarssl)
}

src_install() {
	emake DESTDIR="${D}" install
	dodoc AUTHORS ChangeLog INSTALL README NEWS
}
