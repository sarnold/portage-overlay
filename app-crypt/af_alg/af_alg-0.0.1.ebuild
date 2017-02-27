# Copyright 1999-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI="5"

inherit autotools eutils libtool linux-info multilib versionator multilib-minimal

DESCRIPTION="af_alg is an openssl crypto engine kernel interface thing"
HOMEPAGE="https://github.com/sarnold/af_alg"
SRC_URI="mirror://gentoo/${P}.tar.gz"

LICENSE="openssl"
SLOT="0"
KEYWORDS="~amd64 ~arm ~arm64 ~ia64 ~mips ~ppc ~ppc64 ~sparc ~x86"
IUSE="debug libressl"

DEPEND="virtual/linux-sources
	!libressl? ( dev-libs/openssl:0=[${MULTILIB_USEDEP}] )
	libressl? ( dev-libs/libressl:0=[${MULTILIB_USEDEP}] )"
RDEPEND=""

RESTRICT="test"

ECONF_SOURCE=${S}
CONFIG_CHECK="~CRYPTO_USER_API"
WARNING_CRYPTO_USER_API="You need to enable CONFIG_CRYPTO_USER_API in order to use this package."

src_prepare() {
	sed -i -e "s|ssl/engines|engines|" "${S}"/configure.ac
	eautoreconf

	multilib_copy_sources
}

multilib_src_configure() {
	econf --with-pic
}

multilib_src_compile() {
	use debug && append-flags "-DDEBUG"

	if use debug ; then
		emake clean all || die "emake debug failed"
	else
		emake || die "emake failed"
	fi
}

multilib_src_install() {
	emake DESTDIR="${D}" install || die
	dodoc AUTHORS NEWS README.rst

	prune_libtool_files --modules
}