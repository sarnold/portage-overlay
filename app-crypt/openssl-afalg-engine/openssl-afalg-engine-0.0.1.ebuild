# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI="4"

MY_PN="af-alg"

inherit autotools eutils libtool versionator

DESCRIPTION="af_alg is an openssl crypto engine kernel interface thing"
HOMEPAGE="https://github.com/sarnold/af_alg"
SRC_URI="mirror://gentoo/${MY_PN}-${PV}.tar.gz"

LICENSE="openssl"
SLOT="0"
KEYWORDS="~amd64 ~arm ~arm64 ~ia64 ~mips ~ppc ~ppc64 ~sparc ~x86"
IUSE=""

DEPEND="virtual/linux-sources
	>=dev-libs/openssl-1.0.0d"
RDEPEND=""

RESTRICT="test"

S=${WORKDIR}/${MY_PN}-${PV}

src_prepare() {
	sed -i -e "s|ssl/engines|engines|" "${S}"/configure.ac
	eautoreconf
}

src_configure() {
	econf --with-pic
}

src_install() {
	emake DESTDIR="${D}" install || die
	dodoc AUTHORS NEWS README.rst
}
