# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="2"

SUPPORT_PYTHON_ABIS="1"
PYTHON_DEPEND="2:2.5:2.7"

inherit distutils eutils

DESCRIPTION="lastfmsubmitd is a daemon meant to be used by Last.fm player plugins."
HOMEPAGE="http://www.red-bean.com/decklin/${P}"
SRC_URI="http://www.red-bean.com/decklin/${PN}/${P}.tar.gz"
LICENSE="as-is"

SLOT="0"
KEYWORDS="~amd64 ~arm ~mips ~ppc ~ppc64 ~x86"

IUSE="doc"

DEPEND="!media-sound/lastfm"
RDEPEND="${DEPEND}"

pkg_setup() {

	enewgroup lastfm
	enewuser lastfm -1 -1 -1 lastfm
}

src_prepare() {
	sed -i -e "s|lib\/lastfmsubmitd|$(get_libdir)\/lastfmsubmitd|" \
		"${S}/"setup.py || die "sed failed"
}

src_install() {
	distutils_src_install

	insinto /etc
	doins "${FILESDIR}"/${PN}.conf

	newinitd "${FILESDIR}"/${PN}.init ${PN}

	use doc && dodoc INSTALL

	diropts "-o lastfm -g lastfm -m 0775"
	dodir /var/{log,run,spool}/lastfm
}

pkg_postinst() {
	elog
	ewarn "Please update /etc/lastfmsubmitd.conf with your lastfm user"
	ewarn "info before starting the daemon."
	elog
}
