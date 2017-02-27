# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="5"

inherit eutils autotools versionator

DESCRIPTION="Yet Another implementation of the Session Initiation Protocol"
HOMEPAGE="http://www.linphone.org/technical-corner/belle-sip/overview"
SRC_URI="https://github.com/BelledonneCommunications/${PN}/archive/${PV}.tar.gz -> ${P}.tar.gz"

LICENSE="GPL-2"
KEYWORDS="~amd64 ~arm ~ppc ~sparc ~x86"

IUSE="pic -server -static tls -tunnel"
SLOT="0"

RDEPEND=">=dev-libs/antlr-c-3.2
	dev-java/antlr:3
	app-misc/bctoolbox
	net-libs/mbedtls
"

DEPEND="${RDEPEND}
	dev-util/intltool
	virtual/pkgconfig"


src_prepare() {
	sed -i -e "s#antlr_java_prefixes=.*#antlr_java_prefixes="$srcdir"#" \
		-e "s|-Werror||g" \
		configure.ac

	sed -i -e 's|bctbx_list_delete_link|bctbx_list_erase_link|g' \
		-e 's|bctbx_list_remove_link|bctbx_list_unlink|g' \
		include/belle-sip/list.h

	sed -i 's|, super->base.peer_cname ? super->base.peer_cname : super->base.peer_name ||' \
		src/transports/tls_channel.c

	AT_M4DIR="m4" eautoreconf
}

src_configure() {
	local my_conf="--disable-tests"
	econf ${my_conf} \
		--disable-strict --with-antlr=${EPREFIX}/usr \
		$(use_enable server server-sockets) \
		$(use_enable static) \
		$(use_enable tls) \
		$(use_enable tunnel) \
		$(use_with pic)
}

src_install() {
	emake DESTDIR="${D}" install
	dodoc AUTHORS ChangeLog README NEWS
}
